import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    AuditEvent,
    ClinicalEvent,
    ClinicalEventUpdate,
    MedicalHistoryReview,
    MedicalImagingAsset,
    Notification,
    PatientProfile,
    User,
)
from app.seed import seed_database
from tests.helpers import auth_header, login, register

PHASE2_TABLES = {
    "patient_allergies",
    "chronic_diseases",
    "visit_history",
    "diagnoses",
    "medical_imaging_assets",
    "clinical_events",
    "clinical_event_updates",
    "medical_history_reviews",
}
PHASE2_EVENT_LINK_TABLES = {
    "medications",
    "doctor_notes",
    "visit_history",
    "diagnoses",
    "medical_imaging_assets",
    "recovery_plans",
    "consultation_requests",
    "prescriptions",
    "medication_reminders",
    "notifications",
}
PHASE2_RECOVERY_COLUMNS = {
    "review_status",
    "review_actor_user_id",
    "submitted_at",
    "reviewed_at",
    "approved_at",
    "completed_at",
}
PHASE2_IMAGING_FINDING_COLUMNS = {
    "finding_summary",
    "measurement_summary",
    "observed_at",
    "treatment_relevance_date",
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


def _reviewer_context(client: TestClient, settings) -> tuple[dict[str, str], uuid.UUID]:
    tokens = login(
        client,
        "reviewer.doctor@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    with Session(engine) as db:
        reviewer = db.scalar(select(User).where(User.email == "reviewer.doctor@example.com"))
        reviewer_doctor_id = reviewer.doctor_profile.id
    return auth_header(tokens["access_token"]), reviewer_doctor_id


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
        imaging_columns = set(
            db.scalars(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'medical_imaging_assets'"
                )
            ).all()
        )
        assert PHASE2_IMAGING_FINDING_COLUMNS.issubset(imaging_columns)
        for table_name in PHASE2_EVENT_LINK_TABLES:
            columns = set(
                db.scalars(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        f"WHERE table_name = '{table_name}'"
                    )
                ).all()
            )
            assert "clinical_event_id" in columns, table_name


def test_registered_accounts_can_connect_and_create_care_from_zero(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="zero.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email="zero.doctor@example.com",
        password="Doctor9!",
        role="doctor",
    )
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])

    own_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert own_care.status_code == 200
    patient_id = own_care.json()["patient"]["patient_id"]
    patient_code = own_care.json()["patient"]["synthetic_identifier"]
    patient_display_name = own_care.json()["patient"]["display_name"]
    assert patient_code.startswith("PAT-")
    assert own_care.json()["clinical_events"] == []
    assert own_care.json()["allergies"] == []
    contacts_before = client.get(
        "/api/v1/patient/me/contacts",
        headers=patient_headers,
    )
    assert contacts_before.status_code == 200
    assert contacts_before.json()["items"] == []

    patients_before = client.get("/api/v1/patients", headers=doctor_headers)
    assert patients_before.status_code == 200
    assert patients_before.json()["items"] == []

    patient_probe_before = client.get(
        f"/api/v1/patients/{patient_id}/care",
        headers=doctor_headers,
    )
    assert patient_probe_before.status_code == 404
    assert patient_probe_before.json()["error"]["code"] == "not_found"

    preview = client.post(
        "/api/v1/patients/connect/preview",
        headers=doctor_headers,
        json={"patient_code": patient_code.lower()},
    )
    assert preview.status_code == 200
    assert preview.json()["display_name"] == patient_display_name
    assert preview.json()["masked_patient_code"].endswith(patient_code[-4:])
    assert client.get("/api/v1/patients", headers=doctor_headers).json()["items"] == []

    connected = client.post(
        "/api/v1/patients/connect",
        headers=doctor_headers,
        json={"patient_code": patient_code.lower()},
    )
    assert connected.status_code == 200
    assert connected.json()["patient_id"] == patient_id

    repeated = client.post(
        "/api/v1/patients/connect",
        headers=doctor_headers,
        json={"patient_code": patient_code},
    )
    assert repeated.status_code == 200

    pending = client.get("/api/v1/patient/me/contacts", headers=patient_headers).json()["items"][0]
    approved_connection = client.post(
        f"/api/v1/patient/me/doctor-relationships/{pending['relationship_id']}/approve",
        headers=patient_headers,
        json={"expected_version": pending["request_version"]},
    )
    assert approved_connection.status_code == 200

    patients_after = client.get("/api/v1/patients", headers=doctor_headers)
    assert patients_after.status_code == 200
    assert [item["patient_id"] for item in patients_after.json()["items"]] == [patient_id]

    second_doctor = register(
        client,
        email="zero.doctor.two@example.com",
        password="Doctor9!",
        role="doctor",
    )
    second_doctor_headers = auth_header(second_doctor["access_token"])
    second_connection = client.post(
        "/api/v1/patients/connect",
        headers=second_doctor_headers,
        json={"patient_code": patient_code},
    )
    assert second_connection.status_code == 200

    contacts_after = client.get(
        "/api/v1/patient/me/contacts",
        headers=patient_headers,
    )
    assert contacts_after.status_code == 200
    contact_items = contacts_after.json()["items"]
    assert len(contact_items) == 2
    assert len({contact["doctor_id"] for contact in contact_items}) == 2
    assert all(contact["display_name"] == "Doctor profile" for contact in contact_items)

    doctor_contact_probe = client.get(
        "/api/v1/patient/me/contacts",
        headers=doctor_headers,
    )
    assert doctor_contact_probe.status_code == 404

    created_event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "From-zero care episode",
            "chief_complaint": "From-zero onboarding symptom",
            "symptom_summary": "Created after invite signup and patient-code connection.",
            "diagnosis_summary": "Doctor-owned provisional text for test only.",
            "status": "active",
        },
    )
    assert created_event.status_code == 200
    assert created_event.json()["title"] == "From-zero care episode"

    with Session(engine) as db:
        relationship_audits = db.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "care_relationship_requested")
        ).all()
        assert len(relationship_audits) == 3
        assert relationship_audits[0].metadata_json["patient_code_supplied"] is True
        assert patient_code not in str(relationship_audits[0].metadata_json)


def test_patient_can_update_allowed_profile_and_allergy_surfaces(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    headers = _patient_headers(client, settings)
    records_before = client.get(
        "/api/v1/patient/me/care",
        headers=headers,
    ).json()["records"]

    profile_response = client.patch(
        "/api/v1/patient/me/profile",
        headers=headers,
        json={
            "display_name": "曹",
            "birth_year": 1988,
            "sex": "not specified",
            "preferred_language": "English",
            "contact_preference": "in-app",
            "height_cm": 168,
            "weight_kg": 62.5,
            "blood_type": "A+",
            "systolic_blood_pressure": 118,
            "diastolic_blood_pressure": 76,
            "smoking_status": "Never",
            "alcohol_consumption": "None or rare",
            "heart_history": "Occasional palpitations under review",
            "patient_reported_medications": "Daily multivitamin",
            "surgery_history": "Appendectomy in childhood",
            "family_history": "Parent with hypertension",
            "lifestyle_notes": "Walks most evenings",
            "pregnancy_status": "Not applicable",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["display_name"] == "曹"
    assert profile_response.json()["demographics"]["birth_year"] == 1988
    assert profile_response.json()["demographics"]["height_cm"] == 168
    assert profile_response.json()["demographics"]["weight_kg"] == 62.5
    assert profile_response.json()["demographics"]["blood_type"] == "A+"
    assert profile_response.json()["demographics"]["systolic_blood_pressure"] == 118
    assert profile_response.json()["demographics"]["diastolic_blood_pressure"] == 76
    assert profile_response.json()["demographics"]["heart_history"] == (
        "Occasional palpitations under review"
    )

    unchanged_response = client.patch(
        "/api/v1/patient/me/profile",
        headers=headers,
        json={"blood_type": "A+"},
    )
    assert unchanged_response.status_code == 200
    assert unchanged_response.json()["demographics"]["blood_type"] == "A+"
    records_after = client.get(
        "/api/v1/patient/me/care",
        headers=headers,
    ).json()["records"]
    assert len(records_after) == len(records_before)

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
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
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
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
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


def test_clinical_event_links_phase2_resources_with_safe_boundaries(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)

    event_response = client.post(
        f"/api/v1/patients/{assigned_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Synthetic headache care episode",
            "chief_complaint": "Synthetic headache follow-up",
            "symptom_summary": "Demo-only symptom summary.",
            "diagnosis_summary": "Demo-only provisional diagnosis summary.",
            "onset_date": "2026-07-01",
            "status": "active",
        },
    )
    assert event_response.status_code == 200
    event_payload = event_response.json()
    event_id = event_payload["id"]
    assert event_payload["linked_resource_counts"]["diagnoses"] == 0

    updated_event = client.put(
        f"/api/v1/patients/{assigned_id}/clinical-events/{event_id}",
        headers=doctor_headers,
        json={
            "title": "Synthetic headache care episode updated",
            "chief_complaint": "Synthetic headache monitoring",
            "symptom_summary": "Updated demo-only symptom summary.",
            "diagnosis_summary": "Updated demo-only diagnosis summary.",
            "onset_date": "2026-07-01",
            "status": "monitoring",
        },
    )
    assert updated_event.status_code == 200
    assert updated_event.json()["status"] == "monitoring"

    patient_event_list = client.get("/api/v1/patient/me/clinical-events", headers=patient_headers)
    assert patient_event_list.status_code == 200
    assert patient_event_list.json()["items"][0]["id"] == event_id

    patient_event_detail = client.get(
        f"/api/v1/patient/me/clinical-events/{event_id}",
        headers=patient_headers,
    )
    assert patient_event_detail.status_code == 200
    assert (
        patient_event_detail.json()["diagnosis_summary"] == "Updated demo-only diagnosis summary."
    )

    patient_update = client.post(
        f"/api/v1/patient/me/clinical-events/{event_id}/updates",
        headers=patient_headers,
        json={
            "update_type": "symptom_update",
            "summary": "Patient self-reported demo-only symptom update.",
            "occurred_at": "2026-07-08T12:00:00Z",
        },
    )
    assert patient_update.status_code == 200
    patient_update_payload = patient_update.json()
    assert patient_update_payload["clinical_event_id"] == event_id
    assert patient_update_payload["update_type"] == "symptom_update"

    patient_updates = client.get(
        f"/api/v1/patient/me/clinical-events/{event_id}/updates",
        headers=patient_headers,
    )
    assert patient_updates.status_code == 200
    assert patient_updates.json()["items"][0]["id"] == patient_update_payload["id"]

    patient_event_update = client.put(
        f"/api/v1/patients/{assigned_id}/clinical-events/{event_id}",
        headers=patient_headers,
        json={
            "title": "Blocked patient event update",
            "chief_complaint": "Blocked patient complaint",
        },
    )
    assert patient_event_update.status_code == 404
    assert patient_event_update.json()["error"]["code"] == "not_found"

    cross_patient_event = client.post(
        f"/api/v1/patients/{unrelated_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Blocked cross-patient event",
            "chief_complaint": "Blocked cross-patient complaint",
        },
    )
    assert cross_patient_event.status_code == 404
    assert cross_patient_event.json()["error"]["code"] == "not_found"

    medication = client.post(
        f"/api/v1/patients/{assigned_id}/medications",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "name": "Synthetic event medication",
            "dosage": "Demo dose",
            "schedule": "Demo schedule",
            "status": "active",
            "note": "Demo-only event medication note.",
        },
    )
    assert medication.status_code == 200
    medication_id = medication.json()["id"]
    assert medication.json()["clinical_event_id"] == event_id

    visit = client.post(
        f"/api/v1/patients/{assigned_id}/visit-history",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "visit_type": "follow_up",
            "title": "Synthetic event update",
            "summary": "Demo-only event update summary.",
            "occurred_at": "2026-07-08T09:00:00Z",
            "clinician_label": "Demo clinician",
        },
    )
    assert visit.status_code == 200
    assert visit.json()["clinical_event_id"] == event_id

    diagnosis = client.post(
        f"/api/v1/patients/{assigned_id}/diagnoses",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "label": "Synthetic event diagnosis",
            "status": "active",
            "diagnosed_on": "2026-07-08",
            "notes": "Demo-only event diagnosis note.",
        },
    )
    assert diagnosis.status_code == 200
    diagnosis_id = diagnosis.json()["id"]
    assert diagnosis.json()["clinical_event_id"] == event_id

    patient_diagnosis_update = client.put(
        f"/api/v1/patients/{assigned_id}/diagnoses/{diagnosis_id}",
        headers=patient_headers,
        json={
            "clinical_event_id": event_id,
            "label": "Blocked patient diagnosis edit",
            "status": "resolved",
        },
    )
    assert patient_diagnosis_update.status_code == 404
    assert patient_diagnosis_update.json()["error"]["code"] == "not_found"

    note = client.post(
        f"/api/v1/patients/{assigned_id}/doctor-notes",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "title": "Synthetic event note",
            "body": "Demo-only event note body.",
        },
    )
    assert note.status_code == 200
    assert note.json()["clinical_event_id"] == event_id

    prescription = client.post(
        f"/api/v1/patients/{assigned_id}/prescriptions",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "status": "issued",
            "issued_at": "2026-07-08T10:00:00Z",
            "notes": "Demo-only event prescription note.",
            "medications": [
                {
                    "medication_id": medication_id,
                    "name": "Synthetic event medication",
                    "dosage": "Demo dose",
                    "schedule": "Demo schedule",
                }
            ],
        },
    )
    assert prescription.status_code == 200
    prescription_id = prescription.json()["id"]
    assert prescription.json()["clinical_event_id"] == event_id
    prescription_line_id = prescription.json()["medications"][0]["id"]

    reminder = client.post(
        f"/api/v1/patients/{assigned_id}/medication-reminders",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "prescription_medication_id": prescription_line_id,
            "reminder_type": "medication",
            "schedule_label": "Demo event medication reminder",
            "channel": "in_app",
            "status": "active",
            "next_due_at": "2026-07-08T11:00:00Z",
        },
    )
    assert reminder.status_code == 200
    reminder_id = reminder.json()["id"]
    assert reminder.json()["clinical_event_id"] == event_id

    imaging = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/presign",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "filename": "event-image.png",
            "content_type": "image/png",
            "size_bytes": 1024,
        },
    )
    assert imaging.status_code == 200
    asset_id = imaging.json()["asset_id"]
    assert imaging.json()["clinical_event_id"] == event_id

    uploaded_imaging = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=b"x" * 1024,
    )
    assert uploaded_imaging.status_code == 200
    completed_imaging = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={"uploaded_size_bytes": 1024},
    )
    assert completed_imaging.status_code == 200
    assert completed_imaging.json()["clinical_event_id"] == event_id

    reviewed_imaging = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/review",
        headers=doctor_headers,
        json={
            "review_status": "reviewed",
            "finding_summary": "Manual demo-only imaging finding.",
            "measurement_summary": "Manual demo-only measurement.",
            "observed_at": "2026-07-08T10:30:00Z",
            "treatment_relevance_date": "2026-07-08",
        },
    )
    assert reviewed_imaging.status_code == 200
    assert reviewed_imaging.json()["finding_summary"] == "Manual demo-only imaging finding."
    assert reviewed_imaging.json()["measurement_summary"] == "Manual demo-only measurement."

    recovery_plan = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans",
        headers=doctor_headers,
        json={
            "clinical_event_id": event_id,
            "title": "Synthetic event recovery plan",
            "instructions": "Demo-only event recovery instructions.",
            "tasks": [
                {
                    "category": "medication",
                    "title": "Synthetic event medication task",
                    "detail": "Demo-only event medication task.",
                    "due_label": "Today",
                    "notification_time": "09:00",
                    "medication_id": medication_id,
                },
                {
                    "category": "exercise",
                    "title": "Synthetic event exercise task",
                    "detail": "Demo-only event exercise task.",
                    "due_label": "Daily",
                },
                {
                    "category": "diet",
                    "title": "Synthetic event diet task",
                    "detail": "Demo-only event diet task.",
                    "due_label": "Daily",
                },
                {
                    "category": "follow_up",
                    "title": "Synthetic event follow-up task",
                    "detail": "Demo-only event follow-up task.",
                    "due_label": "This week",
                },
            ],
        },
    )
    assert recovery_plan.status_code == 200
    assert recovery_plan.json()["clinical_event_id"] == event_id

    consultation = client.post(
        "/api/v1/consultations",
        headers=doctor_headers,
        json={
            "patient_id": str(assigned_id),
            "clinical_event_id": event_id,
            "specialty": "Synthetic neurology",
            "question_summary": "Demo-only specialist review question.",
            "priority": "routine",
        },
    )
    assert consultation.status_code == 200
    assert consultation.json()["clinical_event_id"] == event_id

    care = client.get(f"/api/v1/patients/{assigned_id}/care", headers=doctor_headers)
    assert care.status_code == 200
    care_payload = care.json()
    linked_event = care_payload["clinical_events"][0]
    assert linked_event["id"] == event_id
    assert linked_event["patient_updates"][0]["id"] == patient_update_payload["id"]
    assert linked_event["linked_resource_counts"]["diagnoses"] == 1
    assert linked_event["linked_resource_counts"]["prescriptions"] == 1
    assert linked_event["linked_resource_counts"]["recovery_plans"] == 1
    assert linked_event["linked_resource_counts"]["imaging_assets"] == 1
    timeline_types = {entry["entry_type"] for entry in linked_event["timeline"]}
    assert {
        "clinical_event_created",
        "encounter_update",
        "diagnosis_updated",
        "prescription_issued",
        "imaging_review",
        "recovery_plan_updated",
        "doctor_note",
        "consultation_requested",
        "patient_update",
    }.issubset(timeline_types)
    assert care_payload["visit_history"][0]["clinical_event_id"] == event_id
    assert care_payload["diagnoses"][0]["clinical_event_id"] == event_id
    assert care_payload["doctor_notes"][0]["clinical_event_id"] == event_id
    assert any(
        item["id"] == medication_id and item["clinical_event_id"] == event_id
        for item in care_payload["medications"]
    )
    assert any(
        item["id"] == prescription_id and item["clinical_event_id"] == event_id
        for item in care_payload["prescriptions"]
    )
    assert any(
        item["id"] == reminder_id and item["clinical_event_id"] == event_id
        for item in care_payload["medication_reminders"]
    )
    assert care_payload["imaging_assets"][0]["clinical_event_id"] == event_id
    assert (
        care_payload["imaging_assets"][0]["finding_summary"] == "Manual demo-only imaging finding."
    )
    assert care_payload["recovery_plans"][0]["clinical_event_id"] == event_id
    assert care_payload["clinical_event_updates"][0]["id"] == patient_update_payload["id"]

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200
    assert patient_care.json()["clinical_events"][0]["id"] == event_id
    assert (
        patient_care.json()["clinical_events"][0]["diagnosis_summary"]
        == "Updated demo-only diagnosis summary."
    )
    assert patient_care.json()["clinical_event_updates"][0]["id"] == patient_update_payload["id"]
    assert patient_care.json()["doctor_notes"] == []

    with Session(engine) as db:
        event = db.get(ClinicalEvent, uuid.UUID(event_id))
        assert event is not None
        update = db.get(ClinicalEventUpdate, uuid.UUID(patient_update_payload["id"]))
        assert update is not None
        assert update.clinical_event_id == event.id
        notification = db.scalar(
            select(Notification).where(Notification.clinical_event_id == event.id)
        )
        assert notification is not None
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "clinical_event_created",
            "clinical_event_updated",
            "clinical_events_listed",
            "clinical_event_read",
            "clinical_event_patient_update_created",
            "patient_care_bundle_read",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Synthetic headache" not in serialized_metadata
        assert "Demo-only event" not in serialized_metadata
        assert "event-image.png" not in serialized_metadata
        assert "Manual demo-only imaging finding" not in serialized_metadata
        assert "Patient self-reported demo-only symptom update" not in serialized_metadata


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


def test_active_recovery_plan_replacement_is_scoped_to_clinical_event(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    reviewer_headers, reviewer_doctor_id = _reviewer_context(client, settings)
    task_payload = [
        {
            "category": "medication",
            "title": "Synthetic medication task",
            "detail": "Demo-only medication task detail.",
            "due_label": "Today",
            "scheduled_date": datetime.now(UTC).date().isoformat(),
            "notification_time": "09:00",
        },
        {
            "category": "exercise",
            "title": "Synthetic exercise task",
            "detail": "Demo-only exercise task detail.",
            "due_label": "Today",
        },
        {
            "category": "diet",
            "title": "Synthetic diet task",
            "detail": "Demo-only diet task detail.",
            "due_label": "Today",
        },
        {
            "category": "follow_up",
            "title": "Synthetic follow-up task",
            "detail": "Demo-only follow-up task detail.",
            "due_label": "Today",
        },
    ]
    for task in task_payload:
        task["scheduled_date"] = datetime.now(UTC).date().isoformat()

    def create_event(title: str) -> str:
        response = client.post(
            f"/api/v1/patients/{assigned_id}/clinical-events",
            headers=doctor_headers,
            json={
                "title": title,
                "chief_complaint": "Synthetic event complaint",
                "symptom_summary": "Demo-only symptom summary.",
                "diagnosis_summary": "Demo-only diagnosis summary.",
                "onset_date": "2026-07-08",
                "status": "active",
            },
        )
        assert response.status_code == 200
        return response.json()["id"]

    def create_and_approve_plan(event_id: str, title: str) -> str:
        created = client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans",
            headers=doctor_headers,
            json={
                "clinical_event_id": event_id,
                "title": title,
                "instructions": "Demo-only event-scoped recovery instructions.",
                "tasks": task_payload,
            },
        )
        assert created.status_code == 200
        plan_id = created.json()["plan_id"]
        submitted = client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/submit-review",
            headers=doctor_headers,
            json={
                "reviewer_doctor_id": str(reviewer_doctor_id),
                "expected_version": created.json()["version"],
            },
        )
        assert submitted.status_code == 200
        approved = client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
            headers=doctor_headers,
            json={"expected_version": created.json()["version"]},
        )
        assert approved.status_code == 404
        approved = client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
            headers=reviewer_headers,
            json={"expected_version": created.json()["version"]},
        )
        assert approved.status_code == 200
        activated = client.post(
            f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/activate",
            headers=doctor_headers,
        )
        assert activated.status_code == 200
        assert activated.json()["status"] == "active"
        return plan_id

    event_a = create_event("Synthetic event A")
    event_b = create_event("Synthetic event B")
    plan_a = create_and_approve_plan(event_a, "Synthetic event A plan")
    plan_b = create_and_approve_plan(event_b, "Synthetic event B plan")
    replacement_a = create_and_approve_plan(event_a, "Synthetic event A replacement plan")

    plans = client.get(f"/api/v1/patients/{assigned_id}/recovery-plans", headers=doctor_headers)
    assert plans.status_code == 200
    status_by_id = {item["plan_id"]: item["status"] for item in plans.json()["items"]}
    assert status_by_id[plan_a] == "completed"
    assert status_by_id[plan_b] == "active"
    assert status_by_id[replacement_a] == "active"


def test_doctor_can_review_patient_entered_history_without_overwriting_it(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)

    allergy = client.post(
        f"/api/v1/patients/{assigned_id}/allergies",
        headers=patient_headers,
        json={
            "label": "Synthetic patient-entered allergy",
            "reaction": "Demo-only patient-entered reaction",
            "severity": "moderate",
            "status": "active",
        },
    )
    assert allergy.status_code == 200
    allergy_payload = allergy.json()

    patient_review_attempt = client.post(
        f"/api/v1/patients/{assigned_id}/medical-history-reviews",
        headers=patient_headers,
        json={
            "target_type": "allergy",
            "target_id": allergy_payload["id"],
            "action": "verified",
        },
    )
    assert patient_review_attempt.status_code == 404
    assert patient_review_attempt.json()["error"]["code"] == "not_found"

    verified = client.post(
        f"/api/v1/patients/{assigned_id}/medical-history-reviews",
        headers=doctor_headers,
        json={
            "target_type": "allergy",
            "target_id": allergy_payload["id"],
            "action": "verified",
        },
    )
    assert verified.status_code == 200
    assert verified.json()["action"] == "verified"

    amendment = client.post(
        f"/api/v1/patients/{assigned_id}/medical-history-reviews",
        headers=doctor_headers,
        json={
            "target_type": "allergy",
            "target_id": allergy_payload["id"],
            "action": "amendment",
            "amendment_summary": "Doctor amendment: synthetic review note.",
        },
    )
    assert amendment.status_code == 200
    amendment_payload = amendment.json()
    assert amendment_payload["amendment_summary"] == "Doctor amendment: synthetic review note."

    cross_patient_review = client.post(
        f"/api/v1/patients/{unrelated_id}/medical-history-reviews",
        headers=doctor_headers,
        json={
            "target_type": "allergy",
            "target_id": allergy_payload["id"],
            "action": "verified",
        },
    )
    assert cross_patient_review.status_code == 404
    assert cross_patient_review.json()["error"]["code"] == "not_found"

    care = client.get(f"/api/v1/patients/{assigned_id}/care", headers=doctor_headers)
    assert care.status_code == 200
    care_payload = care.json()
    assert care_payload["allergies"][0]["label"] == "Synthetic patient-entered allergy"
    assert care_payload["medical_history_reviews"][0]["id"] == amendment_payload["id"]

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200
    assert patient_care.json()["medical_history_reviews"][0]["id"] == amendment_payload["id"]

    with Session(engine) as db:
        review = db.get(MedicalHistoryReview, uuid.UUID(amendment_payload["id"]))
        assert review is not None
        assert review.target_id == uuid.UUID(allergy_payload["id"])
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
        event_types = {audit.event_type for audit in audits}
        assert "medical_history_review_created" in event_types
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Synthetic patient-entered allergy" not in serialized_metadata
        assert "Doctor amendment: synthetic review note" not in serialized_metadata


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
    assert updated_prescription.status_code == 409
    assert "replacement" in updated_prescription.json()["error"]["message"].lower()

    replacement_prescription = client.post(
        f"/api/v1/patients/{assigned_id}/prescriptions",
        headers=doctor_headers,
        json={
            "status": "issued",
            "issued_at": "2026-07-07T11:00:00Z",
            "notes": "Updated synthetic prescription note.",
            "supersedes_prescription_id": prescription_id,
            "idempotency_key": "phase2-prescription-replacement",
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
    assert replacement_prescription.status_code == 200
    replacement_payload = replacement_prescription.json()
    assert replacement_payload["supersedes_prescription_id"] == prescription_id
    assert replacement_payload["version"] == 2
    line_id = replacement_payload["medications"][0]["id"]

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
    assert {item["id"] for item in care_payload["prescriptions"]} >= {
        prescription_id,
        replacement_payload["id"],
    }
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
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "medication_created",
            "medication_updated",
            "prescription_created",
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
    assert presign_payload["storage_provider"] == "local"
    assert presign_payload["upload_status"] == "pending_upload"
    assert presign_payload["review_status"] == "not_ready"
    assert "object_key" not in presign_payload

    content = b"x" * 4096
    wrong_content_type = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/jpeg"},
        content=content,
    )
    assert wrong_content_type.status_code == 415
    wrong_size = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=content[:-1],
    )
    assert wrong_size.status_code == 422
    uploaded = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=content,
    )
    assert uploaded.status_code == 200, uploaded.text
    assert (
        uploaded.json()["provenance_versions"][0]["checksum_sha256"]
        == hashlib.sha256(content).hexdigest()
    )
    replayed_upload = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=content,
    )
    assert replayed_upload.status_code == 200
    assert len(replayed_upload.json()["provenance_versions"]) == 1
    conflicting_upload = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=b"y" * 4096,
    )
    assert conflicting_upload.status_code == 409
    complete = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={
            "uploaded_size_bytes": 4096,
            "etag": f'"{hashlib.sha256(content).hexdigest()}"',
            "checksum_sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    assert complete.status_code == 200
    complete_payload = complete.json()
    assert complete_payload["upload_status"] == "uploaded"
    assert complete_payload["review_status"] == "pending_review"
    assert "object_key" not in complete_payload
    replayed_complete = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={
            "uploaded_size_bytes": 4096,
            "checksum_sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    assert replayed_complete.status_code == 200

    doctor_list = client.get(f"/api/v1/patients/{assigned_id}/imaging", headers=doctor_headers)
    assert doctor_list.status_code == 200
    assert doctor_list.json()["items"][0]["id"] == asset_id

    patient_list = client.get("/api/v1/patient/me/imaging", headers=patient_headers)
    assert patient_list.status_code == 200
    assert patient_list.json()["items"][0]["id"] == asset_id

    patient_detail = client.get(f"/api/v1/patient/me/imaging/{asset_id}", headers=patient_headers)
    assert patient_detail.status_code == 200
    assert patient_detail.json()["review_status"] == "pending_review"
    patient_download = client.get(
        f"/api/v1/patients/{assigned_id}/imaging/{asset_id}/download",
        headers=patient_headers,
    )
    assert patient_download.status_code == 200
    assert patient_download.content == content

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
        json={
            "review_status": "reviewed",
            "finding_summary": "Manual synthetic imaging result.",
            "measurement_summary": "Manual synthetic measurement.",
            "observed_at": "2026-07-08T10:30:00Z",
            "treatment_relevance_date": "2026-07-08",
        },
    )
    assert review.status_code == 200
    assert review.json()["review_status"] == "reviewed"
    assert review.json()["finding_summary"] == "Manual synthetic imaging result."
    assert review.json()["measurement_summary"] == "Manual synthetic measurement."
    assert review.json()["reviewed_at"] is not None

    cross_patient_complete = client.post(
        f"/api/v1/patients/{unrelated_id}/imaging/{asset_id}/complete",
        headers=doctor_headers,
        json={"uploaded_size_bytes": 4096},
    )
    assert cross_patient_complete.status_code == 404
    assert cross_patient_complete.json()["error"]["code"] == "not_found"
    cross_patient_upload = client.put(
        f"/api/v1/patients/{unrelated_id}/imaging/{asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=content,
    )
    assert cross_patient_upload.status_code == 404
    assert cross_patient_upload.json()["error"]["code"] == "not_found"
    cross_patient_download = client.get(
        f"/api/v1/patients/{unrelated_id}/imaging/{asset_id}/download",
        headers=doctor_headers,
    )
    assert cross_patient_download.status_code == 404
    assert cross_patient_download.json()["error"]["code"] == "not_found"

    expiring = client.post(
        f"/api/v1/patients/{assigned_id}/imaging/presign",
        headers=doctor_headers,
        json={
            "filename": "synthetic-expired-retry.png",
            "content_type": "image/png",
            "size_bytes": 16,
        },
    )
    assert expiring.status_code == 200
    expired_asset_id = expiring.json()["asset_id"]
    with Session(engine) as db:
        expired_asset = db.get(MedicalImagingAsset, expired_asset_id)
        assert expired_asset is not None
        expired_asset.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    expired_upload = client.put(
        f"/api/v1/patients/{assigned_id}/imaging/{expired_asset_id}/content",
        headers={**doctor_headers, "Content-Type": "image/png"},
        content=b"z" * 16,
    )
    assert expired_upload.status_code == 409
    assert expired_upload.json()["error"]["code"] == "conflict"

    patient_care = client.get("/api/v1/patient/me/care", headers=patient_headers)
    assert patient_care.status_code == 200
    assert any(
        item["id"] == asset_id and item["upload_status"] == "uploaded"
        for item in patient_care.json()["imaging_assets"]
    )
    assert any(
        item["id"] == expired_asset_id and item["upload_status"] == "expired"
        for item in patient_care.json()["imaging_assets"]
    )

    with Session(engine) as db:
        asset = db.scalar(select(MedicalImagingAsset).where(MedicalImagingAsset.id == asset_id))
        assert asset is not None
        assert asset.object_key.startswith("medical-imaging-assets/")
        assert asset.upload_status == "uploaded"
        assert asset.review_status == "reviewed"
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "medical_imaging_upload_presigned",
            "medical_imaging_upload_completed",
            "medical_imaging_assets_listed",
            "medical_imaging_asset_read",
            "medical_imaging_asset_reviewed",
            "medical_imaging_bytes_verified",
            "medical_imaging_bytes_downloaded",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "synthetic-phase2-scan" not in serialized_metadata
        assert "medical-imaging-assets/" not in serialized_metadata
        assert "tencent-cos-upload.invalid" not in serialized_metadata
        assert "phase2etag" not in serialized_metadata
        assert "Manual synthetic imaging result" not in serialized_metadata
        assert "Manual synthetic measurement" not in serialized_metadata


def test_recovery_plan_review_today_progress_completion_and_safe_boundaries(
    client: TestClient, settings
) -> None:
    assigned_id, unrelated_id = _seed_patient_ids(settings)
    doctor_headers = _doctor_headers(client, settings)
    patient_headers = _patient_headers(client, settings)
    reviewer_headers, reviewer_doctor_id = _reviewer_context(client, settings)

    task_payload = [
        {
            "category": "medication",
            "title": "Synthetic reviewed medication task",
            "detail": "Demo-only reviewed medication task detail.",
            "due_label": "Today",
            "scheduled_date": datetime.now(UTC).date().isoformat(),
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
    for task in task_payload:
        task["scheduled_date"] = datetime.now(UTC).date().isoformat()
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
        json={
            "reviewer_doctor_id": str(reviewer_doctor_id),
            "expected_version": plan_payload["version"],
        },
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
        json={"expected_version": plan_payload["version"]},
    )
    assert patient_approve.status_code == 404
    assert patient_approve.json()["error"]["code"] == "not_found"

    changes = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/request-changes",
        headers=doctor_headers,
        json={
            "expected_version": plan_payload["version"],
            "comment": "Synthetic changes requested.",
        },
    )
    assert changes.status_code == 404
    changes = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/request-changes",
        headers=reviewer_headers,
        json={
            "expected_version": plan_payload["version"],
            "comment": "Synthetic changes requested.",
        },
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
            json={
                "reviewer_doctor_id": str(reviewer_doctor_id),
                "expected_version": updated.json()["version"],
            },
        ).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
        headers=doctor_headers,
        json={"expected_version": updated.json()["version"]},
    )
    assert approved.status_code == 404
    approved = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/approve",
        headers=reviewer_headers,
        json={"expected_version": updated.json()["version"]},
    )
    assert approved.status_code == 200
    approved_payload = approved.json()
    assert approved_payload["status"] == "approved"
    assert approved_payload["review_status"] == "approved"
    assert approved_payload["approved_at"] is not None
    assert approved_payload["activated_at"] is None
    activated = client.post(
        f"/api/v1/patients/{assigned_id}/recovery-plans/{plan_id}/activate",
        headers=doctor_headers,
    )
    assert activated.status_code == 200

    cross_patient_approve = client.post(
        f"/api/v1/patients/{unrelated_id}/recovery-plans/{plan_id}/approve",
        headers=doctor_headers,
        json={"expected_version": updated.json()["version"]},
    )
    assert cross_patient_approve.status_code == 404
    assert cross_patient_approve.json()["error"]["code"] == "not_found"

    today = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert today.status_code == 200
    today_payload = today.json()["data"]
    assert today_payload["active_recovery_plan"]["plan_id"] == plan_id
    assert today_payload["today_progress"]["completion_percent"] == 0
    task_ids = [task["task_id"] for task in today_payload["today_tasks"]]

    first_complete = client.post(
        f"/api/v1/patient/me/tasks/{task_ids[0]}/completion",
        headers=patient_headers,
        json={"completed": True},
    )
    assert first_complete.status_code == 200
    assert first_complete.json()["task"]["is_completed"] is True

    first_uncomplete = client.delete(
        f"/api/v1/patient/me/tasks/{task_ids[0]}/completion",
        headers=patient_headers,
    )
    assert first_uncomplete.status_code == 200
    assert first_uncomplete.json()["task"]["is_completed"] is False

    after_uncomplete = client.get("/api/v1/patient/me/today", headers=patient_headers)
    assert after_uncomplete.status_code == 200
    assert after_uncomplete.json()["data"]["today_progress"]["completed_task_count"] == 0

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
        audits = db.scalars(select(AuditEvent).where(AuditEvent.patient_id == assigned_id)).all()
        event_types = {audit.event_type for audit in audits}
        assert {
            "recovery_plan_created",
            "recovery_plan_submitted_for_review",
            "recovery_plan_changes_requested",
            "recovery_plan_updated",
            "recovery_plan_approved",
            "recovery_task_completed",
            "recovery_task_uncompleted",
            "recovery_plan_completed",
        }.issubset(event_types)
        serialized_metadata = " ".join(str(audit.metadata_json) for audit in audits)
        assert "Synthetic reviewed production plan" not in serialized_metadata
        assert "Demo-only production review instructions" not in serialized_metadata
        assert "Synthetic reviewed medication task" not in serialized_metadata
        assert "Demo-only reviewed" not in serialized_metadata
