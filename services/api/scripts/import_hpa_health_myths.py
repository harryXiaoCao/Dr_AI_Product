"""Import the licensed HPA Health Myths corpus and review-pending zh-Hans adaptations."""

from pathlib import Path

from app.database import SessionLocal
from app.hpa_health_myths_ingestion import (
    import_hpa_health_myths_corpus,
    load_hpa_health_myths_corpus,
)

CORPUS_PATH = Path("knowledge_base/catalog/hpa_health_myths.zh-Hans.v1.json")


def main() -> None:
    corpus = load_hpa_health_myths_corpus(CORPUS_PATH)
    with SessionLocal.begin() as db:
        result = import_hpa_health_myths_corpus(
            db,
            corpus,
            artifact_locator=str(CORPUS_PATH),
        )
    print(
        "Imported "
        f"publishers={result[0]} rights_records={result[1]} sources={result[2]} "
        f"versions={result[3]} passages={result[4]} zh_hans_artifacts={result[5]}; "
        f"validated_rows={corpus.source_row_count}"
    )


if __name__ == "__main__":
    main()
