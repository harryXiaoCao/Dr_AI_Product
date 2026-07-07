import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import AuditEvent, PatientProfile, RecoveryPlan
from app.seed import seed_database
from tests.helpers import auth_header, login


def _seed_patient_ids(settings) -> tuple[uuid.UUID, uuid.UUID]:
    with Session(engine) as db:
        seed_database(db, settings)
        assigned = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-001")
        )
        unrelated = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-002")
        )
        assert assigned is not None
        assert unrelated is not None
        return assigned.id, unrelated.id


def _plan_payload(title: str = "Synthetic recovery draft") -> dict[str, object]:
    return {
        "title": title,
        "instructions": "Synthetic recovery instructions for demo workflow validation only.",
        "tasks": [
            {
                "category": "medication",
                "title": "Demo medication check",
                "detail": "Review synthetic medication fixture only.",
                "due_label": "Today",
                "notification_time": "09:00",
            },
            {
                "category": "exercise",
                "title": "Demo walking task",
                "detail": "Short synthetic mobility task for UI validation.",
                "due_label": "Today",
            },
            {
                "category": "diet",
                "title": "Demo hydration task",
                "detail": "Synthetic hydration reminder for Today display.",
                "due_label": "Today",
            },
            {
                "category": "follow_up",
                "title": "Demo follow-up task",
                "detail": "Prepare synthetic questions for the next doctor review.",
                "due_label": "Today",
            },
        ],
    }


def test_doctor_can_create_edit_and_activate_recovery_plan(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(doctor["access_token"])

    created = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans",
        json=_plan_payload(),
        headers=headers,
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "draft"
    assert len(payload["tasks"]) == 4
    assert payload["tasks"][0]["category"] == "medication"
    assert payload["tasks"][0]["notification_status"].startswith("Local demo")

    plan_id = payload["plan_id"]
    edited_payload = _plan_payload("Updated synthetic recovery plan")
    edited_payload["instructions"] = "Updated synthetic instructions; still not medical advice."
    edited = client.put(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}",
        json=edited_payload,
        headers=headers,
    )
    assert edited.status_code == 200
    assert edited.json()["title"] == "Updated synthetic recovery plan"

    activated = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/activate",
        headers=headers,
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    with Session(engine) as db:
        active_count = db.scalar(
            select(RecoveryPlan).where(
                RecoveryPlan.patient_id == assigned_id,
                RecoveryPlan.status == "active",
            )
        )
        assert active_count is not None
        audit_types = set(db.scalars(select(AuditEvent.event_type)).all())
        assert {
            "recovery_plan_created",
            "recovery_plan_updated",
            "recovery_plan_activated",
        }.issubset(audit_types)
        metadata = db.scalars(
            select(AuditEvent.metadata_json).where(
                AuditEvent.event_type == "recovery_plan_created"
            )
        ).first()
        assert metadata is not None
        assert "Synthetic recovery instructions" not in str(metadata)


def test_patient_today_readback_and_task_completion(client: TestClient, settings) -> None:
    _seed_patient_ids(settings)
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    headers = auth_header(patient["access_token"])

    today = client.get("/api/v1/patient/me/today", headers=headers)
    assert today.status_code == 200
    data = today.json()["data"]
    assert data["active_recovery_plan"]["status"] == "active"
    categories = {task["category"] for task in data["today_tasks"]}
    assert categories == {"medication", "exercise", "diet", "follow_up"}
    medication = next(task for task in data["today_tasks"] if task["category"] == "medication")
    assert medication["is_completed"] is False
    assert medication["notification_time"] == "09:00"

    completed = client.post(
        f"/api/v1/patient/me/tasks/{medication['task_id']}/completion",
        json={"completed": True},
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["task"]["is_completed"] is True

    today_after = client.get("/api/v1/patient/me/today", headers=headers)
    task_after = next(
        task
        for task in today_after.json()["data"]["today_tasks"]
        if task["task_id"] == medication["task_id"]
    )
    assert task_after["is_completed"] is True


def test_recovery_plan_wrong_role_and_cross_patient_denials_are_neutral(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    unrelated = login(
        client,
        "unrelated.patient@example.com",
        settings.seed_unrelated_patient_password.get_secret_value(),
    )

    patient_create = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans",
        json=_plan_payload(),
        headers=auth_header(patient["access_token"]),
    )
    assert patient_create.status_code == 404
    assert patient_create.json()["error"]["code"] == "not_found"

    cross_doctor = client.post(
        f"/api/v1/patients/{unrelated_id}/recovery-plans",
        json=_plan_payload(),
        headers=auth_header(doctor["access_token"]),
    )
    assert cross_doctor.status_code == 404
    assert cross_doctor.json()["error"]["code"] == "not_found"

    today = client.get("/api/v1/patient/me/today", headers=auth_header(patient["access_token"]))
    task_id = today.json()["data"]["today_tasks"][0]["task_id"]
    cross_patient_completion = client.post(
        f"/api/v1/patient/me/tasks/{task_id}/completion",
        json={"completed": True},
        headers=auth_header(unrelated["access_token"]),
    )
    assert cross_patient_completion.status_code == 404
    assert cross_patient_completion.json()["error"]["code"] == "not_found"
