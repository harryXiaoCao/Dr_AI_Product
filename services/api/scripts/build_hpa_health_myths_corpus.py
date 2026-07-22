"""Build the licensed HPA Health Myths corpus with deterministic zh-Hans adaptations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from opencc import OpenCC

from app.hpa_health_myths_ingestion import (
    CONVERSION_POLICY_VERSION,
    EXPECTED_ROW_COUNT,
    EXPECTED_SOURCE_COUNT,
    HpaHealthMythsCorpus,
    sha256_text,
)

DATASET_LOCATOR = "https://data.gov.tw/dataset/43338"
RIGHTS_LOCATOR = "https://data.gov.tw/license"
CAPTURED_AT = datetime(2026, 7, 17, tzinfo=UTC)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def clean_text(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    for anchor in soup.find_all("a"):
        href = str(anchor.get("href") or "").strip().replace('""', '"')
        label = anchor.get_text(" ", strip=True)
        if href and href not in label:
            anchor.replace_with(f"{label} ({href})" if label else href)
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def normalized_question(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def source_id(question: str) -> str:
    digest = sha256_text(question)[:20].upper()
    return f"KBS-HPA-{digest}"


def version_id(source_stable_id: str, row_ordinal: int, original_checksum: str) -> str:
    source_suffix = source_stable_id.removeprefix("KBS-HPA-")
    return f"KBV-HPA-{source_suffix}-{row_ordinal:03d}-{original_checksum[:10].upper()}"


def parse_date(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d-%b-%y").replace(tzinfo=UTC)


def to_simplified(converter: OpenCC, value: str) -> str:
    """Reach OpenCC's fixed point for adjacent phrase conversions such as `優於`."""

    converted = value
    for _ in range(4):
        next_value = converter.convert(converted)
        if next_value == converted:
            return converted
        converted = next_value
    raise ValueError("OpenCC conversion did not stabilize within four passes.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", type=Path, required=True)
    parser.add_argument("--dataset-html", type=Path, required=True)
    parser.add_argument("--rights-html", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knowledge_base/catalog/hpa_health_myths.zh-Hans.v1.json"),
    )
    parser.add_argument(
        "--raw-copy-output",
        type=Path,
        default=Path("knowledge_base/raw/hpa_health_myths.zh-Hant.dataset-43338.2026-07-02.csv"),
    )
    args = parser.parse_args()

    source_bytes = args.source_csv.read_bytes()
    rows = list(
        csv.DictReader(
            source_bytes.decode("utf-8-sig").splitlines(),
        )
    )
    if len(rows) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Expected {EXPECTED_ROW_COUNT} rows, found {len(rows)}.")
    if set(rows[0]) != {"題目", "答案", "建立時間"}:
        raise ValueError("Unexpected HPA CSV schema.")

    converter = OpenCC("t2s")
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row_ordinal, row in enumerate(rows, start=1):
        question = clean_text(row["題目"])
        answer = clean_text(row["答案"])
        if not question or not answer or not row["建立時間"].strip():
            raise ValueError(f"Incomplete HPA row {row_ordinal}.")
        publisher_date_text = row["建立時間"].strip()
        original = f"{row_ordinal}\n{publisher_date_text}\n{question}\n{answer}"
        simplified_question = to_simplified(converter, question)
        simplified_answer = to_simplified(converter, answer)
        simplified = f"{simplified_question}\n{simplified_answer}"
        if converter.convert(simplified) != simplified:
            raise ValueError(f"Simplified conversion is not idempotent for row {row_ordinal}.")
        grouped[normalized_question(question)].append(
            {
                "row_ordinal": row_ordinal,
                "publisher_date_text": publisher_date_text,
                "publication_date": parse_date(row["建立時間"]),
                "original_question": question,
                "original_answer": answer,
                "original_checksum": sha256_text(original),
                "simplified_question": simplified_question,
                "simplified_answer": simplified_answer,
                "simplified_checksum": sha256_text(simplified),
            }
        )

    if len(grouped) != EXPECTED_SOURCE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_COUNT} unique questions, found {len(grouped)}."
        )

    sources: list[dict[str, object]] = []
    for question, versions in grouped.items():
        stable_id = source_id(question)
        versions.sort(key=lambda item: (item["publication_date"], item["row_ordinal"]))
        previous_id: str | None = None
        built_versions: list[dict[str, object]] = []
        for item in versions:
            stable_version_id = version_id(
                stable_id,
                int(item["row_ordinal"]),
                str(item["original_checksum"]),
            )
            built_versions.append(
                dict(item, stable_id=stable_version_id, supersedes_version_id=previous_id)
            )
            previous_id = stable_version_id
        sources.append(
            {
                "stable_id": stable_id,
                "canonical_locator": f"{DATASET_LOCATOR}#qa-{quote(stable_id.lower())}",
                "current_version_id": built_versions[-1]["stable_id"],
                "versions": built_versions,
            }
        )
    sources.sort(key=lambda item: str(item["stable_id"]))

    payload = {
        "schema_version": "1.0",
        "generated_at": CAPTURED_AT,
        "dataset_title": "保健辟谣",
        "dataset_locator": DATASET_LOCATOR,
        "publisher_name_zh_hant": "衛生福利部國民健康署",
        "publisher_name_zh_hans": "卫生福利部国民健康署",
        "jurisdiction": "TW",
        "source_language": "zh-Hant",
        "stored_adaptation_language": "zh-Hans",
        "source_csv_checksum": sha256_bytes(source_bytes),
        "source_row_count": len(rows),
        "unique_source_count": len(grouped),
        "duplicate_question_group_count": sum(len(items) > 1 for items in grouped.values()),
        "dataset_evidence": {
            "locator": DATASET_LOCATOR,
            "checksum": sha256_bytes(args.dataset_html.read_bytes()),
            "captured_at": CAPTURED_AT,
        },
        "rights_evidence": {
            "locator": RIGHTS_LOCATOR,
            "checksum": sha256_bytes(args.rights_html.read_bytes()),
            "captured_at": CAPTURED_AT,
        },
        "license_name": "政府资料开放授权条款-第1版 (OGDL-Taiwan-1.0)",
        "attribution": ("卫生福利部国民健康署 [2026] 保健辟谣；依政府资料开放授权条款-第1版使用。"),
        "conversion_provider": "opencc",
        "conversion_model": "opencc-python-reimplemented-0.1.7:t2s",
        "conversion_policy_version": CONVERSION_POLICY_VERSION,
        "sources": sources,
    }
    validated = HpaHealthMythsCorpus.model_validate(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(validated.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.raw_copy_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source_csv, args.raw_copy_output)
    print(
        f"Wrote sources={len(validated.sources)} versions={validated.source_row_count} "
        f"duplicate_groups={validated.duplicate_question_group_count} to {args.output}"
    )


if __name__ == "__main__":
    main()
