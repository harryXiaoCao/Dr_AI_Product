from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    KbPassage,
    KbPublisher,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
)

WHO_PERMISSION_REQUEST_ID = "202609681"
WHO_RIGHTS_STABLE_ID = "KBR-WHO-PERMISSION-202609681"
WHO_PARSER_VERSION = "who-fact-sheet-official-text-v2"


class WhoSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1)


class WhoLanguageDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["en", "zh-Hans"]
    title: str = Field(min_length=1, max_length=500)
    canonical_locator: str = Field(
        pattern=r"^https://www\.who\.int/(?:zh/)?news-room/fact-sheets/detail/"
    )
    publisher_date_text: str
    publication_date: str | None = None
    raw_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    sections: list[WhoSection] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_document(self) -> WhoLanguageDocument:
        if sum(len(section.text) for section in self.sections) < 300:
            raise ValueError("WHO fact-sheet extraction is unexpectedly short.")
        prefix = "/zh/" if self.language == "zh-Hans" else "/news-room/"
        if prefix not in self.canonical_locator:
            raise ValueError("WHO document language does not match its official locator.")
        return self


class WhoSourceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_stable_id: str = Field(pattern=r"^KBS-WHO-")
    documents: list[WhoLanguageDocument] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def validate_languages(self) -> WhoSourceBundle:
        languages = [document.language for document in self.documents]
        if len(languages) != len(set(languages)):
            raise ValueError("WHO source bundle repeats an official language.")
        return self


class WhoPermissionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: Literal["202609681"]
    authorization_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    approved_form_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    agreement_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_at: datetime


class WhoFactSheetCorpus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    generated_at: datetime
    permission: WhoPermissionEvidence
    english_index_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    chinese_index_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_language_document_counts: dict[Literal["en", "zh-Hans"], int]
    excluded_content: list[str]
    sources: list[WhoSourceBundle] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_complete_corpus(self) -> WhoFactSheetCorpus:
        counts = {"en": 0, "zh-Hans": 0}
        source_ids: list[str] = []
        locators: list[str] = []
        for source in self.sources:
            source_ids.append(source.source_stable_id)
            for document in source.documents:
                counts[document.language] += 1
                locators.append(document.canonical_locator)
        if counts != self.expected_language_document_counts:
            raise ValueError(f"WHO language-document counts do not match: {counts}")
        if len(source_ids) != len(set(source_ids)) or len(locators) != len(set(locators)):
            raise ValueError("WHO source IDs and official locators must be unique.")
        required_exclusions = {"images", "logos", "third_party_credited_material"}
        if not required_exclusions.issubset(self.excluded_content):
            raise ValueError("WHO corpus must exclude non-licensed visual/third-party material.")
        return self


def load_who_fact_sheet_corpus(path: Path) -> WhoFactSheetCorpus:
    return WhoFactSheetCorpus.model_validate_json(path.read_text(encoding="utf-8"))


def _normalized_document(document: WhoLanguageDocument) -> str:
    return "\n\n".join(f"# {section.heading}\n{section.text}" for section in document.sections)


def _bundle_checksum(bundle: WhoSourceBundle) -> str:
    value = "\n".join(
        f"{document.language}:{document.raw_checksum}:{document.normalized_checksum}"
        for document in sorted(bundle.documents, key=lambda item: item.language)
    )
    return hashlib.sha256(value.encode()).hexdigest()


def import_who_fact_sheet_corpus(
    db: Session,
    corpus: WhoFactSheetCorpus,
    *,
    artifact_locator: str = "knowledge_base/catalog/who_fact_sheets.official.v1.json",
) -> tuple[int, int, int]:
    """Import licensed official text while preserving all clinical release gates."""

    publisher = db.scalar(select(KbPublisher).where(KbPublisher.stable_id == "KBP-WHO"))
    if publisher is None:
        raise ValueError("Import the authoritative WHO metadata catalog first.")

    rights_created = versions_created = passages_created = 0
    rights = db.scalar(
        select(KbRightsRecord).where(KbRightsRecord.stable_id == WHO_RIGHTS_STABLE_ID)
    )
    evidence_checksum = hashlib.sha256(
        (
            corpus.permission.authorization_checksum
            + corpus.permission.approved_form_checksum
            + corpus.permission.agreement_checksum
        ).encode()
    ).hexdigest()
    permission_reference = (
        "WHO Permissions request 202609681. Non-exclusive, worldwide, royalty-free, "
        "non-transferable and non-sublicensable permission for the complete WHO Fact "
        "Sheets collection in the non-commercial Dr. AI Product. Product storage, "
        "format/style normalization, embeddings, attributed verbatim excerpts, RAG/AI "
        "operation and Product distribution are permitted. Translation, standalone "
        "distribution, public-LLM release, advertising, promotional/commercial use, WHO "
        "branding/logo, endorsement claims, and substantive modification are prohibited. "
        "Third-party credited material is excluded. Breach terminates automatically; WHO "
        "may terminate by notice and distribution must cease within at most 90 days."
    )
    attribution = (
        "Identify World Health Organization as the source; show the original fact-sheet "
        "title, publication/update date, official URL, and a clear statement that Dr. AI "
        "was not developed or published by WHO and is not endorsed by or affiliated with "
        "WHO. Do not use the WHO logo or emblem. Verbatim excerpts require a source link. "
        "AI-generated text must not be attributed to WHO; identify WHO only as a general "
        "source and state that WHO is not responsible for AI-generated content."
    )
    if rights is None:
        rights = KbRightsRecord(
            stable_id=WHO_RIGHTS_STABLE_ID,
            publisher_id=publisher.id,
            scope="publisher_fact_sheet_collection",
            license_name="WHO non-exclusive permission, request 202609681",
            permission_reference=permission_reference,
            commercial_use_allowed=False,
            storage_allowed=True,
            transformation_allowed=True,
            translation_allowed=False,
            embedding_allowed=True,
            excerpt_display_allowed=True,
            model_provider_transmission_allowed=True,
            redistribution_allowed=True,
            prior_version_retention_allowed=False,
            attribution_requirements=attribution,
            evidence_checksum=evidence_checksum,
            evidence_locator="https://www.who.int/about/policies/publishing/copyright",
            decision_status="approved",
            legal_reviewer_id="who-permissions-team-request-202609681",
            effective_at=corpus.permission.recorded_at,
        )
        db.add(rights)
        db.flush()
        rights_created = 1
    elif rights.evidence_checksum != evidence_checksum:
        raise ValueError("Stored WHO permission evidence differs from this corpus manifest.")

    for bundle in corpus.sources:
        source = db.scalar(select(KbSource).where(KbSource.stable_id == bundle.source_stable_id))
        if source is None or source.publisher_id != publisher.id:
            raise ValueError(f"Unknown WHO catalog source: {bundle.source_stable_id}")
        source.rights_record_id = rights.id
        source.lifecycle_state = "rights_cleared_review_pending"
        source.medical_review_status = "pending"
        source.native_language_review_status = "pending"
        source.doctor_eligible = False
        source.patient_eligible = False
        source.catalog_verified_at = corpus.generated_at
        original_document = next(
            document
            for document in bundle.documents
            if document.language == source.original_language
        )
        source.title = original_document.title
        source.publication_date = (
            datetime.fromisoformat(original_document.publication_date).date()
            if original_document.publication_date
            else None
        )
        source.official_translations_json = [
            {
                "language": document.language,
                "title": document.title,
                "official_locator": document.canonical_locator,
            }
            for document in bundle.documents
            if document.language != source.original_language
        ]
        source.catalog_summary = (
            "WHO官方事实清单原文已按许可请求202609681存入受访问控制的知识库；"
            "医学、语言及受众审核仍待完成，尚未进入医生或患者检索版本。"
            if source.original_language == "zh-Hans"
            else "Official WHO fact-sheet text stored under permission request 202609681; "
            "medical, language, and audience review remain pending, and the source is not "
            "included in doctor or patient retrieval releases."
        )

        raw_checksum = _bundle_checksum(bundle)
        existing = db.scalar(
            select(KbSourceVersion).where(
                KbSourceVersion.source_id == source.id,
                KbSourceVersion.raw_checksum == raw_checksum,
            )
        )
        if existing is not None:
            continue
        normalized_checksum = hashlib.sha256(
            "\n\n".join(
                f"[{document.language}]\n{_normalized_document(document)}"
                for document in sorted(bundle.documents, key=lambda item: item.language)
            ).encode()
        ).hexdigest()
        version = KbSourceVersion(
            stable_id=(
                f"KBV-{bundle.source_stable_id.removeprefix('KBS-')}-{raw_checksum[:12].upper()}"
            ),
            source_id=source.id,
            publisher_version_label="; ".join(
                f"{document.language}: {document.publisher_date_text}"
                for document in bundle.documents
            ),
            captured_at=corpus.generated_at,
            capture_mode="publisher_original_text",
            raw_checksum=raw_checksum,
            normalized_checksum=normalized_checksum,
            normalized_artifact_locator=f"{artifact_locator}#{bundle.source_stable_id}",
            parser_version=WHO_PARSER_VERSION,
            valid_from=corpus.generated_at,
            change_summary=(
                "Licensed capture of official WHO fact-sheet text; images, logos and "
                "third-party credited material excluded. Review and retrieval remain closed."
            ),
            review_decision="pending",
        )
        db.add(version)
        db.flush()
        versions_created += 1
        version_tag = raw_checksum[:8].upper()
        ordinal = 0
        for document in bundle.documents:
            normalized = _normalized_document(document)
            if hashlib.sha256(normalized.encode()).hexdigest() != document.normalized_checksum:
                raise ValueError(f"Normalized checksum mismatch for {document.canonical_locator}")
            for section_item in document.sections:
                section = KbSection(
                    stable_id=(
                        f"KBC-{bundle.source_stable_id.removeprefix('KBS-')}-"
                        f"{version_tag}-{document.language.upper().replace('-', '')}-{ordinal:03d}"
                    ),
                    version_id=version.id,
                    heading_path_json=[section_item.heading],
                    ordinal=ordinal,
                    language=document.language,
                )
                db.add(section)
                db.flush()
                content_checksum = hashlib.sha256(section_item.text.encode()).hexdigest()
                db.add(
                    KbPassage(
                        stable_id=(
                            f"KBG-{bundle.source_stable_id.removeprefix('KBS-')}-"
                            f"{version_tag}-"
                            f"{document.language.upper().replace('-', '')}-{ordinal:03d}"
                        ),
                        section_id=section.id,
                        version_id=version.id,
                        ordinal=0,
                        text=section_item.text,
                        language=document.language,
                        character_count=len(section_item.text),
                        clinical_concept_tags_json=[],
                        audience_json=["doctor", "patient"],
                        chunking_version="who-official-structural-section-v1",
                        patient_readability_review_status="pending",
                        lexical_eligible=False,
                        vector_eligible=False,
                        embedding_json=None,
                        content_checksum=content_checksum,
                    )
                )
                passages_created += 1
                ordinal += 1

        obsolete_versions = db.scalars(
            select(KbSourceVersion).where(
                KbSourceVersion.source_id == source.id,
                KbSourceVersion.id != version.id,
                KbSourceVersion.capture_mode == "publisher_original_text",
                KbSourceVersion.parser_version.like("who-fact-sheet-official-text-v%"),
            )
        ).all()
        for obsolete_version in obsolete_versions:
            if (
                obsolete_version.review_decision != "pending"
                or obsolete_version.index_release_id is not None
            ):
                raise ValueError("Cannot replace a reviewed or released WHO parser artifact.")
            db.delete(obsolete_version)
    db.flush()
    return rights_created, versions_created, passages_created
