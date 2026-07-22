import hashlib

from fastapi.testclient import TestClient

from tests.helpers import auth_header, register


def _register_payer(
    client: TestClient, *, email: str, organization_name: str
) -> tuple[dict, dict[str, str]]:
    digest = hashlib.sha1(email.encode("utf-8")).hexdigest()[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": f"+1666{int(digest, 16) % 10_000_000:07d}",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "Lin Reviewer",
                "organization_name": organization_name,
                "title": "Medical expenditure reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    return payload, auth_header(payload["access_token"])


def _connected_event(
    client: TestClient,
) -> tuple[dict[str, str], dict[str, str], str, str]:
    patient = register(
        client,
        email="cost.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email="cost.doctor@example.com",
        password="Doctor9!",
        role="doctor",
    )
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    patient_id = care["patient"]["patient_id"]
    client.post(
        "/api/v1/patients/connect",
        headers=doctor_headers,
        json={"patient_code": care["patient"]["synthetic_identifier"]},
    )
    event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Respiratory follow-up",
            "chief_complaint": "Persistent cough follow-up",
            "symptom_summary": "Doctor-recorded clinical context.",
            "diagnosis_summary": "Clinician-owned provisional diagnosis.",
            "status": "active",
        },
    )
    assert event.status_code == 200
    return patient_headers, doctor_headers, patient_id, event.json()["id"]


def test_three_role_care_cost_and_human_review_workflow(client: TestClient) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    _, payer_headers = _register_payer(
        client,
        email="payer.review@example.com",
        organization_name="Synthetic Municipal Medical Insurance",
    )

    organizations = client.get("/api/v1/payer-organizations", headers=doctor_headers)
    assert organizations.status_code == 200
    organization_id = organizations.json()[0]["id"]

    item_payloads = [
        {
            "item_type": "imaging",
            "label": "Chest CT review",
            "service_date": "2026-07-23",
            "status": "completed",
            "quantity": 1,
            "currency": "CNY",
            "actual_cost_minor": 68000,
            "payer_requested_minor": 50000,
            "patient_responsibility_minor": 18000,
            "notes": "Completed after clinician review.",
        },
        {
            "item_type": "follow_up",
            "label": "Respiratory clinic follow-up",
            "service_date": "2026-08-02",
            "status": "scheduled",
            "quantity": 1,
            "currency": "CNY",
            "actual_cost_minor": 12000,
            "payer_requested_minor": 8000,
            "patient_responsibility_minor": 4000,
        },
    ]
    item_ids: list[str] = []
    for payload in item_payloads:
        response = client.post(
            f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items",
            headers=doctor_headers,
            json=payload,
        )
        assert response.status_code == 201, response.text
        assert response.json()["ai_review_status"] == "not_evaluated"
        assert response.json()["ai_review_score"] is None
        item_ids.append(response.json()["id"])

    patient_ledger = client.get("/api/v1/patient/me/care-costs", headers=patient_headers)
    assert patient_ledger.status_code == 200
    assert patient_ledger.json()["actual_total_minor"] == 80000
    assert patient_ledger.json()["payer_requested_total_minor"] == 58000
    assert patient_ledger.json()["patient_responsibility_total_minor"] == 22000
    assert len(patient_ledger.json()["events"][0]["items"]) == 2

    submitted = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": item_ids,
            "doctor_summary": (
                "Please review the completed imaging and scheduled follow-up in the "
                "context of this clinician-managed care episode."
            ),
        },
    )
    assert submitted.status_code == 201, submitted.text
    request_id = submitted.json()["id"]
    assert submitted.json()["requested_total_minor"] == 58000
    assert submitted.json()["ai_review_status"] == "not_evaluated"

    payer_queue = client.get("/api/v1/payer/me/requests", headers=payer_headers)
    assert payer_queue.status_code == 200
    assert [item["id"] for item in payer_queue.json()["items"]] == [request_id]
    assert len(payer_queue.json()["items"][0]["lines"]) == 2

    review = client.post(
        f"/api/v1/payer/me/requests/{request_id}/reviews",
        headers=payer_headers,
        json={
            "action": "request_clarification",
            "reason_code": "documentation_needed",
            "note": "Attach the imaging interpretation before human resolution.",
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "clarification_requested"
    assert review.json()["reviews"][0]["note"].startswith("Attach")

    patient_requests = client.get("/api/v1/patient/me/payer-requests", headers=patient_headers)
    assert patient_requests.status_code == 200
    patient_view = patient_requests.json()["items"][0]
    assert patient_view["status"] == "clarification_requested"
    assert patient_view["reviews"][0]["note"] is None

    dashboard = client.get("/api/v1/payer/me/dashboard", headers=payer_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["open_requests"] == 1
    assert dashboard.json()["clarification_requests"] == 1
    assert dashboard.json()["pending_requested_total_minor"] == 58000


def test_care_cost_authorization_and_validation_fail_closed(client: TestClient) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    other_patient = register(
        client,
        email="other.cost.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    other_headers = auth_header(other_patient["access_token"])

    invalid_totals = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items",
        headers=doctor_headers,
        json={
            "item_type": "medication",
            "label": "Prescription course",
            "service_date": "2026-07-23",
            "actual_cost_minor": 1000,
            "payer_requested_minor": 900,
            "patient_responsibility_minor": 200,
        },
    )
    assert invalid_totals.status_code == 422

    unrelated_ledger = client.get("/api/v1/patient/me/care-costs", headers=other_headers)
    assert unrelated_ledger.status_code == 200
    assert unrelated_ledger.json()["events"] == []

    patient_write = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items",
        headers=patient_headers,
        json={
            "item_type": "medication",
            "label": "Prescription course",
            "service_date": "2026-07-23",
        },
    )
    assert patient_write.status_code == 404

    payer_registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "missing.payer.profile@example.com",
            "phone_number": "+16660000001",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
        },
    )
    assert payer_registration.status_code == 422
