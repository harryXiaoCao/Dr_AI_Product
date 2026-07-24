from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AuthorityTier(StrEnum):
    a = "A"
    b = "B"
    c = "C"
    d = "D"


class KnowledgeAudience(StrEnum):
    doctor = "doctor"
    patient = "patient"


class SourceLifecycleState(StrEnum):
    discovered = "discovered"
    publisher_verified = "publisher_verified"
    rights_pending = "rights_pending"
    captured_and_hashed = "captured_and_hashed"
    parsed = "parsed"
    medical_and_language_review = "medical_and_language_review"
    doctor_approved = "doctor_approved"
    patient_approved = "patient_approved"
    indexed_in_immutable_release = "indexed_in_immutable_release"
    monitored = "monitored"
    superseded = "superseded"
    withdrawn = "withdrawn"
    expired = "expired"
    quarantined = "quarantined"


class SourceStatus(StrEnum):
    current = "current"
    superseded = "superseded"


class EvidenceDecision(StrEnum):
    sufficient = "sufficient"
    no_eligible_evidence = "no_eligible_evidence"
    conflicting = "conflicting"
    stale_or_superseded_only = "stale_or_superseded_only"


class GroundingMode(StrEnum):
    approved_evidence = "approved_evidence"
    general_model_knowledge = "general_model_knowledge"
    fixed_safety_response = "fixed_safety_response"


class SafetyCode(StrEnum):
    permitted_education = "permitted_education"
    permitted_symptom_guidance = "permitted_symptom_guidance"
    emergency = "emergency"
    prohibited_diagnosis = "prohibited_diagnosis"
    prohibited_medication_change = "prohibited_medication_change"
    prompt_attack = "prompt_attack"
    unsupported_input = "unsupported_input"


class FallbackCode(StrEnum):
    emergency = "emergency"
    prohibited_request = "prohibited_request"
    authorization_denied = "authorization_denied"
    no_eligible_evidence = "no_eligible_evidence"
    conflicting_evidence = "conflicting_evidence"
    stale_evidence = "stale_evidence"
    retrieval_unavailable = "retrieval_unavailable"
    provider_timeout = "provider_timeout"
    provider_quota = "provider_quota"
    provider_unavailable = "provider_unavailable"
    malformed_model_output = "malformed_model_output"
    unsupported_citation = "unsupported_citation"
    policy_validation_failed = "policy_validation_failed"
    network_interrupted = "network_interrupted"


class NextActionCode(StrEnum):
    none = "none"
    contact_connected_doctor = "contact_connected_doctor"
    seek_local_care = "seek_local_care"
    call_120 = "call_120"
    ask_clarifying_question = "ask_clarifying_question"
    review_measurement_guidance = "review_measurement_guidance"
    track_measurements = "track_measurements"
    prepare_doctor_questions = "prepare_doctor_questions"
    prepare_symptom_summary = "prepare_symptom_summary"


class PatientContextCategory(StrEnum):
    profile = "profile"
    measurements = "measurements"
    conditions = "conditions"
    medications = "medications"
    clinical_events = "clinical_events"
    recovery_plan = "recovery_plan"


class PatientContextProvenance(StrEnum):
    patient_profile = "patient_profile"
    patient_reported = "patient_reported"
    doctor_record = "doctor_record"
    current_prescription = "current_prescription"
    medication_schedule = "medication_schedule"
    recovery_plan = "recovery_plan"


class RefusalCode(StrEnum):
    diagnosis = "diagnosis"
    medication_change = "medication_change"
    emergency = "emergency"
    unsupported = "unsupported"


class SourceAdmissionContract(BaseModel):
    """Admission decision shared by ingestion and retrieval; not a database entity."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=160)
    authority_tier: AuthorityTier
    organization_allowlisted: bool
    authority_evidence_verified: bool
    commercial_use_allowed: bool
    storage_allowed: bool
    transformation_allowed: bool
    embedding_allowed: bool
    excerpt_display_allowed: bool
    model_provider_transmission_allowed: bool
    medical_review_approved: bool
    native_language_review_approved: bool
    lifecycle_state: SourceLifecycleState
    audiences: set[KnowledgeAudience] = Field(min_length=1)
    rights_record_id: str = Field(min_length=1, max_length=160)
    review_record_ids: list[str] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def enforce_admission_policy(self) -> "SourceAdmissionContract":
        if not self.organization_allowlisted or not self.authority_evidence_verified:
            raise ValueError("Source organization and authority evidence must be verified.")
        if not all(
            (
                self.commercial_use_allowed,
                self.storage_allowed,
                self.embedding_allowed,
                self.excerpt_display_allowed,
                self.medical_review_approved,
            )
        ):
            raise ValueError("Admitted sources require explicit rights and medical approval.")
        approved_states = {
            SourceLifecycleState.doctor_approved,
            SourceLifecycleState.patient_approved,
            SourceLifecycleState.indexed_in_immutable_release,
            SourceLifecycleState.monitored,
        }
        if self.lifecycle_state not in approved_states:
            raise ValueError("Only approved source lifecycle states may enter retrieval.")
        if KnowledgeAudience.patient in self.audiences:
            if not self.native_language_review_approved:
                raise ValueError("Patient evidence requires native-language review.")
            if self.lifecycle_state == SourceLifecycleState.doctor_approved:
                raise ValueError("Doctor approval alone does not admit patient evidence.")
        return self


class DoctorResourceSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    topics: list[str] = Field(default_factory=list, max_length=12)
    document_types: list[str] = Field(default_factory=list, max_length=12)
    organization_ids: list[str] = Field(default_factory=list, max_length=12)
    jurisdictions: list[str] = Field(default_factory=lambda: ["CN"], max_length=8)
    languages: list[Literal["zh-Hans", "en"]] = Field(default_factory=list, max_length=2)
    published_from: date | None = None
    published_to: date | None = None
    status: SourceStatus = SourceStatus.current

    @model_validator(mode="after")
    def validate_date_range(self) -> "DoctorResourceSearchFilters":
        if self.published_from and self.published_to and self.published_from > self.published_to:
            raise ValueError("published_from cannot be after published_to")
        return self


class DoctorResourceSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=2, max_length=300)
    filters: DoctorResourceSearchFilters = Field(default_factory=DoctorResourceSearchFilters)
    cursor: str | None = Field(default=None, max_length=512)
    limit: int = Field(default=20, ge=1, le=50)


class SourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    version_id: str
    passage_ids: list[str] = Field(min_length=1, max_length=8)
    title: str
    publisher: str
    official_locator: str
    jurisdiction: str
    original_language: Literal["zh-Hans", "en"]
    publication_date: date | None
    last_medical_review_date: date
    authority_tier: AuthorityTier
    status: SourceStatus
    patient_use_approved: bool


class DoctorResourceSearchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation: SourceCitation
    matched_passage: str
    matched_terms: list[str] = Field(default_factory=list, max_length=20)


class DoctorResourceSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    original_query: str
    expanded_terms: list[str] = Field(default_factory=list, max_length=20)
    evidence_decision: EvidenceDecision
    items: list[DoctorResourceSearchItem]
    next_cursor: str | None = None
    index_release_id: str


class PatientEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=2, max_length=300)
    language: Literal["zh-Hans", "en"] = "zh-Hans"
    jurisdiction: Literal["CN"] = "CN"
    topics: list[str] = Field(default_factory=list, max_length=8)
    excluded_content_types: list[str] = Field(default_factory=list, max_length=12)
    top_k: int = Field(default=6, ge=1, le=8)


class EvidencePassage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passage_id: str
    source_id: str
    version_id: str
    text: str
    language: Literal["zh-Hans", "en"]
    citation: SourceCitation


class PatientEvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    decision: EvidenceDecision
    passages: list[EvidencePassage] = Field(max_length=8)
    index_release_id: str

    @model_validator(mode="after")
    def require_evidence_only_for_sufficient_decision(self) -> "PatientEvidenceResponse":
        if self.decision == EvidenceDecision.sufficient and not self.passages:
            raise ValueError("Sufficient evidence requires at least one passage.")
        if self.decision != EvidenceDecision.sufficient and self.passages:
            raise ValueError("Failed evidence gates must not release passages.")
        if any(not passage.citation.patient_use_approved for passage in self.passages):
            raise ValueError("Patient retrieval may return only patient-approved sources.")
        return self


class ModelAnswerSection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=1200)
    supporting_passage_ids: list[str] = Field(min_length=1, max_length=8)
    supporting_context_ids: list[str] = Field(default_factory=list, max_length=8)


class PatientContextItem(BaseModel):
    """A bounded, question-selected record fragment sent to the model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    context_id: str = Field(min_length=1, max_length=160)
    category: PatientContextCategory
    field_name: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=500)
    provenance: PatientContextProvenance
    attribution_phrase: str = Field(min_length=1, max_length=120)
    recorded_on: date
    resource_id: str = Field(min_length=1, max_length=80)


class PatientContextBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PatientContextItem] = Field(default_factory=list, max_length=16)


class StructuredModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_language: Literal["zh-Hans", "en"]
    answer_sections: list[ModelAnswerSection] = Field(min_length=1, max_length=6)
    uses_patient_context: bool
    patient_context_attribution: str | None = Field(default=None, max_length=240)
    used_patient_context_ids: list[str] = Field(default_factory=list, max_length=8)
    uncertainties: list[str] = Field(default_factory=list, max_length=8)
    next_action_code: NextActionCode = NextActionCode.none
    refusal_code: RefusalCode | None = None

    @model_validator(mode="after")
    def require_context_attribution(self) -> "StructuredModelOutput":
        has_attribution = self.patient_context_attribution is not None
        has_context_ids = bool(self.used_patient_context_ids)
        if (
            self.uses_patient_context != has_attribution
            or self.uses_patient_context != has_context_ids
        ):
            raise ValueError("Patient-context use, attribution, and context IDs must agree.")
        section_context_ids = {
            context_id
            for section in self.answer_sections
            for context_id in section.supporting_context_ids
        }
        if section_context_ids != set(self.used_patient_context_ids):
            raise ValueError("Used patient-context IDs must match answer-section context IDs.")
        return self


class GeneralModelOutput(BaseModel):
    """Citation-free output for the separately governed model-knowledge mode."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer_language: Literal["zh-Hans", "en"]
    answer_sections: list[str] = Field(min_length=1, max_length=5)
    uncertainties: list[str] = Field(default_factory=list, max_length=8)
    next_action_code: NextActionCode = NextActionCode.none
    declined_portion: str | None = Field(default=None, max_length=500)


class PatientChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=2, max_length=800)
    language: Literal["zh-Hans", "en"] = "zh-Hans"
    session_id: str | None = Field(default=None, min_length=8, max_length=120)


class RetrievalQueryPlan(BaseModel):
    """Bounded query understanding only; it cannot direct safety or evidence selection."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    normalized_intent: str = Field(min_length=1, max_length=120)
    concepts: list[str] = Field(min_length=1, max_length=8)
    synonyms: list[str] = Field(default_factory=list, max_length=12)
    language: Literal["zh-Hans", "en"]
    jurisdiction: Literal["CN"] = "CN"
    ambiguity_reason: str | None = Field(default=None, max_length=240)
    excluded_content_classes: list[
        Literal[
            "clinical_guideline_doctor_only",
            "raw_clinical_record",
            "prescriber_only_medicine_content",
        ]
    ] = Field(default_factory=list, max_length=3)
    candidate_queries: list[str] = Field(min_length=1, max_length=2)
    clarification_needed: bool = False

    @field_validator("concepts", "synonyms")
    @classmethod
    def bounded_terms(cls, values: list[str]) -> list[str]:
        if any(not value or len(value) > 80 for value in values):
            raise ValueError("Planner concepts and synonyms must be short non-empty strings.")
        return list(dict.fromkeys(values))

    @field_validator("candidate_queries")
    @classmethod
    def bounded_queries(cls, values: list[str]) -> list[str]:
        if any(len(value) < 2 or len(value) > 300 for value in values):
            raise ValueError("Candidate queries must contain 2 to 300 characters.")
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def require_ambiguity_reason_for_clarification(self) -> "RetrievalQueryPlan":
        if self.clarification_needed != bool(self.ambiguity_reason):
            raise ValueError("clarification_needed and ambiguity_reason must be present together.")
        return self


class PatientChatSourceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1, le=8)
    passage_id: str
    title: str
    publisher: str
    publication_date: date | None
    last_medical_review_date: date
    official_locator: str


class PatientChatContextCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: PatientContextCategory
    provenance: PatientContextProvenance
    recorded_on: date


class PatientChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grounding_mode: GroundingMode = GroundingMode.fixed_safety_response
    request_id: str
    session_id: str
    answer_language: Literal["zh-Hans", "en"]
    answer_sections: list[str] = Field(min_length=1, max_length=6)
    sources: list[PatientChatSourceCard] = Field(default_factory=list, max_length=8)
    context_used: list[PatientChatContextCard] = Field(default_factory=list, max_length=6)
    uncertainties: list[str] = Field(default_factory=list, max_length=8)
    limitation: str
    next_action_code: NextActionCode
    safety_code: SafetyCode
    urgency_route: (
        Literal[
            "emergency_120",
            "urgent_same_day",
            "clinician_contact",
            "routine_education",
            "prohibited_medication_change",
        ]
        | None
    ) = None
    evidence_decision: EvidenceDecision | None = None
    fallback_code: FallbackCode | None = None
    model_version: str | None = None
    emergency: bool = False
    suggested_action_codes: list[NextActionCode] = Field(default_factory=list, max_length=4)
    follow_up_question: str | None = Field(default=None, max_length=240)

    @model_validator(mode="before")
    @classmethod
    def infer_historical_grounding_mode(cls, data: object) -> object:
        if not isinstance(data, dict) or data.get("grounding_mode") is not None:
            return data
        migrated = dict(data)
        migrated["grounding_mode"] = (
            GroundingMode.approved_evidence
            if migrated.get("sources")
            else GroundingMode.fixed_safety_response
        )
        return migrated

    @model_validator(mode="after")
    def enforce_grounding_mode_contract(self) -> "PatientChatResponse":
        if self.grounding_mode == GroundingMode.approved_evidence and not self.sources:
            raise ValueError("Approved-evidence responses require real source cards.")
        if self.grounding_mode != GroundingMode.approved_evidence and self.sources:
            raise ValueError("Only approved-evidence responses may contain source cards.")
        if self.grounding_mode == GroundingMode.general_model_knowledge:
            if self.context_used:
                raise ValueError("General-model-knowledge responses cannot use patient context.")
            if self.fallback_code is not None:
                raise ValueError("Generated general knowledge is not a fixed fallback.")
        return self


class PatientChatThreadSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: UUID
    title: str
    created_at: datetime
    last_message_at: datetime
    retention_until: datetime


class PatientChatThreadList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PatientChatThreadSummary]


class PatientChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    response: PatientChatResponse | None = None


class PatientChatHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread: PatientChatThreadSummary
    messages: list[PatientChatHistoryMessage]


class ToolContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchMedicalKnowledgeTool(ToolContract):
    tool: Literal["search_medical_knowledge"]
    query: str = Field(min_length=2, max_length=300)
    filters: DoctorResourceSearchFilters
    top_k: int = Field(default=6, ge=1, le=8)


class ReadKnowledgePassagesTool(ToolContract):
    tool: Literal["read_knowledge_passages"]
    source_ids: list[str] = Field(min_length=1, max_length=4)
    passage_ids: list[str] = Field(min_length=1, max_length=8)


class ReadSelectedCareContextTool(ToolContract):
    tool: Literal["read_selected_care_context"]
    context_type: Literal["clinical_event", "recovery_plan", "prescription"]
    resource_id: str
    fields: list[str] = Field(min_length=1, max_length=8)


class PrepareQuestionForDoctorTool(ToolContract):
    tool: Literal["prepare_question_for_doctor"]
    patient_text: str = Field(min_length=2, max_length=300)


class OpenConnectedDoctorFlowTool(ToolContract):
    tool: Literal["open_connected_doctor_flow"]


class ShowEmergencyGuidanceTool(ToolContract):
    tool: Literal["show_emergency_guidance"]
    rule_id: str = Field(min_length=1, max_length=120)


class SearchDoctorResourcesTool(ToolContract):
    tool: Literal["search_doctor_resources"]
    request: DoctorResourceSearchRequest


class ReadSourceRecordTool(ToolContract):
    tool: Literal["read_source_record"]
    source_id: str
    version_id: str


class ListSourceVersionsTool(ToolContract):
    tool: Literal["list_source_versions"]
    source_id: str


class ListRelatedSourcesTool(ToolContract):
    tool: Literal["list_related_sources"]
    source_id: str


class SaveSourceReferenceTool(ToolContract):
    tool: Literal["save_source_reference"]
    source_id: str
    collection_id: str


ChatbotToolCall = Annotated[
    SearchMedicalKnowledgeTool
    | ReadKnowledgePassagesTool
    | ReadSelectedCareContextTool
    | PrepareQuestionForDoctorTool
    | OpenConnectedDoctorFlowTool
    | ShowEmergencyGuidanceTool
    | SearchDoctorResourcesTool
    | ReadSourceRecordTool
    | ListSourceVersionsTool
    | ListRelatedSourcesTool
    | SaveSourceReferenceTool,
    Field(discriminator="tool"),
]


class ChatbotTelemetryEvent(BaseModel):
    """Content-free operational event. Unknown/raw-content fields fail validation."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    actor_role: Literal["doctor", "patient"]
    workflow: Literal["doctor_resource_search", "patient_retrieval", "patient_chat"]
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    query_length: int = Field(ge=0, le=300)
    filter_categories: list[str] = Field(default_factory=list, max_length=16)
    index_release_id: str | None = None
    retrieved_source_ids: list[str] = Field(default_factory=list, max_length=8)
    retrieved_passage_ids: list[str] = Field(default_factory=list, max_length=8)
    evidence_decision: EvidenceDecision | None = None
    grounding_mode: GroundingMode = GroundingMode.fixed_safety_response
    original_retrieval_adequate: bool | None = None
    searched_query_variant_count: int = Field(default=0, ge=0, le=3)
    retrieval_decision: str | None = Field(default=None, max_length=80)
    general_knowledge_eligible: bool = False
    general_knowledge_outcome: str | None = Field(default=None, max_length=80)
    answer_schema_version: str | None = Field(default=None, max_length=120)
    structured_output_repair_count: int = Field(default=0, ge=0, le=1)
    model_version: str | None = None
    policy_version: str
    tool_schema_version: str
    safety_code: SafetyCode
    fallback_code: FallbackCode | None = None
    latency_ms: int = Field(ge=0)
    provider_input_tokens: int | None = Field(default=None, ge=0)
    provider_output_tokens: int | None = Field(default=None, ge=0)
    provider_error_code: str | None = Field(default=None, max_length=120)
    provider_attempt_count: int | None = Field(default=None, ge=1, le=2)
    provider_cost_microunits: int | None = Field(default=None, ge=0)
    rescue_trigger: (
        Literal["short_reference", "colloquial", "ambiguous", "weak_initial_retrieval"] | None
    ) = None
    rescue_attempted: bool = False
    rescue_outcome: (
        Literal[
            "not_triggered",
            "disabled",
            "improved",
            "clarification_needed",
            "planner_timeout",
            "planner_quota",
            "planner_unavailable",
            "malformed",
            "meaning_drift",
            "retry_unavailable",
            "no_improvement",
            "latency_exceeded",
            "cost_exceeded",
            "budget_exceeded",
        ]
        | None
    ) = None
    rescue_planner_model: str | None = Field(default=None, max_length=160)
    rescue_input_tokens: int | None = Field(default=None, ge=0)
    rescue_output_tokens: int | None = Field(default=None, ge=0)
    rescue_cache_hit_tokens: int | None = Field(default=None, ge=0)
    rescue_cache_miss_tokens: int | None = Field(default=None, ge=0)
    rescue_latency_ms: int | None = Field(default=None, ge=0)
    rescue_cost_microunits: int | None = Field(default=None, ge=0)
    rescue_retrieval_delta: float | None = None
    rescue_retry_request_id: str | None = Field(default=None, max_length=120)
    occurred_at: datetime


class ExternalProviderTransmissionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    mode: Literal["synthetic_only", "approved_real_context"] = "synthetic_only"
    data_region: Literal["mainland_china"] = "mainland_china"
    real_context_enabled: bool = False
    allowed_context_fields: list[str] = Field(default_factory=list, max_length=16)
    no_training_contract_verified: bool = False
    no_retention_contract_verified: bool = False
    privacy_review_id: str | None = None
    legal_review_id: str | None = None
    product_approval_id: str | None = None

    @model_validator(mode="after")
    def fail_closed_without_real_context_approvals(self) -> "ExternalProviderTransmissionPolicy":
        if self.mode == "synthetic_only":
            if self.real_context_enabled or self.allowed_context_fields:
                raise ValueError("Synthetic-only mode cannot transmit real patient context.")
            return self
        approvals = (
            self.real_context_enabled,
            bool(self.allowed_context_fields),
            self.no_training_contract_verified,
            self.no_retention_contract_verified,
            bool(self.privacy_review_id),
            bool(self.legal_review_id),
            bool(self.product_approval_id),
        )
        if not all(approvals):
            raise ValueError("Real-context transmission requires every approval gate.")
        return self


DEVELOPMENT_PROVIDER_POLICY = ExternalProviderTransmissionPolicy(
    provider="deepseek",
    mode="synthetic_only",
    data_region="mainland_china",
)

CHATBOT_POLICY_VERSION = "phase3-slice9-practical-guidance-v1-2026-07-17"
CHATBOT_TOOL_SCHEMA_VERSION = "phase3-slice1-2026-07-13"
