"""Import a checked-in public-domain original-language corpus."""

import argparse
from pathlib import Path

from app.database import SessionLocal
from app.open_content_ingestion import import_open_content_catalog, load_open_content_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("knowledge_base/catalog/open_patient_education.v1.json"),
    )
    return parser.parse_args()


def main() -> None:
    path = parse_args().path
    catalog = load_open_content_catalog(path)
    with SessionLocal.begin() as db:
        result = import_open_content_catalog(db, catalog, artifact_locator=str(path))
    print(
        "Imported "
        f"publishers={result[0]} rights_records={result[1]} sources={result[2]} "
        f"passages={result[3]}; validated_documents={len(catalog.documents)}"
    )


if __name__ == "__main__":
    main()
