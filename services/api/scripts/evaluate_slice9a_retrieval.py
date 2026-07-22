from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.chatbot_contracts import PatientEvidenceRequest
from app.database import engine
from app.knowledge_ingestion import activate_index_release
from app.knowledge_retrieval import retrieve
from app.knowledge_retrieval_evaluation import (
    RetrievalEvaluationCase,
    RetrievalObservation,
    evaluate_retrieval_results,
    retrieval_gate_failures,
)
from app.models import KbActiveIndexRelease, KbIndexRelease


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen Slice 9A retrieval-only gate.")
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path("knowledge_base/evaluation/retrieval_cases.slice9a.v2.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--candidate-release-id",
        type=uuid.UUID,
        help="Evaluate a built release transactionally without activating it permanently.",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"Output already exists; refusing to overwrite {args.output}.")
    suite = json.loads(args.suite.read_text())
    if suite["review"]["status"] != "approved":
        raise SystemExit("The frozen retrieval suite lacks clinician approval; evaluation refused.")
    cases = [
        RetrievalEvaluationCase(
            case_id=item["case_id"],
            relevant_source_grades=item["relevant_source_grades"],
            expected_decision=item["expected_decision"],
            forbidden_source_ids=frozenset(item["forbidden_source_ids"]),
            minimum_distinct_sources=item["minimum_distinct_sources"],
            preferred_jurisdiction=item["preferred_jurisdiction"],
            allowed_languages=frozenset(item["allowed_languages"]),
        )
        for item in suite["cases"]
    ]
    observations: list[RetrievalObservation] = []
    release_lineage: dict[str, object] = {}
    with Session(engine) as db:
        original_active = db.get(KbActiveIndexRelease, "patient")
        if original_active is None and args.candidate_release_id is None:
            raise SystemExit("No active patient release exists; evaluation refused.")
        original_release_id = original_active.release_id if original_active else None
        if args.candidate_release_id:
            candidate = db.get(KbIndexRelease, args.candidate_release_id)
            if candidate is None or candidate.status != "built":
                raise SystemExit("Candidate release does not exist or is not in built status.")
            activate_index_release(
                db,
                candidate,
                audience="patient",
                activated_by="slice9a-transactional-evaluator",
            )
        evaluated = db.get(
            KbIndexRelease,
            args.candidate_release_id or original_release_id,
        )
        assert evaluated is not None
        release_lineage = {
            "release_id": str(evaluated.id),
            "stable_id": evaluated.stable_id,
            "embedding_model": evaluated.embedding_model_version,
            "reranker_model": evaluated.reranker_version,
            "permanently_activated": args.candidate_release_id is None,
            "original_active_release_id": (
                str(original_release_id) if original_release_id is not None else None
            ),
        }
        for case, raw_case in zip(cases, suite["cases"], strict=True):
            started = time.perf_counter()
            result = retrieve(
                db,
                PatientEvidenceRequest(query=raw_case["query"], language="zh-Hans"),
                audience="patient",
            )
            observations.append(
                RetrievalObservation(
                    case_id=case.case_id,
                    source_ids=tuple(item.source.stable_id for item in result.candidates),
                    decision=result.decision.value,
                    source_jurisdictions=tuple(
                        item.source.jurisdiction for item in result.candidates
                    ),
                    source_applicable_jurisdictions=tuple(
                        item.applicable_jurisdictions for item in result.candidates
                    ),
                    passage_languages=tuple(
                        item.passage.language for item in result.candidates
                    ),
                    latency_ms=round((time.perf_counter() - started) * 1000),
                )
            )
        db.rollback()
    thresholds = suite["thresholds"]
    metrics = evaluate_retrieval_results(cases, observations, k=thresholds["k"])
    failures = retrieval_gate_failures(metrics, **thresholds)
    artifact = {
        "evaluator_version": "slice9a-source-deduplicated-v2",
        "suite_id": suite["suite_id"],
        "evaluated_at": datetime.now(UTC).isoformat(),
        "review": suite["review"],
        "release": release_lineage,
        "metrics": metrics,
        "failures": failures,
        "passed": not failures,
        "observations": [item.__dict__ for item in observations],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, default=list) + "\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
