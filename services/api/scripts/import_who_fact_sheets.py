"""Import the licensed official-language WHO Fact Sheets corpus."""

import argparse
from pathlib import Path

from app.database import SessionLocal
from app.who_fact_sheets_ingestion import (
    import_who_fact_sheet_corpus,
    load_who_fact_sheet_corpus,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("knowledge_base/catalog/who_fact_sheets.official.v1.json"),
    )
    args = parser.parse_args()
    corpus = load_who_fact_sheet_corpus(args.path)
    with SessionLocal.begin() as db:
        rights, versions, passages = import_who_fact_sheet_corpus(
            db, corpus, artifact_locator=str(args.path)
        )
    print(
        f"Imported rights_records={rights} versions={versions} passages={passages}; "
        f"validated_sources={len(corpus.sources)}"
    )


if __name__ == "__main__":
    main()
