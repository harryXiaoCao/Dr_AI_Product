import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dashboard import _is_recently_active
from app.database import engine
from app.models import (
    AuditEvent,
    DoctorProfile,
    PatientProfile,
    PhoneVerificationChallenge,
    RefreshSession,
    User,
)
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


def test_registration_accepts_phone_required_and_optional_email(client: TestClient) -> None:
    missing_phone = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.patient@example.com",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
        },
    )
    assert missing_phone.status_code == 422

    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.patient@example.com",
            "phone_number": "+8613800099999",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
            "patient_profile": {
                "display_name": "Riley Patient",
                "contact_phone": "+8613800099999",
                "country": "China",
                "province": "Guangdong",
                "city": "Shenzhen",
                "home_address": "100 Recovery Road",
                "height_cm": 168,
                "weight_kg": 62.5,
            },
        },
    )
    assert created.status_code == 201
    assert created.json()["user"]["role"] == "patient"
    assert created.json()["user"]["phone_number"] == "+8613800099999"
    assert created.json()["access_token"]
    assert created.json()["refresh_token"]
    with Session(engine) as db:
        profile = db.scalar(
            select(PatientProfile).where(PatientProfile.display_name == "Riley Patient")
        )
        assert profile is not None
        assert profile.country == "China"
        assert profile.home_address == "100 Recovery Road"
        assert profile.height_cm == 168
        assert profile.weight_kg == 62.5


def test_fixed_registration_code_works_without_a_requested_challenge(
    client: TestClient,
    settings,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "environment", "local")

    created = client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": "+8613800098999",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
        },
    )

    assert created.status_code == 201


def test_phone_registration_login_and_doctor_hospital_intake(client: TestClient) -> None:
    created = client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": "+8613800012345",
            "password": "Doctor9!",
            "role": "doctor",
            "verification_code": "123456",
            "terms_accepted": True,
            "doctor_profile": {
                "display_name": "Dr. Lin Wei",
                "contact_phone": "+8613800012345",
                "avatar_url": "data:image/png;base64,ZmFrZQ==",
                "country": "China",
                "province": "Guangdong",
                "city": "Shenzhen",
                "hospital_name": "Nanshan Care Center",
                "custom_hospital": True,
            },
        },
    )
    assert created.status_code == 201
    assert created.json()["user"]["phone_number"] == "+8613800012345"
    assert created.json()["user"]["display_name"] == "Dr. Lin Wei"
    with Session(engine) as db:
        profile = db.scalar(
            select(DoctorProfile).where(DoctorProfile.display_name == "Dr. Lin Wei")
        )
        assert profile is not None
        assert profile.avatar_url == "data:image/png;base64,ZmFrZQ=="
        assert profile.hospital_name == "Nanshan Care Center"

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "+8613800012345",
            "password": "Doctor9!",
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["role"] == "doctor"


def test_duplicate_registration_contact_returns_conflict(client: TestClient) -> None:
    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate.patient@example.com",
            "phone_number": "+8613800090001",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
            "patient_profile": {
                "display_name": "Duplicate Patient",
                "contact_phone": "+8613800090001",
            },
        },
    )
    assert created.status_code == 201

    duplicate_phone = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate.phone@example.com",
            "phone_number": "+8613800090001",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
            "patient_profile": {
                "display_name": "Duplicate Phone",
                "contact_phone": "+8613800090001",
            },
        },
    )
    assert duplicate_phone.status_code == 409
    assert duplicate_phone.json()["error"]["code"] == "conflict"
    assert (
        duplicate_phone.json()["error"]["message"] == "An account already exists for this contact."
    )

    duplicate_email = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate.patient@example.com",
            "phone_number": "+8613800090002",
            "password": "Patient9!",
            "role": "patient",
            "verification_code": "123456",
            "terms_accepted": True,
            "patient_profile": {
                "display_name": "Duplicate Email",
                "contact_phone": "+8613800090002",
            },
        },
    )
    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["error"]["code"] == "conflict"
    assert (
        duplicate_email.json()["error"]["message"] == "An account already exists for this contact."
    )


def test_registration_code_request_creates_and_consumes_phone_challenge(
    client: TestClient,
) -> None:
    phone_number = "+8613800090999"
    requested = client.post(
        "/api/v1/auth/registration-code/request",
        json={"phone_number": phone_number},
    )
    assert requested.status_code == 200
    code = requested.json()["debug_code"]
    assert code == "123456"

    registered = client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": phone_number,
            "password": "Patient9!",
            "role": "patient",
            "verification_code": code,
            "terms_accepted": True,
        },
    )
    assert registered.status_code == 201
    with Session(engine) as db:
        challenge = db.scalar(
            select(PhoneVerificationChallenge).where(
                PhoneVerificationChallenge.phone_number == phone_number,
                PhoneVerificationChallenge.purpose == "registration",
            )
        )
        assert challenge is not None
        assert challenge.user_id is not None
        assert challenge.consumed_at is not None


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


def test_password_reset_uses_phone_challenge_and_revokes_sessions(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        patient = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
        assert patient is not None
        patient.phone_number = "+8613800010002"
        db.commit()

    unknown = client.post(
        "/api/v1/auth/password-reset/request",
        json={"phone_number": "+8613999999999"},
    )
    assert unknown.status_code == 200
    assert unknown.json()["debug_code"] is None

    requested = client.post(
        "/api/v1/auth/password-reset/request",
        json={"phone_number": "+8613800010002"},
    )
    assert requested.status_code == 200
    verification_code = requested.json()["debug_code"]
    assert verification_code is not None
    assert len(verification_code) == 6

    reset = client.post(
        "/api/v1/auth/password-reset",
        json={
            "phone_number": "+8613800010002",
            "verification_code": verification_code,
            "new_password": "UpdatedPatient9!",
        },
    )
    assert reset.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": "+8613800010002",
                "password": settings.seed_patient_password.get_secret_value(),
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": "+8613800010002",
                "password": "UpdatedPatient9!",
            },
        ).status_code
        == 200
    )
    with Session(engine) as db:
        event = db.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "account_password_reset")
        )
        assert event is not None
        assert event.metadata_json == {"verification_channel": "phone"}


def test_authenticated_password_change_and_doctor_email_update(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(tokens["access_token"])

    email = client.patch(
        "/api/v1/auth/account/email",
        headers=headers,
        json={"email": "doctor.updated@example.com"},
    )
    assert email.status_code == 200
    assert email.json()["email"] == "doctor.updated@example.com"

    changed = client.put(
        "/api/v1/auth/password",
        headers=headers,
        json={
            "current_password": settings.seed_doctor_password.get_secret_value(),
            "new_password": "UpdatedDoctor9!",
        },
    )
    assert changed.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "doctor.updated@example.com",
                "password": "UpdatedDoctor9!",
            },
        ).status_code
        == 200
    )
    with Session(engine) as db:
        event_types = set(
            db.scalars(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type.in_({"account_email_updated", "account_password_changed"})
                )
            ).all()
        )
        assert event_types == {"account_email_updated", "account_password_changed"}


def test_account_email_can_be_removed(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.patch(
        "/api/v1/auth/account/email",
        headers=auth_header(tokens["access_token"]),
        json={"email": ""},
    )

    assert response.status_code == 200
    assert response.json()["email"] is None
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.id == uuid.UUID(response.json()["id"])))
        event = db.scalar(
            select(AuditEvent)
            .where(AuditEvent.event_type == "account_email_updated")
            .order_by(AuditEvent.created_at.desc())
        )
        assert user is not None and user.email is None
        assert event is not None and event.metadata_json["email_removed"] is True


def test_account_email_duplicate_returns_conflict_without_changing_either_account(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.patch(
        "/api/v1/auth/account/email",
        headers=auth_header(tokens["access_token"]),
        json={"email": "doctor.demo@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_in_use"
    with Session(engine) as db:
        emails = set(
            db.scalars(
                select(User.email).where(
                    User.email.in_({"doctor.demo@example.com", "patient.demo@example.com"})
                )
            ).all()
        )
        duplicate_update_event = db.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "account_email_updated")
        )
        assert emails == {"doctor.demo@example.com", "patient.demo@example.com"}
        assert duplicate_update_event is None


def test_recent_doctor_activity_uses_a_fourteen_day_boundary() -> None:
    now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)

    assert _is_recently_active(now - timedelta(days=14), now=now) is True
    assert _is_recently_active(now - timedelta(days=14, seconds=1), now=now) is False
    assert _is_recently_active(None, now=now) is False


def test_expired_access_token_is_rejected(client: TestClient, settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    tokens = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
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


def test_refresh_rotates_and_replay_revokes_family(client: TestClient, settings) -> None:
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


def test_logout_revokes_refresh_and_access_session(client: TestClient, settings) -> None:
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
