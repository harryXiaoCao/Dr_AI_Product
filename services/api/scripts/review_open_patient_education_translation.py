"""Record one required human review for a generated Chinese translation."""

import argparse

from app.database import SessionLocal
from app.knowledge_translation import record_translation_review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_id")
    parser.add_argument("--review-type", choices=("medical", "native_chinese"), required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--decision", choices=("approved", "rejected"), required=True)
    parser.add_argument("--findings")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with SessionLocal.begin() as db:
        artifact = record_translation_review(
            db,
            artifact_stable_id=args.artifact_id,
            review_type=args.review_type,
            reviewer_id=args.reviewer_id,
            approved=args.decision == "approved",
            findings=args.findings,
        )
        print(
            f"artifact={artifact.stable_id} status={artifact.status} "
            f"medical_review={artifact.medical_review_status} "
            f"native_chinese_review={artifact.native_language_review_status}"
        )


if __name__ == "__main__":
    main()
