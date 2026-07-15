import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_ingestion import (
    ImmutableArtifactStore,
    activate_index_release,
    build_index_release,
    capture_source_content,
    import_catalog_metadata,
    load_catalog,
    rollback_index_release,
)
from app.models import KbReview, KbRightsRecord, KbSource, KbSourceVersion
from app.seed import seed_database
from tests.helpers import auth_header, login

CATALOG_PATH = Path("knowledge_base/catalog/authoritative_resources.v1.json")


def test_catalog_contains_complete_who_indexes_and_verified_nhc_sources() -> None:
    catalog = load_catalog(CATALOG_PATH)

    assert len(catalog.sources) == 298
    assert len({source.stable_id for source in catalog.sources}) == 298
    assert len({str(source.canonical_locator) for source in catalog.sources}) == 298
    assert all(source.lifecycle_state == "rights_pending" for source in catalog.sources)
    assert all(source.catalog_visible for source in catalog.sources)
    assert all(source.catalog_summary and source.search_keywords for source in catalog.sources)
    assert all(
        "article text is not stored" in source.catalog_summary
        if source.original_language == "en"
        else "尚未存储或概括文章正文" in source.catalog_summary
        for source in catalog.sources
    )
    who = [source for source in catalog.sources if source.publisher_stable_id == "KBP-WHO"]
    nhc = [source for source in catalog.sources if source.publisher_stable_id == "KBP-NHC"]
    bilingual = [source for source in who if source.official_translations]
    chinese_only = [
        source
        for source in who
        if source.original_language == "zh-Hans" and not source.official_translations
    ]
    english_only = [source for source in who if source.original_language == "en"]
    assert len(who) == 246
    assert len(nhc) == 52
    assert len(bilingual) == 234
    assert len(chinese_only) == 5
    assert len(english_only) == 7
    assert len(bilingual) + len(chinese_only) == 239
    assert len(bilingual) + len(english_only) == 241
    assert all(source.authority_tier == "A" for source in nhc)
    assert all(source.original_language == "zh-Hans" for source in nhc)
    assert all(source.canonical_locator.host == "www.nhc.gov.cn" for source in nhc)
    assert {"高血压", "糖尿病", "哮喘"} <= {source.title for source in catalog.sources}
    assert "原发性肝癌诊疗指南（2024年版）" in {source.title for source in nhc}


def test_metadata_import_is_idempotent_and_never_admits_pending_rights() -> None:
    catalog = load_catalog(CATALOG_PATH)
    with Session(engine) as db:
        first = import_catalog_metadata(db, catalog)
        second = import_catalog_metadata(db, catalog)
        db.commit()

        assert first == (2, 2, 298)
        assert second == (0, 0, 0)
        assert db.scalar(select(func.count()).select_from(KbSource)) == 298
        assert db.scalar(select(func.count()).select_from(KbSourceVersion)) == 298
        assert (
            db.scalar(select(func.count()).select_from(KbSource).where(KbSource.doctor_eligible))
            == 0
        )


def test_raw_capture_fails_closed_without_approved_storage_rights(tmp_path: Path) -> None:
    rights = KbRightsRecord(
        stable_id="KBR-TEST-PENDING",
        publisher_id=None,
        scope="source",
        evidence_checksum="0" * 64,
        evidence_locator="https://example.invalid/rights",
        decision_status="pending",
        storage_allowed=False,
    )
    store = ImmutableArtifactStore(tmp_path)

    with pytest.raises(PermissionError, match="denied"):
        capture_source_content(store, rights, b"raw", b"normalized")
    assert not list(tmp_path.rglob("*"))


def test_release_manifest_is_deterministic_and_rollback_restores_predecessor(
    tmp_path: Path,
) -> None:
    catalog = load_catalog(CATALOG_PATH)
    with Session(engine) as db:
        import_catalog_metadata(db, catalog)
        source = db.scalar(select(KbSource).order_by(KbSource.stable_id))
        assert source is not None
        rights = db.get(KbRightsRecord, source.rights_record_id)
        version = db.scalar(select(KbSourceVersion).where(KbSourceVersion.source_id == source.id))
        assert rights is not None and version is not None
        rights.decision_status = "approved"
        rights.commercial_use_allowed = True
        rights.storage_allowed = True
        rights.embedding_allowed = True
        rights.excerpt_display_allowed = True
        source.doctor_eligible = True
        source.lifecycle_state = "doctor_approved"
        source.medical_review_status = "approved"
        version.review_decision = "approved"
        db.add(
            KbReview(
                stable_id="KBRV-RELEASE-TEST-MEDICAL",
                target_type="source_version",
                target_stable_id=version.stable_id,
                review_type="medical",
                reviewer_role="doctor",
                reviewer_id="reviewer-test",
                decision="approved",
                decision_code="approved_for_doctor_retrieval",
                reviewed_at=datetime.now(UTC),
            )
        )
        db.flush()
        store = ImmutableArtifactStore(tmp_path)

        first = build_index_release(
            db,
            store,
            [version.id],
            audience="doctor",
            embedding_model_version="embedding-test-v1",
            lexical_analyzer_version="lexical-test-v1",
            reranker_version="none",
            approver_ids=["reviewer-test"],
        )
        identical = build_index_release(
            db,
            store,
            [version.id],
            audience="doctor",
            embedding_model_version="embedding-test-v1",
            lexical_analyzer_version="lexical-test-v1",
            reranker_version="none",
            approver_ids=["reviewer-test"],
        )
        assert identical.id == first.id
        activate_index_release(db, first, audience="doctor", activated_by="release-test")

        second_version = KbSourceVersion(
            stable_id=f"{version.stable_id}-V2",
            source_id=source.id,
            captured_at=datetime.now(UTC),
            capture_mode="metadata_only",
            raw_checksum=hashlib.sha256(b"v2").hexdigest(),
            normalized_checksum=hashlib.sha256(b"normalized-v2").hexdigest(),
            parser_version="test-v2",
            change_summary="Release rollback test version.",
            review_decision="approved",
        )
        db.add(second_version)
        db.flush()
        db.add(
            KbReview(
                stable_id="KBRV-RELEASE-TEST-MEDICAL-V2",
                target_type="source_version",
                target_stable_id=second_version.stable_id,
                review_type="medical",
                reviewer_role="doctor",
                reviewer_id="reviewer-test",
                decision="approved",
                decision_code="approved_for_doctor_retrieval",
                reviewed_at=datetime.now(UTC),
            )
        )
        db.flush()
        second = build_index_release(
            db,
            store,
            [second_version.id],
            audience="doctor",
            embedding_model_version="embedding-test-v1",
            lexical_analyzer_version="lexical-test-v1",
            reranker_version="none",
            approver_ids=["reviewer-test"],
        )
        activate_index_release(db, second, audience="doctor", activated_by="release-test")

        restored = rollback_index_release(db, audience="doctor", activated_by="rollback-test")
        assert restored.id == first.id


def test_doctor_catalog_endpoint_lists_metadata_and_denies_patient(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        import_catalog_metadata(db, load_catalog(CATALOG_PATH))
        db.commit()

    doctor = login(
        client,
        "doctor.demo@example.com",
        settings.seed_doctor_password.get_secret_value(),
    )
    response = client.get(
        "/api/v1/doctor/resources?query=高血压",
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "高血压"
    assert response.json()["items"][0]["title_en"] == "Hypertension"
    assert response.json()["items"][0]["is_bilingual"] is True
    assert response.json()["items"][0]["available_languages"] == ["zh-Hans", "en"]
    assert response.json()["items"][0]["rights_mode"] == "official_link_only"

    english_response = client.get(
        "/api/v1/doctor/resources?query=Hypertension",
        headers=auth_header(doctor["access_token"]),
    )
    assert english_response.status_code == 200
    assert english_response.json()["total"] == 1
    assert english_response.json()["items"][0]["title"] == "高血压"

    nhc_response = client.get(
        "/api/v1/doctor/resources?query=原发性肝癌诊疗指南",
        headers=auth_header(doctor["access_token"]),
    )
    assert nhc_response.status_code == 200
    assert nhc_response.json()["total"] == 1
    nhc_item = nhc_response.json()["items"][0]
    assert nhc_item["publisher_id"] == "KBP-NHC"
    assert nhc_item["authority_tier"] == "A"
    assert nhc_item["available_languages"] == ["zh-Hans"]
    assert nhc_item["is_bilingual"] is False

    english_only_response = client.get(
        "/api/v1/doctor/resources?query=Commercial%20determinants%20of%20health",
        headers=auth_header(doctor["access_token"]),
    )
    assert english_only_response.status_code == 200
    english_only_item = english_only_response.json()["items"][0]
    assert english_only_item["original_language"] == "en"
    assert english_only_item["title_en"] == "Commercial determinants of health"
    assert english_only_item["available_languages"] == ["en"]
    assert english_only_item["is_bilingual"] is False

    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    denied = client.get("/api/v1/doctor/resources", headers=auth_header(patient["access_token"]))
    assert denied.status_code == 403
