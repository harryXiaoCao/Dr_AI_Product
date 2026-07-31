import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    CareRelationship,
    ChatMessage,
    ChatRateLimit,
    ChatThread,
    ConsultationRequest,
    DashboardSnapshot,
    DoctorNote,
    MedicalRecord,
    Medication,
    RecoveryPlan,
    RecoveryTask,
    User,
)
from app.seed import seed_database


def test_empty_database_migrates_to_head() -> None:
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert set(inspect(engine).get_table_names()) >= {
        "alembic_version",
        "users",
        "doctor_profiles",
        "patient_profiles",
        "care_relationships",
        "refresh_sessions",
        "dashboard_snapshots",
        "medical_records",
        "medications",
        "doctor_notes",
        "recovery_plans",
        "recovery_tasks",
        "recovery_task_completions",
        "chat_threads",
        "chat_messages",
        "chat_rate_limits",
        "consultation_requests",
        "support_requests",
        "support_request_events",
        "analytics_events",
        "notification_preferences",
        "notification_device_endpoints",
        "notification_outbox",
        "notification_delivery_attempts",
        "notification_events",
    }


def test_phase5_upgrade_backfills_existing_deletion_retention_boundary() -> None:
    config = Config("alembic.ini")
    command.downgrade(config, "20260727_0051")
    user_id = uuid.uuid4()
    request_id = uuid.uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO users (
                        id, email, password_hash, role, is_active, created_at, updated_at
                    )
                    VALUES (
                        :user_id,
                        'legacy.deletion@example.com',
                        'not-a-real-password-hash',
                        CAST('patient' AS user_role),
                        true,
                        now(),
                        now()
                    )
                    """
                ),
                {"user_id": user_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO support_requests (
                        id,
                        requester_user_id,
                        patient_id,
                        request_type,
                        status,
                        subject,
                        body_redacted,
                        source,
                        assigned_to_user_id,
                        audit_metadata_json,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :request_id,
                        :user_id,
                        NULL,
                        'deletion',
                        'queued',
                        'Legacy deletion request',
                        '[redacted legacy body]',
                        'authenticated_app',
                        NULL,
                        '{}'::jsonb,
                        now(),
                        now()
                    )
                    """
                ),
                {"request_id": request_id, "user_id": user_id},
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT retention_boundary_code, public_reference
                    FROM support_requests
                    WHERE id = :request_id
                    """
                ),
                {"request_id": request_id},
            ).one()
        assert row.retention_boundary_code == "regulated_and_audit_retention_applies"
        assert row.public_reference.startswith("REQ-")
    finally:
        command.upgrade(config, "head")


def test_synthetic_seed_is_idempotent(settings) -> None:
    with Session(engine) as db:
        first = seed_database(db, settings)
        second = seed_database(db, settings)

        assert first.users_created == 3
        assert first.relationships_created == 2
        assert first.dashboards_created == 3
        assert first.records_created == 2
        assert first.medications_created == 2
        assert first.notes_created == 1
        assert first.recovery_plans_created == 1
        assert first.recovery_tasks_created == 4
        assert second.users_created == 0
        assert second.relationships_created == 0
        assert second.dashboards_created == 0
        assert second.records_created == 0
        assert second.medications_created == 0
        assert second.notes_created == 0
        assert second.recovery_plans_created == 0
        assert second.recovery_tasks_created == 0
        assert db.scalar(select(func.count()).select_from(User)) == 3
        assert db.scalar(select(func.count()).select_from(CareRelationship)) == 2
        assert db.scalar(select(func.count()).select_from(DashboardSnapshot)) == 3
        assert db.scalar(select(func.count()).select_from(MedicalRecord)) == 2
        assert db.scalar(select(func.count()).select_from(Medication)) == 2
        assert db.scalar(select(func.count()).select_from(DoctorNote)) == 1
        assert db.scalar(select(func.count()).select_from(RecoveryPlan)) == 1
        assert db.scalar(select(func.count()).select_from(RecoveryTask)) == 4
        assert db.scalar(select(func.count()).select_from(ChatThread)) == 0
        assert db.scalar(select(func.count()).select_from(ChatMessage)) == 0
        assert db.scalar(select(func.count()).select_from(ChatRateLimit)) == 0
        assert db.scalar(select(func.count()).select_from(ConsultationRequest)) == 0


def test_seed_contains_only_clearly_synthetic_identifiers(settings) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        emails = set(db.scalars(select(User.email)).all())

    assert emails == {
        "doctor.demo@example.com",
        "patient.demo@example.com",
        "unrelated.patient@example.com",
    }
