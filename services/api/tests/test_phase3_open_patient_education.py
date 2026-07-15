from collections import Counter
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import KbPassage, KbRightsRecord, KbSource, KbSourceVersion
from app.open_content_ingestion import (
    EXPECTED_COLLECTION_COUNTS,
    import_open_content_catalog,
    load_open_content_catalog,
)
from app.seed import seed_database
from tests.helpers import auth_header, login

CORPUS_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")


def test_open_corpus_has_exact_agreed_selection_and_original_text_only() -> None:
    catalog = load_open_content_catalog(CORPUS_PATH)

    assert len(catalog.documents) == 55
    assert Counter(document.collection for document in catalog.documents) == (
        EXPECTED_COLLECTION_COUNTS
    )
    assert all(document.original_language == "en" for document in catalog.documents)
    assert all(document.sections for document in catalog.documents)
    assert all(document.publisher_date_text for document in catalog.documents)
    assert all(
        document.publisher_summary is None or document.publisher_summary
        for document in catalog.documents
    )
    assert "translation" in catalog.capture_policy
    assert "Chinese authority controls" in catalog.jurisdiction_note
    assert {publisher.key for publisher in catalog.publishers} == {
        "medlineplus",
        "nci",
        "nimh",
        "myhealthfinder",
    }


def test_open_corpus_import_is_idempotent_and_retrieval_stays_closed() -> None:
    catalog = load_open_content_catalog(CORPUS_PATH)
    with Session(engine) as db:
        first = import_open_content_catalog(db, catalog)
        second = import_open_content_catalog(db, catalog)
        db.commit()

        assert first[:3] == (4, 4, 55)
        assert first[3] > 55
        assert second == (0, 0, 0, 0)
        assert db.scalar(select(func.count()).select_from(KbSource)) == 55
        assert db.scalar(select(func.count()).select_from(KbSourceVersion)) == 55
        assert db.scalar(select(func.count()).select_from(KbPassage)) == first[3]
        assert db.scalar(select(func.count()).select_from(KbRightsRecord)) == 4
        assert (
            db.scalar(select(func.count()).select_from(KbSource).where(KbSource.doctor_eligible))
            == 0
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
            db.scalar(select(func.count()).select_from(KbPassage).where(KbPassage.vector_eligible))
            == 0
        )


def test_doctor_can_read_original_with_provenance_but_patient_cannot(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        import_open_content_catalog(db, load_open_content_catalog(CORPUS_PATH))
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    listing = client.get(
        "/api/v1/doctor/resources?publisher_id=KBP-MEDLINEPLUS&limit=100",
        headers=auth_header(doctor["access_token"]),
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 35
    item = next(
        entry
        for entry in listing.json()["items"]
        if entry["source_id"] == "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE"
    )
    assert item["rights_mode"] == "stored_text"
    assert item["rights_decision_status"] == "approved"
    assert item["publisher_date_text"].startswith("Date created:")
    assert item["available_languages"] == ["en"]

    detail = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=auth_header(doctor["access_token"]),
    )
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["official_locator"].startswith("https://medlineplus.gov/")
    assert payload["license_name"].startswith("U.S. Government public domain")
    assert payload["rights_evidence_locator"].endswith("/about/using/usingcontent/")
    assert payload["sections"]
    assert len(payload["sections"][0]["original_text"]) > 500

    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    denied = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=auth_header(patient["access_token"]),
    )
    assert denied.status_code == 403

    with Session(engine) as db:
        rights = db.scalar(
            select(KbRightsRecord).where(
                KbRightsRecord.stable_id == "KBR-MEDLINEPLUS-PUBLIC-DOMAIN"
            )
        )
        assert rights is not None
        rights.redistribution_allowed = False
        db.commit()

    rights_closed = client.get(
        f"/api/v1/doctor/resources/{item['source_id']}",
        headers=auth_header(doctor["access_token"]),
    )
    assert rights_closed.status_code == 200
    assert rights_closed.json()["rights_mode"] == "official_link_only"
    assert rights_closed.json()["sections"] == []
