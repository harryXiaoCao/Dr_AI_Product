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
    minimum_distinct_sources: int = 1
    preferred_jurisdiction: str | None = None
    allowed_languages: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RetrievalObservation:
    case_id: str
    source_ids: tuple[str, ...]
    decision: str
    source_jurisdictions: tuple[str, ...] = ()
    source_applicable_jurisdictions: tuple[tuple[str, ...], ...] = ()
    passage_languages: tuple[str, ...] = ()
    latency_ms: int = 0


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
    diversity_matches = jurisdiction_matches = language_matches = 0
    latencies: list[int] = []
    for case in cases:
        observation = observed_by_id.get(case.case_id)
        if observation is None:
            raise ValueError(f"Missing retrieval observation for {case.case_id}.")
        unique_indexes: list[int] = []
        seen_sources: set[str] = set()
        for index, source_id in enumerate(observation.source_ids):
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)
            unique_indexes.append(index)
            if len(unique_indexes) == k:
                break
        returned = tuple(observation.source_ids[index] for index in unique_indexes)
        returned_jurisdictions = tuple(
            observation.source_jurisdictions[index]
            for index in unique_indexes
            if index < len(observation.source_jurisdictions)
        )
        returned_applicable_jurisdictions = tuple(
            observation.source_applicable_jurisdictions[index]
            for index in unique_indexes
            if index < len(observation.source_applicable_jurisdictions)
        )
        returned_languages = tuple(
            observation.passage_languages[index]
            for index in unique_indexes
            if index < len(observation.passage_languages)
        )
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
        diversity_matches += expected_no_evidence or (
            len(set(returned)) >= case.minimum_distinct_sources
        )
        jurisdiction_matches += (
            case.preferred_jurisdiction is None
            or not returned
            or any(
                case.preferred_jurisdiction
                in {
                    returned_jurisdictions[index]
                    if index < len(returned_jurisdictions)
                    else "",
                    *(
                        returned_applicable_jurisdictions[index]
                        if index < len(returned_applicable_jurisdictions)
                        else ()
                    ),
                }
                for index in range(len(returned))
            )
        )
        language_matches += (
            not case.allowed_languages
            or not returned
            or set(returned_languages).issubset(case.allowed_languages)
        )
        latencies.append(max(0, observation.latency_ms))
    count = len(cases)
    ordered_latencies = sorted(latencies)
    p95_index = max(0, math.ceil(0.95 * len(ordered_latencies)) - 1)
    return {
        "case_count": count,
        f"recall_at_{k}": sum(recalls) / len(recalls) if recalls else 1.0,
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 1.0,
        f"ndcg_at_{k}": sum(ndcgs) / len(ndcgs) if ndcgs else 1.0,
        "decision_accuracy": decision_matches / count,
        "forbidden_source_hits": forbidden_hits,
        "source_diversity_pass_rate": diversity_matches / count,
        "jurisdiction_pass_rate": jurisdiction_matches / count,
        "language_pass_rate": language_matches / count,
        "latency_p95_ms": ordered_latencies[p95_index],
        "latency_max_ms": ordered_latencies[-1],
        "no_evidence_precision": (
            no_evidence_true / no_evidence_predicted if no_evidence_predicted else 1.0
        ),
    }


def retrieval_gate_failures(
    metrics: dict[str, float | int],
    *,
    k: int,
    minimum_recall: float,
    minimum_ndcg: float,
    minimum_mrr: float,
    minimum_no_evidence_precision: float,
    maximum_latency_p95_ms: int,
    maximum_single_case_latency_ms: int | None = None,
) -> list[str]:
    checks = {
        f"recall_at_{k}": metrics[f"recall_at_{k}"] >= minimum_recall,
        f"ndcg_at_{k}": metrics[f"ndcg_at_{k}"] >= minimum_ndcg,
        "mrr": metrics["mrr"] >= minimum_mrr,
        "decision_accuracy": metrics["decision_accuracy"] == 1.0,
        "no_evidence_precision": (
            metrics["no_evidence_precision"] >= minimum_no_evidence_precision
        ),
        "forbidden_source_hits": metrics["forbidden_source_hits"] == 0,
        "source_diversity_pass_rate": metrics["source_diversity_pass_rate"] == 1.0,
        "jurisdiction_pass_rate": metrics["jurisdiction_pass_rate"] == 1.0,
        "language_pass_rate": metrics["language_pass_rate"] == 1.0,
        "latency_p95_ms": metrics["latency_p95_ms"] <= maximum_latency_p95_ms,
    }
    if maximum_single_case_latency_ms is not None:
        checks["latency_max_ms"] = (
            metrics["latency_max_ms"] <= maximum_single_case_latency_ms
        )
    return [name for name, passed in checks.items() if not passed]
