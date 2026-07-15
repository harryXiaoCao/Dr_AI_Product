import pytest

from app.knowledge_retrieval_evaluation import (
    RetrievalEvaluationCase,
    RetrievalObservation,
    evaluate_retrieval_results,
)


def test_retrieval_metrics_are_generation_independent_and_detect_leakage() -> None:
    metrics = evaluate_retrieval_results(
        [
            RetrievalEvaluationCase(
                case_id="RET-SYN-001",
                relevant_source_grades={"source-a": 3, "source-b": 2},
                forbidden_source_ids=frozenset({"stale-source"}),
            ),
            RetrievalEvaluationCase(
                case_id="RET-SYN-002",
                relevant_source_grades={},
                expected_decision="no_eligible_evidence",
                forbidden_source_ids=frozenset({"doctor-only-source"}),
            ),
        ],
        [
            RetrievalObservation(
                case_id="RET-SYN-001",
                source_ids=("source-a", "stale-source", "source-b"),
                decision="sufficient",
            ),
            RetrievalObservation(
                case_id="RET-SYN-002",
                source_ids=(),
                decision="no_eligible_evidence",
            ),
        ],
        k=3,
    )

    assert metrics["recall_at_3"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["decision_accuracy"] == 1.0
    assert metrics["no_evidence_precision"] == 1.0
    assert metrics["forbidden_source_hits"] == 1
    assert metrics["ndcg_at_3"] == pytest.approx(0.9558, abs=0.0001)


def test_retrieval_evaluation_rejects_missing_observations() -> None:
    with pytest.raises(ValueError, match="Missing retrieval observation"):
        evaluate_retrieval_results(
            [RetrievalEvaluationCase(case_id="RET-SYN-003", relevant_source_grades={})],
            [],
        )
