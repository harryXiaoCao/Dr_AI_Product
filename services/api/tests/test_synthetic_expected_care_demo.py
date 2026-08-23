import hashlib

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.expected_care_candidates import DeepSeekExpectedCareProvider
from app.models import (
    ClinicalEvent,
    ClinicalService,
    ExpectedCareCandidateRequest,
    ExpectedCareClinicianResponse,
    ExpectedCarePublishedBaseline,
    PayerRequest,
)
from app.synthetic_expected_care_demo import (
    DEMO_FIXTURE_KEY,
    DEMO_PRODUCT_PATH_VERSION,
    bootstrap_synthetic_expected_care_demo,
)
from tests.helpers import auth_header, register


def _payer(client: TestClient, *, email: str) -> tuple[dict, dict[str, str]]:
    digest = hashlib.sha1(email.encode()).hexdigest()[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": f"+1777{int(digest, 16) % 10_000_000:07d}",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "Synthetic Slice E Reviewer",
                "organization_name": "Synthetic Slice E Payer",
                "title": "Synthetic reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    return payload, auth_header(payload["access_token"])


def test_demo_bootstrap_is_idempotent_role_visible_and_provider_free(
    client: TestClient, settings, monkeypatch
) -> None:
    patient_email = "slice.e.demo.patient@example.com"
    doctor_email = "slice.e.demo.doctor@example.com"
    payer_email = "slice.e.demo.payer@example.com"
    patient = register(
        client,
        email=patient_email,
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email=doctor_email,
        password="Doctor9!",
        role="doctor",
    )
    _, payer_headers = _payer(client, email=payer_email)
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    assert (
        client.post(
            "/api/v1/patients/connect",
            headers=doctor_headers,
            json={"patient_code": care["patient"]["synthetic_identifier"]},
        ).status_code
        == 200
    )

    def external_provider_forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("external provider must not be called")

    monkeypatch.setattr(
        DeepSeekExpectedCareProvider,
        "generate",
        external_provider_forbidden,
    )
    with SessionLocal() as db:
        first = bootstrap_synthetic_expected_care_demo(
            db,
            settings,
            doctor_email=doctor_email,
            patient_email=patient_email,
            payer_email=payer_email,
        )
    with SessionLocal() as db:
        second = bootstrap_synthetic_expected_care_demo(
            db,
            settings,
            doctor_email=doctor_email,
            patient_email=patient_email,
            payer_email=payer_email,
        )
        assert first == second
        assert (
            db.scalar(
                select(func.count())
                .select_from(ExpectedCareCandidateRequest)
                .where(ExpectedCareCandidateRequest.clinical_event_id == first.clinical_event_id)
            )
            == 3
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(ExpectedCarePublishedBaseline)
                .where(
                    ExpectedCarePublishedBaseline.clinical_event_id == first.clinical_event_id,
                    ExpectedCarePublishedBaseline.lifecycle_state == "validated_baseline_published",
                )
            )
            == 3
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(ExpectedCareClinicianResponse)
                .where(
                    ExpectedCareClinicianResponse.clinical_event_id == first.clinical_event_id,
                    ExpectedCareClinicianResponse.action == "concur",
                )
            )
            == 2
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(ClinicalService)
                .where(ClinicalService.clinical_event_id == first.clinical_event_id)
            )
            >= 6
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(ClinicalEvent)
                .where(ClinicalEvent.metadata_json["fixture_key"].astext == DEMO_FIXTURE_KEY)
            )
            == 1
        )
        fixture_event = db.get(ClinicalEvent, first.clinical_event_id)
        assert fixture_event is not None
        assert (
            fixture_event.metadata_json["product_path_fixture_version"] == DEMO_PRODUCT_PATH_VERSION
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(PayerRequest)
                .where(PayerRequest.clinical_event_id == first.clinical_event_id)
            )
            == 2
        )

    doctor_items = client.get(
        (
            f"/api/v1/patients/{first.patient_id}/clinical-events/"
            f"{first.clinical_event_id}/expected-care/candidates"
        ),
        headers=doctor_headers,
    )
    assert doctor_items.status_code == 200
    assert {item["state"] for item in doctor_items.json()["items"]} == {
        "validated_baseline_published"
    }
    assert {item["latest_clinician_position"] for item in doctor_items.json()["items"]} == {
        "not_recorded",
        "concur",
    }
    combined_candidate = next(
        item
        for item in doctor_items.json()["items"]
        if item["candidate_result_id"] == str(first.combined_candidate_result_id)
    )
    doctor_snapshot = combined_candidate["cost_estimation_fact_snapshot"]
    doctor_used = {item["category"] for item in doctor_snapshot["facts_used"]}
    assert {
        "symptoms",
        "medical_history",
        "doctor_confirmed_finding",
        "imaging",
        "medication",
        "prescription",
        "recovery_progress",
        "consultation",
        "clinical_service",
        "cost",
    } <= doctor_used
    assert {item["category"] for item in doctor_snapshot["facts_not_used"]} >= {
        "medical_record",
        "doctor_note",
    }
    assert {item["category"] for item in doctor_snapshot["missing_facts"]} == {
        "ai_imaging_observation_draft"
    }

    doctor_care = client.get(
        f"/api/v1/patients/{first.patient_id}/care",
        headers=doctor_headers,
    )
    assert doctor_care.status_code == 200, doctor_care.text
    doctor_care_body = doctor_care.json()
    fixture_event = next(
        item
        for item in doctor_care_body["clinical_events"]
        if item["id"] == str(first.clinical_event_id)
    )
    assert "not an AI diagnosis" in fixture_event["diagnosis_summary"]
    assert len(doctor_care_body["clinical_services"]) >= 6
    assert {item["category"] for item in doctor_care_body["clinical_services"]} >= {
        "rehabilitation",
        "laboratory",
        "imaging",
        "consultation",
        "treatment",
    }
    assert any(
        item["finding_summary"] and "no Vision model was invoked" in item["finding_summary"]
        for item in doctor_care_body["imaging_assets"]
    )
    assert doctor_care_body["prescriptions"]
    assert doctor_care_body["medications"]
    assert doctor_care_body["recovery_plans"][0]["tasks"][0]["is_completed"] is True
    assert doctor_care_body["diagnoses"]
    assert doctor_care_body["records"]
    assert doctor_care_body["doctor_notes"]

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200, patient_care.text
    patient_care_body = patient_care.json()
    assert len(patient_care_body["clinical_services"]) >= 6
    assert patient_care_body["imaging_assets"][0]["finding_summary"]
    assert patient_care_body["prescriptions"]
    assert patient_care_body["medications"]
    assert patient_care_body["recovery_plans"]
    assert patient_care_body["doctor_notes"] == []

    consultations = client.get("/api/v1/consultations", headers=doctor_headers)
    assert consultations.status_code == 200, consultations.text
    assert any(
        item["clinical_event_id"] == str(first.clinical_event_id) and item["status"] == "completed"
        for item in consultations.json()["items"]
    )

    patient_envelope = client.get(
        (f"/api/v1/patient/clinical-events/{first.clinical_event_id}/expected-care-envelope"),
        headers=patient_headers,
    )
    assert patient_envelope.status_code == 200
    assert patient_envelope.json()["state"] == "validated_baseline_published"
    assert "release_lineage" not in patient_envelope.json()
    assert patient_envelope.json()["baseline_id"] == str(first.combined_published_baseline_id)
    patient_snapshot = patient_envelope.json()["cost_estimation_fact_snapshot"]
    assert {item["category"] for item in patient_snapshot["facts_used"]} >= {
        "imaging",
        "prescription",
        "recovery_progress",
        "consultation",
        "cost",
    }
    payer_envelope = client.get(
        (f"/api/v1/payer/requests/{first.combined_payer_request_id}/expected-care-envelope"),
        headers=payer_headers,
    )
    assert payer_envelope.status_code == 200
    assert payer_envelope.json()["submitted_facts"]["payer_request_id"] == str(
        first.combined_payer_request_id
    )
    payer_snapshot = payer_envelope.json()["system_baseline"]["cost_estimation_fact_snapshot"]
    payer_symptoms = next(
        item for item in payer_snapshot["facts_used"] if item["category"] == "symptoms"
    )
    assert payer_symptoms["value"] == {
        "present": True,
        "detail_withheld": True,
        "withholding_reason": "minimum_necessary_payer_view",
    }

    payer_request = client.get(
        f"/api/v1/payer/me/requests/{first.combined_payer_request_id}",
        headers=payer_headers,
    )
    assert payer_request.status_code == 200, payer_request.text
    payer_request_body = payer_request.json()
    assert payer_request_body["status"] == "accepted"
    assert [item["action"] for item in payer_request_body["reviews"]] == [
        "request_clarification",
        "accept",
    ]
    assert payer_request_body["reviews"][0]["clarification_message"].startswith(
        "Please explain"
    )
    assert payer_request_body["reviews"][0]["note"].startswith("Wholly synthetic")
    assert payer_request_body["doctor_responses"][0]["response_type"] == "justification"
    assert payer_request_body["doctor_responses"][0]["comparison_id"] == str(
        first.combined_comparison_id
    )

    doctor_comparison = client.get(
        (
            f"/api/v1/patients/{first.patient_id}/clinical-events/"
            f"{first.clinical_event_id}/expected-care/comparisons/latest"
        ),
        headers=doctor_headers,
    )
    patient_comparison = client.get(
        (f"/api/v1/patient/clinical-events/{first.clinical_event_id}/expected-care-comparison"),
        headers=patient_headers,
    )
    payer_comparison = client.get(
        (f"/api/v1/payer/requests/{first.combined_payer_request_id}/expected-care-comparison"),
        headers=payer_headers,
    )
    for response in (doctor_comparison, patient_comparison, payer_comparison):
        assert response.status_code == 200, response.text
        assert response.json()["comparison_id"] == str(first.combined_comparison_id)
        assert response.json()["state"] == "comparison_published"

    explanation_routes = (
        (
            (
                f"/api/v1/patients/{first.patient_id}/clinical-events/"
                f"{first.clinical_event_id}/expected-care/comparisons/"
                f"{first.combined_comparison_id}/explanations/latest"
            ),
            doctor_headers,
        ),
        (
            (
                f"/api/v1/patient/clinical-events/{first.clinical_event_id}/"
                f"expected-care-comparisons/{first.combined_comparison_id}/"
                "explanations/latest"
            ),
            patient_headers,
        ),
        (
            (
                f"/api/v1/payer/requests/{first.combined_payer_request_id}/"
                f"expected-care-comparisons/{first.combined_comparison_id}/"
                "explanations/latest"
            ),
            payer_headers,
        ),
    )
    for role, (route, headers) in zip(
        ("doctor", "patient", "payer"), explanation_routes, strict=True
    ):
        response = client.get(route, headers=headers)
        assert response.status_code == 200, f"{role}: {response.text}"
        assert response.json()["display_mode"] == "structured_fallback"
        assert response.json()["artifact"]["reason_code"] == "kill_switch_or_release_gate"
