import hashlib
import json
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import AuditEvent, SupportRequest, SupportRequestEvent, User, UserRole

_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,119}$")
_TRANSITIONS = {
    "start_review": ("queued", "reviewing", "support_review_started"),
    "resolve": ("reviewing", "resolved", "support_request_resolved"),
    "mark_failed": ("reviewing", "failed", "support_processing_failed"),
    "retry_queue": ("failed", "queued", "support_requeued_after_failure"),
}


class SupportTransitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupportTransitionResult:
    support_request_id: uuid.UUID
    status: str
    version: int
    replayed: bool


def _checksum(
    *,
    request_id: uuid.UUID,
    action: str,
    expected_version: int,
    actor_kind: str,
) -> str:
    value = json.dumps(
        {
            "request_id": str(request_id),
            "action": action,
            "expected_version": expected_version,
            "actor_kind": actor_kind,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def transition_support_request(
    db: Session,
    *,
    public_reference: str,
    action: str,
    expected_version: int,
    idempotency_key: str,
    actor_user_id: uuid.UUID,
    actor_kind: str = "support_team",
) -> SupportTransitionResult:
    """Apply one operational transition without exposing an admin product route."""

    if action not in _TRANSITIONS:
        raise SupportTransitionError("unsupported_action")
    if actor_kind not in {"support_team", "system"}:
        raise SupportTransitionError("unsupported_actor_kind")
    if expected_version < 1:
        raise SupportTransitionError("invalid_expected_version")
    key = idempotency_key.strip()
    if not _KEY.fullmatch(key):
        raise SupportTransitionError("invalid_idempotency_key")

    actor = db.scalar(
        select(User).where(
            User.id == actor_user_id,
            User.role == UserRole.admin,
            User.is_active.is_(True),
        )
    )
    if actor is None:
        raise SupportTransitionError("operational_actor_not_authorized")

    request = db.scalar(
        select(SupportRequest)
        .options(selectinload(SupportRequest.events))
        .where(SupportRequest.public_reference == public_reference)
        .with_for_update()
    )
    if request is None:
        raise SupportTransitionError("request_not_found")

    request_checksum = _checksum(
        request_id=request.id,
        action=action,
        expected_version=expected_version,
        actor_kind=actor_kind,
    )
    replay = next(
        (event for event in request.events if event.idempotency_key == key),
        None,
    )
    if replay is not None:
        if replay.request_checksum != request_checksum:
            raise SupportTransitionError("idempotency_content_conflict")
        result = SupportTransitionResult(
            support_request_id=request.id,
            status=replay.to_status,
            version=replay.sequence,
            replayed=True,
        )
        db.rollback()
        return result

    from_status, to_status, summary_code = _TRANSITIONS[action]
    if request.version != expected_version:
        raise SupportTransitionError("stale_expected_version")
    if request.status != from_status:
        raise SupportTransitionError("invalid_status_transition")

    request.status = to_status
    request.version += 1
    event = SupportRequestEvent(
        sequence=request.version,
        event_type="status_changed",
        from_status=from_status,
        to_status=to_status,
        actor_kind=actor_kind,
        actor_user_id=actor.id,
        public_summary_code=summary_code,
        idempotency_key=key,
        request_checksum=request_checksum,
    )
    request.events.append(event)
    db.add(
        AuditEvent(
            actor_user_id=actor.id,
            patient_id=request.patient_id,
            event_type="support_request_status_changed",
            resource_type="support_request",
            resource_id=request.id,
            metadata_json={
                "request_type": request.request_type,
                "from_status": from_status,
                "to_status": to_status,
                "actor_kind": actor_kind,
                "public_summary_code": summary_code,
                "retention_boundary_code": request.retention_boundary_code,
            },
        )
    )
    db.commit()
    return SupportTransitionResult(
        support_request_id=request.id,
        status=to_status,
        version=request.version,
        replayed=False,
    )
