from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi.testclient import TestClient

from tests.helpers import auth_header, register
from tests.test_care_cost_workflow import _connected_event


def _line(name: str, quantity: int = 10) -> dict[str, object]:
    return {
        "name": name,
        "dosage": "10 mg tablet",
        "schedule": "Take once daily with food",
        "formulation_strength": "tablet 10 mg",
        "route": "oral",
        "recorded_directions": "Take once daily with food",
        "quantity": quantity,
        "duration_days": quantity,
        "pricing_state": "pending_cost",
        "currency": "CNY",
    }


def test_multi_line_prescription_is_idempotent_immutable_and_superseded(
    client: TestClient,
) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    payload = {
        "clinical_event_id": event_id,
        "status": "finalized",
        "notes": "Synthetic two-line prescription.",
        "idempotency_key": "prescription-two-lines-001",
        "medications": [_line("Synthetic medicine A"), _line("Synthetic medicine B", 5)],
    }

    first = client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=doctor_headers,
        json=payload,
    )
    retry = client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=doctor_headers,
        json=payload,
    )
    assert first.status_code == 200, first.text
    assert retry.status_code == 200
    assert retry.json()["id"] == first.json()["id"]
    assert [line["name"] for line in first.json()["medications"]] == [
        "Synthetic medicine A",
        "Synthetic medicine B",
    ]

    mutation = client.put(
        f"/api/v1/patients/{patient_id}/prescriptions/{first.json()['id']}",
        headers=doctor_headers,
        json={**payload, "notes": "Silent mutation attempt."},
    )
    deletion = client.delete(
        f"/api/v1/patients/{patient_id}/prescriptions/{first.json()['id']}",
        headers=doctor_headers,
    )
    assert mutation.status_code == 409
    assert deletion.status_code == 409

    replacement_payload = {
        **payload,
        "idempotency_key": "prescription-two-lines-002",
        "supersedes_prescription_id": first.json()["id"],
        "notes": "Explicit replacement.",
    }
    replacement = client.post(
        f"/api/v1/patients/{patient_id}/prescriptions",
        headers=doctor_headers,
        json=replacement_payload,
    )
    assert replacement.status_code == 200, replacement.text
    assert replacement.json()["supersedes_prescription_id"] == first.json()["id"]
    assert replacement.json()["version"] == 2

    patient_readback = client.get(
        f"/api/v1/patients/{patient_id}/prescriptions", headers=patient_headers
    )
    assert patient_readback.status_code == 200
    assert len(patient_readback.json()["items"]) == 2


def test_same_key_concurrent_prescription_submission_creates_one_version(
    client: TestClient,
) -> None:
    _, doctor_headers, patient_id, event_id = _connected_event(client)
    payload = {
        "clinical_event_id": event_id,
        "status": "finalized",
        "idempotency_key": "prescription-concurrent-001",
        "medications": [_line("Synthetic concurrent medicine")],
    }

    def submit() -> Any:
        return client.post(
            f"/api/v1/patients/{patient_id}/prescriptions",
            headers=doctor_headers,
            json=payload,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: submit(), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    assert len({response.json()["id"] for response in responses}) == 1
    history = client.get(f"/api/v1/patients/{patient_id}/prescriptions", headers=doctor_headers)
    assert len(history.json()["items"]) == 1


def test_structured_recovery_calendar_is_idempotent_and_published_immutable(
    client: TestClient,
) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    reviewer = register(
        client,
        email="calendar.reviewer@example.com",
        password="Doctor9!",
        role="doctor",
    )
    reviewer_headers = auth_header(reviewer["access_token"])
    patient_code = client.get("/api/v1/patient/me/care", headers=patient_headers).json()["patient"][
        "synthetic_identifier"
    ]
    client.post(
        "/api/v1/patients/connect",
        headers=reviewer_headers,
        json={"patient_code": patient_code},
    )
    contacts = client.get("/api/v1/patient/me/contacts", headers=patient_headers).json()["items"]
    pending = next(
        item for item in contacts if item["relationship_status"] == "pending_patient_approval"
    )
    client.post(
        f"/api/v1/patient/me/doctor-relationships/{pending['relationship_id']}/approve",
        headers=patient_headers,
        json={"expected_version": pending["request_version"]},
    )
    task = {
        "category": "exercise",
        "title": "Supported range-of-motion session",
        "detail": "Complete the clinician-recorded movement sequence.",
        "due_label": "Every morning",
        "frequency": "daily",
        "schedule": "09:00",
        "duration": "15 minutes",
        "responsible_person": "patient",
        "completion_criteria": "Session recorded as complete",
        "reminder": {"enabled": True, "time": "08:45"},
    }
    payload = {
        "clinical_event_id": event_id,
        "title": "Structured joint recovery calendar",
        "indication": "Synthetic post-injury recovery support",
        "start_date": "2026-08-03",
        "instructions": "Follow the calendar and contact the care team for concerns.",
        "idempotency_key": "recovery-calendar-001",
        "phases": [
            {
                "name": "Protection and swelling control",
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
                "goals": "Protect the joint and reduce swelling.",
                "instructions": "Use only clinician-approved activity.",
                "precautions": "Avoid painful loading.",
                "progression_criteria": "Swelling improves and activity is tolerated.",
                "hold_escalation_criteria": "New numbness, deformity, or worsening pain.",
                "review_checkpoint": "Clinician review on day seven.",
                "tasks": [task],
            }
        ],
    }
    created = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans",
        headers=doctor_headers,
        json=payload,
    )
    retry = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans",
        headers=doctor_headers,
        json=payload,
    )
    assert created.status_code == 200, created.text
    assert retry.json()["plan_id"] == created.json()["plan_id"]
    assert created.json()["phases"][0]["tasks"][0]["frequency"] == "daily"

    plan_id = created.json()["plan_id"]
    submitted = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/submit-review",
        headers=doctor_headers,
        json={
            "reviewer_doctor_id": pending["doctor_id"],
            "expected_version": created.json()["version"],
        },
    )
    approved = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/approve",
        headers=reviewer_headers,
        json={"expected_version": created.json()["version"]},
    )
    assert submitted.status_code == 200
    assert approved.status_code == 200
    activated = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate",
        headers=doctor_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["published_at"] is not None
    immutable = client.put(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan_id}",
        headers=doctor_headers,
        json=payload,
    )
    assert immutable.status_code == 409


def test_service_and_consultation_companions_are_source_unique_and_allow_pending_cost(
    client: TestClient,
) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    service_payload = {
        "clinical_event_id": event_id,
        "category": "surgery",
        "name": "Synthetic arthroscopic procedure",
        "service_subtype": "arthroscopy",
        "service_date": "2026-08-05",
        "performing_provider_name": "Synthetic Orthopaedic Team",
        "facility_name": "Synthetic Clinical Center",
        "status": "planned",
        "indication_summary": "Clinician-recorded synthetic indication.",
        "quantity": 1,
        "unit": "procedure",
        "documentation_state": "pending",
        "provenance": {"source": "doctor_entry"},
        "idempotency_key": "clinical-service-surgery-001",
        "financial": {"pricing_state": "pending_cost"},
    }
    first = client.post(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=doctor_headers,
        json=service_payload,
    )
    retry = client.post(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=doctor_headers,
        json=service_payload,
    )
    assert first.status_code == 201, first.text
    assert retry.status_code == 201
    assert retry.json()["id"] == first.json()["id"]

    referral = client.post(
        "/api/v1/consultations",
        headers=doctor_headers,
        json={
            "patient_id": patient_id,
            "clinical_event_id": event_id,
            "specialty": "Orthopaedic specialist",
            "question_summary": "Request specialist review of the synthetic injury.",
            "priority": "soon",
            "consultation_type": "specialist_referral",
        },
    )
    assert referral.status_code == 200, referral.text
    assert referral.json()["clinical_service_id"] is None

    priced_referral = client.post(
        "/api/v1/consultations",
        headers=doctor_headers,
        json={
            "patient_id": patient_id,
            "clinical_event_id": event_id,
            "specialty": "Orthopaedic specialist",
            "question_summary": "Request a second specialist review for billing check.",
            "priority": "routine",
            "consultation_type": "specialist_referral",
            "financial": {"pricing_state": "pending_cost"},
        },
    )
    assert priced_referral.status_code == 422
    assert priced_referral.json()["error"]["details"][0]["field"] == "consultation_type"

    consultation = client.post(
        "/api/v1/consultations",
        headers=doctor_headers,
        json={
            "patient_id": patient_id,
            "clinical_event_id": event_id,
            "specialty": "Sports medicine",
            "question_summary": "Assess the synthetic joint recovery timeline.",
            "priority": "soon",
            "consultation_type": "in_person",
            "status": "completed",
            "clinician_provider": "Synthetic Sports Clinician",
            "service_date": "2026-08-02",
            "reason_indication": "Acute synthetic joint injury follow-up.",
            "outcome_summary": {"summary": "Further evaluation documented."},
            "follow_up_requirement": "Review in one week.",
            "quantity": 1,
            "idempotency_key": "consultation-completed-001",
            "financial": {"pricing_state": "pending_cost"},
        },
    )
    assert consultation.status_code == 200, consultation.text
    assert consultation.json()["outcome_summary"]["summary"]

    ledger = client.get("/api/v1/patient/me/care-costs", headers=patient_headers)
    assert ledger.status_code == 200
    pending = [
        item
        for event in ledger.json()["events"]
        for item in event["items"]
        if item["pricing_state"] == "pending_cost"
    ]
    assert len(pending) == 2
    assert all(not item["submission_eligible"] for item in pending)
