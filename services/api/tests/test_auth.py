from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import RefreshSession, User
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.seed import seed_database
from tests.helpers import auth_header, login


def test_passwords_use_argon2id() -> None:
    encoded = hash_password("a generated test-only passphrase")

    assert encoded.startswith("$argon2id$")
    assert verify_password("a generated test-only passphrase", encoded)
    assert not verify_password("different test passphrase", encoded)


def test_invited_registration_requires_the_role_invite(
    client: TestClient, settings
) -> None:
    denied = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.patient@example.com",
            "password": "generated test passphrase",
            "role": "patient",
            "invite_code": "incorrect-invite",
        },
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "forbidden"

    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.patient@example.com",
            "password": "generated test passphrase",
            "role": "patient",
            "invite_code": settings.patient_invite_code.get_secret_value(),
        },
    )
    assert created.status_code == 201
    assert created.json()["user"]["role"] == "patient"
    assert created.json()["access_token"]
    assert created.json()["refresh_token"]


def test_login_success_failure_and_me(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)

    tokens = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 600
    assert tokens["user"]["role"] == "doctor"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = client.get("/api/v1/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    assert me.json()["display_name"] == "Dr. Avery Demo"
    assert "Synthetic demonstration data only" in me.json()["safety_label"]

    failed = client.post(
        "/api/v1/auth/login",
        json={
            "email": "doctor.demo@example.com",
            "password": "incorrect test password",
        },
    )
    assert failed.status_code == 401
    assert failed.json()["error"]["code"] == "unauthenticated"
    assert failed.json()["error"]["request_id"].startswith("req_")


def test_expired_access_token_is_rejected(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    with Session(engine) as db:
        user = db.scalar(
            select(User).where(User.email == "doctor.demo@example.com")
        )
        session = db.scalar(
            select(RefreshSession).where(
                RefreshSession.token_hash.is_not(None),
                RefreshSession.user_id == user.id,
            )
        )
        expired, _ = create_access_token(
            user,
            session.id,
            settings,
            now=datetime.now(UTC) - timedelta(minutes=30),
        )

    response = client.get("/api/v1/me", headers=auth_header(expired))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert tokens["access_token"] != expired


def test_refresh_rotates_and_replay_revokes_family(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    initial = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    rotated_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )
    assert rotated_response.status_code == 200
    rotated = rotated_response.json()
    assert rotated["refresh_token"] != initial["refresh_token"]

    replay = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )
    assert replay.status_code == 401

    family_revoked = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert family_revoked.status_code == 401


def test_logout_revokes_refresh_and_access_session(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    headers = auth_header(tokens["access_token"])

    logout = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        ).status_code
        == 401
    )
