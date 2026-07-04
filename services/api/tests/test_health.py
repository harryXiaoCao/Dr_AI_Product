from fastapi.testclient import TestClient


def test_health_returns_service_and_database_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "dr-ai-api",
        "environment": "test",
        "database": "ok",
    }
    assert response.headers["X-Request-ID"].startswith("req_")


def test_openapi_describes_non_clinical_foundation(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "Not intended for clinical use" in response.json()["info"]["description"]
