# ruff: noqa: E501
"""Provider-neutral immutable persistence for Clinical Event Intelligence."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


def _id() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class ClinicalEventIntelligenceSnapshot(Base):
    __tablename__ = "clinical_event_intelligence_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "payer_request_id", "snapshot_version", name="uq_cei_snapshot_request_version"
        ),
        Index("ix_cei_snapshot_scope", "clinical_event_id", "created_at"),
        CheckConstraint(
            "snapshot_version > 0 AND payer_request_version > 0", name="ck_cei_snapshot_version"
        ),
        CheckConstraint(
            "service_date_to >= service_date_from", name="ck_cei_snapshot_service_dates"
        ),
        CheckConstraint(
            "snapshot_checksum_sha256 ~ '^[0-9a-f]{64}$'", name="ck_cei_snapshot_checksum"
        ),
    )
    id: Mapped[uuid.UUID] = _id()
    predecessor_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_event_intelligence_snapshots.id", ondelete="RESTRICT")
    )
    payer_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payer_requests.id", ondelete="RESTRICT")
    )
    snapshot_version: Mapped[int] = mapped_column(Integer)
    payer_request_version: Mapped[int] = mapped_column(Integer)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="RESTRICT")
    )
    clinical_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_events.id", ondelete="RESTRICT")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="RESTRICT")
    )
    payer_organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payer_organizations.id", ondelete="RESTRICT")
    )
    hospital_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=True
    )
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="RESTRICT"), nullable=True
    )
    department_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    jurisdiction_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    province: Mapped[str | None] = mapped_column(String(80), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    facility_level: Mapped[str | None] = mapped_column(String(60), nullable=True)
    encounter_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_date_from: Mapped[date] = mapped_column(Date)
    service_date_to: Mapped[date] = mapped_column(Date)
    snapshot_contract_version: Mapped[str] = mapped_column(String(80))
    snapshot_checksum_sha256: Mapped[str] = mapped_column(String(64))
    snapshot_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    source_lineage_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    quality_flags_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceRun(Base):
    __tablename__ = "clinical_event_intelligence_runs"
    __table_args__ = (
        UniqueConstraint(
            "actor_user_id", "payer_request_id", "idempotency_key", name="uq_cei_run_idempotency"
        ),
        UniqueConstraint("snapshot_id", "run_version", name="uq_cei_run_snapshot_version"),
        CheckConstraint("run_version > 0", name="ck_cei_run_version"),
        CheckConstraint("request_checksum_sha256 ~ '^[0-9a-f]{64}$'", name="ck_cei_run_checksum"),
    )
    id: Mapped[uuid.UUID] = _id()
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_snapshots.id", ondelete="RESTRICT")
    )
    predecessor_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    payer_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payer_requests.id", ondelete="RESTRICT")
    )
    run_version: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    request_checksum_sha256: Mapped[str] = mapped_column(String(64))
    purpose_code: Mapped[str] = mapped_column(String(80))
    purpose_contract_version: Mapped[str] = mapped_column(String(80))
    schema_version: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(80))
    model_configuration_version: Mapped[str] = mapped_column(String(80))
    validator_version: Mapped[str] = mapped_column(String(80))
    score_version: Mapped[str] = mapped_column(String(80))
    primary_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("governed_care_releases.id", ondelete="RESTRICT")
    )
    critic_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("governed_care_releases.id", ondelete="RESTRICT")
    )
    lifecycle_state: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceRetrievalSource(Base):
    __tablename__ = "clinical_event_intelligence_retrieval_sources"
    __table_args__ = (
        UniqueConstraint("run_id", "ordinal", name="uq_cei_retrieval_ordinal"),
        CheckConstraint("ordinal >= 0", name="ck_cei_retrieval_ordinal"),
        CheckConstraint("provenance_tier BETWEEN 1 AND 4", name="ck_cei_retrieval_tier"),
    )
    id: Mapped[uuid.UUID] = _id()
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(60))
    governed_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("governed_care_releases.id", ondelete="RESTRICT")
    )
    pricing_reference_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pricing_reference_items.id", ondelete="RESTRICT")
    )
    provenance_tier: Mapped[int] = mapped_column(Integer)
    scope_checksum_sha256: Mapped[str] = mapped_column(String(64))
    lineage_checksum_sha256: Mapped[str] = mapped_column(String(64))
    source_lineage_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligencePathway(Base):
    __tablename__ = "clinical_event_intelligence_pathways"
    __table_args__ = (
        UniqueConstraint("run_id", "pathway_key", name="uq_cei_pathway_key"),
        CheckConstraint(
            "pathway_type IN ('typical_first_line','reasonable_alternative','escalated')",
            name="ck_cei_pathway_type",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 100", name="ck_cei_pathway_confidence"),
        CheckConstraint("length(btrim(usefulness)) > 0", name="ck_cei_pathway_usefulness"),
    )
    id: Mapped[uuid.UUID] = _id()
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    pathway_key: Mapped[str] = mapped_column(String(120))
    pathway_type: Mapped[str] = mapped_column(String(40))
    usefulness: Mapped[str] = mapped_column(Text)
    confidence: Mapped[int] = mapped_column(Integer)
    supporting_facts_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    contradicting_facts_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    missing_information_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    assumptions_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligencePathwayItem(Base):
    __tablename__ = "clinical_event_intelligence_pathway_items"
    __table_args__ = (
        UniqueConstraint("pathway_id", "item_key", name="uq_cei_pathway_item"),
        CheckConstraint(
            "quantity_low >= 0 AND quantity_high >= quantity_low",
            name="ck_cei_pathway_item_quantity",
        ),
        CheckConstraint(
            "cost_low_minor >= 0 AND cost_high_minor >= cost_low_minor",
            name="ck_cei_pathway_item_cost",
        ),
        CheckConstraint("predicted_only", name="ck_cei_pathway_item_predicted"),
    )
    id: Mapped[uuid.UUID] = _id()
    pathway_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_pathways.id", ondelete="RESTRICT")
    )
    item_key: Mapped[str] = mapped_column(String(160))
    label: Mapped[str] = mapped_column(String(240))
    code_system: Mapped[str | None] = mapped_column(String(80))
    service_code: Mapped[str | None] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(80))
    quantity_low: Mapped[int] = mapped_column(Integer)
    quantity_high: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    cost_low_minor: Mapped[int] = mapped_column(Integer)
    cost_high_minor: Mapped[int] = mapped_column(Integer)
    predicted_only: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceProviderAttempt(Base):
    __tablename__ = "clinical_event_intelligence_provider_attempts"
    __table_args__ = (
        UniqueConstraint("run_id", "pass_type", "attempt_number", name="uq_cei_provider_attempt"),
        CheckConstraint("pass_type IN ('primary','critic')", name="ck_cei_attempt_pass"),
        CheckConstraint(
            "attempt_number > 0 AND (pass_type <> 'critic' OR attempt_number = 1)",
            name="ck_cei_attempt_number",
        ),
        CheckConstraint("latency_ms >= 0", name="ck_cei_attempt_latency"),
    )
    id: Mapped[uuid.UUID] = _id()
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    pass_type: Mapped[str] = mapped_column(String(20))
    attempt_number: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(160))
    outcome: Mapped[str] = mapped_column(String(60))
    diagnostic_code: Mapped[str | None] = mapped_column(String(120))
    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_microunits: Mapped[int | None] = mapped_column(Integer)
    output_checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceItemAssessment(Base):
    __tablename__ = "clinical_event_intelligence_item_assessments"
    __table_args__ = (
        UniqueConstraint("run_id", "payer_request_line_id", name="uq_cei_assessment_request_line"),
        CheckConstraint(
            "requested_quantity > 0 AND requested_amount_minor >= 0",
            name="ck_cei_assessment_requested",
        ),
        CheckConstraint(
            "estimated_quantity_low >= 0 AND estimated_quantity_high >= estimated_quantity_low",
            name="ck_cei_assessment_quantity",
        ),
        CheckConstraint(
            "estimated_cost_low_minor >= 0 AND estimated_cost_high_minor >= estimated_cost_low_minor",
            name="ck_cei_assessment_cost",
        ),
        CheckConstraint(
            "clinical_fit BETWEEN 0 AND 100 AND evidence_support BETWEEN 0 AND 100 AND timing_sequence BETWEEN 0 AND 100 AND quantity_intensity BETWEEN 0 AND 100 AND documentation_completeness BETWEEN 0 AND 100 AND cost_alignment BETWEEN 0 AND 100 AND ai_support_score BETWEEN 0 AND 100 AND confidence BETWEEN 0 AND 100",
            name="ck_cei_assessment_scores",
        ),
        CheckConstraint(
            "cost_alignment_weight_bp BETWEEN 0 AND 10000", name="ck_cei_assessment_weight"
        ),
        CheckConstraint("provenance_tier BETWEEN 1 AND 5", name="ck_cei_assessment_tier"),
        CheckConstraint(
            "(provenance_tier = 5 AND exploratory AND wide_uncertainty AND retrieval_source_id IS NULL AND cost_alignment_weight_bp = 0) OR (provenance_tier < 5 AND NOT exploratory AND retrieval_source_id IS NOT NULL)",
            name="ck_cei_assessment_provenance",
        ),
        CheckConstraint("length(btrim(usefulness)) > 0", name="ck_cei_assessment_usefulness"),
        CheckConstraint(
            "disagreement_state IN ('agreement','partial_disagreement','material_disagreement','unavailable')",
            name="ck_cei_assessment_disagreement",
        ),
    )
    id: Mapped[uuid.UUID] = _id()
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    payer_request_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payer_request_lines.id", ondelete="RESTRICT")
    )
    retrieval_source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_event_intelligence_retrieval_sources.id", ondelete="RESTRICT")
    )
    requested_label: Mapped[str] = mapped_column(String(240))
    requested_code: Mapped[str | None] = mapped_column(String(120))
    requested_quantity: Mapped[int] = mapped_column(Integer)
    requested_unit: Mapped[str] = mapped_column(String(80))
    requested_amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    estimated_quantity_low: Mapped[int] = mapped_column(Integer)
    estimated_quantity_high: Mapped[int] = mapped_column(Integer)
    estimated_cost_low_minor: Mapped[int] = mapped_column(Integer)
    estimated_cost_high_minor: Mapped[int] = mapped_column(Integer)
    clinical_fit: Mapped[int] = mapped_column(Integer)
    evidence_support: Mapped[int] = mapped_column(Integer)
    timing_sequence: Mapped[int] = mapped_column(Integer)
    quantity_intensity: Mapped[int] = mapped_column(Integer)
    documentation_completeness: Mapped[int] = mapped_column(Integer)
    cost_alignment: Mapped[int] = mapped_column(Integer)
    cost_alignment_weight_bp: Mapped[int] = mapped_column(Integer)
    ai_support_score: Mapped[int] = mapped_column(Integer)
    support_band: Mapped[str] = mapped_column(String(80))
    score_version: Mapped[str] = mapped_column(String(80))
    provenance_tier: Mapped[int] = mapped_column(Integer)
    exploratory: Mapped[bool] = mapped_column(Boolean, default=False)
    wide_uncertainty: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[int] = mapped_column(Integer)
    usefulness: Mapped[str] = mapped_column(Text)
    mapped_pathways_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    supporting_facts_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    contradicting_facts_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    missing_information_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    alternatives_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    source_lineage_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    brief_comments_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    validation_results_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    disagreement_state: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceArtifact(Base):
    __tablename__ = "clinical_event_intelligence_artifacts"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_cei_artifact_run"),
        UniqueConstraint(
            "payer_request_id", "artifact_version", name="uq_cei_artifact_request_version"
        ),
        CheckConstraint("artifact_version > 0", name="ck_cei_artifact_version"),
        CheckConstraint(
            "disagreement_state IN ('agreement','partial_disagreement','material_disagreement','unavailable')",
            name="ck_cei_artifact_disagreement",
        ),
    )
    id: Mapped[uuid.UUID] = _id()
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_runs.id", ondelete="RESTRICT")
    )
    predecessor_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_event_intelligence_artifacts.id", ondelete="RESTRICT")
    )
    payer_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payer_requests.id", ondelete="RESTRICT")
    )
    artifact_version: Mapped[int] = mapped_column(Integer)
    lifecycle_state: Mapped[str] = mapped_column(String(60))
    requested_set_checksum_sha256: Mapped[str] = mapped_column(String(64))
    snapshot_checksum_sha256: Mapped[str] = mapped_column(String(64))
    result_checksum_sha256: Mapped[str] = mapped_column(String(64))
    configuration_checksum_sha256: Mapped[str] = mapped_column(String(64))
    reconciliation_checksum_sha256: Mapped[str] = mapped_column(String(64))
    disagreement_state: Mapped[str] = mapped_column(String(40))
    artifact_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    validation_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceExplanation(Base):
    __tablename__ = "clinical_event_intelligence_explanations"
    __table_args__ = (
        UniqueConstraint(
            "artifact_id",
            "role",
            "locale",
            "version",
            name="uq_cei_explanation_role_locale_version",
        ),
        CheckConstraint("role IN ('patient','doctor','payer')", name="ck_cei_explanation_role"),
        CheckConstraint("locale IN ('en','zh-Hans')", name="ck_cei_explanation_locale"),
    )
    id: Mapped[uuid.UUID] = _id()
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_artifacts.id", ondelete="RESTRICT")
    )
    purpose_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("governed_care_releases.id", ondelete="RESTRICT"), nullable=True
    )
    role: Mapped[str] = mapped_column(String(20))
    locale: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer)
    display_mode: Mapped[str] = mapped_column(String(40))
    fact_checksum_sha256: Mapped[str] = mapped_column(String(64))
    display_checksum_sha256: Mapped[str] = mapped_column(String(64))
    validation_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    display_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()


class ClinicalEventIntelligenceLineageEvent(Base):
    __tablename__ = "clinical_event_intelligence_lineage_events"
    __table_args__ = (
        UniqueConstraint("artifact_id", "source_event_key", name="uq_cei_lineage_source"),
        CheckConstraint(
            "NOT (doctor_response_id IS NOT NULL AND payer_review_id IS NOT NULL)",
            name="ck_cei_lineage_single_source",
        ),
    )
    id: Mapped[uuid.UUID] = _id()
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_event_intelligence_artifacts.id", ondelete="RESTRICT")
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    doctor_response_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payer_doctor_responses.id", ondelete="RESTRICT")
    )
    payer_review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payer_reviews.id", ondelete="RESTRICT")
    )
    event_type: Mapped[str] = mapped_column(String(60))
    source_event_key: Mapped[str] = mapped_column(String(160))
    source_checksum_sha256: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _created()
