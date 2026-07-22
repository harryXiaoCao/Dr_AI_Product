"""Build a small rights-inherited corpus for unsupported symptom presentations.

The selection contains only MedlinePlus health-topic summaries, a content
class the publisher explicitly identifies as public domain. It inherits the
checked-in publisher and rights evidence from the governed v1 open-content
catalog; linked articles, images, and Medical Encyclopedia content are never
captured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.build_open_patient_education_corpus import (
    MEDLINE_XML_URL,
    clean_text,
    fetch,
    parse_health_topics,
    sha,
)

CAPTURED_AT = "2026-07-21T00:00:00Z"
BASE_CATALOG_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
OUTPUT_PATH = Path("knowledge_base/catalog/open_symptom_presentations.v1.json")
HEALTH_TOPICS = [
    "Low Blood Pressure",
    "Dizziness and Vertigo",
    "Arrhythmia",
    "Pesticides",
    "Skin Conditions",
]
NHS_BABY_MOVEMENTS_URL = "https://www.nhs.uk/pregnancy/keeping-well/your-babys-movements/"
NHS_TERMS_URL = "https://www.nhs.uk/our-policies/terms-and-conditions/"
NHS_EXCLUSIONS_URL = (
    "https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/"
)


def _nhs_review_date(raw: bytes, label: str) -> str | None:
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    match = re.search(rf"{re.escape(label)}:\s*(\d{{1,2}}\s+[A-Z][a-z]+\s+20\d{{2}})", text)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%d %B %Y").date().isoformat()


def _parse_nhs_baby_movements(raw: bytes) -> dict[str, object]:
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.select_one("article")
    title_node = soup.select_one("h1")
    if article is None or title_node is None:
        raise ValueError("NHS baby-movements page structure changed.")

    sections: list[dict[str, str]] = []
    for section in article.select("section"):
        heading_node = section.select_one("h2, h3")
        if heading_node is None:
            continue
        heading = clean_text(heading_node.get_text(" ", strip=True))
        if heading.casefold() == "find out more":
            continue
        blocks: list[str] = []
        for element in section.find_all(["p", "li"]):
            if element.find_parent(["p", "li"]) is not None:
                continue
            text = clean_text(element.get_text(" ", strip=True))
            if text:
                blocks.append(f"• {text}" if element.name == "li" else text)
        if blocks:
            sections.append({"heading": heading, "text": "\n\n".join(blocks)})

    normalized = "\n\n".join(f"# {section['heading']}\n{section['text']}" for section in sections)
    required_phrases = (
        "moving less than usual",
        "Do not wait until the next day",
        "Do not use a home doppler",
    )
    if len(normalized) < 500 or any(phrase not in normalized for phrase in required_phrases):
        raise ValueError("NHS baby-movements extraction is incomplete or has drifted.")

    description = soup.select_one('meta[name="description"]')
    last_reviewed = _nhs_review_date(raw, "Page last reviewed")
    next_review = _nhs_review_date(raw, "Next review due")
    return {
        "stable_id": "KBS-NHS-BABY-MOVEMENTS",
        "publisher_key": "nhs",
        "collection": "nhs_patient_education",
        "title": clean_text(title_node.get_text(" ", strip=True)),
        "canonical_locator": NHS_BABY_MOVEMENTS_URL,
        "source_type": "patient_education",
        "topic": "Reduced fetal movement",
        "original_language": "en",
        "publisher_summary": (clean_text(description.get("content", "")) if description else None),
        "publisher_date_text": (
            f"Page last reviewed: {last_reviewed or 'not stated'}; "
            f"next review due: {next_review or 'not stated'}"
        ),
        "publication_date": None,
        "review_due_date": next_review,
        "jurisdiction": "GB-ENG",
        "population": "pregnant_people",
        "captured_at": CAPTURED_AT,
        "raw_checksum": sha(raw),
        "normalized_checksum": sha(normalized),
        "sections": sections,
    }


def _nhs_publisher(terms: bytes, exclusions: bytes) -> dict[str, object]:
    terms_text = clean_text(BeautifulSoup(terms, "html.parser").get_text(" ", strip=True))
    exclusions_text = clean_text(BeautifulSoup(exclusions, "html.parser").get_text(" ", strip=True))
    required_terms = (
        "Open Government Licence",
        "including commercially",
        "Translation into another language",
        "must not attribute the content to the NHS website",
    )
    if any(value not in terms_text for value in required_terms):
        raise ValueError("NHS licence terms changed or could not be verified.")
    excluded_paths = (
        "/change4life",
        "/best-start-in-life",
        "/be-clear-on-cancer",
        "/oneyou",
        "/smokefree",
        "/quit",
    )
    if any(path in NHS_BABY_MOVEMENTS_URL for path in excluded_paths):
        raise ValueError("Selected NHS source is in an excluded website path.")
    if "Most of the content on the NHS website can be re-used" not in exclusions_text:
        raise ValueError("NHS exclusion evidence changed or could not be verified.")
    evidence_checksum = hashlib.sha256(terms + b"\n--NHS-EXCLUSIONS--\n" + exclusions).hexdigest()
    return {
        "key": "nhs",
        "stable_id": "KBP-NHS-UK",
        "name": "NHS website (England)",
        "authority_url": "https://www.nhs.uk/our-policies/content-policy/",
        "rights_url": NHS_TERMS_URL,
        "rights_name": "Open Government Licence v3.0 with NHS website terms",
        "attribution": (
            "For adapted, translated, or non-refreshed content use: Contains public sector "
            "information licensed under the Open Government Licence v3.0. Do not attribute "
            "the adapted text to the NHS website, imply NHS endorsement, or carry forward "
            "formal clinical approval. Preserve internal provenance to the original page."
        ),
        "rights_evidence": {
            "checksum": evidence_checksum,
            "captured_at": CAPTURED_AT,
            "supporting_locators": [NHS_TERMS_URL, NHS_EXCLUSIONS_URL],
            "evidence_scope": (
                "NHS terms sections 3.3-3.7 plus the content-exclusions page; text only. "
                "Logos, images, videos, linked third-party works, personal data, and medical "
                "devices are excluded."
            ),
        },
        "rights_stable_id": "KBR-NHS-UK-OGL-V3",
        "jurisdiction": "GB-ENG",
        "organization_type": "foreign_national_health_service",
        "authority_basis": (
            "Official NHS website patient education for England; foreign-jurisdiction "
            "evidence pending Mainland-China clinical applicability review."
        ),
        "allowed_content_classes": ["official_patient_education_text"],
        "rights_scope": "publisher_content_class",
        "permission_reference": (
            "Applies only to NHS-authored text on non-excluded nhs.uk pages under OGL v3.0 "
            "and NHS website terms. Translation is an adaptation, loses any transferable "
            "formal clinical-approval claim, requires OGL attribution, and must not imply "
            "NHS endorsement."
        ),
        "rights_decision_status": "approved",
        "rights_permissions": {
            "commercial_use_allowed": True,
            "storage_allowed": True,
            "transformation_allowed": True,
            "translation_allowed": True,
            "embedding_allowed": True,
            "excerpt_display_allowed": True,
            "model_provider_transmission_allowed": True,
            "redistribution_allowed": True,
            "prior_version_retention_allowed": True,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-catalog", type=Path, default=BASE_CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = json.loads(args.base_catalog.read_text(encoding="utf-8"))
    medlineplus = next(
        publisher for publisher in base["publishers"] if publisher["key"] == "medlineplus"
    )
    documents = parse_health_topics(fetch(MEDLINE_XML_URL), titles=HEALTH_TOPICS)
    nhs_page = fetch(NHS_BABY_MOVEMENTS_URL)
    nhs_terms = fetch(NHS_TERMS_URL)
    nhs_exclusions = fetch(NHS_EXCLUSIONS_URL)
    documents.append(_parse_nhs_baby_movements(nhs_page))
    for document in documents:
        document["captured_at"] = CAPTURED_AT

    expected_ids = {
        "KBS-MEDLINEPLUS-LOW-BLOOD-PRESSURE",
        "KBS-MEDLINEPLUS-DIZZINESS-AND-VERTIGO",
        "KBS-MEDLINEPLUS-ARRHYTHMIA",
        "KBS-MEDLINEPLUS-PESTICIDES",
        "KBS-MEDLINEPLUS-SKIN-CONDITIONS",
        "KBS-NHS-BABY-MOVEMENTS",
    }
    observed_ids = {document["stable_id"] for document in documents}
    if observed_ids != expected_ids:
        raise ValueError(
            "Supplementary MedlinePlus selection drifted: "
            f"missing={sorted(expected_ids - observed_ids)} "
            f"unexpected={sorted(observed_ids - expected_ids)}"
        )

    payload = {
        "schema_version": "1.1",
        "generated_at": CAPTURED_AT,
        "capture_policy": (
            "Publisher-authored MedlinePlus health-topic summaries and one NHS patient-"
            "education page only; no linked works, images, video, logos, Medical "
            "Encyclopedia content, generated summary, or translation."
        ),
        "jurisdiction_note": (
            "Foreign-jurisdiction evidence pending medical, native-Simplified-Chinese, "
            "patient-readability, and Mainland-China applicability review. Applicable "
            "Chinese authority controls China-facing answers in any conflict."
        ),
        "expected_collection_counts": {
            "medlineplus_health_topic": len(HEALTH_TOPICS),
            "nhs_patient_education": 1,
        },
        "publishers": [medlineplus, _nhs_publisher(nhs_terms, nhs_exclusions)],
        "documents": documents,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(documents)} governed source candidates to {args.output}.")


if __name__ == "__main__":
    main()
