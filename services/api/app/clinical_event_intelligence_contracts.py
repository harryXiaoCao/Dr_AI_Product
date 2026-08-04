"""Strict provider-neutral contracts for Clinical Event Intelligence."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CEI_PURPOSE_CODE = "clinical_event_intelligence_primary"
CEI_PURPOSE_CONTRACT_VERSION = "clinical-event-intelligence-primary.v1"
CEI_OUTPUT_SCHEMA_VERSION = "clinical-event-intelligence-output.v1"
CEI_PROMPT_VERSION = "clinical-event-intelligence-primary-prompt.v1"
CEI_VALIDATOR_VERSION = "clinical-event-intelligence-validator.v1"
CEI_SCORE_CONTRACT_VERSION = "clinical-event-intelligence-score.v1"
CEI_RECONCILIATION_VERSION = "clinical-event-intelligence-reconciliation.v1"
CEI_MODEL_CONFIGURATION_VERSION = "clinical-event-intelligence-deepseek.v1"
CEI_CRITIC_PURPOSE_CODE = "clinical_event_intelligence_critic"
CEI_CRITIC_PURPOSE_CONTRACT_VERSION = "clinical-event-intelligence-critic.v1"
CEI_CRITIC_SCHEMA_VERSION = "clinical-event-intelligence-critic.v1"
CEI_CRITIC_PROMPT_VERSION = "clinical-event-intelligence-critic-prompt.v1"
CEI_CRITIC_VALIDATOR_VERSION = "clinical-event-intelligence-critic-validator.v1"
CEI_EXPLANATION_PURPOSE_CODE = "clinical_event_intelligence_role_explanation"
CEI_EXPLANATION_PURPOSE_CONTRACT_VERSION = "clinical-event-intelligence-role-explanation.v1"
CEI_EXPLANATION_SCHEMA_VERSION = "clinical-event-intelligence-explanation.v1"
CEI_EXPLANATION_PROMPT_VERSION = "clinical-event-intelligence-role-explanation-prompt.v1"
CEI_EXPLANATION_MODEL_CONFIGURATION_VERSION = (
    "clinical-event-intelligence-role-explanation-deepseek.v1"
)
CEI_EXPLANATION_VALIDATOR_VERSION = "clinical-event-intelligence-role-explanation-validator.v1"


def canonical_checksum(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        ).encode()
    ).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


NonEmptyText = Annotated[str, Field(min_length=1, max_length=500)]
FactId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.:-]{2,159}$")]
Score = Annotated[int, Field(ge=0, le=100)]


class FrozenLocation(StrictModel):
    jurisdiction_code: NonEmptyText | None
    province_code: NonEmptyText | None
    city_code: NonEmptyText | None
    facility_level: NonEmptyText | None
    hospital_id: str | None = None
    clinic_id: str | None = None
    department: str | None = None
    source: Literal[
        "clinical_event",
        "clinical_service_facility",
        "provider_organization",
        "conflicting_structured_records",
        "missing_structured_records",
    ]
    complete: bool


class FrozenFact(StrictModel):
    fact_id: FactId
    category: NonEmptyText
    value: object
    source_type: NonEmptyText
    source_id: NonEmptyText
    verification_state: Literal["verified", "unverified", "stale", "conflicting"]


class FrozenRequestedLine(StrictModel):
    requested_line_id: NonEmptyText
    item_type: NonEmptyText
    label: NonEmptyText
    code_system: NonEmptyText | None
    service_code: NonEmptyText | None
    quantity: Annotated[int, Field(ge=1)]
    unit: NonEmptyText
    requested_minor: Annotated[int, Field(ge=0)]
    actual_cost_minor: Annotated[int, Field(ge=0)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    service_date: str


class FrozenClinicalEventSnapshot(StrictModel):
    snapshot_version: Literal[1] = 1
    payer_request_version: Annotated[int, Field(ge=1)]
    patient_id: NonEmptyText
    clinical_event_id: NonEmptyText
    payer_request_id: NonEmptyText
    encounter_date: str | None
    location: FrozenLocation
    facts_used: list[FrozenFact]
    facts_not_used: list[FrozenFact]
    missing_information: list[NonEmptyText]
    conflicting_information: list[NonEmptyText]
    requested_lines: Annotated[list[FrozenRequestedLine], Field(min_length=1)]
    requested_item_set_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    snapshot_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class RetrievalSource(StrictModel):
    source_id: NonEmptyText
    source_type: Literal[
        "facility_price",
        "payer_price",
        "regional_reference",
        "code_catalog",
        "guideline",
        "care_pathway",
        "payer_policy",
        "comparable_case",
    ]
    release_id: str | None
    release_version: str | None
    checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    authority: NonEmptyText
    provider_transmission_allowed: bool
    payload: dict[str, object]


class RetrievalManifest(StrictModel):
    retrieval_contract_version: Literal["clinical-event-intelligence-retrieval.v1"]
    authorization_scope_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    sources: list[RetrievalSource]
    missing_source_types: list[NonEmptyText]
    manifest_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ProposedPathwayItem(StrictModel):
    item_key: NonEmptyText
    label: NonEmptyText
    category: NonEmptyText
    service_code: str | None
    quantity_low: Annotated[int, Field(ge=1)]
    quantity_high: Annotated[int, Field(ge=1)]
    unit: NonEmptyText
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    cost_low_minor: Annotated[int, Field(ge=0)]
    cost_high_minor: Annotated[int, Field(ge=0)]
    rationale_fact_ids: list[FactId]

    @model_validator(mode="after")
    def valid_quantity_range(self) -> ProposedPathwayItem:
        if self.quantity_high < self.quantity_low or self.cost_high_minor < self.cost_low_minor:
            raise ValueError("pathway quantity range is reversed")
        return self


class ProposedPathway(StrictModel):
    pathway_id: NonEmptyText
    pathway_type: Literal["typical_first_line", "reasonable_alternative", "escalated"]
    trigger_fact_ids: list[FactId]
    usefulness: NonEmptyText
    confidence: Score
    assumptions: list[NonEmptyText]
    limitations: list[NonEmptyText]
    items: Annotated[list[ProposedPathwayItem], Field(min_length=1)]


class ScoreDimensions(StrictModel):
    clinical_fit: Score
    evidence_support: Score
    timing_sequence: Score
    quantity_intensity: Score
    documentation_completeness: Score
    cost_alignment: Score


class ProposedCostEstimate(StrictModel):
    low_minor: Annotated[int, Field(ge=0)]
    high_minor: Annotated[int, Field(ge=0)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    provenance_tier: Literal[1, 2, 3, 4, 5]
    source_ids: list[NonEmptyText]
    is_model_only_exploratory: bool

    @model_validator(mode="after")
    def valid_cost_range(self) -> ProposedCostEstimate:
        if self.high_minor < self.low_minor:
            raise ValueError("cost range is reversed")
        return self


class ProposedQuantityEstimate(StrictModel):
    low: Annotated[int, Field(ge=1)]
    high: Annotated[int, Field(ge=1)]
    unit: NonEmptyText

    @model_validator(mode="after")
    def valid_quantity_range(self) -> ProposedQuantityEstimate:
        if self.high < self.low:
            raise ValueError("quantity range is reversed")
        return self


class RequestedItemProposal(StrictModel):
    requested_line_id: NonEmptyText
    usefulness: NonEmptyText
    mapped_pathway_ids: list[NonEmptyText]
    scores: ScoreDimensions
    estimated_quantity: ProposedQuantityEstimate
    estimated_cost: ProposedCostEstimate
    supporting_fact_ids: list[FactId]
    contradicting_fact_ids: list[FactId]
    missing_information: list[NonEmptyText]
    alternatives: list[NonEmptyText]
    confidence: Literal["low", "moderate", "high"]
    brief_comment: NonEmptyText


class PrimaryIntelligenceOutput(StrictModel):
    purpose_code: Literal["clinical_event_intelligence_primary"]
    purpose_contract_version: Literal["clinical-event-intelligence-primary.v1"]
    schema_version: Literal["clinical-event-intelligence-output.v1"]
    snapshot_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    retrieval_manifest_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    pathways: Annotated[list[ProposedPathway], Field(min_length=1, max_length=12)]
    requested_item_assessments: Annotated[list[RequestedItemProposal], Field(min_length=1)]
    unresolved_questions: list[NonEmptyText]
    overall_confidence: Literal["low", "moderate", "high"]


class CriticDiscrepancy(StrictModel):
    requested_line_id: str | None
    category: Literal[
        "unsupported_fact",
        "pathway_mapping",
        "score_dimension",
        "quantity_range",
        "cost_range",
        "provenance",
        "missing_information",
        "prohibited_conclusion",
    ]
    severity: Literal["minor", "material"]
    fact_ids: list[FactId]
    concise_comment: NonEmptyText


class CriticOutput(StrictModel):
    purpose_code: Literal["clinical_event_intelligence_critic"]
    schema_version: Literal["clinical-event-intelligence-critic.v1"]
    snapshot_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    primary_output_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    discrepancies: list[CriticDiscrepancy]


class ValidatedRequestedItem(StrictModel):
    proposal: RequestedItemProposal
    ai_support_score: Score
    score_band: Literal[
        "strongly_supported",
        "plausible",
        "materially_uncertain",
        "weakly_supported_human_review",
    ]
    score_contract_version: Literal["clinical-event-intelligence-score.v1"]
    cost_alignment_weight_bp: Literal[0, 1000]
    validation_results: list[NonEmptyText]


class ValidatedIntelligence(StrictModel):
    primary: PrimaryIntelligenceOutput
    assessments: list[ValidatedRequestedItem]
    validation_results: list[NonEmptyText]
    output_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class RoleExplanationPlan(StrictModel):
    purpose_code: Literal["clinical_event_intelligence_role_explanation"]
    schema_version: Literal["clinical-event-intelligence-explanation.v1"]
    fact_object_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    selected_fact_ids: Annotated[list[FactId], Field(min_length=1, max_length=80)]
    emphasis: Literal["purpose", "uncertainty", "missing_information", "human_review"]
