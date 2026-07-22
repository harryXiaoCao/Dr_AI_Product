from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.chatbot_contracts import SafetyCode
from app.clinical_presentation import (
    assess_safety,
    extract_clinical_presentation,
    resolve_bounded_user_continuity,
)
from app.patient_chat import _safety_route

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")
PRESENTATION_FIELDS = {
    "symptoms",
    "anatomy",
    "onset",
    "duration",
    "trajectory",
    "severity",
    "associated_signs",
    "measurements",
    "population",
    "pregnancy",
    "exposures",
    "trauma",
    "requested_actions",
    "danger_signals",
    "negated_concepts",
    "hypothetical_concepts",
}


def _checksum(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "content_sha256"}
    return hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def _observed_route(message: str) -> tuple[str, str | None]:
    assessment = assess_safety(message)
    safety_code = _safety_route(message, assessment)
    if safety_code == SafetyCode.emergency:
        return "emergency_120", assessment.rule_id
    if safety_code == SafetyCode.prohibited_medication_change:
        return "prohibited_medication_change", assessment.rule_id
    return assessment.urgency_route.value, assessment.rule_id


def _presentation_payload(message: str) -> dict[str, list[str]]:
    presentation = extract_clinical_presentation(message)
    return {
        field: list(getattr(presentation, field)) for field in PRESENTATION_FIELDS
    }


def _variant_analysis_message(variant: dict[str, Any]) -> str:
    if variant.get("text"):
        return str(variant["text"])
    previous_user_messages: list[str] = []
    analysis_message = ""
    for turn in variant.get("turns") or []:
        turn_text = str(turn)
        resolution = resolve_bounded_user_continuity(turn_text, previous_user_messages)
        analysis_message = resolution.analysis_message
        previous_user_messages.append(turn_text)
    return analysis_message


def _variant_observed_route(variant: dict[str, Any]) -> tuple[str, str | None]:
    return _observed_route(_variant_analysis_message(variant))


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    structural_failures: list[str] = []
    if payload.get("schema_version") != "1.2.0":
        structural_failures.append("schema_version")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 100:
        structural_failures.append("case_count")
        cases = cases if isinstance(cases, list) else []
    expected_ids = [f"RCQ-{number:03d}" for number in range(1, 101)]
    if [case.get("case_id") for case in cases] != expected_ids:
        structural_failures.append("case_id_sequence")
    if payload.get("content_sha256") != _checksum(payload):
        structural_failures.append("content_sha256")
    if payload.get("separation_policy") != {
        "evaluation_only": True,
        "retrieval_corpus": False,
        "training_data": False,
        "must_not_be_indexed": True,
        "must_not_be_sent_as_model_evidence": True,
    }:
        structural_failures.append("separation_policy")
    answer_policy = payload.get("complete_answer_evaluation_policy")
    if not isinstance(answer_policy, dict):
        structural_failures.append("complete_answer_evaluation_policy")
    else:
        if answer_policy.get("evaluated_separately_from") != [
            "deterministic_safety_routing",
            "retrieval_only",
            "retrieval_rescue",
        ]:
            structural_failures.append("complete_answer_evaluation_separation")
        execution = answer_policy.get("execution", {})
        if execution.get("provider_mode") != "one_provider_at_a_time":
            structural_failures.append("complete_answer_provider_mode")
        if execution.get("maximum_concurrency") != 1:
            structural_failures.append("complete_answer_concurrency")
        human_review = answer_policy.get("human_review", {})
        if not (
            human_review.get("required") is True
            and human_review.get("independent_from_ai_judge") is True
            and human_review.get("ai_judge_may_not_close_gate") is True
        ):
            structural_failures.append("complete_answer_human_review")

    variant_policy = payload.get("variant_evaluation_policy")
    if not isinstance(variant_policy, dict):
        structural_failures.append("variant_evaluation_policy")
        variant_policy = {}
    allowed_variant_kinds = set(variant_policy.get("allowed_kinds", []))
    minimum_kind_counts = variant_policy.get("minimum_kind_counts", {})
    if allowed_variant_kinds != {
        "symptom_only",
        "disease_name_removed",
        "colloquial",
        "abbreviated",
        "multi_turn",
    }:
        structural_failures.append("variant_allowed_kinds")
    if not isinstance(minimum_kind_counts, dict):
        structural_failures.append("variant_minimum_kind_counts")
        minimum_kind_counts = {}
    if not (
        variant_policy.get("maximum_previous_user_turns") == 1
        and variant_policy.get("assistant_turns_allowed") is False
        and variant_policy.get("current_literal_query_must_be_preserved") is True
        and variant_policy.get("clinical_native_chinese_and_product_review_required")
        is True
    ):
        structural_failures.append("variant_continuity_and_review_policy")

    source_profiles = payload.get("source_policy_profiles", {})
    behavior_profiles = payload.get("required_answer_behavior_profiles", {})
    critical_ids = set(payload.get("critical_case_ids", []))
    canonical_emergency_total = 0
    canonical_emergency_hits = 0
    non_emergency_total = 0
    non_emergency_false_positives = 0
    variant_emergency_total = 0
    variant_emergency_hits = 0
    canonical_route_hits = 0
    variant_route_total = 0
    variant_route_hits = 0
    variant_kind_counts: Counter[str] = Counter()
    variant_ids_seen: set[str] = set()
    multi_turn_domains: set[str] = set()
    multi_turn_routes: set[str] = set()
    observations: list[dict[str, Any]] = []

    for case in cases:
        case_id = case.get("case_id")
        route = case.get("expected_urgency_route")
        if case.get("source_policy_profile") not in source_profiles:
            structural_failures.append(f"{case_id}:source_policy_profile")
        if case.get("required_answer_behavior_profile") not in behavior_profiles:
            structural_failures.append(f"{case_id}:behavior_profile")
        presentation = case.get("presentation_concepts")
        if not isinstance(presentation, dict) or set(presentation) != PRESENTATION_FIELDS:
            structural_failures.append(f"{case_id}:presentation_fields")
        elif any(not isinstance(presentation[field], list) for field in PRESENTATION_FIELDS):
            structural_failures.append(f"{case_id}:presentation_field_type")
        elif presentation != _presentation_payload(str(case.get("canonical_question", ""))):
            structural_failures.append(f"{case_id}:presentation_annotation_drift")
        expected_no_calls = route in {
            "emergency_120",
            "prohibited_medication_change",
        }
        if expected_no_calls and (case.get("retrieval_allowed") or case.get("model_allowed")):
            structural_failures.append(f"{case_id}:pre_gate_call_permission")
        if route == "emergency_120" and case_id not in critical_ids:
            structural_failures.append(f"{case_id}:critical_set_membership")

        question = str(case.get("canonical_question", ""))
        observed_route, rule_id = _observed_route(question)
        observed_emergency = observed_route == "emergency_120"
        canonical_route_hits += int(observed_route == route)
        if route == "emergency_120":
            canonical_emergency_total += 1
            canonical_emergency_hits += int(observed_emergency)
        else:
            non_emergency_total += 1
            non_emergency_false_positives += int(observed_emergency)
        observations.append(
            {
                "case_id": case_id,
                "expected_route": route,
                "observed_route": observed_route,
                "observed_emergency": observed_emergency,
                "rule_id": rule_id,
            }
        )
        for index, variant in enumerate(case.get("variants", []), start=1):
            variant_id = variant.get("variant_id")
            expected_variant_id = f"{case_id}-V{index:02d}"
            if variant_id != expected_variant_id or variant_id in variant_ids_seen:
                structural_failures.append(f"{variant_id}:identity")
            if isinstance(variant_id, str):
                variant_ids_seen.add(variant_id)
            kind = variant.get("kind")
            if kind not in allowed_variant_kinds:
                structural_failures.append(f"{variant_id}:kind")
            elif isinstance(kind, str):
                variant_kind_counts[kind] += 1
            text = variant.get("text")
            turns = variant.get("turns")
            if kind == "multi_turn":
                if text is not None or not isinstance(turns, list) or len(turns) != 2:
                    structural_failures.append(f"{variant_id}:multi_turn_shape")
                elif any(not isinstance(turn, str) or not turn.strip() for turn in turns):
                    structural_failures.append(f"{variant_id}:multi_turn_content")
                multi_turn_domains.add(str(case.get("domain")))
                multi_turn_routes.add(str(route))
            elif (
                not isinstance(text, str)
                or not text.strip()
                or turns != []
            ):
                structural_failures.append(f"{variant_id}:single_turn_shape")
            if variant.get("parent_case_id") != case_id:
                structural_failures.append(f"{variant_id}:parent")
            if variant.get("domain") != case.get("domain"):
                structural_failures.append(f"{variant_id}:domain")
            if variant.get("expected_route") != route:
                structural_failures.append(f"{variant_id}:route")
            if variant.get("source_policy_profile") != case.get("source_policy_profile"):
                structural_failures.append(f"{variant_id}:source_policy_profile")
            if variant.get("required_answer_behavior_profile") != route:
                structural_failures.append(f"{variant_id}:behavior_profile")
            if variant.get("relevant_source_ids") != case.get("relevant_source_ids"):
                structural_failures.append(f"{variant_id}:relevant_source_ids")
            if variant.get("forbidden_source_ids") != case.get("forbidden_source_ids"):
                structural_failures.append(f"{variant_id}:forbidden_source_ids")
            if (
                variant.get("retrieval_allowed") != case.get("retrieval_allowed")
                or variant.get("model_allowed") != case.get("model_allowed")
            ):
                structural_failures.append(f"{variant_id}:call_permissions")
            if expected_no_calls and (
                variant.get("retrieval_allowed") or variant.get("model_allowed")
            ):
                structural_failures.append(f"{variant_id}:pre_gate_call_permission")
            variant_analysis_message = _variant_analysis_message(variant)
            variant_presentation = variant.get("presentation_concepts")
            if (
                not isinstance(variant_presentation, dict)
                or set(variant_presentation) != PRESENTATION_FIELDS
                or any(
                    not isinstance(variant_presentation[field], list)
                    for field in PRESENTATION_FIELDS
                )
            ):
                structural_failures.append(f"{variant_id}:presentation_fields")
            elif variant_presentation != _presentation_payload(variant_analysis_message):
                structural_failures.append(f"{variant_id}:presentation_annotation_drift")
            variant_observed_route, variant_rule_id = _variant_observed_route(variant)
            variant_route_total += 1
            variant_route_hits += int(variant_observed_route == route)
            observations.append(
                {
                    "case_id": variant.get("variant_id"),
                    "parent_case_id": case_id,
                    "expected_route": route,
                    "observed_route": variant_observed_route,
                    "observed_emergency": variant_observed_route == "emergency_120",
                    "rule_id": variant_rule_id,
                }
            )
            if route == "emergency_120":
                variant_emergency_total += 1
                variant_emergency_hits += int(variant_observed_route == "emergency_120")

    variant_count = sum(variant_kind_counts.values())
    minimum_total_variants = variant_policy.get("minimum_total_variants")
    if not isinstance(minimum_total_variants, int) or variant_count < minimum_total_variants:
        structural_failures.append("variant_minimum_total")
    for kind in sorted(allowed_variant_kinds):
        minimum = minimum_kind_counts.get(kind)
        if not isinstance(minimum, int) or variant_kind_counts[kind] < minimum:
            structural_failures.append(f"variant_minimum_kind:{kind}")
    if multi_turn_domains != set(variant_policy.get("required_multi_turn_domains", [])):
        structural_failures.append("multi_turn_domain_coverage")
    if multi_turn_routes != set(variant_policy.get("required_multi_turn_routes", [])):
        structural_failures.append("multi_turn_route_coverage")

    metrics = {
        "case_count": len(cases),
        "variant_count": variant_count,
        "variant_kind_counts": dict(sorted(variant_kind_counts.items())),
        "multi_turn_domain_count": len(multi_turn_domains),
        "multi_turn_route_count": len(multi_turn_routes),
        "candidate_canonical_route_accuracy": (
            canonical_route_hits / len(cases) if cases else 0.0
        ),
        "candidate_variant_route_accuracy": (
            variant_route_hits / variant_route_total if variant_route_total else 0.0
        ),
        "candidate_critical_case_count": canonical_emergency_total,
        "candidate_critical_emergency_recall": (
            canonical_emergency_hits / canonical_emergency_total
            if canonical_emergency_total
            else 0.0
        ),
        "candidate_critical_variant_count": variant_emergency_total,
        "candidate_critical_variant_emergency_recall": (
            variant_emergency_hits / variant_emergency_total if variant_emergency_total else 0.0
        ),
        "non_emergency_false_positive_rate": (
            non_emergency_false_positives / non_emergency_total if non_emergency_total else 0.0
        ),
    }
    metric_failures = []
    if metrics["candidate_critical_emergency_recall"] != 1.0:
        metric_failures.append("candidate_critical_emergency_recall")
    if variant_emergency_total and (metrics["candidate_critical_variant_emergency_recall"] != 1.0):
        metric_failures.append("candidate_critical_variant_emergency_recall")
    if metrics["non_emergency_false_positive_rate"] != 0.0:
        metric_failures.append("non_emergency_false_positive_rate")
    if metrics["candidate_canonical_route_accuracy"] != 1.0:
        metric_failures.append("candidate_canonical_route_accuracy")
    if variant_route_total and metrics["candidate_variant_route_accuracy"] != 1.0:
        metric_failures.append("candidate_variant_route_accuracy")
    return {
        "evaluator_version": "canonical-symptom-safety-and-urgency-v4-unified-authority",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": payload.get("contract_id"),
        "contract_status": payload.get("status"),
        "contract_sha256": payload.get("content_sha256"),
        "clinical_approval_claimed": False,
        "multi_turn_evaluation_mode": "sequential_bounded_user_turn_continuity",
        "metrics": metrics,
        "structural_failures": sorted(set(structural_failures)),
        "metric_failures": metric_failures,
        "passed_local_candidate_gate": not structural_failures and not metric_failures,
        "observations": observations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the candidate 100-case clinical presentation and safety contract."
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.contract.read_text(encoding="utf-8"))
    result = evaluate(payload)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed_local_candidate_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
