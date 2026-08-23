from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    AuditEvent,
    CareRelationship,
    ClinicalEvent,
    Notification,
    PatientProfile,
    PayerRequest,
    RecoveryPlan,
    RecoveryPlanReviewDecision,
    RecoveryTask,
    User,
)
from app.seed import seed_database
from tests.helpers import auth_header, login


def _headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    return auth_header(login(client, email, password)["access_token"])


def _task(title: str, scheduled_date: date | None) -> dict[str, object]:
    return {
        "category": "exercise",
        "title": title,
        "detail": "Synthetic workflow-integrity task.",
        "due_label": "Display label only",
        "scheduled_date": scheduled_date.isoformat() if scheduled_date else None,
        "time_zone": "Asia/Shanghai",
    }


def test_patient_consent_reapproval_and_revocation_are_fail_closed(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        doctor = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
        unrelated = db.scalar(select(User).where(User.email == "unrelated.patient@example.com"))
        relationship = db.scalar(
            select(CareRelationship).where(
                CareRelationship.doctor_id == doctor.doctor_profile.id,
                CareRelationship.patient_id == unrelated.patient_profile.id,
            )
        )
        assert relationship.status == "revoked"
        patient_id = unrelated.patient_profile.id
        clinical_event_id = db.scalar(
            select(ClinicalEvent.id).where(ClinicalEvent.patient_id == patient_id)
        )
        payer_request_id = db.scalar(
            select(PayerRequest.id).where(PayerRequest.patient_id == patient_id)
        )

    doctor_headers = _headers(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    patient_headers = _headers(
        client,
        "unrelated.patient@example.com",
        settings.seed_unrelated_patient_password.get_secret_value(),
    )

    requested = client.post(
        "/api/v1/patients/connect",
        json={"patient_code": "SYN-PATIENT-002"},
        headers=doctor_headers,
    )
    assert requested.status_code == 200
    assert requested.json()["relationship_label"] == "Pending patient approval"
    assert client.get(f"/api/v1/patients/{patient_id}", headers=doctor_headers).status_code == 404

    contacts = client.get("/api/v1/patient/me/contacts", headers=patient_headers).json()["items"]
    pending = next(
        item for item in contacts if item["relationship_status"] == "pending_patient_approval"
    )
    repeated = client.post(
        "/api/v1/patients/connect",
        json={"patient_code": "SYN-PATIENT-002"},
        headers=doctor_headers,
    )
    assert repeated.status_code == 200
    contacts_after_repeat = client.get(
        "/api/v1/patient/me/contacts", headers=patient_headers
    ).json()["items"]
    assert contacts_after_repeat[0]["request_version"] == pending["request_version"]

    approved = client.post(
        f"/api/v1/patient/me/doctor-relationships/{pending['relationship_id']}/approve",
        json={"expected_version": pending["request_version"]},
        headers=patient_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"
    assert client.get(f"/api/v1/patients/{patient_id}", headers=doctor_headers).status_code == 200
    consultation = client.post(
        "/api/v1/consultations",
        json={
            "patient_id": str(patient_id),
            "specialty": "Synthetic rehabilitation",
            "question_summary": "Synthetic relationship-gated request.",
            "status": "requested",
        },
        headers=doctor_headers,
    )
    assert consultation.status_code == 200

    revoked = client.post(
        f"/api/v1/patient/me/doctor-relationships/{pending['relationship_id']}/revoke",
        json={"expected_version": approved.json()["request_version"]},
        headers=patient_headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert client.get(f"/api/v1/patients/{patient_id}", headers=doctor_headers).status_code == 404
    assert (
        client.get(
            f"/api/v1/private-chats/{patient_id}/messages", headers=doctor_headers
        ).status_code
        == 404
    )
    gated_routes = [
        f"/api/v1/patients/{patient_id}/care",
        f"/api/v1/patients/{patient_id}/clinical-events",
        f"/api/v1/patients/{patient_id}/recovery-plans",
        f"/api/v1/patients/{patient_id}/care-costs",
    ]
    if clinical_event_id is not None:
        gated_routes.append(
            f"/api/v1/patients/{patient_id}/clinical-events/{clinical_event_id}/expected-care/candidates"
        )
    if payer_request_id is not None:
        gated_routes.append(f"/api/v1/doctor/payer-requests/{payer_request_id}/intelligence")
    for route in gated_routes:
        assert client.get(route, headers=doctor_headers).status_code == 404, route
    visible_consultations = client.get("/api/v1/consultations", headers=doctor_headers).json()[
        "items"
    ]
    assert all(item["patient_id"] != str(patient_id) for item in visible_consultations)

    with Session(engine) as db:
        notifications = db.scalars(
            select(Notification).where(
                Notification.patient_id == patient_id,
                Notification.notification_type == "care_relationship_approval_requested",
            )
        ).all()
        assert len(notifications) == 1
        events = db.scalars(
            select(AuditEvent.event_type).where(
                AuditEvent.resource_id == relationship.id,
                AuditEvent.event_type.in_(
                    {
                        "care_relationship_requested",
                        "care_relationship_approved",
                        "care_relationship_revoked",
                    }
                ),
            )
        ).all()
        assert set(events) == {
            "care_relationship_requested",
            "care_relationship_approved",
            "care_relationship_revoked",
        }


def test_concurrent_connection_requests_share_one_pending_cycle(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    doctor_headers = _headers(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    def request_connection(_: int):
        return client.post(
            "/api/v1/patients/connect",
            json={"patient_code": "SYN-PATIENT-002"},
            headers=doctor_headers,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(request_connection, range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    with Session(engine) as db:
        patient = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-002")
        )
        relationship = db.scalar(
            select(CareRelationship).where(CareRelationship.patient_id == patient.id)
        )
        assert relationship.status == "pending_patient_approval"
        assert relationship.request_version == 2
        notifications = db.scalars(
            select(Notification).where(
                Notification.patient_id == patient.id,
                Notification.notification_type == "care_relationship_approval_requested",
            )
        ).all()
        assert len(notifications) == 1


def test_distinct_reviewer_approval_and_activation(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        patient = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-001")
        )
        author = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
        reviewer = db.scalar(select(User).where(User.email == "reviewer.doctor@example.com"))
        patient_id = patient.id
        author_doctor_id = author.doctor_profile.id
        reviewer_doctor_id = reviewer.doctor_profile.id

    author_headers = _headers(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    reviewer_headers = _headers(
        client, "reviewer.doctor@example.com", settings.seed_doctor_password.get_secret_value()
    )
    payload = {
        "title": "Independently reviewed synthetic plan",
        "instructions": "Synthetic workflow only.",
        "tasks": [_task("Structured review task", date.today())],
    }
    created = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans", json=payload, headers=author_headers
    )
    assert created.status_code == 200
    plan = created.json()
    assert plan["author_doctor_id"] == str(author_doctor_id)

    self_review = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/submit-review",
        json={"reviewer_doctor_id": str(author_doctor_id), "expected_version": plan["version"]},
        headers=author_headers,
    )
    assert self_review.status_code == 422

    submitted = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/submit-review",
        json={"reviewer_doctor_id": str(reviewer_doctor_id), "expected_version": plan["version"]},
        headers=author_headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["review_status"] == "in_review"
    assert (
        client.post(
            f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/approve",
            json={"expected_version": plan["version"]},
            headers=author_headers,
        ).status_code
        == 404
    )

    approved = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/approve",
        json={
            "expected_version": plan["version"],
            "comment": "Independent synthetic review complete.",
        },
        headers=reviewer_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["activated_at"] is None
    duplicate = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/approve",
        json={"expected_version": plan["version"]},
        headers=reviewer_headers,
    )
    assert duplicate.status_code == 409

    activated = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{plan['plan_id']}/activate",
        headers=author_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    with Session(engine) as db:
        decision = db.scalar(
            select(RecoveryPlanReviewDecision).where(
                RecoveryPlanReviewDecision.plan_id == plan["plan_id"]
            )
        )
        assert decision.reviewer_doctor_id == reviewer_doctor_id
        assert decision.reviewer_doctor_id != author_doctor_id

    second = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans", json=payload, headers=author_headers
    ).json()
    submitted_after_activation = client.post(
        f"/api/v1/patients/{patient_id}/recovery-plans/{second['plan_id']}/submit-review",
        json={
            "reviewer_doctor_id": str(reviewer_doctor_id),
            "expected_version": second["version"],
        },
        headers=author_headers,
    )
    assert submitted_after_activation.status_code == 200
    patient_headers = _headers(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    reviewer_contact = next(
        item
        for item in client.get("/api/v1/patient/me/contacts", headers=patient_headers).json()[
            "items"
        ]
        if item["doctor_id"] == str(reviewer_doctor_id)
    )
    assert (
        client.post(
            f"/api/v1/patient/me/doctor-relationships/{reviewer_contact['relationship_id']}/revoke",
            json={"expected_version": reviewer_contact["request_version"]},
            headers=patient_headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/patients/{patient_id}/recovery-plans/{second['plan_id']}/approve",
            json={"expected_version": second["version"]},
            headers=reviewer_headers,
        ).status_code
        == 404
    )


def test_today_aggregates_multiple_active_plans_and_structured_categories(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        patient = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-001")
        )
        author = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
        today = datetime.now(UTC).astimezone().date()
        for index in range(2):
            plan = RecoveryPlan(
                patient_id=patient.id,
                doctor_id=author.doctor_profile.id,
                title=f"Synthetic source plan {index + 1}",
                instructions="Structured schedule aggregation fixture.",
                status="active",
                review_status="approved",
                safety_label="Synthetic demonstration data only. Do not enter real patient data.",
                activated_at=datetime.now(UTC),
            )
            db.add(plan)
            db.flush()
            dates = [today - timedelta(days=1), today, today + timedelta(days=1), None]
            for order, scheduled_date in enumerate(dates):
                plan.tasks.append(
                    RecoveryTask(
                        patient_id=patient.id,
                        category="exercise",
                        title=f"Plan {index + 1} task {order + 1}",
                        detail="Synthetic categorized task.",
                        due_label="Today" if scheduled_date != today else "Not used for scheduling",
                        scheduled_date=scheduled_date,
                        time_zone="Asia/Shanghai",
                        sort_order=order,
                    )
                )
        boundary_plan = RecoveryPlan(
            patient_id=patient.id,
            doctor_id=author.doctor_profile.id,
            title="Time-zone boundary plan",
            instructions="Per-task IANA date boundary fixture.",
            status="active",
            review_status="approved",
            safety_label="Synthetic demonstration data only. Do not enter real patient data.",
            activated_at=datetime.now(UTC),
        )
        db.add(boundary_plan)
        db.flush()
        for order, zone_name in enumerate(("Pacific/Kiritimati", "Pacific/Honolulu")):
            local_date = datetime.now(UTC).astimezone(ZoneInfo(zone_name)).date()
            boundary_plan.tasks.append(
                RecoveryTask(
                    patient_id=patient.id,
                    category="follow_up",
                    title=f"Boundary today {zone_name}",
                    detail="Synthetic time-zone boundary task.",
                    due_label="Never parsed",
                    scheduled_date=local_date,
                    time_zone=zone_name,
                    sort_order=order,
                )
            )
        db.commit()

    patient_headers = _headers(
        client, "patient.demo@example.com", settings.seed_patient_password.get_secret_value()
    )
    response = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    categories = data["task_categories"]
    assert len(data["active_recovery_plans"]) >= 3
    assert len(categories["overdue"]) == 2
    assert len(categories["today"]) >= 2
    assert len(categories["upcoming"]) == 2
    assert len(categories["unscheduled"]) >= 2
    today_titles = {item["title"] for item in categories["today"]}
    assert "Boundary today Pacific/Kiritimati" in today_titles
    assert "Boundary today Pacific/Honolulu" in today_titles
    assert all(task["plan_title"] for items in categories.values() for task in items)
    assert all(task["due_label"] == "Today" for task in categories["upcoming"])
