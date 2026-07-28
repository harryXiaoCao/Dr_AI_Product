import hashlib
import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.database import engine
from app.models import PayerMembership, PayerOrganization
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

    medication = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "name": "Respiratory medication course",
            "dosage": "10 mg",
            "schedule": "Once daily",
            "status": "active",
            "financial": {
                "pricing_state": "final",
                "service_date": "2026-07-23",
                "total_cost_minor": 68000,
                "payer_requested_minor": 50000,
                "patient_responsibility_minor": 18000,
            },
        },
    )
    assert medication.status_code == 200, medication.text
    consultation = client.post(
        "/api/v1/consultations",
        headers=doctor_headers,
        json={
            "patient_id": patient_id,
            "clinical_event_id": event_id,
            "specialty": "Respiratory medicine",
            "question_summary": "Review the follow-up plan and documented findings.",
            "priority": "routine",
            "financial": {
                "pricing_state": "estimated",
                "service_date": "2026-08-02",
                "total_cost_minor": 12000,
                "payer_requested_minor": 8000,
                "patient_responsibility_minor": 4000,
            },
        },
    )
    assert consultation.status_code == 200, consultation.text

    patient_ledger = client.get("/api/v1/patient/me/care-costs", headers=patient_headers)
    assert patient_ledger.status_code == 200
    assert patient_ledger.json()["actual_total_minor"] == 80000
    assert patient_ledger.json()["payer_requested_total_minor"] == 58000
    assert patient_ledger.json()["patient_responsibility_total_minor"] == 22000
    items = patient_ledger.json()["events"][0]["items"]
    assert len(items) == 2
    assert {item["source_type"] for item in items} == {"medication", "consultation"}
    assert all(item["submission_eligible"] for item in items)
    item_ids = [item["id"] for item in items]

    consultation_cost_update = client.put(
        (
            f"/api/v1/patients/{patient_id}/consultations/"
            f"{consultation.json()['consultation_id']}/financial"
        ),
        headers=doctor_headers,
        json={
            "pricing_state": "estimated",
            "service_date": "2026-08-02",
            "total_cost_minor": 12000,
            "payer_requested_minor": 8000,
            "patient_responsibility_minor": 4000,
        },
    )
    assert consultation_cost_update.status_code == 200, consultation_cost_update.text
    assert consultation_cost_update.json()["source_type"] == "consultation"
    assert (
        consultation_cost_update.json()["source_record_id"]
        == (consultation.json()["clinical_service_id"])
    )

    submitted = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": item_ids,
            "doctor_summary": (
                "Please review the medication product and scheduled consultation in "
                "the context of this clinician-managed care episode."
            ),
        },
    )
    assert submitted.status_code == 201, submitted.text
    request_id = submitted.json()["id"]
    assert submitted.json()["requested_total_minor"] == 58000
    assert submitted.json()["ai_review_status"] == "not_evaluated"
    assert {line["care_cost_item_id"] for line in submitted.json()["lines"]} == set(item_ids)

    source_edit = client.put(
        f"/api/v1/patients/{patient_id}/medications/{medication.json()['id']}",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "name": "Respiratory medication course updated",
            "dosage": "10 mg",
            "schedule": "Once daily",
            "status": "active",
            "financial": {
                "pricing_state": "final",
                "service_date": "2026-07-23",
                "total_cost_minor": 70000,
                "payer_requested_minor": 52000,
                "patient_responsibility_minor": 18000,
            },
        },
    )
    assert source_edit.status_code == 200, source_edit.text
    refreshed_ledger = client.get("/api/v1/patient/me/care-costs", headers=patient_headers).json()
    updated_item = next(
        item
        for item in refreshed_ledger["events"][0]["items"]
        if item["source_record_id"] == medication.json()["id"]
    )
    assert updated_item["label"].endswith("updated")
    assert updated_item["actual_cost_minor"] == 70000
    immutable_request = client.get(
        "/api/v1/patient/me/payer-requests", headers=patient_headers
    ).json()["items"][0]
    medication_snapshot = next(
        line
        for line in immutable_request["lines"]
        if line["care_cost_item_id"] == updated_item["id"]
    )
    assert medication_snapshot["label"] == "Respiratory medication course"
    assert medication_snapshot["actual_cost_minor"] == 68000

    duplicate_submission = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": [item_ids[0]],
            "doctor_summary": "A repeated source row must not create another snapshot.",
        },
    )
    assert duplicate_submission.status_code == 409
    assert duplicate_submission.json()["error"]["code"] == "conflict"

    empty_submission = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": [],
            "doctor_summary": "An explicit item selection is required for submission.",
        },
    )
    assert empty_submission.status_code == 422

    payer_queue = client.get("/api/v1/payer/me/requests", headers=payer_headers)
    assert payer_queue.status_code == 200
    assert [item["id"] for item in payer_queue.json()["items"]] == [request_id]
    assert len(payer_queue.json()["items"][0]["lines"]) == 2

    review = client.post(
        f"/api/v1/payer/me/requests/{request_id}/reviews",
        headers={**payer_headers, "Idempotency-Key": "payer-review-clarification-001"},
        json={
            "action": "request_clarification",
            "expected_version": 1,
            "reason_code": "documentation_needed",
            "note": "Attach the imaging interpretation before human resolution.",
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "clarification_requested"
    assert review.json()["version"] == 2
    assert review.json()["reviews"][0]["from_status"] == "submitted"
    assert review.json()["reviews"][0]["to_status"] == "clarification_requested"
    assert review.json()["reviews"][0]["reviewer_display_name"]
    assert review.json()["reviews"][0]["note"].startswith("Attach")
    replayed_review = client.post(
        f"/api/v1/payer/me/requests/{request_id}/reviews",
        headers={**payer_headers, "Idempotency-Key": "payer-review-clarification-001"},
        json={
            "action": "request_clarification",
            "expected_version": 1,
            "reason_code": "documentation_needed",
            "note": "Attach the imaging interpretation before human resolution.",
        },
    )
    assert replayed_review.status_code == 200
    assert len(replayed_review.json()["reviews"]) == 1
    stale_review = client.post(
        f"/api/v1/payer/me/requests/{request_id}/reviews",
        headers={**payer_headers, "Idempotency-Key": "payer-review-stale-version-001"},
        json={
            "action": "accept",
            "expected_version": 1,
            "reason_code": "review_complete",
        },
    )
    assert stale_review.status_code == 409
    assert stale_review.json()["error"]["details"][0]["code"] == "stale_version"

    doctor_response = client.post(
        f"/api/v1/doctor/me/payer-requests/{request_id}/responses",
        headers={**doctor_headers, "Idempotency-Key": "doctor-clarification-response-001"},
        json={
            "expected_version": 2,
            "response_type": "clarification_response",
            "summary": (
                "The synthetic consultation and medication amounts reflect the "
                "documented care episode and delivered-service records."
            ),
        },
    )
    assert doctor_response.status_code == 200, doctor_response.text
    assert doctor_response.json()["status"] == "under_review"
    assert doctor_response.json()["version"] == 3
    assert doctor_response.json()["doctor_responses"][0]["version"] == 3
    replayed_response = client.post(
        f"/api/v1/doctor/me/payer-requests/{request_id}/responses",
        headers={**doctor_headers, "Idempotency-Key": "doctor-clarification-response-001"},
        json={
            "expected_version": 2,
            "response_type": "clarification_response",
            "summary": (
                "The synthetic consultation and medication amounts reflect the "
                "documented care episode and delivered-service records."
            ),
        },
    )
    assert replayed_response.status_code == 200
    assert len(replayed_response.json()["doctor_responses"]) == 1

    patient_requests = client.get("/api/v1/patient/me/payer-requests", headers=patient_headers)
    assert patient_requests.status_code == 200
    patient_view = patient_requests.json()["items"][0]
    assert patient_view["status"] == "under_review"
    assert patient_view["doctor_responses"][0]["response_type"] == "clarification_response"
    assert patient_view["reviews"][0]["note"] is None

    dashboard = client.get("/api/v1/payer/me/dashboard", headers=payer_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["open_requests"] == 1
    assert dashboard.json()["clarification_requests"] == 0
    assert dashboard.json()["pending_requested_total_minor"] == 58000

    rejected = client.post(
        f"/api/v1/payer/me/requests/{request_id}/reviews",
        headers={**payer_headers, "Idempotency-Key": "payer-review-reject-001"},
        json={
            "action": "reject",
            "expected_version": 3,
            "reason_code": "unsupported_request",
            "note": "Reviewer-only explanation that doctors and patients must not receive.",
        },
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["version"] == 4
    assert rejected.json()["reviews"][-1]["action"] == "reject"
    assert rejected.json()["reviews"][-1]["note"].startswith("Reviewer-only")

    doctor_requests = client.get("/api/v1/doctor/me/payer-requests", headers=doctor_headers)
    assert doctor_requests.status_code == 200
    doctor_view = doctor_requests.json()["items"][0]
    assert doctor_view["status"] == "rejected"
    assert doctor_view["reviewed_at"] is not None
    assert doctor_view["reviews"][-1]["action"] == "reject"
    assert doctor_view["reviews"][-1]["reason_code"] == "unsupported_request"
    assert doctor_view["reviews"][-1]["note"] is None

    rejected_dashboard = client.get("/api/v1/payer/me/dashboard", headers=payer_headers)
    assert rejected_dashboard.status_code == 200
    assert rejected_dashboard.json()["open_requests"] == 0
    assert rejected_dashboard.json()["completed_reviews"] == 1
    assert rejected_dashboard.json()["pending_requested_total_minor"] == 0


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
        f"/api/v1/patients/{patient_id}/medications",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "name": "Prescription course",
            "dosage": "10 mg",
            "schedule": "Once daily",
            "financial": {
                "pricing_state": "final",
                "total_cost_minor": 1000,
                "payer_requested_minor": 900,
                "patient_responsibility_minor": 200,
            },
        },
    )
    assert invalid_totals.status_code == 422

    pending_medication = client.post(
        f"/api/v1/patients/{patient_id}/medications",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "name": "Urgent medication with cost pending",
            "dosage": "10 mg",
            "schedule": "Once daily",
            "financial": {"pricing_state": "pending_cost"},
        },
    )
    assert pending_medication.status_code == 200, pending_medication.text
    pending_ledger = client.get(
        f"/api/v1/patients/{patient_id}/care-costs",
        headers=doctor_headers,
    ).json()
    pending_item = pending_ledger["events"][0]["items"][0]
    assert pending_item["submission_eligible"] is False
    assert pending_item["ineligibility_reason"] == "cost_pending"
    _register_payer(
        client,
        email="pending.cost.payer@example.com",
        organization_name="Synthetic Pending Cost Fund",
    )
    organization_id = client.get(
        "/api/v1/payer-organizations",
        headers=doctor_headers,
    ).json()[0]["id"]
    blocked_submission = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": [pending_item["id"]],
            "doctor_summary": "This pending-cost item must not pass the submission gate.",
        },
    )
    assert blocked_submission.status_code == 422
    assert blocked_submission.json()["error"]["details"][0]["code"] == "cost_pending"

    generic_duplicate = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items",
        headers=doctor_headers,
        json={
            "item_type": "medication",
            "label": "Disconnected duplicate",
            "service_date": "2026-07-23",
            "actual_cost_minor": 1000,
            "payer_requested_minor": 800,
            "patient_responsibility_minor": 200,
        },
    )
    assert generic_duplicate.status_code == 409
    assert generic_duplicate.json()["error"]["code"] == "integrated_financial_required"

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
            "actual_cost_minor": 1000,
            "payer_requested_minor": 800,
            "patient_responsibility_minor": 200,
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


def test_imaging_clinical_service_is_the_single_billable_source(
    client: TestClient,
) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)
    _register_payer(
        client,
        email="imaging.service.payer@example.com",
        organization_name="Synthetic Imaging Review Fund",
    )
    organization_id = client.get("/api/v1/payer-organizations", headers=doctor_headers).json()[0][
        "id"
    ]

    created = client.post(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "category": "imaging",
            "name": "Low-dose CT chest",
            "service_subtype": "CT",
            "body_region": "Chest",
            "status": "scheduled",
            "ordered_at": "2026-07-24T02:00:00Z",
            "scheduled_at": "2026-07-25T02:00:00Z",
            "indication_summary": "Clinician-recorded respiratory follow-up indication.",
            "financial": {"pricing_state": "pending_cost"},
        },
    )
    assert created.status_code == 201, created.text
    service = created.json()
    assert service["category"] == "imaging"
    assert service["status"] == "scheduled"
    assert service["imaging_asset_ids"] == []

    pending_ledger = client.get("/api/v1/patient/me/care-costs", headers=patient_headers).json()
    pending_item = pending_ledger["events"][0]["items"][0]
    assert pending_item["source_type"] == "imaging"
    assert pending_item["source_record_id"] == service["id"]
    assert pending_item["source_status"] == "scheduled"
    assert pending_item["pricing_state"] == "pending_cost"
    assert pending_item["submission_eligible"] is False
    assert pending_item["ineligibility_reason"] == "cost_pending"

    for filename in ("ct-series.dcm", "radiology-report.pdf"):
        prepared = client.post(
            f"/api/v1/patients/{patient_id}/imaging/presign",
            headers=doctor_headers,
            json={
                "clinical_event_id": event_id,
                "clinical_service_id": service["id"],
                "filename": filename,
                "content_type": (
                    "application/dicom" if filename.endswith(".dcm") else "application/pdf"
                ),
                "size_bytes": 4096,
            },
        )
        assert prepared.status_code == 200, prepared.text
        assert prepared.json()["clinical_service_id"] == service["id"]
        uploaded = client.put(
            (f"/api/v1/patients/{patient_id}/imaging/{prepared.json()['asset_id']}/content"),
            headers={
                **doctor_headers,
                "Content-Type": (
                    "application/dicom" if filename.endswith(".dcm") else "application/pdf"
                ),
            },
            content=b"x" * 4096,
        )
        assert uploaded.status_code == 200, uploaded.text
        completed = client.post(
            f"/api/v1/patients/{patient_id}/imaging/{prepared.json()['asset_id']}/complete",
            headers=doctor_headers,
            json={"uploaded_size_bytes": 4096},
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["clinical_service_id"] == service["id"]

    service_list = client.get(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=patient_headers,
    )
    assert service_list.status_code == 200
    assert len(service_list.json()["items"][0]["imaging_asset_ids"]) == 2
    ledger_after_evidence = client.get(
        "/api/v1/patient/me/care-costs", headers=patient_headers
    ).json()
    assert len(ledger_after_evidence["events"][0]["items"]) == 1

    completed_cost = client.put(
        f"/api/v1/patients/{patient_id}/clinical-services/{service['id']}/financial",
        headers=doctor_headers,
        json={
            "pricing_state": "estimated",
            "service_date": "2026-07-25",
            "total_cost_minor": 88000,
            "payer_requested_minor": 70000,
            "patient_responsibility_minor": 18000,
        },
    )
    assert completed_cost.status_code == 200, completed_cost.text
    item_id = completed_cost.json()["id"]
    assert completed_cost.json()["submission_eligible"] is True

    submitted = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests",
        headers=doctor_headers,
        json={
            "payer_organization_id": organization_id,
            "care_cost_item_ids": [item_id],
            "doctor_summary": (
                "Please review the scheduled imaging service and its estimated "
                "doctor-entered allocation."
            ),
        },
    )
    assert submitted.status_code == 201, submitted.text
    assert submitted.json()["lines"][0]["label"] == "Low-dose CT chest"
    assert submitted.json()["lines"][0]["actual_cost_minor"] == 88000

    source_edit = client.put(
        f"/api/v1/patients/{patient_id}/clinical-services/{service['id']}",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "category": "imaging",
            "name": "Low-dose CT chest completed",
            "service_subtype": "CT",
            "body_region": "Chest",
            "status": "completed",
            "scheduled_at": "2026-07-25T02:00:00Z",
            "performed_at": "2026-07-25T02:30:00Z",
            "financial": {
                "pricing_state": "final",
                "service_date": "2026-07-25",
                "total_cost_minor": 90000,
                "payer_requested_minor": 72000,
                "patient_responsibility_minor": 18000,
            },
        },
    )
    assert source_edit.status_code == 200, source_edit.text
    assert datetime.fromisoformat(
        source_edit.json()["ordered_at"].replace("Z", "+00:00")
    ) == datetime.fromisoformat(service["ordered_at"].replace("Z", "+00:00"))
    refreshed_item = client.get("/api/v1/patient/me/care-costs", headers=patient_headers).json()[
        "events"
    ][0]["items"][0]
    assert refreshed_item["actual_cost_minor"] == 90000
    assert refreshed_item["source_status"] == "completed"
    assert refreshed_item["already_submitted"] is True
    assert refreshed_item["ineligibility_reason"] == "already_submitted"

    immutable = client.get("/api/v1/patient/me/payer-requests", headers=patient_headers).json()[
        "items"
    ][0]["lines"][0]
    assert immutable["label"] == "Low-dose CT chest"
    assert immutable["actual_cost_minor"] == 88000

    patient_write = client.post(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=patient_headers,
        json={
            "clinical_event_id": event_id,
            "category": "imaging",
            "name": "Unauthorized MRI",
            "service_subtype": "MRI",
            "body_region": "Brain",
        },
    )
    assert patient_write.status_code == 404


def test_doctor_can_record_non_imaging_delivered_services_and_costs(
    client: TestClient,
) -> None:
    patient_headers, doctor_headers, patient_id, event_id = _connected_event(client)

    for index, category in enumerate(("laboratory", "consultation", "treatment", "rehabilitation")):
        response = client.post(
            f"/api/v1/patients/{patient_id}/clinical-services",
            headers=doctor_headers,
            json={
                "clinical_event_id": event_id,
                "category": category,
                "name": f"Synthetic {category} service",
                "service_subtype": f"{category}-fixture",
                "status": "completed",
                "performed_at": f"2026-07-{20 + index}T02:00:00Z",
                "financial": {
                    "pricing_state": "final",
                    "service_date": f"2026-07-{20 + index}",
                    "total_cost_minor": 10000 + index,
                    "payer_requested_minor": 8000,
                    "patient_responsibility_minor": 2000 + index,
                },
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["category"] == category
        assert response.json()["body_region"] is None

    patient_view = client.get(
        f"/api/v1/patients/{patient_id}/clinical-services",
        headers=patient_headers,
    )
    assert patient_view.status_code == 200
    assert {item["category"] for item in patient_view.json()["items"]} == {
        "laboratory",
        "consultation",
        "treatment",
        "rehabilitation",
    }


def test_payer_can_update_only_reviewer_owned_profile_fields(client: TestClient) -> None:
    payer_session, payer_headers = _register_payer(
        client,
        email="payer.profile@example.com",
        organization_name="Synthetic Provincial Review Fund",
    )
    doctor = register(
        client,
        email="payer.profile.doctor@example.com",
        password="Doctor9!",
        role="doctor",
    )
    doctor_headers = auth_header(doctor["access_token"])

    before = client.get("/api/v1/payer/me/profile", headers=payer_headers)
    assert before.status_code == 200
    organization_before = before.json()["organization"]

    updated = client.patch(
        "/api/v1/payer/me/profile",
        headers=payer_headers,
        json={
            "display_name": "Mei Reviewer",
            "title": "Senior expenditure reviewer",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["display_name"] == "Mei Reviewer"
    assert updated.json()["title"] == "Senior expenditure reviewer"
    assert updated.json()["organization"] == organization_before
    assert updated.json()["status"] == "active"
    assert updated.json()["scope"] == "synthetic_review"

    dashboard = client.get("/api/v1/payer/me/dashboard", headers=payer_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["profile"]["display_name"] == "Mei Reviewer"

    unchanged = client.patch(
        "/api/v1/payer/me/profile",
        headers=payer_headers,
        json={
            "display_name": "Mei Reviewer",
            "title": "Senior expenditure reviewer",
        },
    )
    assert unchanged.status_code == 422
    assert unchanged.json()["error"]["code"] == "validation_failed"

    governance_write = client.patch(
        "/api/v1/payer/me/profile",
        headers=payer_headers,
        json={
            "display_name": "Mei Reviewer",
            "scope": "all_requests",
            "status": "active",
            "organization": {"verification_status": "verified"},
        },
    )
    assert governance_write.status_code == 422
    assert governance_write.json()["error"]["code"] == "validation_failed"

    with engine.begin() as connection:
        connection.execute(
            update(PayerMembership)
            .where(PayerMembership.user_id == payer_session["user"]["id"])
            .values(status="revoked")
        )
    inactive_membership = client.patch(
        "/api/v1/payer/me/profile",
        headers=payer_headers,
        json={"display_name": "No longer authorized"},
    )
    assert inactive_membership.status_code == 404
    assert inactive_membership.json()["error"]["code"] == "not_found"

    wrong_role = client.patch(
        "/api/v1/payer/me/profile",
        headers=doctor_headers,
        json={"display_name": "Not a payer reviewer"},
    )
    assert wrong_role.status_code == 404
    assert wrong_role.json()["error"]["code"] == "not_found"


def test_payer_with_ambiguous_active_organization_fails_closed(
    client: TestClient,
) -> None:
    payer_session, payer_headers = _register_payer(
        client,
        email="payer.ambiguous@example.com",
        organization_name="Synthetic Primary Payer",
    )
    with Session(engine) as db:
        secondary = PayerOrganization(
            name=f"Synthetic Secondary Payer {uuid.uuid4()}",
            organization_type="public_payer",
            jurisdiction_code="CN",
            verification_status="synthetic_only",
        )
        db.add(secondary)
        db.flush()
        db.add(
            PayerMembership(
                payer_organization_id=secondary.id,
                user_id=uuid.UUID(payer_session["user"]["id"]),
                display_name="Ambiguous Reviewer",
                title="Synthetic reviewer",
                status="active",
                scope="synthetic_review",
            )
        )
        db.commit()

    response = client.get("/api/v1/payer/me/dashboard", headers=payer_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payer_organization_context_ambiguous"
