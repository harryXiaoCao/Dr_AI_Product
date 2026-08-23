"""Capture the licensed official-language WHO Fact Sheets text corpus.

Only the fact-sheet article body is normalized. Images, logos, page chrome,
credits, and third-party visual material are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from bs4 import BeautifulSoup, NavigableString, Tag

USER_AGENT = "DrAI-WHO-Permission-202609681/1.0"


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def clean_text(value: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", value).strip()


def fetch(url: str, cache_dir: Path) -> bytes:
    target = cache_dir / f"{sha(url)}.html"
    if target.exists():
        return target.read_bytes()
    parts = urlsplit(url)
    request_url = urlunsplit(
        (parts.scheme, parts.netloc, quote(parts.path, safe="/%()'"), parts.query, parts.fragment)
    )
    request = urllib.request.Request(request_url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            if len(raw) < 10_000:
                raise ValueError(f"WHO response is unexpectedly short for {url}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            return raw
        except Exception as error:  # noqa: BLE001 - retry preserves the final cause
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to capture {url}: {last_error}") from last_error


def parse_date(value: str) -> str | None:
    for pattern in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date().isoformat()
        except ValueError:
            pass
    return None


def structured_sections(article: Tag) -> list[dict[str, str]]:
    for unwanted in article.select(
        "script, style, svg, picture, figure, img, video, audio, form, button, "
        ".credit, .credits, .image-credit, .sf-image-credit, [class*='image-credit']"
    ):
        unwanted.decompose()
    sections: list[dict[str, str]] = []
    heading = "Fact sheet"
    blocks: list[str] = []

    def flush() -> None:
        nonlocal blocks
        text = "\n\n".join(blocks).strip()
        if text:
            sections.append({"heading": heading, "text": text})
        blocks = []

    block_names = {"h2", "h3", "h4", "h5", "p", "li", "table"}

    def is_leaf_text_div(element: Tag) -> bool:
        return (
            element.name == "div"
            and element.find(["div", "h2", "h3", "h4", "h5", "p", "li", "ul", "ol", "table"])
            is None
        )

    descendants = list(article.descendants)
    document_order = {id(node): ordinal for ordinal, node in enumerate(descendants)}
    candidates: list[Tag | NavigableString] = []
    for node in descendants:
        if isinstance(node, Tag):
            if node.name in block_names:
                if (
                    node.name in {"p", "li", "table"}
                    and node.find_parent(["p", "li", "table"]) is not None
                ):
                    continue
                candidates.append(node)
            elif is_leaf_text_div(node):
                candidates.append(node)
            continue
        if not isinstance(node, NavigableString) or not clean_text(str(node)):
            continue
        if node.find_parent(list(block_names)) is not None:
            continue
        parent_div = node.find_parent("div")
        if parent_div is not None and is_leaf_text_div(parent_div):
            continue
        candidates.append(node)

    candidates.sort(key=lambda item: document_order[id(item)])
    for element in candidates:
        if isinstance(element, NavigableString):
            element_name = "text"
            text = clean_text(str(element))
        else:
            element_name = element.name
            text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue
        if element_name in {"h2", "h3", "h4", "h5"}:
            if blocks:
                flush()
                heading = text
            elif heading == "Fact sheet":
                heading = text
            else:
                heading = f"{heading} / {text}"
        elif element_name == "li":
            blocks.append(f"• {text}")
        else:
            blocks.append(text)
    if not blocks and heading != "Fact sheet":
        blocks.append(heading)
    flush()
    return sections


def parse_page(url: str, language: str, raw: bytes) -> dict[str, object]:
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.select_one("article.sf-detail-body-wrapper")
    if article is None:
        raise ValueError(f"No WHO fact-sheet article body found: {url}")
    title_node = soup.select_one("h1")
    if title_node is None:
        raise ValueError(f"No WHO fact-sheet title found: {url}")
    title = clean_text(title_node.get_text(" ", strip=True))
    date_node = soup.select_one(".sf-detail-header .timestamp, article ~ * .timestamp")
    if date_node is None:
        date_node = soup.select_one(".timestamp")
    date_text = clean_text(date_node.get_text(" ", strip=True)) if date_node else "Date not stated"
    sections = structured_sections(article)
    normalized = "\n\n".join(f"# {item['heading']}\n{item['text']}" for item in sections)
    if len(normalized) < 300:
        raise ValueError(f"WHO fact-sheet extraction is unexpectedly short: {url}")
    return {
        "language": language,
        "title": title,
        "canonical_locator": url,
        "publisher_date_text": date_text,
        "publication_date": parse_date(date_text),
        "raw_checksum": sha(raw),
        "normalized_checksum": sha(normalized),
        "sections": sections,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--english-index", type=Path, required=True)
    parser.add_argument("--chinese-index", type=Path, required=True)
    parser.add_argument("--authorization-evidence", type=Path, required=True)
    parser.add_argument("--approved-form-evidence", type=Path, required=True)
    parser.add_argument("--agreement-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    who_sources = [
        source for source in catalog["sources"] if source["publisher_stable_id"] == "KBP-WHO"
    ]
    jobs: list[tuple[str, str, str]] = []
    for source in who_sources:
        jobs.append((source["stable_id"], source["original_language"], source["canonical_locator"]))
        jobs.extend(
            (source["stable_id"], translation["language"], translation["official_locator"])
            for translation in source["official_translations"]
        )
    if len({job[2] for job in jobs}) != len(jobs):
        raise ValueError("Authoritative catalog repeats a WHO official locator.")

    documents: dict[str, list[dict[str, object]]] = {
        source["stable_id"]: [] for source in who_sources
    }
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_jobs = {
            executor.submit(fetch, url, args.cache_dir): (source_id, language, url)
            for source_id, language, url in jobs
        }
        completed = 0
        for future in as_completed(future_jobs):
            source_id, language, url = future_jobs[future]
            documents[source_id].append(parse_page(url, language, future.result()))
            completed += 1
            if completed % 25 == 0 or completed == len(jobs):
                print(f"Captured {completed}/{len(jobs)} official WHO pages", flush=True)

    timestamp = datetime.fromisoformat(args.generated_at.replace("Z", "+00:00"))
    timestamp = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
    counts = {"en": 0, "zh-Hans": 0}
    sources = []
    for source in who_sources:
        source_documents = sorted(documents[source["stable_id"]], key=lambda item: item["language"])
        for document in source_documents:
            counts[document["language"]] += 1
        sources.append({"source_stable_id": source["stable_id"], "documents": source_documents})
    payload = {
        "schema_version": "1.0",
        "generated_at": timestamp,
        "permission": {
            "request_id": "202609681",
            "authorization_checksum": sha(args.authorization_evidence.read_bytes()),
            "approved_form_checksum": sha(args.approved_form_evidence.read_bytes()),
            "agreement_checksum": sha(args.agreement_evidence.read_bytes()),
            "recorded_at": timestamp,
        },
        "english_index_checksum": sha(args.english_index.read_bytes()),
        "chinese_index_checksum": sha(args.chinese_index.read_bytes()),
        "expected_language_document_counts": counts,
        "excluded_content": ["images", "logos", "third_party_credited_material"],
        "sources": sources,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(sources)} WHO sources and {sum(counts.values())} language documents")


if __name__ == "__main__":
    main()
