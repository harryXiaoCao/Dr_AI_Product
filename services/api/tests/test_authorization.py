from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import CareRelationship, PatientProfile
from app.seed import seed_database
from tests.helpers import auth_header, login


def test_doctor_patient_roles_and_cross_patient_isolation(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        assigned = db.scalar(
            select(PatientProfile).where(
                PatientProfile.synthetic_identifier == "SYN-PATIENT-001"
            )
        )
        unrelated = db.scalar(
            select(PatientProfile).where(
                PatientProfile.synthetic_identifier == "SYN-PATIENT-002"
            )
        )
        assigned_id = assigned.id
        unrelated_id = unrelated.id

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    doctor_headers = auth_header(doctor["access_token"])
    assert client.get("/api/v1/patients", headers=doctor_headers).status_code == 200
    assert (
        client.get(
            f"/api/v1/patients/{assigned_id}", headers=doctor_headers
        ).status_code
        == 200
    )
    unrelated_probe = client.get(
        f"/api/v1/patients/{unrelated_id}", headers=doctor_headers
    )
    assert unrelated_probe.status_code == 404
    assert unrelated_probe.json()["error"]["code"] == "not_found"

    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    patient_headers = auth_header(patient["access_token"])
    assert (
        client.get(
            f"/api/v1/patients/{assigned_id}", headers=patient_headers
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/patients/{unrelated_id}", headers=patient_headers
        ).status_code
        == 404
    )
    assert client.get("/api/v1/patients", headers=patient_headers).status_code == 404
    assert (
        client.get("/api/v1/patient/me/today", headers=doctor_headers).status_code
        == 404
    )


def test_revoked_relationship_removes_doctor_access(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        relationship = db.scalar(
            select(CareRelationship).where(CareRelationship.is_active.is_(True))
        )
        patient_id = relationship.patient_id
        relationship.is_active = False
        relationship.revoked_at = datetime.now(UTC)
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 404
    assert response.json()["error"]["message"] == (
        "The requested resource was not found."
    )


def test_role_specific_seeded_dashboards(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    doctor_dashboard = client.get(
        "/api/v1/me/dashboard", headers=auth_header(doctor["access_token"])
    )
    assert doctor_dashboard.status_code == 200
    assert doctor_dashboard.json()["role"] == "doctor"
    assert doctor_dashboard.json()["data"]["hospital"]["name"].startswith("Synthetic")

    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    patient_dashboard = client.get(
        "/api/v1/patient/me/today", headers=auth_header(patient["access_token"])
    )
    assert patient_dashboard.status_code == 200
    assert patient_dashboard.json()["role"] == "patient"
    assert patient_dashboard.json()["data"]["medical_records"] == []
