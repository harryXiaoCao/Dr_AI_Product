"""Append-only, checksum-bound operational controls for expected-care AI releases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.expected_care_comparison import _checksum
from app.models import (
    ExpectedCareExplanationRelease,
    ExpectedCareExplanationReleaseEvent,
)

ACCEPTED_EARLY_STAGE_REVIEW_STATES = frozenset(
    {
        "approved",
        "not_required_for_early_synthetic_development",
        "product_owner_waived_for_current_stage",
    }
)


class ExplanationReleaseTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class ReleaseTransitionResult:
    event: ExpectedCareExplanationReleaseEvent
    idempotent_replay: bool


def _lock(session: Session, release_key: str) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"expected-care-release-operation:{release_key}"},
    )


def _event_checksum(event_type: str, evidence: dict[str, object]) -> str:
    return _checksum({"event_type": event_type, "evidence": evidence})


def _append_idempotent(
    session: Session,
    *,
    release: ExpectedCareExplanationRelease,
    actor_user_id: uuid.UUID | None,
    event_type: str,
    idempotency_key: str,
    evidence: dict[str, object],
) -> ReleaseTransitionResult:
    payload = {
        **evidence,
        "idempotency_key": idempotency_key,
        "content_checksum_sha256": _event_checksum(event_type, evidence),
        "content_free_readiness_evidence": True,
    }
    existing = session.scalars(
        select(ExpectedCareExplanationReleaseEvent).where(
            ExpectedCareExplanationReleaseEvent.release_id == release.id,
            ExpectedCareExplanationReleaseEvent.event_type == event_type,
        )
    ).all()
    for event in existing:
        if event.evidence_json.get("idempotency_key") != idempotency_key:
            continue
        if event.evidence_json != payload:
            raise ExplanationReleaseTransitionError("idempotency_content_conflict")
        return ReleaseTransitionResult(event=event, idempotent_replay=True)
    event = ExpectedCareExplanationReleaseEvent(
        release_id=release.id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        evidence_json=payload,
    )
    session.add(event)
    session.flush()
    return ReleaseTransitionResult(event=event, idempotent_replay=False)


def _require_version(
    release: ExpectedCareExplanationRelease,
    expected_version: str,
) -> None:
    if release.version != expected_version:
        raise ExplanationReleaseTransitionError("expected_version_conflict")


def _events(session: Session, release_key: str) -> list[ExpectedCareExplanationReleaseEvent]:
    return session.scalars(
        select(ExpectedCareExplanationReleaseEvent)
        .join(
            ExpectedCareExplanationRelease,
            ExpectedCareExplanationRelease.id == ExpectedCareExplanationReleaseEvent.release_id,
        )
        .where(ExpectedCareExplanationRelease.release_key == release_key)
        .order_by(ExpectedCareExplanationReleaseEvent.sequence)
    ).all()


def effective_active_release_id(session: Session, release_key: str) -> uuid.UUID | None:
    active: uuid.UUID | None = None
    for event in _events(session, release_key):
        if event.event_type in {"release_activated", "release_rolled_back"}:
            active = event.release_id
        elif (
            event.event_type
            in {
                "release_superseded",
                "release_superseded_by_rollback",
                "purpose_kill_switch_engaged",
                "release_marked_unsuitable",
            }
            and active == event.release_id
        ):
            active = None
    return active


def register_early_stage_waivers(
    session: Session,
    *,
    release: ExpectedCareExplanationRelease,
    expected_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    statuses: dict[str, str],
) -> ReleaseTransitionResult:
    _lock(session, release.release_key)
    _require_version(release, expected_version)
    required = {
        str(item["review_type"])
        for item in release.review_requirements_json
        if isinstance(item, dict) and item.get("review_type")
    }
    if set(statuses) != required or any(
        value not in ACCEPTED_EARLY_STAGE_REVIEW_STATES for value in statuses.values()
    ):
        raise ExplanationReleaseTransitionError("stage_waiver_contract_incomplete")
    return _append_idempotent(
        session,
        release=release,
        actor_user_id=actor_user_id,
        event_type="early_stage_waivers_registered",
        idempotency_key=idempotency_key,
        evidence={
            "expected_version": expected_version,
            "statuses": statuses,
            "scope": "synthetic_development_and_controlled_staging_only",
            "future_real_world_gates_preserved": True,
        },
    )


def early_stage_waivers_ready(
    session: Session,
    release: ExpectedCareExplanationRelease,
) -> bool:
    events = session.scalars(
        select(ExpectedCareExplanationReleaseEvent)
        .where(
            ExpectedCareExplanationReleaseEvent.release_id == release.id,
            ExpectedCareExplanationReleaseEvent.event_type == "early_stage_waivers_registered",
        )
        .order_by(ExpectedCareExplanationReleaseEvent.created_at.desc())
    ).all()
    if not events:
        return False
    statuses = events[0].evidence_json.get("statuses")
    return (
        isinstance(statuses, dict)
        and bool(statuses)
        and all(value in ACCEPTED_EARLY_STAGE_REVIEW_STATES for value in statuses.values())
    )


def verify_release_content(
    release: ExpectedCareExplanationRelease,
    *,
    expected_source_checksums: dict[str, str],
    purpose_code: str,
    purpose_contract_version: str,
    schema_version: str,
    prompt_version: str,
    model_configuration_version: str,
) -> None:
    if (
        release.purpose_code != purpose_code
        or release.purpose_contract_version != purpose_contract_version
        or release.schema_version != schema_version
        or release.prompt_version != prompt_version
        or release.model_configuration_version != model_configuration_version
    ):
        raise ExplanationReleaseTransitionError("purpose_or_contract_incompatible")
    if any(
        release.source_checksums_json.get(key) != value
        for key, value in expected_source_checksums.items()
    ):
        raise ExplanationReleaseTransitionError("release_checksum_drift")
    if not release.machine_gates_json or not all(
        value is True for value in release.machine_gates_json.values()
    ):
        raise ExplanationReleaseTransitionError("mandatory_machine_gate_failed")


def activate_release(
    session: Session,
    *,
    release: ExpectedCareExplanationRelease,
    expected_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    expected_source_checksums: dict[str, str],
    purpose_code: str,
    purpose_contract_version: str,
    schema_version: str,
    prompt_version: str,
    model_configuration_version: str,
    rollback_target: str,
) -> ReleaseTransitionResult:
    _lock(session, release.release_key)
    _require_version(release, expected_version)
    verify_release_content(
        release,
        expected_source_checksums=expected_source_checksums,
        purpose_code=purpose_code,
        purpose_contract_version=purpose_contract_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        model_configuration_version=model_configuration_version,
    )
    if not early_stage_waivers_ready(session, release):
        raise ExplanationReleaseTransitionError("early_stage_waivers_missing")
    if rollback_target == "fixed_structured_fallback":
        if release.rollback_target_release_id is not None:
            raise ExplanationReleaseTransitionError("explicit_rollback_target_mismatch")
    else:
        try:
            rollback_target_id = uuid.UUID(rollback_target)
        except ValueError as exc:
            raise ExplanationReleaseTransitionError("explicit_rollback_target_invalid") from exc
        if release.rollback_target_release_id != rollback_target_id:
            raise ExplanationReleaseTransitionError("explicit_rollback_target_mismatch")
    active_id = effective_active_release_id(session, release.release_key)
    if active_id is not None and active_id != release.id:
        raise ExplanationReleaseTransitionError("conflicting_active_release")
    return _append_idempotent(
        session,
        release=release,
        actor_user_id=actor_user_id,
        event_type="release_activated",
        idempotency_key=idempotency_key,
        evidence={
            "expected_version": expected_version,
            "source_checksums": expected_source_checksums,
            "machine_gates_verified": True,
            "stage": "early_synthetic_controlled_staging",
            "rollback_target": rollback_target,
        },
    )


def supersede_release(
    session: Session,
    *,
    active_release: ExpectedCareExplanationRelease,
    successor: ExpectedCareExplanationRelease,
    expected_active_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    rollback_target: str,
) -> tuple[ReleaseTransitionResult, ReleaseTransitionResult]:
    _lock(session, active_release.release_key)
    _require_version(active_release, expected_active_version)
    if successor.predecessor_release_id != active_release.id:
        raise ExplanationReleaseTransitionError("predecessor_mismatch")
    if (
        successor.purpose_code != active_release.purpose_code
        or successor.purpose_contract_version != active_release.purpose_contract_version
        or successor.schema_version != active_release.schema_version
        or not successor.machine_gates_json
        or not all(value is True for value in successor.machine_gates_json.values())
        or not early_stage_waivers_ready(session, successor)
    ):
        raise ExplanationReleaseTransitionError("successor_not_activation_ready")
    if effective_active_release_id(session, active_release.release_key) != active_release.id:
        raise ExplanationReleaseTransitionError("expected_active_release_conflict")
    if rollback_target != str(successor.rollback_target_release_id):
        raise ExplanationReleaseTransitionError("explicit_rollback_target_mismatch")
    superseded = _append_idempotent(
        session,
        release=active_release,
        actor_user_id=actor_user_id,
        event_type="release_superseded",
        idempotency_key=f"{idempotency_key}:supersede",
        evidence={
            "expected_version": expected_active_version,
            "successor_release_id": str(successor.id),
        },
    )
    activated = _append_idempotent(
        session,
        release=successor,
        actor_user_id=actor_user_id,
        event_type="release_activated",
        idempotency_key=f"{idempotency_key}:activate",
        evidence={
            "predecessor_release_id": str(active_release.id),
            "stage": "early_synthetic_controlled_staging",
            "rollback_target": rollback_target,
        },
    )
    return superseded, activated


def engage_purpose_kill_switch(
    session: Session,
    *,
    active_release: ExpectedCareExplanationRelease,
    expected_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    reason_code: str,
) -> ReleaseTransitionResult:
    _lock(session, active_release.release_key)
    _require_version(active_release, expected_version)
    if effective_active_release_id(session, active_release.release_key) != active_release.id:
        raise ExplanationReleaseTransitionError("expected_active_release_conflict")
    return _append_idempotent(
        session,
        release=active_release,
        actor_user_id=actor_user_id,
        event_type="purpose_kill_switch_engaged",
        idempotency_key=idempotency_key,
        evidence={"expected_version": expected_version, "reason_code": reason_code},
    )


def rollback_release(
    session: Session,
    *,
    current_release: ExpectedCareExplanationRelease,
    rollback_target: ExpectedCareExplanationRelease,
    expected_current_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
) -> tuple[ReleaseTransitionResult, ReleaseTransitionResult]:
    _lock(session, current_release.release_key)
    _require_version(current_release, expected_current_version)
    if current_release.rollback_target_release_id != rollback_target.id:
        raise ExplanationReleaseTransitionError("explicit_rollback_target_mismatch")
    if effective_active_release_id(session, current_release.release_key) != current_release.id:
        raise ExplanationReleaseTransitionError("expected_active_release_conflict")
    ended = _append_idempotent(
        session,
        release=current_release,
        actor_user_id=actor_user_id,
        event_type="release_superseded_by_rollback",
        idempotency_key=f"{idempotency_key}:current",
        evidence={
            "expected_version": expected_current_version,
            "rollback_target_release_id": str(rollback_target.id),
        },
    )
    restored = _append_idempotent(
        session,
        release=rollback_target,
        actor_user_id=actor_user_id,
        event_type="release_rolled_back",
        idempotency_key=f"{idempotency_key}:target",
        evidence={"rolled_back_from_release_id": str(current_release.id)},
    )
    return ended, restored


def mark_release_unsuitable(
    session: Session,
    *,
    release: ExpectedCareExplanationRelease,
    expected_version: str,
    actor_user_id: uuid.UUID | None,
    idempotency_key: str,
    reason_codes: list[str],
) -> ReleaseTransitionResult:
    """Append correction evidence without changing the historical release row."""

    _lock(session, release.release_key)
    _require_version(release, expected_version)
    if not reason_codes:
        raise ExplanationReleaseTransitionError("unsuitable_reason_required")
    return _append_idempotent(
        session,
        release=release,
        actor_user_id=actor_user_id,
        event_type="release_marked_unsuitable",
        idempotency_key=idempotency_key,
        evidence={
            "expected_version": expected_version,
            "reason_codes": reason_codes,
            "historical_release_unchanged": True,
        },
    )
