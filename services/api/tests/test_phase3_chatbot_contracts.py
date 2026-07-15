from datetime import UTC, date, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from app.chatbot_contracts import (
    CHATBOT_POLICY_VERSION,
    CHATBOT_TOOL_SCHEMA_VERSION,
    DEVELOPMENT_PROVIDER_POLICY,
    AuthorityTier,
    ChatbotTelemetryEvent,
    ChatbotToolCall,
    DoctorResourceSearchRequest,
    EvidenceDecision,
    ExternalProviderTransmissionPolicy,
    FallbackCode,
    KnowledgeAudience,
    ModelAnswerSection,
    PatientEvidenceResponse,
    SafetyCode,
    SourceAdmissionContract,
    SourceCitation,
    SourceLifecycleState,
    SourceStatus,
    StructuredModelOutput,
)
from app.config import Settings


def _source_admission(**overrides: object) -> SourceAdmissionContract:
    values: dict[str, object] = {
        "source_id": "source-cn-001",
        "authority_tier": AuthorityTier.a,
        "organization_allowlisted": True,
        "authority_evidence_verified": True,
        "commercial_use_allowed": True,
        "storage_allowed": True,
        "transformation_allowed": True,
        "embedding_allowed": True,
        "excerpt_display_allowed": True,
        "model_provider_transmission_allowed": False,
        "medical_review_approved": True,
        "native_language_review_approved": True,
        "lifecycle_state": SourceLifecycleState.patient_approved,
        "audiences": {KnowledgeAudience.doctor, KnowledgeAudience.patient},
        "rights_record_id": "rights-001",
        "review_record_ids": ["medical-001", "language-001"],
    }
    values.update(overrides)
    return SourceAdmissionContract.model_validate(values)


def _citation(*, patient_use_approved: bool = True) -> SourceCitation:
    return SourceCitation(
        source_id="source-cn-001",
        version_id="version-001",
        passage_ids=["passage-001"],
        title="Synthetic reviewed health guidance",
        publisher="Synthetic national health authority",
        official_locator="https://example.invalid/source-cn-001",
        jurisdiction="CN",
        original_language="zh-Hans",
        publication_date=date(2026, 1, 1),
        last_medical_review_date=date(2026, 7, 13),
        authority_tier=AuthorityTier.a,
        status=SourceStatus.current,
        patient_use_approved=patient_use_approved,
    )


def test_source_admission_is_rights_review_and_audience_gated() -> None:
    admitted = _source_admission()
    assert admitted.audiences == {KnowledgeAudience.doctor, KnowledgeAudience.patient}

    with pytest.raises(ValidationError, match="rights and medical approval"):
        _source_admission(embedding_allowed=False)
    with pytest.raises(ValidationError, match="native-language review"):
        _source_admission(native_language_review_approved=False)
    with pytest.raises(ValidationError, match="lifecycle states"):
        _source_admission(lifecycle_state=SourceLifecycleState.rights_pending)


def test_doctor_search_contract_rejects_unknown_fields_and_large_pages() -> None:
    request = DoctorResourceSearchRequest(query="hypertension guidance")
    assert request.filters.jurisdictions == ["CN"]
    assert request.limit == 20

    with pytest.raises(ValidationError):
        DoctorResourceSearchRequest.model_validate({"query": "guidance", "limit": 51})
    with pytest.raises(ValidationError):
        DoctorResourceSearchRequest.model_validate({"query": "guidance", "patient_id": "x"})


def test_patient_evidence_fails_closed_after_unsuccessful_gate() -> None:
    with pytest.raises(ValidationError, match="Failed evidence gates"):
        PatientEvidenceResponse.model_validate(
            {
                "request_id": "req-001",
                "decision": EvidenceDecision.conflicting,
                "passages": [
                    {
                        "passage_id": "passage-001",
                        "source_id": "source-cn-001",
                        "version_id": "version-001",
                        "text": "Synthetic evidence passage.",
                        "language": "zh-Hans",
                        "citation": _citation().model_dump(),
                    }
                ],
                "index_release_id": "index-001",
            }
        )
    with pytest.raises(ValidationError, match="patient-approved"):
        PatientEvidenceResponse.model_validate(
            {
                "request_id": "req-002",
                "decision": EvidenceDecision.sufficient,
                "passages": [
                    {
                        "passage_id": "passage-002",
                        "source_id": "source-cn-002",
                        "version_id": "version-002",
                        "text": "Synthetic doctor-only evidence passage.",
                        "language": "zh-Hans",
                        "citation": _citation(patient_use_approved=False).model_dump(),
                    }
                ],
                "index_release_id": "index-001",
            }
        )


def test_structured_output_requires_citations_and_context_attribution() -> None:
    output = StructuredModelOutput(
        answer_language="zh-Hans",
        answer_sections=[
            ModelAnswerSection(
                text="This is synthetic educational content.",
                supporting_passage_ids=["passage-001"],
            )
        ],
        uses_patient_context=False,
    )
    assert output.patient_context_attribution is None

    with pytest.raises(ValidationError, match="must agree"):
        StructuredModelOutput.model_validate(
            {
                **output.model_dump(),
                "uses_patient_context": True,
                "patient_context_attribution": None,
            }
        )


def test_tool_calls_are_allowlisted_and_schema_strict() -> None:
    adapter = TypeAdapter(ChatbotToolCall)
    tool_call = adapter.validate_python({"tool": "show_emergency_guidance", "rule_id": "cn-120"})
    assert tool_call.tool == "show_emergency_guidance"

    with pytest.raises(ValidationError):
        adapter.validate_python({"tool": "run_sql", "query": "select 1"})
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {"tool": "show_emergency_guidance", "rule_id": "cn-120", "raw_prompt": "x"}
        )


def test_telemetry_schema_rejects_raw_content() -> None:
    values = {
        "request_id": "req-001",
        "actor_role": "patient",
        "workflow": "patient_chat",
        "query_sha256": "a" * 64,
        "query_length": 24,
        "policy_version": CHATBOT_POLICY_VERSION,
        "tool_schema_version": CHATBOT_TOOL_SCHEMA_VERSION,
        "safety_code": SafetyCode.permitted_education,
        "fallback_code": FallbackCode.no_eligible_evidence,
        "latency_ms": 18,
        "occurred_at": datetime.now(UTC),
    }
    event = ChatbotTelemetryEvent.model_validate(values)
    assert event.query_length == 24

    with pytest.raises(ValidationError):
        ChatbotTelemetryEvent.model_validate({**values, "raw_prompt": "private text"})
    with pytest.raises(ValidationError):
        ChatbotTelemetryEvent.model_validate({**values, "query_sha256": "not-a-hash"})


def test_external_provider_policy_and_settings_default_to_synthetic_only() -> None:
    assert DEVELOPMENT_PROVIDER_POLICY.mode == "synthetic_only"
    assert DEVELOPMENT_PROVIDER_POLICY.real_context_enabled is False

    with pytest.raises(ValidationError, match="every approval gate"):
        ExternalProviderTransmissionPolicy(
            provider="deepseek",
            mode="approved_real_context",
            real_context_enabled=True,
            allowed_context_fields=["selected_care_context"],
        )

    settings = Settings()
    assert settings.chatbot_data_mode == "synthetic_only"
    assert settings.chatbot_external_provider_real_context_enabled is False

    with pytest.raises(ValidationError, match="every approval gate"):
        Settings(chatbot_external_provider_real_context_enabled=True)
