"""Install reviewed, source-provenanced terminology before building a new release."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_retrieval import normalize_medical_text
from app.models import KbPassage, KbReview, KbSource, KbSourceVersion, KbTerm


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--terms",
        type=Path,
        default=Path("knowledge_base/terminology/terms.slice9a.v1.json"),
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path("knowledge_base/evaluation/retrieval_cases.slice9a.v2.json"),
    )
    args = parser.parse_args()
    terms_document = json.loads(args.terms.read_text())
    suite = json.loads(args.suite.read_text())
    if suite["suite_id"] != terms_document["review_basis_suite_id"]:
        raise SystemExit("Terminology review basis does not match the frozen suite.")
    review = suite["review"]
    if review["status"] != "approved":
        raise SystemExit("Reviewed terminology cannot be installed from an unapproved suite.")

    created = unchanged = 0
    with Session(engine) as db:
        for item in terms_document["terms"]:
            sources = list(
                db.scalars(
                    select(KbSource).where(
                        KbSource.stable_id.in_(item["provenance_source_ids"])
                    )
                )
            )
            if len(sources) != len(item["provenance_source_ids"]):
                raise SystemExit(f"Terminology provenance is missing for {item['stable_id']}.")
            source_text = " ".join(
                [
                    *(
                        value
                        for source in sources
                        for value in (
                            source.title,
                            source.catalog_summary,
                            *source.search_keywords_json,
                        )
                    ),
                    *db.scalars(
                        select(KbPassage.text)
                        .join(KbSourceVersion, KbSourceVersion.id == KbPassage.version_id)
                        .where(
                            KbSourceVersion.source_id.in_([source.id for source in sources]),
                            KbSourceVersion.review_decision == "approved",
                            KbPassage.language == "zh-Hans",
                        )
                    ),
                ]
            )
            normalized_source_text = normalize_medical_text(source_text)
            supported_aliases = [
                item["preferred_zh"],
                item["preferred_en"],
                *item["aliases"],
            ]
            missing_aliases = [
                alias
                for alias in supported_aliases
                if normalize_medical_text(alias) not in normalized_source_text
            ]
            if missing_aliases:
                raise SystemExit(
                    "A terminology alias lacks reviewed source text: "
                    f"{item['stable_id']} {missing_aliases}."
                )

            expected = {
                "preferred_zh": item["preferred_zh"],
                "preferred_en": item["preferred_en"],
                "aliases_json": item["aliases"],
                "concept_type": item["concept_type"],
                "disambiguation_notes": item["disambiguation_notes"],
                "provenance_source_ids_json": item["provenance_source_ids"],
                "prohibited_expansions_json": item["prohibited_expansions"],
                "review_status": "approved",
            }
            term = db.scalar(select(KbTerm).where(KbTerm.stable_id == item["stable_id"]))
            if term is None:
                term = KbTerm(stable_id=item["stable_id"], **expected)
                db.add(term)
                created += 1
            elif any(getattr(term, key) != value for key, value in expected.items()):
                raise SystemExit(f"Existing terminology drifted: {item['stable_id']}.")
            else:
                unchanged += 1

            review_id = "KBRV-TERM-" + hashlib.sha256(
                f"{item['stable_id']}:{suite['suite_id']}".encode()
            ).hexdigest()[:24].upper()
            if db.scalar(select(KbReview).where(KbReview.stable_id == review_id)) is None:
                db.add(
                    KbReview(
                        stable_id=review_id,
                        target_type="term",
                        target_stable_id=item["stable_id"],
                        review_type="medical_terminology",
                        reviewer_role=review["reviewer_role"],
                        reviewer_id=review["reviewer_id"],
                        decision="approved",
                        decision_code="slice9a_source_alias_and_relevance_label_approved",
                        findings=(
                            "Aliases are present verbatim in already reviewed source text; the "
                            "frozen suite's approved relevance labels supply the cross-source "
                            "HbA1c-to-type-2-diabetes retrieval relationship."
                        ),
                        reviewed_at=datetime.fromisoformat(review["reviewed_at"]).replace(
                            tzinfo=UTC
                        ),
                    )
                )
        db.commit()
    print(json.dumps({"created": created, "unchanged": unchanged}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
