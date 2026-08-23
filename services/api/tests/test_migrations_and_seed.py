import json
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
        "clinical_event_intelligence_snapshots",
        "clinical_event_intelligence_runs",
        "clinical_event_intelligence_retrieval_sources",
        "clinical_event_intelligence_pathways",
        "clinical_event_intelligence_pathway_items",
        "clinical_event_intelligence_provider_attempts",
        "clinical_event_intelligence_item_assessments",
        "clinical_event_intelligence_artifacts",
        "clinical_event_intelligence_explanations",
        "clinical_event_intelligence_lineage_events",
    }

    payer_line_columns = {
        column["name"] for column in inspect(engine).get_columns("payer_request_lines")
    }
    assert {"code_system", "service_code", "quantity", "unit"} <= payer_line_columns
    payer_review_columns = {
        column["name"] for column in inspect(engine).get_columns("payer_reviews")
    }
    assert "clarification_message" in payer_review_columns

    snapshot_columns = {
        column["name"]: column
        for column in inspect(engine).get_columns("clinical_event_intelligence_snapshots")
    }
    for location_column in (
        "hospital_id",
        "clinic_id",
        "department_code",
        "jurisdiction_code",
        "province",
        "city",
        "facility_level",
        "encounter_at",
    ):
        assert snapshot_columns[location_column]["nullable"] is True

    pathway_checks = {
        constraint["name"]: constraint["sqltext"]
        for constraint in inspect(engine).get_check_constraints(
            "clinical_event_intelligence_pathway_items"
        )
    }
    assessment_checks = {
        constraint["name"]: constraint["sqltext"]
        for constraint in inspect(engine).get_check_constraints(
            "clinical_event_intelligence_item_assessments"
        )
    }
    assert "quantity_low >= 0" in pathway_checks["ck_cei_pathway_item_quantity"]
    assert "estimated_quantity_low >= 0" in assessment_checks["ck_cei_assessment_quantity"]


def test_clinical_event_intelligence_migration_downgrade_and_reupgrade() -> None:
    config = Config("alembic.ini")
    command.downgrade(config, "20260730_0054")
    assert "clinical_event_intelligence_artifacts" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert "clinical_event_intelligence_artifacts" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        trigger_count = connection.scalar(
            text(
                "SELECT count(*) FROM pg_trigger "
                "WHERE NOT tgisinternal AND tgname LIKE "
                "'trg_clinical_event_intelligence_%_append_only'"
            )
        )
    assert trigger_count == 10


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

        assert first.users_created == 4
        assert first.relationships_created == 3
        assert first.dashboards_created == 4
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
        assert db.scalar(select(func.count()).select_from(User)) == 4
        assert db.scalar(select(func.count()).select_from(CareRelationship)) == 3
        assert db.scalar(select(func.count()).select_from(DashboardSnapshot)) == 4
        snapshots = db.scalars(select(DashboardSnapshot)).all()
        assert all("fee_items" not in snapshot.payload for snapshot in snapshots)
        assert all(
            "demo credits" not in json.dumps(snapshot.payload).lower()
            for snapshot in snapshots
        )
        doctor_quick_access = next(
            snapshot.payload["quick_access"]
            for snapshot in snapshots
            if "quick_access" in snapshot.payload
        )
        assert "Imaging records and manual review" in doctor_quick_access
        assert not any("AI" in label for label in doctor_quick_access)
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
        "reviewer.doctor@example.com",
        "patient.demo@example.com",
        "unrelated.patient@example.com",
    }
