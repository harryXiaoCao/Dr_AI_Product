"""Import a complete reviewed-shape translation artifact as pending human review."""

import argparse
from pathlib import Path

from app.database import SessionLocal
from app.knowledge_translation import import_translation_corpus, load_translation_corpus

TRANSLATION_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TRANSLATION_PATH)
    return parser.parse_args()


def main() -> None:
    path = parse_args().path
    corpus = load_translation_corpus(path)
    with SessionLocal.begin() as db:
        result = import_translation_corpus(
            db,
            corpus,
            artifact_locator=str(path),
        )
    print(
        f"Imported translation_artifacts={result[0]} translation_sections={result[1]}; "
        f"source_count_change=0 status=generated_pending_review documents={len(corpus.documents)}"
    )


if __name__ == "__main__":
    main()
