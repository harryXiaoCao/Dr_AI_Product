"""Import a validated, metadata-only knowledge catalog into PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.database import SessionLocal
from app.knowledge_ingestion import import_catalog_metadata, load_catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("knowledge_base/catalog/authoritative_resources.v1.json"),
    )
    args = parser.parse_args()
    catalog = load_catalog(args.catalog)
    with SessionLocal.begin() as db:
        publishers, rights, sources = import_catalog_metadata(db, catalog)
    print(
        f"Imported publishers={publishers} rights_records={rights} sources={sources}; "
        f"validated_sources={len(catalog.sources)}"
    )


if __name__ == "__main__":
    main()
