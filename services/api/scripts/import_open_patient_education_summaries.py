"""Import the product-owner-confirmed, manually reviewed 55-summary artifact."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from app.database import SessionLocal
from app.knowledge_summarization import import_reviewed_summary_corpus, load_summary_corpus

SUMMARY_PATH = Path(
    "knowledge_base/summaries/open_patient_education.en-zh-Hans.deepseek-v4-flash.v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--reviewed-at", default=None)
    parser.add_argument("--findings", default=None)
    parser.add_argument("--confirm-all-55-reviewed", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_all_55_reviewed:
        raise SystemExit("Refusing import without --confirm-all-55-reviewed.")
    reviewed_at = (
        datetime.fromisoformat(args.reviewed_at) if args.reviewed_at else datetime.now(UTC)
    )
    if reviewed_at.tzinfo is None:
        reviewed_at = reviewed_at.replace(tzinfo=UTC)
    corpus = load_summary_corpus(SUMMARY_PATH)
    with SessionLocal.begin() as db:
        created = import_reviewed_summary_corpus(
            db,
            corpus,
            artifact_locator=str(SUMMARY_PATH),
            reviewer_id=args.reviewer_id,
            reviewed_at=reviewed_at,
            review_findings=args.findings,
        )
    print(
        f"summary_artifacts_created={created} documents={len(corpus.documents)} "
        "status=approved source_count_change=0"
    )


if __name__ == "__main__":
    main()
