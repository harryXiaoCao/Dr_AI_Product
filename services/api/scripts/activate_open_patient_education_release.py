"""Promote the reviewed corpus and activate its immutable patient release."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from app.database import SessionLocal
from app.patient_knowledge_release import (
    build_and_activate_patient_release,
    promote_reviewed_translations_for_patient_use,
)

DEFAULT_FINDINGS = (
    "The product owner confirmed on 2026-07-16 that all 55 entries and documents "
    "were manually reviewed and approved for patient use. Individual reviewer names "
    "were not supplied; this provenance limitation is preserved explicitly."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--findings", default=DEFAULT_FINDINGS)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("knowledge_base/release_artifacts"),
    )
    parser.add_argument("--confirm-all-55-patient-approved", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_all_55_patient_approved:
        raise SystemExit(
            "Refusing activation without --confirm-all-55-patient-approved."
        )
    with SessionLocal.begin() as db:
        promotion = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id=args.reviewer_id,
            findings=args.findings,
            reviewed_at=datetime.now(UTC),
        )
        release = build_and_activate_patient_release(
            db,
            version_ids=promotion.version_ids,
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
