from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    case_id: str
    relevant_source_grades: dict[str, int]
    expected_decision: str = "sufficient"
    forbidden_source_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RetrievalObservation:
    case_id: str
    source_ids: tuple[str, ...]
    decision: str


def _dcg(grades: Sequence[int]) -> float:
    return sum((2**grade - 1) / math.log2(rank + 2) for rank, grade in enumerate(grades))


def evaluate_retrieval_results(
    cases: Sequence[RetrievalEvaluationCase],
    observations: Sequence[RetrievalObservation],
    *,
    k: int = 6,
) -> dict[str, float | int]:
    """Score frozen retrieval outputs without invoking a generator or model judge."""

    if not cases or k < 1:
        raise ValueError("Retrieval evaluation requires cases and a positive k.")
    observed_by_id = {item.case_id: item for item in observations}
    if len(observed_by_id) != len(observations):
        raise ValueError("Observed case IDs must be unique.")
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    decision_matches = forbidden_hits = no_evidence_true = no_evidence_predicted = 0
    for case in cases:
        observation = observed_by_id.get(case.case_id)
        if observation is None:
            raise ValueError(f"Missing retrieval observation for {case.case_id}.")
        returned = observation.source_ids[:k]
        relevant = set(case.relevant_source_grades)
        if relevant:
            hits = [source_id for source_id in returned if source_id in relevant]
            recalls.append(len(set(hits)) / len(relevant))
            first_rank = next(
                (rank for rank, source_id in enumerate(returned, start=1) if source_id in relevant),
                None,
            )
            reciprocal_ranks.append(1 / first_rank if first_rank else 0.0)
            grades = [case.relevant_source_grades.get(source_id, 0) for source_id in returned]
            ideal = sorted(case.relevant_source_grades.values(), reverse=True)[:k]
            ndcgs.append(_dcg(grades) / _dcg(ideal))
        forbidden_hits += len(set(returned) & case.forbidden_source_ids)
        decision_matches += observation.decision == case.expected_decision
        expected_no_evidence = case.expected_decision != "sufficient"
        predicted_no_evidence = observation.decision != "sufficient"
        no_evidence_true += expected_no_evidence and predicted_no_evidence
        no_evidence_predicted += predicted_no_evidence
    count = len(cases)
    return {
        "case_count": count,
        f"recall_at_{k}": sum(recalls) / len(recalls) if recalls else 1.0,
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 1.0,
        f"ndcg_at_{k}": sum(ndcgs) / len(ndcgs) if ndcgs else 1.0,
        "decision_accuracy": decision_matches / count,
        "forbidden_source_hits": forbidden_hits,
        "no_evidence_precision": (
            no_evidence_true / no_evidence_predicted if no_evidence_predicted else 1.0
        ),
    }
