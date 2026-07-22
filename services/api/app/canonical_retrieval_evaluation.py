from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any


def _rate(items: list[Any], predicate: Callable[[Any], bool]) -> float:
    if not items:
        return 1.0
    return sum(1 for item in items if predicate(item)) / len(items)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _percentile_95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(max(0, value) for value in values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _subject_index(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    subjects: dict[str, dict[str, Any]] = {}
    for case in contract.get("cases", []):
        case_id = str(case.get("case_id", ""))
        subjects[case_id] = {
            "subject_id": case_id,
            "parent_case_id": None,
            "kind": "canonical",
            "retrieval_allowed": case.get("retrieval_allowed") is True,
            "relevant_source_ids": list(case.get("relevant_source_ids", [])),
            "forbidden_source_ids": list(case.get("forbidden_source_ids", [])),
            "coverage_status": case.get("coverage_audit", {}).get("status"),
        }
        for variant in case.get("variants", []):
            variant_id = str(variant.get("variant_id", ""))
            subjects[variant_id] = {
                "subject_id": variant_id,
                "parent_case_id": case_id,
                "kind": str(variant.get("kind", "")),
                "retrieval_allowed": variant.get("retrieval_allowed") is True,
                "relevant_source_ids": list(variant.get("relevant_source_ids", [])),
                "forbidden_source_ids": list(variant.get("forbidden_source_ids", [])),
                "coverage_status": variant.get("coverage_audit", {}).get("status"),
            }
    return subjects


def _observation_index(
    coverage: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    observations = list(coverage.get("observations", [])) + list(
        coverage.get("variant_observations", [])
    )
    ids = [str(item.get("variant_id") or item.get("case_id") or "") for item in observations]
    return {subject_id: item for subject_id, item in zip(ids, observations, strict=True)}, ids


def _label_state(subject: dict[str, Any]) -> str:
    if subject["relevant_source_ids"]:
        return "support"
    if subject["coverage_status"] == "reviewed_no_eligible_evidence":
        return "no_evidence"
    return "pending"


def evaluate_canonical_retrieval(
    contract: dict[str, Any],
    policy: dict[str, Any],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    """Score release-matched retrieval without treating candidates as approved evidence."""

    structural_failures: list[str] = []
    binding = policy.get("contract_binding", {})
    coverage_binding = policy.get("coverage_binding", {})
    if policy.get("schema_version") != "1.0.0":
        structural_failures.append("policy_schema_version")
    if binding.get("contract_id") != contract.get("contract_id"):
        structural_failures.append("policy_contract_id")
    if binding.get("contract_sha256") != contract.get("content_sha256"):
        structural_failures.append("policy_contract_sha256")
    if coverage.get("contract_id") != contract.get("contract_id"):
        structural_failures.append("coverage_contract_id")
    if coverage.get("contract_sha256") != contract.get("content_sha256"):
        structural_failures.append("coverage_contract_sha256")
    if coverage_binding.get("auditor_version") != coverage.get("auditor_version"):
        structural_failures.append("coverage_auditor_version")
    if sorted(coverage_binding.get("active_release_ids", [])) != sorted(
        coverage.get("active_release_ids", [])
    ):
        structural_failures.append("coverage_active_release_ids")
    if coverage.get("provider_calls") != 0:
        structural_failures.append("coverage_provider_calls")
    if coverage.get("paid_usage_usd") != 0:
        structural_failures.append("coverage_paid_usage")
    scope = policy.get("scope", {})
    if scope.get("top_k") != 6 or scope.get("ranking_unit") != "source_id":
        structural_failures.append("policy_ranking_scope")
    for field, expected in {
        "retrieval_only": True,
        "answer_generation": False,
        "retrieval_rescue": False,
        "model_planner": False,
        "evaluation_data_is_retrieval_corpus": False,
        "evaluation_data_is_training_data": False,
        "candidate_hits_are_clinical_support": False,
    }.items():
        if scope.get(field) is not expected:
            structural_failures.append(f"policy_scope:{field}")

    subjects = _subject_index(contract)
    observations, observation_ids = _observation_index(coverage)
    for duplicate in sorted(_duplicates(observation_ids)):
        structural_failures.append(f"duplicate_observation:{duplicate}")
    expected_ids = set(subjects)
    observed_ids = set(observation_ids)
    for missing in sorted(expected_ids - observed_ids):
        structural_failures.append(f"missing_observation:{missing}")
    for unexpected in sorted(observed_ids - expected_ids):
        structural_failures.append(f"unexpected_observation:{unexpected}")

    readiness_failures: list[str] = []
    if contract.get("frozen") is not True:
        readiness_failures.append("contract_not_frozen")
    contract_review = contract.get("review", {})
    for field in (
        "clinical_status",
        "native_simplified_chinese_status",
        "product_status",
    ):
        if contract_review.get(field) != "approved":
            readiness_failures.append(f"contract_review_pending:{field}")
    policy_review = policy.get("review", {})
    for field in (
        "clinical_status",
        "native_simplified_chinese_status",
        "product_status",
    ):
        if policy_review.get(field) != "approved":
            readiness_failures.append(f"policy_review_pending:{field}")
    if all(
        policy_review.get(field) == "approved"
        for field in (
            "clinical_status",
            "native_simplified_chinese_status",
            "product_status",
        )
    ) and (not policy_review.get("reviewer_ids") or not policy_review.get("reviewed_at")):
        readiness_failures.append("policy_review_provenance")
    if all(
        contract_review.get(field) == "approved"
        for field in (
            "clinical_status",
            "native_simplified_chinese_status",
            "product_status",
        )
    ) and (
        not contract_review.get("reviewer_id")
        or not contract_review.get("reviewer_role")
        or not contract_review.get("reviewed_at")
    ):
        readiness_failures.append("contract_review_provenance")

    eligible_subjects = [item for item in subjects.values() if item["retrieval_allowed"]]
    pre_safety_subjects = [item for item in subjects.values() if not item["retrieval_allowed"]]
    support_subjects: list[dict[str, Any]] = []
    no_evidence_subjects: list[dict[str, Any]] = []
    for subject in eligible_subjects:
        state = _label_state(subject)
        if state == "support":
            support_subjects.append(subject)
        elif state == "no_evidence":
            no_evidence_subjects.append(subject)
        else:
            readiness_failures.append(f"source_label_pending:{subject['subject_id']}")

    minimum_support_count = int(policy.get("thresholds", {}).get("minimum_support_label_count", 0))
    if len(support_subjects) < minimum_support_count:
        readiness_failures.append("support_label_count")
    symptom_support = [item for item in support_subjects if item["kind"] == "symptom_only"]
    minimum_symptom_count = int(
        policy.get("thresholds", {}).get("minimum_symptom_only_support_label_count", 0)
    )
    if len(symptom_support) < minimum_symptom_count:
        readiness_failures.append("symptom_only_support_label_count")

    retrieval_errors = sum(
        1
        for subject in eligible_subjects
        if observations.get(subject["subject_id"], {}).get("audit_status") == "retrieval_error"
    )
    pre_safety_zero_calls = _rate(
        pre_safety_subjects,
        lambda subject: (
            int(observations.get(subject["subject_id"], {}).get("retrieval_call_count", -1)) == 0
        ),
    )
    forbidden_source_hits: list[dict[str, str]] = []
    for subject in subjects.values():
        observed_sources = observations.get(subject["subject_id"], {}).get(
            "candidate_source_ids", []
        )
        for source_id in sorted(set(observed_sources) & set(subject["forbidden_source_ids"])):
            forbidden_source_hits.append(
                {"subject_id": subject["subject_id"], "source_id": source_id}
            )

    per_support: dict[str, dict[str, float | bool]] = {}
    for subject in support_subjects:
        observation = observations.get(subject["subject_id"], {})
        retrieved = list(observation.get("candidate_source_ids", []))
        relevant = set(subject["relevant_source_ids"])
        hits = relevant & set(retrieved)
        ranks = [index + 1 for index, value in enumerate(retrieved) if value in relevant]
        per_support[subject["subject_id"]] = {
            "recall_at_6": len(hits) / len(relevant),
            "reciprocal_rank": 1 / min(ranks) if ranks else 0.0,
            "decision_and_relevance_pass": bool(hits)
            and observation.get("decision") == "sufficient",
        }

    paired_comparisons: list[bool] = []
    for subject in support_subjects:
        parent_id = subject["parent_case_id"]
        if not parent_id or parent_id not in per_support:
            continue
        paired_comparisons.append(
            float(per_support[subject["subject_id"]]["recall_at_6"])
            >= float(per_support[parent_id]["recall_at_6"])
        )

    eligible_observations = [
        observations.get(subject["subject_id"], {}) for subject in eligible_subjects
    ]
    latencies = [int(item.get("retrieval_latency_ms", 0)) for item in eligible_observations]

    def candidate_sufficient(subject: dict[str, Any]) -> bool:
        return observations.get(subject["subject_id"], {}).get("decision") == "sufficient"

    thresholds = policy.get("thresholds", {})
    required_thresholds = {
        "minimum_support_label_count",
        "minimum_symptom_only_support_label_count",
        "minimum_source_label_readiness_rate",
        "minimum_relevant_source_recall_at_6",
        "minimum_mean_reciprocal_rank",
        "minimum_relevant_decision_pass_rate",
        "minimum_symptom_only_relevant_source_recall_at_6",
        "minimum_paired_variant_non_degradation_rate",
        "minimum_paired_variant_comparison_count",
        "minimum_no_evidence_precision",
        "minimum_pre_safety_zero_retrieval_rate",
        "maximum_forbidden_source_hits",
        "maximum_retrieval_errors",
        "maximum_retrieval_latency_p95_ms",
        "maximum_single_subject_latency_ms",
        "maximum_provider_calls",
        "maximum_paid_usage_usd",
    }
    for missing in sorted(required_thresholds - set(thresholds)):
        structural_failures.append(f"missing_threshold:{missing}")
    metrics: dict[str, Any] = {
        "canonical_subject_count": len(contract.get("cases", [])),
        "variant_subject_count": sum(
            len(case.get("variants", [])) for case in contract.get("cases", [])
        ),
        "retrieval_eligible_subject_count": len(eligible_subjects),
        "pre_safety_subject_count": len(pre_safety_subjects),
        "support_label_count": len(support_subjects),
        "no_evidence_label_count": len(no_evidence_subjects),
        "source_label_readiness_rate": (
            (len(support_subjects) + len(no_evidence_subjects)) / len(eligible_subjects)
            if eligible_subjects
            else 1.0
        ),
        "candidate_sufficiency_rate": _rate(eligible_subjects, candidate_sufficient),
        "symptom_only_candidate_sufficiency_rate": _rate(
            [item for item in eligible_subjects if item["kind"] == "symptom_only"],
            candidate_sufficient,
        ),
        "relevant_source_recall_at_6": _mean(
            [float(item["recall_at_6"]) for item in per_support.values()]
        ),
        "mean_reciprocal_rank": _mean(
            [float(item["reciprocal_rank"]) for item in per_support.values()]
        ),
        "relevant_decision_pass_rate": _rate(
            list(per_support.values()),
            lambda item: bool(item["decision_and_relevance_pass"]),
        )
        if per_support
        else None,
        "symptom_only_relevant_source_recall_at_6": _mean(
            [float(per_support[item["subject_id"]]["recall_at_6"]) for item in symptom_support]
        ),
        "paired_variant_non_degradation_rate": _rate(paired_comparisons, lambda passed: passed)
        if paired_comparisons
        else None,
        "paired_variant_comparison_count": len(paired_comparisons),
        "no_evidence_precision": _rate(
            no_evidence_subjects,
            lambda subject: (
                observations.get(subject["subject_id"], {}).get("decision")
                == "no_eligible_evidence"
            ),
        ),
        "pre_safety_zero_retrieval_rate": pre_safety_zero_calls,
        "forbidden_source_hit_count": len(forbidden_source_hits),
        "retrieval_error_count": retrieval_errors,
        "retrieval_latency_p95_ms": _percentile_95(latencies),
        "retrieval_latency_max_ms": max(latencies, default=0),
        "provider_call_count": int(coverage.get("provider_calls", 0)),
        "paid_usage_usd": float(coverage.get("paid_usage_usd", 0)),
    }

    metric_failures: list[str] = []

    def require_minimum(name: str, threshold_name: str) -> None:
        value = metrics[name]
        if value is None:
            metric_failures.append(f"unscored:{name}")
        elif threshold_name not in thresholds or float(value) < float(thresholds[threshold_name]):
            metric_failures.append(name)

    require_minimum("source_label_readiness_rate", "minimum_source_label_readiness_rate")
    require_minimum("relevant_source_recall_at_6", "minimum_relevant_source_recall_at_6")
    require_minimum("mean_reciprocal_rank", "minimum_mean_reciprocal_rank")
    require_minimum("relevant_decision_pass_rate", "minimum_relevant_decision_pass_rate")
    require_minimum(
        "symptom_only_relevant_source_recall_at_6",
        "minimum_symptom_only_relevant_source_recall_at_6",
    )
    require_minimum(
        "paired_variant_non_degradation_rate",
        "minimum_paired_variant_non_degradation_rate",
    )
    require_minimum("no_evidence_precision", "minimum_no_evidence_precision")
    require_minimum("pre_safety_zero_retrieval_rate", "minimum_pre_safety_zero_retrieval_rate")
    for metric_name, threshold_name in (
        ("forbidden_source_hit_count", "maximum_forbidden_source_hits"),
        ("retrieval_error_count", "maximum_retrieval_errors"),
        ("retrieval_latency_p95_ms", "maximum_retrieval_latency_p95_ms"),
        ("retrieval_latency_max_ms", "maximum_single_subject_latency_ms"),
        ("provider_call_count", "maximum_provider_calls"),
        ("paid_usage_usd", "maximum_paid_usage_usd"),
    ):
        if threshold_name not in thresholds or float(metrics[metric_name]) > float(
            thresholds[threshold_name]
        ):
            metric_failures.append(metric_name)
    if len(paired_comparisons) < int(
        thresholds.get("minimum_paired_variant_comparison_count", len(paired_comparisons) + 1)
    ):
        metric_failures.append("paired_variant_comparison_count")

    return {
        "passed": not structural_failures and not readiness_failures and not metric_failures,
        "structural_failures": structural_failures,
        "readiness_failures": readiness_failures,
        "metric_failures": metric_failures,
        "metrics": metrics,
        "forbidden_source_hits": forbidden_source_hits,
        "scored_support_subjects": per_support,
        "clinical_approval_claimed": False,
        "eligible_evidence_claimed": False,
    }
