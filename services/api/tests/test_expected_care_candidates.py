import copy
import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from app.care_reference_engine import EvaluationContext, EvaluationRequest
from app.care_reference_integration import CareReferenceAuthorizationError
from app.cost_estimation_facts import (
    CostFactScopeError,
    build_cost_estimation_fact_snapshot,
    serialize_cost_fact_snapshot,
)
from app.database import SessionLocal
from app.expected_care_candidates import (
    ExpectedCareCandidateConflict,
    ExpectedCareProviderError,
    ProviderCandidateResponse,
    generate_expected_care_candidate,
)
from app.models import (
    CareCostItem,
    ChronicDisease,
    ClinicalEvent,
    ClinicalService,
    ConsultationRequest,
    Diagnosis,
    DoctorProfile,
    ExpectedCareCandidateAttempt,
    ExpectedCareCandidateRequest,
    ExpectedCareCandidateResult,
    MedicalImagingAsset,
    MedicalRecord,
    Medication,
    PatientAllergy,
    PatientProfile,
    PayerOrganization,
    PayerRequest,
    Prescription,
    PrescriptionMedication,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
    User,
    VisitHistory,
)
from app.synthetic_care_reference import (
    install_synthetic_care_reference_bundle,
    install_synthetic_laboratory_reference_bundle,
    synthetic_active_selection,
    synthetic_laboratory_selection,
)
from tests.helpers import auth_header, register


def _context(*, evaluated_on: date = date(2026, 7, 25)) -> EvaluationContext:
    return EvaluationContext(
        evaluated_on=evaluated_on,
        reference_date=date(2026, 7, 25),
        jurisdiction="CN",
        region="Synthetic Province",
        encounter_type="outpatient",
        facility_ownership="public",
        facility_level="primary",
        currency="CNY",
        patient_age=42,
    )


def _connected_case(
    client: TestClient,
    *,
    suffix: str,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    patient_email = f"candidate.patient.{suffix}@example.com"
    doctor_email = f"candidate.doctor.{suffix}@example.com"
    patient = register(client, email=patient_email, password="Patient9!", role="patient")
    doctor = register(client, email=doctor_email, password="Doctor9!", role="doctor")
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    patient_id = uuid.UUID(care["patient"]["patient_id"])
    connected = client.post(
        "/api/v1/patients/connect",
        headers=doctor_headers,
        json={"patient_code": care["patient"]["synthetic_identifier"]},
    )
    assert connected.status_code == 200
    event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Synthetic candidate event",
            "chief_complaint": "Must never enter provider input.",
            "symptom_summary": "Confidential unrelated history.",
            "status": "active",
        },
    )
    assert event.status_code == 200
    with SessionLocal() as session:
        actor_id = session.scalar(select(User.id).where(User.email == doctor_email))
    assert actor_id is not None
    return actor_id, patient_id, uuid.UUID(event.json()["id"])


def _valid_output(provider_input: dict[str, object]) -> dict[str, object]:
    context = provider_input["context"]
    totals = provider_input["server_totals"]
    assert isinstance(context, dict)
    assert isinstance(totals, dict)
    return {
        "purpose_code": provider_input["purpose_code"],
        "purpose_contract_version": provider_input["purpose_contract_version"],
        "schema_version": provider_input["schema_version"],
        "minimum_input_checksum_sha256": provider_input["minimum_input_checksum_sha256"],
        "scenario_release_id": provider_input["scenario_release_id"],
        "reference_date": context["reference_date"],
        "jurisdiction": context["jurisdiction"],
        "region": context["region"],
        "facility_ownership": context["facility_ownership"],
        "facility_level": context["facility_level"],
        "currency": context["currency"],
        "assumptions": copy.deepcopy(provider_input["allowed_assumptions"]),
        "missing_information": copy.deepcopy(provider_input["allowed_missing_information"]),
        "attributable_exceptions": [],
        "confidence_category": "moderate",
        "confidence_limitations": [
            "Wholly synthetic reference data; clinician responses remain separate."
        ],
        "items": copy.deepcopy(provider_input["admitted_candidates"]),
        "total_low_minor": totals["total_low_minor"],
        "total_high_minor": totals["total_high_minor"],
        "release_lineage": copy.deepcopy(provider_input["release_lineage"]),
    }


class StubProvider:
    def __init__(
        self,
        mutations: list[Callable[[dict[str, object]], None] | ExpectedCareProviderError]
        | None = None,
    ) -> None:
        self.mutations = list(mutations or [])
        self.calls = 0
        self.inputs: list[dict[str, object]] = []

    def generate(self, *, provider_input, output_schema, settings):
        del output_schema, settings
        self.calls += 1
        self.inputs.append(copy.deepcopy(provider_input))
        if self.mutations:
            mutation = self.mutations[min(self.calls - 1, len(self.mutations) - 1)]
            if isinstance(mutation, ExpectedCareProviderError):
                raise mutation
        else:
            mutation = None
        output = _valid_output(provider_input)
        if callable(mutation):
            mutation(output)
        return ProviderCandidateResponse(
            output=output,
            provider="deterministic_stub",
            model="stub-expected-care-v1",
            input_tokens=120,
            output_tokens=80,
            cost_microunits=40,
        )


def _enable(settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "expected_care_candidate_enabled", True)
    monkeypatch.setattr(settings, "expected_care_provider", "deterministic_stub")
    monkeypatch.setattr(settings, "expected_care_model", "stub-expected-care-v1")


def _generate(
    session,
    *,
    actor_id,
    patient_id,
    event_id,
    settings,
    provider,
    key,
    predecessor_request_id=None,
):
    return generate_expected_care_candidate(
        session,
        actor_user_id=actor_id,
        patient_id=patient_id,
        clinical_event_id=event_id,
        selection=synthetic_active_selection(),
        request=EvaluationRequest(context=_context()),
        idempotency_key=key,
        settings=settings,
        provider=provider,
        predecessor_request_id=predecessor_request_id,
    )


def test_valid_candidate_is_immutable_pending_review_and_minimum_necessary(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="valid")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-valid-001",
        )
        session.commit()
        assert generated.request.lifecycle_state == "generated_pending_review"
        assert generated.request.validation_outcome == "validated"
        assert generated.result.total_low_minor == 2000
        assert generated.result.total_high_minor == 6000
        assert generated.result.candidate_json["confidence_category"] == "moderate"
        assert generated.result.validation_json["immutable_baseline_published"] is True
        assert generated.result.validation_json["doctor_may_modify_or_hide"] is False
        assert session.scalar(select(func.count()).select_from(ExpectedCareCandidateAttempt)) == 1

    assert provider.calls == 1
    transmitted = provider.inputs[0]
    serialized = str(transmitted)
    assert str(patient_id) not in serialized
    assert str(event_id) not in serialized
    assert "Clinical Event symptoms and complaint" in serialized
    assert "Confidential unrelated history." in serialized
    assert "doctor_summary" not in serialized
    assert "notes" not in serialized
    assert "attachment" not in serialized
    snapshot = transmitted["clinical_event_fact_snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["authority_boundary"]["provider_may_not_add_or_modify_facts"] is True
    assert snapshot["snapshot_checksum_sha256"]


def test_combined_synthetic_event_fact_snapshot_and_role_safety(client) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="combined-facts")
    unrelated = register(
        client,
        email="candidate.patient.combined-facts-unrelated@example.com",
        password="Patient9!",
        role="patient",
    )
    unrelated_care = client.get(
        "/api/v1/patient/me/care",
        headers=auth_header(unrelated["access_token"]),
    ).json()
    unrelated_patient_id = uuid.UUID(unrelated_care["patient"]["patient_id"])
    now = datetime(2026, 7, 25, 9, 0, tzinfo=UTC)
    with SessionLocal() as session:
        patient = session.get(PatientProfile, patient_id)
        event = session.get(ClinicalEvent, event_id)
        doctor = session.scalar(select(DoctorProfile).where(DoctorProfile.user_id == actor_id))
        patient_user_id = session.scalar(
            select(PatientProfile.user_id).where(PatientProfile.id == patient_id)
        )
        assert patient is not None and event is not None and doctor is not None
        assert patient_user_id is not None
        patient.heart_history = "Synthetic cardiac history."
        patient.patient_reported_medications = "Synthetic current supplement."
        session.add_all(
            [
                PatientAllergy(
                    patient_id=patient_id,
                    label="Synthetic allergy",
                    reaction="Synthetic rash",
                    severity="mild",
                    status="active",
                    recorded_by_user_id=actor_id,
                ),
                ChronicDisease(
                    patient_id=patient_id,
                    name="Synthetic chronic condition",
                    status="active",
                    diagnosed_on=date(2020, 1, 1),
                    notes="Synthetic history only.",
                    recorded_by_user_id=actor_id,
                ),
                VisitHistory(
                    patient_id=patient_id,
                    clinical_event_id=event_id,
                    visit_type="follow_up",
                    title="Synthetic event record",
                    summary="Synthetic record summary.",
                    occurred_at=now,
                    clinician_label="Synthetic clinician",
                    recorded_by_user_id=actor_id,
                ),
                Diagnosis(
                    patient_id=patient_id,
                    clinical_event_id=event_id,
                    label="Synthetic confirmed finding",
                    status="active",
                    diagnosed_on=date(2026, 7, 25),
                    notes="Doctor-owned synthetic finding.",
                    recorded_by_user_id=actor_id,
                ),
                MedicalRecord(
                    patient_id=patient_id,
                    title="Patient-wide synthetic record",
                    category="history",
                    summary="Not event bound.",
                    recorded_at=now,
                ),
            ]
        )
        medication = Medication(
            patient_id=patient_id,
            clinical_event_id=event_id,
            name="Synthetic medicine",
            dosage="1 synthetic unit",
            schedule="daily",
            status="active",
            note="Synthetic only.",
        )
        session.add(medication)
        session.flush()
        prescription = Prescription(
            patient_id=patient_id,
            clinical_event_id=event_id,
            prescribed_by_user_id=actor_id,
            status="issued",
            issued_at=now,
            notes="Synthetic prescription.",
        )
        session.add(prescription)
        session.flush()
        session.add(
            PrescriptionMedication(
                prescription_id=prescription.id,
                medication_id=medication.id,
                name=medication.name,
                dosage=medication.dosage,
                schedule=medication.schedule,
                start_date=date(2026, 7, 25),
                end_date=date(2026, 8, 1),
                metadata_json={"data_class": "wholly_synthetic"},
            )
        )
        plan = RecoveryPlan(
            patient_id=patient_id,
            doctor_id=doctor.id,
            clinical_event_id=event_id,
            title="Synthetic recovery plan",
            instructions="Synthetic recovery instructions.",
            status="active",
            review_status="approved",
            safety_label="synthetic_only",
        )
        session.add(plan)
        session.flush()
        task = RecoveryTask(
            plan_id=plan.id,
            patient_id=patient_id,
            medication_id=medication.id,
            category="medication",
            title="Take synthetic medicine",
            detail="Synthetic adherence task.",
            due_label="Today",
            notification_time="09:00",
            sort_order=1,
        )
        session.add(task)
        session.flush()
        session.add(
            RecoveryTaskCompletion(
                task_id=task.id,
                patient_id=patient_id,
                actor_user_id=patient_user_id,
                completed_at=now,
            )
        )
        service = ClinicalService(
            patient_id=patient_id,
            clinical_event_id=event_id,
            category="laboratory",
            name="Synthetic laboratory panel",
            service_subtype="synthetic_panel",
            service_code="SYN-LAB-001",
            ordered_by_doctor_id=doctor.id,
            performing_provider_name="Synthetic provider",
            status="completed",
            ordered_at=now - timedelta(days=1),
            performed_at=now,
            indication_summary="Synthetic indication.",
        )
        session.add(service)
        session.flush()
        session.add_all(
            [
                CareCostItem(
                    patient_id=patient_id,
                    clinical_event_id=event_id,
                    created_by_user_id=actor_id,
                    clinical_service_id=service.id,
                    item_type="laboratory",
                    label="Synthetic laboratory panel",
                    service_date=date(2026, 7, 25),
                    status="completed",
                    pricing_state="final",
                    quantity=1,
                    currency="CNY",
                    actual_cost_minor=2400,
                    payer_requested_minor=1800,
                    patient_responsibility_minor=600,
                    ai_review_status="not_evaluated",
                ),
                ConsultationRequest(
                    patient_id=patient_id,
                    clinical_event_id=event_id,
                    clinical_service_id=None,
                    requested_by_user_id=actor_id,
                    specialty="Synthetic rehabilitation",
                    question_summary="Synthetic follow-up question.",
                    priority="routine",
                    status="completed",
                    safety_label="synthetic_only",
                ),
                MedicalImagingAsset(
                    patient_id=patient_id,
                    clinical_event_id=event_id,
                    clinical_service_id=None,
                    uploaded_by_user_id=actor_id,
                    reviewed_by_user_id=actor_id,
                    storage_provider="tencent_cos",
                    content_type="image/png",
                    file_extension=".png",
                    size_bytes=128,
                    uploaded_size_bytes=128,
                    object_key=f"synthetic/{uuid.uuid4()}.png",
                    upload_status="uploaded",
                    review_status="reviewed",
                    finding_summary="Synthetic manual imaging finding.",
                    measurement_summary="Synthetic measurement.",
                    observed_at=now,
                    treatment_relevance_date=date(2026, 7, 25),
                    expires_at=now + timedelta(hours=1),
                    uploaded_at=now,
                    reviewed_at=now,
                ),
            ]
        )
        session.flush()

        snapshot = build_cost_estimation_fact_snapshot(
            session,
            patient_id=patient_id,
            clinical_event_id=event_id,
        )
        categories = {item["category"] for item in snapshot["facts_used"]}
        assert {
            "symptoms",
            "medical_history",
            "allergy",
            "chronic_condition",
            "medical_record",
            "doctor_confirmed_finding",
            "imaging",
            "medication",
            "prescription",
            "recovery_progress",
            "consultation",
            "clinical_service",
            "cost",
        } <= categories
        assert any(
            item["reason"] == "patient_wide_record_has_no_clinical_event_binding"
            for item in snapshot["facts_not_used"]
        )
        assert any(
            item["category"] == "ai_imaging_observation_draft" for item in snapshot["missing_facts"]
        )
        payer = serialize_cost_fact_snapshot(snapshot, role="payer")
        payer_symptom = next(item for item in payer["facts_used"] if item["category"] == "symptoms")
        assert payer_symptom["value"]["detail_withheld"] is True
        doctor_view = serialize_cost_fact_snapshot(snapshot, role="doctor")
        assert doctor_view["snapshot_checksum_sha256"] == snapshot["snapshot_checksum_sha256"]

        with pytest.raises(CostFactScopeError):
            build_cost_estimation_fact_snapshot(
                session,
                patient_id=unrelated_patient_id,
                clinical_event_id=event_id,
            )


def test_malformed_schema_retries_once_then_persists_invalid(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="malformed")
    _enable(settings, monkeypatch)

    def malformed(output):
        output.pop("items")

    provider = StubProvider([malformed, malformed])
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-malformed-001",
        )
        session.commit()
        assert generated.request.lifecycle_state == "invalid"
        assert generated.request.validation_reason_codes_json == ["malformed_schema"]
        assert generated.result.candidate_json["artifact_type"] == "fixed_safe_fallback"
    assert provider.calls == 2


@pytest.mark.parametrize(
    ("field", "replacement", "reason"),
    [
        ("service_code", "HALLUCINATED-CODE", "unsupported_candidate_item"),
        ("amount_low_minor", 999999, "unsupported_candidate_item"),
        ("unit", "invented-unit", "unsupported_candidate_item"),
    ],
)
def test_hallucinated_item_fields_are_rejected(
    client, settings, monkeypatch, field, replacement, reason
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix=field)
    _enable(settings, monkeypatch)

    def mutate(output):
        output["items"][0][field] = replacement

    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider([mutate]),
            key=f"candidate-hallucination-{field}",
        )
        session.commit()
    assert generated.request.lifecycle_state == "invalid"
    assert reason in generated.request.validation_reason_codes_json


def test_wrong_currency_and_unreconciled_total_are_rejected(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="currency-total")
    _enable(settings, monkeypatch)

    def mutate(output):
        output["currency"] = "USD"
        output["total_high_minor"] += 1

    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider([mutate]),
            key="candidate-currency-total-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "invalid"
    assert "candidate_currency_mismatch" in generated.request.validation_reason_codes_json
    assert "unreconciled_candidate_total" in generated.request.validation_reason_codes_json


def test_release_checksum_drift_in_output_is_rejected(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="checksum")
    _enable(settings, monkeypatch)

    def mutate(output):
        output["release_lineage"][0]["payload_checksum_sha256"] = "f" * 64

    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider([mutate]),
            key="candidate-checksum-drift-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "invalid"
    assert "release_or_checksum_drift" in generated.request.validation_reason_codes_json


def test_unadmitted_assumption_is_rejected(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="assumption")
    _enable(settings, monkeypatch)

    def mutate(output):
        output["assumptions"].append("Invented clinical applicability assumption.")

    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider([mutate]),
            key="candidate-assumption-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "invalid"
    assert "assumption_not_admitted" in generated.request.validation_reason_codes_json


def test_stale_release_is_suppressed_without_provider_call(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="stale")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(
            session,
            next_review_on=date(2026, 7, 24),
            activate_on=date(2026, 7, 23),
        )
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-stale-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "suppressed"
    assert "stale_reference_release" in generated.request.validation_reason_codes_json
    assert provider.calls == 0


def test_provider_transmission_denial_is_suppressed(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="rights")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(
            session,
            version="rights-blocked-v1",
            provider_transmission_allowed=False,
        )
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-rights-denied-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "suppressed"
    assert generated.request.validation_outcome == "rights_denied"
    assert provider.calls == 0


def test_timeout_has_one_bounded_retry_and_safe_fallback(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="timeout")
    _enable(settings, monkeypatch)
    timeout = ExpectedCareProviderError("timeout", retryable=True)
    provider = StubProvider([timeout, timeout])
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-timeout-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "provider_unavailable"
    assert generated.result.candidate_json["manual_workflow_available"] is True
    assert generated.result.candidate_json["pending_cost_workflow_available"] is True
    assert provider.calls == 2


def test_quota_exhaustion_is_non_retrying_and_uses_safe_fallback(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="quota")
    _enable(settings, monkeypatch)
    provider = StubProvider([ExpectedCareProviderError("quota", retryable=False)])
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-quota-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "provider_unavailable"
    assert generated.request.validation_reason_codes_json == ["quota"]
    assert generated.result.candidate_json["artifact_type"] == "fixed_safe_fallback"
    assert provider.calls == 1


def test_budget_exhaustion_prevents_provider_call(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="budget")
    _enable(settings, monkeypatch)
    monkeypatch.setattr(settings, "expected_care_max_cost_microunits", 1)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-budget-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "provider_unavailable"
    assert generated.request.validation_reason_codes_json == ["budget_exhausted"]
    assert provider.calls == 0


def test_kill_switch_prevents_provider_call(client, settings) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="kill")
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-kill-switch-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "suppressed"
    assert generated.request.validation_reason_codes_json == ["kill_switch_disabled"]
    assert provider.calls == 0


def test_unconfigured_provider_fails_without_using_deepseek_transport(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="provider-config")
    _enable(settings, monkeypatch)
    monkeypatch.setattr(settings, "expected_care_provider", "unconfigured-provider")
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=None,
            key="candidate-provider-config-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "provider_unavailable"
    assert generated.request.validation_reason_codes_json == ["unsupported_provider_configuration"]


def test_idempotent_duplicate_returns_same_immutable_result(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="idempotent")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        first = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-idempotent-001",
        )
        session.commit()
        second = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-idempotent-001",
        )
        session.commit()
        assert first.request.id == second.request.id
        assert first.result.id == second.result.id
        assert second.idempotent_replay is True
        assert session.scalar(select(func.count()).select_from(ExpectedCareCandidateRequest)) == 1
    assert provider.calls == 1


def test_idempotency_key_rejects_changed_request(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="conflict")
    _enable(settings, monkeypatch)
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider(),
            key="candidate-conflict-001",
        )
        session.commit()
        changed = EvaluationContext(**{**_context().__dict__, "patient_age": 43})
        with pytest.raises(ExpectedCareCandidateConflict, match="idempotency_payload_conflict"):
            generate_expected_care_candidate(
                session,
                actor_user_id=actor_id,
                patient_id=patient_id,
                clinical_event_id=event_id,
                selection=synthetic_active_selection(),
                request=EvaluationRequest(context=changed),
                idempotency_key="candidate-conflict-001",
                settings=settings,
                provider=StubProvider(),
            )


def test_regeneration_appends_predecessor_lineage(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="lineage")
    _enable(settings, monkeypatch)
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        first = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider(),
            key="candidate-lineage-001",
        )
        session.commit()
        second = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider(),
            key="candidate-lineage-002",
            predecessor_request_id=first.request.id,
        )
        session.commit()
        assert second.request.predecessor_request_id == first.request.id
        assert second.request.id != first.request.id
        assert session.scalar(select(func.count()).select_from(ExpectedCareCandidateResult)) == 2


def test_cross_patient_access_fails_neutrally(client, settings, monkeypatch) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="owner")
    other_actor_id, _, _ = _connected_case(client, suffix="other")
    _enable(settings, monkeypatch)
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        with pytest.raises(CareReferenceAuthorizationError, match="not_found"):
            _generate(
                session,
                actor_id=other_actor_id,
                patient_id=patient_id,
                event_id=event_id,
                settings=settings,
                provider=StubProvider(),
                key="candidate-cross-patient-001",
            )
        assert session.scalar(select(func.count()).select_from(ExpectedCareCandidateRequest)) == 0
    assert actor_id != other_actor_id


def test_attempts_results_and_requests_are_database_immutable(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="immutable")
    _enable(settings, monkeypatch)
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=StubProvider(),
            key="candidate-immutable-001",
        )
        session.commit()
        with pytest.raises(DBAPIError):
            session.execute(
                update(ExpectedCareCandidateRequest)
                .where(ExpectedCareCandidateRequest.id == generated.request.id)
                .values(lifecycle_state="doctor_reviewed")
            )
            session.commit()
        session.rollback()
        stored = session.get(ExpectedCareCandidateRequest, generated.request.id)
        assert stored is not None
        assert stored.lifecycle_state == "generated_pending_review"


def test_no_default_provider_or_network_is_used_by_stub_suite(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="network-proof")
    _enable(settings, monkeypatch)

    def forbidden_urlopen(*args, **kwargs):
        del args, kwargs
        raise AssertionError("external request attempted")

    monkeypatch.setattr("urllib.request.urlopen", forbidden_urlopen)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        generated = _generate(
            session,
            actor_id=actor_id,
            patient_id=patient_id,
            event_id=event_id,
            settings=settings,
            provider=provider,
            key="candidate-network-proof-001",
        )
        session.commit()
    assert generated.request.lifecycle_state == "generated_pending_review"
    assert provider.calls == 1


def test_unrelated_synthetic_laboratory_scenario_uses_same_candidate_contract(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="laboratory")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_laboratory_reference_bundle(session)
        generated = generate_expected_care_candidate(
            session,
            actor_user_id=actor_id,
            patient_id=patient_id,
            clinical_event_id=event_id,
            selection=synthetic_laboratory_selection(),
            request=EvaluationRequest(context=_context()),
            idempotency_key="candidate-laboratory-001",
            settings=settings,
            provider=provider,
        )
        session.commit()
    assert generated.request.lifecycle_state == "generated_pending_review"
    assert generated.result.total_low_minor == 700
    assert generated.result.total_high_minor == 900
    assert generated.result.candidate_json["items"][0]["category"] == "laboratory"


def test_optional_payer_request_is_authorized_without_transmitting_payer_notes(
    client, settings, monkeypatch
) -> None:
    actor_id, patient_id, event_id = _connected_case(client, suffix="payer-scope")
    _enable(settings, monkeypatch)
    provider = StubProvider()
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        actor = session.get(User, actor_id)
        assert actor is not None and actor.doctor_profile is not None
        organization = PayerOrganization(
            name="Synthetic Candidate Payer",
            organization_type="public_payer",
            jurisdiction_code="CN",
            verification_status="synthetic_only",
        )
        session.add(organization)
        session.flush()
        payer_request = PayerRequest(
            clinical_event_id=event_id,
            patient_id=patient_id,
            doctor_id=actor.doctor_profile.id,
            payer_organization_id=organization.id,
            status="submitted",
            currency="CNY",
            requested_total_minor=3000,
            doctor_summary="PAYER-PRIVATE-NOTE-MUST-NOT-TRANSMIT",
            ai_review_status="not_evaluated",
        )
        session.add(payer_request)
        session.flush()
        generated = generate_expected_care_candidate(
            session,
            actor_user_id=actor_id,
            patient_id=patient_id,
            clinical_event_id=event_id,
            payer_request_id=payer_request.id,
            selection=synthetic_active_selection(),
            request=EvaluationRequest(context=_context()),
            idempotency_key="candidate-payer-scope-001",
            settings=settings,
            provider=provider,
        )
        session.commit()
    assert generated.request.payer_request_id == payer_request.id
    assert generated.request.lifecycle_state == "generated_pending_review"
    assert "PAYER-PRIVATE-NOTE-MUST-NOT-TRANSMIT" not in str(provider.inputs[0])
