import logging

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine
from app.seed import seed_database


def test_validation_uses_standard_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": ""},
    )

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "validation_failed"
    assert body["error"]["request_id"].startswith("req_")
    assert body["error"]["details"]
    assert body["error"]["details"][0]["message"] == (
        "The supplied value is invalid."
    )


def test_logs_do_not_contain_credentials_tokens_or_synthetic_content(
    client: TestClient, settings, caplog
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
    sensitive_password = "a password that must never be logged"
    sensitive_refresh = "refresh-token-that-must-never-be-logged"
    synthetic_content = "50mg demo medication fixture"

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "doctor.demo@example.com",
                "password": sensitive_password,
            },
        )
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": sensitive_refresh},
        )

    logs = caplog.text
    assert sensitive_password not in logs
    assert sensitive_refresh not in logs
    assert synthetic_content not in logs
    assert "Authorization" not in logs
