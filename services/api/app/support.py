import hashlib
import json
import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Header, status
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import AuditEvent, SupportRequest, SupportRequestEvent, UserRole
from app.rbac import neutral_not_found, require_enabled_role
from app.schemas import (
    SupportRequestCreateRequest,
    SupportRequestListResponse,
    SupportRequestResponse,
    SupportRequestTimelineEvent,
    SupportRequestWithdrawRequest,
)

router = APIRouter(prefix="/api/v1", tags=["support"])

SUPPORT_ALLOWED_ROLES = {UserRole.doctor, UserRole.patient, UserRole.payer}
SYNTHETIC_DATA_LABEL = "Synthetic demonstration data only. Do not enter real patient data."
CONTACT_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d .-]{7,}\d")
CLINICAL_CONTENT_PATTERNS = (
    re.compile(
        r"\b(ct scan|medical scan|dicom|lab result|medical record|diagnosis|diagnose)\b",
        re.I,
    ),
    re.compile(r"\b(medication change|change my dose|prescribe|prescription)\b", re.I),
)
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,119}$")


def _support_response(
    request: SupportRequest,
    *,
    replayed: bool = False,
) -> SupportRequestResponse:
    can_withdraw = request.status in {"queued", "reviewing"}
    return SupportRequestResponse(
        request_id=request.id,
        reference=request.public_reference,
        request_type=request.request_type,  # type: ignore[arg-type]
        status=request.status,  # type: ignore[arg-type]
        version=request.version,
        subject=request.subject,
        retention_boundary_code=request.retention_boundary_code,  # type: ignore[arg-type]
        deletion_effect_code=(
            "request_only_no_immediate_deletion"
            if request.request_type == "deletion"
            else "not_a_deletion_request"
        ),
        available_actions=["withdraw"] if can_withdraw else [],
        timeline=[
            SupportRequestTimelineEvent(
                sequence=event.sequence,
                event_type=event.event_type,  # type: ignore[arg-type]
                status=event.to_status,  # type: ignore[arg-type]
                actor_kind=event.actor_kind,  # type: ignore[arg-type]
                summary_code=event.public_summary_code,
                occurred_at=event.created_at,
            )
            for event in request.events
        ],
        replayed=replayed,
        created_at=request.created_at,
        updated_at=request.updated_at,
        safety_label=SYNTHETIC_DATA_LABEL,
    )


def _validate_support_text(subject: str, message: str) -> None:
    combined = f"{subject}\n{message}"
    details: list[dict[str, str]] = []
    if CONTACT_PATTERN.search(combined):
        details.append(
            {
                "field": "message",
                "code": "unsafe_content",
                "message": "Do not include contact details or real patient identifiers.",
            }
        )
    if any(pattern.search(combined) for pattern in CLINICAL_CONTENT_PATTERNS):
        details.append(
            {
                "field": "message",
                "code": "unsafe_content",
                "message": "Do not include clinical details or real patient data.",
            }
        )
    if details:
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            details,
        )


def _redacted_body(message: str) -> str:
    redacted = CONTACT_PATTERN.sub("[redacted contact]", message)
    if len(redacted) > 1000:
        return f"{redacted[:1000]}..."
    return redacted


def _idempotency_key(value: str) -> str:
    normalized = value.strip()
    if not IDEMPOTENCY_PATTERN.fullmatch(normalized):
        raise ApiError(
            422,
            "validation_failed",
            "The request could not be validated.",
            [
                {
                    "field": "Idempotency-Key",
                    "code": "invalid_idempotency_key",
                    "message": (
                        "Use 12 to 120 letters, numbers, dots, underscores, "
                        "colons, or hyphens."
                    ),
                }
            ],
        )
    return normalized


def _checksum(value: dict[str, object]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _request_query():
    return select(SupportRequest).options(selectinload(SupportRequest.events))


def _retention_boundary(request_type: str) -> str:
    if request_type == "deletion":
        return "regulated_and_audit_retention_applies"
    return "standard_support_retention"


def _patient_id_for_requester(user: CurrentUser) -> uuid.UUID | None:
    if user.role == UserRole.patient and user.patient_profile is not None:
        return user.patient_profile.id
    return None


def _record_support_audit(
    db: DbSession,
    *,
    user: CurrentUser,
    request: SupportRequest,
    event_type: str,
    metadata: dict[str, object],
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=request.patient_id,
            event_type=event_type,
            resource_type="support_request",
            resource_id=request.id,
            metadata_json=metadata,
        )
    )


@router.post(
    "/support-requests",
    response_model=SupportRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_support_request(
    body: SupportRequestCreateRequest,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> SupportRequestResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    key = _idempotency_key(idempotency_key)
    subject = body.subject.strip()
    message = body.message.strip()
    _validate_support_text(subject, message)
    message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    request_checksum = _checksum(
        {
            "request_type": body.request_type,
            "subject": subject,
            "message_sha256": message_hash,
        }
    )
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"support-request:{user.id}:{key}"},
    )
    existing = db.scalar(
        _request_query().where(
            SupportRequest.requester_user_id == user.id,
            SupportRequest.idempotency_key == key,
        )
    )
    if existing is not None:
        if existing.request_checksum != request_checksum:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used with different request content.",
            )
        db.rollback()
        return _support_response(existing, replayed=True)

    request_id = uuid.uuid4()
    request = SupportRequest(
        id=request_id,
        requester_user_id=user.id,
        patient_id=_patient_id_for_requester(user),
        request_type=body.request_type,
        status="queued",
        public_reference=f"REQ-{request_id.hex[:12].upper()}",
        idempotency_key=key,
        request_checksum=request_checksum,
        version=1,
        retention_boundary_code=_retention_boundary(body.request_type),
        subject=subject,
        body_redacted=_redacted_body(message),
        source="authenticated_app",
        audit_metadata_json={
            "requester_role": user.role.value,
            "message_sha256": message_hash,
            "message_char_count": len(message),
            "body_redacted": True,
            "identity_review_required": body.request_type == "deletion",
            "contains_real_patient_data": False,
        },
    )
    db.add(request)
    db.flush()
    db.add(
        SupportRequestEvent(
            support_request_id=request.id,
            sequence=1,
            event_type="submitted",
            from_status=None,
            to_status="queued",
            actor_kind="requester",
            actor_user_id=user.id,
            public_summary_code="request_submitted",
            idempotency_key=key,
            request_checksum=request_checksum,
        )
    )
    _record_support_audit(
        db,
        user=user,
        request=request,
        event_type="support_request_queued",
        metadata={
            "request_type": request.request_type,
            "status": request.status,
            "requester_role": user.role.value,
            "body_redacted": True,
            "identity_review_required": body.request_type == "deletion",
        },
    )
    db.commit()
    request = db.scalar(_request_query().where(SupportRequest.id == request.id))
    assert request is not None
    return _support_response(request)


@router.get("/support-requests", response_model=SupportRequestListResponse)
def list_support_requests(user: CurrentUser, db: DbSession) -> SupportRequestListResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    requests = db.scalars(
        _request_query()
        .where(SupportRequest.requester_user_id == user.id)
        .order_by(SupportRequest.created_at.desc())
    ).all()
    for request in requests:
        _record_support_audit(
            db,
            user=user,
            request=request,
            event_type="support_requests_listed",
            metadata={"request_type": request.request_type, "status": request.status},
        )
    db.commit()
    return SupportRequestListResponse(items=[_support_response(item) for item in requests])


@router.get("/support-requests/{request_id}", response_model=SupportRequestResponse)
def get_support_request(
    request_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> SupportRequestResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    request = db.scalar(
        _request_query().where(
            SupportRequest.id == request_id,
            SupportRequest.requester_user_id == user.id,
        )
    )
    if request is None:
        raise neutral_not_found()
    _record_support_audit(
        db,
        user=user,
        request=request,
        event_type="support_request_status_read",
        metadata={"request_type": request.request_type, "status": request.status},
    )
    db.commit()
    return _support_response(request)


@router.post(
    "/support-requests/{request_id}/withdraw",
    response_model=SupportRequestResponse,
)
def withdraw_support_request(
    request_id: uuid.UUID,
    body: SupportRequestWithdrawRequest,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> SupportRequestResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    key = _idempotency_key(idempotency_key)
    request = db.scalar(
        _request_query()
        .where(
            SupportRequest.id == request_id,
            SupportRequest.requester_user_id == user.id,
        )
        .with_for_update()
    )
    if request is None:
        raise neutral_not_found()

    action_checksum = _checksum(
        {
            "action": "withdraw",
            "expected_version": body.expected_version,
            "support_request_id": str(request.id),
        }
    )
    replay = next(
        (event for event in request.events if event.idempotency_key == key),
        None,
    )
    if replay is not None:
        if replay.request_checksum != action_checksum:
            raise ApiError(
                409,
                "conflict",
                "The idempotency key was already used with different action content.",
            )
        db.rollback()
        return _support_response(request, replayed=True)

    if request.version != body.expected_version:
        raise ApiError(
            409,
            "conflict",
            "The request changed. Reload it before trying again.",
        )
    if request.status not in {"queued", "reviewing"}:
        raise ApiError(
            409,
            "conflict",
            "This request can no longer be withdrawn.",
        )

    previous_status = request.status
    request.status = "cancelled"
    request.version += 1
    request.withdrawn_at = datetime.now(UTC)
    request.events.append(
        SupportRequestEvent(
            sequence=len(request.events) + 1,
            event_type="withdrawn",
            from_status=previous_status,
            to_status="cancelled",
            actor_kind="requester",
            actor_user_id=user.id,
            public_summary_code="request_withdrawn_by_requester",
            idempotency_key=key,
            request_checksum=action_checksum,
        )
    )
    _record_support_audit(
        db,
        user=user,
        request=request,
        event_type="support_request_withdrawn",
        metadata={
            "request_type": request.request_type,
            "from_status": previous_status,
            "to_status": request.status,
            "requester_role": user.role.value,
            "retention_boundary_code": request.retention_boundary_code,
        },
    )
    db.commit()
    request = db.scalar(_request_query().where(SupportRequest.id == request.id))
    assert request is not None
    return _support_response(request)
