from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select
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
    }


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
