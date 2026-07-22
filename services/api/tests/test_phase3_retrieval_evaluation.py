import pytest

from app.knowledge_retrieval_evaluation import (
    RetrievalEvaluationCase,
    RetrievalObservation,
    evaluate_retrieval_results,
    retrieval_gate_failures,
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
                source_jurisdictions=("CN", "US", "CN"),
                source_applicable_jurisdictions=((), (), ()),
                passage_languages=("zh-Hans", "zh-Hans", "zh-Hans"),
                latency_ms=80,
            ),
            RetrievalObservation(
                case_id="RET-SYN-002",
                source_ids=(),
                decision="no_eligible_evidence",
                latency_ms=20,
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
    assert metrics["latency_p95_ms"] == 80
    assert metrics["latency_max_ms"] == 80
    assert metrics["jurisdiction_pass_rate"] == 1.0


def test_retrieval_gate_reports_each_failed_production_threshold() -> None:
    failures = retrieval_gate_failures(
        {
            "recall_at_6": 0.8,
            "ndcg_at_6": 0.7,
            "mrr": 0.75,
            "decision_accuracy": 0.9,
            "no_evidence_precision": 0.9,
            "forbidden_source_hits": 1,
            "source_diversity_pass_rate": 0.9,
            "jurisdiction_pass_rate": 0.9,
            "language_pass_rate": 0.9,
            "latency_p95_ms": 1500,
            "latency_max_ms": 9000,
        },
        k=6,
        minimum_recall=0.85,
        minimum_ndcg=0.8,
        minimum_mrr=0.85,
        minimum_no_evidence_precision=0.95,
        maximum_latency_p95_ms=1200,
        maximum_single_case_latency_ms=8000,
    )

    assert failures == [
        "recall_at_6",
        "ndcg_at_6",
        "mrr",
        "decision_accuracy",
        "no_evidence_precision",
        "forbidden_source_hits",
        "source_diversity_pass_rate",
        "jurisdiction_pass_rate",
        "language_pass_rate",
        "latency_p95_ms",
        "latency_max_ms",
    ]


def test_retrieval_metrics_count_each_source_once_and_keep_metadata_aligned() -> None:
    metrics = evaluate_retrieval_results(
        [
            RetrievalEvaluationCase(
                case_id="RET-SYN-DUPLICATES",
                relevant_source_grades={"source-a": 3, "source-b": 2},
                preferred_jurisdiction="CN",
                allowed_languages=frozenset({"zh-Hans"}),
            )
        ],
        [
            RetrievalObservation(
                case_id="RET-SYN-DUPLICATES",
                source_ids=("source-a", "source-a", "source-b"),
                decision="sufficient",
                source_jurisdictions=("CN", "US", "CN"),
                source_applicable_jurisdictions=((), (), ()),
                passage_languages=("zh-Hans", "en", "zh-Hans"),
            )
        ],
        k=3,
    )

    assert metrics["recall_at_3"] == 1.0
    assert metrics["ndcg_at_3"] == 1.0
    assert metrics["jurisdiction_pass_rate"] == 1.0
    assert metrics["language_pass_rate"] == 1.0


def test_jurisdiction_gate_accepts_reviewed_applicability_without_relabelling_origin() -> None:
    metrics = evaluate_retrieval_results(
        [
            RetrievalEvaluationCase(
                case_id="RET-SYN-APPLICABILITY",
                relevant_source_grades={"source-tw": 3},
                preferred_jurisdiction="CN",
                allowed_languages=frozenset({"zh-Hans"}),
            )
        ],
        [
            RetrievalObservation(
                case_id="RET-SYN-APPLICABILITY",
                source_ids=("source-tw",),
                decision="sufficient",
                source_jurisdictions=("TW",),
                source_applicable_jurisdictions=(("CN",),),
                passage_languages=("zh-Hans",),
            )
        ],
    )

    assert metrics["jurisdiction_pass_rate"] == 1.0


def test_retrieval_evaluation_rejects_missing_observations() -> None:
    with pytest.raises(ValueError, match="Missing retrieval observation"):
        evaluate_retrieval_results(
            [RetrievalEvaluationCase(case_id="RET-SYN-003", relevant_source_grades={})],
            [],
        )
