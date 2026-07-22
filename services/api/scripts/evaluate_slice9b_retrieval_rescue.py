from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai_chat import DeepSeekChatAdapter
from app.chatbot_contracts import PatientEvidenceRequest
from app.clinical_presentation import assess_safety, resolve_bounded_user_continuity
from app.config import get_settings
from app.database import engine
from app.knowledge_retrieval import retrieve
from app.retrieval_rescue import attempt_retrieval_rescue, choose_trigger

DEFAULT_SUITE = Path("knowledge_base/evaluation/retrieval_rescue_cases.slice9b.v2.json")
RUNNER_VERSION = "slice9b-retrieval-rescue-v4-presentation-aware-ambiguity"


def _load_and_validate(path: Path) -> dict[str, object]:
    suite = json.loads(path.read_text())
    if suite.get("schema_version") != "1.0" or not suite.get("suite_id"):
        raise SystemExit("The Slice 9B suite header is invalid.")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("The Slice 9B suite must contain cases.")
    ids = [item.get("case_id") for item in cases]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise SystemExit("Slice 9B case IDs must be present and unique.")
    if {item.get("kind") for item in cases} != {"hard", "ordinary"}:
        raise SystemExit("The suite must freeze both hard and ordinary-control cases.")
    if any(not item.get("query") or not item.get("relevant_source_ids") for item in cases):
        raise SystemExit("Every case requires a query and relevant source IDs.")
    if any("expected_trigger" not in item for item in cases):
        raise SystemExit("Every Slice 9B case must declare its expected trigger.")
    review = suite.get("review")
    if not isinstance(review, dict):
        raise SystemExit("The Slice 9B suite requires a review record.")
    if review.get("status") == "approved":
        required_review_fields = (
            "reviewer_id",
            "reviewer_role",
            "reviewed_at",
            "clinical_reviewer_id",
            "clinical_reviewer_role",
            "clinical_reviewed_at",
            "native_chinese_reviewer_id",
            "native_chinese_reviewed_at",
        )
        if any(not review.get(field) for field in required_review_fields):
            raise SystemExit("Approved Slice 9B review metadata is incomplete.")
        if review.get("corrections_required") not in {True, False}:
            raise SystemExit("Approved Slice 9B review must record correction status.")
    return suite


def _hit_count(source_ids: set[str], relevant: set[str]) -> int:
    return len(source_ids & relevant)


def _percentile_95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(0, round(0.95 * len(ordered) + 0.5) - 1)]


def _trusted_case_context(item: dict[str, object]):
    recent = [str(value) for value in item.get("recent_user_messages", [])]
    query = str(item["query"])
    continuity = resolve_bounded_user_continuity(query, recent)
    assessment = assess_safety(continuity.analysis_message)
    if assessment.urgency_route.value == "emergency_120":
        raise SystemExit(f"Slice 9B case {item['case_id']} became an emergency before retrieval.")
    presentation = assessment.presentation
    if presentation is None:
        raise SystemExit(f"Slice 9B case {item['case_id']} has no controlled presentation.")
    if continuity.carried_previous_user_turn:
        presentation = replace(presentation, literal_query=query)
    bounded_recent = recent[-1:] if continuity.carried_previous_user_turn else []
    return continuity, presentation, bounded_recent


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or run the frozen Slice 9B gate.")
    parser.add_argument("command", choices=("validate", "preflight", "run"))
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    suite = _load_and_validate(args.suite)
    if args.command == "validate":
        print(
            json.dumps(
                {
                    "suite_id": suite["suite_id"],
                    "case_count": len(suite["cases"]),
                    "review_status": suite["review"]["status"],
                    "valid": True,
                },
                indent=2,
            )
        )
        return 0
    if args.command == "run" and args.output is None:
        raise SystemExit("--output is required for a run.")
    if args.output is not None and args.output.exists():
        raise SystemExit("The output artifact already exists; refusing to overwrite evidence.")
    if suite["review"]["status"] != "approved":
        raise SystemExit("The frozen Slice 9B suite is not approved; run refused.")
    if not suite["review"].get("clinical_reviewer_qualification_verified"):
        raise SystemExit(
            "Product-owner approval is recorded, but qualified clinical review is not "
            "verified; run refused."
        )
    if not suite["review"].get("native_chinese_review_verified"):
        raise SystemExit(
            "Product-owner approval is recorded, but native-Chinese review is not "
            "verified; run refused."
        )
    settings = get_settings()
    if args.command == "preflight":
        preflight = []
        with Session(engine) as db:
            for item in suite["cases"]:
                _, presentation, _ = _trusted_case_context(item)
                request = PatientEvidenceRequest(query=item["query"], language="zh-Hans")
                baseline = retrieve(db, request, audience="patient", presentation=presentation)
                relevant = set(item["relevant_source_ids"])
                baseline_sources = {candidate.source.stable_id for candidate in baseline.candidates}
                baseline_hits = _hit_count(baseline_sources, relevant)
                trigger = choose_trigger(item["query"], baseline, settings)
                actual_trigger = trigger.value if trigger else None
                preflight.append(
                    {
                        "case_id": item["case_id"],
                        "kind": item["kind"],
                        "baseline_hit_count": baseline_hits,
                        "relevant_source_count": len(relevant),
                        "baseline_improvable": baseline_hits < len(relevant),
                        "expected_trigger": item["expected_trigger"],
                        "trigger": actual_trigger,
                        "trigger_matches": actual_trigger == item["expected_trigger"],
                    }
                )
            db.rollback()
        failures = []
        if any(item["kind"] == "hard" and not item["baseline_improvable"] for item in preflight):
            failures.append("hard_case_not_improvable")
        if any(not item["trigger_matches"] for item in preflight):
            failures.append("trigger_mismatch")
        artifact = {
            "suite_id": suite["suite_id"],
            "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
            "runner_version": RUNNER_VERSION,
            "mode": "structural_preflight",
            "evaluated_at": datetime.now(UTC).isoformat(),
            "safety_gate_before_retrieval": True,
            "trusted_presentation_retry": True,
            "presentation_aware_ambiguity_trigger": True,
            "maximum_admitted_previous_user_turns": 1,
            "model_calls": 0,
            "provider_reported_tokens": 0,
            "cost_microunits": 0,
            "passed": not failures,
            "failures": failures,
            "observations": preflight,
        }
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
        return 0 if not failures else 1
    if settings.deepseek_api_key is None:
        raise SystemExit("DR_AI_DEEPSEEK_API_KEY is required for the live rescue gate.")
    observations = []
    adapter = DeepSeekChatAdapter()
    with Session(engine) as db:
        for item in suite["cases"]:
            continuity, presentation, bounded_recent = _trusted_case_context(item)
            request = PatientEvidenceRequest(query=item["query"], language="zh-Hans")
            baseline = retrieve(db, request, audience="patient", presentation=presentation)
            rescued = attempt_retrieval_rescue(
                db,
                original_message=item["query"],
                language="zh-Hans",
                request=request,
                initial=baseline,
                recent_user_messages=bounded_recent,
                trusted_presentation=presentation,
                trusted_context_message=continuity.analysis_message,
                settings=settings,
                adapter=adapter,
            )
            relevant = set(item["relevant_source_ids"])
            baseline_sources = {candidate.source.stable_id for candidate in baseline.candidates}
            rescued_sources = {
                candidate.source.stable_id for candidate in rescued.retrieval.candidates
            }
            baseline_hits = _hit_count(baseline_sources, relevant)
            rescued_hits = _hit_count(rescued_sources, relevant)
            actual_trigger = rescued.metadata.trigger.value if rescued.metadata.trigger else None
            observations.append(
                {
                    "case_id": item["case_id"],
                    "kind": item["kind"],
                    "baseline_hit_count": baseline_hits,
                    "rescued_hit_count": rescued_hits,
                    "non_degraded": rescued_hits >= baseline_hits,
                    "improved": rescued_hits > baseline_hits,
                    "baseline_improvable": baseline_hits < len(relevant),
                    "expected_trigger": item["expected_trigger"],
                    "trigger": actual_trigger,
                    "trigger_matches": actual_trigger == item["expected_trigger"],
                    "outcome": rescued.metadata.outcome.value,
                    "planner_used": rescued.metadata.planner_model is not None,
                    "context_dominant": rescued.metadata.context_dominant,
                    "resolved_topic_evidence_only": (rescued.metadata.resolved_topic_evidence_only),
                    "planner_latency_ms": rescued.metadata.planner_latency_ms,
                    "retry_latency_ms": rescued.metadata.retry_latency_ms,
                    "latency_ms": rescued.metadata.latency_ms,
                    "cost_microunits": rescued.metadata.cost_microunits,
                    "index_release_id": baseline.release.stable_id,
                }
            )
        db.rollback()
    hard = [item for item in observations if item["kind"] == "hard"]
    ordinary = [item for item in observations if item["kind"] == "ordinary"]
    attempted = [item for item in observations if item["trigger"] is not None]
    hard_rate = sum(item["improved"] for item in hard) / len(hard)
    ordinary_rate = sum(item["non_degraded"] for item in ordinary) / len(ordinary)
    trigger_rate = sum(item["trigger_matches"] for item in observations) / len(observations)
    planner_attempt_count = sum(item["planner_used"] for item in observations)
    improved_observations = [item for item in observations if item["improved"]]
    context_resolved = [
        item
        for item in improved_observations
        if item["trigger"] in {"short_reference", "ambiguous"}
    ]
    context_dominant_rate = (
        sum(item["context_dominant"] is True for item in context_resolved) / len(context_resolved)
        if context_resolved
        else 1.0
    )
    resolved_topic_evidence_rate = (
        sum(item["resolved_topic_evidence_only"] is True for item in improved_observations)
        / len(improved_observations)
        if improved_observations
        else 1.0
    )
    latency_p95 = _percentile_95([item["latency_ms"] for item in attempted])
    costs = [item["cost_microunits"] for item in attempted if item["cost_microunits"] is not None]
    average_cost = statistics.fmean(costs) if costs else 0.0
    thresholds = suite["thresholds"]
    failures = []
    if any(not item["baseline_improvable"] for item in hard):
        failures.append("hard_case_not_improvable")
    if any(
        item["baseline_hit_count"] < len(case["relevant_source_ids"])
        for item, case in zip(observations, suite["cases"], strict=True)
        if item["kind"] == "ordinary"
    ):
        failures.append("ordinary_baseline_relevance")
    if hard_rate < thresholds["minimum_hard_query_improvement_rate"]:
        failures.append("hard_query_improvement_rate")
    if ordinary_rate < thresholds["minimum_ordinary_non_degradation_rate"]:
        failures.append("ordinary_non_degradation_rate")
    if trigger_rate < thresholds["minimum_trigger_match_rate"]:
        failures.append("trigger_match_rate")
    if planner_attempt_count < thresholds["minimum_planner_attempt_count"]:
        failures.append("planner_attempt_count")
    if context_dominant_rate < 1.0:
        failures.append("context_dominant_invariant")
    if resolved_topic_evidence_rate < 1.0:
        failures.append("resolved_topic_evidence_invariant")
    if latency_p95 > thresholds["maximum_rescue_latency_p95_ms"]:
        failures.append("rescue_latency_p95_ms")
    if average_cost > thresholds["maximum_average_rescue_cost_microunits"]:
        failures.append("average_rescue_cost_microunits")
    artifact = {
        "suite_id": suite["suite_id"],
        "suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
        "runner_version": RUNNER_VERSION,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "review": suite["review"],
        "presentation_aware_ambiguity_trigger": True,
        "metrics": {
            "hard_query_improvement_rate": hard_rate,
            "ordinary_non_degradation_rate": ordinary_rate,
            "trigger_match_rate": trigger_rate,
            "planner_attempt_count": planner_attempt_count,
            "context_dominant_pass_rate": context_dominant_rate,
            "resolved_topic_evidence_pass_rate": resolved_topic_evidence_rate,
            "rescue_latency_p95_ms": latency_p95,
            "average_rescue_cost_microunits": average_cost,
        },
        "failures": failures,
        "passed": not failures,
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
