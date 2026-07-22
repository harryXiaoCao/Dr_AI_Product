"""Promote all reviewed HPA Q&A records into the combined patient release."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from app.database import SessionLocal
from app.patient_knowledge_release import (
    active_patient_release_version_ids,
    build_and_activate_patient_release,
    promote_reviewed_hpa_for_patient_use,
)

DEFAULT_FINDINGS = (
    "The product owner confirmed on 2026-07-17 that all 697 HPA Health Myths "
    "question-answer records were human-reviewed and approved for patient use, "
    "including medical accuracy, native Simplified-Chinese readability, and "
    "Mainland-China applicability review. Individual reviewer identities were not "
    "supplied; this provenance limitation is preserved explicitly. Taiwan-specific "
    "program eligibility, schedules, contacts, and legal requirements must still be "
    "identified as Taiwan-specific when present."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reviewer-id",
        default="product-owner-confirmed-unspecified",
    )
    parser.add_argument("--findings", default=DEFAULT_FINDINGS)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("knowledge_base/release_artifacts"),
    )
    parser.add_argument("--confirm-all-697-human-reviewed", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_all_697_human_reviewed:
        raise SystemExit("Refusing activation without --confirm-all-697-human-reviewed.")
    with SessionLocal.begin() as db:
        existing_version_ids = active_patient_release_version_ids(db)
        promotion = promote_reviewed_hpa_for_patient_use(
            db,
            reviewer_id=args.reviewer_id,
            findings=args.findings,
            reviewed_at=datetime.now(UTC),
        )
        combined_version_ids = list(dict.fromkeys([*existing_version_ids, *promotion.version_ids]))
        release = build_and_activate_patient_release(
            db,
            version_ids=combined_version_ids,
            artifact_root=args.artifact_root,
            approver_id=args.reviewer_id,
        )
        print(
            f"release={release.stable_id} status={release.status} "
            f"sources={release.source_count} versions={release.version_count} "
            f"passages={release.passage_count} versions_created={promotion.versions_created} "
            f"sections_created={promotion.sections_created} "
            f"passages_created={promotion.passages_created} "
            f"reviews_created={promotion.reviews_created}"
        )


if __name__ == "__main__":
    main()
