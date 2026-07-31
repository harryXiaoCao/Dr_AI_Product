"""Register corrected pending v3 and independent Slice D synthetic-stage evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.expected_care_candidates import (
    MODEL_CONFIGURATION_VERSION as CANDIDATE_MODEL_VERSION,
)
from app.expected_care_candidates import (
    OUTPUT_SCHEMA_VERSION as CANDIDATE_SCHEMA_VERSION,
)
from app.expected_care_candidates import PROMPT_VERSION as CANDIDATE_PROMPT_VERSION
from app.expected_care_candidates import (
    PURPOSE_CODE as CANDIDATE_PURPOSE_CODE,
)
from app.expected_care_candidates import (
    PURPOSE_CONTRACT_VERSION as CANDIDATE_CONTRACT_VERSION,
)
from app.expected_care_candidates import ExpectedCareCandidateOutput
from app.expected_care_comparison import _checksum
from app.expected_care_explanations import (
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
    ExpectedCareExplanationOutput,
)
from app.expected_care_release_operations import (
    mark_release_unsuitable,
    register_early_stage_waivers,
)
from app.models import (
    ExpectedCareExplanationRelease,
    ExpectedCareExplanationReleaseEvent,
    GovernedCareRelease,
    GovernedCareReleaseReview,
)

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = (
    API_ROOT.parents[1]
    if API_ROOT.name == "api" and API_ROOT.parent.name == "services"
    else API_ROOT
)
F_SUITE = REPO_ROOT / "evaluation/expected_care/frozen_suite.v1.json"
F_RESULT = REPO_ROOT / "evaluation/expected_care/results/20260726T141758Z.sanitized.json"
D_SUITE = REPO_ROOT / "evaluation/expected_care_candidate/frozen_suite.v1.json"
D_RESULT = REPO_ROOT / "evaluation/expected_care_candidate/results/20260726T142027Z.sanitized.json"
F_RELEASE = (
    REPO_ROOT / "evaluation/expected_care/releases/expected-care-role-explanation.v3.pending.json"
)
F_V1_RELEASE = (
    REPO_ROOT / "evaluation/expected_care/releases/expected-care-role-explanation.v1.pending.json"
)
F_V2_RELEASE = (
    REPO_ROOT / "evaluation/expected_care/releases/expected-care-role-explanation.v2.pending.json"
)
F_V1_RESULT = REPO_ROOT / "evaluation/expected_care/results/20260726T110441Z.sanitized.json"
F_V2_RESULT = REPO_ROOT / "evaluation/expected_care/results/20260726T111243Z.sanitized.json"
D_RELEASE = (
    REPO_ROOT
    / "evaluation/expected_care_candidate/releases/expected-care-candidate.v1.pending.json"
)
EXPLANATION_SOURCE = REPO_ROOT / "services/api/app/expected_care_explanations.py"
COMPARISON_SOURCE = REPO_ROOT / "services/api/app/expected_care_comparison.py"
CANDIDATE_SOURCE = REPO_ROOT / "services/api/app/expected_care_candidates.py"
REVIEWS = (
    "clinical",
    "pricing",
    "native_simplified_chinese",
    "privacy",
    "security",
    "legal",
    "payer_workflow",
    "regulatory",
)
WAIVER_STATUS = "product_owner_waived_for_current_stage"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_immutable(path: Path, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != encoded:
            raise SystemExit(f"Immutable release artifact conflicts: {path}")
        return
    path.write_text(encoded)


def _register_historical_explanation_release(
    db,
    *,
    artifact_path: Path,
    result_path: Path,
    predecessor: ExpectedCareExplanationRelease | None,
) -> ExpectedCareExplanationRelease:
    """Register immutable predecessor evidence without comparing it to new source."""

    artifact = json.loads(artifact_path.read_text())
    if (
        artifact["release_key"] != "expected-care-role-explanation"
        or artifact["evaluation_result_checksum_sha256"] != _file_checksum(result_path)
        or artifact["source_checksums"]["sanitized_result_file_sha256"]
        != _file_checksum(result_path)
        or artifact["activation_state"] != "blocked_pending_external_reviews"
        or artifact["kill_switch_state"] != "on"
    ):
        raise SystemExit(f"Historical artifact integrity failed: {artifact_path}")
    existing = db.scalar(
        select(ExpectedCareExplanationRelease).where(
            ExpectedCareExplanationRelease.release_key == artifact["release_key"],
            ExpectedCareExplanationRelease.version == artifact["version"],
        )
    )
    if existing is not None:
        if existing.source_checksums_json != artifact["source_checksums"]:
            raise SystemExit(f"Historical release conflict: {artifact_path}")
        return existing
    expected_predecessor = artifact.get("predecessor_release_version")
    if expected_predecessor != (predecessor.version if predecessor else None):
        raise SystemExit(f"Historical predecessor mismatch: {artifact_path}")
    release = ExpectedCareExplanationRelease(
        predecessor_release_id=predecessor.id if predecessor else None,
        rollback_target_release_id=None,
        release_key=artifact["release_key"],
        version=artifact["version"],
        purpose_code=artifact["purpose_code"],
        purpose_contract_version=artifact["purpose_contract_version"],
        schema_version=artifact["schema_version"],
        prompt_version=artifact["prompt_version"],
        model_configuration_version=artifact["model_configuration_version"],
        provider=artifact["provider"],
        model=artifact["model"],
        source_checksums_json=artifact["source_checksums"],
        evaluation_manifest_checksum_sha256=artifact["evaluation_manifest_checksum_sha256"],
        evaluation_result_checksum_sha256=artifact["evaluation_result_checksum_sha256"],
        review_requirements_json=artifact["review_requirements"],
        machine_gates_json=artifact["machine_gates"],
        activation_state=artifact["activation_state"],
        kill_switch_state=artifact["kill_switch_state"],
    )
    db.add(release)
    db.flush()
    db.add(
        ExpectedCareExplanationReleaseEvent(
            release_id=release.id,
            actor_user_id=None,
            event_type="release_registered_pending",
            evidence_json={
                "historical_artifact_checksum_sha256": _file_checksum(artifact_path),
                "historical_release_unchanged": True,
                "content_free": True,
            },
        )
    )
    db.flush()
    return release


def main() -> None:
    f_result = json.loads(F_RESULT.read_text())
    d_result = json.loads(D_RESULT.read_text())
    if not f_result["machine_gate_passed"] or not d_result["machine_gate_passed"]:
        raise SystemExit("A mandatory executable machine gate did not pass.")
    reviews = [
        {
            "review_type": review_type,
            "status": WAIVER_STATUS,
            "scope": "early_synthetic_development_and_controlled_staging_only",
            "future_real_world_gate_preserved": True,
        }
        for review_type in REVIEWS
    ]
    f_checksums = {
        "frozen_suite_file_sha256": _file_checksum(F_SUITE),
        "sanitized_result_file_sha256": _file_checksum(F_RESULT),
        "explanation_source_sha256": _file_checksum(EXPLANATION_SOURCE),
        "comparison_source_sha256": _file_checksum(COMPARISON_SOURCE),
        "output_schema_sha256": _checksum(ExpectedCareExplanationOutput.model_json_schema()),
    }
    f_artifact = {
        "release_key": "expected-care-role-explanation",
        "version": "v3-2026-07-26",
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "source_checksums": f_checksums,
        "evaluation_manifest_checksum_sha256": f_result["suite_checksum_sha256"],
        "evaluation_result_checksum_sha256": _file_checksum(F_RESULT),
        "review_requirements": reviews,
        "machine_gates": f_result["machine_gates"],
        "activation_state": "pending_controlled_synthetic_staging",
        "kill_switch_state": "on",
        "predecessor_release_version": "v2-2026-07-26",
        "rollback_target": "fixed_structured_fallback",
        "real_world_activation_allowed": False,
    }
    _write_immutable(F_RELEASE, f_artifact)

    d_checksums = {
        "frozen_suite_file_sha256": _file_checksum(D_SUITE),
        "sanitized_result_file_sha256": _file_checksum(D_RESULT),
        "candidate_source_sha256": _file_checksum(CANDIDATE_SOURCE),
        "output_schema_sha256": _checksum(ExpectedCareCandidateOutput.model_json_schema()),
    }
    d_artifact = {
        "release_key": "expected-care-candidate",
        "version": "v1-synthetic-stage-2026-07-26",
        "purpose_code": CANDIDATE_PURPOSE_CODE,
        "purpose_contract_version": CANDIDATE_CONTRACT_VERSION,
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "prompt_version": CANDIDATE_PROMPT_VERSION,
        "model_configuration_version": CANDIDATE_MODEL_VERSION,
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "source_checksums": d_checksums,
        "evaluation_manifest_checksum_sha256": d_result["suite_checksum_sha256"],
        "evaluation_result_checksum_sha256": _file_checksum(D_RESULT),
        "review_requirements": reviews,
        "machine_gates": d_result["machine_gates"],
        "activation_state": "pending_controlled_synthetic_staging",
        "kill_switch_state": "on",
        "predecessor_release_version": None,
        "rollback_target": "fixed_safe_fallback",
        "real_world_activation_allowed": False,
    }
    _write_immutable(D_RELEASE, d_artifact)

    with SessionLocal() as db:
        v1 = _register_historical_explanation_release(
            db,
            artifact_path=F_V1_RELEASE,
            result_path=F_V1_RESULT,
            predecessor=None,
        )
        v2 = _register_historical_explanation_release(
            db,
            artifact_path=F_V2_RELEASE,
            result_path=F_V2_RESULT,
            predecessor=v1,
        )
        mark_release_unsuitable(
            db,
            release=v2,
            expected_version=v2.version,
            actor_user_id=None,
            idempotency_key="v2-validator-and-executable-gate-correction",
            reason_codes=[
                "factual_contradiction_validator_gap",
                "hard_coded_machine_gate_counts",
            ],
        )
        v3 = db.scalar(
            select(ExpectedCareExplanationRelease).where(
                ExpectedCareExplanationRelease.release_key == f_artifact["release_key"],
                ExpectedCareExplanationRelease.version == f_artifact["version"],
            )
        )
        if v3 is None:
            v3 = ExpectedCareExplanationRelease(
                predecessor_release_id=v2.id,
                rollback_target_release_id=None,
                release_key=str(f_artifact["release_key"]),
                version=str(f_artifact["version"]),
                purpose_code=PURPOSE_CODE,
                purpose_contract_version=PURPOSE_CONTRACT_VERSION,
                schema_version=OUTPUT_SCHEMA_VERSION,
                prompt_version=PROMPT_VERSION,
                model_configuration_version=MODEL_CONFIGURATION_VERSION,
                provider="deepseek",
                model="deepseek-v4-flash",
                source_checksums_json=f_checksums,
                evaluation_manifest_checksum_sha256=str(
                    f_artifact["evaluation_manifest_checksum_sha256"]
                ),
                evaluation_result_checksum_sha256=str(
                    f_artifact["evaluation_result_checksum_sha256"]
                ),
                review_requirements_json=reviews,
                machine_gates_json=f_result["machine_gates"],
                activation_state="pending_controlled_synthetic_staging",
                kill_switch_state="on",
            )
            db.add(v3)
            db.flush()
            db.add(
                ExpectedCareExplanationReleaseEvent(
                    release_id=v3.id,
                    actor_user_id=None,
                    event_type="release_registered_pending",
                    evidence_json={
                        "stage": "early_synthetic_controlled_staging",
                        "rollback_target": "fixed_structured_fallback",
                        "external_approval_fabricated": False,
                    },
                )
            )
        register_early_stage_waivers(
            db,
            release=v3,
            expected_version=v3.version,
            actor_user_id=None,
            idempotency_key="v3-early-stage-waivers",
            statuses={review_type: WAIVER_STATUS for review_type in REVIEWS},
        )

        d_release = db.scalar(
            select(GovernedCareRelease).where(
                GovernedCareRelease.release_type == "ai_purpose",
                GovernedCareRelease.release_key == "expected-care-candidate",
                GovernedCareRelease.version == d_artifact["version"],
            )
        )
        if d_release is None:
            payload_checksum = _checksum(d_artifact)
            d_release = GovernedCareRelease(
                release_type="ai_purpose",
                release_key="expected-care-candidate",
                version=str(d_artifact["version"]),
                schema_version=CANDIDATE_SCHEMA_VERSION,
                lifecycle_status="reviewed",
                jurisdiction="synthetic_only",
                region="Synthetic Province",
                facility_scope_json={"stage": "controlled_synthetic_staging"},
                currency="CNY",
                effective_from=date(2026, 7, 26),
                effective_to=date(2027, 7, 25),
                source_authority="Dr. AI synthetic product fixture",
                source_locator=(
                    "urn:dr-ai:synthetic-ai-purpose:expected-care-candidate:"
                    f"{d_artifact['version']}"
                ),
                retrieved_at=datetime.now(UTC),
                source_checksum_sha256=_file_checksum(D_RESULT),
                payload_checksum_sha256=payload_checksum,
                provenance_json={
                    "data_class": "wholly_synthetic",
                    "purpose_code": CANDIDATE_PURPOSE_CODE,
                    "source_checksums": d_checksums,
                    "machine_gates": d_result["machine_gates"],
                    "activation_state": "pending_controlled_synthetic_staging",
                    "kill_switch_state": "on",
                    "rollback_target": "fixed_safe_fallback",
                },
                required_review_types_json=list(REVIEWS),
                rights_status=WAIVER_STATUS,
                storage_allowed=True,
                derivation_allowed=True,
                redistribution_allowed=False,
                provider_transmission_allowed=True,
                last_verified_on=date(2026, 7, 26),
                next_review_on=date(2027, 1, 26),
            )
            db.add(d_release)
            db.flush()
            for review_type in REVIEWS:
                d_release.reviews.append(
                    GovernedCareReleaseReview(
                        review_type=review_type,
                        decision=WAIVER_STATUS,
                        reviewer_name="Dr. AI product-owner early-stage policy",
                        reviewed_payload_checksum_sha256=payload_checksum,
                        rationale=(
                            "Not an external or professional approval. Applies only "
                            "to wholly synthetic development and controlled staging; "
                            "the future real-world gate remains required."
                        ),
                    )
                )
        db.commit()
        print(
            json.dumps(
                {
                    "slice_f_v3_release_id": str(v3.id),
                    "slice_d_release_id": str(d_release.id),
                    "slice_f_artifact": str(F_RELEASE.relative_to(REPO_ROOT)),
                    "slice_d_artifact": str(D_RELEASE.relative_to(REPO_ROOT)),
                }
            )
        )


if __name__ == "__main__":
    main()
