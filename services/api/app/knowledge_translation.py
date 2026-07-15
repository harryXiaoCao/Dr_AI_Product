from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    KbPassage,
    KbReview,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
    KbTranslationArtifact,
    KbTranslationSection,
)

TRANSLATION_SCHEMA_VERSION = "1.0"
TRANSLATION_TARGET_LANGUAGE = "zh-Hans"
TRANSLATION_PROMPT_POLICY_VERSION = "medical-en-to-zh-hans-v1"
EXPECTED_OPEN_DOCUMENT_COUNT = 55


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class TranslationUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> TranslationUsage:
        if self.total_tokens < self.input_tokens + self.output_tokens:
            raise ValueError("Provider total tokens cannot be below input plus output tokens.")
        return self


class TranslationSectionArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordinal: int = Field(ge=0)
    source_section_stable_id: str = Field(pattern=r"^KBC-[A-Z0-9-]+$")
    source_text_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translated_heading: str
    translated_text: str = Field(min_length=1)
    translation_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_translation_checksum(self) -> TranslationSectionArtifact:
        payload = f"{self.translated_heading}\n{self.translated_text}"
        if sha256_text(payload) != self.translation_checksum:
            raise ValueError("Translation section checksum does not match its content.")
        citation_list = (
            _han_character_ratio(self.translated_heading) >= 0.25
            and self.translated_text.count("http") >= 2
        )
        if _han_character_ratio(payload) < 0.08 and not citation_list:
            raise ValueError("Translation section does not contain enough Simplified Chinese.")
        return self


class TranslationDocumentArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^KBS-[A-Z0-9-]+$")
    source_version_id: str = Field(pattern=r"^KBV-[A-Z0-9-]+$")
    source_normalized_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translated_title: str = Field(min_length=1, max_length=500)
    sections: list[TranslationSectionArtifact] = Field(min_length=1)
    usage: TranslationUsage
    generated_at: datetime
    response_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_structure(self) -> TranslationDocumentArtifact:
        ordinals = [section.ordinal for section in self.sections]
        if ordinals != list(range(len(self.sections))):
            raise ValueError("Translation sections must preserve contiguous source order.")
        if _han_character_ratio(self.translated_title) < 0.25 and not re.fullmatch(
            r"[A-Z0-9][A-Z0-9 .+/\-]{1,30}", self.translated_title
        ):
            raise ValueError("Translated title does not contain enough Simplified Chinese.")
        canonical = _canonical_translation_document(
            self.translated_title,
            [section.model_dump(mode="json") for section in self.sections],
        )
        if sha256_text(canonical) != self.response_checksum:
            raise ValueError("Translation document checksum does not match its content.")
        return self


class TranslationCorpusArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    source_corpus_locator: str
    source_corpus_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_language: Literal["zh-Hans"]
    provider: Literal["deepseek"]
    model: str = Field(min_length=1, max_length=160)
    prompt_policy_version: Literal["medical-en-to-zh-hans-v1"]
    completed_at: datetime
    documents: list[TranslationDocumentArtifact]

    @model_validator(mode="after")
    def validate_complete_corpus(self) -> TranslationCorpusArtifact:
        if len(self.documents) != EXPECTED_OPEN_DOCUMENT_COUNT:
            raise ValueError(
                f"Translation corpus must contain exactly {EXPECTED_OPEN_DOCUMENT_COUNT} documents."
            )
        source_ids = [document.source_id for document in self.documents]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Translation corpus source IDs must be unique.")
        return self


def load_translation_corpus(path: Path) -> TranslationCorpusArtifact:
    return TranslationCorpusArtifact.model_validate_json(path.read_text(encoding="utf-8"))


def import_translation_corpus(
    db: Session,
    corpus: TranslationCorpusArtifact,
    *,
    artifact_locator: str,
) -> tuple[int, int]:
    """Import derived translations without creating or approving any source."""

    artifacts_created = sections_created = 0
    source_count_before = db.scalar(select(func.count()).select_from(KbSource)) or 0
    for document in corpus.documents:
        row = db.execute(
            select(KbSource, KbSourceVersion, KbRightsRecord)
            .join(KbSourceVersion, KbSourceVersion.source_id == KbSource.id)
            .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
            .where(
                KbSource.stable_id == document.source_id,
                KbSourceVersion.stable_id == document.source_version_id,
            )
        ).one_or_none()
        if row is None:
            raise ValueError(f"Unknown source/version pair: {document.source_id}")
        source, version, rights = row
        if version.normalized_checksum != document.source_normalized_checksum:
            raise ValueError(f"Source checksum drift for {document.source_id}.")
        if not _translation_rights_allowed(rights):
            raise ValueError(
                f"Translation/provider rights are not approved for {document.source_id}."
            )

        existing = db.scalar(
            select(KbTranslationArtifact).where(
                KbTranslationArtifact.source_version_id == version.id,
                KbTranslationArtifact.target_language == corpus.target_language,
                KbTranslationArtifact.model == corpus.model,
                KbTranslationArtifact.prompt_policy_version == corpus.prompt_policy_version,
            )
        )
        if existing is not None:
            if existing.translation_checksum != document.response_checksum:
                raise ValueError(f"Existing translation differs for {document.source_id}.")
            continue

        source_sections = db.execute(
            select(KbSection, KbPassage)
            .join(KbPassage, KbPassage.section_id == KbSection.id)
            .where(KbSection.version_id == version.id)
            .order_by(KbSection.ordinal, KbPassage.ordinal)
        ).all()
        if len(source_sections) != len(document.sections):
            raise ValueError(f"Source section count drift for {document.source_id}.")
        for translated, (section, passage) in zip(document.sections, source_sections, strict=True):
            if translated.source_section_stable_id != section.stable_id:
                raise ValueError(f"Source section lineage drift for {document.source_id}.")
            if translated.source_text_checksum != passage.content_checksum:
                raise ValueError(f"Source text checksum drift for {document.source_id}.")

        artifact = KbTranslationArtifact(
            stable_id=(
                f"KBT-{document.source_id.removeprefix('KBS-')}-ZH-"
                f"{document.response_checksum[:12].upper()}"
            ),
            source_id=source.id,
            source_version_id=version.id,
            target_language=corpus.target_language,
            translated_title=document.translated_title,
            provider=corpus.provider,
            model=corpus.model,
            prompt_policy_version=corpus.prompt_policy_version,
            source_checksum=document.source_normalized_checksum,
            translation_checksum=document.response_checksum,
            artifact_locator=f"{artifact_locator}#{document.source_id}",
            status="generated_pending_review",
            medical_review_status="pending",
            native_language_review_status="pending",
            input_tokens=document.usage.input_tokens,
            output_tokens=document.usage.output_tokens,
            generated_at=document.generated_at,
        )
        db.add(artifact)
        db.flush()
        artifacts_created += 1
        for translated in document.sections:
            db.add(
                KbTranslationSection(
                    stable_id=(
                        f"KBTS-{document.source_id.removeprefix('KBS-')}-ZH-"
                        f"{translated.ordinal:03d}-{translated.translation_checksum[:10].upper()}"
                    ),
                    artifact_id=artifact.id,
                    source_section_stable_id=translated.source_section_stable_id,
                    ordinal=translated.ordinal,
                    translated_heading=translated.translated_heading,
                    translated_text=translated.translated_text,
                    content_checksum=translated.translation_checksum,
                )
            )
            sections_created += 1

    db.flush()
    source_count_after = db.scalar(select(func.count()).select_from(KbSource)) or 0
    if source_count_after != source_count_before:
        raise RuntimeError("Translation import changed the knowledge-source count.")
    return artifacts_created, sections_created


def record_translation_review(
    db: Session,
    *,
    artifact_stable_id: str,
    review_type: Literal["medical", "native_chinese"],
    reviewer_id: str,
    approved: bool,
    findings: str | None = None,
    reviewed_at: datetime | None = None,
) -> KbTranslationArtifact:
    artifact = db.scalar(
        select(KbTranslationArtifact).where(KbTranslationArtifact.stable_id == artifact_stable_id)
    )
    if artifact is None:
        raise ValueError("Translation artifact was not found.")
    decision = "approved" if approved else "rejected"
    timestamp = reviewed_at or datetime.now(UTC)
    review_id = sha256_text(
        f"{artifact_stable_id}:{review_type}:{reviewer_id}:{decision}:{timestamp.isoformat()}"
    )[:20].upper()
    db.add(
        KbReview(
            stable_id=f"KBRV-TRANSLATION-{review_id}",
            target_type="translation_artifact",
            target_stable_id=artifact_stable_id,
            review_type=review_type,
            reviewer_role=(
                "medical_reviewer" if review_type == "medical" else "native_chinese_reviewer"
            ),
            reviewer_id=reviewer_id,
            decision=decision,
            decision_code=f"translation_{review_type}_{decision}",
            findings=findings,
            reviewed_at=timestamp,
        )
    )
    if review_type == "medical":
        artifact.medical_review_status = decision
    else:
        artifact.native_language_review_status = decision
    if not approved:
        artifact.status = "rejected"
        artifact.approved_at = None
    elif (
        artifact.medical_review_status == "approved"
        and artifact.native_language_review_status == "approved"
    ):
        artifact.status = "approved"
        artifact.approved_at = timestamp
    else:
        artifact.status = "generated_pending_review"
    db.flush()
    return artifact


def _translation_rights_allowed(rights: KbRightsRecord) -> bool:
    return bool(
        rights.decision_status == "approved"
        and rights.storage_allowed
        and rights.transformation_allowed
        and rights.translation_allowed
        and rights.model_provider_transmission_allowed
        and rights.redistribution_allowed
    )


def _han_character_ratio(value: str) -> float:
    compact = re.sub(r"\s+", "", value)
    if not compact:
        return 0.0
    return len(re.findall(r"[\u3400-\u9fff]", compact)) / len(compact)


def _canonical_translation_document(title: str, sections: list[dict[str, object]]) -> str:
    normalized_sections = [
        {
            "ordinal": section["ordinal"],
            "source_section_stable_id": section["source_section_stable_id"],
            "source_text_checksum": section["source_text_checksum"],
            "translated_heading": section["translated_heading"],
            "translated_text": section["translated_text"],
            "translation_checksum": section["translation_checksum"],
        }
        for section in sections
    ]
    return json.dumps(
        {"translated_title": title, "sections": normalized_sections},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
