import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_translation import (
    TRANSLATION_PROMPT_POLICY_VERSION,
    TranslationCorpusArtifact,
    TranslationDocumentArtifact,
    TranslationSectionArtifact,
    TranslationUsage,
    _canonical_translation_document,
    import_translation_corpus,
    load_translation_corpus,
    record_translation_review,
    sha256_text,
)
from app.models import (
    KbPassage,
    KbRightsRecord,
    KbSource,
    KbTranslationArtifact,
    KbTranslationSection,
)
from app.open_content_ingestion import import_open_content_catalog, load_open_content_catalog
from app.seed import seed_database
from tests.helpers import auth_header, login

SOURCE_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
SUPPLEMENTARY_SOURCE_PATH = Path("knowledge_base/catalog/open_symptom_presentations.v1.json")
SUPPLEMENTARY_TRANSLATION_PATH = Path(
    "knowledge_base/translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.json"
)


def test_translation_validation_accepts_untranslated_reference_citations() -> None:
    heading = "参考文献"
    text = (
        "Smith A. Clinical reference. https://example.test/one\n"
        "Jones B. Medical reference. https://example.test/two"
    )
    section = TranslationSectionArtifact(
        ordinal=0,
        source_section_stable_id="KBC-REFERENCE-TEST-000",
        source_text_checksum="0" * 64,
        translated_heading=heading,
        translated_text=text,
        translation_checksum=sha256_text(f"{heading}\n{text}"),
    )

    assert section.translated_heading == "参考文献"


def test_translation_schema_1_1_binds_a_supplementary_corpus_count() -> None:
    document = _translation_corpus().documents[0]
    payload = {
        "schema_version": "1.1",
        "source_corpus_locator": "knowledge_base/catalog/supplement.json",
        "source_corpus_checksum": "0" * 64,
        "expected_document_count": 1,
        "target_language": "zh-Hans",
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "prompt_policy_version": TRANSLATION_PROMPT_POLICY_VERSION,
        "completed_at": datetime(2026, 7, 21, tzinfo=UTC),
        "documents": [document],
    }

    artifact = TranslationCorpusArtifact.model_validate(payload)
    assert artifact.expected_document_count == 1
    with pytest.raises(ValidationError, match="exactly 2"):
        TranslationCorpusArtifact.model_validate({**payload, "expected_document_count": 2})
    without_count = dict(payload)
    without_count.pop("expected_document_count")
    with pytest.raises(ValidationError, match="requires expected_document_count"):
        TranslationCorpusArtifact.model_validate(without_count)
    with pytest.raises(ValidationError, match="schema 1.0 must use the frozen"):
        TranslationCorpusArtifact.model_validate({**payload, "schema_version": "1.0"})


def _translation_corpus() -> TranslationCorpusArtifact:
    source = load_open_content_catalog(SOURCE_PATH)
    documents: list[TranslationDocumentArtifact] = []
    for document in source.documents:
        sections: list[TranslationSectionArtifact] = []
        for ordinal, section in enumerate(document.sections):
            translated_heading = f"第 {ordinal + 1} 节"
            translated_text = (
                f"这是来源文档 {document.stable_id} 第 {ordinal + 1} 节的"
                "简体中文测试翻译，保留原文结构且尚待人工审核。"
            )
            sections.append(
                TranslationSectionArtifact(
                    ordinal=ordinal,
                    source_section_stable_id=(
                        f"KBC-{document.stable_id.removeprefix('KBS-')}-{ordinal:03d}"
                    ),
                    source_text_checksum=sha256_text(section.text),
                    translated_heading=translated_heading,
                    translated_text=translated_text,
                    translation_checksum=sha256_text(f"{translated_heading}\n{translated_text}"),
                )
            )
        translated_title = f"健康知识与患者教育（{len(documents) + 1}）"
        section_payloads = [section.model_dump(mode="json") for section in sections]
        documents.append(
            TranslationDocumentArtifact(
                source_id=document.stable_id,
                source_version_id=(
                    f"KBV-{document.stable_id.removeprefix('KBS-')}-"
                    f"{document.raw_checksum[:12].upper()}"
                ),
                source_normalized_checksum=document.normalized_checksum,
                translated_title=translated_title,
                sections=sections,
                usage=TranslationUsage(
                    input_tokens=100,
                    output_tokens=120,
                    total_tokens=220,
                ),
                generated_at=datetime(2026, 7, 15, tzinfo=UTC),
                response_checksum=sha256_text(
                    _canonical_translation_document(translated_title, section_payloads)
                ),
            )
        )
    return TranslationCorpusArtifact(
        schema_version="1.0",
        source_corpus_locator=str(SOURCE_PATH),
        source_corpus_checksum=hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        target_language="zh-Hans",
        provider="deepseek",
        model="deepseek-v4-flash",
        prompt_policy_version=TRANSLATION_PROMPT_POLICY_VERSION,
        completed_at=datetime(2026, 7, 15, tzinfo=UTC),
        documents=documents,
    )


def test_translation_import_is_idempotent_and_never_adds_sources() -> None:
    source = load_open_content_catalog(SOURCE_PATH)
    corpus = _translation_corpus()
    with Session(engine) as db:
        import_open_content_catalog(db, source)
        source_count = db.scalar(select(func.count()).select_from(KbSource))
        first = import_translation_corpus(
            db,
            corpus,
            artifact_locator="knowledge_base/translations/test.json",
        )
        second = import_translation_corpus(
            db,
            corpus,
            artifact_locator="knowledge_base/translations/test.json",
        )
        db.commit()

        assert source_count == 55
        assert db.scalar(select(func.count()).select_from(KbSource)) == source_count
        assert first == (55, sum(len(item.sections) for item in source.documents))
        assert second == (0, 0)
        assert db.scalar(select(func.count()).select_from(KbTranslationArtifact)) == 55
        assert db.scalar(select(func.count()).select_from(KbTranslationSection)) == first[1]
        assert (
            db.scalar(select(func.count()).select_from(KbPassage).where(KbPassage.lexical_eligible))
            == 0
        )
        assert (
            db.scalar(select(func.count()).select_from(KbPassage).where(KbPassage.vector_eligible))
            == 0
        )


def test_supplementary_translation_artifact_imports_only_as_pending_review() -> None:
    source = load_open_content_catalog(SUPPLEMENTARY_SOURCE_PATH)
    corpus = load_translation_corpus(SUPPLEMENTARY_TRANSLATION_PATH)
    with Session(engine) as db:
        import_open_content_catalog(
            db,
            source,
            artifact_locator=str(SUPPLEMENTARY_SOURCE_PATH),
        )
        first = import_translation_corpus(
            db,
            corpus,
            artifact_locator=str(SUPPLEMENTARY_TRANSLATION_PATH),
        )
        second = import_translation_corpus(
            db,
            corpus,
            artifact_locator=str(SUPPLEMENTARY_TRANSLATION_PATH),
        )
        db.commit()

        assert corpus.schema_version == "1.1"
        assert corpus.expected_document_count == 6
        assert first == (6, 11)
        assert second == (0, 0)
        artifacts = db.scalars(select(KbTranslationArtifact)).all()
        assert len(artifacts) == 6
        assert all(artifact.status == "generated_pending_review" for artifact in artifacts)
        assert all(artifact.medical_review_status == "pending" for artifact in artifacts)
        assert all(artifact.native_language_review_status == "pending" for artifact in artifacts)
        assert not db.scalar(
            select(func.count()).select_from(KbPassage).where(KbPassage.lexical_eligible)
        )
        assert not db.scalar(
            select(func.count()).select_from(KbPassage).where(KbPassage.vector_eligible)
        )


def test_translation_import_fails_closed_when_provider_right_is_revoked() -> None:
    with Session(engine) as db:
        import_open_content_catalog(db, load_open_content_catalog(SOURCE_PATH))
        rights = db.scalar(
            select(KbRightsRecord).where(
                KbRightsRecord.stable_id == "KBR-MEDLINEPLUS-PUBLIC-DOMAIN"
            )
        )
        assert rights is not None
        rights.model_provider_transmission_allowed = False
        with pytest.raises(ValueError, match="Translation/provider rights"):
            import_translation_corpus(
                db,
                _translation_corpus(),
                artifact_locator="knowledge_base/translations/test.json",
            )


def test_catalog_becomes_bilingual_only_after_both_human_reviews(
    client: TestClient,
    settings,
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        import_open_content_catalog(db, load_open_content_catalog(SOURCE_PATH))
        import_translation_corpus(
            db,
            _translation_corpus(),
            artifact_locator="knowledge_base/translations/test.json",
        )
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    headers = auth_header(doctor["access_token"])
    before = client.get(
        "/api/v1/doctor/resources?publisher_id=KBP-MEDLINEPLUS&limit=100",
        headers=headers,
    )
    item = next(
        entry
        for entry in before.json()["items"]
        if entry["source_id"] == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
    )
    assert before.json()["total"] == 35
    assert item["available_languages"] == ["en"]
    assert item["is_bilingual"] is False
    assert item["zh_translation_status"] == "generated_pending_review"

    with Session(engine) as db:
        artifact = db.scalar(
            select(KbTranslationArtifact).where(
                KbTranslationArtifact.source_id
                == db.scalar(
                    select(KbSource.id).where(
                        KbSource.stable_id == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
                    )
                )
            )
        )
        assert artifact is not None
        record_translation_review(
            db,
            artifact_stable_id=artifact.stable_id,
            review_type="medical",
            reviewer_id="medical-reviewer-1",
            approved=True,
        )
        db.commit()

    after_one = client.get(
        "/api/v1/doctor/resources?publisher_id=KBP-MEDLINEPLUS&limit=100",
        headers=headers,
    )
    item = next(
        entry
        for entry in after_one.json()["items"]
        if entry["source_id"] == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
    )
    assert item["available_languages"] == ["en"]
    assert item["zh_translation_status"] == "generated_pending_review"

    with Session(engine) as db:
        artifact = db.scalar(
            select(KbTranslationArtifact).where(
                KbTranslationArtifact.status == "generated_pending_review",
                KbTranslationArtifact.source_id
                == db.scalar(
                    select(KbSource.id).where(
                        KbSource.stable_id == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
                    )
                ),
            )
        )
        assert artifact is not None
        record_translation_review(
            db,
            artifact_stable_id=artifact.stable_id,
            review_type="native_chinese",
            reviewer_id="native-reviewer-1",
            approved=True,
        )
        db.commit()

    after_both = client.get(
        "/api/v1/doctor/resources?publisher_id=KBP-MEDLINEPLUS&limit=100",
        headers=headers,
    )
    item = next(
        entry
        for entry in after_both.json()["items"]
        if entry["source_id"] == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
    )
    assert after_both.json()["total"] == 35
    assert item["available_languages"] == ["en", "zh-Hans"]
    assert item["is_bilingual"] is True
    assert item["zh_translation_status"] == "approved"
    assert item["title"].startswith("健康知识与患者教育")

    chinese_search = client.get(
        f"/api/v1/doctor/resources?query={item['title']}&limit=100",
        headers=headers,
    )
    assert chinese_search.status_code == 200
    assert any(entry["source_id"] == item["source_id"] for entry in chinese_search.json()["items"])

    detail = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert len(detail.json()["translations"]) == 1
    translation = detail.json()["translations"][0]
    assert translation["language"] == "zh-Hans"
    assert translation["translation_type"] == "ai_generated_unofficial"
    assert translation["sections"]
