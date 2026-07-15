import hashlib
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_ingestion import (
    ImmutableArtifactStore,
    activate_index_release,
    build_index_release,
)
from app.knowledge_retrieval import (
    EMBEDDING_MODEL_VERSION,
    LEXICAL_ANALYZER_VERSION,
    RERANKER_VERSION,
    embed_text,
)
from app.models import (
    KbPassage,
    KbPublisher,
    KbRetrievalEvent,
    KbReview,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
    KbTerm,
)
from app.seed import seed_database
from tests.helpers import auth_header, login


def _add_approved_source(
    db: Session,
    *,
    suffix: str,
    title: str,
    passage_text: str,
    conflict_group_key: str | None = None,
) -> KbSourceVersion:
    publisher = KbPublisher(
        stable_id=f"KBP-SYNTHETIC-{suffix}",
        official_name_zh=f"合成测试卫生机构{suffix}",
        organization_type="national_health_authority",
        authority_basis="Synthetic authority metadata used only in retrieval tests.",
        authority_evidence_locator=f"https://example.invalid/publisher/{suffix}",
        verified_domains_json=["example.invalid"],
        jurisdiction="CN",
        review_status="authority_verified",
        allowed_content_classes_json=["guideline"],
        reviewed_at=datetime.now(UTC),
    )
    db.add(publisher)
    db.flush()
    rights = KbRightsRecord(
        stable_id=f"KBR-SYNTHETIC-{suffix}",
        publisher_id=publisher.id,
        scope="publisher",
        commercial_use_allowed=True,
        storage_allowed=True,
        transformation_allowed=True,
        embedding_allowed=True,
        excerpt_display_allowed=True,
        evidence_checksum="a" * 64,
        evidence_locator=f"https://example.invalid/rights/{suffix}",
        decision_status="approved",
    )
    db.add(rights)
    db.flush()
    source = KbSource(
        stable_id=f"KBS-SYNTHETIC-{suffix}",
        publisher_id=publisher.id,
        rights_record_id=rights.id,
        title=title,
        canonical_locator=f"https://example.invalid/source/{suffix}",
        source_type="clinical_guideline",
        jurisdiction="CN",
        intended_audiences_json=["doctor", "patient"],
        topic="chronic_disease",
        original_language="zh-Hans",
        official_translations_json=[],
        catalog_summary=f"关于{title}的合成测试目录摘要。",
        search_keywords_json=["高血压", "血压高", "high blood pressure"],
        publication_date=date(2026, 1, 1),
        authority_tier="A",
        lifecycle_state="patient_approved",
        medical_review_status="approved",
        native_language_review_status="approved",
        doctor_eligible=True,
        patient_eligible=True,
        catalog_visible=True,
        status="current",
        discovered_at=datetime.now(UTC),
        catalog_verified_at=datetime.now(UTC),
    )
    db.add(source)
    db.flush()
    version = KbSourceVersion(
        stable_id=f"KBV-SYNTHETIC-{suffix}",
        source_id=source.id,
        captured_at=datetime.now(UTC),
        capture_mode="synthetic_test",
        raw_checksum=hashlib.sha256(f"raw-{suffix}".encode()).hexdigest(),
        normalized_checksum=hashlib.sha256(passage_text.encode()).hexdigest(),
        parser_version="synthetic-test-v1",
        valid_from=datetime.now(UTC),
        review_decision="approved",
    )
    db.add(version)
    db.flush()
    section = KbSection(
        stable_id=f"KBSEC-SYNTHETIC-{suffix}",
        version_id=version.id,
        heading_path_json=["高血压管理"],
        ordinal=1,
        language="zh-Hans",
    )
    db.add(section)
    db.flush()
    db.add(
        KbPassage(
            stable_id=f"KBPASS-SYNTHETIC-{suffix}",
            section_id=section.id,
            version_id=version.id,
            ordinal=1,
            text=passage_text,
            language="zh-Hans",
            character_count=len(passage_text),
            clinical_concept_tags_json=["高血压", "血压管理"],
            audience_json=["doctor", "patient"],
            chunking_version="clinical-structure-v1",
            patient_readability_review_status="approved",
            lexical_eligible=True,
            vector_eligible=True,
            embedding_json=embed_text(passage_text),
            content_checksum=hashlib.sha256(passage_text.encode()).hexdigest(),
            conflict_group_key=conflict_group_key,
        )
    )
    for review_type in ("medical", "native_language"):
        db.add(
            KbReview(
                stable_id=f"KBRV-{suffix}-{review_type.upper()}",
                target_type="source_version",
                target_stable_id=version.stable_id,
                review_type=review_type,
                reviewer_role="doctor" if review_type == "medical" else "native_reviewer",
                reviewer_id=f"reviewer-{suffix}",
                decision="approved",
                decision_code=f"approved_{review_type}",
                reviewed_at=datetime(2026, 7, 14, tzinfo=UTC),
            )
        )
    return version


def _activate_retrieval_corpus(db: Session, tmp_path) -> None:
    first = _add_approved_source(
        db,
        suffix="A",
        title="成人高血压管理指南",
        passage_text="成人血压持续升高时，应由医生结合规范测量和整体风险进行评估。",
    )
    second = _add_approved_source(
        db,
        suffix="B",
        title="基层高血压健康教育指南",
        passage_text="规律测量血压并记录结果，有助于医生评估高血压管理情况。",
    )
    db.add(
        KbTerm(
            stable_id="KBT-HYPERTENSION",
            preferred_zh="高血压",
            preferred_en="hypertension",
            aliases_json=["血压高", "high blood pressure"],
            concept_type="condition",
            provenance_source_ids_json=["KBS-SYNTHETIC-A", "KBS-SYNTHETIC-B"],
            prohibited_expansions_json=[],
            review_status="approved",
        )
    )
    db.flush()
    store = ImmutableArtifactStore(tmp_path)
    for audience in ("doctor", "patient"):
        release = build_index_release(
            db,
            store,
            [first.id, second.id],
            audience=audience,
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(
            db,
            release,
            audience=audience,
            activated_by="retrieval-test",
        )


def test_catalog_search_uses_keywords_and_metadata_summary(client: TestClient, settings) -> None:
    from pathlib import Path

    from app.knowledge_ingestion import import_catalog_metadata, load_catalog

    with Session(engine) as db:
        seed_database(db, settings)
        import_catalog_metadata(
            db,
            load_catalog(Path("knowledge_base/catalog/authoritative_resources.v1.json")),
        )
        db.commit()
    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    response = client.get(
        "/api/v1/doctor/resources?query=血压高",
        headers=auth_header(doctor["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    item = response.json()["items"][0]
    assert item["title"] == "高血压"
    assert "high blood pressure" in item["search_keywords"]
    assert "尚未存储或概括文章正文" in item["catalog_summary"]


def test_hybrid_retrieval_expands_terms_filters_and_records_no_raw_query(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    response = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={
            "query": "血压高怎么办",
            "filters": {"jurisdictions": ["CN"], "organization_ids": ["KBP-SYNTHETIC-A"]},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence_decision"] == "sufficient"
    assert "高血压" in payload["expanded_terms"]
    assert [item["citation"]["source_id"] for item in payload["items"]] == ["KBS-SYNTHETIC-A"]
    with Session(engine) as db:
        event = db.scalar(select(KbRetrievalEvent))
        assert event is not None
        assert event.query_sha256 == hashlib.sha256("血压高怎么办".encode()).hexdigest()
        assert "血压高怎么办" not in str(event.score_summary_json)


def test_patient_evidence_requires_source_diversity_and_role_boundary(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "血压高怎么办", "language": "zh-Hans", "jurisdiction": "CN"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "sufficient"
    assert len({passage["source_id"] for passage in payload["passages"]}) == 2

    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    denied = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(doctor["access_token"]),
        json={"query": "血压高怎么办"},
    )
    assert denied.status_code == 403


def test_doctor_retrieval_cursor_is_release_and_query_bound(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        db.commit()
    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    first = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={"query": "血压高怎么办", "filters": {"jurisdictions": ["CN"]}, "limit": 1},
    )
    assert first.status_code == 200
    cursor = first.json()["next_cursor"]
    assert cursor
    second = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={
            "query": "血压高怎么办",
            "filters": {"jurisdictions": ["CN"]},
            "limit": 1,
            "cursor": cursor,
        },
    )
    assert second.status_code == 200
    assert (
        second.json()["items"][0]["citation"]["source_id"]
        != first.json()["items"][0]["citation"]["source_id"]
    )

    rejected = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={
            "query": "不同问题",
            "filters": {"jurisdictions": ["CN"]},
            "limit": 1,
            "cursor": cursor,
        },
    )
    assert rejected.status_code == 400


def test_retrieval_fails_closed_without_an_active_approved_release(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        db.commit()
    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    response = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={"query": "高血压指南"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "retrieval_unavailable"
