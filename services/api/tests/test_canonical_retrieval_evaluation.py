from __future__ import annotations

import copy
import json
from pathlib import Path

from app.canonical_retrieval_evaluation import evaluate_canonical_retrieval

EVALUATION_DIR = Path(__file__).resolve().parents[1] / "knowledge_base/evaluation"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "knowledge_base/release_artifacts/evaluation"
COVERAGE_ARTIFACT = (
    "canonical-rural-symptom-coverage-"
    "KBIR-D3DFA94CC95660019B6EF94E-v9-gate-metrics-local-20260721.json"
)


def _fixture() -> tuple[dict, dict, dict]:
    approved_review = {
        "clinical_status": "approved",
        "native_simplified_chinese_status": "approved",
        "product_status": "approved",
        "reviewer_id": "reviewer-1",
        "reviewer_role": "clinical_product_review",
        "reviewed_at": "2026-07-21T00:00:00Z",
    }
    contract = {
        "contract_id": "contract-v1",
        "content_sha256": "abc123",
        "frozen": True,
        "review": approved_review,
        "cases": [
            {
                "case_id": "C1",
                "retrieval_allowed": True,
                "relevant_source_ids": ["S1"],
                "forbidden_source_ids": ["FORBIDDEN"],
                "coverage_audit": {"status": "reviewed_supported"},
                "variants": [
                    {
                        "variant_id": "V1",
                        "kind": "symptom_only",
                        "retrieval_allowed": True,
                        "relevant_source_ids": ["S1"],
                        "forbidden_source_ids": ["FORBIDDEN"],
                        "coverage_audit": {"status": "reviewed_supported"},
                    }
                ],
            },
            {
                "case_id": "C2",
                "retrieval_allowed": False,
                "relevant_source_ids": [],
                "forbidden_source_ids": [],
                "coverage_audit": {"status": "not_applicable_pre_safety"},
                "variants": [],
            },
        ],
    }
    policy = {
        "schema_version": "1.0.0",
        "contract_binding": {"contract_id": "contract-v1", "contract_sha256": "abc123"},
        "coverage_binding": {
            "auditor_version": "audit-v1",
            "active_release_ids": ["R1"],
        },
        "scope": {
            "ranking_unit": "source_id",
            "top_k": 6,
            "retrieval_only": True,
            "answer_generation": False,
            "retrieval_rescue": False,
            "model_planner": False,
            "evaluation_data_is_retrieval_corpus": False,
            "evaluation_data_is_training_data": False,
            "candidate_hits_are_clinical_support": False,
        },
        "thresholds": {
            "minimum_support_label_count": 2,
            "minimum_symptom_only_support_label_count": 1,
            "minimum_source_label_readiness_rate": 1.0,
            "minimum_relevant_source_recall_at_6": 0.85,
            "minimum_mean_reciprocal_rank": 0.85,
            "minimum_relevant_decision_pass_rate": 1.0,
            "minimum_symptom_only_relevant_source_recall_at_6": 0.9,
            "minimum_paired_variant_non_degradation_rate": 1.0,
            "minimum_paired_variant_comparison_count": 1,
            "minimum_no_evidence_precision": 0.95,
            "minimum_pre_safety_zero_retrieval_rate": 1.0,
            "maximum_forbidden_source_hits": 0,
            "maximum_retrieval_errors": 0,
            "maximum_retrieval_latency_p95_ms": 2500,
            "maximum_single_subject_latency_ms": 8000,
            "maximum_provider_calls": 0,
            "maximum_paid_usage_usd": 0,
        },
        "review": {
            "clinical_status": "approved",
            "native_simplified_chinese_status": "approved",
            "product_status": "approved",
            "reviewer_ids": ["reviewer-1"],
            "reviewed_at": "2026-07-21T00:00:00Z",
        },
    }
    coverage = {
        "contract_id": "contract-v1",
        "contract_sha256": "abc123",
        "auditor_version": "audit-v1",
        "active_release_ids": ["R1"],
        "provider_calls": 0,
        "paid_usage_usd": 0,
        "observations": [
            {
                "case_id": "C1",
                "audit_status": "candidate_support_pending_case_review",
                "decision": "sufficient",
                "candidate_source_ids": ["S1"],
                "retrieval_call_count": 1,
                "retrieval_latency_ms": 100,
            },
            {
                "case_id": "C2",
                "audit_status": "not_applicable_pre_safety",
                "decision": None,
                "candidate_source_ids": [],
                "retrieval_call_count": 0,
                "retrieval_latency_ms": 0,
            },
        ],
        "variant_observations": [
            {
                "case_id": "C1",
                "variant_id": "V1",
                "variant_kind": "symptom_only",
                "audit_status": "candidate_support_pending_case_review",
                "decision": "sufficient",
                "candidate_source_ids": ["S1"],
                "retrieval_call_count": 1,
                "retrieval_latency_ms": 120,
            }
        ],
    }
    return contract, policy, coverage


def test_reviewed_release_matched_retrieval_gate_passes() -> None:
    contract, policy, coverage = _fixture()

    result = evaluate_canonical_retrieval(contract, policy, coverage)

    assert result["passed"]
    assert result["structural_failures"] == []
    assert result["readiness_failures"] == []
    assert result["metric_failures"] == []
    assert result["metrics"]["symptom_only_relevant_source_recall_at_6"] == 1.0
    assert result["metrics"]["paired_variant_non_degradation_rate"] == 1.0
    assert result["metrics"]["pre_safety_zero_retrieval_rate"] == 1.0


def test_pending_labels_fail_closed_without_scoring_candidates_as_support() -> None:
    contract, policy, coverage = _fixture()
    contract["frozen"] = False
    contract["review"] = {
        "clinical_status": "pending",
        "native_simplified_chinese_status": "pending",
        "product_status": "pending",
    }
    policy["review"] = {
        "clinical_status": "pending",
        "native_simplified_chinese_status": "pending",
        "product_status": "pending",
        "reviewer_ids": [],
        "reviewed_at": None,
    }
    for case in contract["cases"]:
        case["relevant_source_ids"] = []
        for variant in case["variants"]:
            variant["relevant_source_ids"] = []

    result = evaluate_canonical_retrieval(contract, policy, coverage)

    assert not result["passed"]
    assert "contract_not_frozen" in result["readiness_failures"]
    assert "source_label_pending:C1" in result["readiness_failures"]
    assert "source_label_pending:V1" in result["readiness_failures"]
    assert result["metrics"]["candidate_sufficiency_rate"] == 1.0
    assert result["metrics"]["relevant_source_recall_at_6"] is None
    assert "unscored:relevant_source_recall_at_6" in result["metric_failures"]
    assert not result["eligible_evidence_claimed"]
    assert not result["clinical_approval_claimed"]


def test_symptom_only_degradation_forbidden_leakage_and_latency_fail() -> None:
    contract, policy, coverage = _fixture()
    degraded = copy.deepcopy(coverage)
    degraded["variant_observations"][0]["candidate_source_ids"] = ["FORBIDDEN"]
    degraded["variant_observations"][0]["retrieval_latency_ms"] = 9000

    result = evaluate_canonical_retrieval(contract, policy, degraded)

    assert not result["passed"]
    assert result["metrics"]["forbidden_source_hit_count"] == 1
    assert result["metrics"]["paired_variant_non_degradation_rate"] == 0.0
    assert "symptom_only_relevant_source_recall_at_6" in result["metric_failures"]
    assert "paired_variant_non_degradation_rate" in result["metric_failures"]
    assert "forbidden_source_hit_count" in result["metric_failures"]
    assert "retrieval_latency_max_ms" in result["metric_failures"]


def test_contract_release_and_observation_drift_fail_structurally() -> None:
    contract, policy, coverage = _fixture()
    drifted = copy.deepcopy(coverage)
    drifted["contract_sha256"] = "different"
    drifted["active_release_ids"] = ["R2"]
    drifted["observations"].pop()

    result = evaluate_canonical_retrieval(contract, policy, drifted)

    assert not result["passed"]
    assert "coverage_contract_sha256" in result["structural_failures"]
    assert "coverage_active_release_ids" in result["structural_failures"]
    assert "missing_observation:C2" in result["structural_failures"]


def test_current_canonical_gate_is_structurally_valid_but_readiness_blocked() -> None:
    contract = json.loads(
        (EVALUATION_DIR / "canonical_rural_symptom_questions.v1.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (EVALUATION_DIR / "canonical_rural_symptom_retrieval_gate.v1.json").read_text(
            encoding="utf-8"
        )
    )
    coverage = json.loads(
        (ARTIFACT_DIR / COVERAGE_ARTIFACT).read_text(encoding="utf-8")
    )

    result = evaluate_canonical_retrieval(contract, policy, coverage)

    assert not result["passed"]
    assert result["structural_failures"] == []
    assert result["metrics"]["retrieval_eligible_subject_count"] == 92
    assert result["metrics"]["pre_safety_subject_count"] == 93
    assert result["metrics"]["support_label_count"] == 0
    assert result["metrics"]["candidate_sufficiency_rate"] == 34 / 92
    assert result["metrics"]["symptom_only_candidate_sufficiency_rate"] == 3 / 8
    assert result["metrics"]["pre_safety_zero_retrieval_rate"] == 1.0
    assert result["metrics"]["forbidden_source_hit_count"] == 0
    assert result["metrics"]["retrieval_error_count"] == 0
    assert "support_label_count" in result["readiness_failures"]
    assert "unscored:relevant_source_recall_at_6" in result["metric_failures"]
