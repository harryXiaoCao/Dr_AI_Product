"""Authenticated, role-scoped Phase 6 notification API."""

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    CareRelationship,
    ClinicalEvent,
    ClinicalEventUpdate,
    ClinicalService,
    ConsultationRequest,
    ExpectedCareComparison,
    MedicalImagingAsset,
    MedicationReminder,
    Notification,
    NotificationDeviceEndpoint,
    NotificationOutbox,
    NotificationPreference,
    PayerMembership,
    PayerRequest,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    UserRole,
)
from app.notification_contracts import EVENT_CONTRACTS
from app.notification_delivery import readiness
from app.notification_service import _event, after_quiet_hours
from app.rbac import require_enabled_role

router = APIRouter(prefix="/api/v1", tags=["notifications"])
ALLOWED_ROLES = {UserRole.patient, UserRole.doctor, UserRole.payer}
TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
TOKEN_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,119}$")


class NotificationItem(BaseModel):
    id: uuid.UUID
    event_type: str
    severity: str
    source_category: str
    status: str
    title: str
    body: str
    actor_kind: Literal["system"] = "system"
    occurred_at: datetime
    scheduled_for: datetime | None
    delivery_state: str
    read_at: datetime | None
    dismissed_at: datetime | None
    expires_at: datetime | None
    superseded_at: datetime | None
    can_dismiss: bool
    can_mark_unread: bool
    deep_link_available: bool
    version: int


class NotificationList(BaseModel):
    items: list[NotificationItem]
    unread_count: int
    next_cursor: None = None
    generated_at: datetime


class NotificationPreferenceBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_categories: list[str]
    in_product_enabled: bool = True
    external_channels: list[Literal["apns", "android_emas", "web_push"]]
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    locale: Literal["en", "zh-Hans"]
    time_zone: str = Field(min_length=1, max_length=64)
    preview_level: Literal["generic", "private_in_app"] = "generic"
    expected_version: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_bounded_fields(self) -> "NotificationPreferenceBody":
        allowed = set(EVENT_CONTRACTS)
        if not set(self.allowed_categories).issubset(allowed):
            raise ValueError("unsupported notification category")
        if len(self.allowed_categories) != len(set(self.allowed_categories)):
            raise ValueError("notification categories must be unique")
        if len(self.external_channels) != len(set(self.external_channels)):
            raise ValueError("external channels must be unique")
        if (self.quiet_hours_start is None) != (self.quiet_hours_end is None):
            raise ValueError("quiet hours require both start and end")
        if self.quiet_hours_start is not None and (
            not TIME_PATTERN.fullmatch(self.quiet_hours_start)
            or not TIME_PATTERN.fullmatch(self.quiet_hours_end or "")
        ):
            raise ValueError("quiet hours must use HH:MM")
        try:
            ZoneInfo(self.time_zone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown IANA time zone") from exc
        return self


class NotificationPreferenceResponse(BaseModel):
    allowed_categories: list[str]
    in_product_enabled: bool
    external_channels: list[str]
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    locale: str
    time_zone: str
    preview_level: str
    version: int


class NotificationMutationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class EndpointBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Literal["apns", "android_emas", "web_push"]
    platform: Literal["ios", "android", "web"]
    token_hash: str
    previous_token_hash: str | None = None
    permission_state: Literal["permission_not_requested", "permission_denied", "active", "revoked"]

    @model_validator(mode="after")
    def validate_endpoint(self) -> "EndpointBody":
        if not TOKEN_HASH_PATTERN.fullmatch(self.token_hash):
            raise ValueError("token_hash must be a lowercase SHA-256 digest")
        if self.previous_token_hash is not None:
            if not TOKEN_HASH_PATTERN.fullmatch(self.previous_token_hash):
                raise ValueError("previous_token_hash must be a lowercase SHA-256 digest")
            if self.previous_token_hash == self.token_hash:
                raise ValueError("rotated endpoint hashes must differ")
        expected = {"apns": "ios", "android_emas": "android", "web_push": "web"}
        if expected[self.channel] != self.platform:
            raise ValueError("channel and platform do not match")
        return self


class EndpointResponse(BaseModel):
    id: uuid.UUID
    channel: str
    platform: str
    status: str
    readiness_code: str
    last_seen_at: datetime | None
    revoked_at: datetime | None


class ReadinessResponse(BaseModel):
    channel: str
    provider: str
    ready: bool
    code: str
    blockers: list[str]


class ReadinessListResponse(BaseModel):
    channels: list[ReadinessResponse]


class OpenResponse(BaseModel):
    status: Literal["resolved", "expired", "denied", "unavailable"]
    route_code: str | None = None
    route_path: str | None = None


def _delivery_state(notification: Notification) -> str:
    states = {entry.status for entry in notification.outbox_entries}
    if not states:
        return "in_product_only"
    for state in ("delivered", "accepted", "retrying", "failed", "unknown", "pending"):
        if state in states:
            return state
    return sorted(states)[0]


def _idempotency_key(value: str) -> str:
    key = value.strip()
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise ApiError(422, "validation_failed", "Use a valid idempotency key.")
    return key


def _checksum(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _item(notification: Notification) -> NotificationItem:
    terminal = notification.status in {"cancelled", "expired", "superseded", "dismissed"}
    return NotificationItem(
        id=notification.id,
        event_type=notification.notification_type,
        severity=notification.severity,
        source_category=notification.source_category,
        status=notification.status,
        title=notification.title,
        body=notification.body,
        occurred_at=notification.created_at,
        scheduled_for=notification.scheduled_for,
        delivery_state=_delivery_state(notification),
        read_at=notification.read_at,
        dismissed_at=notification.dismissed_at,
        expires_at=notification.expires_at,
        superseded_at=notification.superseded_at,
        can_dismiss=not terminal and notification.severity != "warning",
        can_mark_unread=notification.status == "read",
        deep_link_available=not terminal and notification.deep_link_code is not None,
        version=notification.version,
    )


def _own_notification(db: DbSession, user: CurrentUser, notification_id: uuid.UUID) -> Notification:
    notification = db.scalar(
        select(Notification)
        .options(
            selectinload(Notification.outbox_entries),
            selectinload(Notification.events),
        )
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .with_for_update()
    )
    if notification is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    return notification


def _source_is_actionable_for_open(
    db: DbSession,
    notification: Notification,
) -> bool:
    """Recheck the typed authoritative source before returning a destination."""

    source_id = notification.source_resource_id
    if source_id is None:
        return False
    if notification.source_category == "care_relationship":
        return (
            db.scalar(
                select(CareRelationship.id).where(
                    CareRelationship.id == source_id,
                    CareRelationship.patient_id == notification.patient_id,
                    CareRelationship.status == "pending_patient_approval",
                )
            )
            is not None
        )
    if notification.source_category == "medication_reminder":
        reminder = db.get(MedicationReminder, source_id)
        return (
            reminder is not None
            and reminder.patient_id == notification.patient_id
            and reminder.status == "active"
            and reminder.next_due_at == notification.scheduled_for
        )
    if notification.source_category == "recovery_task":
        task = db.scalar(
            select(RecoveryTask)
            .join(RecoveryPlan)
            .where(
                RecoveryTask.id == source_id,
                RecoveryTask.patient_id == notification.patient_id,
                RecoveryPlan.status == "active",
            )
        )
        completion = db.scalar(
            select(RecoveryTaskCompletion.id).where(
                RecoveryTaskCompletion.task_id == source_id,
                RecoveryTaskCompletion.patient_id == notification.patient_id,
            )
        )
        return task is not None and completion is None
    if notification.source_category == "clinical_event":
        return (
            db.scalar(
                select(ClinicalEvent.id).where(
                    ClinicalEvent.id == source_id,
                    ClinicalEvent.patient_id == notification.patient_id,
                )
            )
            is not None
        )
    if notification.source_category == "clinical_event_update":
        return (
            db.scalar(
                select(ClinicalEventUpdate.id).where(
                    ClinicalEventUpdate.id == source_id,
                    ClinicalEventUpdate.patient_id == notification.patient_id,
                )
            )
            is not None
        )
    if notification.source_category == "consultation":
        return (
            db.scalar(
                select(ConsultationRequest.id).where(
                    ConsultationRequest.id == source_id,
                    ConsultationRequest.patient_id == notification.patient_id,
                    ConsultationRequest.status.not_in({"cancelled", "closed"}),
                )
            )
            is not None
        )
    if notification.source_category == "clinical_service":
        return (
            db.scalar(
                select(ClinicalService.id).where(
                    ClinicalService.id == source_id,
                    ClinicalService.patient_id == notification.patient_id,
                    ClinicalService.status != "cancelled",
                )
            )
            is not None
        )
    if notification.source_category == "medical_imaging_asset":
        return (
            db.scalar(
                select(MedicalImagingAsset.id).where(
                    MedicalImagingAsset.id == source_id,
                    MedicalImagingAsset.patient_id == notification.patient_id,
                    MedicalImagingAsset.upload_status != "expired",
                )
            )
            is not None
        )
    if notification.source_category == "payer_request":
        return (
            db.scalar(
                select(PayerRequest.id).where(
                    PayerRequest.id == notification.payer_request_id,
                    PayerRequest.id == source_id,
                    PayerRequest.patient_id == notification.patient_id,
                    PayerRequest.payer_organization_id == notification.payer_organization_id,
                )
            )
            is not None
        )
    if notification.source_category == "expected_care_comparison":
        comparison = db.get(ExpectedCareComparison, source_id)
        return (
            comparison is not None
            and comparison.lifecycle_state == "comparison_published"
            and comparison.patient_id == notification.patient_id
            and comparison.payer_request_id == notification.payer_request_id
        )
    return False


@router.get("/notifications", response_model=NotificationList)
def list_notifications(
    user: CurrentUser,
    db: DbSession,
    category: str | None = Query(default=None, max_length=80),
    notification_status: str | None = Query(default=None, alias="status", max_length=40),
) -> NotificationList:
    require_enabled_role(user, ALLOWED_ROLES)
    query = (
        select(Notification)
        .options(selectinload(Notification.outbox_entries))
        .where(Notification.user_id == user.id)
    )
    if category is not None:
        if category not in EVENT_CONTRACTS:
            raise ApiError(422, "validation_failed", "Unknown notification category.")
        query = query.where(Notification.notification_type == category)
    if notification_status is not None:
        query = query.where(Notification.status == notification_status)
    rows = db.scalars(query.order_by(Notification.created_at.desc())).all()
    unread_count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.status == "unread",
        )
    )
    return NotificationList(
        items=[_item(row) for row in rows],
        unread_count=int(unread_count or 0),
        generated_at=datetime.now(UTC),
    )


@router.get("/notification-preferences", response_model=NotificationPreferenceResponse)
def get_notification_preference(user: CurrentUser, db: DbSession) -> NotificationPreferenceResponse:
    require_enabled_role(user, ALLOWED_ROLES)
    row = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.role == user.role.value,
        )
    )
    if row is None:
        return NotificationPreferenceResponse(
            allowed_categories=sorted(
                event_type
                for event_type, contract in EVENT_CONTRACTS.items()
                if user.role.value in contract["roles"]
            ),
            in_product_enabled=True,
            external_channels=[],
            locale="en",
            time_zone="UTC",
            preview_level="generic",
            version=0,
        )
    return NotificationPreferenceResponse(
        allowed_categories=row.allowed_categories_json,
        in_product_enabled=row.in_product_enabled,
        external_channels=row.external_channels_json,
        quiet_hours_start=row.quiet_hours_start,
        quiet_hours_end=row.quiet_hours_end,
        locale=row.locale,
        time_zone=row.time_zone,
        preview_level=row.preview_level,
        version=row.version,
    )


@router.put("/notification-preferences", response_model=NotificationPreferenceResponse)
def put_notification_preference(
    body: NotificationPreferenceBody,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> NotificationPreferenceResponse:
    require_enabled_role(user, ALLOWED_ROLES)
    key = _idempotency_key(idempotency_key)
    request_checksum = _checksum(body.model_dump(mode="json"))
    disallowed_categories = [
        event_type
        for event_type in body.allowed_categories
        if user.role.value not in EVENT_CONTRACTS[event_type]["roles"]
    ]
    if disallowed_categories:
        raise ApiError(
            422,
            "validation_failed",
            "One or more notification categories are unavailable for this role.",
        )
    unavailable = [
        channel for channel in body.external_channels if not readiness(settings, channel).ready
    ]
    if unavailable:
        raise ApiError(
            422,
            "notification_channel_unavailable",
            "One or more external notification channels are not ready.",
            [
                {
                    "field": "external_channels",
                    "code": readiness(settings, channel).code,
                    "message": f"{channel} is unavailable.",
                }
                for channel in unavailable
            ],
        )
    row = db.scalar(
        select(NotificationPreference)
        .where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.role == user.role.value,
        )
        .with_for_update()
    )
    if row is None:
        if body.expected_version != 0:
            raise ApiError(409, "conflict", "Notification preferences changed. Reload them.")
        row = NotificationPreference(user_id=user.id, role=user.role.value)
        db.add(row)
    else:
        if row.last_idempotency_key == key:
            if row.last_request_checksum != request_checksum:
                raise ApiError(
                    409,
                    "conflict",
                    "The idempotency key was already used with different preference content.",
                )
            db.rollback()
            return get_notification_preference(user, db)
        if body.expected_version != row.version:
            raise ApiError(409, "conflict", "Notification preferences changed. Reload them.")
        row.version += 1
    row.allowed_categories_json = sorted(body.allowed_categories)
    # Safety-relevant records stay in the inbox even when external delivery is off.
    row.in_product_enabled = True
    row.external_channels_json = sorted(body.external_channels)
    row.quiet_hours_start = body.quiet_hours_start
    row.quiet_hours_end = body.quiet_hours_end
    row.locale = body.locale
    row.time_zone = body.time_zone
    row.preview_level = body.preview_level
    row.last_idempotency_key = key
    row.last_request_checksum = request_checksum
    now = datetime.now(UTC)
    pending_outbox = db.scalars(
        select(NotificationOutbox)
        .join(Notification)
        .where(
            Notification.user_id == user.id,
            NotificationOutbox.status.in_({"pending", "retrying"}),
        )
        .with_for_update()
    ).all()
    for outbox in pending_outbox:
        if outbox.channel not in body.external_channels:
            outbox.status = "cancelled"
            outbox.last_result_code = "channel_disabled_by_user"
            continue
        outbox.available_at = after_quiet_hours(
            outbox.notification.scheduled_for or now,
            time_zone=body.time_zone,
            quiet_hours_start=body.quiet_hours_start,
            quiet_hours_end=body.quiet_hours_end,
        )
    db.commit()
    db.refresh(row)
    return get_notification_preference(user, db)


@router.get("/notifications/readiness", response_model=ReadinessListResponse)
def notification_readiness(user: CurrentUser, settings: AppSettings) -> ReadinessListResponse:
    require_enabled_role(user, ALLOWED_ROLES)
    return ReadinessListResponse(
        channels=[
            ReadinessResponse(
                channel=state.channel,
                provider=state.provider,
                ready=state.ready,
                code=state.code,
                blockers=list(state.blockers),
            )
            for state in (
                readiness(settings, channel) for channel in ("apns", "android_emas", "web_push")
            )
        ]
    )


@router.get("/notification-device-endpoints", response_model=list[EndpointResponse])
def list_notification_endpoints(user: CurrentUser, db: DbSession) -> list[EndpointResponse]:
    require_enabled_role(user, ALLOWED_ROLES)
    rows = db.scalars(
        select(NotificationDeviceEndpoint)
        .where(NotificationDeviceEndpoint.user_id == user.id)
        .order_by(NotificationDeviceEndpoint.created_at)
    ).all()
    return [
        EndpointResponse(
            id=row.id,
            channel=row.channel,
            platform=row.platform,
            status=row.status,
            readiness_code=row.readiness_code,
            last_seen_at=row.last_seen_at,
            revoked_at=row.revoked_at,
        )
        for row in rows
    ]


@router.post("/notification-device-endpoints", response_model=EndpointResponse)
def register_notification_endpoint(
    body: EndpointBody,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> EndpointResponse:
    require_enabled_role(user, ALLOWED_ROLES)
    state = readiness(settings, body.channel)
    row = db.scalar(
        select(NotificationDeviceEndpoint)
        .where(
            NotificationDeviceEndpoint.user_id == user.id,
            NotificationDeviceEndpoint.channel == body.channel,
            NotificationDeviceEndpoint.token_hash == body.token_hash,
        )
        .with_for_update()
    )
    now = datetime.now(UTC)
    effective_status = body.permission_state
    readiness_code = state.code
    if body.permission_state == "active" and not state.ready:
        effective_status = "unsupported"
    if row is None:
        row = NotificationDeviceEndpoint(
            user_id=user.id,
            channel=body.channel,
            platform=body.platform,
            token_hash=body.token_hash,
        )
        db.add(row)
    if body.previous_token_hash is not None:
        previous = db.scalar(
            select(NotificationDeviceEndpoint)
            .where(
                NotificationDeviceEndpoint.user_id == user.id,
                NotificationDeviceEndpoint.channel == body.channel,
                NotificationDeviceEndpoint.platform == body.platform,
                NotificationDeviceEndpoint.token_hash == body.previous_token_hash,
            )
            .with_for_update()
        )
        if previous is not None:
            previous.status = "stale"
            previous.readiness_code = "endpoint_rotated"
            previous.rotated_at = now
            previous.revoked_at = now
    row.status = effective_status
    row.readiness_code = readiness_code
    row.last_seen_at = now
    row.revoked_at = now if effective_status in {"revoked", "unsupported"} else None
    db.commit()
    db.refresh(row)
    return EndpointResponse(
        id=row.id,
        channel=row.channel,
        platform=row.platform,
        status=row.status,
        readiness_code=row.readiness_code,
        last_seen_at=row.last_seen_at,
        revoked_at=row.revoked_at,
    )


@router.delete(
    "/notification-device-endpoints/{endpoint_id}",
    response_model=EndpointResponse,
)
def sign_out_notification_endpoint(
    endpoint_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> EndpointResponse:
    require_enabled_role(user, ALLOWED_ROLES)
    row = db.scalar(
        select(NotificationDeviceEndpoint)
        .where(
            NotificationDeviceEndpoint.id == endpoint_id,
            NotificationDeviceEndpoint.user_id == user.id,
        )
        .with_for_update()
    )
    if row is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    row.status = "signed_out"
    row.readiness_code = "signed_out"
    row.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return EndpointResponse(
        id=row.id,
        channel=row.channel,
        platform=row.platform,
        status=row.status,
        readiness_code=row.readiness_code,
        last_seen_at=row.last_seen_at,
        revoked_at=row.revoked_at,
    )


def _transition(
    db: DbSession,
    user: CurrentUser,
    notification_id: uuid.UUID,
    body: NotificationMutationBody,
    idempotency_key: str,
    *,
    action: Literal["read", "unread", "dismiss"],
) -> NotificationItem:
    notification = _own_notification(db, user, notification_id)
    key = _idempotency_key(idempotency_key)
    request_checksum = _checksum({"action": action, "expected_version": body.expected_version})
    replay = next(
        (event for event in notification.events if event.idempotency_key == key),
        None,
    )
    if replay is not None:
        if replay.evidence_json.get("request_checksum") != request_checksum:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used with different action content.",
            )
        db.rollback()
        return _item(notification)
    if notification.version != body.expected_version:
        raise ApiError(409, "conflict", "This notification changed. Reload it.")
    now = datetime.now(UTC)
    previous = notification.status
    if previous in {"cancelled", "expired", "superseded", "dismissed"}:
        raise ApiError(409, "conflict", "This notification is no longer actionable.")
    if action == "read":
        notification.status = "read"
        notification.read_at = now
    elif action == "unread":
        notification.status = "unread"
        notification.read_at = None
    else:
        if notification.severity == "warning":
            raise ApiError(409, "conflict", "This warning remains visible in history.")
        notification.status = "dismissed"
        notification.dismissed_at = now
    notification.version += 1
    _event(
        notification,
        event_type=action,
        from_status=previous,
        to_status=notification.status,
        actor_kind="user",
        actor_user_id=user.id,
        idempotency_key=key,
        evidence={"action": action, "request_checksum": request_checksum},
    )
    db.commit()
    db.refresh(notification)
    return _item(notification)


@router.post("/notifications/{notification_id}/read", response_model=NotificationItem)
def mark_notification_read(
    notification_id: uuid.UUID,
    body: NotificationMutationBody,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> NotificationItem:
    return _transition(
        db,
        user,
        notification_id,
        body,
        idempotency_key,
        action="read",
    )


@router.post("/notifications/{notification_id}/unread", response_model=NotificationItem)
def mark_notification_unread(
    notification_id: uuid.UUID,
    body: NotificationMutationBody,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> NotificationItem:
    return _transition(
        db,
        user,
        notification_id,
        body,
        idempotency_key,
        action="unread",
    )


@router.post("/notifications/{notification_id}/dismiss", response_model=NotificationItem)
def dismiss_notification(
    notification_id: uuid.UUID,
    body: NotificationMutationBody,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> NotificationItem:
    return _transition(
        db,
        user,
        notification_id,
        body,
        idempotency_key,
        action="dismiss",
    )


@router.post("/notifications/{notification_id}/open", response_model=OpenResponse)
def open_notification(notification_id: uuid.UUID, user: CurrentUser, db: DbSession) -> OpenResponse:
    notification = _own_notification(db, user, notification_id)
    now = datetime.now(UTC)
    if notification.expires_at is not None and notification.expires_at <= now:
        return OpenResponse(status="expired")
    if notification.status in {"cancelled", "expired", "superseded", "dismissed"}:
        return OpenResponse(status="unavailable")
    if not _source_is_actionable_for_open(db, notification):
        return OpenResponse(status="unavailable")
    route_code = notification.deep_link_code
    route_path = {
        "patient_medications": "/patient/medical-service/medications",
        "patient_recovery": "/patient/recovery-plan",
        "patient_contacts": "/patient/contacts",
        "patient_care_cost": "/patient/care-costs",
        "patient_dashboard": "/patient",
        "patient_consultations": "/patient",
        "patient_medical_service": "/patient/medical-service/records",
        "patient_imaging": "/patient/medical-service/imaging",
        "doctor_patient_care": "/doctor/patients",
        "payer_request": (
            f"/payer/requests/{notification.payer_request_id}/expected-care"
            if notification.payer_request_id
            else None
        ),
        "doctor_payer_request": (
            f"/doctor/payer-requests/{notification.payer_request_id}"
            if notification.payer_request_id
            else None
        ),
        "doctor_expected_care": "/doctor/payer-requests",
    }.get(route_code or "")
    authorized = route_path is not None
    if route_code == "payer_request":
        membership = db.scalar(
            select(PayerMembership).where(
                PayerMembership.user_id == user.id,
                PayerMembership.status == "active",
                PayerMembership.payer_organization_id == notification.payer_organization_id,
            )
        )
        request = db.scalar(
            select(PayerRequest).where(
                PayerRequest.id == notification.payer_request_id,
                PayerRequest.payer_organization_id == notification.payer_organization_id,
            )
        )
        authorized = membership is not None and request is not None
    elif route_code == "doctor_payer_request":
        request = db.scalar(
            select(PayerRequest).where(
                PayerRequest.id == notification.payer_request_id,
                PayerRequest.doctor_id == (user.doctor_profile.id if user.doctor_profile else None),
            )
        )
        relationship = (
            db.scalar(
                select(CareRelationship.id).where(
                    CareRelationship.doctor_id == user.doctor_profile.id,
                    CareRelationship.patient_id == notification.patient_id,
                    CareRelationship.is_active.is_(True),
                )
            )
            if user.doctor_profile is not None
            else None
        )
        authorized = request is not None and relationship is not None
    elif route_code == "doctor_expected_care":
        if user.doctor_profile is None:
            authorized = False
        elif notification.payer_request_id is not None:
            request = db.scalar(
                select(PayerRequest).where(
                    PayerRequest.id == notification.payer_request_id,
                    PayerRequest.doctor_id == user.doctor_profile.id,
                )
            )
            relationship = db.scalar(
                select(CareRelationship.id).where(
                    CareRelationship.doctor_id == user.doctor_profile.id,
                    CareRelationship.patient_id == notification.patient_id,
                    CareRelationship.is_active.is_(True),
                )
            )
            authorized = request is not None and relationship is not None
        else:
            relationship = db.scalar(
                select(CareRelationship).where(
                    CareRelationship.doctor_id == user.doctor_profile.id,
                    CareRelationship.patient_id == notification.patient_id,
                    CareRelationship.is_active.is_(True),
                )
            )
            authorized = relationship is not None
    elif route_code == "doctor_patient_care":
        authorized = (
            user.doctor_profile is not None
            and db.scalar(
                select(CareRelationship.id).where(
                    CareRelationship.doctor_id == user.doctor_profile.id,
                    CareRelationship.patient_id == notification.patient_id,
                    CareRelationship.is_active.is_(True),
                )
            )
            is not None
        )
    elif route_code in {
        "patient_medications",
        "patient_recovery",
        "patient_care_cost",
        "patient_dashboard",
        "patient_consultations",
        "patient_medical_service",
        "patient_imaging",
        "patient_contacts",
    }:
        authorized = user.patient_profile is not None and (
            notification.patient_id == user.patient_profile.id
        )
    if not authorized:
        return OpenResponse(status="denied")
    if notification.status != "read":
        previous = notification.status
        notification.status = "read"
        notification.read_at = now
        notification.version += 1
        _event(
            notification,
            event_type="opened",
            from_status=previous,
            to_status="read",
            actor_kind="user",
            actor_user_id=user.id,
            idempotency_key=f"open:{notification.version}",
            evidence={"route_code": route_code or "unavailable"},
        )
        db.commit()
    return OpenResponse(status="resolved", route_code=route_code, route_path=route_path)
