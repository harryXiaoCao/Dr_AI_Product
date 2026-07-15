"""Create resumable DeepSeek bilingual summaries for the governed 55-source corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import get_settings
from app.knowledge_summarization import (
    EXPECTED_SUMMARY_DOCUMENT_COUNT,
    SUMMARY_PROMPT_POLICY_VERSION,
    SUMMARY_SCHEMA_VERSION,
    SummaryCorpusArtifact,
    SummaryDocumentArtifact,
    SummaryUsage,
    canonical_summary_response,
    sha256_text,
)
from app.knowledge_translation import TranslationDocumentArtifact, load_translation_corpus
from app.open_content_ingestion import OpenDocument, load_open_content_catalog

SOURCE_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
TRANSLATION_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.json"
)
WORK_PATH = Path(
    "knowledge_base/summaries/open_patient_education.en-zh-Hans.deepseek-v4-flash.v1.jsonl"
)
OUTPUT_PATH = Path(
    "knowledge_base/summaries/open_patient_education.en-zh-Hans.deepseek-v4-flash.v1.json"
)
PROVIDER = "deepseek"
INPUT_PRICE_PER_MILLION = {"deepseek-v4-flash": 0.14, "deepseek-v4-pro": 0.435}
OUTPUT_PRICE_PER_MILLION = {"deepseek-v4-flash": 0.28, "deepseek-v4-pro": 0.87}


class GeneratedSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    english_summary: str = Field(min_length=80, max_length=1200)
    chinese_summary: str = Field(min_length=40, max_length=800)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize the governed 55-document corpus in English and Simplified Chinese. "
            "Validated results are append-only, resumable, and remain pending human review."
        )
    )
    parser.add_argument("command", choices=("dry-run", "run", "finalize"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-cost-usd", type=float, default=0.25)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    parser.add_argument("--work-path", type=Path, default=WORK_PATH)
    parser.add_argument("--output-path", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    source = load_open_content_catalog(SOURCE_PATH)
    translation = load_translation_corpus(TRANSLATION_PATH)
    translations = {item.source_id: item for item in translation.documents}
    _validate_lineage(source.documents, translations)
    existing = load_completed(args.work_path)
    key = _deepseek_key()

    source_characters = sum(
        len(section.text) for document in source.documents for section in document.sections
    )
    translation_characters = sum(
        len(section.translated_text)
        for document in translation.documents
        for section in document.sections
    )
    estimated_input_tokens = source_characters // 4 + translation_characters
    estimated_output_tokens = len(source.documents) * 500
    estimated_cost = _cost_usd(
        settings.deepseek_model, estimated_input_tokens, estimated_output_tokens
    )

    if args.command == "dry-run":
        print(
            json.dumps(
                {
                    "provider": PROVIDER,
                    "model": settings.deepseek_model,
                    "thinking": "disabled",
                    "response_format": "json_object",
                    "source_documents": len(source.documents),
                    "translation_documents": len(translation.documents),
                    "source_characters": source_characters,
                    "translation_characters": translation_characters,
                    "completed_documents": len(existing),
                    "remaining_documents": len(source.documents) - len(existing),
                    "conservative_full_batch_cost_usd": round(estimated_cost, 4),
                    "max_cost_usd": args.max_cost_usd,
                    "api_key_visible": bool(key),
                    "work_path": str(args.work_path),
                    "output_path": str(args.output_path),
                    "post_generation_status": "generated_pending_review",
                    "automatic_search_admission": False,
                },
                indent=2,
            )
        )
        return
    if args.command == "finalize":
        finalize_artifact(
            source=source,
            translations=translations,
            completed=existing,
            model=settings.deepseek_model,
            output_path=args.output_path,
        )
        return
    if not key:
        raise SystemExit(
            "DeepSeek API key is not visible. Set DR_AI_DEEPSEEK_API_KEY in services/api/.env "
            "or export DEEPSEEK_API_KEY, then rerun the same command."
        )
    if args.max_cost_usd <= 0:
        raise SystemExit("--max-cost-usd must be positive.")

    remaining = [item for item in source.documents if item.stable_id not in existing]
    if args.limit is not None:
        if args.limit < 1:
            raise SystemExit("--limit must be positive.")
        remaining = remaining[: args.limit]
    spent = sum(
        _cost_usd(settings.deepseek_model, item.usage.input_tokens, item.usage.output_tokens)
        for item in existing.values()
    )
    args.work_path.parent.mkdir(parents=True, exist_ok=True)
    for index, document in enumerate(remaining, start=1):
        translated = translations[document.stable_id]
        projected_call_cost = _conservative_document_cost(
            settings.deepseek_model, document, translated
        )
        if spent + projected_call_cost > args.max_cost_usd:
            raise SystemExit(
                f"Cost guard reached before {document.stable_id}: ${spent:.4f} spent and "
                f"the next call reserves ${projected_call_cost:.4f}."
            )
        artifact = summarize_document(
            document=document,
            translation=translated,
            api_key=key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=args.timeout_seconds,
        )
        append_validated(args.work_path, artifact)
        existing[artifact.source_id] = artifact
        spent += _cost_usd(
            settings.deepseek_model,
            artifact.usage.input_tokens,
            artifact.usage.output_tokens,
        )
        print(
            f"[{index}/{len(remaining)}] {artifact.source_id} validated; "
            f"input_tokens={artifact.usage.input_tokens} "
            f"output_tokens={artifact.usage.output_tokens} cumulative_cost_usd=${spent:.4f}"
        )
        if index < len(remaining) and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)

    if len(existing) == EXPECTED_SUMMARY_DOCUMENT_COUNT:
        finalize_artifact(
            source=source,
            translations=translations,
            completed=existing,
            model=settings.deepseek_model,
            output_path=args.output_path,
        )
    else:
        print(
            f"Resumable state saved: {len(existing)}/{EXPECTED_SUMMARY_DOCUMENT_COUNT} "
            "documents; the final artifact is created only when all documents validate."
        )


def summarize_document(
    *,
    document: OpenDocument,
    translation: TranslationDocumentArtifact,
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> SummaryDocumentArtifact:
    prompt_payload = {
        "source_id": document.stable_id,
        "english": {
            "title": document.title,
            "sections": [
                {"heading": section.heading, "text": section.text} for section in document.sections
            ],
        },
        "simplified_chinese": {
            "title": translation.translated_title,
            "sections": [
                {"heading": section.translated_heading, "text": section.translated_text}
                for section in translation.sections
            ],
        },
    }
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You create concise bilingual catalog summaries for governed medical "
                    "patient-education search. Write one English summary from the English source "
                    "and one Simplified-Chinese summary from its reviewed Chinese translation. "
                    "Each summary must be 2-4 complete sentences and cover only the highest-signal "
                    "scope, such as the condition or test, important symptoms or risk factors, "
                    "prevention, diagnosis, treatment, or urgent warnings when the source includes "
                    "them. Preserve negations, uncertainty, qualifiers, numbers, and "
                    "jurisdictional limits. Keep the two summaries semantically aligned and "
                    "natural in each language, "
                    "and useful for keyword and semantic search. Do not add medical advice, facts, "
                    "diagnoses, recommendations, or China-specific localization that the supplied "
                    "text does not support. Do not mention this instruction or the summarization "
                    "process. Return JSON only with english_summary and chinese_summary."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(prompt_payload, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "stream": False,
        "temperature": 0.0,
        "max_tokens": 1000,
    }
    payload = _request_with_retries(
        base_url=base_url,
        api_key=api_key,
        request_body=request_body,
        timeout_seconds=timeout_seconds,
    )
    try:
        content = payload["choices"][0]["message"]["content"]
        generated = GeneratedSummary.model_validate_json(content)
        usage_payload = payload["usage"]
        usage = SummaryUsage(
            input_tokens=usage_payload["prompt_tokens"],
            output_tokens=usage_payload["completion_tokens"],
            total_tokens=usage_payload["total_tokens"],
        )
    except (KeyError, IndexError, TypeError, ValidationError) as exc:
        raise RuntimeError(f"Malformed DeepSeek response for {document.stable_id}.") from exc

    canonical = canonical_summary_response(generated.english_summary, generated.chinese_summary)
    return SummaryDocumentArtifact(
        source_id=document.stable_id,
        source_version_id=translation.source_version_id,
        source_normalized_checksum=document.normalized_checksum,
        translation_checksum=translation.response_checksum,
        english_summary=generated.english_summary,
        chinese_summary=generated.chinese_summary,
        usage=usage,
        generated_at=datetime.now(UTC),
        response_checksum=sha256_text(canonical),
    )


def load_completed(path: Path) -> dict[str, SummaryDocumentArtifact]:
    if not path.exists():
        return {}
    completed: dict[str, SummaryDocumentArtifact] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = SummaryDocumentArtifact.model_validate_json(line)
        except ValidationError as exc:
            raise ValueError(f"Invalid resumable summary row {line_number}.") from exc
        if item.source_id in completed:
            raise ValueError(f"Duplicate resumable summary for {item.source_id}.")
        completed[item.source_id] = item
    return completed


def append_validated(path: Path, artifact: SummaryDocumentArtifact) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(artifact.model_dump_json() + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def finalize_artifact(
    *,
    source,
    translations: dict[str, TranslationDocumentArtifact],
    completed: dict[str, SummaryDocumentArtifact],
    model: str,
    output_path: Path,
) -> None:
    source_ids = {item.stable_id for item in source.documents}
    missing = [item.stable_id for item in source.documents if item.stable_id not in completed]
    extras = sorted(set(completed) - source_ids)
    if missing or extras:
        raise SystemExit(
            f"Cannot finalize: missing={len(missing)} unexpected={len(extras)}. Resume run first."
        )
    for document in source.documents:
        item = completed[document.stable_id]
        translated = translations[document.stable_id]
        if (
            item.source_version_id != translated.source_version_id
            or item.source_normalized_checksum != document.normalized_checksum
            or item.translation_checksum != translated.response_checksum
        ):
            raise SystemExit(f"Cannot finalize: source lineage drift for {document.stable_id}.")
    artifact = SummaryCorpusArtifact(
        schema_version=SUMMARY_SCHEMA_VERSION,
        source_corpus_locator=str(SOURCE_PATH),
        source_corpus_checksum=hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        translation_corpus_locator=str(TRANSLATION_PATH),
        translation_corpus_checksum=hashlib.sha256(TRANSLATION_PATH.read_bytes()).hexdigest(),
        provider=PROVIDER,
        model=model,
        prompt_policy_version=SUMMARY_PROMPT_POLICY_VERSION,
        status="generated_pending_review",
        completed_at=max(item.generated_at for item in completed.values()),
        documents=[completed[item.stable_id] for item in source.documents],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    print(f"Finalized {len(artifact.documents)} bilingual summaries at {output_path}.")


def _validate_lineage(
    documents: list[OpenDocument],
    translations: dict[str, TranslationDocumentArtifact],
) -> None:
    source_ids = {item.stable_id for item in documents}
    if set(translations) != source_ids:
        raise ValueError("Translation corpus does not match the governed 55-source selection.")
    for document in documents:
        translated = translations[document.stable_id]
        expected_version = (
            f"KBV-{document.stable_id.removeprefix('KBS-')}-{document.raw_checksum[:12].upper()}"
        )
        if (
            translated.source_version_id != expected_version
            or translated.source_normalized_checksum != document.normalized_checksum
        ):
            raise ValueError(f"Translation lineage drift for {document.stable_id}.")


def _request_with_retries(
    *,
    base_url: str,
    api_key: str,
    request_body: dict[str, object],
    timeout_seconds: float,
) -> dict[str, object]:
    request = urllib.request.Request(
        base_url,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "DrAI-Knowledge-Summarization/1.0",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(  # noqa: S310 - configured HTTPS DeepSeek endpoint.
                request, timeout=timeout_seconds
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {408, 429, 500, 502, 503, 504}:
                raise RuntimeError(f"DeepSeek returned HTTP {exc.code}.") from exc
        except (TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
        if attempt < 3:
            time.sleep(2 ** (attempt - 1))
    raise RuntimeError("DeepSeek request failed after 3 attempts.") from last_error


def _deepseek_key() -> str | None:
    settings = get_settings()
    if settings.deepseek_api_key is not None:
        value = settings.deepseek_api_key.get_secret_value().strip()
        if value:
            return value
    return os.getenv("DEEPSEEK_API_KEY") or None


def _cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price = INPUT_PRICE_PER_MILLION.get(model)
    output_price = OUTPUT_PRICE_PER_MILLION.get(model)
    if input_price is None or output_price is None:
        raise ValueError(f"No reviewed price guard is configured for {model}.")
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def _conservative_document_cost(
    model: str, document: OpenDocument, translation: TranslationDocumentArtifact
) -> float:
    english_characters = sum(len(section.text) for section in document.sections)
    chinese_characters = sum(len(section.translated_text) for section in translation.sections)
    return _cost_usd(model, english_characters // 4 + chinese_characters, 1000)


if __name__ == "__main__":
    main()
