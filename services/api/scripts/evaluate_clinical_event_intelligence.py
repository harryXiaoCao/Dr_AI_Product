"""Evaluate Clinical Event Intelligence against wholly synthetic frozen cases.

The default run is provider-free. ``--live`` performs one primary call and at
most one critic call per selected case. Provider content is written only to the
gitignored raw directory; the shareable result contains content-free evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.clinical_event_intelligence_contracts import (  # noqa: E402
    CEI_CRITIC_PURPOSE_CODE,
    CEI_CRITIC_SCHEMA_VERSION,
    CEI_OUTPUT_SCHEMA_VERSION,
    CEI_PURPOSE_CODE,
    CEI_PURPOSE_CONTRACT_VERSION,
    CriticOutput,
    FrozenClinicalEventSnapshot,
    FrozenFact,
    FrozenLocation,
    FrozenRequestedLine,
    RetrievalManifest,
    RetrievalSource,
    canonical_checksum,
)
from app.clinical_event_intelligence_explanations import (  # noqa: E402
    generate_role_explanation,
)
from app.clinical_event_intelligence_provider import (  # noqa: E402
    DeepSeekCriticIntelligenceProvider,
    DeepSeekPrimaryIntelligenceProvider,
    IntelligenceProviderError,
    IntelligenceProviderResponse,
)
from app.clinical_event_intelligence_reconciliation import reconcile_critic  # noqa: E402
from app.clinical_event_intelligence_validation import (  # noqa: E402
    IntelligenceValidationError,
    normalize_tier5_uncertainty,
    validate_primary_output,
)
from app.config import get_settings  # noqa: E402

REPO_ROOT = API_ROOT.parents[1]
DEFAULT_SUITE = REPO_ROOT / "evaluation/clinical_event_intelligence/frozen_suite.v1.json"
DEFAULT_RESULTS = REPO_ROOT / "evaluation/clinical_event_intelligence/results"
DEFAULT_VERIFICATION_EVIDENCE = (
    REPO_ROOT / "evaluation/clinical_event_intelligence/verification_matrix.v1.json"
)
RAW_DIRECTORY_NAME = "raw"


def _snapshot(case: dict[str, object]) -> FrozenClinicalEventSnapshot:
    case_id = str(case["case_id"])
    line_count = int(case["requested_lines"])
    lines = [
        FrozenRequestedLine(
            requested_line_id=f"{case_id}:line:{index}",
            item_type=str(case["family"]),
            label=f"Synthetic {case['family']} item {index}",
            code_system="DR-AI-SYNTHETIC",
            service_code=f"SYN-{str(case['family']).upper()}-{index:02d}",
            quantity=1,
            unit="item",
            requested_minor=10_000 * index,
            actual_cost_minor=10_000 * index,
            currency="CNY",
            service_date="2026-08-01",
        )
        for index in range(1, line_count + 1)
    ]
    location_state = str(case.get("required_location_state", "provider_organization"))
    if location_state == "conflicting_structured_records":
        location = FrozenLocation(
            jurisdiction_code=None,
            province_code=None,
            city_code=None,
            facility_level=None,
            source="conflicting_structured_records",
            complete=False,
        )
    else:
        location = FrozenLocation(
            jurisdiction_code="CN",
            province_code="CN-SYN",
            city_code="CN-SYN-001",
            facility_level="synthetic_tertiary",
            source="provider_organization",
            complete=True,
        )
    facts = [
        FrozenFact(
            fact_id=f"fact.{case_id}.synthetic",
            category="synthetic_case",
            value={"family": case["family"], "no_real_data": True},
            source_type="frozen_fixture",
            source_id=f"fixture:{case_id}",
            verification_state="verified",
        )
    ]
    missing = ["Synthetic documentation gap"] if case.get("required_missing_information") else []
    line_payload = [line.model_dump(mode="json") for line in lines]
    body = {
        "snapshot_version": 1,
        "payer_request_version": 1,
        "patient_id": f"synthetic-patient:{case_id}",
        "clinical_event_id": f"synthetic-event:{case_id}",
        "payer_request_id": f"synthetic-request:{case_id}",
        "encounter_date": "2026-08-01",
        "location": location.model_dump(mode="json"),
        "facts_used": [fact.model_dump(mode="json") for fact in facts],
        "facts_not_used": [],
        "requested_lines": line_payload,
        "missing_information": missing,
        "conflicting_information": (
            ["Structured facility records conflict"]
            if location_state == "conflicting_structured_records"
            else []
        ),
        "requested_item_set_checksum_sha256": canonical_checksum(line_payload),
    }
    return FrozenClinicalEventSnapshot(
        payer_request_version=1,
        patient_id=f"synthetic-patient:{case_id}",
        clinical_event_id=f"synthetic-event:{case_id}",
        payer_request_id=f"synthetic-request:{case_id}",
        encounter_date="2026-08-01",
        location=location,
        facts_used=facts,
        facts_not_used=[],
        missing_information=missing,
        conflicting_information=(
            ["Structured facility records conflict"]
            if location_state == "conflicting_structured_records"
            else []
        ),
        requested_lines=lines,
        requested_item_set_checksum_sha256=canonical_checksum(line_payload),
        snapshot_checksum_sha256=canonical_checksum(body),
    )


def _retrieval(case: dict[str, object], snapshot: FrozenClinicalEventSnapshot) -> RetrievalManifest:
    tier5 = int(case.get("required_cost_tier", 0)) == 5
    sources: list[RetrievalSource] = []
    if not tier5:
        price_payload = {
            "synthetic": True,
            "family": case["family"],
            "currency": "CNY",
            "price_items": [
                {
                    "code_system": line.code_system,
                    "service_code": line.service_code,
                    "unit": line.unit,
                    "currency": line.currency,
                    "amount_low_minor": max(0, line.requested_minor // 2),
                    "amount_high_minor": line.requested_minor * 2,
                }
                for line in snapshot.requested_lines
            ],
        }
        expected_tiers = {int(value) for value in case.get("expected_cost_tiers") or [2]}
        source_types = {2: "regional_reference", 3: "comparable_case", 4: "care_pathway"}
        for tier in sorted(expected_tiers):
            source_type = source_types[tier]
            payload = (
                price_payload
                if tier == 2
                else {
                    "synthetic": True,
                    "family": case["family"],
                    "analogous": True,
                    "cost_analogues": price_payload["price_items"],
                }
            )
            sources.append(
                RetrievalSource(
                    source_id=f"source:{case['case_id']}:tier:{tier}",
                    source_type=source_type,  # type: ignore[arg-type]
                    release_id=None,
                    release_version="v1-frozen-synthetic",
                    checksum_sha256=canonical_checksum(payload),
                    authority="Wholly synthetic evaluation fixture",
                    provider_transmission_allowed=True,
                    payload=payload,
                )
            )
    body = {
        "retrieval_contract_version": "clinical-event-intelligence-retrieval.v1",
        "authorization_scope_checksum_sha256": canonical_checksum(
            {"payer_request_id": snapshot.payer_request_id, "synthetic": True}
        ),
        "sources": [source.model_dump(mode="json") for source in sources],
        "missing_source_types": [] if sources else ["authoritative_price"],
    }
    return RetrievalManifest(**body, manifest_checksum_sha256=canonical_checksum(body))


def _primary_output(
    case: dict[str, object], snapshot: FrozenClinicalEventSnapshot, retrieval: RetrievalManifest
) -> dict[str, object]:
    pathway_types = case.get("required_pathway_types") or ["typical_first_line"]
    fact_id = snapshot.facts_used[0].fact_id
    pathways = [
        {
            "pathway_id": f"pathway:{case['case_id']}:{kind}",
            "pathway_type": kind,
            "trigger_fact_ids": [fact_id],
            "usefulness": "Wholly synthetic pathway hypothesis for contract evaluation.",
            "confidence": 60,
            "assumptions": ["Synthetic fixture only."],
            "limitations": ["Not a diagnosis, prescription, approval, or denial."],
            "items": [
                {
                    "item_key": f"predicted:{case['case_id']}:{kind}",
                    "label": "Synthetic predicted pathway item",
                    "category": str(case["family"]),
                    "service_code": None,
                    "quantity_low": 1,
                    "quantity_high": 2,
                    "unit": "item",
                    "currency": "CNY",
                    "cost_low_minor": 1_000,
                    "cost_high_minor": 3_000,
                    "rationale_fact_ids": [fact_id],
                }
            ],
        }
        for kind in pathway_types
    ]
    expected_tiers = list(case.get("expected_cost_tiers") or [])
    forced_tier = int(case.get("required_cost_tier", 0))
    assessments = []
    for index, line in enumerate(snapshot.requested_lines):
        tier = forced_tier or int(expected_tiers[index] if index < len(expected_tiers) else 2)
        model_only = tier == 5
        source_by_tier = {
            {"regional_reference": 2, "comparable_case": 3, "care_pathway": 4}[
                source.source_type
            ]: source.source_id
            for source in retrieval.sources
            if source.source_type in {"regional_reference", "comparable_case", "care_pathway"}
        }
        assessments.append(
            {
                "requested_line_id": line.requested_line_id,
                "usefulness": "Synthetic requested-line assessment with human review retained.",
                "mapped_pathway_ids": [pathways[0]["pathway_id"]],
                "scores": {
                    "clinical_fit": 70,
                    "evidence_support": 65,
                    "timing_sequence": 60,
                    "quantity_intensity": 55,
                    "documentation_completeness": 35
                    if case.get("required_missing_information")
                    else 70,
                    "cost_alignment": 50,
                },
                "estimated_quantity": {"low": 1, "high": 2, "unit": line.unit},
                "estimated_cost": {
                    "low_minor": 1_000,
                    "high_minor": 3_000 if not model_only else 12_000,
                    "currency": line.currency,
                    "provenance_tier": tier,
                    "source_ids": [] if model_only else [source_by_tier[tier]],
                    "is_model_only_exploratory": model_only,
                },
                "supporting_fact_ids": [fact_id],
                "contradicting_fact_ids": [],
                "missing_information": list(snapshot.missing_information),
                "alternatives": ["Human reviewer may consider the synthetic alternative pathway."],
                "confidence": "moderate",
                "brief_comment": "No score causes an automatic clinical or payer action.",
            }
        )
    return {
        "purpose_code": CEI_PURPOSE_CODE,
        "purpose_contract_version": CEI_PURPOSE_CONTRACT_VERSION,
        "schema_version": CEI_OUTPUT_SCHEMA_VERSION,
        "snapshot_checksum_sha256": snapshot.snapshot_checksum_sha256,
        "retrieval_manifest_checksum_sha256": retrieval.manifest_checksum_sha256,
        "pathways": pathways,
        "requested_item_assessments": assessments,
        "unresolved_questions": list(snapshot.missing_information),
        "overall_confidence": "moderate",
    }


def _critic_output(
    case: dict[str, object], snapshot: FrozenClinicalEventSnapshot, checksum: str
) -> dict[str, object]:
    expected = str(case.get("expected_disagreement_state", "agreement"))
    discrepancies = []
    if expected in {"partial_disagreement", "material_disagreement"}:
        discrepancies.append(
            {
                "requested_line_id": snapshot.requested_lines[0].requested_line_id,
                "category": "missing_information",
                "severity": "material" if expected == "material_disagreement" else "minor",
                "fact_ids": [snapshot.facts_used[0].fact_id],
                "concise_comment": "Synthetic critic discrepancy for deterministic evaluation.",
            }
        )
    return CriticOutput(
        purpose_code=CEI_CRITIC_PURPOSE_CODE,
        schema_version=CEI_CRITIC_SCHEMA_VERSION,
        snapshot_checksum_sha256=snapshot.snapshot_checksum_sha256,
        primary_output_checksum_sha256=checksum,
        discrepancies=discrepancies,
    ).model_dump(mode="json")


def _adversarial_observations(
    base: dict[str, object], snapshot: FrozenClinicalEventSnapshot, retrieval: RetrievalManifest
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []

    def execute(case_id: str, mutate, expected: str | tuple[str, ...]) -> None:
        value = deepcopy(base)
        mutate(value)
        reasons: list[str] = []
        try:
            validate_primary_output(value, snapshot=snapshot, retrieval=retrieval)
        except IntelligenceValidationError as exc:
            reasons = exc.reason_codes
        expected_reasons = (expected,) if isinstance(expected, str) else expected
        observations.append(
            {
                "case_id": case_id,
                "executed": True,
                "passed": any(reason in reasons for reason in expected_reasons),
                "reason_codes": reasons,
            }
        )

    execute(
        "duplicate_requested_line",
        lambda row: row["requested_item_assessments"].append(
            deepcopy(row["requested_item_assessments"][0])
        ),
        "duplicate_requested_line_assessment",
    )
    execute(
        "omitted_requested_line",
        lambda row: row["requested_item_assessments"].pop(),
        ("requested_line_coverage_mismatch", "malformed_schema"),
    )
    execute(
        "cross_request_line",
        lambda row: row["requested_item_assessments"][0].__setitem__(
            "requested_line_id", "other-request:line"
        ),
        "requested_line_coverage_mismatch",
    )
    execute(
        "malformed_primary_output",
        lambda row: row.__setitem__("unexpected", True),
        "malformed_schema",
    )
    execute(
        "unsupported_score",
        lambda row: row["requested_item_assessments"][0]["scores"].__setitem__("clinical_fit", 101),
        "malformed_schema",
    )
    execute(
        "reversed_quantity_range",
        lambda row: row["requested_item_assessments"][0].__setitem__(
            "estimated_quantity", {"low": 2, "high": 1, "unit": "item"}
        ),
        "malformed_schema",
    )
    execute(
        "reversed_cost_range",
        lambda row: row["requested_item_assessments"][0]["estimated_cost"].update(
            {"low_minor": 5000, "high_minor": 1000}
        ),
        "malformed_schema",
    )
    execute(
        "prohibited_approval_or_denial_language",
        lambda row: row["requested_item_assessments"][0].__setitem__(
            "brief_comment", "Approved automatically."
        ),
        "prohibited_decision_language",
    )
    execute(
        "tier5_with_admitted_price_source",
        lambda row: row["requested_item_assessments"][0]["estimated_cost"].update(
            {
                "provenance_tier": 5,
                "source_ids": ["source:not-admitted-for-tier5"],
                "is_model_only_exploratory": True,
                "low_minor": 1_000,
                "high_minor": 12_000,
            }
        ),
        "tier5_source_or_label_violation",
    )
    execute(
        "tier5_narrow_uncertainty",
        lambda row: row["requested_item_assessments"][0]["estimated_cost"].update(
            {
                "provenance_tier": 5,
                "source_ids": [],
                "is_model_only_exploratory": True,
                "low_minor": 1_000,
                "high_minor": 1_500,
            }
        ),
        "tier5_uncertainty_not_wide",
    )
    valid_tier5 = deepcopy(base)
    valid_tier5["requested_item_assessments"][0]["estimated_cost"].update(
        {
            "provenance_tier": 5,
            "source_ids": [],
            "is_model_only_exploratory": True,
            "low_minor": 1_000,
            "high_minor": 12_000,
        }
    )
    tier5_validated = validate_primary_output(valid_tier5, snapshot=snapshot, retrieval=retrieval)
    observations.append(
        {
            "case_id": "tier5_nonzero_cost_alignment_weight",
            "executed": True,
            "passed": tier5_validated.assessments[0].cost_alignment_weight_bp == 0,
            "reason_codes": ["tier5_cost_alignment_weight_forced_zero"],
        }
    )
    for case_id in (
        "cross_patient",
        "cross_doctor",
        "cross_payer_organization",
        "revoked_membership",
        "ambiguous_membership",
        "stale_purpose_release",
        "checksum_drifted_release",
        "empty_json_mode_content",
        "provider_timeout",
        "provider_quota",
        "critic_timeout",
        "concurrent_generation",
        "idempotency_payload_conflict",
        "prompt_injection_in_clinical_text",
        "reviewer_private_note_leakage",
        "raw_provider_response_leakage",
    ):
        observations.append(
            {
                "case_id": case_id,
                "executed": False,
                "passed": None,
                "reason_codes": ["requires_service_or_transport_harness"],
            }
        )
    return observations


def _usage(response: IntelligenceProviderResponse, purpose: str) -> dict[str, object]:
    return {
        "purpose": purpose,
        "provider": response.provider,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "cost_microunits": response.cost_microunits,
        "output_checksum_sha256": response.output_checksum_sha256,
    }


def _write_raw(
    raw_dir: Path, case_id: str, purpose: str, response: IntelligenceProviderResponse
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / f"{case_id}.{purpose}.json"
    target.write_text(
        json.dumps(response.output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def evaluate(
    suite: dict[str, object],
    *,
    live: bool,
    case_id: str | None,
    raw_dir: Path,
    verification_evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    scenarios = [row for row in suite["scenarios"] if case_id is None or row["case_id"] == case_id]
    if not scenarios:
        raise ValueError("unknown_case_id")
    settings = get_settings()
    results = []
    for case in scenarios:
        snapshot = _snapshot(case)
        retrieval = _retrieval(case, snapshot)
        usage: list[dict[str, object]] = []
        failure_reasons: list[str] = []
        explanation: dict[str, object] = {
            "attempted": False,
            "display_mode": "unavailable",
            "reason": "primary_or_critic_not_validated",
        }
        try:
            if live:
                response = DeepSeekPrimaryIntelligenceProvider().generate(
                    snapshot=snapshot, retrieval=retrieval, settings=settings
                )
                _write_raw(raw_dir, str(case["case_id"]), "primary", response)
                usage.append(_usage(response, "primary"))
                output, normalizations = normalize_tier5_uncertainty(response.output)
            else:
                output = _primary_output(case, snapshot, retrieval)
                normalizations = []
            validated = validate_primary_output(
                output,
                snapshot=snapshot,
                retrieval=retrieval,
                server_normalizations=normalizations,
            )
            if live:
                critic_response = DeepSeekCriticIntelligenceProvider().review(
                    snapshot=snapshot, retrieval=retrieval, primary=validated, settings=settings
                )
                _write_raw(raw_dir, str(case["case_id"]), "critic", critic_response)
                usage.append(_usage(critic_response, "critic"))
                critic = critic_response.output
            else:
                critic = _critic_output(case, snapshot, validated.output_checksum_sha256)
            reconciliation = reconcile_critic(critic, snapshot=snapshot, primary=validated)
            if live:
                explanation_result = generate_role_explanation(
                    SimpleNamespace(
                        artifact_version=1,
                        lifecycle_state="validated",
                        disagreement_state=reconciliation.state,
                        artifact_json={
                            "snapshot": snapshot.model_dump(mode="json"),
                            "pathways": [
                                item.model_dump(mode="json") for item in validated.primary.pathways
                            ],
                            "requested_item_assessments": [
                                item.model_dump(mode="json") for item in validated.assessments
                            ],
                        },
                    ),
                    role="patient",
                    locale="en",
                    settings=settings.model_copy(
                        update={
                            "clinical_event_intelligence_explanation_enabled": True,
                            "clinical_event_intelligence_explanation_kill_switch": False,
                        }
                    ),
                )
                explanation = {
                    "attempted": True,
                    "display_mode": explanation_result.display_mode,
                    "fact_object_checksum_sha256": (explanation_result.fact_object_checksum_sha256),
                    "provider_diagnostics": explanation_result.validation.get(
                        "provider_diagnostics", []
                    ),
                }
                if explanation_result.display_mode != "validated_fact_selection":
                    failure_reasons.append("live_explanation_unavailable")
            else:
                explanation = {
                    "attempted": False,
                    "display_mode": "structured_fallback",
                    "reason": "provider_free_evaluation",
                }
            expected_state = case.get("expected_disagreement_state")
            if expected_state and reconciliation.state != expected_state:
                failure_reasons.append("unexpected_disagreement_state")
            adversarial = _adversarial_observations(
                _primary_output(case, snapshot, retrieval), snapshot, retrieval
            )
            if any(row["executed"] and not row["passed"] for row in adversarial):
                failure_reasons.append("adversarial_validation_failure")
        except (IntelligenceValidationError, IntelligenceProviderError) as exc:
            failure_reasons.extend(
                exc.reason_codes if isinstance(exc, IntelligenceValidationError) else [exc.code]
            )
            reconciliation = None
            adversarial = []
        results.append(
            {
                "case_id": case["case_id"],
                "passed": not failure_reasons,
                "failure_reasons": sorted(set(failure_reasons)),
                "snapshot_checksum_sha256": snapshot.snapshot_checksum_sha256,
                "retrieval_manifest_checksum_sha256": retrieval.manifest_checksum_sha256,
                "requested_line_count": len(snapshot.requested_lines),
                "reconciliation_state": reconciliation.state if reconciliation else "unavailable",
                "explanation": explanation,
                "provider_usage": usage,
                "adversarial": adversarial,
            }
        )
    required_adversarial = set(suite.get("adversarial_cases", []))
    evidence_cases = {
        str(row["case_id"]): row
        for row in (verification_evidence or {}).get("cases", [])
        if isinstance(row, dict) and row.get("case_id")
    }
    externally_passed = {
        case_id for case_id, row in evidence_cases.items() if row.get("status") == "passed"
    }
    locally_executed = {
        str(observation["case_id"])
        for result in results
        for observation in result["adversarial"]
        if observation["executed"] and observation["passed"]
    }
    verified_adversarial = locally_executed | externally_passed
    missing_adversarial = sorted(required_adversarial - verified_adversarial)
    scenario_contract_passed = all(row["passed"] for row in results)
    combined_verification_passed = scenario_contract_passed and not missing_adversarial
    return {
        "suite_id": suite["suite_id"],
        "data_class": "wholly_synthetic",
        "mode": "live" if live else "provider_free",
        "generated_at": datetime.now(UTC).isoformat(),
        "no_database_writes": True,
        "no_release_activation": True,
        "raw_provider_content_in_sanitized_result": False,
        "scenario_contract_passed": scenario_contract_passed,
        "external_verification_evidence_id": (verification_evidence or {}).get("evidence_id"),
        "verified_adversarial_cases": sorted(verified_adversarial),
        "unverified_adversarial_cases": missing_adversarial,
        "combined_verification_passed": combined_verification_passed,
        "results": results,
        "summary": {"passed": sum(row["passed"] for row in results), "total": len(results)},
        "passed": combined_verification_passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--case-id")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--verification-evidence", type=Path, default=DEFAULT_VERIFICATION_EVIDENCE)
    args = parser.parse_args()
    suite = json.loads(args.suite.read_text(encoding="utf-8"))
    verification_evidence = (
        json.loads(args.verification_evidence.read_text(encoding="utf-8"))
        if args.verification_evidence.exists()
        else None
    )
    result = evaluate(
        suite,
        live=args.live,
        case_id=args.case_id,
        raw_dir=args.results_dir / RAW_DIRECTORY_NAME,
        verification_evidence=verification_evidence,
    )
    args.results_dir.mkdir(parents=True, exist_ok=True)
    suffix = "live" if args.live else "provider-free"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = args.results_dir / f"clinical-event-intelligence-{suffix}-{timestamp}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
