"""Purpose-specific release governance for Slice D candidate generation."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.care_reference_governance import activate_release
from app.config import Settings
from app.expected_care_candidates import (
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
    ExpectedCareCandidateOutput,
    _checksum,
)
from app.models import (
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
)

RELEASE_TYPE = "ai_purpose"
RELEASE_KEY = "expected-care-candidate"
SCOPE_KEY = "controlled_synthetic_staging"


class CandidateReleaseTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateReleaseBinding:
    release_id: uuid.UUID
    version: str
    payload_checksum_sha256: str


def candidate_source_checksum_sha256() -> str:
    source = Path(__file__).with_name("expected_care_candidates.py")
    return hashlib.sha256(source.read_bytes()).hexdigest()


def candidate_runtime_contract_checksum(settings: Settings) -> str:
    return _checksum(
        {
            "purpose_code": PURPOSE_CODE,
            "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "prompt_version": PROMPT_VERSION,
            "model_configuration_version": MODEL_CONFIGURATION_VERSION,
            "provider": settings.expected_care_provider,
            "model": settings.expected_care_model,
            "output_schema": ExpectedCareCandidateOutput.model_json_schema(),
        }
    )


def verify_candidate_release(release: GovernedCareRelease, settings: Settings) -> None:
    provenance = release.provenance_json
    expected = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "provider": settings.expected_care_provider,
        "model": settings.expected_care_model,
        "runtime_contract_checksum_sha256": candidate_runtime_contract_checksum(settings),
        "candidate_source_sha256": candidate_source_checksum_sha256(),
    }
    if (
        release.release_type != RELEASE_TYPE
        or release.release_key != RELEASE_KEY
        or release.schema_version != OUTPUT_SCHEMA_VERSION
        or any(provenance.get(key) != value for key, value in expected.items())
    ):
        raise CandidateReleaseTransitionError("purpose_or_runtime_incompatible")
    gates = provenance.get("machine_gates")
    if (
        not isinstance(gates, dict)
        or not gates
        or not all(value is True for value in gates.values())
    ):
        raise CandidateReleaseTransitionError("mandatory_machine_gate_failed")
    if not release.provider_transmission_allowed:
        raise CandidateReleaseTransitionError("provider_transmission_denied")


def active_candidate_release(
    session: Session,
    settings: Settings,
) -> CandidateReleaseBinding:
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == RELEASE_KEY,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if pointer is None:
        raise CandidateReleaseTransitionError("inactive_release")
    release = session.get(GovernedCareRelease, pointer.release_id)
    if release is None:
        raise CandidateReleaseTransitionError("inactive_release")
    verify_candidate_release(release, settings)
    return CandidateReleaseBinding(
        release_id=release.id,
        version=release.version,
        payload_checksum_sha256=release.payload_checksum_sha256,
    )


def activate_candidate_release(
    session: Session,
    *,
    release: GovernedCareRelease,
    settings: Settings,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    on_date: date,
    expected_version: str,
) -> GovernedCareReleaseActivation:
    verify_candidate_release(release, settings)
    active = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == RELEASE_KEY,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if (
        active is not None
        and active.release_id != release.id
        and release.supersedes_release_id != active.release_id
    ):
        raise CandidateReleaseTransitionError("predecessor_mismatch")
    return activate_release(
        session,
        release=release,
        scope_key=SCOPE_KEY,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
        on_date=on_date,
        expected_version=expected_version,
    )


def engage_candidate_kill_switch(
    session: Session,
    *,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
) -> GovernedCareReleaseActivation:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"care-reference-release:{RELEASE_TYPE}:{RELEASE_KEY}:{SCOPE_KEY}"},
    )
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == RELEASE_KEY,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if pointer is None:
        raise CandidateReleaseTransitionError("inactive_release")
    event = GovernedCareReleaseActivation(
        release_id=pointer.release_id,
        release_type=RELEASE_TYPE,
        release_key=RELEASE_KEY,
        scope_key=SCOPE_KEY,
        action="kill_switch",
        prior_release_id=pointer.release_id,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
    )
    session.add(event)
    session.delete(pointer)
    session.flush()
    return event


def rollback_candidate_release(
    session: Session,
    *,
    current_release: GovernedCareRelease,
    rollback_target: GovernedCareRelease,
    settings: Settings,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    on_date: date,
    expected_current_version: str,
) -> GovernedCareReleaseActivation:
    if current_release.version != expected_current_version:
        raise CandidateReleaseTransitionError("expected_version_conflict")
    if current_release.supersedes_release_id != rollback_target.id:
        raise CandidateReleaseTransitionError("predecessor_mismatch")
    verify_candidate_release(current_release, settings)
    verify_candidate_release(rollback_target, settings)
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == RELEASE_KEY,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if pointer is None or pointer.release_id != current_release.id:
        raise CandidateReleaseTransitionError("expected_active_release_conflict")
    return activate_release(
        session,
        release=rollback_target,
        scope_key=SCOPE_KEY,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
        on_date=on_date,
        rollback=True,
        expected_version=rollback_target.version,
    )
