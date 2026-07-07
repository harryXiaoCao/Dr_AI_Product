import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import AuditEvent, MedicalImagingAsset, PatientProfile
from app.seed import seed_database
from tests.helpers import auth_header, login

PHASE2_TABLES = {
    "patient_allergies",
    "chronic_diseases",
    "visit_history",
    "diagnoses",
    "medical_imaging_assets",
}
PHASE2_RECOVERY_COLUMNS = {
    "review_status",
    "review_actor_user_id",
    "submitted_at",
    "reviewed_at",
    "approved_at",
    "completed_at",
}


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


def _doctor_headers(client: TestClient, settings) -> dict[str, str]:
    tokens = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    return auth_header(tokens["access_token"])


def _patient_headers(client: TestClient, settings) -> dict[str, str]:
    tokens = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    return auth_header(tokens["access_token"])


def test_phase2_tables_are_present_and_seed_keeps_them_empty(settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        for table_name in PHASE2_TABLES:
            count = db.scalar(text(f"SELECT count(*) FROM {table_name}"))
            assert count == 0, table_name
        recovery_columns = set(
            db.scalars(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'recovery_plans'"
                )
            ).all()
        )
        assert PHASE2_RECOVERY_COLUMNS.issubset(recovery_columns)


def test_patient_can_update_allowed_profile_and_allergy_surfaces(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    headers = _patient_headers(client, settings)

    profile_response = client.patch(
        "/api/v1/patient/me/profile",
        headers=headers,
        json={
            "display_name": "Riley Demo Patient Updated",
            "birth_year": 1988,
            "sex": "not specified",
            "preferred_language": "English",
            "contact_preference": "in-app",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["demographics"]["birth_year"] == 1988

    allergy_response = client.post(
        f"/api/v1/patients/{assigned_id}/allergies",
        headers=headers,
        json={
            "label": "Synthetic pollen sensitivity",
            "reaction": "Demo-only seasonal response",
            "severity": "mild",
            "status": "active",
        },
    )
    assert allergy_response.status_code == 200
    assert allergy_response.json()["severity"] == "mild"

    cross_patient_response = client.post(
        f"/api/v1/patients/{unrelated_id}/allergies",
        headers=headers,
        json={"label": "Synthetic blocked allergy"},
    )
    assert cross_patient_response.status_code == 404
    assert cross_patient_response.json()["error"]["code"] == "not_found"

    with Session(engine) as db:
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.patient_id == assigned_id)
        ).all()
        event_types = {audit.event_type for audit in audits}
        assert "patient_profile_updated" in event_types
        allergy_audit = next(
            audit for audit in audits if audit.event_type == "patient_allergy_created"
        )
        assert allergy_audit.metadata_json == {
            "severity": "mild",
            "status": "active",
            "actor_role": "patient",
        }
        assert "Synthetic pollen sensitivity" not in str(allergy_audit.metadata_json)


def test_doctor_can_crud_core_medical_history_and_notes_with_metadata_only_audit(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    headers = _doctor_headers(client, settings)

    visit = client.post(
        f"/api/v1/patients/{assigned_id}/visit-history",
        headers=headers,
        json={
            "visit_type": "follow_up",
            "title": "Synthetic follow-up visit",
            "summary": "Demo-only visit summary for Phase 2 workflow tests.",
            "occurred_at": "2026-07-07T09:00:00Z",
            "clinician_label": "Demo clinician",
        },
    )
    assert visit.status_code == 200
    visit_id = visit.json()["id"]

    diagnosis = client.post(
        f"/api/v1/patients/{assigned_id}/diagnoses",
        headers=headers,
        json={
            "label": "Synthetic observation",
            "status": "active",
            "diagnosed_on": "2026-07-07",
            "notes": "Demo-only diagnosis note.",
        },
    )
    assert diagnosis.status_code == 200
    diagnosis_id = diagnosis.json()["id"]

    note = client.post(
        f"/api/v1/patients/{assigned_id}/doctor-notes",
        headers=headers,
        json={
            "title": "Synthetic Phase 2 note",
            "body": "Doctor-facing demo note for Phase 2 workflow tests.",
        },
    )
    assert note.status_code == 200
    note_id = note.json()["id"]

    updated_note = client.put(
        f"/api/v1/patients/{assigned_id}/doctor-notes/{note_id}",
        headers=headers,
        json={
            "title": "Synthetic Phase 2 note updated",
            "body": "Updated doctor-facing demo note.",
        },
    )
    assert updated_note.status_code == 200
    assert updated_note.json()["title"] == "Synthetic Phase 2 note updated"

    care = client.get(f"/api/v1/patients/{assigned_id}/care", headers=headers)
    assert care.status_code == 200
    care_payload = care.json()
    assert care_payload["visit_history"][0]["id"] == visit_id
    assert care_payload["diagnoses"][0]["id"] == diagnosis_id
    assert care_payload["doctor_notes"][0]["id"] == note_id

    assert (
        client.delete(
            f"/api/v1/patients/{assigned_id}/visit-history/{visit_id}",
            headers=headers,
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/patients/{assigned_id}/diagnoses/{diagnosis_id}",
            headers=headers,
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/patients/{assigned_id}/doctor-notes/{note_id}",
            headers=headers,
        ).status_code
        == 204
    )

    with Session(engine) as db:
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.patient_id == assigned_id)
        ).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "visit_history_created",
            "diagnosis_created",
            "doctor_note_created",
            "doctor_note_updated",
            "patient_care_bundle_read",
            "visit_history_deleted",
            "diagnosis_deleted",
            "doctor_note_deleted",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Demo-only visit summary" not in serialized_metadata
        assert "Synthetic observation" not in serialized_metadata
        assert "Doctor-facing demo note" not in serialized_metadata


def test_patient_can_read_history_but_cannot_write_doctor_owned_history(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    patient_headers = _patient_headers(client, settings)

    diagnosis_response = client.post(
        f"/api/v1/patients/{assigned_id}/diagnoses",
        headers=patient_headers,
        json={"label": "Synthetic blocked diagnosis"},
    )
    assert diagnosis_response.status_code == 404
    assert diagnosis_response.json()["error"]["code"] == "not_found"

    note_response = client.get(
        f"/api/v1/patients/{assigned_id}/doctor-notes",
        headers=patient_headers,
    )
    assert note_response.status_code == 404
    assert note_response.json()["error"]["code"] == "not_found"

    care_response = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert care_response.status_code == 200
    assert care_response.json()["doctor_notes"] == []


def test_doctor_can_manage_medication_prescription_and_reminders_with_safe_readback(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)

    medication = client.post(
        f"/api/v1/patients/{assigned_id}/medications",
        headers=doctor_headers,
        json={
            "name": "Synthetic Phase 2 medication",
            "dosage": "10 mg",
            "schedule": "Every demo morning",
            "status": "active",
            "note": "Demo-only medication note.",
        },
    )
    assert medication.status_code == 200
    medication_payload = medication.json()
    medication_id = medication_payload["id"]

    updated_medication = client.put(
        f"/api/v1/patients/{assigned_id}/medications/{medication_id}",
        headers=doctor_headers,
        json={
            "name": "Synthetic Phase 2 medication updated",
            "dosage": "10 mg",
            "schedule": "Every demo evening",
            "status": "paused",
            "note": "Updated demo-only medication note.",
        },
    )
    assert updated_medication.status_code == 200
    assert updated_medication.json()["status"] == "paused"

    prescription = client.post(
        f"/api/v1/patients/{assigned_id}/prescriptions",
        headers=doctor_headers,
        json={
            "status": "issued",
            "issued_at": "2026-07-07T10:00:00Z",
            "notes": "Synthetic prescription note.",
            "medications": [
                {
                    "medication_id": medication_id,
                    "name": "Synthetic Phase 2 medication updated",
                    "dosage": "10 mg",
                    "schedule": "Every demo evening",
                    "start_date": "2026-07-07",
                    "end_date": "2026-07-14",
                }
            ],
        },
    )
    assert prescription.status_code == 200
    prescription_payload = prescription.json()
    prescription_id = prescription_payload["id"]
    line_id = prescription_payload["medications"][0]["id"]

    updated_prescription = client.put(
        f"/api/v1/patients/{assigned_id}/prescriptions/{prescription_id}",
        headers=doctor_headers,
        json={
            "status": "issued",
            "issued_at": "2026-07-07T11:00:00Z",
            "notes": "Updated synthetic prescription note.",
            "medications": [
                {
                    "medication_id": medication_id,
                    "name": "Synthetic Phase 2 medication updated",
                    "dosage": "10 mg",
                    "schedule": "Every demo evening",
                    "start_date": "2026-07-07",
                    "end_date": "2026-07-21",
                }
            ],
        },
    )
    assert updated_prescription.status_code == 200
    line_id = updated_prescription.json()["medications"][0]["id"]

    medication_reminder = client.post(
        f"/api/v1/patients/{assigned_id}/medication-reminders",
        headers=doctor_headers,
        json={
            "medication_id": medication_id,
            "reminder_type": "medication",
            "schedule_label": "Demo medication reminder",
            "channel": "in_app",
            "status": "active",
            "next_due_at": "2026-07-08T09:00:00Z",
        },
    )
    assert medication_reminder.status_code == 200
    reminder_id = medication_reminder.json()["id"]

    refill_reminder = client.post(
        f"/api/v1/patients/{assigned_id}/medication-reminders",
        headers=doctor_headers,
        json={
            "prescription_medication_id": line_id,
            "reminder_type": "refill",
            "schedule_label": "Demo refill reminder",
            "channel": "in_app",
            "status": "active",
            "next_due_at": "2026-07-12T09:00:00Z",
        },
    )
    assert refill_reminder.status_code == 200
    assert refill_reminder.json()["reminder_type"] == "refill"

    paused_reminder = client.put(
        f"/api/v1/patients/{assigned_id}/medication-reminders/{reminder_id}",
        headers=doctor_headers,
        json={
            "medication_id": medication_id,
            "reminder_type": "medication",
            "schedule_label": "Demo medication reminder paused",
            "channel": "in_app",
            "status": "paused",
            "next_due_at": "2026-07-08T09:00:00Z",
        },
    )
    assert paused_reminder.status_code == 200
    assert paused_reminder.json()["status"] == "paused"

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200
    care_payload = patient_care.json()
    assert any(item["id"] == medication_id for item in care_payload["medications"])
    assert care_payload["prescriptions"][0]["id"] == prescription_id
    assert {item["reminder_type"] for item in care_payload["medication_reminders"]} == {
        "medication",
        "refill",
    }
    assert care_payload["doctor_notes"] == []

    reminders = client.get("/api/v1/reminders", headers=patient_headers)
    assert reminders.status_code == 200
    assert len(reminders.json()["items"]) == 2

    notifications = client.get("/api/v1/patient/me/notifications", headers=patient_headers)
    assert notifications.status_code == 200
    notification_payload = notifications.json()["items"]
    assert {item["notification_type"] for item in notification_payload} >= {
        "medication_reminder",
        "refill_reminder",
    }
    serialized_notifications = str(notification_payload)
    assert "Synthetic Phase 2 medication" not in serialized_notifications
    assert "Every demo" not in serialized_notifications
    assert "Demo refill reminder" not in serialized_notifications

    patient_write = client.post(
        f"/api/v1/patients/{assigned_id}/medications",
        headers=patient_headers,
        json={
            "name": "Blocked patient medication",
            "dosage": "1 mg",
            "schedule": "Never",
            "status": "active",
            "note": "",
        },
    )
    assert patient_write.status_code == 404
    assert patient_write.json()["error"]["code"] == "not_found"

    cross_patient_write = client.post(
        f"/api/v1/patients/{unrelated_id}/prescriptions",
        headers=doctor_headers,
        json={
            "status": "draft",
            "medications": [
                {
                    "name": "Blocked synthetic medication",
                    "dosage": "1 mg",
                    "schedule": "Never",
                }
            ],
        },
    )
    assert cross_patient_write.status_code == 404
    assert cross_patient_write.json()["error"]["code"] == "not_found"

    with Session(engine) as db:
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.patient_id == assigned_id)
        ).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "medication_created",
            "medication_updated",
            "prescription_created",
            "prescription_updated",
            "medication_reminder_created",
            "medication_reminder_updated",
            "notifications_listed",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Synthetic Phase 2 medication" not in serialized_metadata
        assert "Every demo" not in serialized_metadata
        assert "Demo-only medication note" not in serialized_metadata
        assert "Synthetic prescription note" not in serialized_metadata
        assert "Demo medication reminder" not in serialized_metadata


def test_phase2_imaging_upload_completion_review_and_safe_boundaries(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)

    presign = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/presign",
        headers=doctor_headers,
        json={
            "filename": "synthetic-phase2-scan.png",
            "content_type": "image/png",
            "size_bytes": 4096,
        },
    )
    assert presign.status_code == 200
    presign_payload = presign.json()
    asset_id = presign_payload["asset_id"]
    assert presign_payload["storage_provider"] == "tencent_cos"
    assert presign_payload["upload_status"] == "pending_upload"
    assert presign_payload["review_status"] == "not_ready"
    assert "object_key" not in presign_payload

    complete = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={
            "uploaded_size_bytes": 4096,
            "etag": '"phase2etag"',
            "checksum_sha256": "a" * 64,
        },
    )
    assert complete.status_code == 200
    complete_payload = complete.json()
    assert complete_payload["upload_status"] == "uploaded"
    assert complete_payload["review_status"] == "pending_review"
    assert "object_key" not in complete_payload

    doctor_list = client.get(f"/api/v1/patients/{assigned_id}/imaging", headers=doctor_headers)
    assert doctor_list.status_code == 200
    assert doctor_list.json()["items"][0]["id"] == asset_id

    patient_list = client.get("/api/v1/patient/me/imaging", headers=patient_headers)
    assert patient_list.status_code == 200
    assert patient_list.json()["items"][0]["id"] == asset_id

    patient_detail = client.get(f"/api/v1/patient/me/imaging/{asset_id}", headers=patient_headers)
    assert patient_detail.status_code == 200
    assert patient_detail.json()["review_status"] == "pending_review"

    patient_review = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/review",
        headers=patient_headers,
        json={"review_status": "reviewed"},
    )
    assert patient_review.status_code == 404
    assert patient_review.json()["error"]["code"] == "not_found"

    review = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/review",
        headers=doctor_headers,
        json={"review_status": "reviewed"},
    )
    assert review.status_code == 200
    assert review.json()["review_status"] == "reviewed"
    assert review.json()["reviewed_at"] is not None

    cross_patient_complete = client.post(
        f"/api/v1/patients/{unrelated_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={"uploaded_size_bytes": 4096},
    )
    assert cross_patient_complete.status_code == 404
    assert cross_patient_complete.json()["error"]["code"] == "not_found"

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200
    assert patient_care.json()["imaging_assets"][0]["id"] == asset_id

    with Session(engine) as db:
        asset = db.scalar(select(MedicalImagingAsset).where(MedicalImagingAsset.id == asset_id))
        assert asset is not None
        assert asset.object_key.startswith("medical-imaging-assets/")
        assert asset.upload_status == "uploaded"
        assert asset.review_status == "reviewed"
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.patient_id == assigned_id)
        ).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "medical_imaging_upload_presigned",
            "medical_imaging_upload_completed",
            "medical_imaging_assets_listed",
            "medical_imaging_asset_read",
            "medical_imaging_asset_reviewed",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "synthetic-phase2-scan" not in serialized_metadata
        assert "medical-imaging-assets/" not in serialized_metadata
        assert "tencent-cos-upload.invalid" not in serialized_metadata
        assert "phase2etag" not in serialized_metadata


def test_recovery_plan_review_today_progress_completion_and_safe_boundaries(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)

    task_payload = [
        {
            "category": "medication",
            "title": "Synthetic reviewed medication task",
            "detail": "Demo-only reviewed medication task detail.",
            "due_label": "Today",
            "notification_time": "09:00",
        },
        {
            "category": "exercise",
            "title": "Synthetic reviewed exercise task",
            "detail": "Demo-only reviewed exercise task detail.",
            "due_label": "Today",
        },
        {
            "category": "diet",
            "title": "Synthetic reviewed diet task",
            "detail": "Demo-only reviewed diet task detail.",
            "due_label": "Today",
        },
        {
            "category": "follow_up",
            "title": "Synthetic reviewed follow-up task",
            "detail": "Demo-only reviewed follow-up task detail.",
            "due_label": "Today",
        },
    ]
    plan = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans",
        headers=doctor_headers,
        json={
            "title": "Synthetic reviewed production plan",
            "instructions": "Demo-only production review instructions.",
            "tasks": task_payload,
        },
    )
    assert plan.status_code == 200
    plan_payload = plan.json()
    plan_id = plan_payload["plan_id"]
    assert plan_payload["status"] == "draft"
    assert plan_payload["review_status"] == "draft"
    assert plan_payload["progress_summary"] == {
        "task_count": 4,
        "completed_task_count": 0,
        "remaining_task_count": 4,
        "completion_percent": 0,
    }

    submitted = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/submit-review",
        headers=doctor_headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["review_status"] == "in_review"
    assert submitted.json()["submitted_at"] is not None

    edit_while_in_review = client.put(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}",
        headers=doctor_headers,
        json={
            "title": "Blocked in-review edit",
            "instructions": "Demo-only blocked edit.",
            "tasks": task_payload,
        },
    )
    assert edit_while_in_review.status_code == 409
    assert edit_while_in_review.json()["error"]["code"] == "conflict"

    patient_approve = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
        headers=patient_headers,
    )
    assert patient_approve.status_code == 404
    assert patient_approve.json()["error"]["code"] == "not_found"

    changes = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/request-changes",
        headers=doctor_headers,
    )
    assert changes.status_code == 200
    assert changes.json()["review_status"] == "changes_requested"
    assert changes.json()["reviewed_at"] is not None

    updated_tasks = [dict(task) for task in task_payload]
    updated_tasks[1]["title"] = "Synthetic reviewed exercise task updated"
    updated = client.put(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}",
        headers=doctor_headers,
        json={
            "title": "Synthetic reviewed production plan updated",
            "instructions": "Demo-only production review instructions updated.",
            "tasks": updated_tasks,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["review_status"] == "draft"

    assert (
        client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/submit-review",
            headers=doctor_headers,
        ).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
        headers=doctor_headers,
    )
    assert approved.status_code == 200
    approved_payload = approved.json()
    assert approved_payload["status"] == "active"
    assert approved_payload["review_status"] == "approved"
    assert approved_payload["approved_at"] is not None
    assert approved_payload["activated_at"] is not None

    cross_patient_approve = client.post(
        f"/api/v1/patients/{unrelated_id}/recovery-plans/{plan_id}/approve",
        headers=doctor_headers,
    )
    assert cross_patient_approve.status_code == 404
    assert cross_patient_approve.json()["error"]["code"] == "not_found"

    today = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert today.status_code == 200
    today_payload = today.json()["data"]
    assert today_payload["active_recovery_plan"]["plan_id"] == plan_id
    assert today_payload["today_progress"]["completion_percent"] == 0
    task_ids = [task["task_id"] for task in today_payload["today_tasks"]]

    incomplete_close = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/complete",
        headers=doctor_headers,
    )
    assert incomplete_close.status_code == 422
    assert incomplete_close.json()["error"]["code"] == "validation_failed"

    for task_id in task_ids:
        completed = client.post(
            f"/api/v1/patient/me/tasks/{task_id}/completion",
            headers=patient_headers,
            json={"completed": True},
        )
        assert completed.status_code == 200

    progressed_today = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert progressed_today.status_code == 200
    assert progressed_today.json()["data"]["today_progress"] == {
        "task_count": 4,
        "completed_task_count": 4,
        "remaining_task_count": 0,
        "completion_percent": 100,
    }

    closed = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/complete",
        headers=doctor_headers,
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "completed"
    assert closed.json()["completed_at"] is not None

    after_close_today = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert after_close_today.status_code == 200
    assert plan_id not in str(after_close_today.json()["data"].get("active_recovery_plan"))

    with Session(engine) as db:
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.patient_id == assigned_id)
        ).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "recovery_plan_created",
            "recovery_plan_submitted_for_review",
            "recovery_plan_changes_requested",
            "recovery_plan_updated",
            "recovery_plan_approved",
            "recovery_task_completed",
            "recovery_plan_completed",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Synthetic reviewed production plan" not in serialized_metadata
        assert "Demo-only production review instructions" not in serialized_metadata
        assert "Synthetic reviewed medication task" not in serialized_metadata
        assert "Demo-only reviewed" not in serialized_metadata
