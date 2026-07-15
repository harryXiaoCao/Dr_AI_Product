"""Import the checked-in public-domain original-language corpus."""

from pathlib import Path

from app.database import SessionLocal
from app.open_content_ingestion import import_open_content_catalog, load_open_content_catalog


def main() -> None:
    path = Path("knowledge_base/catalog/open_patient_education.v1.json")
    catalog = load_open_content_catalog(path)
    with SessionLocal.begin() as db:
        result = import_open_content_catalog(db, catalog)
    print(
        "Imported "
        f"publishers={result[0]} rights_records={result[1]} sources={result[2]} "
        f"passages={result[3]}; validated_documents={len(catalog.documents)}"
    )


if __name__ == "__main__":
    main()
