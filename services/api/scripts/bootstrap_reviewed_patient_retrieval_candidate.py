"""Promote the two frozen reviewed corpora and build one non-active candidate."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.database import SessionLocal
from app.patient_knowledge_release import (
    active_patient_release_version_ids,
    build_patient_candidate_release,
    promote_reviewed_hpa_for_patient_use,
    promote_reviewed_translations_for_patient_use,
)

OPEN_FINDINGS = (
    "Product-owner confirmation recorded that all 55 translated documents were manually "
    "reviewed and approved for patient use on 2026-07-16. Individual reviewer names were "
    "not supplied; that provenance limitation is preserved."
)
HPA_FINDINGS = (
    "Product-owner confirmation recorded that all 697 HPA Simplified-Chinese Q&A records "
    "completed medical, native-language, patient-readability, and Mainland-applicability "
    "human review on 2026-07-17. Individual reviewer names were not supplied; Taiwan-specific "
    "programs, contacts, schedules, approvals, and legal requirements retain their jurisdiction."
)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-id", default="product-owner-confirmed-unspecified")
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("knowledge_base/release_artifacts"),
    )
    parser.add_argument("--confirm-all-55-reviewed", action="store_true")
    parser.add_argument("--confirm-all-697-reviewed", action="store_true")
    parser.add_argument("--embedding-batch-size", type=int, default=8)
    parser.add_argument("--embedding-batch-character-budget", type=int, default=6000)
    parser.add_argument("--embedding-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--embedding-max-attempts", type=int, default=3)
    args = parser.parse_args()
    if not args.confirm_all_55_reviewed or not args.confirm_all_697_reviewed:
        raise SystemExit("Both frozen-corpus review confirmations are required.")

    with SessionLocal.begin() as db:
        existing = active_patient_release_version_ids(db)
        open_promotion = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id=args.reviewer_id,
            findings=OPEN_FINDINGS,
            reviewed_at=datetime(2026, 7, 16, tzinfo=UTC),
        )
        hpa_promotion = promote_reviewed_hpa_for_patient_use(
            db,
            reviewer_id=args.reviewer_id,
            findings=HPA_FINDINGS,
            reviewed_at=datetime(2026, 7, 17, tzinfo=UTC),
        )
        version_ids = list(
            dict.fromkeys(
                [*existing, *open_promotion.version_ids, *hpa_promotion.version_ids]
            )
        )
        release = build_patient_candidate_release(
            db,
            version_ids=version_ids,
            artifact_root=args.artifact_root,
            approver_id=args.reviewer_id,
            embedding_batch_size=args.embedding_batch_size,
            embedding_batch_character_budget=args.embedding_batch_character_budget,
            embedding_timeout_seconds=args.embedding_timeout_seconds,
            embedding_max_attempts=args.embedding_max_attempts,
        )
        print(
            json.dumps(
                {
                    "release_id": str(release.id),
                    "stable_id": release.stable_id,
                    "status": release.status,
                    "source_count": release.source_count,
                    "version_count": release.version_count,
                    "passage_count": release.passage_count,
                    "embedding_model": release.embedding_model_version,
                    "reranker_model": release.reranker_version,
                    "active": False,
                    "open_versions_created": open_promotion.versions_created,
                    "hpa_versions_created": hpa_promotion.versions_created,
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
