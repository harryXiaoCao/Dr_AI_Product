import logging

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import PatientProfile
from app.seed import seed_database
from tests.helpers import auth_header, login


def test_validation_uses_standard_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": ""},
    )

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "validation_failed"
    assert body["error"]["request_id"].startswith("req_")
    assert body["error"]["details"]
    assert body["error"]["details"][0]["message"] == ("The supplied value is invalid.")


def test_logs_do_not_contain_credentials_tokens_or_synthetic_content(
    client: TestClient, settings, caplog
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        assigned = db.scalar(
            select(PatientProfile).where(PatientProfile.synthetic_identifier == "SYN-PATIENT-001")
        )
        assert assigned is not None
        assigned_id = assigned.id
    sensitive_password = "a password that must never be logged"
    sensitive_refresh = "refresh-token-that-must-never-be-logged"
    synthetic_content = "50mg demo medication fixture"
    sensitive_upload_name = "private-synthetic-scan-log-check.png"
    sensitive_prompt = "My phone number is +1 555 123 4567. Please call me."
    sensitive_summary = "Interpret my medical record and lab result."

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "doctor.demo@example.com",
                "password": sensitive_password,
            },
        )
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": sensitive_refresh},
        )
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
        client.post(
            f"/api/v1/patients/{assigned_id}/assets/presign",
            headers=auth_header(doctor["access_token"]),
            json={
                "filename": sensitive_upload_name,
                "content_type": "image/png",
                "size_bytes": 2048,
            },
        )
        client.post(
            "/api/v1/chat/threads/patient-education/messages",
            headers=auth_header(patient["access_token"]),
            json={"message": sensitive_prompt},
        )
        client.post(
            "/api/v1/consultations",
            headers=auth_header(doctor["access_token"]),
            json={
                "patient_id": str(assigned_id),
                "specialty": "Pulmonology demo review",
                "question_summary": sensitive_summary,
            },
        )

    logs = caplog.text
    assert sensitive_password not in logs
    assert sensitive_refresh not in logs
    assert sensitive_upload_name not in logs
    assert sensitive_prompt not in logs
    assert sensitive_summary not in logs
    assert synthetic_content not in logs
    assert "Authorization" not in logs
    assert "Bearer " not in logs
    assert "deepseek" not in logs.lower()
