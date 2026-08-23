from pathlib import Path

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_ingestion import import_catalog_metadata, load_catalog
from app.models import KbPassage, KbRightsRecord, KbSource, KbSourceVersion
from app.seed import seed_database
from app.who_fact_sheets_ingestion import (
    WHO_RIGHTS_STABLE_ID,
    import_who_fact_sheet_corpus,
    load_who_fact_sheet_corpus,
)
from scripts.build_who_fact_sheets_corpus import structured_sections
from tests.helpers import auth_header, login

CATALOG_PATH = Path("knowledge_base/catalog/authoritative_resources.v1.json")
CORPUS_PATH = Path("knowledge_base/catalog/who_fact_sheets.official.v1.json")


def test_who_parser_preserves_legacy_orphan_text_nodes() -> None:
    soup = BeautifulSoup(
        """
        <article>
          <h2>Overview</h2>
          <p>Introductory paragraph.</p>
          <div>
            <p>The triple threat includes:</p>
            <strong>Noncommunicable diseases</strong>
            such as heart disease, asthma, cancer and diabetes.
            <p>Closing paragraph.</p>
          </div>
          <h3>Risk factors</h3>
          <h4>Environmental risks</h4>
          <p>Environmental risk details.</p>
          <h2>Terminal source heading</h2>
        </article>
        """,
        "html.parser",
    )
    sections = structured_sections(soup.article)
    captured = "\n".join(section["text"] for section in sections)
    assert "Introductory paragraph." in captured
    assert "Noncommunicable diseases" in captured
    assert "such as heart disease, asthma, cancer and diabetes." in captured
    assert "Closing paragraph." in captured
    assert sections[-2]["heading"] == "Risk factors / Environmental risks"
    assert sections[-1] == {
        "heading": "Terminal source heading",
        "text": "Terminal source heading",
    }


def test_who_corpus_is_complete_and_permission_bounded() -> None:
    corpus = load_who_fact_sheet_corpus(CORPUS_PATH)
    assert corpus.permission.request_id == "202609681"
    assert len(corpus.sources) >= 246
    assert corpus.expected_language_document_counts["en"] >= 241
    assert corpus.expected_language_document_counts["zh-Hans"] >= 239
    assert {"images", "logos", "third_party_credited_material"} <= set(corpus.excluded_content)
    assert all(
        document.sections and document.normalized_checksum
        for source in corpus.sources
        for document in source.documents
    )


def test_who_import_is_idempotent_and_retrieval_remains_closed() -> None:
    catalog = load_catalog(CATALOG_PATH)
    corpus = load_who_fact_sheet_corpus(CORPUS_PATH)
    with Session(engine) as db:
        import_catalog_metadata(db, catalog)
        first = import_who_fact_sheet_corpus(db, corpus)
        second = import_who_fact_sheet_corpus(db, corpus)
        db.commit()
        assert first[0] == 1
        assert first[1] == len(corpus.sources)
        assert first[2] > len(corpus.sources)
        assert second == (0, 0, 0)
        rights = db.scalar(
            select(KbRightsRecord).where(KbRightsRecord.stable_id == WHO_RIGHTS_STABLE_ID)
        )
        assert rights is not None
        assert rights.decision_status == "approved"
        assert rights.storage_allowed and rights.embedding_allowed
        assert rights.model_provider_transmission_allowed
        assert not rights.commercial_use_allowed
        assert not rights.translation_allowed
        assert not rights.prior_version_retention_allowed
        who_sources = db.scalars(
            select(KbSource).where(KbSource.rights_record_id == rights.id)
        ).all()
        assert len(who_sources) == len(corpus.sources)
        assert all(
            source.lifecycle_state == "rights_cleared_review_pending" for source in who_sources
        )
        assert all(
            not source.doctor_eligible and not source.patient_eligible for source in who_sources
        )
        source_ids = [source.id for source in who_sources]
        version_ids = db.scalars(
            select(KbSourceVersion.id).where(KbSourceVersion.source_id.in_(source_ids))
        ).all()
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbPassage)
                .where(KbPassage.version_id.in_(version_ids), KbPassage.lexical_eligible)
            )
            == 0
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbPassage)
                .where(KbPassage.version_id.in_(version_ids), KbPassage.vector_eligible)
            )
            == 0
        )


def test_doctor_reader_exposes_both_official_languages_without_retrieval_admission(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        import_catalog_metadata(db, load_catalog(CATALOG_PATH))
        import_who_fact_sheet_corpus(db, load_who_fact_sheet_corpus(CORPUS_PATH))
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    listing = client.get(
        "/api/v1/doctor/resources?query=高血压",
        headers=auth_header(doctor["access_token"]),
    )
    assert listing.status_code == 200
    item = listing.json()["items"][0]
    assert item["rights_mode"] == "stored_text"
    assert item["rights_decision_status"] == "approved"
    assert item["lifecycle_state"] == "rights_cleared_review_pending"

    detail = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=auth_header(doctor["access_token"]),
    )
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["sections"]
    assert any("高血压" in section["original_text"] for section in payload["sections"])
    official_english = next(
        translation for translation in payload["translations"] if translation["language"] == "en"
    )
    assert official_english["translation_type"] == "official_publisher_version"
    assert official_english["review_status"] == "official_text_medical_review_pending"
    assert official_english["sections"]
