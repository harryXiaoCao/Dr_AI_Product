from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class SafetyCode(StrEnum):
    permitted_education = "permitted_education"
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


class StructuredModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_language: Literal["zh-Hans", "en"]
    answer_sections: list[ModelAnswerSection] = Field(min_length=1, max_length=6)
    uses_patient_context: bool
    patient_context_attribution: str | None = Field(default=None, max_length=240)
    uncertainties: list[str] = Field(default_factory=list, max_length=8)
    next_action_code: NextActionCode = NextActionCode.none
    refusal_code: RefusalCode | None = None

    @model_validator(mode="after")
    def require_context_attribution(self) -> "StructuredModelOutput":
        if self.uses_patient_context != (self.patient_context_attribution is not None):
            raise ValueError("Patient-context use and attribution must agree.")
        return self


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
    model_version: str | None = None
    policy_version: str
    tool_schema_version: str
    safety_code: SafetyCode
    fallback_code: FallbackCode | None = None
    latency_ms: int = Field(ge=0)
    provider_input_tokens: int | None = Field(default=None, ge=0)
    provider_output_tokens: int | None = Field(default=None, ge=0)
    provider_cost_microunits: int | None = Field(default=None, ge=0)
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

CHATBOT_POLICY_VERSION = "phase3-slice1-2026-07-13"
CHATBOT_TOOL_SCHEMA_VERSION = "phase3-slice1-2026-07-13"
