import json
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import KbPassage, KbRightsRecord, KbSource, KbSourceVersion
from app.open_content_ingestion import (
    EXPECTED_COLLECTION_COUNTS,
    OpenContentCatalog,
    import_open_content_catalog,
    load_open_content_catalog,
)
from app.seed import seed_database
from tests.helpers import auth_header, login

CORPUS_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
SUPPLEMENTARY_CORPUS_PATH = Path("knowledge_base/catalog/open_symptom_presentations.v1.json")


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


def test_supplementary_symptom_corpus_inherits_rights_and_stays_review_pending() -> None:
    base = load_open_content_catalog(CORPUS_PATH)
    supplement = load_open_content_catalog(SUPPLEMENTARY_CORPUS_PATH)
    expected_ids = {
        "KBS-MEDLINEPLUS-LOW-BLOOD-PRESSURE",
        "KBS-MEDLINEPLUS-DIZZINESS-AND-VERTIGO",
        "KBS-MEDLINEPLUS-ARRHYTHMIA",
        "KBS-MEDLINEPLUS-PESTICIDES",
        "KBS-MEDLINEPLUS-SKIN-CONDITIONS",
        "KBS-NHS-BABY-MOVEMENTS",
    }

    assert supplement.schema_version == "1.1"
    assert supplement.expected_collection_counts == {
        "medlineplus_health_topic": 5,
        "nhs_patient_education": 1,
    }
    assert {item.stable_id for item in supplement.documents} == expected_ids
    assert expected_ids.isdisjoint({item.stable_id for item in base.documents})
    assert {publisher.key for publisher in supplement.publishers} == {"medlineplus", "nhs"}
    assert next(item for item in supplement.publishers if item.key == "medlineplus") == next(
        item for item in base.publishers if item.key == "medlineplus"
    )
    nhs = next(item for item in supplement.publishers if item.key == "nhs")
    assert nhs.rights_stable_id == "KBR-NHS-UK-OGL-V3"
    assert nhs.rights_name.startswith("Open Government Licence v3.0")
    assert nhs.jurisdiction == "GB-ENG"
    assert nhs.rights_permissions.translation_allowed
    assert nhs.rights_permissions.model_provider_transmission_allowed
    assert len(nhs.rights_evidence.supporting_locators) == 2
    serialized_catalog = SUPPLEMENTARY_CORPUS_PATH.read_text(encoding="utf-8")
    assert "RCQ-" not in serialized_catalog
    nhs_document = next(
        document
        for document in supplement.documents
        if document.stable_id == "KBS-NHS-BABY-MOVEMENTS"
    )
    nhs_text = "\n".join(section.text for section in nhs_document.sections)
    assert "moving less than usual" in nhs_text
    assert "Do not wait until the next day" in nhs_text
    assert "Tommy" not in nhs_text
    assert "Royal College" not in nhs_text

    base_payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    base_payload["expected_collection_counts"] = EXPECTED_COLLECTION_COUNTS
    with pytest.raises(ValidationError, match="schema 1.0 must use the frozen"):
        OpenContentCatalog.model_validate(base_payload)

    supplement_payload = json.loads(SUPPLEMENTARY_CORPUS_PATH.read_text(encoding="utf-8"))
    supplement_payload.pop("expected_collection_counts")
    with pytest.raises(ValidationError, match="schema 1.1 requires"):
        OpenContentCatalog.model_validate(supplement_payload)

    with Session(engine) as db:
        import_open_content_catalog(db, base)
        first = import_open_content_catalog(
            db,
            supplement,
            artifact_locator=str(SUPPLEMENTARY_CORPUS_PATH),
        )
        second = import_open_content_catalog(
            db,
            supplement,
            artifact_locator=str(SUPPLEMENTARY_CORPUS_PATH),
        )
        db.commit()

        assert first == (1, 1, 6, 11)
        assert second == (0, 0, 0, 0)
        sources = db.scalars(select(KbSource).where(KbSource.stable_id.in_(expected_ids))).all()
        assert len(sources) == 6
        assert all(source.lifecycle_state == "rights_cleared_review_pending" for source in sources)
        assert all(not source.patient_eligible and not source.doctor_eligible for source in sources)
        versions = db.scalars(
            select(KbSourceVersion).where(
                KbSourceVersion.source_id.in_(source.id for source in sources)
            )
        ).all()
        assert len(versions) == 6
        assert all(
            version.normalized_artifact_locator.startswith(f"{SUPPLEMENTARY_CORPUS_PATH}#")
            for version in versions
        )
        nhs_source = next(
            source for source in sources if source.stable_id == "KBS-NHS-BABY-MOVEMENTS"
        )
        assert nhs_source.jurisdiction == "GB-ENG"
        assert nhs_source.population == "pregnant_people"
        assert nhs_source.review_due_date.isoformat() == "2027-07-08"
        nhs_rights = db.scalar(
            select(KbRightsRecord).where(KbRightsRecord.stable_id == "KBR-NHS-UK-OGL-V3")
        )
        assert nhs_rights is not None
        assert nhs_rights.decision_status == "approved"
        assert nhs_rights.translation_allowed
        assert nhs_rights.model_provider_transmission_allowed
        assert "must not imply NHS endorsement" in nhs_rights.permission_reference


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
