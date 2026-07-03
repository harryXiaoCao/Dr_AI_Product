from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "dr-ai-api",
        "environment": "local",
    }


def test_openapi_describes_non_clinical_foundation() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "Not intended for clinical use" in response.json()["info"]["description"]
