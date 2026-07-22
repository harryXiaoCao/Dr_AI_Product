from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.chatbot_contracts import PatientEvidenceRequest
from app.clinical_presentation import assess_safety, resolve_bounded_user_continuity
from app.database import engine
from app.errors import ApiError
from app.knowledge_retrieval import retrieve

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")


def _patient_request(query: str) -> PatientEvidenceRequest:
    return PatientEvidenceRequest(
        query=query,
        language="zh-Hans",
        jurisdiction="CN",
        excluded_content_types=[
            "clinical_guideline_doctor_only",
            "raw_clinical_record",
            "prescriber_only_medicine_content",
        ],
    )


def _retrieve_sequential_variant(
    db: Session,
    turns: list[str],
) -> tuple[Any | None, str | None, list[dict[str, Any]]]:
    """Run each synthetic user turn through production-shared continuity.

    The evaluator deliberately performs no model or rescue-planner call. Each
    retrieval uses the current turn as the literal query while its controlled
    presentation may include the immediately preceding user turn.
    """

    previous_user_messages: list[str] = []
    final_result = None
    final_error_code = None
    trace: list[dict[str, Any]] = []
    for index, turn in enumerate(turns, start=1):
        resolution = resolve_bounded_user_continuity(turn, previous_user_messages)
        assessment = assess_safety(resolution.analysis_message)
        presentation = assessment.presentation
        if presentation is not None and resolution.carried_previous_user_turn:
            presentation = replace(presentation, literal_query=resolution.literal_query)
        item: dict[str, Any] = {
            "turn_index": index,
            "continuity_reason": resolution.reason.value,
            "carried_previous_user_turn": resolution.carried_previous_user_turn,
            "literal_query_preserved": (presentation is None or presentation.literal_query == turn),
            "safety_route": assessment.urgency_route.value,
            "retrieval_attempted": False,
        }
        if assessment.urgency_route.value == "emergency_120":
            final_result = None
            final_error_code = None
            item["retrieval_outcome"] = "bypassed_pre_safety"
        else:
            item["retrieval_attempted"] = True
            try:
                final_result = retrieve(
                    db,
                    _patient_request(turn),
                    audience="patient",
                    presentation=presentation,
                )
            except ApiError as exc:
                final_result = None
                final_error_code = exc.code
                item["retrieval_outcome"] = "retrieval_error"
                item["error_code"] = exc.code
            else:
                final_error_code = None
                item["retrieval_outcome"] = final_result.decision.value
                item["retrieval_view_kinds"] = list(final_result.view_kinds)
                item["literal_candidate_count"] = final_result.literal_candidate_count
                item["retrieval_latency_ms"] = final_result.latency_ms
        trace.append(item)
        previous_user_messages.append(turn)
    return final_result, final_error_code, trace


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the active patient release against the 100-case candidate contract. "
            "Retrieved sources remain candidates until case-specific clinical review."
        )
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-cases", type=int, default=100)
    args = parser.parse_args()
    payload: dict[str, Any] = json.loads(args.contract.read_text(encoding="utf-8"))
    observations = []
    variant_observations = []
    release_ids: set[str] = set()
    decision_counts: Counter[str] = Counter()
    variant_decision_counts: Counter[str] = Counter()

    with Session(engine) as db:
        for case in payload["cases"][: args.max_cases]:
            if not case["retrieval_allowed"]:
                decision_counts["not_applicable_pre_safety"] += 1
                observations.append(
                    {
                        "case_id": case["case_id"],
                        "audit_status": "not_applicable_pre_safety",
                        "decision": None,
                        "candidate_source_ids": [],
                        "clinically_relevant_source_ids": [],
                        "clinical_relevance_review_status": "pending",
                        "retrieval_view_kinds": [],
                        "literal_candidate_count": 0,
                        "retrieval_call_count": 0,
                        "retrieval_latency_ms": 0,
                    }
                )
                continue
            result, error_code, turn_trace = _retrieve_sequential_variant(
                db, [str(case["canonical_question"])]
            )
            if error_code is not None:
                decision_counts["retrieval_error"] += 1
                observations.append(
                    {
                        "case_id": case["case_id"],
                        "audit_status": "retrieval_error",
                        "decision": None,
                        "error_code": error_code,
                        "candidate_source_ids": [],
                        "clinically_relevant_source_ids": [],
                        "clinical_relevance_review_status": "pending",
                        "retrieval_view_kinds": [],
                        "literal_candidate_count": 0,
                        "retrieval_call_count": 1,
                        "retrieval_latency_ms": 0,
                        "turn_trace": turn_trace,
                    }
                )
                continue
            if result is None:
                decision_counts["unexpected_pre_safety_bypass"] += 1
                observations.append(
                    {
                        "case_id": case["case_id"],
                        "audit_status": "unexpected_pre_safety_bypass",
                        "decision": None,
                        "candidate_source_ids": [],
                        "clinically_relevant_source_ids": [],
                        "clinical_relevance_review_status": "pending",
                        "retrieval_view_kinds": [],
                        "literal_candidate_count": 0,
                        "retrieval_call_count": 0,
                        "retrieval_latency_ms": 0,
                        "turn_trace": turn_trace,
                    }
                )
                continue
            release_ids.add(result.release.stable_id)
            decision_counts[result.decision.value] += 1
            observations.append(
                {
                    "case_id": case["case_id"],
                    "audit_status": (
                        "candidate_support_pending_case_review"
                        if result.candidates
                        else "no_released_evidence"
                    ),
                    "decision": result.decision.value,
                    "candidate_source_ids": list(
                        dict.fromkeys(item.source.stable_id for item in result.candidates)
                    ),
                    "candidate_jurisdictions": list(
                        dict.fromkeys(item.source.jurisdiction for item in result.candidates)
                    ),
                    "candidate_languages": list(
                        dict.fromkeys(item.passage.language for item in result.candidates)
                    ),
                    "clinically_relevant_source_ids": [],
                    "clinical_relevance_review_status": "pending",
                    "retrieval_view_kinds": list(result.view_kinds),
                    "literal_candidate_count": result.literal_candidate_count,
                    "retrieval_call_count": 1,
                    "retrieval_latency_ms": result.latency_ms,
                    "turn_trace": turn_trace,
                }
            )

        for case in payload["cases"][: args.max_cases]:
            for variant in case["variants"]:
                base = {
                    "case_id": case["case_id"],
                    "variant_id": variant["variant_id"],
                    "variant_kind": variant["kind"],
                }
                if not variant["retrieval_allowed"]:
                    variant_decision_counts["not_applicable_pre_safety"] += 1
                    variant_observations.append(
                        {
                            **base,
                            "audit_status": "not_applicable_pre_safety",
                            "decision": None,
                            "candidate_source_ids": [],
                            "clinically_relevant_source_ids": [],
                            "clinical_relevance_review_status": "pending",
                            "retrieval_view_kinds": [],
                            "literal_candidate_count": 0,
                            "retrieval_call_count": 0,
                            "retrieval_latency_ms": 0,
                        }
                    )
                    continue
                turns = [str(variant["text"])] if variant["text"] else list(variant["turns"])
                result, error_code, turn_trace = _retrieve_sequential_variant(db, turns)
                if error_code is not None:
                    variant_decision_counts["retrieval_error"] += 1
                    variant_observations.append(
                        {
                            **base,
                            "audit_status": "retrieval_error",
                            "decision": None,
                            "error_code": error_code,
                            "candidate_source_ids": [],
                            "clinically_relevant_source_ids": [],
                            "clinical_relevance_review_status": "pending",
                            "retrieval_view_kinds": [],
                            "literal_candidate_count": 0,
                            "retrieval_call_count": sum(
                                bool(item["retrieval_attempted"]) for item in turn_trace
                            ),
                            "retrieval_latency_ms": sum(
                                int(item.get("retrieval_latency_ms", 0)) for item in turn_trace
                            ),
                            "input_mode": (
                                "sequential_bounded_user_turn_continuity"
                                if variant["turns"]
                                else "single_variant_text"
                            ),
                            "turn_trace": turn_trace,
                        }
                    )
                    continue
                if result is None:
                    variant_decision_counts["not_applicable_pre_safety"] += 1
                    variant_observations.append(
                        {
                            **base,
                            "audit_status": "not_applicable_pre_safety",
                            "decision": None,
                            "candidate_source_ids": [],
                            "clinically_relevant_source_ids": [],
                            "clinical_relevance_review_status": "pending",
                            "retrieval_view_kinds": [],
                            "literal_candidate_count": 0,
                            "retrieval_call_count": sum(
                                bool(item["retrieval_attempted"]) for item in turn_trace
                            ),
                            "retrieval_latency_ms": sum(
                                int(item.get("retrieval_latency_ms", 0)) for item in turn_trace
                            ),
                            "input_mode": "sequential_bounded_user_turn_continuity",
                            "turn_trace": turn_trace,
                        }
                    )
                    continue
                release_ids.add(result.release.stable_id)
                variant_decision_counts[result.decision.value] += 1
                variant_observations.append(
                    {
                        **base,
                        "audit_status": (
                            "candidate_support_pending_case_review"
                            if result.candidates
                            else "no_released_evidence"
                        ),
                        "decision": result.decision.value,
                        "candidate_source_ids": list(
                            dict.fromkeys(item.source.stable_id for item in result.candidates)
                        ),
                        "candidate_jurisdictions": list(
                            dict.fromkeys(item.source.jurisdiction for item in result.candidates)
                        ),
                        "candidate_languages": list(
                            dict.fromkeys(item.passage.language for item in result.candidates)
                        ),
                        "clinically_relevant_source_ids": [],
                        "clinical_relevance_review_status": "pending",
                        "retrieval_view_kinds": list(result.view_kinds),
                        "literal_candidate_count": result.literal_candidate_count,
                        "retrieval_call_count": sum(
                            bool(item["retrieval_attempted"]) for item in turn_trace
                        ),
                        "retrieval_latency_ms": sum(
                            int(item.get("retrieval_latency_ms", 0)) for item in turn_trace
                        ),
                        "input_mode": (
                            "sequential_bounded_user_turn_continuity"
                            if variant["turns"]
                            else "single_variant_text"
                        ),
                        "turn_trace": turn_trace,
                    }
                )
        db.rollback()

    result_payload = {
        "auditor_version": "canonical-active-release-coverage-v6-gate-metrics",
        "audited_at": datetime.now(UTC).isoformat(),
        "contract_id": payload["contract_id"],
        "contract_sha256": payload["content_sha256"],
        "contract_status": payload["status"],
        "active_release_ids": sorted(release_ids),
        "provider_calls": 0,
        "paid_usage_usd": 0,
        "case_count": len(observations),
        "decision_counts": dict(sorted(decision_counts.items())),
        "variant_count": len(variant_observations),
        "variant_decision_counts": dict(sorted(variant_decision_counts.items())),
        "limitations": [
            "A retrieval hit is only a candidate and is not a claim of case-specific "
            "clinical support.",
            "Relevant source IDs stay empty until named case-by-case clinical review is recorded.",
            "This audit does not evaluate answer generation or claim-to-citation support.",
            "Generated presentation views are deterministic descriptions; their text is not "
            "stored in retrieval telemetry.",
            "All literal and generated patient candidates must centrally match the controlled "
            "presentation before evidence sufficiency is considered.",
            "Multi-turn variants run sequentially through the production-shared bounded "
            "user-turn continuity resolver. This retrieval-only audit makes no answer-model "
            "or rescue-planner call.",
            "Retrieval latency is measured inside the production retrieval function. For a "
            "multi-turn subject, the reported latency is the sum of attempted user-turn "
            "retrievals and excludes safety-assessment and evaluator overhead.",
        ],
        "observations": observations,
        "variant_observations": variant_observations,
    }
    rendered = json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
