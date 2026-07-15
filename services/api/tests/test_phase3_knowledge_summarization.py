import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_summarization import (
    SUMMARY_PROMPT_POLICY_VERSION,
    SummaryCorpusArtifact,
    SummaryDocumentArtifact,
    SummaryUsage,
    canonical_summary_response,
    import_reviewed_summary_corpus,
    load_summary_corpus,
    sha256_text,
)
from app.knowledge_translation import (
    import_translation_corpus,
    load_translation_corpus,
    record_translation_review,
)
from app.models import KbSource, KbSummaryArtifact, KbTranslationArtifact
from app.open_content_ingestion import import_open_content_catalog, load_open_content_catalog
from app.seed import seed_database
from tests.helpers import auth_header, login

SOURCE_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
TRANSLATION_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.json"
)
SUMMARY_PATH = Path(
    "knowledge_base/summaries/open_patient_education.en-zh-Hans.deepseek-v4-flash.v1.json"
)


def _summary_document(index: int) -> SummaryDocumentArtifact:
    source = load_open_content_catalog(SOURCE_PATH).documents[index]
    translation = load_translation_corpus(TRANSLATION_PATH).documents[index]
    english = (
        f"This patient-education resource explains {source.title}, including its main health "
        "context and the topics covered by the governed source. It summarizes only information "
        "present in the publisher text and preserves important qualifications and warnings."
    )
    chinese = (
        f"这份患者教育资料介绍{translation.translated_title}，包括其主要健康背景和原文涵盖的主题。"
        "摘要仅依据受治理的中文译文，并保留重要限定条件与警示信息。"
    )
    return SummaryDocumentArtifact(
        source_id=source.stable_id,
        source_version_id=translation.source_version_id,
        source_normalized_checksum=source.normalized_checksum,
        translation_checksum=translation.response_checksum,
        english_summary=english,
        chinese_summary=chinese,
        usage=SummaryUsage(input_tokens=100, output_tokens=80, total_tokens=180),
        generated_at=datetime(2026, 7, 15, tzinfo=UTC),
        response_checksum=sha256_text(canonical_summary_response(english, chinese)),
    )


def test_summary_document_requires_bilingual_content_and_valid_checksum() -> None:
    item = _summary_document(0)
    assert item.english_summary.startswith("This patient-education resource")
    assert "患者教育资料" in item.chinese_summary

    with pytest.raises(ValidationError, match="checksum"):
        SummaryDocumentArtifact.model_validate({**item.model_dump(), "response_checksum": "0" * 64})


def test_summary_corpus_requires_all_55_governed_sources() -> None:
    documents = [_summary_document(index) for index in range(55)]
    corpus = SummaryCorpusArtifact(
        schema_version="1.0",
        source_corpus_locator=str(SOURCE_PATH),
        source_corpus_checksum=hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        translation_corpus_locator=str(TRANSLATION_PATH),
        translation_corpus_checksum=hashlib.sha256(TRANSLATION_PATH.read_bytes()).hexdigest(),
        provider="deepseek",
        model="deepseek-v4-flash",
        prompt_policy_version=SUMMARY_PROMPT_POLICY_VERSION,
        status="generated_pending_review",
        completed_at=datetime(2026, 7, 15, tzinfo=UTC),
        documents=documents,
    )

    assert len(corpus.documents) == 55
    assert len({item.source_id for item in corpus.documents}) == 55

    with pytest.raises(ValidationError, match="exactly 55"):
        SummaryCorpusArtifact.model_validate(
            {**corpus.model_dump(), "documents": corpus.model_dump()["documents"][:-1]}
        )


def test_reviewed_summary_import_is_idempotent_and_summary_text_is_searchable(
    client: TestClient,
    settings,
) -> None:
    reviewed_at = datetime(2026, 7, 15, tzinfo=UTC)
    with Session(engine) as db:
        seed_database(db, settings)
        import_open_content_catalog(db, load_open_content_catalog(SOURCE_PATH))
        import_translation_corpus(
            db,
            load_translation_corpus(TRANSLATION_PATH),
            artifact_locator=str(TRANSLATION_PATH),
        )
        artifacts = db.scalars(select(KbTranslationArtifact)).all()
        for artifact in artifacts:
            record_translation_review(
                db,
                artifact_stable_id=artifact.stable_id,
                review_type="medical",
                reviewer_id="test-medical-reviewer",
                approved=True,
                reviewed_at=reviewed_at,
            )
            record_translation_review(
                db,
                artifact_stable_id=artifact.stable_id,
                review_type="native_chinese",
                reviewer_id="test-native-chinese-reviewer",
                approved=True,
                reviewed_at=reviewed_at,
            )
        source_count = db.scalar(select(func.count()).select_from(KbSource))
        corpus = load_summary_corpus(SUMMARY_PATH)
        first = import_reviewed_summary_corpus(
            db,
            corpus,
            artifact_locator=str(SUMMARY_PATH),
            reviewer_id="test-summary-reviewers",
            reviewed_at=reviewed_at,
        )
        second = import_reviewed_summary_corpus(
            db,
            corpus,
            artifact_locator=str(SUMMARY_PATH),
            reviewer_id="test-summary-reviewers",
            reviewed_at=reviewed_at,
        )
        db.commit()

        assert first == 55
        assert second == 0
        assert db.scalar(select(func.count()).select_from(KbSource)) == source_count
        assert db.scalar(select(func.count()).select_from(KbSummaryArtifact)) == 55

    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    response = client.get(
        "/api/v1/doctor/resources",
        params={"query": "usually has no symptoms"},
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 200
    assert any(
        item["source_id"] == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
        for item in response.json()["items"]
    )
