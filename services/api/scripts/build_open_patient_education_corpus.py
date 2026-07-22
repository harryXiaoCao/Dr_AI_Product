"""Build the reviewed U.S. public-domain patient-education corpus.

Only publisher text is retained. Images, navigation, linked third-party
material, and generated summaries/translations are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from bs4 import BeautifulSoup, Tag

CAPTURED_AT = "2026-07-15T00:00:00Z"
MEDLINE_XML_URL = "https://medlineplus.gov/xml/mplus_topics_compressed_2026-07-14.zip"

HEALTH_TOPICS = [
    "High Blood Pressure",
    "Diabetes Type 2",
    "Asthma",
    "COPD",
    "Heart Diseases",
    "Stroke",
    "Cholesterol Levels: What You Need to Know",
    "Obesity",
    "Healthy Aging",
    "Depression",
    "Anxiety",
    "Sleep Disorders",
    "Flu",
    "Pneumonia",
    "Tuberculosis",
    "Hepatitis B",
    "HIV",
    "Breast Cancer",
    "Lung Cancer",
    "Colorectal Cancer",
    "Pregnancy",
    "Prenatal Care",
    "Children's Health",
    "Nutrition",
    "Exercise and Physical Fitness",
]

HTML_SOURCES = [
    # MedlinePlus medical tests (10)
    (
        "medlineplus_test",
        "blood-glucose-test",
        "https://medlineplus.gov/lab-tests/blood-glucose-test/",
    ),
    (
        "medlineplus_test",
        "cholesterol-levels",
        "https://medlineplus.gov/lab-tests/cholesterol-levels/",
    ),
    (
        "medlineplus_test",
        "complete-blood-count-cbc",
        "https://medlineplus.gov/lab-tests/complete-blood-count-cbc/",
    ),
    (
        "medlineplus_test",
        "comprehensive-metabolic-panel-cmp",
        "https://medlineplus.gov/lab-tests/comprehensive-metabolic-panel-cmp/",
    ),
    (
        "medlineplus_test",
        "hemoglobin-a1c-hba1c-test",
        "https://medlineplus.gov/lab-tests/hemoglobin-a1c-hba1c-test/",
    ),
    (
        "medlineplus_test",
        "liver-function-tests",
        "https://medlineplus.gov/lab-tests/liver-function-tests/",
    ),
    (
        "medlineplus_test",
        "measuring-blood-pressure",
        "https://medlineplus.gov/lab-tests/measuring-blood-pressure/",
    ),
    (
        "medlineplus_test",
        "tsh-thyroid-stimulating-hormone-test",
        "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/",
    ),
    (
        "medlineplus_test",
        "blood-in-urine",
        "https://medlineplus.gov/lab-tests/blood-in-urine/",
    ),
    ("medlineplus_test", "creatinine-test", "https://medlineplus.gov/lab-tests/creatinine-test/"),
    # NCI patient education (10)
    ("nci", "what-is-cancer", "https://www.cancer.gov/about-cancer/understanding/what-is-cancer"),
    ("nci", "cancer-diagnosis", "https://www.cancer.gov/about-cancer/diagnosis-staging/diagnosis"),
    ("nci", "cancer-staging", "https://www.cancer.gov/about-cancer/diagnosis-staging/staging"),
    ("nci", "treatment-types", "https://www.cancer.gov/about-cancer/treatment/types"),
    ("nci", "treatment-side-effects", "https://www.cancer.gov/about-cancer/treatment/side-effects"),
    ("nci", "coping-with-cancer", "https://www.cancer.gov/about-cancer/coping"),
    ("nci", "feelings-and-cancer", "https://www.cancer.gov/about-cancer/coping/feelings"),
    ("nci", "questions-for-doctor", "https://www.cancer.gov/about-cancer/coping/questions"),
    (
        "nci",
        "cancer-prevention-overview",
        "https://www.cancer.gov/about-cancer/causes-prevention/patient-prevention-overview-pdq",
    ),
    ("nci", "cancer-prognosis", "https://www.cancer.gov/about-cancer/diagnosis-staging/prognosis"),
    # NIMH fact sheets (5)
    ("nimh", "depression", "https://www.nimh.nih.gov/health/publications/depression"),
    (
        "nimh",
        "generalized-anxiety-disorder",
        "https://www.nimh.nih.gov/health/publications/generalized-anxiety-disorder-gad",
    ),
    (
        "nimh",
        "post-traumatic-stress-disorder",
        "https://www.nimh.nih.gov/health/publications/post-traumatic-stress-disorder-ptsd",
    ),
    ("nimh", "schizophrenia", "https://www.nimh.nih.gov/health/publications/schizophrenia"),
    (
        "nimh",
        "understanding-psychosis",
        "https://www.nimh.nih.gov/health/publications/understanding-psychosis",
    ),
    # MyHealthfinder preventive-health pages (5)
    (
        "myhealthfinder",
        "get-screened",
        "https://odphp.health.gov/myhealthfinder/doctor-visits/screening-tests/get-screened",
    ),
    (
        "myhealthfinder",
        "blood-pressure",
        "https://odphp.health.gov/myhealthfinder/doctor-visits/screening-tests/get-your-blood-pressure-checked",
    ),
    (
        "myhealthfinder",
        "enough-sleep",
        "https://odphp.health.gov/myhealthfinder/healthy-living/mental-health-and-relationships/get-enough-sleep",
    ),
    (
        "myhealthfinder",
        "heart-healthy",
        "https://odphp.health.gov/myhealthfinder/health-conditions/heart-health/keep-your-heart-healthy",
    ),
    (
        "myhealthfinder",
        "prevent-type-2-diabetes",
        "https://odphp.health.gov/myhealthfinder/health-conditions/diabetes/take-steps-prevent-type-2-diabetes",
    ),
]

PUBLISHERS = {
    "medlineplus": {
        "stable_id": "KBP-MEDLINEPLUS",
        "name": "MedlinePlus, U.S. National Library of Medicine",
        "authority_url": "https://medlineplus.gov/about/general/aboutmedlineplus/",
        "rights_url": "https://medlineplus.gov/about/using/usingcontent/",
        "rights_name": "U.S. Government public domain (specified MedlinePlus content classes)",
        "attribution": (
            "Credit MedlinePlus, U.S. National Library of Medicine, and link to the original page."
        ),
    },
    "nci": {
        "stable_id": "KBP-NCI",
        "name": "National Cancer Institute",
        "authority_url": "https://www.cancer.gov/about-nci",
        "rights_url": "https://www.cancer.gov/policies/copyright-reuse",
        "rights_name": "U.S. Government public domain text unless otherwise indicated",
        "attribution": (
            "Credit the National Cancer Institute and link to the original page; do not "
            "imply NCI endorsement."
        ),
    },
    "nimh": {
        "stable_id": "KBP-NIMH",
        "name": "National Institute of Mental Health",
        "authority_url": "https://www.nimh.nih.gov/about",
        "rights_url": "https://www.nimh.nih.gov/site-info/policies",
        "rights_name": "U.S. Government public domain text",
        "attribution": (
            "Credit the National Institute of Mental Health and link to the original fact "
            "sheet; do not imply NIMH endorsement."
        ),
    },
    "myhealthfinder": {
        "stable_id": "KBP-ODPHP",
        "name": "Office of Disease Prevention and Health Promotion",
        "authority_url": "https://odphp.health.gov/about-odphp",
        "rights_url": "https://odphp.health.gov/copyright-policy",
        "rights_name": "U.S. Government public domain text",
        "attribution": (
            "Credit ODPHP/MyHealthfinder and link to the original page; exclude third-party "
            "images and materials."
        ),
    },
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "DrAI-Knowledge-Catalog/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def stable_slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:72]


def parse_date(text: str) -> str | None:
    match = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})",
        text,
    )
    if match:
        return datetime.strptime(match.group(0), "%B %d, %Y").date().isoformat()
    slash_date = re.search(r"\b\d{2}/\d{2}/\d{4}\b", text)
    if slash_date:
        return datetime.strptime(slash_date.group(0), "%m/%d/%Y").date().isoformat()
    return None


def html_sections(container: Tag) -> list[dict[str, object]]:
    for unwanted in container.select(
        "script, style, svg, picture, figure, img, video, audio, nav, form, button, "
        ".usa-skipnav, .cgdp-image, .caption, .credit"
    ):
        unwanted.decompose()
    sections: list[dict[str, object]] = []
    heading = "Introduction"
    blocks: list[str] = []

    def flush() -> None:
        nonlocal blocks
        text = "\n\n".join(blocks).strip()
        if text:
            sections.append({"heading": heading, "text": text})
        blocks = []

    for element in container.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        if element.find_parent(["p", "li", "table"]) is not None:
            continue
        text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue
        if element.name.startswith("h"):
            flush()
            heading = text
        elif element.name == "li":
            blocks.append(f"• {text}")
        else:
            blocks.append(text)
    flush()
    return sections


def parse_html(kind: str, slug: str, url: str, raw: bytes) -> dict[str, object]:
    soup = BeautifulSoup(raw, "html.parser")
    title_node = soup.select_one("h1")
    title = (
        clean_text(title_node.get_text(" ", strip=True))
        if title_node
        else clean_text(soup.title.get_text())
    )
    description = soup.select_one('meta[name="description"]')
    publisher_summary = clean_text(description.get("content", "")) if description else ""
    selectors = {
        "medlineplus_test": "article, #mplus-content, main",
        "nci": ".cgdp-article-body, article, main",
        "nimh": "#main_content_inner, article, main",
        "myhealthfinder": "#main-content article, main article, main",
    }
    container = soup.select_one(selectors[kind])
    if container is None:
        raise ValueError(f"No article container found for {url}")
    date_selectors = {
        "medlineplus_test": "#lastupdate",
        "nci": ".cgdp-document-dates",
        "nimh": ".publication-meta, .field--name-field-publication-date, article",
        "myhealthfinder": ".topic-last-updated",
    }
    date_node = soup.select_one(date_selectors[kind])
    date_text = (
        clean_text(date_node.get_text(" ", strip=True)) if date_node else "Date not stated on page"
    )
    if kind == "nimh":
        matches = re.findall(
            r"(?:Revised|Updated|Published)\s+(?:[A-Z][a-z]+\s+\d{1,2},\s+)?\d{4}", date_text
        )
        date_text = matches[-1] if matches else "Date not stated on page"
    publisher_key = "medlineplus" if kind == "medlineplus_test" else kind
    source_type = {
        "medlineplus_test": "medical_test_explanation",
        "nci": "patient_education",
        "nimh": "fact_sheet",
        "myhealthfinder": "preventive_health",
    }[kind]
    sections = html_sections(container)
    normalized = "\n\n".join(f"# {item['heading']}\n{item['text']}" for item in sections)
    if len(normalized) < 500:
        raise ValueError(f"Extracted article is unexpectedly short: {url}")
    return {
        "stable_id": f"KBS-{publisher_key.upper()}-{stable_slug(slug).upper()}",
        "publisher_key": publisher_key,
        "collection": kind,
        "title": title,
        "canonical_locator": url,
        "source_type": source_type,
        "topic": title,
        "original_language": "en",
        "publisher_summary": publisher_summary or None,
        "publisher_date_text": date_text,
        "publication_date": parse_date(date_text),
        "captured_at": CAPTURED_AT,
        "raw_checksum": sha(raw),
        "normalized_checksum": sha(normalized),
        "sections": sections,
    }


def parse_health_topics(
    raw_zip: bytes,
    *,
    titles: list[str] | None = None,
) -> list[dict[str, object]]:
    with zipfile.ZipFile(BytesIO(raw_zip)) as archive:
        xml_name = next(name for name in archive.namelist() if name.endswith(".xml"))
        root = ElementTree.fromstring(archive.read(xml_name))
    by_title = {topic.attrib["title"]: topic for topic in root.findall("health-topic")}
    selected_titles = titles or HEALTH_TOPICS
    missing = sorted(set(selected_titles) - set(by_title))
    if missing:
        raise ValueError(f"Missing MedlinePlus health topics: {missing}")
    documents = []
    for title in selected_titles:
        topic = by_title[title]
        summary_html = topic.findtext("full-summary") or ""
        summary = clean_text(BeautifulSoup(summary_html, "html.parser").get_text(" ", strip=True))
        meta_description = clean_text(topic.findtext("meta-desc") or "")
        created = topic.attrib.get("date-created", "")
        normalized = f"# {title}\n{summary}"
        documents.append(
            {
                "stable_id": f"KBS-MEDLINEPLUS-{stable_slug(title).upper()}",
                "publisher_key": "medlineplus",
                "collection": "medlineplus_health_topic",
                "title": title,
                "canonical_locator": topic.attrib["url"],
                "source_type": "health_topic_summary",
                "topic": title,
                "original_language": "en",
                "publisher_summary": meta_description or None,
                "publisher_date_text": f"Date created: {created}",
                "publication_date": parse_date(created),
                "captured_at": CAPTURED_AT,
                "raw_checksum": sha(summary_html),
                "normalized_checksum": sha(normalized),
                "sections": [{"heading": title, "text": summary}],
            }
        )
    return documents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("knowledge_base/catalog/open_patient_education.v1.json")
    )
    args = parser.parse_args()
    raw_xml = fetch(MEDLINE_XML_URL)
    documents = parse_health_topics(raw_xml)
    for index, (kind, slug, url) in enumerate(HTML_SOURCES, 1):
        print(f"[{index}/{len(HTML_SOURCES)}] {url}")
        documents.append(parse_html(kind, slug, url, fetch(url)))
    counts = {
        key: sum(document["collection"] == key for document in documents)
        for key in ("medlineplus_health_topic", "medlineplus_test", "nci", "nimh", "myhealthfinder")
    }
    if counts != {
        "medlineplus_health_topic": 25,
        "medlineplus_test": 10,
        "nci": 10,
        "nimh": 5,
        "myhealthfinder": 5,
    }:
        raise ValueError(f"Unexpected collection counts: {counts}")
    rights_evidence = {}
    for key, publisher in PUBLISHERS.items():
        rights_html = fetch(publisher["rights_url"])
        rights_evidence[key] = {"checksum": sha(rights_html), "captured_at": CAPTURED_AT}
    payload = {
        "schema_version": "1.0",
        "generated_at": CAPTURED_AT,
        "capture_policy": (
            "Original publisher text only; no generated summary or translation; images and "
            "third-party linked material excluded."
        ),
        "jurisdiction_note": (
            "Foreign-jurisdiction evidence. Applicable Chinese authority controls "
            "China-facing answers in any conflict."
        ),
        "publishers": [
            dict(value, key=key, rights_evidence=rights_evidence[key])
            for key, value in PUBLISHERS.items()
        ],
        "documents": documents,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(documents)} original-language documents to {args.output}")


if __name__ == "__main__":
    main()
