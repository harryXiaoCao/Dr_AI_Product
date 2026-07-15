from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    KbReview,
    KbRightsRecord,
    KbSource,
    KbSourceVersion,
    KbSummaryArtifact,
    KbTranslationArtifact,
)

SUMMARY_SCHEMA_VERSION = "1.0"
SUMMARY_PROMPT_POLICY_VERSION = "bilingual-medical-search-summary-v1"
EXPECTED_SUMMARY_DOCUMENT_COUNT = 55


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SummaryUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> SummaryUsage:
        if self.total_tokens < self.input_tokens + self.output_tokens:
            raise ValueError("Provider total tokens cannot be below input plus output tokens.")
        return self


class SummaryDocumentArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^KBS-[A-Z0-9-]+$")
    source_version_id: str = Field(pattern=r"^KBV-[A-Z0-9-]+$")
    source_normalized_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    english_summary: str = Field(min_length=80, max_length=1200)
    chinese_summary: str = Field(min_length=40, max_length=800)
    usage: SummaryUsage
    generated_at: datetime
    response_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_content(self) -> SummaryDocumentArtifact:
        if len(re.findall(r"[A-Za-z]+", self.english_summary)) < 12:
            raise ValueError("English summary does not contain enough English text.")
        if len(re.findall(r"[\u3400-\u9fff]", self.chinese_summary)) < 20:
            raise ValueError("Chinese summary does not contain enough Simplified Chinese.")
        canonical = canonical_summary_response(self.english_summary, self.chinese_summary)
        if sha256_text(canonical) != self.response_checksum:
            raise ValueError("Summary response checksum does not match its content.")
        return self


class SummaryCorpusArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    source_corpus_locator: str
    source_corpus_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_corpus_locator: str
    translation_corpus_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider: Literal["deepseek"]
    model: str = Field(min_length=1, max_length=160)
    prompt_policy_version: Literal["bilingual-medical-search-summary-v1"]
    status: Literal["generated_pending_review"]
    completed_at: datetime
    documents: list[SummaryDocumentArtifact]

    @model_validator(mode="after")
    def validate_complete_corpus(self) -> SummaryCorpusArtifact:
        if len(self.documents) != EXPECTED_SUMMARY_DOCUMENT_COUNT:
            raise ValueError(
                f"Summary corpus must contain exactly {EXPECTED_SUMMARY_DOCUMENT_COUNT} documents."
            )
        source_ids = [document.source_id for document in self.documents]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Summary corpus source IDs must be unique.")
        return self


def load_summary_corpus(path: Path) -> SummaryCorpusArtifact:
    return SummaryCorpusArtifact.model_validate_json(path.read_text(encoding="utf-8"))


def import_reviewed_summary_corpus(
    db: Session,
    corpus: SummaryCorpusArtifact,
    *,
    artifact_locator: str,
    reviewer_id: str,
    reviewed_at: datetime,
    review_findings: str | None = None,
) -> int:
    """Import manually reviewed summaries without changing source or retrieval eligibility."""

    if not reviewer_id.strip():
        raise ValueError("A summary reviewer identifier is required.")
    created = 0
    source_count_before = db.scalar(select(func.count()).select_from(KbSource)) or 0
    for document in corpus.documents:
        row = db.execute(
            select(KbSource, KbSourceVersion, KbRightsRecord, KbTranslationArtifact)
            .join(KbSourceVersion, KbSourceVersion.source_id == KbSource.id)
            .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
            .join(
                KbTranslationArtifact,
                KbTranslationArtifact.source_version_id == KbSourceVersion.id,
            )
            .where(
                KbSource.stable_id == document.source_id,
                KbSourceVersion.stable_id == document.source_version_id,
                KbTranslationArtifact.translation_checksum == document.translation_checksum,
                KbTranslationArtifact.status == "approved",
            )
        ).one_or_none()
        if row is None:
            raise ValueError(
                f"Approved source/version/translation lineage was not found: {document.source_id}"
            )
        source, version, rights, translation = row
        if version.normalized_checksum != document.source_normalized_checksum:
            raise ValueError(f"Source checksum drift for {document.source_id}.")
        if not _summary_rights_allowed(rights):
            raise ValueError(f"Summary rights are not approved for {document.source_id}.")

        existing = db.scalar(
            select(KbSummaryArtifact).where(
                KbSummaryArtifact.source_version_id == version.id,
                KbSummaryArtifact.model == corpus.model,
                KbSummaryArtifact.prompt_policy_version == corpus.prompt_policy_version,
            )
        )
        if existing is not None:
            if existing.summary_checksum != document.response_checksum:
                raise ValueError(f"Existing summary differs for {document.source_id}.")
            if existing.status != "approved":
                raise ValueError(f"Existing summary is not approved for {document.source_id}.")
            continue

        stable_id = (
            f"KBSM-{document.source_id.removeprefix('KBS-')}-"
            f"{document.response_checksum[:12].upper()}"
        )
        artifact = KbSummaryArtifact(
            stable_id=stable_id,
            source_id=source.id,
            source_version_id=version.id,
            translation_artifact_id=translation.id,
            english_summary=document.english_summary,
            chinese_summary=document.chinese_summary,
            provider=corpus.provider,
            model=corpus.model,
            prompt_policy_version=corpus.prompt_policy_version,
            source_checksum=document.source_normalized_checksum,
            translation_checksum=document.translation_checksum,
            summary_checksum=document.response_checksum,
            artifact_locator=f"{artifact_locator}#{document.source_id}",
            status="approved",
            reviewer_id=reviewer_id,
            review_findings=review_findings,
            reviewed_at=reviewed_at,
            input_tokens=document.usage.input_tokens,
            output_tokens=document.usage.output_tokens,
            generated_at=document.generated_at,
        )
        db.add(artifact)
        db.flush()
        review_key = sha256_text(f"{stable_id}:{reviewer_id}:{reviewed_at.isoformat()}:approved")[
            :20
        ].upper()
        db.add(
            KbReview(
                stable_id=f"KBRV-SUMMARY-{review_key}",
                target_type="summary_artifact",
                target_stable_id=stable_id,
                review_type="bilingual_summary",
                reviewer_role="medical_and_native_language_reviewers",
                reviewer_id=reviewer_id,
                decision="approved",
                decision_code="bilingual_summary_manual_review_approved",
                findings=review_findings,
                reviewed_at=reviewed_at,
            )
        )
        created += 1

    db.flush()
    source_count_after = db.scalar(select(func.count()).select_from(KbSource)) or 0
    if source_count_after != source_count_before:
        raise RuntimeError("Summary import changed the knowledge-source count.")
    return created


def canonical_summary_response(english_summary: str, chinese_summary: str) -> str:
    return json.dumps(
        {"chinese_summary": chinese_summary, "english_summary": english_summary},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _summary_rights_allowed(rights: KbRightsRecord) -> bool:
    return bool(
        rights.decision_status == "approved"
        and rights.storage_allowed
        and rights.transformation_allowed
        and rights.model_provider_transmission_allowed
        and rights.redistribution_allowed
    )
