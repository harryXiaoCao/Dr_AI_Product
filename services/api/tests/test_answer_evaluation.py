import copy
import json
from pathlib import Path

import pytest

from app.answer_evaluation import (
    CanonicalAnswerObservation,
    answer_gate_failures,
    contract_readiness_failures,
    evaluate_answer_results,
)
from scripts.evaluate_canonical_answers import (
    _premodel_subject_inputs,
    _production_path_subject_inputs,
    _safe_fallback_subject_inputs,
    score_results,
)

CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json"
)


def test_premodel_subject_matrix_has_exact_canonical_and_variant_scope() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    subjects = _premodel_subject_inputs(contract)

    assert len(subjects) == 93
    assert len({subject["input_id"] for subject in subjects}) == 93
    assert sum(subject["input_kind"] == "canonical" for subject in subjects) == 47
    assert sum(subject["input_kind"] != "canonical" for subject in subjects) == 46
    assert sum(subject["expected_route"] == "emergency_120" for subject in subjects) == 82
    assert (
        sum(subject["expected_route"] == "prohibited_medication_change" for subject in subjects)
        == 11
    )
    assert all(1 <= len(subject["turns"]) <= 2 for subject in subjects)


def test_production_path_partitions_exact_contract_without_overlap() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    all_subjects = _production_path_subject_inputs(contract)
    premodel = _premodel_subject_inputs(contract)
    fallback = _safe_fallback_subject_inputs(contract)

    assert len(all_subjects) == 185
    assert len({subject["input_id"] for subject in all_subjects}) == 185
    assert len(premodel) == 93
    assert len(fallback) == 92
    assert sum(subject["input_kind"] == "canonical" for subject in fallback) == 53
    assert sum(subject["input_kind"] != "canonical" for subject in fallback) == 39
    assert {subject["input_id"] for subject in premodel}.isdisjoint(
        subject["input_id"] for subject in fallback
    )
    assert {subject["input_id"] for subject in all_subjects} == {
        subject["input_id"] for subject in [*premodel, *fallback]
    }
    assert all(subject["retrieval_allowed"] for subject in fallback)
    assert all(subject["model_allowed"] for subject in fallback)
    assert all(1 <= len(subject["turns"]) <= 2 for subject in fallback)


def _observation(
    *,
    input_id: str,
    parent_case_id: str,
    input_kind: str,
    expected_route: str,
) -> CanonicalAnswerObservation:
    if expected_route == "emergency_120":
        return CanonicalAnswerObservation(
            input_id=input_id,
            parent_case_id=parent_case_id,
            input_kind=input_kind,
            expected_route=expected_route,
            observed_safety_code="emergency",
            observed_urgency_route=expected_route,
            fallback_code="emergency",
            evidence_decision=None,
            cited_source_ids=(),
            relevant_source_ids=frozenset(),
            forbidden_source_ids=frozenset(),
            retrieval_call_count=0,
            planner_call_count=0,
            answer_model_call_count=0,
            claim_support_passed=True,
            uncertainty_present=True,
            next_action_code="call_120",
            emergency_guidance_present=True,
            latency_ms=4,
        )
    if expected_route == "prohibited_medication_change":
        return CanonicalAnswerObservation(
            input_id=input_id,
            parent_case_id=parent_case_id,
            input_kind=input_kind,
            expected_route=expected_route,
            observed_safety_code="prohibited_medication_change",
            observed_urgency_route=expected_route,
            fallback_code="prohibited_request",
            evidence_decision=None,
            cited_source_ids=(),
            relevant_source_ids=frozenset(),
            forbidden_source_ids=frozenset(),
            retrieval_call_count=0,
            planner_call_count=0,
            answer_model_call_count=0,
            claim_support_passed=True,
            uncertainty_present=True,
            next_action_code="contact_connected_doctor",
            emergency_guidance_present=False,
            latency_ms=5,
        )
    next_action = (
        "seek_local_care" if expected_route == "urgent_same_day" else "contact_connected_doctor"
    )
    return CanonicalAnswerObservation(
        input_id=input_id,
        parent_case_id=parent_case_id,
        input_kind=input_kind,
        expected_route=expected_route,
        observed_safety_code="permitted_symptom_guidance",
        observed_urgency_route=expected_route,
        fallback_code=None,
        evidence_decision="sufficient",
        cited_source_ids=("source-reviewed",),
        relevant_source_ids=frozenset({"source-reviewed"}),
        forbidden_source_ids=frozenset({"source-forbidden"}),
        retrieval_call_count=1,
        planner_call_count=0,
        answer_model_call_count=1,
        claim_support_passed=True,
        uncertainty_present=True,
        next_action_code=next_action,
        emergency_guidance_present=False,
        latency_ms=650,
        provider_input_tokens=1000,
        provider_output_tokens=200,
        provider_cost_microunits=196,
    )


def _raw_observation(observation: CanonicalAnswerObservation) -> dict:
    return {
        "input_id": observation.input_id,
        "observed_safety_code": observation.observed_safety_code,
        "observed_urgency_route": observation.observed_urgency_route,
        "fallback_code": observation.fallback_code,
        "evidence_decision": observation.evidence_decision,
        "cited_source_ids": list(observation.cited_source_ids),
        "retrieval_call_count": observation.retrieval_call_count,
        "planner_call_count": observation.planner_call_count,
        "answer_model_call_count": observation.answer_model_call_count,
        "claim_support_passed": observation.claim_support_passed,
        "uncertainty_present": observation.uncertainty_present,
        "next_action_code": observation.next_action_code,
        "emergency_guidance_present": observation.emergency_guidance_present,
        "latency_ms": observation.latency_ms,
        "provider_input_tokens": observation.provider_input_tokens,
        "provider_output_tokens": observation.provider_output_tokens,
        "provider_cost_microunits": observation.provider_cost_microunits,
        "provider_failure": observation.provider_failure,
    }


def test_complete_answer_metrics_keep_safety_retrieval_and_generation_gates_separate() -> None:
    observations = [
        _observation(
            input_id="RCQ-088",
            parent_case_id="RCQ-088",
            input_kind="canonical",
            expected_route="emergency_120",
        ),
        _observation(
            input_id="RCQ-009",
            parent_case_id="RCQ-009",
            input_kind="canonical",
            expected_route="prohibited_medication_change",
        ),
        _observation(
            input_id="RCQ-001",
            parent_case_id="RCQ-001",
            input_kind="canonical",
            expected_route="routine_education",
        ),
        _observation(
            input_id="RCQ-001-V01",
            parent_case_id="RCQ-001",
            input_kind="symptom_only",
            expected_route="routine_education",
        ),
    ]

    metrics, details = evaluate_answer_results(observations)

    assert metrics["machine_pass_rate"] == 1.0
    assert metrics["emergency_recall"] == 1.0
    assert metrics["zero_pre_emergency_call_rate"] == 1.0
    assert metrics["medication_gate_pass_rate"] == 1.0
    assert metrics["claim_support_pass_rate"] == 1.0
    assert metrics["variant_non_degradation_rate"] == 1.0
    assert metrics["forbidden_source_hits"] == 0
    assert metrics["total_provider_cost_microunits"] == 392
    assert all(item["machine_passed"] for item in details)


def test_complete_answer_gate_detects_forbidden_leakage_and_pre_emergency_calls() -> None:
    emergency = _observation(
        input_id="RCQ-088",
        parent_case_id="RCQ-088",
        input_kind="canonical",
        expected_route="emergency_120",
    )
    emergency = CanonicalAnswerObservation(
        **{
            **emergency.__dict__,
            "retrieval_call_count": 1,
            "answer_model_call_count": 1,
        }
    )
    generated = _observation(
        input_id="RCQ-001",
        parent_case_id="RCQ-001",
        input_kind="canonical",
        expected_route="routine_education",
    )
    generated = CanonicalAnswerObservation(
        **{
            **generated.__dict__,
            "cited_source_ids": ("source-forbidden",),
            "claim_support_passed": False,
        }
    )

    metrics, _ = evaluate_answer_results([emergency, generated])
    thresholds = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))[
        "complete_answer_evaluation_policy"
    ]["machine_thresholds"]
    failures = answer_gate_failures(metrics, thresholds)

    assert "machine_pass_rate" in failures
    assert "zero_pre_emergency_call_rate" in failures
    assert "claim_support_pass_rate" in failures
    assert "relevant_source_pass_rate" in failures
    assert "forbidden_source_hits" in failures


def test_complete_answer_gate_rejects_route_field_mismatch() -> None:
    observation = _observation(
        input_id="RCQ-001",
        parent_case_id="RCQ-001",
        input_kind="canonical",
        expected_route="routine_education",
    )
    observation = CanonicalAnswerObservation(
        **{
            **observation.__dict__,
            "observed_urgency_route": "clinician_contact",
        }
    )

    metrics, details = evaluate_answer_results([observation])

    assert metrics["route_and_action_pass_rate"] == 0.0
    assert details[0]["route_and_action_pass"] is False


def test_candidate_contract_is_structural_but_not_ready_for_paid_answers() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    failures = contract_readiness_failures(contract)

    assert "contract_not_approved_frozen" in failures
    assert "critical_set_not_approved_frozen" in failures
    assert "review_clinical_status" in failures
    assert "RCQ-001:relevant_source_ids" in failures
    assert "RCQ-001:coverage_not_approved" in failures
    assert "RCQ-003-V01:relevant_source_ids" in failures
    assert "RCQ-003-V01:coverage_not_approved" in failures


def test_reviewed_contract_with_approved_case_labels_is_answer_run_ready() -> None:
    contract = copy.deepcopy(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    contract["status"] = "approved_frozen"
    contract["frozen"] = True
    contract["critical_set_status"] = "clinician_approved_frozen"
    contract["review"].update(
        {
            "clinical_status": "approved",
            "native_simplified_chinese_status": "approved",
            "product_status": "approved",
            "reviewer_id": "reviewer-1",
            "reviewer_role": "clinical_native_chinese_product_review",
            "reviewed_at": "2026-07-21T00:00:00Z",
        }
    )
    for case in contract["cases"]:
        subjects = [case, *case["variants"]]
        for subject in subjects:
            if not subject["model_allowed"]:
                continue
            subject["relevant_source_ids"] = ["source-reviewed"]
            subject["coverage_audit"] = {
                "status": "approved",
                "eligible_source_ids": ["source-reviewed"],
                "missing_requirements": [],
            }

    assert contract_readiness_failures(contract) == []


def test_initial_batch_pass_cannot_claim_full_machine_or_human_gate() -> None:
    contract = copy.deepcopy(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    planned = []
    raw_observations = []
    for route in (
        "emergency_120",
        "prohibited_medication_change",
        "urgent_same_day",
        "clinician_contact",
        "routine_education",
    ):
        case = next(item for item in contract["cases"] if item["expected_urgency_route"] == route)
        planned.append(case["case_id"])
        if case["model_allowed"]:
            case["relevant_source_ids"] = ["source-reviewed"]
        raw_observations.append(
            _raw_observation(
                _observation(
                    input_id=case["case_id"],
                    parent_case_id=case["case_id"],
                    input_kind="canonical",
                    expected_route=route,
                )
            )
        )
    results = {
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "provider": "synthetic-test-provider",
        "model": "synthetic-test-model",
        "active_release_id": "KBIR-SYNTHETIC",
        "maximum_concurrency": 1,
        "evaluation_scope": "initial_batch",
        "planned_input_ids": planned,
        "observations": raw_observations,
    }

    artifact = score_results(contract, results)

    assert artifact["batch_machine_passed"] is True
    assert artifact["ready_for_full_contract_run"] is True
    assert artifact["machine_gate_passed"] is False
    assert artifact["human_review"]["status"] == "pending"
    assert artifact["overall_gate_passed"] is False


def test_score_rejects_partial_or_unplanned_initial_batch() -> None:
    contract = copy.deepcopy(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    results = {
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "provider": "synthetic-test-provider",
        "model": "synthetic-test-model",
        "active_release_id": "KBIR-SYNTHETIC",
        "maximum_concurrency": 1,
        "evaluation_scope": "initial_batch",
        "planned_input_ids": ["RCQ-001"],
        "observations": [],
    }

    with pytest.raises(ValueError, match="Planned complete-answer inputs"):
        score_results(contract, results)


def test_score_rejects_truthy_strings_and_negative_usage() -> None:
    contract = {
        "contract_id": "malformed-observation-contract",
        "content_sha256": "malformed-checksum",
        "complete_answer_evaluation_policy": json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))[
            "complete_answer_evaluation_policy"
        ],
        "cases": [
            {
                "case_id": "C1",
                "expected_urgency_route": "routine_education",
                "retrieval_allowed": True,
                "model_allowed": True,
                "relevant_source_ids": ["source-reviewed"],
                "forbidden_source_ids": [],
                "coverage_audit": {
                    "status": "approved",
                    "eligible_source_ids": ["source-reviewed"],
                },
                "variants": [],
            }
        ],
    }
    observation = _raw_observation(
        _observation(
            input_id="C1",
            parent_case_id="C1",
            input_kind="canonical",
            expected_route="routine_education",
        )
    )
    results = {
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "provider": "synthetic-test-provider",
        "model": "synthetic-test-model",
        "active_release_id": "KBIR-SYNTHETIC",
        "maximum_concurrency": 1,
        "evaluation_scope": "full_contract",
        "planned_input_ids": ["C1"],
        "observations": [observation],
    }
    results["observations"][0]["claim_support_passed"] = "false"

    with pytest.raises(ValueError, match="claim_support_passed must be boolean"):
        score_results(contract, results)

    results["observations"][0]["claim_support_passed"] = True
    results["observations"][0]["provider_cost_microunits"] = -1
    with pytest.raises(ValueError, match="provider_cost_microunits"):
        score_results(contract, results)


def test_full_matrix_scoring_uses_variant_specific_route_and_source_labels() -> None:
    real_policy = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))[
        "complete_answer_evaluation_policy"
    ]
    contract = {
        "contract_id": "synthetic-variant-contract",
        "content_sha256": "synthetic-checksum",
        "complete_answer_evaluation_policy": real_policy,
        "cases": [
            {
                "case_id": "C1",
                "expected_urgency_route": "routine_education",
                "retrieval_allowed": True,
                "model_allowed": True,
                "relevant_source_ids": ["source-parent"],
                "forbidden_source_ids": ["source-variant"],
                "coverage_audit": {
                    "status": "approved",
                    "eligible_source_ids": ["source-parent"],
                },
                "variants": [
                    {
                        "variant_id": "V1",
                        "kind": "symptom_only",
                        "expected_route": "urgent_same_day",
                        "retrieval_allowed": True,
                        "model_allowed": True,
                        "relevant_source_ids": ["source-variant"],
                        "forbidden_source_ids": ["source-parent"],
                        "coverage_audit": {
                            "status": "approved",
                            "eligible_source_ids": ["source-variant"],
                        },
                    }
                ],
            }
        ],
    }
    parent = _observation(
        input_id="C1",
        parent_case_id="C1",
        input_kind="canonical",
        expected_route="routine_education",
    )
    parent = CanonicalAnswerObservation(
        **{
            **parent.__dict__,
            "cited_source_ids": ("source-parent",),
            "relevant_source_ids": frozenset({"source-parent"}),
        }
    )
    variant = _observation(
        input_id="V1",
        parent_case_id="C1",
        input_kind="symptom_only",
        expected_route="urgent_same_day",
    )
    variant = CanonicalAnswerObservation(
        **{
            **variant.__dict__,
            "cited_source_ids": ("source-variant",),
            "relevant_source_ids": frozenset({"source-variant"}),
        }
    )
    results = {
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "provider": "synthetic-test-provider",
        "model": "synthetic-test-model",
        "active_release_id": "KBIR-SYNTHETIC",
        "maximum_concurrency": 1,
        "evaluation_scope": "full_contract",
        "planned_input_ids": ["C1", "V1"],
        "observations": [_raw_observation(parent), _raw_observation(variant)],
    }

    artifact = score_results(contract, results)

    variant_detail = next(item for item in artifact["observations"] if item["input_id"] == "V1")
    assert variant_detail["expected_route"] == "urgent_same_day"
    assert variant_detail["route_and_action_pass"] is True
    assert variant_detail["evidence_pass"] is True
    assert artifact["batch_machine_passed"] is True
    assert artifact["machine_gate_passed"] is True
