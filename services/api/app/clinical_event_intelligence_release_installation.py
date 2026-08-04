"""Build and idempotently install the three synthetic-stage CEI releases."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import canonical_checksum
from app.clinical_event_intelligence_governance import (
    ACCEPTED_SYNTHETIC_REVIEW_STATES,
    EVALUATION_PATHS,
    EXPLANATION_RELEASE_KEY,
    FIXED_FALLBACK_TARGET,
    PRIMARY_RELEASE_KEY,
    PURPOSE_SPECS,
    RELEASE_TYPE,
    SCOPE_KEY,
    evaluation_checksums,
    purpose_runtime_contract,
    purpose_source_checksums,
    verify_intelligence_release,
)
from app.config import Settings
from app.models import (
    GovernedCareRelease,
    GovernedCareReleaseActivation,
    GovernedCareReleaseReview,
)

RELEASE_VERSION = "v1-controlled-synthetic-20260802"
WAIVER_STATUS = "product_owner_waived_for_current_stage"
REVIEW_TYPES = (
    "clinical",
    "pricing",
    "native_simplified_chinese",
    "privacy",
    "security",
    "legal",
    "payer_workflow",
    "regulatory",
)
DEFAULT_ARTIFACT_ROOT = EVALUATION_PATHS["evaluation_manifest_checksum_sha256"].parent / "releases"
REPO_ROOT = Path(__file__).resolve().parents[3]


class IntelligenceReleaseInstallationError(ValueError):
    pass


def _read_evidence() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    suite = json.loads(
        EVALUATION_PATHS["evaluation_manifest_checksum_sha256"].read_text(encoding="utf-8")
    )
    verification = json.loads(
        EVALUATION_PATHS["verification_matrix_checksum_sha256"].read_text(encoding="utf-8")
    )
    provider_free = json.loads(
        EVALUATION_PATHS["provider_free_result_checksum_sha256"].read_text(encoding="utf-8")
    )
    live = json.loads(EVALUATION_PATHS["live_result_checksum_sha256"].read_text(encoding="utf-8"))
    if not all(isinstance(value, dict) for value in (suite, verification, provider_free, live)):
        raise IntelligenceReleaseInstallationError("evaluation_evidence_invalid")
    return suite, verification, {"provider_free": provider_free, "live": live}


def _provider_evidence_matches(
    live: dict[str, object],
    *,
    release_key: str,
    provider: str,
    model: str,
) -> bool:
    results = live.get("results")
    if not isinstance(results, list):
        return False
    if release_key == EXPLANATION_RELEASE_KEY:
        return any(
            isinstance(result, dict)
            and isinstance((explanation := result.get("explanation")), dict)
            and explanation.get("display_mode") == "validated_fact_selection"
            and any(
                isinstance(row, dict)
                and row.get("provider") == provider
                and row.get("model") == model
                for row in explanation.get("provider_diagnostics", [])
            )
            for result in results
        )
    purpose = "primary" if release_key == PRIMARY_RELEASE_KEY else "critic"
    return any(
        isinstance(result, dict)
        and any(
            isinstance(row, dict)
            and row.get("purpose") == purpose
            and row.get("provider") == provider
            and row.get("model") == model
            for row in result.get("provider_usage", [])
        )
        for result in results
    )


def derive_machine_gates(
    *,
    release_key: str,
    settings: Settings,
) -> dict[str, bool]:
    suite, verification, evidence = _read_evidence()
    provider_free = evidence["provider_free"]
    live = evidence["live"]
    required_adversarial = {str(value) for value in suite.get("adversarial_cases", [])}
    verified = {
        str(row.get("case_id"))
        for row in verification.get("cases", [])
        if isinstance(row, dict) and row.get("status") == "passed"
    }
    runtime = purpose_runtime_contract(release_key, settings)
    return {
        "provider_free_combined_verification": (
            provider_free.get("passed") is True
            and provider_free.get("combined_verification_passed") is True
            and provider_free.get("scenario_contract_passed") is True
            and provider_free.get("unverified_adversarial_cases") == []
        ),
        "live_combined_verification": (
            live.get("passed") is True
            and live.get("combined_verification_passed") is True
            and live.get("scenario_contract_passed") is True
            and live.get("unverified_adversarial_cases") == []
        ),
        "synthetic_only_evidence": (
            suite.get("data_class") == "wholly_synthetic"
            and provider_free.get("data_class") == "wholly_synthetic"
            and live.get("data_class") == "wholly_synthetic"
        ),
        "adversarial_matrix_complete": (
            verification.get("execution", {}).get("status") == "passed"
            and bool(required_adversarial)
            and required_adversarial <= verified
        ),
        "provider_model_verified": _provider_evidence_matches(
            live,
            release_key=release_key,
            provider=str(runtime["provider"]),
            model=str(runtime["model"]),
        ),
        "no_evaluation_side_effects": (
            provider_free.get("no_database_writes") is True
            and provider_free.get("no_release_activation") is True
            and live.get("no_database_writes") is True
            and live.get("no_release_activation") is True
        ),
        "sanitized_no_raw_provider_content": (
            provider_free.get("raw_provider_content_in_sanitized_result") is False
            and live.get("raw_provider_content_in_sanitized_result") is False
        ),
        "mandatory_threshold_contract_present": bool(suite.get("mandatory_machine_thresholds")),
        "future_real_world_gates_preserved": (
            suite.get("future_real_world_gates_preserved") is True
        ),
    }


def build_release_payload(
    *,
    release_key: str,
    settings: Settings,
    version: str = RELEASE_VERSION,
    predecessor_version: str | None = None,
) -> dict[str, object]:
    spec = PURPOSE_SPECS.get(release_key)
    if spec is None:
        raise IntelligenceReleaseInstallationError("unknown_purpose_release")
    gates = derive_machine_gates(release_key=release_key, settings=settings)
    if not all(gates.values()):
        failed = sorted(key for key, passed in gates.items() if not passed)
        raise IntelligenceReleaseInstallationError(
            f"mandatory_machine_gate_failed:{','.join(failed)}"
        )
    runtime = purpose_runtime_contract(release_key, settings)
    return {
        "release_type": RELEASE_TYPE,
        "release_key": release_key,
        "version": version,
        "schema_version": spec.schema_version,
        "runtime_contract": runtime,
        "runtime_contract_checksum_sha256": canonical_checksum(runtime),
        "source_checksums": purpose_source_checksums(release_key),
        "evaluation_checksums": evaluation_checksums(),
        "machine_gates": gates,
        "review_types": list(REVIEW_TYPES),
        "stage_review_status": WAIVER_STATUS,
        "data_class": "wholly_synthetic",
        "scope_key": SCOPE_KEY,
        "effective_from": "2026-08-02",
        "effective_to": "2027-08-01",
        "next_review_on": "2027-02-01",
        "provider_transmission_allowed": True,
        "storage_allowed": True,
        "derivation_allowed": True,
        "redistribution_allowed": False,
        "predecessor_version": predecessor_version,
        "rollback_target": predecessor_version or FIXED_FALLBACK_TARGET,
        "real_world_activation_allowed": False,
        "future_real_world_gates_preserved": True,
    }


def _write_immutable_artifact(path: Path, payload: dict[str, object]) -> None:
    artifact = {
        **payload,
        "source_checksum_sha256": canonical_checksum(payload["source_checksums"]),
        "payload_checksum_sha256": canonical_checksum(payload),
    }
    encoded = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise IntelligenceReleaseInstallationError("immutable_release_artifact_conflict")
        return
    path.write_text(encoded, encoding="utf-8")


def _artifact_locator(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def install_intelligence_releases(
    session: Session,
    *,
    settings: Settings,
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
    version: str = RELEASE_VERSION,
    predecessor_version: str | None = None,
) -> list[GovernedCareRelease]:
    installed: list[GovernedCareRelease] = []
    for release_key in PURPOSE_SPECS:
        payload = build_release_payload(
            release_key=release_key,
            settings=settings,
            version=version,
            predecessor_version=predecessor_version,
        )
        payload_checksum = canonical_checksum(payload)
        source_checksum = canonical_checksum(payload["source_checksums"])
        artifact_path = artifact_root / f"{release_key}.{version}.json"
        _write_immutable_artifact(artifact_path, payload)
        existing = session.scalar(
            select(GovernedCareRelease).where(
                GovernedCareRelease.release_type == RELEASE_TYPE,
                GovernedCareRelease.release_key == release_key,
                GovernedCareRelease.version == version,
            )
        )
        if existing is not None:
            if (
                existing.payload_checksum_sha256 != payload_checksum
                or existing.source_checksum_sha256 != source_checksum
            ):
                raise IntelligenceReleaseInstallationError("immutable_release_conflict")
            verify_intelligence_release(existing, settings=settings)
            installed.append(existing)
            continue
        predecessor = None
        predecessor_version = payload["predecessor_version"]
        if predecessor_version:
            predecessor = session.scalar(
                select(GovernedCareRelease).where(
                    GovernedCareRelease.release_type == RELEASE_TYPE,
                    GovernedCareRelease.release_key == release_key,
                    GovernedCareRelease.version == predecessor_version,
                )
            )
            if predecessor is None:
                raise IntelligenceReleaseInstallationError("predecessor_release_not_found")
        release = GovernedCareRelease(
            release_type=RELEASE_TYPE,
            release_key=release_key,
            version=version,
            schema_version=str(payload["schema_version"]),
            lifecycle_status="reviewed",
            jurisdiction="synthetic_only",
            region="Synthetic China",
            facility_scope_json={"stage": SCOPE_KEY, "synthetic_only": True},
            currency="CNY",
            effective_from=date.fromisoformat(str(payload["effective_from"])),
            effective_to=date.fromisoformat(str(payload["effective_to"])),
            source_authority="Dr. AI wholly synthetic CEI evaluation package",
            source_locator=f"urn:dr-ai:synthetic-ai-purpose:{release_key}:{version}",
            retrieved_at=datetime.now(UTC),
            source_checksum_sha256=source_checksum,
            payload_checksum_sha256=payload_checksum,
            provenance_json={
                "data_class": "wholly_synthetic",
                "scope_key": SCOPE_KEY,
                "runtime_contract": payload["runtime_contract"],
                "runtime_contract_checksum_sha256": payload["runtime_contract_checksum_sha256"],
                "source_checksums": payload["source_checksums"],
                "evaluation_checksums": payload["evaluation_checksums"],
                "machine_gates": payload["machine_gates"],
                "release_payload": payload,
                "stage_review_status": WAIVER_STATUS,
                "future_real_world_gates_preserved": True,
            },
            required_review_types_json=list(REVIEW_TYPES),
            rights_status=WAIVER_STATUS,
            storage_allowed=True,
            derivation_allowed=True,
            redistribution_allowed=False,
            provider_transmission_allowed=True,
            last_verified_on=date(2026, 8, 2),
            next_review_on=date.fromisoformat(str(payload["next_review_on"])),
            supersedes_release_id=predecessor.id if predecessor else None,
        )
        session.add(release)
        session.flush()
        for review_type in REVIEW_TYPES:
            session.add(
                GovernedCareReleaseReview(
                    release_id=release.id,
                    review_type=review_type,
                    decision=WAIVER_STATUS,
                    reviewer_name="Dr. AI product-owner early synthetic-stage policy",
                    reviewed_payload_checksum_sha256=payload_checksum,
                    rationale=(
                        "Wholly synthetic local development and controlled staging only; "
                        "this is not external professional approval."
                    ),
                )
            )
        session.flush()
        registration_command = {
            "action": "register",
            "release_id": str(release.id),
            "version": version,
            "payload_checksum_sha256": payload_checksum,
        }
        session.add(
            GovernedCareReleaseActivation(
                release_id=release.id,
                release_type=RELEASE_TYPE,
                release_key=release_key,
                scope_key=SCOPE_KEY,
                action="register",
                prior_release_id=None,
                actor_user_id=None,
                reason_code="synthetic_release_install",
                idempotency_key=f"install:{release_key}:{version}",
                operation_checksum_sha256=canonical_checksum(registration_command),
                evidence_json={
                    "command": registration_command,
                    "artifact_path": _artifact_locator(artifact_path),
                    "rollback_target": FIXED_FALLBACK_TARGET,
                    "content_free": True,
                    "future_real_world_gates_preserved": True,
                },
            )
        )
        session.flush()
        verify_intelligence_release(release, settings=settings)
        installed.append(release)
    return installed


assert WAIVER_STATUS in ACCEPTED_SYNTHETIC_REVIEW_STATES
