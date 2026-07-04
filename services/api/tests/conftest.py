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

os.environ.setdefault(
    "DR_AI_DATABASE_URL", "postgresql+psycopg://localhost/dr_ai_test"
)
os.environ["DR_AI_ENVIRONMENT"] = "test"
os.environ["DR_AI_JWT_SECRET"] = secrets.token_urlsafe(48)
os.environ["DR_AI_DOCTOR_INVITE_CODE"] = secrets.token_urlsafe(18)
os.environ["DR_AI_PATIENT_INVITE_CODE"] = secrets.token_urlsafe(18)
os.environ["DR_AI_SEED_DOCTOR_PASSWORD"] = TEST_DOCTOR_PASSWORD
os.environ["DR_AI_SEED_PATIENT_PASSWORD"] = TEST_PATIENT_PASSWORD
os.environ["DR_AI_SEED_UNRELATED_PATIENT_PASSWORD"] = TEST_UNRELATED_PASSWORD

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
                "TRUNCATE dashboard_snapshots, refresh_sessions, "
                "care_relationships, patient_profiles, doctor_profiles, users "
                "RESTART IDENTITY CASCADE"
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
