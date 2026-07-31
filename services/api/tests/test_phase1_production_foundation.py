import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    AnalyticsEvent,
    AuditEvent,
    Clinic,
    Hospital,
    RoleAssignment,
    SupportRequest,
    User,
    UserRole,
)
from app.security import hash_password
from app.seed import seed_database
from tests.helpers import auth_header, login

PHASE1_TABLES = {
    "hospitals",
    "clinics",
    "role_assignments",
    "doctor_teams",
    "doctor_team_memberships",
    "clinic_resources",
    "equipment",
    "appointments",
    "equipment_bookings",
    "prescriptions",
    "prescription_medications",
    "medication_reminders",
    "notifications",
    "invoices",
    "payment_statuses",
    "revenue_summaries",
    "analytics_events",
    "support_requests",
}


def test_phase1_tables_are_present_after_migration() -> None:
    with engine.connect() as connection:
        names = set(
            connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            ).scalars()
        )

    assert PHASE1_TABLES.issubset(names)


def test_seed_keeps_production_foundation_tables_empty(settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        for table_name in PHASE1_TABLES:
            count = db.scalar(text(f"SELECT count(*) FROM {table_name}"))
            assert count == 0, table_name


def test_specialist_and_admin_registration_fail_closed(
    client: TestClient,
    settings,
) -> None:
    for role in ("specialist", "admin"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{role}.future@example.com",
                "phone_number": f"+1555000{1 if role == 'specialist' else 2}",
                "password": "Future9!",
                "role": role,
                "verification_code": "123456",
                "terms_accepted": True,
            },
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "forbidden"


def test_specialist_and_admin_cannot_use_beta_dashboard_or_patient_routes(
    client: TestClient,
) -> None:
    for role in (UserRole.specialist, UserRole.admin):
        email = f"{role.value}.{uuid.uuid4()}@example.com"
        password = "generated test passphrase"
        with Session(engine) as db:
            db.add(User(email=email, password_hash=hash_password(password), role=role))
            db.commit()

        tokens = login(client, email, password)
        headers = auth_header(tokens["access_token"])

        dashboard = client.get("/api/v1/me/dashboard", headers=headers)
        assert dashboard.status_code == 403
        assert dashboard.json()["error"]["code"] == "forbidden"

        patients = client.get("/api/v1/patients", headers=headers)
        assert patients.status_code == 404
        assert patients.json()["error"]["code"] == "not_found"


def test_support_queue_and_role_assignment_models_persist_metadata(settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        patient = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
        doctor = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
        hospital = Hospital(
            name="Production Foundation Hospital",
            legal_name="Production Foundation Hospital LLC",
            status="draft",
            metadata_json={"phase": "phase_1_foundation"},
        )
        db.add(hospital)
        db.flush()
        clinic = Clinic(
            hospital_id=hospital.id,
            name="Production Foundation Clinic",
            timezone="Asia/Shanghai",
            status="draft",
            metadata_json={"source": "test"},
        )
        db.add(clinic)
        db.flush()
        assignment = RoleAssignment(
            user_id=doctor.id,
            role=UserRole.doctor,
            hospital_id=hospital.id,
            clinic_id=clinic.id,
            status="active",
        )
        request = SupportRequest(
            requester_user_id=patient.id,
            patient_id=patient.patient_profile.id,
            request_type="deletion",
            status="queued",
            public_reference="REQ-PHASE1DIRECT",
            idempotency_key="phase1-direct-request",
            request_checksum="0" * 64,
            version=1,
            retention_boundary_code="regulated_and_audit_retention_applies",
            subject="Synthetic deletion request",
            body_redacted="[redacted synthetic request body]",
            source="authenticated_app",
            audit_metadata_json={
                "contains_real_patient_data": False,
                "identity_review_required": True,
            },
        )
        db.add_all([assignment, request])
        db.flush()
        db.add(
            AuditEvent(
                actor_user_id=patient.id,
                patient_id=patient.patient_profile.id,
                event_type="support_request_queued",
                resource_type="support_request",
                resource_id=request.id,
                metadata_json={
                    "request_type": request.request_type,
                    "status": request.status,
                    "body_redacted": True,
                },
            )
        )
        db.add(
            AnalyticsEvent(
                actor_user_id=patient.id,
                patient_id=patient.patient_profile.id,
                clinic_id=clinic.id,
                event_type="support_request_queued",
                resource_type="support_request",
                resource_id=request.id,
                role="patient",
                environment="test",
                schema_version="legacy",
                deduplication_key="phase1-direct-analytics",
                event_checksum=None,
                outcome="completed",
                failure_category=None,
                latency_ms=None,
                metadata_json={"request_type": "deletion"},
            )
        )
        db.commit()

        assert db.scalar(select(func.count()).select_from(RoleAssignment)) == 1
        stored_request = db.scalar(select(SupportRequest))
        assert stored_request.status == "queued"
        assert stored_request.audit_metadata_json["identity_review_required"] is True
        assert "REQUEST DEMO DELETION" not in stored_request.body_redacted
        stored_audit = db.scalar(
            select(AuditEvent).where(AuditEvent.resource_type == "support_request")
        )
        assert stored_audit.metadata_json["body_redacted"] is True


def test_authenticated_patient_support_request_persists_status_and_audit_metadata(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    headers = auth_header(patient["access_token"])

    created = client.post(
        "/api/v1/support-requests",
        headers={**headers, "Idempotency-Key": "patient-deletion-create-001"},
        json={
            "request_type": "deletion",
            "subject": "Synthetic account deletion review",
            "message": "Please queue this synthetic account deletion review.",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["request_type"] == "deletion"
    assert body["status"] == "queued"
    assert body["request_id"]
    assert "Synthetic demonstration data only" in body["safety_label"]

    listed = client.get("/api/v1/support-requests", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["items"][0]["request_id"] == body["request_id"]

    status_read = client.get(f"/api/v1/support-requests/{body['request_id']}", headers=headers)
    assert status_read.status_code == 200
    assert status_read.json()["status"] == "queued"

    with Session(engine) as db:
        stored_request = db.scalar(select(SupportRequest))
        assert stored_request.request_type == "deletion"
        assert stored_request.status == "queued"
        assert stored_request.audit_metadata_json["identity_review_required"] is True
        assert stored_request.audit_metadata_json["body_redacted"] is True
        assert "Please queue" in stored_request.body_redacted
        assert stored_request.patient_id is not None

        events = db.scalars(
            select(AuditEvent).where(AuditEvent.resource_id == stored_request.id)
        ).all()
        event_types = {event.event_type for event in events}
        assert {
            "support_request_queued",
            "support_requests_listed",
            "support_request_status_read",
        }.issubset(event_types)
        queued = next(event for event in events if event.event_type == "support_request_queued")
        assert queued.metadata_json["request_type"] == "deletion"
        assert queued.metadata_json["body_redacted"] is True
        assert "message" not in queued.metadata_json
        assert "subject" not in queued.metadata_json


def test_doctor_feedback_request_is_not_patient_scoped(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )

    created = client.post(
        "/api/v1/support-requests",
        headers={
            **auth_header(doctor["access_token"]),
            "Idempotency-Key": "doctor-feedback-create-001",
        },
        json={
            "request_type": "feedback",
            "subject": "Synthetic workflow feedback",
            "message": "The synthetic support queue should keep this feedback.",
        },
    )

    assert created.status_code == 201
    with Session(engine) as db:
        stored_request = db.scalar(select(SupportRequest))
        assert stored_request.requester.role == UserRole.doctor
        assert stored_request.patient_id is None
        assert stored_request.audit_metadata_json["requester_role"] == "doctor"


def test_support_request_status_is_scoped_to_requester(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
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
    created = client.post(
        "/api/v1/support-requests",
        headers={
            **auth_header(patient["access_token"]),
            "Idempotency-Key": "patient-support-create-001",
        },
        json={
            "request_type": "support",
            "subject": "Synthetic support status",
            "message": "Please keep this synthetic request status visible.",
        },
    )
    assert created.status_code == 201

    denied = client.get(
        f"/api/v1/support-requests/{created.json()['request_id']}",
        headers=auth_header(unrelated["access_token"]),
    )

    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "not_found"


def test_support_requests_reject_unsupported_roles_without_side_effects_and_unsafe_content(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        for role in (UserRole.specialist, UserRole.admin):
            db.add(
                User(
                    email=f"{role.value}.future@example.com",
                    password_hash=hash_password("generated test passphrase"),
                    role=role,
                )
            )
        db.commit()

    for role in ("specialist", "admin"):
        tokens = login(client, f"{role}.future@example.com", "generated test passphrase")
        headers = auth_header(tokens["access_token"])
        for method in ("post", "get"):
            if method == "post":
                role_denied = client.post(
                    "/api/v1/support-requests",
                    headers={
                        **headers,
                        "Idempotency-Key": f"future-{role}-support-001",
                    },
                    json={
                        "request_type": "support",
                        "subject": f"Synthetic {role} support",
                        "message": "This future role should not inherit queue access.",
                    },
                )
            else:
                role_denied = client.get("/api/v1/support-requests", headers=headers)
            assert role_denied.status_code == 403
            assert role_denied.json()["error"]["code"] == "forbidden"

    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(SupportRequest)) == 0
        assert db.scalar(select(func.count()).select_from(AuditEvent)) == 0

    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    unsafe = client.post(
        "/api/v1/support-requests",
        headers={
            **auth_header(patient["access_token"]),
            "Idempotency-Key": "patient-unsafe-feedback-001",
        },
        json={
            "request_type": "feedback",
            "subject": "Synthetic feedback",
            "message": "Please review this CT scan and email person@example.com.",
        },
    )
    assert unsafe.status_code == 422
    assert unsafe.json()["error"]["code"] == "validation_failed"
