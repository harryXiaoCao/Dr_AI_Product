import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import AuditEvent, DemoMedicalAsset, PatientProfile, SimulatedAssessment
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


def test_doctor_can_presign_demo_asset_and_audit_event_is_metadata_only(
    client: TestClient, settings
) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    response = client.post(
        f"/api/v1/patients/{assigned_id}/assets/presign",
        headers=auth_header(doctor["access_token"]),
        json={
            "filename": "synthetic-ct-demo.png",
            "content_type": "image/png",
            "size_bytes": 2048,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "PUT"
    assert payload["safety_label"] == (
        "Synthetic demonstration data only. Do not enter real patient data."
    )
    assert payload["upload_url"].startswith("https://demo-upload.invalid/demo-assets/")
    with Session(engine) as db:
        asset = db.scalar(select(DemoMedicalAsset))
        audit = db.scalar(select(AuditEvent).where(AuditEvent.event_type == "demo_asset_presigned"))
        assert asset is not None
        assert asset.patient_id == assigned_id
        assert audit is not None
        assert audit.patient_id == assigned_id
        assert "upload_url" not in audit.metadata_json
        assert audit.metadata_json["content_type"] == "image/png"


def test_presign_rejects_unsupported_media_type(client: TestClient, settings) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    response = client.post(
        f"/api/v1/patients/{assigned_id}/assets/presign",
        headers=auth_header(doctor["access_token"]),
        json={
            "filename": "synthetic-ct-demo.exe",
            "content_type": "application/x-msdownload",
            "size_bytes": 2048,
        },
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_presign_rejects_oversized_upload_metadata(client: TestClient, settings) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    response = client.post(
        f"/api/v1/patients/{assigned_id}/assets/presign",
        headers=auth_header(doctor["access_token"]),
        json={
            "filename": "synthetic-ct-demo.png",
            "content_type": "image/png",
            "size_bytes": 20_000_000,
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_presign_rejects_filename_content_type_mismatch(client: TestClient, settings) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    response = client.post(
        f"/api/v1/patients/{assigned_id}/assets/presign",
        headers=auth_header(doctor["access_token"]),
        json={
            "filename": "scan.exe",
            "content_type": "image/png",
            "size_bytes": 2048,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"
    assert response.json()["error"]["details"][0]["code"] == "content_type_mismatch"


def test_presign_cross_patient_denial_remains_neutral(client: TestClient, settings) -> None:
    _, unrelated_id = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    response = client.post(
        f"/api/v1/patients/{unrelated_id}/assets/presign",
        headers=auth_header(doctor["access_token"]),
        json={
            "filename": "synthetic-ct-demo.png",
            "content_type": "image/png",
            "size_bytes": 2048,
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_assessment_is_deterministic_idempotent_and_audited(client: TestClient, settings) -> None:
    assigned_id, _ = _seed_patient_ids(settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(doctor["access_token"])
    request_body = {
        "mode": "simulated",
        "fixture_id": "synthetic_lung_case_001",
        "idempotency_key": "test-idempotency-key-001",
    }

    first = client.post(
        f"/api/v1/patients/{assigned_id}/assessments", headers=headers, json=request_body
    )
    second = client.post(
        f"/api/v1/patients/{assigned_id}/assessments",
        headers=headers,
        json=request_body,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["mode"] == "simulated"
    assert payload["status"] == "completed"
    assert payload["risk_band"] == "moderate"
    assert payload["demo_score"] == 0.54
    assert payload["input_completeness"] == "complete"
    assert payload["model_version"] == "fixture-simulator-1.0.0"
    assert payload["safety_label"] == "Research simulation - not for diagnosis."
    assert "clinical inference" in payload["limitations"][0]
    with Session(engine) as db:
        assessments = db.scalars(select(SimulatedAssessment)).all()
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "simulated_assessment_completed")
        ).all()
        assert len(assessments) == 1
        assert len(audits) == 1
        assert audits[0].metadata_json["fixture_id"] == "synthetic_lung_case_001"


def test_assessment_denials_and_patient_readback_are_role_safe(
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
    doctor_headers = auth_header(doctor["access_token"])
    patient_headers = auth_header(patient["access_token"])

    create_response = client.post(
        f"/api/v1/patients/{assigned_id}/assessments",
        headers=doctor_headers,
        json={
            "mode": "simulated",
            "fixture_id": "synthetic_lung_case_001",
            "idempotency_key": "test-idempotency-key-002",
        },
    )
    assert create_response.status_code == 200

    patient_create = client.post(
        f"/api/v1/patients/{assigned_id}/assessments",
        headers=patient_headers,
        json={
            "mode": "simulated",
            "fixture_id": "synthetic_lung_case_001",
            "idempotency_key": "test-idempotency-key-003",
        },
    )
    assert patient_create.status_code == 404
    assert patient_create.json()["error"]["code"] == "not_found"

    cross_patient = client.post(
        f"/api/v1/patients/{unrelated_id}/assessments",
        headers=doctor_headers,
        json={
            "mode": "simulated",
            "fixture_id": "synthetic_lung_case_001",
            "idempotency_key": "test-idempotency-key-004",
        },
    )
    assert cross_patient.status_code == 404

    readback = client.get(f"/api/v1/patients/{assigned_id}/assessments", headers=patient_headers)
    assert readback.status_code == 200
    assert len(readback.json()["items"]) == 1
    assert readback.json()["items"][0]["safety_label"] == (
        "Research simulation - not for diagnosis."
    )
