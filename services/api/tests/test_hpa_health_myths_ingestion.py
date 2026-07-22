import re
from pathlib import Path

from fastapi.testclient import TestClient
from opencc import OpenCC
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.chatbot_contracts import EvidenceDecision, PatientEvidenceRequest
from app.database import engine
from app.hpa_health_myths_ingestion import (
    EXPECTED_ROW_COUNT,
    EXPECTED_SOURCE_COUNT,
    import_hpa_health_myths_corpus,
    load_hpa_health_myths_corpus,
)
from app.knowledge_retrieval import retrieve
from app.models import (
    KbPassage,
    KbReview,
    KbRightsRecord,
    KbSource,
    KbSourceVersion,
    KbTranslationArtifact,
)
from app.patient_knowledge_release import (
    build_and_activate_patient_release,
    promote_reviewed_hpa_for_patient_use,
)
from app.seed import seed_database
from tests.helpers import auth_header, login

CORPUS_PATH = Path("knowledge_base/catalog/hpa_health_myths.zh-Hans.v1.json")


def test_hpa_corpus_preserves_every_row_as_simplified_chinese_version() -> None:
    corpus = load_hpa_health_myths_corpus(CORPUS_PATH)
    versions = [version for source in corpus.sources for version in source.versions]
    converter = OpenCC("t2s")

    assert len(corpus.sources) == EXPECTED_SOURCE_COUNT
    assert len(versions) == EXPECTED_ROW_COUNT
    assert corpus.duplicate_question_group_count == 13
    assert all(
        converter.convert(item.simplified_question) == item.simplified_question for item in versions
    )
    assert all(
        converter.convert(item.simplified_answer) == item.simplified_answer for item in versions
    )
    assert all(
        not re.search(
            r"</?(?:a|div|span|p|br|strong|ol|li)\b|&[a-zA-Z#0-9]+;",
            item.simplified_answer,
            flags=re.IGNORECASE,
        )
        for item in versions
    )
    assert "预防保健服务是健保署提供的?" in {item.simplified_question for item in versions}
    assert "卫生福利部国民健康署" == corpus.publisher_name_zh_hans


def test_hpa_import_is_idempotent_and_keeps_all_review_gates_closed() -> None:
    corpus = load_hpa_health_myths_corpus(CORPUS_PATH)
    with Session(engine) as db:
        first = import_hpa_health_myths_corpus(
            db,
            corpus,
            artifact_locator=str(CORPUS_PATH),
        )
        second = import_hpa_health_myths_corpus(
            db,
            corpus,
            artifact_locator=str(CORPUS_PATH),
        )
        db.commit()

        assert first == (
            1,
            1,
            EXPECTED_SOURCE_COUNT,
            EXPECTED_ROW_COUNT,
            EXPECTED_ROW_COUNT,
            EXPECTED_ROW_COUNT,
        )
        assert second == (0, 0, 0, 0, 0, 0)
        assert db.scalar(select(func.count()).select_from(KbSource)) == EXPECTED_SOURCE_COUNT
        assert db.scalar(select(func.count()).select_from(KbSourceVersion)) == EXPECTED_ROW_COUNT
        assert db.scalar(select(func.count()).select_from(KbPassage)) == EXPECTED_ROW_COUNT
        assert (
            db.scalar(select(func.count()).select_from(KbTranslationArtifact)) == EXPECTED_ROW_COUNT
        )
        assert (
            db.scalar(select(func.count()).select_from(KbSource).where(KbSource.patient_eligible))
            == 0
        )
        assert (
            db.scalar(select(func.count()).select_from(KbPassage).where(KbPassage.lexical_eligible))
            == 0
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbTranslationArtifact)
                .where(KbTranslationArtifact.target_language == "zh-Hans")
            )
            == EXPECTED_ROW_COUNT
        )


def test_doctor_catalog_exposes_all_hpa_records_with_simplified_content(
    client: TestClient,
    settings,
) -> None:
    corpus = load_hpa_health_myths_corpus(CORPUS_PATH)
    with Session(engine) as db:
        seed_database(db, settings)
        import_hpa_health_myths_corpus(db, corpus, artifact_locator=str(CORPUS_PATH))
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    listing = client.get(
        "/api/v1/doctor/resources?publisher_id=KBP-TW-HPA&limit=100",
        headers=auth_header(doctor["access_token"]),
    )
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] == EXPECTED_ROW_COUNT
    assert len(payload["items"]) == 100
    assert all(item["publisher_id"] == "KBP-TW-HPA" for item in payload["items"])
    assert all("zh-Hans" in item["available_languages"] for item in payload["items"])
    assert all(item["source_id"].startswith("KBV-HPA-") for item in payload["items"])

    item = payload["items"][0]
    detail = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=auth_header(doctor["access_token"]),
    )
    assert detail.status_code == 200
    resource = detail.json()
    assert resource["publisher_name"] == "卫生福利部国民健康署"
    assert resource["jurisdiction"] == "TW"
    assert resource["sections"]
    assert resource["translations"][0]["language"] == "zh-Hans"
    assert resource["translations"][0]["translation_type"] == ("deterministic_script_conversion")
    assert resource["translations"][0]["review_status"] == (
        "pending_medical_and_native_simplified_chinese_review"
    )
    assert resource["translations"][0]["sections"][0]["original_text"]


def test_reviewed_hpa_records_build_idempotent_patient_release(tmp_path) -> None:
    corpus = load_hpa_health_myths_corpus(CORPUS_PATH)
    with Session(engine) as db:
        import_hpa_health_myths_corpus(db, corpus, artifact_locator=str(CORPUS_PATH))
        first = promote_reviewed_hpa_for_patient_use(
            db,
            reviewer_id="product-owner-confirmed-unspecified",
            findings="All 697 records were human-reviewed for patient use.",
        )
        second = promote_reviewed_hpa_for_patient_use(
            db,
            reviewer_id="product-owner-confirmed-unspecified",
            findings="All 697 records were human-reviewed for patient use.",
        )
        release = build_and_activate_patient_release(
            db,
            version_ids=first.version_ids,
            artifact_root=tmp_path,
            approver_id="product-owner-confirmed-unspecified",
        )
        db.flush()

        assert first.versions_created == EXPECTED_ROW_COUNT
        assert first.sections_created == EXPECTED_ROW_COUNT
        assert first.passages_created == EXPECTED_ROW_COUNT
        assert first.reviews_created == EXPECTED_ROW_COUNT * 4
        assert second.versions_created == 0
        assert second.sections_created == 0
        assert second.passages_created == 0
        assert second.reviews_created == 0
        assert release.source_count == EXPECTED_SOURCE_COUNT
        assert release.version_count == EXPECTED_SOURCE_COUNT
        assert len(release.build_results_json["historical_markers"]) == (
            EXPECTED_ROW_COUNT - EXPECTED_SOURCE_COUNT
        )
        assert release.passage_count == EXPECTED_SOURCE_COUNT
        assert release.status == "active"
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbReview)
                .where(KbReview.decision_code == "product_owner_confirmed_hpa_patient_use_approved")
            )
            == EXPECTED_ROW_COUNT * 4
        )
        rights = db.scalar(
            select(KbRightsRecord).where(
                KbRightsRecord.stable_id == "KBR-TW-HPA-OGDL-1-0-HEALTH-MYTHS"
            )
        )
        assert rights is not None
        assert rights.embedding_allowed
        assert rights.model_provider_transmission_allowed
        reviewed_sources = list(
            db.scalars(select(KbSource).where(KbSource.publisher_id == rights.publisher_id))
        )
        assert len(reviewed_sources) == EXPECTED_SOURCE_COUNT
        assert all("已完成" in source.catalog_summary for source in reviewed_sources)
        assert all(
            "审核尚未完成" not in source.catalog_summary
            for source in reviewed_sources
        )

        # Patient requests cannot observe an activated release until its build
        # transaction commits. Committing here also keeps this integration test
        # on the production visibility boundary instead of querying hundreds of
        # newly inserted, uncommitted release rows with stale planner statistics.
        db.commit()
        result = retrieve(
            db,
            PatientEvidenceRequest(query="嚼槟榔不咽槟榔汁是不是就没事"),
            audience="patient",
        )
        assert result.decision == EvidenceDecision.sufficient
        assert result.candidates
        assert any("不吞槟榔汁" in item.passage.text for item in result.candidates)
        assert all(item.source.publisher_id == rights.publisher_id for item in result.candidates)
