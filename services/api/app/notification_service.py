"""Server-owned creation, deduplication, supersession, and suppression."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import (
    CareRelationship,
    Notification,
    NotificationEvent,
    NotificationOutbox,
    NotificationPreference,
    PayerMembership,
    PayerRequest,
    User,
)
from app.notification_contracts import EVENT_CONTRACTS, render_notification, validate_contract

TERMINAL_NOTIFICATION_STATES = {"cancelled", "expired", "superseded", "dismissed"}
EXTERNAL_CHANNELS = {"apns", "android_emas", "web_push"}


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _event(
    notification: Notification,
    *,
    event_type: str,
    from_status: str | None,
    to_status: str,
    actor_kind: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    evidence: dict[str, object] | None = None,
) -> None:
    sequence = max((row.sequence for row in notification.events), default=0) + 1
    payload = {
        "event_type": event_type,
        "from_status": from_status,
        "to_status": to_status,
        "actor_kind": actor_kind,
        "evidence": evidence or {},
    }
    notification.events.append(
        NotificationEvent(
            sequence=sequence,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            idempotency_key=idempotency_key,
            event_checksum=_digest(payload),
            evidence_json=evidence or {},
        )
    )


def preference_for(db: Session, user: User) -> NotificationPreference | None:
    return db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.role == user.role.value,
        )
    )


def _validate_recipient_scope(
    db: Session,
    *,
    recipient: User,
    patient_id: uuid.UUID | None,
    payer_organization_id: uuid.UUID | None,
    payer_request_id: uuid.UUID | None,
) -> None:
    """Reject an inbox row before persistence when its typed scope is inconsistent."""

    if recipient.role.value == "patient":
        if recipient.patient_profile is None or patient_id != recipient.patient_profile.id:
            raise ValueError("notification_patient_scope_mismatch")
    elif recipient.role.value == "doctor":
        if recipient.doctor_profile is None:
            raise ValueError("notification_doctor_scope_mismatch")
        if patient_id is not None:
            relationship = db.scalar(
                select(CareRelationship.id).where(
                    CareRelationship.doctor_id == recipient.doctor_profile.id,
                    CareRelationship.patient_id == patient_id,
                    CareRelationship.is_active.is_(True),
                )
            )
            if relationship is None:
                raise ValueError("notification_doctor_scope_mismatch")
    elif recipient.role.value == "payer":
        if payer_organization_id is None or payer_request_id is None:
            raise ValueError("payer_notification_scope_mismatch")
        membership = db.scalar(
            select(PayerMembership.id).where(
                PayerMembership.user_id == recipient.id,
                PayerMembership.payer_organization_id == payer_organization_id,
                PayerMembership.status == "active",
            )
        )
        payer_request = db.scalar(
            select(PayerRequest).where(
                PayerRequest.id == payer_request_id,
                PayerRequest.payer_organization_id == payer_organization_id,
            )
        )
        if (
            membership is None
            or payer_request is None
            or patient_id != payer_request.patient_id
        ):
            raise ValueError("payer_notification_scope_mismatch")


def after_quiet_hours(
    value: datetime,
    *,
    time_zone: str,
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
) -> datetime:
    if quiet_hours_start is None or quiet_hours_end is None:
        return value
    start_hour, start_minute = (int(part) for part in quiet_hours_start.split(":"))
    end_hour, end_minute = (int(part) for part in quiet_hours_end.split(":"))
    if (start_hour, start_minute) == (end_hour, end_minute):
        return value
    zone = ZoneInfo(time_zone)
    local = value.astimezone(zone)
    local_minutes = local.hour * 60 + local.minute
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    spans_midnight = start_minutes > end_minutes
    inside = (
        local_minutes >= start_minutes or local_minutes < end_minutes
        if spans_midnight
        else start_minutes <= local_minutes < end_minutes
    )
    if not inside:
        return value
    end_date = local.date()
    if spans_midnight and local_minutes >= start_minutes:
        end_date += timedelta(days=1)
    local_end = datetime.combine(
        end_date,
        datetime.min.time().replace(hour=end_hour, minute=end_minute),
        tzinfo=zone,
    )
    return local_end.astimezone(UTC)


def create_notification(
    db: Session,
    *,
    recipient: User,
    event_type: str,
    source_resource_id: uuid.UUID,
    scheduled_for: datetime | None,
    patient_id: uuid.UUID | None = None,
    clinical_event_id: uuid.UUID | None = None,
    payer_organization_id: uuid.UUID | None = None,
    payer_request_id: uuid.UUID | None = None,
    locale: str | None = None,
    time_zone: str | None = None,
    occurrence_key: str,
) -> tuple[Notification, bool]:
    contract = EVENT_CONTRACTS[event_type]
    deep_link_code = str(
        contract["deep_links"][recipient.role.value]
        if "deep_links" in contract
        else contract["deep_link"]
    )
    validate_contract(event_type, recipient.role.value, deep_link_code)
    _validate_recipient_scope(
        db,
        recipient=recipient,
        patient_id=patient_id,
        payer_organization_id=payer_organization_id,
        payer_request_id=payer_request_id,
    )
    preference = preference_for(db, recipient)
    resolved_locale = locale or (preference.locale if preference else "en")
    resolved_time_zone = time_zone or (preference.time_zone if preference else "UTC")
    rendered = render_notification(event_type, resolved_locale)
    # Identity is scoped by separate typed columns and never enters this digest.
    deduplication_key = _digest({"event_type": event_type, "occurrence_key": occurrence_key})
    content_checksum = _digest(
        {
            "event_type": event_type,
            "template_code": rendered.template_code,
            "locale": rendered.locale,
            "scheduled_for": scheduled_for,
            "deep_link_code": deep_link_code,
            "source_resource_id": str(source_resource_id),
            "payer_organization_id": str(payer_organization_id) if payer_organization_id else None,
            "payer_request_id": str(payer_request_id) if payer_request_id else None,
        }
    )
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"notification-occurrence:{deduplication_key}"},
    )
    existing = db.scalar(
        select(Notification).where(
            Notification.user_id == recipient.id,
            Notification.notification_type == event_type,
            Notification.source_category == contract["source_category"],
            Notification.source_resource_id == source_resource_id,
            Notification.deduplication_key == deduplication_key,
        )
    )
    if existing is not None:
        if existing.content_checksum != content_checksum:
            raise RuntimeError("notification_deduplication_content_conflict")
        return existing, True

    now = datetime.now(UTC)
    for prior in db.scalars(
        select(Notification)
        .where(
            Notification.user_id == recipient.id,
            Notification.notification_type == event_type,
            Notification.source_category == contract["source_category"],
            Notification.source_resource_id == source_resource_id,
            Notification.status.not_in(TERMINAL_NOTIFICATION_STATES),
        )
        .with_for_update()
    ).all():
        previous = prior.status
        prior.status = "superseded"
        prior.superseded_at = now
        prior.version += 1
        _event(
            prior,
            event_type="superseded",
            from_status=previous,
            to_status="superseded",
            actor_kind="system",
            actor_user_id=None,
            idempotency_key=f"supersede:{deduplication_key}",
            evidence={"reason_code": "newer_source_occurrence"},
        )
        for outbox in prior.outbox_entries:
            if outbox.status in {"pending", "retrying", "claimed"}:
                outbox.status = "cancelled"
                outbox.last_result_code = "superseded_before_delivery"

    notification_id = uuid.uuid4()
    expiry_anchor = max(now, scheduled_for) if scheduled_for is not None else now
    notification = Notification(
        id=notification_id,
        user_id=recipient.id,
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
        notification_type=event_type,
        channel="in_app",
        status="unread",
        severity=str(contract["severity"]),
        audience_role=recipient.role.value,
        source_category=str(contract["source_category"]),
        source_resource_id=source_resource_id,
        payer_organization_id=payer_organization_id,
        payer_request_id=payer_request_id,
        deduplication_key=deduplication_key,
        content_checksum=content_checksum,
        template_code=rendered.template_code,
        locale=rendered.locale,
        time_zone=resolved_time_zone,
        privacy_class="generic",
        title=rendered.title,
        body=rendered.body,
        deep_link_code=deep_link_code,
        scheduled_for=scheduled_for,
        expires_at=expiry_anchor + timedelta(hours=int(contract["expiry_hours"])),
        version=1,
        metadata_json={"content_free": True},
    )
    db.add(notification)
    _event(
        notification,
        event_type="created",
        from_status=None,
        to_status="unread",
        actor_kind="system",
        actor_user_id=None,
        idempotency_key=f"create:{deduplication_key}",
        evidence={"event_type": event_type},
    )
    enabled_external = set()
    if preference and event_type in preference.allowed_categories_json:
        enabled_external = set(preference.external_channels_json).intersection(EXTERNAL_CHANNELS)
    for channel in sorted(enabled_external):
        available_at = after_quiet_hours(
            scheduled_for or now,
            time_zone=preference.time_zone,
            quiet_hours_start=preference.quiet_hours_start,
            quiet_hours_end=preference.quiet_hours_end,
        )
        notification.outbox_entries.append(
            NotificationOutbox(
                id=uuid.uuid4(),
                channel=channel,
                status="pending",
                available_at=available_at,
                max_attempts=3,
            )
        )
    db.flush()
    for prior in db.scalars(
        select(Notification).where(
            Notification.user_id == recipient.id,
            Notification.notification_type == event_type,
            Notification.source_category == contract["source_category"],
            Notification.source_resource_id == source_resource_id,
            Notification.status == "superseded",
            Notification.superseded_by_id.is_(None),
        )
    ).all():
        prior.superseded_by_id = notification.id
    return notification, False


def suppress_source_notifications(
    db: Session,
    *,
    source_category: str,
    source_resource_id: uuid.UUID,
    reason_code: str,
    actor_user_id: uuid.UUID | None,
) -> int:
    now = datetime.now(UTC)
    notifications = db.scalars(
        select(Notification)
        .where(
            Notification.source_category == source_category,
            Notification.source_resource_id == source_resource_id,
            Notification.status.not_in(TERMINAL_NOTIFICATION_STATES),
        )
        .with_for_update()
    ).all()
    for notification in notifications:
        previous = notification.status
        notification.status = "cancelled"
        notification.cancelled_at = now
        notification.version += 1
        _event(
            notification,
            event_type="cancelled",
            from_status=previous,
            to_status="cancelled",
            actor_kind="user" if actor_user_id else "system",
            actor_user_id=actor_user_id,
            idempotency_key=f"cancel:{reason_code}:{notification.version}",
            evidence={"reason_code": reason_code},
        )
        for outbox in notification.outbox_entries:
            if outbox.status in {"pending", "retrying", "claimed"}:
                outbox.status = "cancelled"
                outbox.last_result_code = reason_code
    return len(notifications)
