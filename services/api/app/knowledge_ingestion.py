from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.knowledge_rights import provider_transmission_allowed
from app.models import (
    KbActiveIndexRelease,
    KbIndexRelease,
    KbIndexReleasePassage,
    KbPassage,
    KbPublisher,
    KbReview,
    KbRightsRecord,
    KbSource,
    KbSourceFamily,
    KbSourceVersion,
    KbTerm,
)

CATALOG_SCHEMA_VERSION = "1.0"
METADATA_PARSER_VERSION = "catalog-metadata-v1"


class CatalogPublisher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBP-[A-Z0-9-]+$")
    official_name_zh: str = Field(min_length=2, max_length=240)
    official_name_en: str | None = Field(default=None, max_length=240)
    organization_type: str = Field(min_length=2, max_length=80)
    authority_basis: str = Field(min_length=10)
    authority_evidence_locator: HttpUrl
    verified_domains: list[str] = Field(min_length=1)
    jurisdiction: str = Field(min_length=2, max_length=40)
    allowed_content_classes: list[str] = Field(min_length=1)


class CatalogRightsRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBR-[A-Z0-9-]+$")
    publisher_stable_id: str
    scope: Literal["publisher", "source"]
    evidence_locator: HttpUrl
    evidence_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision_status: Literal["pending", "approved", "denied"]
    commercial_use_allowed: bool = False
    storage_allowed: bool = False
    transformation_allowed: bool = False
    translation_allowed: bool = False
    embedding_allowed: bool = False
    excerpt_display_allowed: bool = False
    model_provider_transmission_allowed: bool = False
    redistribution_allowed: bool = False
    prior_version_retention_allowed: bool = False
    attribution_requirements: str | None = None

    @model_validator(mode="after")
    def approved_records_need_required_rights(self) -> CatalogRightsRecord:
        if self.decision_status == "approved" and not all(
            (
                self.commercial_use_allowed,
                self.storage_allowed,
                self.embedding_allowed,
                self.excerpt_display_allowed,
            )
        ):
            raise ValueError("Approved retrieval rights must explicitly allow core product uses.")
        return self


class CatalogTranslation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["zh-Hans", "en"]
    title: str = Field(min_length=1, max_length=500)
    official_locator: HttpUrl


class CatalogDiscoverySource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locator: HttpUrl
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")


class CatalogSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBS-[A-Z0-9-]+$")
    publisher_stable_id: str
    rights_record_stable_id: str
    title: str = Field(min_length=1, max_length=500)
    canonical_locator: HttpUrl
    source_type: str = Field(min_length=2, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=40)
    intended_audiences: list[Literal["doctor", "patient"]] = Field(min_length=1)
    topic: str = Field(min_length=2, max_length=120)
    original_language: Literal["zh-Hans", "en"]
    official_translations: list[CatalogTranslation] = Field(default_factory=list)
    catalog_summary: str = Field(min_length=10, max_length=1000)
    search_keywords: list[str] = Field(min_length=1, max_length=40)
    authority_tier: Literal["A", "B", "C", "D"]
    lifecycle_state: Literal["rights_pending", "doctor_approved", "patient_approved"]
    catalog_visible: bool
    catalog_verified_at: datetime
    metadata_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_official_translations(self) -> CatalogSource:
        languages = {translation.language for translation in self.official_translations}
        if self.original_language in languages:
            raise ValueError("Official translations must not repeat the original language.")
        if len(languages) != len(self.official_translations):
            raise ValueError("Official translation languages must be unique.")
        return self


class KnowledgeCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    generated_at: datetime
    discovery_source_locator: HttpUrl
    discovery_source_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_discovery_source_locator: HttpUrl
    translation_discovery_source_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    supplemental_discovery_sources: list[CatalogDiscoverySource] = Field(default_factory=list)
    publishers: list[CatalogPublisher] = Field(min_length=1)
    rights_records: list[CatalogRightsRecord] = Field(min_length=1)
    sources: list[CatalogSource] = Field(min_length=100)

    @model_validator(mode="after")
    def validate_references_and_uniqueness(self) -> KnowledgeCatalog:
        publisher_ids = [item.stable_id for item in self.publishers]
        rights_ids = [item.stable_id for item in self.rights_records]
        source_ids = [item.stable_id for item in self.sources]
        locators = [str(item.canonical_locator) for item in self.sources]
        for values, label in (
            (publisher_ids, "publisher stable IDs"),
            (rights_ids, "rights stable IDs"),
            (source_ids, "source stable IDs"),
            (locators, "canonical locators"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"Catalog contains duplicate {label}.")
        publisher_id_set = set(publisher_ids)
        rights_by_id = {item.stable_id: item for item in self.rights_records}
        for rights in self.rights_records:
            if rights.publisher_stable_id not in publisher_id_set:
                raise ValueError(f"Unknown publisher in {rights.stable_id}.")
        for source in self.sources:
            rights = rights_by_id.get(source.rights_record_stable_id)
            if source.publisher_stable_id not in publisher_id_set or rights is None:
                raise ValueError(f"Broken publisher or rights reference in {source.stable_id}.")
            if rights.publisher_stable_id != source.publisher_stable_id:
                raise ValueError(f"Rights publisher mismatch in {source.stable_id}.")
            if source.lifecycle_state != "rights_pending" and rights.decision_status != "approved":
                raise ValueError(f"Unapproved rights cannot admit {source.stable_id}.")
        return self


class ImmutableArtifactStore:
    """Content-addressed local adapter for the future immutable COS vault."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def put(self, namespace: str, content: bytes, suffix: str) -> tuple[str, str]:
        checksum = hashlib.sha256(content).hexdigest()
        target = self.root / namespace / checksum[:2] / f"{checksum}.{suffix.lstrip('.')}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != content:
                raise RuntimeError("Immutable artifact checksum collision.")
        else:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            descriptor = os.open(target, flags, 0o440)
            try:
                os.write(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return checksum, target.as_uri()


def load_catalog(path: Path) -> KnowledgeCatalog:
    return KnowledgeCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def import_catalog_metadata(db: Session, catalog: KnowledgeCatalog) -> tuple[int, int, int]:
    """Idempotently import authoritative locators without copying restricted article text."""

    publishers_created = rights_created = sources_created = 0
    publishers: dict[str, KbPublisher] = {}
    for item in catalog.publishers:
        publisher = db.scalar(select(KbPublisher).where(KbPublisher.stable_id == item.stable_id))
        if publisher is None:
            publisher = KbPublisher(
                stable_id=item.stable_id,
                official_name_zh=item.official_name_zh,
                official_name_en=item.official_name_en,
                organization_type=item.organization_type,
                authority_basis=item.authority_basis,
                authority_evidence_locator=str(item.authority_evidence_locator),
                verified_domains_json=item.verified_domains,
                jurisdiction=item.jurisdiction,
                review_status="authority_verified",
                allowed_content_classes_json=item.allowed_content_classes,
                reviewed_at=catalog.generated_at,
            )
            db.add(publisher)
            db.flush()
            publishers_created += 1
        publishers[item.stable_id] = publisher

    rights_records: dict[str, KbRightsRecord] = {}
    for item in catalog.rights_records:
        rights = db.scalar(select(KbRightsRecord).where(KbRightsRecord.stable_id == item.stable_id))
        if rights is None:
            rights = KbRightsRecord(
                stable_id=item.stable_id,
                publisher_id=publishers[item.publisher_stable_id].id,
                scope=item.scope,
                commercial_use_allowed=item.commercial_use_allowed,
                storage_allowed=item.storage_allowed,
                transformation_allowed=item.transformation_allowed,
                translation_allowed=item.translation_allowed,
                embedding_allowed=item.embedding_allowed,
                excerpt_display_allowed=item.excerpt_display_allowed,
                model_provider_transmission_allowed=item.model_provider_transmission_allowed,
                redistribution_allowed=item.redistribution_allowed,
                prior_version_retention_allowed=item.prior_version_retention_allowed,
                attribution_requirements=item.attribution_requirements,
                evidence_checksum=item.evidence_checksum,
                evidence_locator=str(item.evidence_locator),
                decision_status=item.decision_status,
            )
            db.add(rights)
            db.flush()
            rights_created += 1
        rights_records[item.stable_id] = rights

    for item in catalog.sources:
        source = db.scalar(select(KbSource).where(KbSource.stable_id == item.stable_id))
        if source is None:
            source = KbSource(
                stable_id=item.stable_id,
                publisher_id=publishers[item.publisher_stable_id].id,
                rights_record_id=rights_records[item.rights_record_stable_id].id,
                title=item.title,
                canonical_locator=str(item.canonical_locator),
                source_type=item.source_type,
                jurisdiction=item.jurisdiction,
                intended_audiences_json=item.intended_audiences,
                topic=item.topic,
                original_language=item.original_language,
                official_translations_json=[
                    translation.model_dump(mode="json")
                    for translation in item.official_translations
                ],
                catalog_summary=item.catalog_summary,
                search_keywords_json=item.search_keywords,
                authority_tier=item.authority_tier,
                lifecycle_state=item.lifecycle_state,
                medical_review_status="pending",
                native_language_review_status="pending",
                doctor_eligible=False,
                patient_eligible=False,
                catalog_visible=item.catalog_visible,
                status="current",
                discovered_at=catalog.generated_at,
                catalog_verified_at=item.catalog_verified_at,
            )
            db.add(source)
            db.flush()
            sources_created += 1
        existing_version = db.scalar(
            select(KbSourceVersion).where(
                KbSourceVersion.source_id == source.id,
                KbSourceVersion.raw_checksum == item.metadata_checksum,
            )
        )
        if existing_version is not None:
            continue
        translations = [
            translation.model_dump(mode="json") for translation in item.official_translations
        ]
        metadata = json.dumps(
            {
                "title": item.title,
                "locator": str(item.canonical_locator),
                "official_translations": translations,
                "catalog_summary": item.catalog_summary,
                "search_keywords": item.search_keywords,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        previous = db.scalar(
            select(KbSourceVersion)
            .where(KbSourceVersion.source_id == source.id)
            .order_by(KbSourceVersion.captured_at.desc())
            .limit(1)
        )
        if previous is not None:
            previous.valid_to = item.catalog_verified_at
        source.title = item.title
        source.topic = item.topic
        source.official_translations_json = translations
        source.catalog_summary = item.catalog_summary
        source.search_keywords_json = item.search_keywords
        source.catalog_verified_at = item.catalog_verified_at
        source.lifecycle_state = "rights_pending"
        source.doctor_eligible = False
        source.patient_eligible = False
        db.add(
            KbSourceVersion(
                stable_id=(
                    f"KBV-{item.stable_id.removeprefix('KBS-')}-"
                    f"{item.metadata_checksum[:12].upper()}"
                ),
                source_id=source.id,
                captured_at=item.catalog_verified_at,
                capture_mode="metadata_only",
                raw_checksum=item.metadata_checksum,
                normalized_checksum=hashlib.sha256(metadata).hexdigest(),
                parser_version=METADATA_PARSER_VERSION,
                valid_from=item.catalog_verified_at,
                supersedes_version_id=previous.id if previous else None,
                change_summary=(
                    "Updated official-locator metadata capture; no article body stored."
                    if previous
                    else "Initial official-locator metadata capture; no article body stored."
                ),
                review_decision="pending",
            )
        )
    db.flush()
    return publishers_created, rights_created, sources_created


def capture_source_content(
    store: ImmutableArtifactStore,
    rights: KbRightsRecord,
    raw_content: bytes,
    normalized_content: bytes,
) -> tuple[tuple[str, str], tuple[str, str]]:
    if rights.decision_status != "approved" or not rights.storage_allowed:
        raise PermissionError("Raw capture is denied until an approved storage right is recorded.")
    raw = store.put("raw", raw_content, "bin")
    normalized = store.put("normalized", normalized_content, "txt")
    return raw, normalized


def build_index_release(
    db: Session,
    store: ImmutableArtifactStore,
    version_ids: list[uuid.UUID],
    *,
    audience: Literal["doctor", "patient"],
    embedding_model_version: str,
    lexical_analyzer_version: str,
    reranker_version: str,
    approver_ids: list[str],
    passage_embeddings: dict[uuid.UUID, list[float]] | None = None,
    historical_markers: list[dict[str, object]] | None = None,
) -> KbIndexRelease:
    if not version_ids or not approver_ids:
        raise ValueError("An index release needs at least one version and one approver.")
    versions = list(
        db.scalars(
            select(KbSourceVersion)
            .where(KbSourceVersion.id.in_(version_ids))
            .order_by(KbSourceVersion.stable_id)
        )
    )
    if len(versions) != len(set(version_ids)):
        raise ValueError("One or more requested source versions do not exist.")
    approved_terms = [
        {
            "stable_id": term.stable_id,
            "preferred_zh": term.preferred_zh,
            "preferred_en": term.preferred_en,
            "aliases": term.aliases_json,
            "prohibited_expansions": term.prohibited_expansions_json,
        }
        for term in db.scalars(
            select(KbTerm)
            .where(KbTerm.review_status == "approved")
            .order_by(KbTerm.stable_id)
        )
    ]
    manifest_versions: list[dict[str, object]] = []
    manifest_passages: list[dict[str, str | None]] = []
    passage_ids: list[uuid.UUID] = []
    source_ids: set[uuid.UUID] = set()
    source_applicable_jurisdictions: dict[str, list[str]] = {}
    for version in versions:
        source = db.get(KbSource, version.source_id)
        rights = db.get(KbRightsRecord, source.rights_record_id) if source else None
        source_family = (
            db.get(KbSourceFamily, source.source_family_id)
            if source and source.source_family_id
            else None
        )
        eligible = (
            source.patient_eligible
            if audience == "patient" and source
            else source.doctor_eligible
            if source
            else False
        )
        if (
            source is None
            or rights is None
            or (source_family is not None and source_family.status != "active")
            or not eligible
            or source.status != "current"
            or version.review_decision != "approved"
            or rights.decision_status != "approved"
            or not rights.embedding_allowed
            or (audience == "patient" and not provider_transmission_allowed(rights, source))
        ):
            raise ValueError(f"Version {version.stable_id} is not eligible for {audience} release.")
        medical_review = db.scalar(
            select(KbReview).where(
                KbReview.target_stable_id.in_([source.stable_id, version.stable_id]),
                KbReview.review_type == "medical",
                KbReview.decision == "approved",
            )
        )
        native_review = db.scalar(
            select(KbReview).where(
                KbReview.target_stable_id.in_([source.stable_id, version.stable_id]),
                KbReview.review_type == "native_language",
                KbReview.decision == "approved",
            )
        )
        if medical_review is None or (audience == "patient" and native_review is None):
            raise ValueError(f"Version {version.stable_id} is missing required review lineage.")
        jurisdiction_review = db.scalar(
            select(KbReview).where(
                KbReview.target_stable_id.in_([source.stable_id, version.stable_id]),
                KbReview.review_type == "jurisdiction_applicability",
                KbReview.decision == "approved",
            )
        )
        applicable_jurisdictions = ["CN"] if jurisdiction_review is not None else []
        if applicable_jurisdictions:
            source_applicable_jurisdictions[source.stable_id] = applicable_jurisdictions
        source_ids.add(source.id)
        manifest_versions.append(
            {
                "source_id": source.stable_id,
                "version_id": version.stable_id,
                "normalized_checksum": version.normalized_checksum,
                "applicable_jurisdictions": applicable_jurisdictions,
            }
        )
        eligibility = [
            KbPassage.version_id == version.id,
            KbPassage.lexical_eligible.is_(True),
            KbPassage.vector_eligible.is_(True),
        ]
        if passage_embeddings is None:
            eligibility.extend(
                [
                    KbPassage.embedding_json.is_not(None),
                    KbPassage.embedding_model_version == embedding_model_version,
                ]
            )
        passages = list(
            db.scalars(select(KbPassage).where(*eligibility).order_by(KbPassage.stable_id))
        )
        for passage in passages:
            if audience not in passage.audience_json:
                continue
            if audience == "patient" and passage.patient_readability_review_status != "approved":
                continue
            if passage_embeddings is not None and passage.id not in passage_embeddings:
                raise ValueError(f"A release embedding is missing for {passage.stable_id}.")
            passage_ids.append(passage.id)
            manifest_passages.append(
                {
                    "passage_id": passage.stable_id,
                    "content_checksum": passage.content_checksum,
                    "conflict_group_key": passage.conflict_group_key,
                }
            )
    if audience == "patient" and not passage_ids:
        raise ValueError(
            f"No passages use embedding model {embedding_model_version} "
            f"for this {audience} release."
        )
    manifest = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "audience": audience,
        "versions": manifest_versions,
        "passages": manifest_passages,
        "embedding_model_version": embedding_model_version,
        "lexical_analyzer_version": lexical_analyzer_version,
        "reranker_version": reranker_version,
        "terminology": approved_terms,
        "historical_markers": historical_markers or [],
        "provider_transmission_rights_rechecked": audience == "patient",
    }
    payload = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    checksum, locator = store.put("index-releases", payload, "json")
    existing = db.scalar(select(KbIndexRelease).where(KbIndexRelease.manifest_checksum == checksum))
    if existing is not None:
        return existing
    release = KbIndexRelease(
        stable_id=f"KBIR-{checksum[:24].upper()}",
        manifest_checksum=checksum,
        manifest_artifact_locator=locator,
        source_count=len(source_ids),
        version_count=len(versions),
        passage_count=len(passage_ids),
        embedding_model_version=embedding_model_version,
        lexical_analyzer_version=lexical_analyzer_version,
        reranker_version=reranker_version,
        build_results_json={
            "deterministic_manifest": True,
            "audience": audience,
            "terminology": approved_terms,
            "historical_markers": historical_markers or [],
            "source_applicable_jurisdictions": source_applicable_jurisdictions,
            "provider_transmission_rights_rechecked": audience == "patient",
        },
        approver_ids_json=approver_ids,
        status="built",
    )
    db.add(release)
    db.flush()
    db.add_all(
        KbIndexReleasePassage(
            release_id=release.id,
            passage_id=passage_id,
            embedding_json=(
                passage_embeddings[passage_id] if passage_embeddings is not None else None
            ),
            embedding_model_version=(
                embedding_model_version if passage_embeddings is not None else None
            ),
        )
        for passage_id in passage_ids
    )
    return release


def activate_index_release(
    db: Session,
    release: KbIndexRelease,
    *,
    audience: Literal["doctor", "patient"],
    activated_by: str,
) -> None:
    now = datetime.now(UTC)
    active = db.get(KbActiveIndexRelease, audience)
    if active is None:
        active = KbActiveIndexRelease(
            audience=audience,
            release_id=release.id,
            activated_by=activated_by,
            activated_at=now,
        )
        db.add(active)
    else:
        if active.release_id != release.id:
            release.rollback_predecessor_id = active.release_id
        active.release_id = release.id
        active.activated_by = activated_by
        active.activated_at = now
    release.status = "active"
    release.released_at = now
    db.flush()


def rollback_index_release(
    db: Session,
    *,
    audience: Literal["doctor", "patient"],
    activated_by: str,
) -> KbIndexRelease:
    active = db.get(KbActiveIndexRelease, audience)
    current = db.get(KbIndexRelease, active.release_id) if active else None
    predecessor = (
        db.get(KbIndexRelease, current.rollback_predecessor_id)
        if current and current.rollback_predecessor_id
        else None
    )
    if current is None or predecessor is None:
        raise ValueError("The active release has no rollback predecessor.")
    current.status = "rolled_back"
    activate_index_release(db, predecessor, audience=audience, activated_by=activated_by)
    return predecessor
