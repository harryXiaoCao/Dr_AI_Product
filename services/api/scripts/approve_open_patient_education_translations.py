"""Promote the fully reviewed 55-document Chinese translation corpus."""

import argparse
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.database import SessionLocal
from app.knowledge_translation import (
    EXPECTED_OPEN_DOCUMENT_COUNT,
    TRANSLATION_PROMPT_POLICY_VERSION,
    record_translation_review,
)
from app.models import KbSource, KbTranslationArtifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record both required approvals for the complete open-patient-education "
            "Simplified-Chinese translation corpus."
        )
    )
    parser.add_argument("--medical-reviewer-id", required=True)
    parser.add_argument("--native-chinese-reviewer-id", required=True)
    parser.add_argument("--findings")
    parser.add_argument("--confirm-all-55-reviewed", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_all_55_reviewed:
        raise SystemExit(
            "Refusing promotion without --confirm-all-55-reviewed. "
            "Generation completion alone is not review approval."
        )

    with SessionLocal.begin() as db:
        source_count_before = db.scalar(select(func.count()).select_from(KbSource)) or 0
        artifacts = db.scalars(
            select(KbTranslationArtifact)
            .where(
                KbTranslationArtifact.provider == "deepseek",
                KbTranslationArtifact.model == "deepseek-v4-flash",
                KbTranslationArtifact.prompt_policy_version == TRANSLATION_PROMPT_POLICY_VERSION,
                KbTranslationArtifact.target_language == "zh-Hans",
            )
            .order_by(KbTranslationArtifact.stable_id)
        ).all()
        if len(artifacts) != EXPECTED_OPEN_DOCUMENT_COUNT:
            raise SystemExit(
                f"Expected {EXPECTED_OPEN_DOCUMENT_COUNT} translation artifacts; "
                f"found {len(artifacts)}. Nothing was promoted."
            )

        reviewed_at = datetime.now(UTC)
        medical_approvals = 0
        native_chinese_approvals = 0
        for artifact in artifacts:
            if artifact.medical_review_status != "approved":
                record_translation_review(
                    db,
                    artifact_stable_id=artifact.stable_id,
                    review_type="medical",
                    reviewer_id=args.medical_reviewer_id,
                    approved=True,
                    findings=args.findings,
                    reviewed_at=reviewed_at,
                )
                medical_approvals += 1
            if artifact.native_language_review_status != "approved":
                record_translation_review(
                    db,
                    artifact_stable_id=artifact.stable_id,
                    review_type="native_chinese",
                    reviewer_id=args.native_chinese_reviewer_id,
                    approved=True,
                    findings=args.findings,
                    reviewed_at=reviewed_at,
                )
                native_chinese_approvals += 1
            if artifact.status != "approved":
                raise RuntimeError(f"Dual approval did not promote {artifact.stable_id}.")

        source_count_after = db.scalar(select(func.count()).select_from(KbSource)) or 0
        if source_count_after != source_count_before:
            raise RuntimeError("Translation review changed the knowledge-source count.")

        print(
            f"approved_artifacts={len(artifacts)} "
            f"medical_reviews_created={medical_approvals} "
            f"native_chinese_reviews_created={native_chinese_approvals} "
            f"source_count_change={source_count_after - source_count_before}"
        )


if __name__ == "__main__":
    main()
