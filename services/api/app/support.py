import hashlib
import re
import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import AuditEvent, SupportRequest, UserRole
from app.rbac import neutral_not_found, require_enabled_role
from app.schemas import (
    SupportRequestCreateRequest,
    SupportRequestListResponse,
    SupportRequestResponse,
)

router = APIRouter(prefix="/api/v1", tags=["support"])

SUPPORT_ALLOWED_ROLES = {UserRole.doctor, UserRole.patient}
SYNTHETIC_DATA_LABEL = "Synthetic demonstration data only. Do not enter real patient data."
CONTACT_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d .-]{7,}\d")
CLINICAL_CONTENT_PATTERNS = (
    re.compile(r"\b(ct|scan|dicom|lab result|medical record|diagnosis|diagnose)\b", re.I),
    re.compile(r"\b(medication change|change my dose|prescribe|prescription)\b", re.I),
)


def _support_response(request: SupportRequest) -> SupportRequestResponse:
    return SupportRequestResponse(
        request_id=request.id,
        request_type=request.request_type,  # type: ignore[arg-type]
        status=request.status,  # type: ignore[arg-type]
        subject=request.subject,
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
) -> SupportRequestResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    subject = body.subject.strip()
    message = body.message.strip()
    _validate_support_text(subject, message)
    message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    request = SupportRequest(
        requester_user_id=user.id,
        patient_id=_patient_id_for_requester(user),
        request_type=body.request_type,
        status="queued",
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
    db.refresh(request)
    return _support_response(request)


@router.get("/support-requests", response_model=SupportRequestListResponse)
def list_support_requests(user: CurrentUser, db: DbSession) -> SupportRequestListResponse:
    require_enabled_role(user, SUPPORT_ALLOWED_ROLES)
    requests = db.scalars(
        select(SupportRequest)
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
        select(SupportRequest).where(
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
