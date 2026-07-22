"""Validate the supplementary symptom-presentation corpus review gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.knowledge_review import (
    load_supplementary_review_manifest,
    validate_supplementary_review_manifest,
)
from app.knowledge_translation import load_translation_corpus
from app.open_content_ingestion import load_open_content_catalog

DEFAULT_MANIFEST = Path("knowledge_base/reviews/open_symptom_presentations.v1.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="Return success for valid pending material; default requires admission readiness.",
    )
    args = parser.parse_args()

    manifest = load_supplementary_review_manifest(args.manifest)
    catalog_path = Path(manifest.source_catalog.locator)
    translation_path = Path(manifest.translation_artifact.locator)
    result = validate_supplementary_review_manifest(
        manifest,
        catalog=load_open_content_catalog(catalog_path),
        catalog_path=catalog_path,
        translation=load_translation_corpus(translation_path),
        translation_path=translation_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.structure_only:
        return 0 if result["structurally_valid"] else 1
    return 0 if result["admission_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
