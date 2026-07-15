"""Create resumable DeepSeek Simplified-Chinese translations for the 55-source corpus."""

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

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.config import get_settings
from app.knowledge_translation import (
    EXPECTED_OPEN_DOCUMENT_COUNT,
    TRANSLATION_PROMPT_POLICY_VERSION,
    TRANSLATION_SCHEMA_VERSION,
    TranslationCorpusArtifact,
    TranslationDocumentArtifact,
    TranslationSectionArtifact,
    TranslationUsage,
    sha256_text,
)
from app.open_content_ingestion import OpenDocument, load_open_content_catalog

SOURCE_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
WORK_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.jsonl"
)
OUTPUT_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.json"
)
PROVIDER = "deepseek"
INPUT_PRICE_PER_MILLION = {
    "deepseek-v4-flash": 0.14,
    "deepseek-v4-pro": 0.435,
}
OUTPUT_PRICE_PER_MILLION = {
    "deepseek-v4-flash": 0.28,
    "deepseek-v4-pro": 0.87,
}


class GeneratedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordinal: int = Field(ge=0)
    translated_heading: str
    translated_text: str = Field(min_length=1)


class GeneratedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    translated_title: str = Field(min_length=1, max_length=500)
    sections: list[GeneratedSection] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_section_order(self) -> GeneratedDocument:
        if [section.ordinal for section in self.sections] != list(range(len(self.sections))):
            raise ValueError("DeepSeek response did not preserve contiguous section order.")
        return self


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Translate the governed 55-document English corpus into Simplified Chinese. "
            "Validated results are append-only and resumable."
        )
    )
    parser.add_argument("command", choices=("dry-run", "run", "finalize"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-cost-usd", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    parser.add_argument("--work-path", type=Path, default=WORK_PATH)
    parser.add_argument("--output-path", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    source_bytes = SOURCE_PATH.read_bytes()
    source = load_open_content_catalog(SOURCE_PATH)
    existing = load_completed(args.work_path)
    key = _deepseek_key()
    total_characters = sum(
        len(section.text) for document in source.documents for section in document.sections
    )
    estimated_input_tokens = total_characters // 4
    estimated_output_tokens = total_characters
    estimated_cost = _cost_usd(
        settings.deepseek_model,
        estimated_input_tokens,
        estimated_output_tokens,
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
                    "source_sections": sum(len(item.sections) for item in source.documents),
                    "source_characters": total_characters,
                    "completed_documents": len(existing),
                    "remaining_documents": len(source.documents) - len(existing),
                    "estimated_full_batch_cost_usd": round(estimated_cost, 4),
                    "max_cost_usd": args.max_cost_usd,
                    "api_key_visible": bool(key),
                    "work_path": str(args.work_path),
                    "output_path": str(args.output_path),
                    "source_count_change": 0,
                    "post_import_status": "generated_pending_review",
                },
                indent=2,
            )
        )
        return
    if args.command == "finalize":
        finalize_artifact(
            source=source,
            source_checksum=hashlib.sha256(source_bytes).hexdigest(),
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
        _cost_usd(
            settings.deepseek_model,
            item.usage.input_tokens,
            item.usage.output_tokens,
        )
        for item in existing.values()
    )
    args.work_path.parent.mkdir(parents=True, exist_ok=True)
    for index, document in enumerate(remaining, start=1):
        if spent >= args.max_cost_usd:
            raise SystemExit(f"Cost guard reached before {document.stable_id}: ${spent:.4f} spent.")
        artifact = translate_document(
            document=document,
            api_key=key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=args.timeout_seconds,
        )
        call_cost = _cost_usd(
            settings.deepseek_model,
            artifact.usage.input_tokens,
            artifact.usage.output_tokens,
        )
        if spent + call_cost > args.max_cost_usd:
            raise SystemExit(
                f"Validated {document.stable_id}, but its ${call_cost:.4f} cost would exceed "
                "the batch guard. Increase --max-cost-usd to retain it."
            )
        append_validated(args.work_path, artifact)
        existing[artifact.source_id] = artifact
        spent += call_cost
        print(
            f"[{index}/{len(remaining)}] {artifact.source_id} validated; "
            f"input_tokens={artifact.usage.input_tokens} "
            f"output_tokens={artifact.usage.output_tokens} cumulative_cost_usd=${spent:.4f}"
        )
        if index < len(remaining) and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)

    if len(existing) == EXPECTED_OPEN_DOCUMENT_COUNT:
        finalize_artifact(
            source=source,
            source_checksum=hashlib.sha256(source_bytes).hexdigest(),
            completed=existing,
            model=settings.deepseek_model,
            output_path=args.output_path,
        )
    else:
        print(
            f"Resumable state saved: {len(existing)}/{EXPECTED_OPEN_DOCUMENT_COUNT} documents; "
            "the final import artifact is created only when all documents validate."
        )


def translate_document(
    *,
    document: OpenDocument,
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> TranslationDocumentArtifact:
    source_sections = [
        {
            "ordinal": ordinal,
            "heading": section.heading,
            "text": section.text,
        }
        for ordinal, section in enumerate(document.sections)
    ]
    prompt_payload = {
        "source_id": document.stable_id,
        "title": document.title,
        "sections": source_sections,
    }
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional medical translator. Translate publisher-authored "
                    "English patient-education text into faithful, natural Simplified Chinese. "
                    "Preserve every warning, negation, qualifier, number, unit, medication name, "
                    "heading, and section boundary. Do not summarize, add advice, localize U.S. "
                    "medical policy to China, or claim the translation is official. Keep necessary "
                    "standard English abbreviations in parentheses when clinically useful. Return "
                    "JSON only with translated_title and sections; each section must contain the "
                    "same ordinal plus translated_heading and translated_text."
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
        "max_tokens": 32768,
    }
    payload = _request_with_retries(
        base_url=base_url,
        api_key=api_key,
        request_body=request_body,
        timeout_seconds=timeout_seconds,
    )
    try:
        content = payload["choices"][0]["message"]["content"]
        generated = GeneratedDocument.model_validate_json(content)
        usage_payload = payload["usage"]
        usage = TranslationUsage(
            input_tokens=usage_payload["prompt_tokens"],
            output_tokens=usage_payload["completion_tokens"],
            total_tokens=usage_payload["total_tokens"],
        )
    except (KeyError, IndexError, TypeError, ValidationError) as exc:
        raise RuntimeError(f"Malformed DeepSeek response for {document.stable_id}.") from exc
    if len(generated.sections) != len(document.sections):
        raise RuntimeError(f"DeepSeek changed the section count for {document.stable_id}.")

    enriched_sections: list[TranslationSectionArtifact] = []
    for generated_section, source_section in zip(
        generated.sections, document.sections, strict=True
    ):
        ordinal = generated_section.ordinal
        source_section_id = f"KBC-{document.stable_id.removeprefix('KBS-')}-{ordinal:03d}"
        translated_payload = (
            f"{generated_section.translated_heading}\n{generated_section.translated_text}"
        )
        enriched_sections.append(
            TranslationSectionArtifact(
                ordinal=ordinal,
                source_section_stable_id=source_section_id,
                source_text_checksum=sha256_text(source_section.text),
                translated_heading=generated_section.translated_heading,
                translated_text=generated_section.translated_text,
                translation_checksum=sha256_text(translated_payload),
            )
        )
    canonical = _canonical_response(generated.translated_title, enriched_sections)
    return TranslationDocumentArtifact(
        source_id=document.stable_id,
        source_version_id=(
            f"KBV-{document.stable_id.removeprefix('KBS-')}-{document.raw_checksum[:12].upper()}"
        ),
        source_normalized_checksum=document.normalized_checksum,
        translated_title=generated.translated_title,
        sections=enriched_sections,
        usage=usage,
        generated_at=datetime.now(UTC),
        response_checksum=sha256_text(canonical),
    )


def load_completed(path: Path) -> dict[str, TranslationDocumentArtifact]:
    if not path.exists():
        return {}
    completed: dict[str, TranslationDocumentArtifact] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = TranslationDocumentArtifact.model_validate_json(line)
        except ValidationError as exc:
            raise ValueError(f"Invalid resumable translation row {line_number}.") from exc
        if item.source_id in completed:
            raise ValueError(f"Duplicate resumable translation for {item.source_id}.")
        completed[item.source_id] = item
    return completed


def append_validated(path: Path, artifact: TranslationDocumentArtifact) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(artifact.model_dump_json() + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def finalize_artifact(
    *,
    source,
    source_checksum: str,
    completed: dict[str, TranslationDocumentArtifact],
    model: str,
    output_path: Path,
) -> None:
    missing = [item.stable_id for item in source.documents if item.stable_id not in completed]
    extras = sorted(set(completed) - {item.stable_id for item in source.documents})
    if missing or extras:
        raise SystemExit(
            f"Cannot finalize: missing={len(missing)} unexpected={len(extras)}. Resume run first."
        )
    artifact = TranslationCorpusArtifact(
        schema_version=TRANSLATION_SCHEMA_VERSION,
        source_corpus_locator=str(SOURCE_PATH),
        source_corpus_checksum=source_checksum,
        target_language="zh-Hans",
        provider=PROVIDER,
        model=model,
        prompt_policy_version=TRANSLATION_PROMPT_POLICY_VERSION,
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
    print(f"Finalized {len(artifact.documents)} translations at {output_path}.")


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
            "User-Agent": "DrAI-Knowledge-Translation/1.0",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(  # noqa: S310 - configured HTTPS DeepSeek endpoint.
                request,
                timeout=timeout_seconds,
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


def _canonical_response(
    title: str,
    sections: list[TranslationSectionArtifact],
) -> str:
    return json.dumps(
        {
            "translated_title": title,
            "sections": [section.model_dump(mode="json") for section in sections],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


if __name__ == "__main__":
    main()
