import os
import secrets
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

TEST_DOCTOR_PASSWORD = secrets.token_urlsafe(18)
TEST_PATIENT_PASSWORD = secrets.token_urlsafe(18)
TEST_UNRELATED_PASSWORD = secrets.token_urlsafe(18)

os.environ.setdefault("DR_AI_DATABASE_URL", "postgresql+psycopg://localhost/dr_ai_test")
os.environ["DR_AI_ENVIRONMENT"] = "test"
os.environ["DR_AI_JWT_SECRET"] = secrets.token_urlsafe(48)
os.environ["DR_AI_DOCTOR_INVITE_CODE"] = secrets.token_urlsafe(18)
os.environ["DR_AI_PATIENT_INVITE_CODE"] = secrets.token_urlsafe(18)
os.environ["DR_AI_SEED_DOCTOR_PASSWORD"] = TEST_DOCTOR_PASSWORD
os.environ["DR_AI_SEED_PATIENT_PASSWORD"] = TEST_PATIENT_PASSWORD
os.environ["DR_AI_SEED_UNRELATED_PATIENT_PASSWORD"] = TEST_UNRELATED_PASSWORD
os.environ.pop("DR_AI_CORS_ALLOWED_ORIGINS", None)

from app.config import get_settings  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None]:
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest.fixture(autouse=True)
def clean_database(migrated_database: None) -> Generator[None]:
    del migrated_database
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE phone_verification_challenges, support_requests, chatbot_events, "
                "payer_reviews, payer_request_lines, payer_requests, care_cost_items, "
                "payer_memberships, payer_organizations, "
                "kb_source_candidates, kb_source_fetch_runs, "
                "kb_retrieval_events, kb_index_release_passages, kb_terms, kb_passages, "
                "kb_sections, kb_summary_artifacts, kb_translation_sections, "
                "kb_translation_artifacts, "
                "kb_active_index_releases, kb_reviews, kb_source_versions, "
                "kb_index_releases, kb_sources, kb_source_families, "
                "kb_rights_records, kb_publishers, "
                "analytics_events, revenue_summaries, "
                "payment_statuses, invoices, notifications, medication_reminders, "
                "prescription_medications, prescriptions, equipment_bookings, "
                "appointments, equipment, clinic_resources, doctor_team_memberships, "
                "doctor_teams, role_assignments, clinics, hospitals, "
                "audit_events, consultation_requests, chat_messages, chat_threads, "
                "chat_rate_limits, simulated_assessments, demo_medical_assets, "
                "recovery_task_completions, recovery_tasks, recovery_plans, "
                "diagnoses, visit_history, chronic_diseases, patient_allergies, "
                "doctor_notes, medications, medical_records, "
                "dashboard_snapshots, refresh_sessions, care_relationships, "
                "patient_profiles, doctor_profiles, users RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def settings():
    return get_settings()
