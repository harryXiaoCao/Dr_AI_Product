import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.clinical_event_intelligence_contracts import (
    CEI_PURPOSE_CONTRACT_VERSION,
    CEI_RECONCILIATION_VERSION,
    FrozenClinicalEventSnapshot,
    FrozenFact,
    FrozenLocation,
    FrozenRequestedLine,
    RetrievalManifest,
    RetrievalSource,
    canonical_checksum,
)
from app.clinical_event_intelligence_explanations import generate_role_explanation
from app.clinical_event_intelligence_provider import (
    DeepSeekCriticIntelligenceProvider,
    DeepSeekPrimaryIntelligenceProvider,
    provider_safe_retrieval,
    provider_safe_snapshot,
)
from app.clinical_event_intelligence_reconciliation import reconcile_critic
from app.clinical_event_intelligence_routes import _payload, router
from app.clinical_event_intelligence_validation import (
    IntelligenceValidationError,
    aggregate_ai_support_score,
    normalize_cost_provenance,
    normalize_tier5_uncertainty,
    validate_primary_output,
)
from app.config import Settings
from app.provider_transport import JsonProviderResponse

PATIENT_ID = "11111111-1111-4111-8111-111111111111"
EVENT_ID = "22222222-2222-4222-8222-222222222222"
REQUEST_ID = "33333333-3333-4333-8333-333333333333"
LINE_ID = "44444444-4444-4444-8444-444444444444"
FACT_SOURCE_ID = "55555555-5555-4555-8555-555555555555"
HOSPITAL_ID = "66666666-6666-4666-8666-666666666666"
CLINIC_ID = "77777777-7777-4777-8777-777777777777"
RELEASE_ID = "88888888-8888-4888-8888-888888888888"
EXCLUDED_SENTINEL = "EXCLUDED_PRIVATE_FACT_SENTINEL"


def _snapshot() -> FrozenClinicalEventSnapshot:
    location = FrozenLocation(
        jurisdiction_code="CN",
        province_code="CN-GD",
        city_code="CN-SZ",
        facility_level="tertiary",
        hospital_id=HOSPITAL_ID,
        clinic_id=CLINIC_ID,
        department="CARD",
        source="clinical_event",
        complete=True,
    )
    facts = [
        FrozenFact(
            fact_id="event.symptom_summary",
            category="clinical_event",
            value="Synthetic symptom summary",
            source_type="clinical_event",
            source_id=FACT_SOURCE_ID,
            verification_state="verified",
        )
    ]
    excluded = [
        FrozenFact(
            fact_id="medical_record.not_used.1",
            category="laboratory_or_report",
            value=EXCLUDED_SENTINEL,
            source_type="medical_records",
            source_id=str(uuid.uuid4()),
            verification_state="unverified",
        )
    ]
    lines = [
        FrozenRequestedLine(
            requested_line_id=LINE_ID,
            item_type="laboratory",
            label="Synthetic panel",
            code_system="DR_AI_INTERNAL",
            service_code="LAB_PANEL",
            quantity=1,
            unit="panel",
            requested_minor=10000,
            actual_cost_minor=10000,
            currency="CNY",
            service_date="2026-08-01",
        )
    ]
    body = {
        "snapshot_version": 1,
        "payer_request_version": 1,
        "patient_id": PATIENT_ID,
        "clinical_event_id": EVENT_ID,
        "payer_request_id": REQUEST_ID,
        "encounter_date": "2026-08-01T09:00:00+00:00",
        "location": location.model_dump(mode="json"),
        "facts_used": [item.model_dump(mode="json") for item in facts],
        "facts_not_used": [item.model_dump(mode="json") for item in excluded],
        "missing_information": [],
        "conflicting_information": [],
        "requested_lines": [item.model_dump(mode="json") for item in lines],
        "requested_item_set_checksum_sha256": canonical_checksum(
            [item.model_dump(mode="json") for item in lines]
        ),
    }
    return FrozenClinicalEventSnapshot(
        **body,
        snapshot_checksum_sha256=canonical_checksum(body),
    )


def _retrieval() -> RetrievalManifest:
    source = RetrievalSource(
        source_id=f"release:{RELEASE_ID}",
        source_type="regional_reference",
        release_id=RELEASE_ID,
        release_version="v1",
        checksum_sha256="a" * 64,
        authority="Synthetic regional authority",
        provider_transmission_allowed=True,
        payload={
            "scope_key": f"payer:{REQUEST_ID}",
            "facility_scope": {
                "hospital_ids": [HOSPITAL_ID],
                "clinic_ids": [CLINIC_ID],
                "facility_levels": ["tertiary"],
            },
            "price_items": [
                {
                    "source_item_id": str(uuid.uuid4()),
                    "code_system": "DR_AI_INTERNAL",
                    "service_code": "LAB_PANEL",
                    "unit": "panel",
                    "currency": "CNY",
                    "amount_low_minor": 8000,
                    "amount_high_minor": 12000,
                }
            ],
        },
    )
    body = {
        "retrieval_contract_version": "clinical-event-intelligence-retrieval.v1",
        "authorization_scope_checksum_sha256": "b" * 64,
        "sources": [source.model_dump(mode="json")],
        "missing_source_types": [],
    }
    return RetrievalManifest(**body, manifest_checksum_sha256=canonical_checksum(body))


def _primary_output(
    snapshot: FrozenClinicalEventSnapshot,
    retrieval: RetrievalManifest,
    *,
    line_id: str = LINE_ID,
    tier5_high: int = 20000,
) -> dict[str, object]:
    return {
        "purpose_code": "clinical_event_intelligence_primary",
        "purpose_contract_version": CEI_PURPOSE_CONTRACT_VERSION,
        "schema_version": "clinical-event-intelligence-output.v1",
        "snapshot_checksum_sha256": snapshot.snapshot_checksum_sha256,
        "retrieval_manifest_checksum_sha256": retrieval.manifest_checksum_sha256,
        "pathways": [
            {
                "pathway_id": "pathway_typical",
                "pathway_type": "typical_first_line",
                "trigger_fact_ids": ["event.symptom_summary"],
                "usefulness": "Provides a bounded comparison hypothesis.",
                "confidence": 60,
                "assumptions": [],
                "limitations": ["Synthetic evidence only."],
                "items": [
                    {
                        "item_key": "predicted_follow_up",
                        "label": "Synthetic follow-up",
                        "category": "consultation",
                        "service_code": None,
                        "quantity_low": 1,
                        "quantity_high": 1,
                        "unit": "visit",
                        "currency": "CNY",
                        "cost_low_minor": 1000,
                        "cost_high_minor": 3000,
                        "rationale_fact_ids": ["event.symptom_summary"],
                    }
                ],
            }
        ],
        "requested_item_assessments": [
            {
                "requested_line_id": line_id,
                "usefulness": "May help document the current request.",
                "mapped_pathway_ids": ["pathway_typical"],
                "scores": {
                    "clinical_fit": 80,
                    "evidence_support": 70,
                    "timing_sequence": 60,
                    "quantity_intensity": 50,
                    "documentation_completeness": 40,
                    "cost_alignment": 99,
                },
                "estimated_quantity": {"low": 1, "high": 2, "unit": "panel"},
                "estimated_cost": {
                    "low_minor": 10000,
                    "high_minor": tier5_high,
                    "currency": "CNY",
                    "provenance_tier": 5,
                    "source_ids": [],
                    "is_model_only_exploratory": True,
                },
                "supporting_fact_ids": ["event.symptom_summary"],
                "contradicting_fact_ids": [],
                "missing_information": ["A recent result is missing."],
                "alternatives": ["Clarify before comparing alternatives."],
                "confidence": "moderate",
                "brief_comment": "Human review remains responsible.",
            }
        ],
        "unresolved_questions": ["Is a recent result available?"],
        "overall_confidence": "moderate",
    }


def test_tier5_scoring_has_zero_cost_weight_and_exact_line_coverage() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    validated = validate_primary_output(
        _primary_output(snapshot, retrieval), snapshot=snapshot, retrieval=retrieval
    )
    item = validated.assessments[0]
    assert item.cost_alignment_weight_bp == 0
    expected, weight = aggregate_ai_support_score(item.proposal.scores, provenance_tier=5)
    assert item.ai_support_score == expected
    assert weight == 0
    assert item.proposal.estimated_cost.is_model_only_exploratory is True


def test_tier5_narrow_range_and_duplicate_line_fail_deterministically() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    with pytest.raises(IntelligenceValidationError) as narrow:
        validate_primary_output(
            _primary_output(snapshot, retrieval, tier5_high=10000),
            snapshot=snapshot,
            retrieval=retrieval,
        )
    assert "tier5_uncertainty_not_wide" in narrow.value.reason_codes
    duplicate = _primary_output(snapshot, retrieval)
    duplicate["requested_item_assessments"] = (  # type: ignore[index]
        duplicate["requested_item_assessments"] * 2  # type: ignore[operator]
    )
    with pytest.raises(IntelligenceValidationError) as coverage:
        validate_primary_output(duplicate, snapshot=snapshot, retrieval=retrieval)
    assert "duplicate_requested_line_assessment" in coverage.value.reason_codes


def test_tier5_safe_widening_changes_only_high_and_records_lineage() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    narrow = _primary_output(snapshot, retrieval, tier5_high=11000)
    original = json.loads(json.dumps(narrow))
    normalized, results = normalize_tier5_uncertainty(narrow)
    estimate = normalized["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    assert estimate["low_minor"] == 10000
    assert estimate["high_minor"] == 20000
    original["requested_item_assessments"][0]["estimated_cost"]["high_minor"] = 20000
    assert normalized == original
    assert results == ["server_widened_tier5_uncertainty"]
    validated = validate_primary_output(
        normalized,
        snapshot=snapshot,
        retrieval=retrieval,
        server_normalizations=results,
    )
    assert "server_widened_tier5_uncertainty" in validated.validation_results


def test_claimed_cost_tier_must_match_source_type_and_requested_line() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    retrieval.sources[0].source_type = "guideline"
    output = _primary_output(snapshot, retrieval)
    estimate = output["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    estimate.update(  # type: ignore[union-attr]
        {
            "provenance_tier": 2,
            "source_ids": [f"release:{RELEASE_ID}"],
            "is_model_only_exploratory": False,
        }
    )
    with pytest.raises(IntelligenceValidationError) as exc:
        validate_primary_output(output, snapshot=snapshot, retrieval=retrieval)
    assert "cost_provenance_tier_source_mismatch" in exc.value.reason_codes


def test_server_binds_cost_tier_to_admitted_line_matched_source() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    output = _primary_output(snapshot, retrieval)
    estimate = output["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    estimate.update(  # type: ignore[union-attr]
        {
            "provenance_tier": 1,
            "source_ids": [f"release:{RELEASE_ID}"],
            "is_model_only_exploratory": False,
        }
    )
    normalized, results = normalize_cost_provenance(output, snapshot=snapshot, retrieval=retrieval)
    normalized_estimate = normalized["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    assert normalized_estimate["provenance_tier"] == 2
    assert normalized_estimate["source_ids"] == [f"release:{RELEASE_ID}"]
    assert results == [f"server_bound_cost_provenance:{LINE_ID}:tier_2"]
    validated = validate_primary_output(
        normalized,
        snapshot=snapshot,
        retrieval=retrieval,
        server_normalizations=results,
    )
    assert results[0] in validated.validation_results


@pytest.mark.parametrize("source_id", ["release:unknown", f"release:{RELEASE_ID}"])
def test_server_refuses_unknown_or_line_mismatched_cost_source(source_id: str) -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    if source_id != "release:unknown":
        retrieval.sources[0].payload["price_items"][0]["service_code"] = "OTHER-LINE"
    output = _primary_output(snapshot, retrieval, tier5_high=10001)
    estimate = output["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    estimate.update(  # type: ignore[union-attr]
        {
            "provenance_tier": 2,
            "source_ids": [source_id],
            "is_model_only_exploratory": False,
        }
    )
    normalized, results = normalize_cost_provenance(output, snapshot=snapshot, retrieval=retrieval)
    normalized, widening = normalize_tier5_uncertainty(normalized)
    normalized_estimate = normalized["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    assert normalized_estimate["provenance_tier"] == 5
    assert normalized_estimate["source_ids"] == []
    assert normalized_estimate["is_model_only_exploratory"] is True
    assert normalized_estimate["high_minor"] == 20000
    assert results == [f"server_forced_tier5_no_admitted_cost_source:{LINE_ID}"]
    assert widening == ["server_widened_tier5_uncertainty"]
    validate_primary_output(
        normalized,
        snapshot=snapshot,
        retrieval=retrieval,
        server_normalizations=results + widening,
    )


class _CaptureTransport:
    def __init__(self) -> None:
        self.body: dict[str, object] | None = None

    def request(self, **kwargs) -> JsonProviderResponse:
        self.body = kwargs["request_body"]
        user = self.body["messages"][1]  # type: ignore[index]
        json.loads(user["content"])  # type: ignore[index]
        output = _primary_output(_snapshot(), _retrieval(), line_id="requested_line_001")
        return JsonProviderResponse(
            payload={
                "model": "deepseek-v4-pro",
                "choices": [{"message": {"content": json.dumps(output)}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            }
        )


class _CriticCaptureTransport:
    def __init__(self, snapshot, primary) -> None:
        self.snapshot = snapshot
        self.primary = primary
        self.body: dict[str, object] | None = None

    def request(self, **kwargs) -> JsonProviderResponse:
        self.body = kwargs["request_body"]
        output = {
            "purpose_code": "clinical_event_intelligence_critic",
            "schema_version": "clinical-event-intelligence-critic.v1",
            "snapshot_checksum_sha256": self.snapshot.snapshot_checksum_sha256,
            "primary_output_checksum_sha256": self.primary.output_checksum_sha256,
            "discrepancies": [],
        }
        return JsonProviderResponse(
            payload={
                "model": "deepseek-v4-pro",
                "choices": [{"message": {"content": json.dumps(output)}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            }
        )


def test_primary_provider_body_excludes_scope_ids_excluded_facts_and_internal_scopes() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    safe_snapshot, aliases = provider_safe_snapshot(snapshot)
    safe_retrieval, source_aliases = provider_safe_retrieval(retrieval)
    serialized = json.dumps({"snapshot": safe_snapshot, "retrieval": safe_retrieval})
    for value in (
        PATIENT_ID,
        EVENT_ID,
        REQUEST_ID,
        FACT_SOURCE_ID,
        HOSPITAL_ID,
        CLINIC_ID,
        RELEASE_ID,
        EXCLUDED_SENTINEL,
    ):
        assert value not in serialized
    assert aliases == {"requested_line_001": LINE_ID}
    assert source_aliases == {"retrieval_source_001": f"release:{RELEASE_ID}"}
    transport = _CaptureTransport()
    settings = Settings(
        environment="test",
        deepseek_api_key=SecretStr("synthetic-key"),
        clinical_event_intelligence_primary_enabled=True,
        clinical_event_intelligence_primary_kill_switch=False,
    )
    response = DeepSeekPrimaryIntelligenceProvider(transport).generate(
        snapshot=snapshot,
        retrieval=retrieval,
        settings=settings,
    )
    assert response.output["requested_item_assessments"][0]["requested_line_id"] == LINE_ID  # type: ignore[index]
    assert response.cost_microunits == 870
    body_text = json.dumps(transport.body)
    assert EXCLUDED_SENTINEL not in body_text
    assert PATIENT_ID not in body_text


def test_critic_payload_realiases_line_and_source_ids() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    output = _primary_output(snapshot, retrieval)
    estimate = output["requested_item_assessments"][0]["estimated_cost"]  # type: ignore[index]
    estimate.update(  # type: ignore[union-attr]
        {
            "provenance_tier": 2,
            "source_ids": [f"release:{RELEASE_ID}"],
            "is_model_only_exploratory": False,
        }
    )
    retrieval.sources[0].payload["price_items"] = [
        {
            "code_system": "DR_AI_INTERNAL",
            "service_code": "LAB_PANEL",
            "unit": "panel",
            "currency": "CNY",
        }
    ]
    primary = validate_primary_output(output, snapshot=snapshot, retrieval=retrieval)
    transport = _CriticCaptureTransport(snapshot, primary)
    settings = Settings(
        environment="test",
        deepseek_api_key=SecretStr("synthetic-key"),
        clinical_event_intelligence_critic_enabled=True,
        clinical_event_intelligence_critic_kill_switch=False,
    )
    DeepSeekCriticIntelligenceProvider(transport).review(
        snapshot=snapshot,
        retrieval=retrieval,
        primary=primary,
        settings=settings,
    )
    body = json.dumps(transport.body)
    assert LINE_ID not in body
    assert f"release:{RELEASE_ID}" not in body
    assert "requested_line_001" in body
    assert "retrieval_source_001" in body


def test_reconciliation_is_bounded_and_never_replaces_primary() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    primary = validate_primary_output(
        _primary_output(snapshot, retrieval), snapshot=snapshot, retrieval=retrieval
    )
    critic = {
        "purpose_code": "clinical_event_intelligence_critic",
        "schema_version": "clinical-event-intelligence-critic.v1",
        "snapshot_checksum_sha256": snapshot.snapshot_checksum_sha256,
        "primary_output_checksum_sha256": primary.output_checksum_sha256,
        "discrepancies": [
            {
                "requested_line_id": LINE_ID,
                "category": "score_dimension",
                "severity": "material",
                "fact_ids": ["event.symptom_summary"],
                "concise_comment": "The dimension needs human review.",
            }
        ],
    }
    result = reconcile_critic(critic, snapshot=snapshot, primary=primary)
    assert result.state == "material_disagreement"
    assert result.reconciliation_version == CEI_RECONCILIATION_VERSION
    assert result.deterministic_primary_preserved is True


class _EmptyScalars:
    def all(self) -> list[object]:
        return []


class _PayloadDb:
    def scalars(self, _query):
        return _EmptyScalars()

    def scalar(self, _query):
        return SimpleNamespace(
            id=uuid.uuid4(),
            display_mode="validated_fact_selection",
            locale="en",
            fact_checksum_sha256="f" * 64,
            display_json={"sections": [], "no_automatic_action": True},
            validation_json={"valid": True, "reason_codes": []},
        )


def test_role_payload_is_allowlisted_and_flutter_contract_aligned() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    validated = validate_primary_output(
        _primary_output(snapshot, retrieval), snapshot=snapshot, retrieval=retrieval
    )
    artifact = SimpleNamespace(
        id=uuid.uuid4(),
        artifact_version=1,
        lifecycle_state="validated",
        requested_set_checksum_sha256=snapshot.requested_item_set_checksum_sha256,
        disagreement_state="agreement",
        artifact_json={
            "snapshot": snapshot.model_dump(mode="json"),
            "pathways": [item.model_dump(mode="json") for item in validated.primary.pathways],
            "requested_item_assessments": [
                item.model_dump(mode="json") for item in validated.assessments
            ],
            "reviewer_private_note": "PRIVATE_REVIEWER_NOTE_SENTINEL",
            "raw_provider_response": "RAW_PROVIDER_RESPONSE_SENTINEL",
            "hidden_prompt": "HIDDEN_PROMPT_SENTINEL",
            "credential": "CREDENTIAL_SENTINEL",
            "chain_of_thought": "CHAIN_OF_THOUGHT_SENTINEL",
        },
        validation_json={"valid": True},
        created_at=datetime.now(UTC),
    )
    db = _PayloadDb()
    for role in ("patient", "doctor", "payer"):
        result = _payload(db, artifact, role=role)  # type: ignore[arg-type]
        encoded = json.dumps(result, default=str)
        assert PATIENT_ID not in encoded
        assert EVENT_ID not in encoded
        assert REQUEST_ID not in encoded
        assert FACT_SOURCE_ID not in encoded
        assert EXCLUDED_SENTINEL not in encoded
        for sentinel in (
            "PRIVATE_REVIEWER_NOTE_SENTINEL",
            "RAW_PROVIDER_RESPONSE_SENTINEL",
            "HIDDEN_PROMPT_SENTINEL",
            "CREDENTIAL_SENTINEL",
            "CHAIN_OF_THOUGHT_SENTINEL",
        ):
            assert sentinel not in encoded
        item = result["requested_item_assessments"][0]  # type: ignore[index]
        assert item["label"] == "Synthetic panel"
        assert item["requested_quantity"] == 1
        assert item["actual_cost_minor"] == 10000
        assert item["scores"]["ai_support_score"] >= 0
        assert result["missing_documentation"]
        assert result["counterfactuals"]
        assert result["critic"]["state"] == "agreement"
        assert "lineage" in result
        assert result["explanation"]["display_mode"] == "validated_fact_selection"
        assert result["explanation"]["validation"] == {
            "valid": True,
            "reason_codes": [],
        }


def test_role_explanation_strips_hidden_source_ids_and_binds_locale() -> None:
    snapshot = _snapshot()
    retrieval = _retrieval()
    output = _primary_output(snapshot, retrieval)
    proposal = output["requested_item_assessments"][0]  # type: ignore[index]
    proposal["estimated_cost"] = {  # type: ignore[index]
        "low_minor": 8000,
        "high_minor": 12000,
        "currency": "CNY",
        "provenance_tier": 2,
        "source_ids": [f"release:{RELEASE_ID}"],
        "is_model_only_exploratory": False,
    }
    validated = validate_primary_output(output, snapshot=snapshot, retrieval=retrieval)
    artifact = SimpleNamespace(
        artifact_version=1,
        lifecycle_state="validated",
        disagreement_state="agreement",
        artifact_json={
            "snapshot": snapshot.model_dump(mode="json"),
            "pathways": [item.model_dump(mode="json") for item in validated.primary.pathways],
            "requested_item_assessments": [
                item.model_dump(mode="json") for item in validated.assessments
            ],
            "reviewer_private_note": "PRIVATE_REVIEWER_NOTE_SENTINEL",
            "raw_provider_response": "RAW_PROVIDER_RESPONSE_SENTINEL",
            "hidden_prompt": "HIDDEN_PROMPT_SENTINEL",
            "credential": "CREDENTIAL_SENTINEL",
            "chain_of_thought": "CHAIN_OF_THOUGHT_SENTINEL",
        },
    )
    result = generate_role_explanation(
        artifact,
        role="patient",
        locale="zh-Hans",
        settings=Settings(environment="test"),
    )
    encoded = json.dumps(result.display, default=str)
    assert result.display["locale"] == "zh-Hans"
    assert RELEASE_ID not in encoded
    assert "source_ids" not in encoded
    for sentinel in (
        "PRIVATE_REVIEWER_NOTE_SENTINEL",
        "RAW_PROVIDER_RESPONSE_SENTINEL",
        "HIDDEN_PROMPT_SENTINEL",
        "CREDENTIAL_SENTINEL",
        "CHAIN_OF_THOUGHT_SENTINEL",
    ):
        assert sentinel not in encoded


def test_canonical_request_keyed_routes_and_default_kill_switches() -> None:
    paths = {route.path for route in router.routes}
    assert "/api/v1/doctor/payer-requests/{request_id}/intelligence" in paths
    assert "/api/v1/patient/payer-requests/{request_id}/intelligence" in paths
    assert "/api/v1/payer/requests/{request_id}/intelligence" in paths
    assert (
        "/api/v1/doctor/payer-requests/{request_id}/intelligence/{artifact_id}/responses" in paths
    )
    settings = Settings(environment="test", _env_file=None)
    assert settings.clinical_event_intelligence_primary_model == "deepseek-v4-pro"
    assert settings.clinical_event_intelligence_explanation_model == "deepseek-v4-flash"
    assert settings.clinical_event_intelligence_primary_enabled is False
    assert settings.clinical_event_intelligence_primary_kill_switch is True
