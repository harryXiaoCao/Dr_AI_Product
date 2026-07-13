from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import PatientProfile
from app.seed import seed_database
from tests.helpers import auth_header, login


def _headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    session = login(client, email, password)
    return auth_header(session["access_token"])


def test_connected_doctor_and_patient_share_private_conversation(client, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        patient = db.scalar(
            select(PatientProfile).where(
                PatientProfile.synthetic_identifier == "SYN-PATIENT-001"
            )
        )
        assert patient is not None
        patient_id = str(patient.id)

    doctor_headers = _headers(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    patient_headers = _headers(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    doctor_contacts = client.get("/api/v1/doctor/me/contacts", headers=doctor_headers)
    assert doctor_contacts.status_code == 200
    assert patient_id in {item["patient_id"] for item in doctor_contacts.json()["items"]}

    patient_contacts = client.get("/api/v1/patient/me/contacts", headers=patient_headers)
    assert patient_contacts.status_code == 200
    doctor_id = patient_contacts.json()["items"][0]["doctor_id"]

    sent = client.post(
        f"/api/v1/private-chats/{doctor_id}/messages",
        json={"message": "Could you clarify tomorrow's follow-up plan?"},
        headers=patient_headers,
    )
    assert sent.status_code == 200
    assert sent.json()["sender_role"] == "patient"

    received = client.get(
        f"/api/v1/private-chats/{patient_id}/messages", headers=doctor_headers
    )
    assert received.status_code == 200
    assert [item["content"] for item in received.json()["items"]] == [
        "Could you clarify tomorrow's follow-up plan?"
    ]

    reply = client.post(
        f"/api/v1/private-chats/{patient_id}/messages",
        json={"message": "Yes. I will review it with you tomorrow."},
        headers=doctor_headers,
    )
    assert reply.status_code == 200
    assert reply.json()["sender_role"] == "doctor"

    patient_view = client.get(
        f"/api/v1/private-chats/{doctor_id}/messages", headers=patient_headers
    )
    assert [item["sender_role"] for item in patient_view.json()["items"]] == [
        "patient",
        "doctor",
    ]


def test_private_conversation_rejects_unconnected_patient(client, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        unrelated = db.scalar(
            select(PatientProfile).where(
                PatientProfile.synthetic_identifier == "SYN-PATIENT-002"
            )
        )
        assert unrelated is not None
        unrelated_id = str(unrelated.id)
    doctor_headers = _headers(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    response = client.post(
        f"/api/v1/private-chats/{unrelated_id}/messages",
        json={"message": "This must not be delivered."},
        headers=doctor_headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
