from __future__ import annotations

import hashlib
from datetime import UTC, datetime, time
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    KbPassage,
    KbPublisher,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
    KbTranslationArtifact,
    KbTranslationSection,
)

EXPECTED_ROW_COUNT = 697
EXPECTED_SOURCE_COUNT = 684
HPA_PUBLISHER_ID = "KBP-TW-HPA"
HPA_RIGHTS_ID = "KBR-TW-HPA-OGDL-1-0-HEALTH-MYTHS"
PARSER_VERSION = "hpa-health-myths-csv-v1"
CONVERSION_POLICY_VERSION = "deterministic-zh-hant-to-zh-hans-v1"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locator: HttpUrl
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    captured_at: datetime


class CorpusVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBV-HPA-[A-Z0-9-]+$")
    row_ordinal: int = Field(ge=1)
    publisher_date_text: str
    publication_date: datetime
    original_question: str = Field(min_length=1)
    original_answer: str = Field(min_length=1)
    original_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    simplified_question: str = Field(min_length=1)
    simplified_answer: str = Field(min_length=1)
    simplified_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedes_version_id: str | None = None

    @model_validator(mode="after")
    def validate_checksums(self) -> CorpusVersion:
        original = (
            f"{self.row_ordinal}\n{self.publisher_date_text}\n"
            f"{self.original_question}\n{self.original_answer}"
        )
        simplified = f"{self.simplified_question}\n{self.simplified_answer}"
        if sha256_text(original) != self.original_checksum:
            raise ValueError("Original question-answer checksum mismatch.")
        if sha256_text(simplified) != self.simplified_checksum:
            raise ValueError("Simplified question-answer checksum mismatch.")
        return self


class CorpusSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBS-HPA-[A-Z0-9-]+$")
    canonical_locator: HttpUrl
    current_version_id: str = Field(pattern=r"^KBV-HPA-[A-Z0-9-]+$")
    versions: list[CorpusVersion] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_versions(self) -> CorpusSource:
        version_ids = [item.stable_id for item in self.versions]
        if len(version_ids) != len(set(version_ids)):
            raise ValueError("Source version IDs must be unique.")
        if self.current_version_id != version_ids[-1]:
            raise ValueError("The current version must be the final chronological version.")
        for index, version in enumerate(self.versions):
            expected = self.versions[index - 1].stable_id if index else None
            if version.supersedes_version_id != expected:
                raise ValueError("Source version supersession chain is invalid.")
        return self


class HpaHealthMythsCorpus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    generated_at: datetime
    dataset_title: str
    dataset_locator: HttpUrl
    publisher_name_zh_hant: str
    publisher_name_zh_hans: str
    jurisdiction: str
    source_language: str
    stored_adaptation_language: str
    source_csv_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_row_count: int
    unique_source_count: int
    duplicate_question_group_count: int
    dataset_evidence: EvidenceRecord
    rights_evidence: EvidenceRecord
    license_name: str
    attribution: str
    conversion_provider: str
    conversion_model: str
    conversion_policy_version: str
    sources: list[CorpusSource]

    @model_validator(mode="after")
    def validate_complete_corpus(self) -> HpaHealthMythsCorpus:
        if self.source_row_count != EXPECTED_ROW_COUNT:
            raise ValueError(f"Expected {EXPECTED_ROW_COUNT} source rows.")
        if self.unique_source_count != EXPECTED_SOURCE_COUNT:
            raise ValueError(f"Expected {EXPECTED_SOURCE_COUNT} unique questions.")
        if len(self.sources) != self.unique_source_count:
            raise ValueError("Unique source count does not match the source collection.")
        versions = [version for source in self.sources for version in source.versions]
        if len(versions) != self.source_row_count:
            raise ValueError("Version count does not preserve every source row.")
        if self.source_language != "zh-Hant" or self.stored_adaptation_language != "zh-Hans":
            raise ValueError("The corpus must preserve zh-Hant lineage and zh-Hans adaptations.")
        if self.conversion_policy_version != CONVERSION_POLICY_VERSION:
            raise ValueError("Unexpected conversion policy version.")
        return self


def load_hpa_health_myths_corpus(path: Path) -> HpaHealthMythsCorpus:
    return HpaHealthMythsCorpus.model_validate_json(path.read_text(encoding="utf-8"))


def import_hpa_health_myths_corpus(
    db: Session,
    corpus: HpaHealthMythsCorpus,
    *,
    artifact_locator: str,
) -> tuple[int, int, int, int, int, int]:
    """Store all licensed Q&A versions and review-pending Simplified Chinese adaptations."""

    publisher_created = rights_created = sources_created = 0
    versions_created = passages_created = translations_created = 0

    publisher = db.scalar(select(KbPublisher).where(KbPublisher.stable_id == HPA_PUBLISHER_ID))
    if publisher is None:
        publisher = KbPublisher(
            stable_id=HPA_PUBLISHER_ID,
            official_name_zh=corpus.publisher_name_zh_hans,
            official_name_en="Health Promotion Administration, Ministry of Health and Welfare",
            organization_type="foreign_national_health_authority",
            authority_basis=(
                "Official Taiwan national health-promotion authority and publisher of the "
                "licensed Health Myths open dataset. Taiwan-jurisdiction evidence only."
            ),
            authority_evidence_locator=str(corpus.dataset_locator),
            verified_domains_json=["data.gov.tw", "www.hpa.gov.tw"],
            jurisdiction=corpus.jurisdiction,
            review_status="authority_verified",
            allowed_content_classes_json=["official_health_myth_qa"],
            reviewed_at=corpus.generated_at,
        )
        db.add(publisher)
        db.flush()
        publisher_created = 1

    rights = db.scalar(select(KbRightsRecord).where(KbRightsRecord.stable_id == HPA_RIGHTS_ID))
    if rights is None:
        rights = KbRightsRecord(
            stable_id=HPA_RIGHTS_ID,
            publisher_id=publisher.id,
            scope="dataset",
            license_name=corpus.license_name,
            permission_reference=(
                "Applies to the text fields released in dataset 43338. Logos, trademarks, "
                "separately marked third-party works, images, videos, and external attachments "
                "are excluded. Embedding and model-provider transmission remain disabled until "
                "their separate product/legal gate is recorded."
            ),
            commercial_use_allowed=True,
            storage_allowed=True,
            transformation_allowed=True,
            translation_allowed=True,
            embedding_allowed=False,
            excerpt_display_allowed=True,
            model_provider_transmission_allowed=False,
            redistribution_allowed=True,
            prior_version_retention_allowed=True,
            attribution_requirements=corpus.attribution,
            evidence_checksum=corpus.rights_evidence.checksum,
            evidence_locator=str(corpus.rights_evidence.locator),
            decision_status="approved",
            effective_at=corpus.rights_evidence.captured_at,
        )
        db.add(rights)
        db.flush()
        rights_created = 1

    for source_item in corpus.sources:
        current = source_item.versions[-1]
        source = db.scalar(select(KbSource).where(KbSource.stable_id == source_item.stable_id))
        if source is None:
            source = KbSource(
                stable_id=source_item.stable_id,
                publisher_id=publisher.id,
                rights_record_id=rights.id,
                title=current.simplified_question,
                canonical_locator=str(source_item.canonical_locator),
                source_type="health_myth_qa",
                jurisdiction=corpus.jurisdiction,
                intended_audiences_json=["doctor", "patient"],
                topic="health_education",
                original_language=corpus.source_language,
                official_translations_json=[],
                catalog_summary=(
                    "台湾卫生福利部国民健康署官方保健辟谣问答的简体中文适配。"
                    "台湾适用性、医疗、原生简体中文及患者可读性审查尚未完成。"
                ),
                search_keywords_json=[current.simplified_question],
                publication_date=current.publication_date.date(),
                authority_tier="C",
                lifecycle_state="rights_cleared_review_pending",
                medical_review_status="pending",
                native_language_review_status="pending",
                doctor_eligible=False,
                patient_eligible=False,
                catalog_visible=True,
                status="current",
                discovered_at=corpus.generated_at,
                catalog_verified_at=corpus.generated_at,
            )
            db.add(source)
            db.flush()
            sources_created += 1

        prior_version: KbSourceVersion | None = None
        for version_item in source_item.versions:
            normalized_original_checksum = sha256_text(
                f"{version_item.original_question}\n{version_item.original_answer}"
            )
            version = db.scalar(
                select(KbSourceVersion).where(KbSourceVersion.stable_id == version_item.stable_id)
            )
            if version is None:
                version = KbSourceVersion(
                    stable_id=version_item.stable_id,
                    source_id=source.id,
                    publisher_version_label=version_item.publisher_date_text,
                    captured_at=corpus.generated_at,
                    capture_mode="licensed_dataset_original_text",
                    raw_checksum=version_item.original_checksum,
                    normalized_checksum=normalized_original_checksum,
                    raw_artifact_locator=(
                        "knowledge_base/raw/"
                        "hpa_health_myths.zh-Hant.dataset-43338.2026-07-02.csv"
                        f"#row-{version_item.row_ordinal}"
                    ),
                    normalized_artifact_locator=(f"{artifact_locator}#{version_item.stable_id}"),
                    parser_version=PARSER_VERSION,
                    valid_from=datetime.combine(
                        version_item.publication_date.date(), time.min, tzinfo=UTC
                    ),
                    supersedes_version_id=prior_version.id if prior_version else None,
                    change_summary=(
                        "Initial licensed dataset record."
                        if prior_version is None
                        else "Later publisher row for the same normalized question."
                    ),
                    review_decision="pending",
                )
                db.add(version)
                db.flush()
                versions_created += 1

                suffix = version_item.stable_id.removeprefix("KBV-")
                section = KbSection(
                    stable_id=f"KBC-{suffix}-000",
                    version_id=version.id,
                    heading_path_json=[version_item.original_question],
                    ordinal=0,
                    language="zh-Hant",
                )
                db.add(section)
                db.flush()
                db.add(
                    KbPassage(
                        stable_id=f"KBG-{suffix}-000",
                        section_id=section.id,
                        version_id=version.id,
                        ordinal=0,
                        text=version_item.original_answer,
                        language="zh-Hant",
                        character_count=len(version_item.original_answer),
                        clinical_concept_tags_json=[],
                        audience_json=["doctor", "patient"],
                        chunking_version="hpa-health-myth-qa-v1",
                        patient_readability_review_status="pending",
                        lexical_eligible=False,
                        vector_eligible=False,
                        embedding_json=None,
                        content_checksum=sha256_text(version_item.original_answer),
                    )
                )
                passages_created += 1

                artifact = KbTranslationArtifact(
                    stable_id=f"KBT-{suffix}-ZH",
                    source_id=source.id,
                    source_version_id=version.id,
                    target_language="zh-Hans",
                    translated_title=version_item.simplified_question,
                    provider=corpus.conversion_provider,
                    model=corpus.conversion_model,
                    prompt_policy_version=corpus.conversion_policy_version,
                    source_checksum=normalized_original_checksum,
                    translation_checksum=version_item.simplified_checksum,
                    artifact_locator=f"{artifact_locator}#{version_item.stable_id}-zh-Hans",
                    status="generated_pending_review",
                    medical_review_status="pending",
                    native_language_review_status="pending",
                    input_tokens=None,
                    output_tokens=None,
                    generated_at=corpus.generated_at,
                )
                db.add(artifact)
                db.flush()
                db.add(
                    KbTranslationSection(
                        stable_id=f"KBTS-{suffix}-ZH-000",
                        artifact_id=artifact.id,
                        source_section_stable_id=section.stable_id,
                        ordinal=0,
                        translated_heading=version_item.simplified_question,
                        translated_text=version_item.simplified_answer,
                        content_checksum=version_item.simplified_checksum,
                    )
                )
                translations_created += 1
            prior_version = version

    db.flush()
    return (
        publisher_created,
        rights_created,
        sources_created,
        versions_created,
        passages_created,
        translations_created,
    )
