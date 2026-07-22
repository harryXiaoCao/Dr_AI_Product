import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.main import EmbeddingRequest, RerankRequest, embeddings, settings


def test_embedding_request_rejects_wrong_model_without_loading_models() -> None:
    with pytest.raises(HTTPException) as exc_info:
        embeddings(EmbeddingRequest(model="wrong", input=["血压监测"]))
    assert exc_info.value.status_code == 409


def test_reranker_request_rejects_duplicate_document_ids() -> None:
    with pytest.raises(ValidationError):
        RerankRequest.model_validate(
            {
                "model": settings.reranker_api_model,
                "query": "血压监测",
                "documents": [
                    {"id": "same", "text": "第一段"},
                    {"id": "same", "text": "第二段"},
                ],
            }
        )
