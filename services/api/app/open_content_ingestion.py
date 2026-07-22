from __future__ import annotations

import hashlib
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Literal

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
)

OPEN_CONTENT_PARSER_VERSION = "publisher-original-text-v1"
EXPECTED_COLLECTION_COUNTS = {
    "medlineplus_health_topic": 25,
    "medlineplus_test": 10,
    "nci": 10,
    "nimh": 5,
    "myhealthfinder": 5,
}


class OpenPublisherEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    captured_at: datetime
    supporting_locators: list[HttpUrl] = Field(default_factory=list)
    evidence_scope: str | None = None


class OpenRightsPermissions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commercial_use_allowed: bool = True
    storage_allowed: bool = True
    transformation_allowed: bool = True
    translation_allowed: bool = True
    embedding_allowed: bool = True
    excerpt_display_allowed: bool = True
    model_provider_transmission_allowed: bool = True
    redistribution_allowed: bool = True
    prior_version_retention_allowed: bool = True


class OpenPublisher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    stable_id: str = Field(pattern=r"^KBP-[A-Z0-9-]+$")
    name: str
    authority_url: HttpUrl
    rights_url: HttpUrl
    rights_name: str
    attribution: str
    rights_evidence: OpenPublisherEvidence
    rights_stable_id: str | None = Field(default=None, pattern=r"^KBR-[A-Z0-9-]+$")
    jurisdiction: str = "US"
    organization_type: str = "foreign_national_health_authority"
    authority_basis: str | None = None
    allowed_content_classes: list[str] = Field(
        default_factory=lambda: ["official_patient_education_text"]
    )
    rights_scope: str = "publisher_content_class"
    permission_reference: str | None = None
    rights_decision_status: Literal["approved", "pending", "denied"] = "approved"
    rights_permissions: OpenRightsPermissions = Field(default_factory=OpenRightsPermissions)


class OpenSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    text: str = Field(min_length=1)


class OpenDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBS-[A-Z0-9-]+$")
    publisher_key: str
    collection: str
    title: str
    canonical_locator: HttpUrl
    source_type: str
    topic: str
    original_language: str
    publisher_summary: str | None
    publisher_date_text: str
    publication_date: date | None
    review_due_date: date | None = None
    jurisdiction: str | None = None
    population: str | None = None
    captured_at: datetime
    raw_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    sections: list[OpenSection] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_complete_document(self) -> OpenDocument:
        if sum(len(section.text) for section in self.sections) < 500:
            raise ValueError("Captured publisher text is unexpectedly short.")
        return self


class OpenContentCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0", "1.1"]
    generated_at: datetime
    capture_policy: str
    jurisdiction_note: str
    expected_collection_counts: dict[str, int] | None = None
    publishers: list[OpenPublisher]
    documents: list[OpenDocument]

    @model_validator(mode="after")
    def validate_governed_selection(self) -> OpenContentCatalog:
        counts = Counter(document.collection for document in self.documents)
        if self.schema_version == "1.0":
            if self.expected_collection_counts is not None:
                raise ValueError("Open-content schema 1.0 must use the frozen 55-source scope.")
            expected_counts = EXPECTED_COLLECTION_COUNTS
        else:
            if self.expected_collection_counts is None:
                raise ValueError("Open-content schema 1.1 requires expected_collection_counts.")
            expected_counts = self.expected_collection_counts
        if counts != expected_counts:
            raise ValueError(f"Open-content selection counts do not match policy: {counts}")
        if any(not key or value < 1 for key, value in expected_counts.items()):
            raise ValueError("Open-content selection counts must be positive.")
        publisher_keys = {publisher.key for publisher in self.publishers}
        if any(document.publisher_key not in publisher_keys for document in self.documents):
            raise ValueError("Document references an unknown publisher.")
        stable_ids = [document.stable_id for document in self.documents]
        locators = [str(document.canonical_locator) for document in self.documents]
        if len(stable_ids) != len(set(stable_ids)) or len(locators) != len(set(locators)):
            raise ValueError("Open-content source IDs and locators must be unique.")
        return self


def load_open_content_catalog(path: Path) -> OpenContentCatalog:
    return OpenContentCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def _normalized_document(document: OpenDocument) -> str:
    return "\n\n".join(f"# {section.heading}\n{section.text}" for section in document.sections)


def import_open_content_catalog(
    db: Session,
    catalog: OpenContentCatalog,
    *,
    artifact_locator: str = "knowledge_base/catalog/open_patient_education.v1.json",
) -> tuple[int, int, int, int]:
    """Import rights-cleared originals while leaving every retrieval gate closed."""

    publishers_created = rights_created = sources_created = passages_created = 0
    publishers: dict[str, KbPublisher] = {}
    rights_records: dict[str, KbRightsRecord] = {}
    for item in catalog.publishers:
        publisher = db.scalar(select(KbPublisher).where(KbPublisher.stable_id == item.stable_id))
        if publisher is None:
            publisher = KbPublisher(
                stable_id=item.stable_id,
                official_name_zh=item.name,
                official_name_en=item.name,
                organization_type=item.organization_type,
                authority_basis=item.authority_basis
                or (
                    "Verified official United States national health-authority patient "
                    "education; foreign-jurisdiction evidence only."
                ),
                authority_evidence_locator=str(item.authority_url),
                verified_domains_json=[item.authority_url.host],
                jurisdiction=item.jurisdiction,
                review_status="authority_verified",
                allowed_content_classes_json=item.allowed_content_classes,
                reviewed_at=catalog.generated_at,
            )
            db.add(publisher)
            db.flush()
            publishers_created += 1
        publishers[item.key] = publisher

        rights_stable_id = (
            item.rights_stable_id or item.stable_id.replace("KBP-", "KBR-") + "-PUBLIC-DOMAIN"
        )
        rights = db.scalar(
            select(KbRightsRecord).where(KbRightsRecord.stable_id == rights_stable_id)
        )
        if rights is None:
            rights = KbRightsRecord(
                stable_id=rights_stable_id,
                publisher_id=publisher.id,
                scope=item.rights_scope,
                license_name=item.rights_name,
                permission_reference=item.permission_reference
                or (
                    "Applies only to publisher-authored text in the selected public-domain "
                    "content class. Third-party images, logos, linked works, and content "
                    "marked otherwise are excluded."
                ),
                commercial_use_allowed=item.rights_permissions.commercial_use_allowed,
                storage_allowed=item.rights_permissions.storage_allowed,
                transformation_allowed=item.rights_permissions.transformation_allowed,
                translation_allowed=item.rights_permissions.translation_allowed,
                embedding_allowed=item.rights_permissions.embedding_allowed,
                excerpt_display_allowed=item.rights_permissions.excerpt_display_allowed,
                model_provider_transmission_allowed=(
                    item.rights_permissions.model_provider_transmission_allowed
                ),
                redistribution_allowed=item.rights_permissions.redistribution_allowed,
                prior_version_retention_allowed=(
                    item.rights_permissions.prior_version_retention_allowed
                ),
                attribution_requirements=item.attribution,
                evidence_checksum=item.rights_evidence.checksum,
                evidence_locator=str(item.rights_url),
                decision_status=item.rights_decision_status,
                effective_at=item.rights_evidence.captured_at,
            )
            db.add(rights)
            db.flush()
            rights_created += 1
        rights_records[item.key] = rights

    for document in catalog.documents:
        source = db.scalar(select(KbSource).where(KbSource.stable_id == document.stable_id))
        if source is None:
            source = KbSource(
                stable_id=document.stable_id,
                publisher_id=publishers[document.publisher_key].id,
                rights_record_id=rights_records[document.publisher_key].id,
                title=document.title,
                canonical_locator=str(document.canonical_locator),
                source_type=document.source_type,
                jurisdiction=document.jurisdiction
                or publishers[document.publisher_key].jurisdiction,
                intended_audiences_json=["doctor", "patient"],
                topic=document.topic,
                population=document.population,
                original_language="en",
                official_translations_json=[],
                catalog_summary=(
                    document.publisher_summary
                    or "No separate publisher summary is present on the source page."
                ),
                search_keywords_json=[document.title],
                publication_date=document.publication_date,
                review_due_date=document.review_due_date,
                authority_tier="B",
                lifecycle_state=(
                    "rights_cleared_review_pending"
                    if rights_records[document.publisher_key].decision_status == "approved"
                    else "rights_review_pending"
                ),
                medical_review_status="pending",
                native_language_review_status="pending",
                doctor_eligible=False,
                patient_eligible=False,
                catalog_visible=True,
                status="current",
                discovered_at=document.captured_at,
                catalog_verified_at=document.captured_at,
            )
            db.add(source)
            db.flush()
            sources_created += 1
        version = db.scalar(
            select(KbSourceVersion).where(
                KbSourceVersion.source_id == source.id,
                KbSourceVersion.raw_checksum == document.raw_checksum,
            )
        )
        if version is not None:
            continue
        normalized = _normalized_document(document)
        if hashlib.sha256(normalized.encode()).hexdigest() != document.normalized_checksum:
            raise ValueError(f"Normalized checksum mismatch for {document.stable_id}.")
        version = KbSourceVersion(
            stable_id=f"KBV-{document.stable_id.removeprefix('KBS-')}-{document.raw_checksum[:12].upper()}",
            source_id=source.id,
            publisher_version_label=document.publisher_date_text,
            captured_at=document.captured_at,
            capture_mode="publisher_original_text",
            raw_checksum=document.raw_checksum,
            normalized_checksum=document.normalized_checksum,
            normalized_artifact_locator=(f"{artifact_locator}#{document.stable_id}"),
            parser_version=OPEN_CONTENT_PARSER_VERSION,
            valid_from=document.captured_at,
            change_summary="Initial capture of publisher-authored original English text.",
            review_decision="pending",
        )
        db.add(version)
        db.flush()
        for section_ordinal, section_item in enumerate(document.sections):
            section = KbSection(
                stable_id=f"KBC-{document.stable_id.removeprefix('KBS-')}-{section_ordinal:03d}",
                version_id=version.id,
                heading_path_json=[section_item.heading],
                ordinal=section_ordinal,
                language="en",
            )
            db.add(section)
            db.flush()
            text_checksum = hashlib.sha256(section_item.text.encode()).hexdigest()
            db.add(
                KbPassage(
                    stable_id=(
                        f"KBG-{document.stable_id.removeprefix('KBS-')}-{section_ordinal:03d}"
                    ),
                    section_id=section.id,
                    version_id=version.id,
                    ordinal=0,
                    text=section_item.text,
                    language="en",
                    character_count=len(section_item.text),
                    clinical_concept_tags_json=[],
                    audience_json=["doctor", "patient"],
                    chunking_version="original-publisher-section-v1",
                    patient_readability_review_status="pending",
                    lexical_eligible=False,
                    vector_eligible=False,
                    embedding_json=None,
                    content_checksum=text_checksum,
                )
            )
            passages_created += 1
    db.flush()
    return publishers_created, rights_created, sources_created, passages_created
