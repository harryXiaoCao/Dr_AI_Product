import hashlib
import json
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot_contracts import EvidenceDecision, PatientEvidenceRequest
from app.config import get_settings
from app.database import engine
from app.knowledge_freshness import set_source_family_kill_switch
from app.knowledge_ingestion import (
    ImmutableArtifactStore,
    activate_index_release,
    build_index_release,
)
from app.knowledge_retrieval import (
    EMBEDDING_MODEL_VERSION,
    LEXICAL_ANALYZER_VERSION,
    RERANKER_VERSION,
    _active_rows,
    _central_query_requirements,
    _cross_encoder_rerank,
    _rank_candidates,
    embed_text,
    retrieve,
)
from app.knowledge_rights import provider_transmission_allowed
from app.models import (
    KbIndexReleasePassage,
    KbPassage,
    KbPublisher,
    KbRetrievalEvent,
    KbReview,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceFamily,
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
    jurisdiction: str = "CN",
    clinical_tags: list[str] | None = None,
    search_keywords: list[str] | None = None,
) -> KbSourceVersion:
    publisher = KbPublisher(
        stable_id=f"KBP-SYNTHETIC-{suffix}",
        official_name_zh=f"合成测试卫生机构{suffix}",
        organization_type="national_health_authority",
        authority_basis="Synthetic authority metadata used only in retrieval tests.",
        authority_evidence_locator=f"https://example.invalid/publisher/{suffix}",
        verified_domains_json=["example.invalid"],
        jurisdiction=jurisdiction,
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
        model_provider_transmission_allowed=True,
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
        jurisdiction=jurisdiction,
        intended_audiences_json=["doctor", "patient"],
        topic="chronic_disease",
        original_language="zh-Hans",
        official_translations_json=[],
        catalog_summary=f"关于{title}的合成测试目录摘要。",
        search_keywords_json=(
            search_keywords
            if search_keywords is not None
            else ["高血压", "血压高", "high blood pressure"]
        ),
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
            clinical_concept_tags_json=(
                clinical_tags
                if clinical_tags is not None
                else ["高血压", "血压管理", "血压记录", "血压测量"]
            ),
            audience_json=["doctor", "patient"],
            chunking_version="clinical-structure-v1",
            patient_readability_review_status="approved",
            lexical_eligible=True,
            vector_eligible=True,
            embedding_json=embed_text(passage_text),
            embedding_model_version=EMBEDDING_MODEL_VERSION,
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


def test_colloquial_interrogative_recording_maps_to_measurement_intent() -> None:
    requirements = dict(_central_query_requirements("读数偏高该咋保存着记才好？"))

    assert "measurement_tracking" in requirements


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


def test_active_rows_use_only_compatible_release_membership_embeddings(tmp_path) -> None:
    with Session(engine) as db:
        version = _add_approved_source(
            db,
            suffix="RELEASE-EMBEDDING",
            title="不可变发布嵌入测试",
            passage_text="血压测量结果需要结合规范测量方法进行解释。",
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [version.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        snapshot = db.scalar(
            select(KbIndexReleasePassage).where(KbIndexReleasePassage.release_id == release.id)
        )
        passage = db.get(KbPassage, snapshot.passage_id)
        release_embedding = [0.125] * len(passage.embedding_json)
        snapshot.embedding_json = release_embedding
        snapshot.embedding_model_version = EMBEDDING_MODEL_VERSION
        passage.embedding_json = [0.875] * len(release_embedding)
        passage.embedding_model_version = "superseded-passage-model"
        db.flush()

        _, rows = _active_rows(db, "patient")

        assert len(rows) == 1
        assert rows[0][4] == release_embedding

        snapshot.embedding_model_version = "incompatible-release-model"
        db.flush()
        _, incompatible_rows = _active_rows(db, "patient")

        assert incompatible_rows == []


def test_patient_release_refuses_missing_provider_transmission_rights(tmp_path) -> None:
    with Session(engine) as db:
        version = _add_approved_source(
            db,
            suffix="NO-TRANSMISSION",
            title="患者教育资料",
            passage_text="这是一段仅用于权限测试的患者教育资料。",
        )
        source = db.get(KbSource, version.source_id)
        rights = db.get(KbRightsRecord, source.rights_record_id)
        rights.model_provider_transmission_allowed = False
        db.flush()

        with pytest.raises(ValueError, match="not eligible for patient release"):
            build_index_release(
                db,
                ImmutableArtifactStore(tmp_path),
                [version.id],
                audience="patient",
                embedding_model_version=EMBEDDING_MODEL_VERSION,
                lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
                reranker_version=RERANKER_VERSION,
                approver_ids=["retrieval-reviewer"],
            )


def test_provider_transmission_rights_reject_expiry_future_effect_and_mismatch() -> None:
    now = datetime(2026, 7, 18, tzinfo=UTC)
    with Session(engine) as db:
        version = _add_approved_source(
            db,
            suffix="RIGHTS-LIFECYCLE",
            title="权限生命周期测试资料",
            passage_text="这是一段仅用于权限生命周期测试的患者教育资料。",
        )
        source = db.get(KbSource, version.source_id)
        rights = db.get(KbRightsRecord, source.rights_record_id)
        assert provider_transmission_allowed(rights, source, now=now)

        rights.expires_at = now
        assert not provider_transmission_allowed(rights, source, now=now)
        rights.expires_at = None
        rights.effective_at = now + timedelta(seconds=1)
        assert not provider_transmission_allowed(rights, source, now=now)
        rights.effective_at = None
        rights.source_id = uuid.uuid4()
        assert not provider_transmission_allowed(rights, source, now=now)
        rights.source_id = None
        rights.decision_status = "revoked"
        assert not provider_transmission_allowed(rights, source, now=now)


def test_cross_encoder_reranker_uses_declared_service_response(monkeypatch) -> None:
    with Session(engine) as db:
        version = _add_approved_source(
            db,
            suffix="CROSS-ENCODER",
            title="高血压记录",
            passage_text="规律记录血压有助于医生了解一段时间内的变化。",
        )
        passage = db.scalar(select(KbPassage).where(KbPassage.version_id == version.id))
        source = db.get(KbSource, version.source_id)
        publisher = db.get(KbPublisher, source.publisher_id)
        candidates = _rank_candidates(
            [(passage, version, source, publisher)],
            "怎样记录高血压",
            [],
            prefer_china=True,
            query_vector=embed_text("怎样记录高血压"),
            require_lexical_anchor=True,
        )
        settings = get_settings()
        monkeypatch.setattr(settings, "knowledge_reranker_backend", "http_service")
        monkeypatch.setattr(
            settings, "knowledge_reranker_service_url", "https://reranker.example.invalid"
        )
        monkeypatch.setattr(settings, "knowledge_reranker_model", "reranker-test-v1")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return b'{"results":[{"id":"KBPASS-SYNTHETIC-CROSS-ENCODER","score":0.93}]}'

        monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())

        reranked, backend, fallback = _cross_encoder_rerank(db, "怎样记录高血压", candidates)

        assert backend == "cross_encoder"
        assert fallback is None
        assert reranked[0].rerank_score == pytest.approx(1.18)


def test_cross_encoder_skips_service_when_no_candidates(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "knowledge_reranker_backend", "http_service")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: pytest.fail("empty candidate set reached reranker service"),
    )

    with Session(engine) as db:
        reranked, backend, fallback = _cross_encoder_rerank(db, "阑尾炎", [])

    assert reranked == []
    assert backend == "not_applicable"
    assert fallback is None


def test_cross_encoder_budget_selects_distinct_sources(monkeypatch) -> None:
    with Session(engine) as db:
        versions = [
            _add_approved_source(
                db,
                suffix=suffix,
                title=f"高血压记录资料{suffix}",
                passage_text=f"来源{suffix}说明如何测量并记录血压。",
            )
            for suffix in ("DIVERSE-A", "DIVERSE-B", "DIVERSE-C")
        ]
        rows = []
        for version in versions:
            passage = db.scalar(select(KbPassage).where(KbPassage.version_id == version.id))
            source = db.get(KbSource, version.source_id)
            publisher = db.get(KbPublisher, source.publisher_id)
            rows.append((passage, version, source, publisher))
        candidates = _rank_candidates(
            rows,
            "怎样记录血压",
            [],
            prefer_china=True,
            query_vector=embed_text("怎样记录血压"),
            require_lexical_anchor=True,
        )
        candidates.insert(1, candidates[0])
        settings = get_settings()
        monkeypatch.setattr(settings, "knowledge_reranker_backend", "http_service")
        monkeypatch.setattr(settings, "knowledge_reranker_max_candidates", 3)
        monkeypatch.setattr(
            settings, "knowledge_reranker_service_url", "https://reranker.example.invalid"
        )
        monkeypatch.setattr(settings, "knowledge_reranker_model", "reranker-test-v1")
        requested_source_ids: list[str] = []

        class FakeResponse:
            def __init__(self, request) -> None:
                payload = json.loads(request.data)
                passage_ids = [item["id"] for item in payload["documents"]]
                requested_source_ids.extend(
                    next(
                        candidate.source.stable_id
                        for candidate in candidates
                        if candidate.passage.stable_id == passage_id
                    )
                    for passage_id in passage_ids
                )
                self.body = json.dumps(
                    {
                        "results": [
                            {"id": passage_id, "score": 1.0 - index / 10}
                            for index, passage_id in enumerate(passage_ids)
                        ]
                    }
                ).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return self.body

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda request, **kwargs: FakeResponse(request)
        )

        _cross_encoder_rerank(db, "怎样记录血压", candidates)

        assert len(requested_source_ids) == 3
        assert len(set(requested_source_ids)) == 3


def test_cross_encoder_respects_smaller_purpose_specific_budget(monkeypatch) -> None:
    with Session(engine) as db:
        versions = [
            _add_approved_source(
                db,
                suffix=f"PURPOSE-{index}",
                title=f"血压记录来源{index}",
                passage_text=f"来源{index}说明如何测量并记录血压。",
            )
            for index in range(3)
        ]
        rows = []
        for version in versions:
            passage = db.scalar(select(KbPassage).where(KbPassage.version_id == version.id))
            source = db.get(KbSource, version.source_id)
            publisher = db.get(KbPublisher, source.publisher_id)
            rows.append((passage, version, source, publisher))
        candidates = _rank_candidates(
            rows,
            "怎样记录血压",
            [],
            prefer_china=True,
            query_vector=embed_text("怎样记录血压"),
            require_lexical_anchor=True,
        )
        settings = get_settings()
        monkeypatch.setattr(settings, "knowledge_reranker_backend", "http_service")
        monkeypatch.setattr(settings, "knowledge_reranker_max_candidates", 4)
        monkeypatch.setattr(
            settings, "knowledge_reranker_service_url", "https://reranker.example.invalid"
        )
        requested_ids: list[str] = []

        class FakeResponse:
            def __init__(self, request) -> None:
                payload = json.loads(request.data)
                requested_ids.extend(item["id"] for item in payload["documents"])
                self.body = json.dumps(
                    {"results": [{"id": passage_id, "score": 1.0} for passage_id in requested_ids]}
                ).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return self.body

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda request, **kwargs: FakeResponse(request)
        )

        reranked, backend, fallback = _cross_encoder_rerank(
            db,
            "怎样记录血压",
            candidates,
            candidate_limit_override=2,
        )

        assert backend == "cross_encoder"
        assert fallback is None
        assert len(requested_ids) == 2
        assert len(reranked) == 3


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


def test_patient_multiview_retrieval_recovers_symptom_only_colloquial_query(
    settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        abdominal_pain = _add_approved_source(
            db,
            suffix="ABDOMINAL-PAIN",
            title="腹痛的就医评估",
            passage_text=(
                "腹部疼痛需要结合疼痛位置、开始时间、变化过程和伴随表现进行评估。"
                "疼痛转移或逐渐加重时，应尽快由医务人员检查。"
            ),
            clinical_tags=["腹痛", "腹部疼痛", "疼痛转移"],
            search_keywords=["腹痛", "腹部疼痛", "疼痛位置"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [abdominal_pain.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.flush()

        result = retrieve(
            db,
            PatientEvidenceRequest(
                query="肚脐周围疼了一天，后来挪到右下边，需要去看吗？",
                language="zh-Hans",
                jurisdiction="CN",
            ),
            audience="patient",
        )

    assert result.literal_candidate_count == 0
    assert result.decision == EvidenceDecision.sufficient
    assert {candidate.source.stable_id for candidate in result.candidates} == {
        "KBS-SYNTHETIC-ABDOMINAL-PAIN"
    }
    assert result.view_kinds[:2] == ("literal", "clinical_presentation")


def test_patient_multiview_retrieval_uses_reported_exposure_without_inventing_diagnosis(
    settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        heat_guidance = _add_approved_source(
            db,
            suffix="HEAT-INJURY",
            title="中暑与热伤害的识别",
            passage_text=(
                "热伤害可出现头痛、恶心和全身无力。应离开高温环境并观察意识、"
                "呼吸和体温等危险表现，症状加重时及时就医。"
            ),
            clinical_tags=["中暑", "热伤害", "高温暴露"],
            search_keywords=["中暑", "热伤害", "高温环境"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [heat_guidance.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.flush()

        result = retrieve(
            db,
            PatientEvidenceRequest(
                query="大热天地里干完活，头疼恶心，浑身发软。",
                language="zh-Hans",
                jurisdiction="CN",
            ),
            audience="patient",
        )

    assert result.literal_candidate_count == 0
    assert result.decision == EvidenceDecision.sufficient
    assert {candidate.source.stable_id for candidate in result.candidates} == {
        "KBS-SYNTHETIC-HEAT-INJURY"
    }


def test_patient_multiview_requires_reported_exposure_to_be_central(settings, tmp_path) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        pallor = _add_approved_source(
            db,
            suffix="PALLOR-NOT-INSULIN",
            title="脸色苍白与贫血评估",
            passage_text="脸色苍白可能有多种原因，需要由医务人员结合症状和检查判断。",
            clinical_tags=["脸色苍白", "贫血"],
            search_keywords=["脸色苍白", "贫血"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [pallor.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.flush()

        result = retrieve(
            db,
            PatientEvidenceRequest(
                query="打完胰岛素后冒冷汗、手抖、心慌。",
                language="zh-Hans",
                jurisdiction="CN",
            ),
            audience="patient",
        )

    assert result.decision == EvidenceDecision.no_eligible_evidence
    assert result.candidates == []


def test_patient_multiview_requires_every_reported_clinical_context(settings, tmp_path) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        complete = _add_approved_source(
            db,
            suffix="PREGNANT-ABDOMINAL-TRAUMA",
            title="孕妇腹部受撞击后的评估",
            passage_text="怀孕期间腹部受撞击后出现腹痛，应尽快由医务人员评估。",
            clinical_tags=["孕妇", "腹部受撞击", "腹痛"],
            search_keywords=["怀孕", "腹部受撞击", "腹痛"],
        )
        partial = _add_approved_source(
            db,
            suffix="ABDOMINAL-TRAUMA-ONLY",
            title="腹部受撞击后的评估",
            passage_text="腹部受撞击后出现腹痛，需要结合受伤经过进行评估。",
            clinical_tags=["腹部受撞击", "腹痛"],
            search_keywords=["腹部受撞击", "腹痛"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [complete.id, partial.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.flush()

        result = retrieve(
            db,
            PatientEvidenceRequest(
                query="我怀孕了，肚子被撞后腹痛。",
                language="zh-Hans",
                jurisdiction="CN",
            ),
            audience="patient",
        )

    assert result.decision == EvidenceDecision.sufficient
    assert {candidate.source.stable_id for candidate in result.candidates} == {
        "KBS-SYNTHETIC-PREGNANT-ABDOMINAL-TRAUMA"
    }


def test_patient_retrieval_rejects_authoritative_but_topically_unrelated_sources(
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
        json={
            "query": "嚼槟榔不咽槟榔汁是不是就没事",
            "language": "zh-Hans",
            "jurisdiction": "CN",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "no_eligible_evidence"
    assert response.json()["passages"] == []


def test_patient_retrieval_requires_unknown_named_entity_to_exist_in_evidence(
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
        json={
            "query": "一种不存在的药物 Zeta-999 能治疗所有癌症吗？",
            "language": "zh-Hans",
            "jurisdiction": "CN",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "no_eligible_evidence"
    assert response.json()["passages"] == []


def test_patient_retrieval_requires_symptom_to_be_central_not_generic_heart_content(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        generic = _add_approved_source(
            db,
            suffix="GENERIC-HEART",
            title="心脏健康教育",
            passage_text="心脏病包括多种情况，个别人也会提到心慌或漏跳。",
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [generic.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "最近心慌像漏跳一样，可能和什么有关？", "language": "zh-Hans"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "no_eligible_evidence"


def test_patient_retrieval_applies_presentation_centrality_to_literal_hits(
    settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        cough = _add_approved_source(
            db,
            suffix="NIGHT-COUGH",
            title="夜间咳嗽的就医评估",
            passage_text=(
                "夜间或躺下后咳嗽加重时，应记录持续时间和伴随表现，并由医务人员结合情况评估。"
            ),
            clinical_tags=["咳嗽", "夜间咳嗽"],
            search_keywords=["咳嗽", "夜间咳嗽", "躺下后咳嗽"],
        )
        incidental = _add_approved_source(
            db,
            suffix="NIGHT-SLEEP",
            title="夜间躺下后的睡眠习惯",
            passage_text="晚上躺下后保持安静，有助于形成规律的睡眠习惯。",
            clinical_tags=["睡眠", "睡眠习惯"],
            search_keywords=["晚上", "躺下", "睡眠"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [cough.id, incidental.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.flush()

        result = retrieve(
            db,
            PatientEvidenceRequest(
                query="晚上躺下后咳嗽很厉害。",
                language="zh-Hans",
                jurisdiction="CN",
            ),
            audience="patient",
        )

    assert result.literal_candidate_count >= 1
    assert result.decision == EvidenceDecision.sufficient
    assert {candidate.source.stable_id for candidate in result.candidates} == {
        "KBS-SYNTHETIC-NIGHT-COUGH"
    }


def test_patient_retrieval_requires_mechanism_evidence_for_medication_mechanism_query(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        broad = _add_approved_source(
            db,
            suffix="BROAD-MEDICATION",
            title="血压稳定后可以暂停降压药吗",
            passage_text="不要自行停用降压药，应与医生讨论血压记录和当前处方。",
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [broad.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "降压药通常是怎样帮助控制血压的？", "language": "zh-Hans"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "no_eligible_evidence"


def test_medication_query_requires_the_same_central_clinical_topic(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        blood_pressure = _add_approved_source(
            db,
            suffix="BP-MECHANISM",
            title="降压药如何帮助控制血压",
            passage_text="这类药物通过影响血管阻力等机制帮助控制血压。",
        )
        blood_lipids = _add_approved_source(
            db,
            suffix="LIPID-MECHANISM",
            title="降血脂药物如何帮助控制血脂",
            passage_text="这类药物通过影响胆固醇代谢机制帮助控制血脂。",
            clinical_tags=["血脂", "胆固醇"],
            search_keywords=["血脂", "胆固醇", "cholesterol"],
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [blood_pressure.id, blood_lipids.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "降压药通常怎样帮助控制血压？", "language": "zh-Hans"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "sufficient"
    assert {item["source_id"] for item in response.json()["passages"]} == {
        "KBS-SYNTHETIC-BP-MECHANISM"
    }


def test_stale_decision_requires_a_release_scoped_historical_match(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        current = _add_approved_source(
            db,
            suffix="CURRENT-SCREENING",
            title="当前筛查建议",
            passage_text="当前筛查建议应根据年龄、风险和适用地区由医生确认。",
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [current.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
            historical_markers=[
                {
                    "source_id": "KBS-SYNTHETIC-HISTORICAL-SCREENING",
                    "version_id": "KBV-SYNTHETIC-HISTORICAL-SCREENING",
                    "language": "zh-Hans",
                    "search_text": "已经撤回的旧版筛查时间表",
                    "content_checksum": "a" * 64,
                }
            ],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "已撤回的旧版筛查时间表是什么？", "language": "zh-Hans"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "stale_or_superseded_only"
    assert response.json()["passages"] == []


def test_explicit_cross_jurisdiction_conflict_fails_closed(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        cn = _add_approved_source(
            db,
            suffix="CONFLICT-CN",
            title="中国筛查建议",
            passage_text="中国筛查建议应结合适用人群和当前风险。",
            jurisdiction="CN",
        )
        tw = _add_approved_source(
            db,
            suffix="CONFLICT-TW",
            title="台湾筛查建议",
            passage_text="台湾筛查项目按当地适用人群和时间安排执行。",
            jurisdiction="TW",
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [cn.id, tw.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(db, release, audience="patient", activated_by="test")
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={"query": "不同地区筛查建议不一致时应该看哪一个？", "language": "zh-Hans"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "conflicting"
    assert response.json()["passages"] == []


def test_patient_retrieval_maps_colloquial_symptom_to_matching_clinical_concept(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        rhythm = _add_approved_source(
            db,
            suffix="RHYTHM",
            title="心悸和心律失常的就医评估",
            passage_text=(
                "心悸可被感觉为心跳过快、不规律或像漏跳一拍。"
                "医生会结合发作时间、伴随症状和检查进行评估。"
            ),
        )
        unrelated = _add_approved_source(
            db,
            suffix="SLEEP",
            title="睡眠健康教育",
            passage_text=(
                "保持规律作息和足够睡眠有助于日常健康管理。"
                "一些人也可能偶然提到心悸，但这不是本文的主题。"
            ),
        )
        db.flush()
        release = build_index_release(
            db,
            ImmutableArtifactStore(tmp_path),
            [rhythm.id, unrelated.id],
            audience="patient",
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
            reranker_version=RERANKER_VERSION,
            approver_ids=["retrieval-reviewer"],
        )
        activate_index_release(
            db,
            release,
            audience="patient",
            activated_by="retrieval-test",
        )
        db.commit()
    patient = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )

    response = client.post(
        "/api/v1/retrieval/patient/evidence",
        headers=auth_header(patient["access_token"]),
        json={
            "query": "熬夜多了心脏像跳空了一下，这是怎么回事？",
            "language": "zh-Hans",
            "jurisdiction": "CN",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "sufficient"
    assert {item["source_id"] for item in payload["passages"]} == {"KBS-SYNTHETIC-RHYTHM"}


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


def test_source_family_kill_switch_removes_released_evidence_at_runtime(
    client: TestClient, settings, tmp_path
) -> None:
    with Session(engine) as db:
        seed_database(db, settings)
        _activate_retrieval_corpus(db, tmp_path)
        source = db.scalar(select(KbSource).where(KbSource.stable_id == "KBS-SYNTHETIC-A"))
        assert source is not None
        family = KbSourceFamily(
            stable_id="KBF-SYNTHETIC-A",
            publisher_id=source.publisher_id,
            name="Synthetic source family A",
            jurisdiction="CN",
            seed_locators_json=["https://example.invalid/source/A"],
            allowed_domains_json=["example.invalid"],
            allowed_path_prefixes_json=["/source/"],
            content_classes_json=["guideline"],
            parser_version="synthetic-v1",
            fetch_interval_minutes=60,
            max_response_bytes=100_000,
            capture_policy="full_text",
            rights_gate_status="approved",
            status="active",
        )
        db.add(family)
        db.flush()
        source.source_family_id = family.id
        set_source_family_kill_switch(
            db,
            stable_id=family.stable_id,
            killed=True,
            actor_id="retrieval-safety-test",
            reason_code="source_family_incident",
        )
        db.commit()

    doctor = login(
        client, "doctor.demo@example.com", settings.seed_doctor_password.get_secret_value()
    )
    response = client.post(
        "/api/v1/retrieval/doctor/resources/search",
        headers=auth_header(doctor["access_token"]),
        json={
            "query": "血压高怎么办",
            "filters": {"organization_ids": ["KBP-SYNTHETIC-A"]},
        },
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["evidence_decision"] == "no_eligible_evidence"
