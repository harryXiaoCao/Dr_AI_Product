"""Immutable release bindings and operations for the three CEI purposes."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import (
    CEI_CRITIC_PROMPT_VERSION,
    CEI_CRITIC_PURPOSE_CODE,
    CEI_CRITIC_PURPOSE_CONTRACT_VERSION,
    CEI_CRITIC_SCHEMA_VERSION,
    CEI_CRITIC_VALIDATOR_VERSION,
    CEI_EXPLANATION_MODEL_CONFIGURATION_VERSION,
    CEI_EXPLANATION_PROMPT_VERSION,
    CEI_EXPLANATION_PURPOSE_CODE,
    CEI_EXPLANATION_PURPOSE_CONTRACT_VERSION,
    CEI_EXPLANATION_SCHEMA_VERSION,
    CEI_EXPLANATION_VALIDATOR_VERSION,
    CEI_MODEL_CONFIGURATION_VERSION,
    CEI_OUTPUT_SCHEMA_VERSION,
    CEI_PROMPT_VERSION,
    CEI_PURPOSE_CODE,
    CEI_PURPOSE_CONTRACT_VERSION,
    CEI_RECONCILIATION_VERSION,
    CEI_SCORE_CONTRACT_VERSION,
    CEI_VALIDATOR_VERSION,
    CriticOutput,
    PrimaryIntelligenceOutput,
    RoleExplanationPlan,
    canonical_checksum,
)
from app.config import Settings
from app.models import (
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
)

RELEASE_TYPE = "ai_purpose"
SCOPE_KEY = "controlled_synthetic_staging"
PRIMARY_RELEASE_KEY = "clinical-event-intelligence-primary"
CRITIC_RELEASE_KEY = "clinical-event-intelligence-critic"
EXPLANATION_RELEASE_KEY = "clinical-event-intelligence-role-explanation"
FIXED_FALLBACK_TARGET = "fixed_structured_fallback"
ACCEPTED_SYNTHETIC_REVIEW_STATES = frozenset(
    {
        "not_required_for_early_synthetic_development",
        "product_owner_waived_for_current_stage",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVALUATION_ROOT = _REPO_ROOT / "evaluation/clinical_event_intelligence"
EVALUATION_PATHS = {
    "evaluation_manifest_checksum_sha256": _EVALUATION_ROOT / "frozen_suite.v1.json",
    "verification_matrix_checksum_sha256": _EVALUATION_ROOT / "verification_matrix.v1.json",
    "provider_free_result_checksum_sha256": (
        _EVALUATION_ROOT / "results/clinical-event-intelligence-provider-free-20260801T175010Z.json"
    ),
    "live_result_checksum_sha256": (
        _EVALUATION_ROOT / "results/clinical-event-intelligence-live-20260801T153444Z.json"
    ),
}


class IntelligenceReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class IntelligenceReleaseBinding:
    release_id: uuid.UUID
    release_key: str
    version: str
    payload_checksum_sha256: str


@dataclass(frozen=True)
class IntelligencePurposeSpec:
    release_key: str
    purpose_code: str
    purpose_contract_version: str
    schema_version: str
    prompt_version: str
    model_configuration_version: str
    validator_version: str
    scoring_aggregation_version: str
    source_files: tuple[str, ...]
    provider_setting: str
    model_setting: str
    output_schema: type


@dataclass(frozen=True)
class ReleaseOperationResult:
    event: GovernedCareReleaseActivation
    idempotent_replay: bool


PURPOSE_SPECS = {
    PRIMARY_RELEASE_KEY: IntelligencePurposeSpec(
        release_key=PRIMARY_RELEASE_KEY,
        purpose_code=CEI_PURPOSE_CODE,
        purpose_contract_version=CEI_PURPOSE_CONTRACT_VERSION,
        schema_version=CEI_OUTPUT_SCHEMA_VERSION,
        prompt_version=CEI_PROMPT_VERSION,
        model_configuration_version=CEI_MODEL_CONFIGURATION_VERSION,
        validator_version=CEI_VALIDATOR_VERSION,
        scoring_aggregation_version=CEI_SCORE_CONTRACT_VERSION,
        source_files=(
            "clinical_event_intelligence_contracts.py",
            "clinical_event_intelligence_provider.py",
            "clinical_event_intelligence_service.py",
            "clinical_event_intelligence_validation.py",
            "clinical_event_intelligence_retrieval.py",
            "clinical_event_snapshot.py",
            "clinical_event_intelligence_reconciliation.py",
        ),
        provider_setting="clinical_event_intelligence_primary_provider",
        model_setting="clinical_event_intelligence_primary_model",
        output_schema=PrimaryIntelligenceOutput,
    ),
    CRITIC_RELEASE_KEY: IntelligencePurposeSpec(
        release_key=CRITIC_RELEASE_KEY,
        purpose_code=CEI_CRITIC_PURPOSE_CODE,
        purpose_contract_version=CEI_CRITIC_PURPOSE_CONTRACT_VERSION,
        schema_version=CEI_CRITIC_SCHEMA_VERSION,
        prompt_version=CEI_CRITIC_PROMPT_VERSION,
        model_configuration_version=CEI_MODEL_CONFIGURATION_VERSION,
        validator_version=CEI_CRITIC_VALIDATOR_VERSION,
        scoring_aggregation_version=CEI_RECONCILIATION_VERSION,
        source_files=(
            "clinical_event_intelligence_contracts.py",
            "clinical_event_intelligence_provider.py",
            "clinical_event_intelligence_validation.py",
            "clinical_event_intelligence_reconciliation.py",
        ),
        provider_setting="clinical_event_intelligence_critic_provider",
        model_setting="clinical_event_intelligence_critic_model",
        output_schema=CriticOutput,
    ),
    EXPLANATION_RELEASE_KEY: IntelligencePurposeSpec(
        release_key=EXPLANATION_RELEASE_KEY,
        purpose_code=CEI_EXPLANATION_PURPOSE_CODE,
        purpose_contract_version=CEI_EXPLANATION_PURPOSE_CONTRACT_VERSION,
        schema_version=CEI_EXPLANATION_SCHEMA_VERSION,
        prompt_version=CEI_EXPLANATION_PROMPT_VERSION,
        model_configuration_version=CEI_EXPLANATION_MODEL_CONFIGURATION_VERSION,
        validator_version=CEI_EXPLANATION_VALIDATOR_VERSION,
        scoring_aggregation_version="validated-role-fact-selection.v1",
        source_files=(
            "clinical_event_intelligence_contracts.py",
            "clinical_event_intelligence_explanations.py",
            "clinical_event_intelligence_routes.py",
        ),
        provider_setting="clinical_event_intelligence_explanation_provider",
        model_setting="clinical_event_intelligence_explanation_model",
        output_schema=RoleExplanationPlan,
    ),
}


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluation_checksums() -> dict[str, str]:
    return {key: _file_checksum(path) for key, path in EVALUATION_PATHS.items()}


def purpose_source_checksums(release_key: str) -> dict[str, str]:
    spec = PURPOSE_SPECS.get(release_key)
    if spec is None:
        raise IntelligenceReleaseError("unknown_purpose_release")
    app_root = Path(__file__).resolve().parent
    return {name: _file_checksum(app_root / name) for name in spec.source_files}


def purpose_runtime_contract(
    release_key: str,
    settings: Settings,
) -> dict[str, object]:
    spec = PURPOSE_SPECS.get(release_key)
    if spec is None:
        raise IntelligenceReleaseError("unknown_purpose_release")
    return {
        "purpose_code": spec.purpose_code,
        "purpose_contract_version": spec.purpose_contract_version,
        "schema_version": spec.schema_version,
        "prompt_version": spec.prompt_version,
        "model_configuration_version": spec.model_configuration_version,
        "validator_version": spec.validator_version,
        "scoring_aggregation_version": spec.scoring_aggregation_version,
        "provider": getattr(settings, spec.provider_setting),
        "model": getattr(settings, spec.model_setting),
        "output_schema_checksum_sha256": canonical_checksum(spec.output_schema.model_json_schema()),
    }


def _validate_release_reviews(release: GovernedCareRelease) -> None:
    required = {str(value) for value in release.required_review_types_json}
    approved = {
        review.review_type
        for review in release.reviews
        if review.decision in ACCEPTED_SYNTHETIC_REVIEW_STATES
        and review.reviewed_payload_checksum_sha256 == release.payload_checksum_sha256
    }
    if not required or not required <= approved:
        raise IntelligenceReleaseError("required_reviews_missing")


def _verify_historical_release_integrity(
    release: GovernedCareRelease,
    *,
    on_date: date | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    if release.release_key not in PURPOSE_SPECS or release.release_type != RELEASE_TYPE:
        raise IntelligenceReleaseError("unknown_purpose_release")
    today = on_date or date.today()
    if release.lifecycle_status not in {"reviewed", "active"}:
        raise IntelligenceReleaseError("release_not_reviewed")
    if release.effective_from > today or (
        release.effective_to is not None and release.effective_to < today
    ):
        raise IntelligenceReleaseError("release_outside_effective_window")
    if release.next_review_on is None or release.next_review_on < today:
        raise IntelligenceReleaseError("release_stale")
    if release.jurisdiction != "synthetic_only":
        raise IntelligenceReleaseError("release_not_synthetic_only")
    if release.rights_status not in ACCEPTED_SYNTHETIC_REVIEW_STATES:
        raise IntelligenceReleaseError("release_rights_unresolved")
    if not release.storage_allowed or not release.derivation_allowed:
        raise IntelligenceReleaseError("release_usage_rights_denied")
    if not release.provider_transmission_allowed:
        raise IntelligenceReleaseError("provider_transmission_denied")
    _validate_release_reviews(release)
    provenance = release.provenance_json
    payload = provenance.get("release_payload")
    if not isinstance(payload, dict):
        raise IntelligenceReleaseError("release_payload_missing")
    if canonical_checksum(payload) != release.payload_checksum_sha256:
        raise IntelligenceReleaseError("release_payload_checksum_drift")
    stored_sources = provenance.get("source_checksums")
    if (
        not isinstance(stored_sources, dict)
        or payload.get("source_checksums") != stored_sources
        or release.source_checksum_sha256 != canonical_checksum(stored_sources)
    ):
        raise IntelligenceReleaseError("release_source_checksum_drift")
    stored_evaluations = provenance.get("evaluation_checksums")
    if (
        not isinstance(stored_evaluations, dict)
        or payload.get("evaluation_checksums") != stored_evaluations
    ):
        raise IntelligenceReleaseError("release_evaluation_checksum_drift")
    stored_runtime = provenance.get("runtime_contract")
    if (
        not isinstance(stored_runtime, dict)
        or payload.get("runtime_contract") != stored_runtime
        or provenance.get("runtime_contract_checksum_sha256") != canonical_checksum(stored_runtime)
    ):
        raise IntelligenceReleaseError("runtime_contract_checksum_drift")
    expected_fields = {
        "release_key": release.release_key,
        "version": release.version,
        "schema_version": release.schema_version,
        "data_class": "wholly_synthetic",
        "scope_key": SCOPE_KEY,
        "real_world_activation_allowed": False,
    }
    if any(payload.get(key) != value for key, value in expected_fields.items()):
        raise IntelligenceReleaseError("release_payload_database_mismatch")
    gates = provenance.get("machine_gates")
    if (
        not isinstance(gates, dict)
        or not gates
        or not all(value is True for value in gates.values())
        or payload.get("machine_gates") != gates
    ):
        raise IntelligenceReleaseError("mandatory_machine_gate_failed")
    if len(release.source_checksum_sha256) != 64 or len(release.payload_checksum_sha256) != 64:
        raise IntelligenceReleaseError("release_checksum_invalid")
    return provenance, payload


def verify_intelligence_release(
    release: GovernedCareRelease,
    *,
    settings: Settings,
    on_date: date | None = None,
) -> None:
    spec = PURPOSE_SPECS.get(release.release_key)
    if spec is None:
        raise IntelligenceReleaseError("unknown_purpose_release")
    provenance, payload = _verify_historical_release_integrity(
        release,
        on_date=on_date,
    )
    source_checksums = purpose_source_checksums(release.release_key)
    if provenance.get("source_checksums") != source_checksums:
        raise IntelligenceReleaseError("release_source_checksum_drift")
    if release.source_checksum_sha256 != canonical_checksum(source_checksums):
        raise IntelligenceReleaseError("release_source_checksum_drift")
    current_evaluation_checksums = evaluation_checksums()
    if provenance.get("evaluation_checksums") != current_evaluation_checksums:
        raise IntelligenceReleaseError("release_evaluation_checksum_drift")
    runtime_contract = purpose_runtime_contract(release.release_key, settings)
    if provenance.get("runtime_contract") != runtime_contract:
        raise IntelligenceReleaseError("purpose_or_model_release_mismatch")
    if provenance.get("runtime_contract_checksum_sha256") != canonical_checksum(runtime_contract):
        raise IntelligenceReleaseError("runtime_contract_checksum_drift")
    if (
        payload.get("source_checksums") != source_checksums
        or payload.get("evaluation_checksums") != current_evaluation_checksums
    ):
        raise IntelligenceReleaseError("release_payload_checksum_drift")
    if payload.get("runtime_contract") != runtime_contract:
        raise IntelligenceReleaseError("purpose_or_model_release_mismatch")


def active_intelligence_release(
    db: Session,
    *,
    release_key: str,
    settings: Settings,
) -> IntelligenceReleaseBinding:
    pointer = db.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == release_key,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    release = db.get(GovernedCareRelease, pointer.release_id) if pointer else None
    if release is None:
        raise IntelligenceReleaseError("inactive_release")
    verify_intelligence_release(release, settings=settings)
    return IntelligenceReleaseBinding(
        release_id=release.id,
        release_key=release_key,
        version=release.version,
        payload_checksum_sha256=release.payload_checksum_sha256,
    )


def _lock(session: Session, release_key: str) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"cei-release-operation:{release_key}:{SCOPE_KEY}"},
    )


def _operation_checksum(command: dict[str, object]) -> str:
    return canonical_checksum(command)


def _existing_operation(
    session: Session,
    *,
    release_key: str,
    idempotency_key: str,
    operation_checksum_sha256: str,
) -> GovernedCareReleaseActivation | None:
    existing = session.scalar(
        select(GovernedCareReleaseActivation).where(
            GovernedCareReleaseActivation.release_type == RELEASE_TYPE,
            GovernedCareReleaseActivation.release_key == release_key,
            GovernedCareReleaseActivation.scope_key == SCOPE_KEY,
            GovernedCareReleaseActivation.idempotency_key == idempotency_key,
        )
    )
    if existing is not None and existing.operation_checksum_sha256 != operation_checksum_sha256:
        raise IntelligenceReleaseError("idempotency_content_conflict")
    return existing


def _append_operation(
    session: Session,
    *,
    release: GovernedCareRelease,
    action: str,
    prior_release_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    idempotency_key: str,
    command: dict[str, object],
    evidence: dict[str, object],
) -> GovernedCareReleaseActivation:
    operation_checksum = _operation_checksum(command)
    event = GovernedCareReleaseActivation(
        release_id=release.id,
        release_type=RELEASE_TYPE,
        release_key=release.release_key,
        scope_key=SCOPE_KEY,
        action=action,
        prior_release_id=prior_release_id,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
        idempotency_key=idempotency_key,
        operation_checksum_sha256=operation_checksum,
        evidence_json={
            **evidence,
            "command": command,
            "content_free": True,
            "future_real_world_gates_preserved": True,
        },
    )
    session.add(event)
    session.flush()
    return event


def activate_intelligence_release(
    session: Session,
    *,
    release: GovernedCareRelease,
    settings: Settings,
    expected_version: str,
    expected_payload_checksum_sha256: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    on_date: date | None = None,
) -> ReleaseOperationResult:
    _lock(session, release.release_key)
    if release.version != expected_version:
        raise IntelligenceReleaseError("expected_version_conflict")
    if release.payload_checksum_sha256 != expected_payload_checksum_sha256:
        raise IntelligenceReleaseError("expected_checksum_conflict")
    verify_intelligence_release(release, settings=settings, on_date=on_date)
    command = {
        "action": "activate",
        "release_id": str(release.id),
        "expected_version": expected_version,
        "expected_payload_checksum_sha256": expected_payload_checksum_sha256,
        "reason_code": reason_code,
    }
    operation_checksum = _operation_checksum(command)
    existing = _existing_operation(
        session,
        release_key=release.release_key,
        idempotency_key=idempotency_key,
        operation_checksum_sha256=operation_checksum,
    )
    if existing is not None:
        return ReleaseOperationResult(existing, True)
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == release.release_key,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    prior_release_id = pointer.release_id if pointer else None
    if prior_release_id is not None and prior_release_id != release.id:
        if release.supersedes_release_id != prior_release_id:
            raise IntelligenceReleaseError("exact_predecessor_required")
        action = "supersede"
    elif prior_release_id == release.id:
        action = "activate_noop"
    else:
        action = "activate"
    event = _append_operation(
        session,
        release=release,
        action=action,
        prior_release_id=prior_release_id,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
        idempotency_key=idempotency_key,
        command=command,
        evidence={
            "stage": SCOPE_KEY,
            "payload_checksum_sha256": release.payload_checksum_sha256,
            "rollback_target": release.provenance_json["release_payload"]["rollback_target"],
        },
    )
    if pointer is None:
        session.add(
            GovernedActiveCareRelease(
                release_type=RELEASE_TYPE,
                release_key=release.release_key,
                scope_key=SCOPE_KEY,
                release_id=release.id,
                activation_event_id=event.id,
            )
        )
    elif pointer.release_id != release.id:
        pointer.release_id = release.id
        pointer.activation_event_id = event.id
    session.flush()
    return ReleaseOperationResult(event, False)


def engage_intelligence_kill_switch(
    session: Session,
    *,
    release: GovernedCareRelease,
    settings: Settings,
    expected_version: str,
    expected_payload_checksum_sha256: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
) -> ReleaseOperationResult:
    _lock(session, release.release_key)
    if release.version != expected_version:
        raise IntelligenceReleaseError("expected_version_conflict")
    if release.payload_checksum_sha256 != expected_payload_checksum_sha256:
        raise IntelligenceReleaseError("expected_checksum_conflict")
    verify_intelligence_release(release, settings=settings)
    command = {
        "action": "kill_switch",
        "release_id": str(release.id),
        "expected_version": expected_version,
        "expected_payload_checksum_sha256": expected_payload_checksum_sha256,
        "reason_code": reason_code,
    }
    checksum = _operation_checksum(command)
    existing = _existing_operation(
        session,
        release_key=release.release_key,
        idempotency_key=idempotency_key,
        operation_checksum_sha256=checksum,
    )
    if existing is not None:
        return ReleaseOperationResult(existing, True)
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == release.release_key,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if pointer is None or pointer.release_id != release.id:
        raise IntelligenceReleaseError("expected_active_release_conflict")
    event = _append_operation(
        session,
        release=release,
        action="kill_switch",
        prior_release_id=release.id,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
        idempotency_key=idempotency_key,
        command=command,
        evidence={"active_pointer_removed": True},
    )
    session.delete(pointer)
    session.flush()
    return ReleaseOperationResult(event, False)


def rollback_intelligence_release(
    session: Session,
    *,
    current_release: GovernedCareRelease,
    rollback_target: GovernedCareRelease | None,
    settings: Settings,
    expected_current_version: str,
    expected_current_payload_checksum_sha256: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    on_date: date | None = None,
) -> ReleaseOperationResult:
    _lock(session, current_release.release_key)
    if current_release.version != expected_current_version:
        raise IntelligenceReleaseError("expected_version_conflict")
    if current_release.payload_checksum_sha256 != expected_current_payload_checksum_sha256:
        raise IntelligenceReleaseError("expected_checksum_conflict")
    verify_intelligence_release(current_release, settings=settings, on_date=on_date)
    target_value = str(rollback_target.id) if rollback_target else FIXED_FALLBACK_TARGET
    command = {
        "action": "rollback",
        "release_id": str(current_release.id),
        "expected_version": expected_current_version,
        "expected_payload_checksum_sha256": expected_current_payload_checksum_sha256,
        "rollback_target": target_value,
        "reason_code": reason_code,
    }
    checksum = _operation_checksum(command)
    existing = _existing_operation(
        session,
        release_key=current_release.release_key,
        idempotency_key=idempotency_key,
        operation_checksum_sha256=checksum,
    )
    if existing is not None:
        return ReleaseOperationResult(existing, True)
    pointer = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == RELEASE_TYPE,
            GovernedActiveCareRelease.release_key == current_release.release_key,
            GovernedActiveCareRelease.scope_key == SCOPE_KEY,
        )
    )
    if pointer is None or pointer.release_id != current_release.id:
        raise IntelligenceReleaseError("expected_active_release_conflict")
    declared_target = current_release.provenance_json["release_payload"].get("rollback_target")
    if rollback_target is None:
        if (
            current_release.supersedes_release_id is not None
            or declared_target != FIXED_FALLBACK_TARGET
        ):
            raise IntelligenceReleaseError("exact_rollback_target_required")
        event = _append_operation(
            session,
            release=current_release,
            action="rollback_to_fallback",
            prior_release_id=current_release.id,
            actor_user_id=actor_user_id,
            reason_code=reason_code,
            idempotency_key=idempotency_key,
            command=command,
            evidence={
                "rollback_target": FIXED_FALLBACK_TARGET,
                "active_pointer_removed": True,
            },
        )
        session.delete(pointer)
    else:
        if (
            rollback_target.release_key != current_release.release_key
            or current_release.supersedes_release_id != rollback_target.id
            or declared_target != rollback_target.version
        ):
            raise IntelligenceReleaseError("exact_rollback_target_required")
        _verify_historical_release_integrity(rollback_target, on_date=on_date)
        event = _append_operation(
            session,
            release=rollback_target,
            action="rollback",
            prior_release_id=current_release.id,
            actor_user_id=actor_user_id,
            reason_code=reason_code,
            idempotency_key=idempotency_key,
            command=command,
            evidence={
                "rolled_back_from_release_id": str(current_release.id),
                "rollback_target_release_id": str(rollback_target.id),
                "matching_source_deployment_required_for_readiness": True,
            },
        )
        pointer.release_id = rollback_target.id
        pointer.activation_event_id = event.id
    session.flush()
    return ReleaseOperationResult(event, False)


def intelligence_readiness(db: Session, settings: Settings) -> dict[str, str]:
    purposes = {
        "primary": (
            settings.clinical_event_intelligence_primary_enabled,
            settings.clinical_event_intelligence_primary_kill_switch,
            PRIMARY_RELEASE_KEY,
        ),
        "critic": (
            settings.clinical_event_intelligence_critic_enabled,
            settings.clinical_event_intelligence_critic_kill_switch,
            CRITIC_RELEASE_KEY,
        ),
        "explanation": (
            settings.clinical_event_intelligence_explanation_enabled,
            settings.clinical_event_intelligence_explanation_kill_switch,
            EXPLANATION_RELEASE_KEY,
        ),
    }
    result: dict[str, str] = {}
    for purpose, (enabled, killed, key) in purposes.items():
        if not enabled:
            result[purpose] = "disabled"
        elif killed:
            result[purpose] = "kill_switched"
        else:
            try:
                active_intelligence_release(db, release_key=key, settings=settings)
            except IntelligenceReleaseError as exc:
                result[purpose] = str(exc)
            else:
                result[purpose] = "ready"
    return result


PurposeAction = Literal["activate", "kill_switch", "rollback"]
