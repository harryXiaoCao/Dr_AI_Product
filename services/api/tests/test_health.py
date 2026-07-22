import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings


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


def test_cors_defaults_to_same_origin_only() -> None:
    settings = Settings(
        _env_file=None,
        environment="test",
        jwt_secret="test-secret-value-with-enough-entropy-123",
    )

    assert settings.cors_allowed_origins == []

    response = Settings(
        _env_file=None,
        environment="staging",
        jwt_secret="staging-secret-value-with-enough-entropy-123",
        cors_allowed_origins=["https://beta.example.test"],
    )

    assert response.cors_allowed_origins == ["https://beta.example.test"]


def test_wildcard_cors_is_rejected_outside_local_environments() -> None:
    with pytest.raises(ValidationError, match="cannot contain \\*"):
        Settings(
            environment="staging",
            jwt_secret="staging-secret-value-with-enough-entropy-123",
            cors_allowed_origins=["*"],
        )


def test_production_rejects_local_retrieval_models() -> None:
    with pytest.raises(ValidationError, match="Production retrieval requires"):
        Settings(
            _env_file=None,
            environment="production",
            jwt_secret="production-secret-value-with-enough-entropy-123",
        )


def test_production_accepts_declared_mainland_retrieval_services() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret="production-secret-value-with-enough-entropy-123",
        knowledge_embedding_backend="http_service",
        knowledge_embedding_service_url="https://embedding.internal.example.cn/v1/embeddings",
        knowledge_embedding_model="BAAI/bge-m3@dr-ai-mainland-v1",
        knowledge_reranker_backend="http_service",
        knowledge_reranker_service_url="https://reranker.internal.example.cn/v1/rerank",
        knowledge_reranker_model="BAAI/bge-reranker-v2-m3@dr-ai-mainland-medical-v1",
    )

    assert settings.knowledge_model_service_data_region == "mainland_china"
