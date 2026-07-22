from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.knowledge_translation import TranslationCorpusArtifact
from app.open_content_ingestion import OpenContentCatalog

SOURCE_REVIEW_ROLES = (
    "rights",
    "medical",
    "patient_readability",
    "mainland_applicability",
    "product",
)
TRANSLATION_REVIEW_ROLES = (
    "medical",
    "native_zh_hans",
    "patient_readability",
    "mainland_applicability",
    "product",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "approved", "rejected"]
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    findings: str | None = None

    @model_validator(mode="after")
    def validate_named_decision(self) -> ReviewDecision:
        if self.status == "pending":
            if self.reviewer_id is not None or self.reviewed_at is not None:
                raise ValueError("Pending reviews cannot claim a reviewer or review time.")
        elif self.reviewer_id is None or self.reviewed_at is None:
            raise ValueError("Approved and rejected reviews require a reviewer and review time.")
        if self.status == "rejected" and not self.findings:
            raise ValueError("Rejected reviews require findings.")
        return self


class BlockingFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(pattern=r"^KBF-[A-Z0-9-]+$")
    severity: Literal["blocking"]
    status: Literal["open", "resolved"]
    scope: Literal["source", "translation", "patient_use"]
    description: str = Field(min_length=1)
    resolution: str | None = None

    @model_validator(mode="after")
    def validate_resolution(self) -> BlockingFinding:
        if self.status == "resolved" and not self.resolution:
            raise ValueError("Resolved findings require a recorded resolution.")
        if self.status == "open" and self.resolution is not None:
            raise ValueError("Open findings cannot claim a resolution.")
        return self


class CorpusArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locator: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("locator")
    @classmethod
    def validate_workspace_relative_locator(cls, value: str) -> str:
        locator = Path(value)
        if locator.is_absolute() or ".." in locator.parts:
            raise ValueError("Artifact locators must be workspace-relative without traversal.")
        if not locator.parts or locator.parts[0] != "knowledge_base":
            raise ValueError("Artifact locators must remain under knowledge_base.")
        return value


class ReviewSeparationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retrieval_corpus: Literal[True]
    evaluation_contract: Literal[False]
    training_data: Literal[False]
    raw_patient_queries_included: Literal[False]
    activation_allowed_while_pending: Literal[False]
    model_generation_may_close_review: Literal[False]


class SupplementarySourceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^KBS-[A-Z0-9-]+$")
    source_version_id: str = Field(pattern=r"^KBV-[A-Z0-9-]+$")
    source_normalized_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_response_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights_record_stable_id: str = Field(pattern=r"^KBR-[A-Z0-9-]+$")
    rights_state: Literal["license_evidence_captured_review_pending"]
    proposed_presentation_concepts: list[str] = Field(min_length=1)
    known_evidence_limitations: list[str] = Field(min_length=1)
    source_reviews: dict[str, ReviewDecision]
    translation_reviews: dict[str, ReviewDecision]
    blocking_findings: list[BlockingFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_roles(self) -> SupplementarySourceReview:
        if set(self.source_reviews) != set(SOURCE_REVIEW_ROLES):
            raise ValueError("Source review roles do not match the governed role set.")
        if set(self.translation_reviews) != set(TRANSLATION_REVIEW_ROLES):
            raise ValueError("Translation review roles do not match the governed role set.")
        if len(self.proposed_presentation_concepts) != len(
            set(self.proposed_presentation_concepts)
        ):
            raise ValueError("Proposed presentation concepts must be unique.")
        finding_ids = [finding.finding_id for finding in self.blocking_findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("Blocking finding IDs must be unique within a source.")
        return self


class SupplementaryReviewManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    review_id: str = Field(pattern=r"^KBRM-[A-Z0-9-]+$")
    status: Literal["review_pending", "approved_for_admission", "rejected"]
    generated_at: datetime
    source_catalog: CorpusArtifactReference
    translation_artifact: CorpusArtifactReference
    expected_source_count: int = Field(ge=1)
    separation_policy: ReviewSeparationPolicy
    sources: list[SupplementarySourceReview]

    @model_validator(mode="after")
    def validate_manifest_scope(self) -> SupplementaryReviewManifest:
        if len(self.sources) != self.expected_source_count:
            raise ValueError(
                f"Review manifest must contain exactly {self.expected_source_count} sources."
            )
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Review manifest source IDs must be unique.")
        return self


def load_supplementary_review_manifest(path: Path) -> SupplementaryReviewManifest:
    return SupplementaryReviewManifest.model_validate_json(path.read_text(encoding="utf-8"))


def validate_supplementary_review_manifest(
    manifest: SupplementaryReviewManifest,
    *,
    catalog: OpenContentCatalog,
    catalog_path: Path,
    translation: TranslationCorpusArtifact,
    translation_path: Path,
) -> dict[str, object]:
    """Validate lineage separately from named human-review readiness."""

    structural_failures: list[str] = []
    readiness_failures: list[str] = []

    if manifest.source_catalog.locator != catalog_path.as_posix():
        structural_failures.append("source_catalog_locator_mismatch")
    if manifest.source_catalog.sha256 != sha256_file(catalog_path):
        structural_failures.append("source_catalog_checksum_mismatch")
    if manifest.translation_artifact.locator != translation_path.as_posix():
        structural_failures.append("translation_artifact_locator_mismatch")
    if manifest.translation_artifact.sha256 != sha256_file(translation_path):
        structural_failures.append("translation_artifact_checksum_mismatch")
    if translation.source_corpus_locator != manifest.source_catalog.locator:
        structural_failures.append("translation_source_locator_mismatch")
    if translation.source_corpus_checksum != manifest.source_catalog.sha256:
        structural_failures.append("translation_source_checksum_mismatch")

    catalog_documents = {document.stable_id: document for document in catalog.documents}
    catalog_publishers = {publisher.key: publisher for publisher in catalog.publishers}
    translation_documents = {document.source_id: document for document in translation.documents}
    review_sources = {source.source_id: source for source in manifest.sources}
    if set(review_sources) != set(catalog_documents):
        structural_failures.append("review_catalog_source_set_mismatch")
    if set(review_sources) != set(translation_documents):
        structural_failures.append("review_translation_source_set_mismatch")

    for source_id, review in review_sources.items():
        document = catalog_documents.get(source_id)
        translated = translation_documents.get(source_id)
        if document is None or translated is None:
            continue
        expected_version_id = (
            f"KBV-{source_id.removeprefix('KBS-')}-{document.raw_checksum[:12].upper()}"
        )
        if review.source_version_id != expected_version_id:
            structural_failures.append(f"source_version_mismatch:{source_id}")
        if translated.source_version_id != expected_version_id:
            structural_failures.append(f"translation_version_mismatch:{source_id}")
        if review.source_normalized_checksum != document.normalized_checksum:
            structural_failures.append(f"source_checksum_mismatch:{source_id}")
        if translated.source_normalized_checksum != document.normalized_checksum:
            structural_failures.append(f"translation_source_checksum_mismatch:{source_id}")
        if review.translation_response_checksum != translated.response_checksum:
            structural_failures.append(f"translation_checksum_mismatch:{source_id}")
        publisher = catalog_publishers.get(document.publisher_key)
        expected_rights_id = (
            (
                publisher.rights_stable_id
                or publisher.stable_id.replace("KBP-", "KBR-") + "-PUBLIC-DOMAIN"
            )
            if publisher is not None
            else None
        )
        if review.rights_record_stable_id != expected_rights_id:
            structural_failures.append(f"rights_record_mismatch:{source_id}")

        for role, decision in review.source_reviews.items():
            if decision.status != "approved":
                readiness_failures.append(f"source_review_{decision.status}:{source_id}:{role}")
        for role, decision in review.translation_reviews.items():
            if decision.status != "approved":
                readiness_failures.append(
                    f"translation_review_{decision.status}:{source_id}:{role}"
                )
        for finding in review.blocking_findings:
            if finding.status == "open":
                readiness_failures.append(f"blocking_finding_open:{source_id}:{finding.finding_id}")

    structurally_valid = not structural_failures
    human_reviews_complete = not any(
        item.startswith(("source_review_", "translation_review_")) for item in readiness_failures
    )
    blocking_findings_resolved = not any(
        item.startswith("blocking_finding_open:") for item in readiness_failures
    )
    computed_ready = structurally_valid and not readiness_failures
    if computed_ready and manifest.status != "approved_for_admission":
        readiness_failures.append("manifest_status_not_approved_for_admission")
    elif not computed_ready and manifest.status == "approved_for_admission":
        structural_failures.append("manifest_claims_unearned_admission")
        structurally_valid = False

    admission_ready = (
        structurally_valid
        and not readiness_failures
        and manifest.status == "approved_for_admission"
    )

    return {
        "validator_version": "supplementary-review-validator-v1",
        "review_id": manifest.review_id,
        "source_count": len(manifest.sources),
        "structurally_valid": structurally_valid,
        "human_reviews_complete": human_reviews_complete,
        "blocking_findings_resolved": blocking_findings_resolved,
        "admission_ready": admission_ready,
        "candidate_build_allowed": admission_ready,
        "activation_allowed": False,
        "clinical_approval_claimed": admission_ready,
        "structural_failures": structural_failures,
        "readiness_failures": readiness_failures,
    }
