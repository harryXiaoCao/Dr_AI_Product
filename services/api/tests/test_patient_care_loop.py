import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import DoctorNote, MedicalRecord, Medication, PatientProfile
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


def test_doctor_can_search_and_open_assigned_patient_care_bundle(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(doctor["access_token"])

    search = client.get("/api/v1/patients?q=Riley", headers=headers)
    assert search.status_code == 200
    assert len(search.json()["items"]) == 1
    assert search.json()["items"][0]["patient_id"] == str(assigned_id)

    empty_search = client.get("/api/v1/patients?q=NoMatch", headers=headers)
    assert empty_search.status_code == 200
    assert empty_search.json()["items"] == []

    bundle = client.get(f"/api/v1/patients/{assigned_id}/care", headers=headers)
    assert bundle.status_code == 200
    payload = bundle.json()
    assert payload["patient"]["display_name"] == "Riley Demo Patient"
    assert payload["patient"]["relationship_label"] == "Care relationship active"
    assert len(payload["records"]) == 2
    assert len(payload["medications"]) == 2
    assert len(payload["doctor_notes"]) == 1
    assert "Synthetic" in payload["records"][0]["title"]


def test_patient_can_read_own_records_and_medications_but_not_doctor_notes(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    headers = auth_header(patient["access_token"])

    bundle = client.get(f"/api/v1/patients/{assigned_id}/care", headers=headers)
    assert bundle.status_code == 200
    payload = bundle.json()
    assert len(payload["records"]) == 2
    assert len(payload["medications"]) == 2
    assert payload["doctor_notes"] == []

    own_medications = client.get("/api/v1/medications", headers=headers)
    assert own_medications.status_code == 200
    assert len(own_medications.json()["items"]) == 2

    own_care = client.get("/api/v1/patient/me/care", headers=headers)
    assert own_care.status_code == 200
    assert len(own_care.json()["records"]) == 2
    assert own_care.json()["doctor_notes"] == []

    notes = client.get(f"/api/v1/patients/{assigned_id}/doctor-notes", headers=headers)
    assert notes.status_code == 404
    assert notes.json()["error"]["code"] == "not_found"


def test_cross_patient_care_loop_reads_are_neutral_not_found(client: TestClient, settings) -> None:
    _, unrelated_id = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(doctor["access_token"])

    for path in (
        f"/api/v1/patients/{unrelated_id}/records",
        f"/api/v1/patients/{unrelated_id}/medications",
        f"/api/v1/patients/{unrelated_id}/doctor-notes",
        f"/api/v1/patients/{unrelated_id}/care",
    ):
        response = client.get(path, headers=headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


def test_patient_care_loop_empty_states_use_empty_lists(client: TestClient, settings) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    with Session(engine) as db:
        for model in (DoctorNote, MedicalRecord, Medication):
            db.query(model).delete()
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    response = client.get(
        f"/api/v1/patients/{assigned_id}/care",
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["records"] == []
    assert response.json()["medications"] == []
    assert response.json()["doctor_notes"] == []


def test_patient_search_validation_uses_standard_error_envelope(
    client: TestClient, settings
) -> None:
    _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    response = client.get(
        "/api/v1/patients?q=" + ("x" * 81),
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"
