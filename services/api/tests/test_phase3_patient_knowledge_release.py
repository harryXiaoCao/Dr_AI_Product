from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.patient_knowledge_release as patient_release_module
from app.chatbot_contracts import EvidenceDecision, PatientEvidenceRequest
from app.config import get_settings
from app.database import engine
from app.errors import ApiError
from app.knowledge_retrieval import EMBEDDING_MODEL_VERSION, retrieve
from app.knowledge_translation import (
    import_translation_corpus,
    load_translation_corpus,
    record_translation_review,
)
from app.models import (
    KbActiveIndexRelease,
    KbIndexReleasePassage,
    KbPassage,
    KbReview,
    KbSource,
    KbSourceVersion,
    KbTranslationArtifact,
)
from app.open_content_ingestion import import_open_content_catalog, load_open_content_catalog
from app.patient_knowledge_release import (
    build_and_activate_patient_release,
    build_patient_candidate_release,
    current_patient_version_ids,
    promote_reviewed_translations_for_patient_use,
)

CATALOG_PATH = Path("knowledge_base/catalog/open_patient_education.v1.json")
TRANSLATION_PATH = Path(
    "knowledge_base/translations/open_patient_education.zh-Hans.deepseek-v4-flash.v1.json"
)
REVIEWED_AT = datetime(2026, 7, 16, tzinfo=UTC)


def test_embedding_batches_bound_aggregate_text_without_splitting_a_passage() -> None:
    passages = [SimpleNamespace(text="a" * 400) for _ in range(5)]
    passages.append(SimpleNamespace(text="b" * 1_200))

    batches = list(
        patient_release_module._embedding_batches(
            passages,
            maximum_count=4,
            character_budget=1_000,
        )
    )

    assert [len(batch) for batch in batches] == [2, 2, 1, 1]
    assert [item for batch in batches for item in batch] == passages
    assert all(
        sum(len(item.text) for item in batch) <= 1_000 or len(batch) == 1
        for batch in batches
    )


def _import_translations(db: Session, *, approve: bool) -> None:
    import_open_content_catalog(db, load_open_content_catalog(CATALOG_PATH))
    import_translation_corpus(
        db,
        load_translation_corpus(TRANSLATION_PATH),
        artifact_locator=str(TRANSLATION_PATH),
    )
    if not approve:
        return
    artifacts = list(db.scalars(select(KbTranslationArtifact)))
    for artifact in artifacts:
        for review_type, reviewer_id in (
            ("medical", "medical-reviewer"),
            ("native_chinese", "native-reviewer"),
        ):
            record_translation_review(
                db,
                artifact_stable_id=artifact.stable_id,
                review_type=review_type,
                reviewer_id=reviewer_id,
                approved=True,
                reviewed_at=REVIEWED_AT,
            )


def test_patient_promotion_refuses_unapproved_translations() -> None:
    with Session(engine) as db:
        _import_translations(db, approve=False)
        with pytest.raises(ValueError, match="approved medical and native-Chinese"):
            promote_reviewed_translations_for_patient_use(
                db,
                reviewer_id="product-owner-confirmed-unspecified",
                findings="Approval test.",
                reviewed_at=REVIEWED_AT,
            )


def test_patient_promotion_and_release_are_idempotent_and_retrievable(
    tmp_path, monkeypatch
) -> None:
    with Session(engine) as db:
        _import_translations(db, approve=True)
        source_count = db.scalar(select(func.count()).select_from(KbSource))
        first = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id="product-owner-confirmed-unspecified",
            findings="All 55 entries were manually reviewed and approved for patient use.",
            reviewed_at=REVIEWED_AT,
        )
        second = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id="product-owner-confirmed-unspecified",
            findings="All 55 entries were manually reviewed and approved for patient use.",
            reviewed_at=REVIEWED_AT,
        )
        release = build_and_activate_patient_release(
            db,
            version_ids=first.version_ids,
            artifact_root=tmp_path,
            approver_id="product-owner-confirmed-unspecified",
        )
        db.flush()

        assert source_count == 55
        assert db.scalar(select(func.count()).select_from(KbSource)) == source_count
        assert first.versions_created == 55
        assert first.sections_created == 426
        assert first.passages_created == 426
        assert first.reviews_created == 165
        assert second.versions_created == 0
        assert second.sections_created == 0
        assert second.passages_created == 0
        assert second.reviews_created == 0
        assert release.source_count == 55
        assert release.version_count == 55
        assert release.passage_count == 426
        assert release.status == "active"
        assert db.get(KbActiveIndexRelease, "patient").release_id == release.id
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbPassage)
                .where(KbPassage.language == "zh-Hans", KbPassage.vector_eligible)
            )
            == 426
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbSourceVersion)
                .where(KbSourceVersion.capture_mode == "reviewed_translation")
            )
            == 55
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(KbReview)
                .where(KbReview.decision_code == "product_owner_confirmed_patient_use_approved")
            )
            == 165
        )

        result = retrieve(
            db,
            PatientEvidenceRequest(query="高血压为什么需要定期测量血压？"),
            audience="patient",
        )
        assert result.decision == EvidenceDecision.sufficient
        assert len({candidate.source.stable_id for candidate in result.candidates}) >= 2
        assert all(candidate.passage.language == "zh-Hans" for candidate in result.candidates)
        assert all(candidate.source.jurisdiction == "US" for candidate in result.candidates)

        settings = get_settings()
        monkeypatch.setattr(settings, "knowledge_embedding_model", "embedding-candidate-v2")
        monkeypatch.setattr(settings, "knowledge_reranker_model", "reranker-candidate-v2")
        embedding_calls = 0

        def flaky_embeddings(values, _model):
            nonlocal embedding_calls
            embedding_calls += 1
            if embedding_calls == 1:
                raise ApiError(
                    503,
                    "retrieval_unavailable",
                    "Synthetic transient embedding failure.",
                )
            return [[0.25, 0.75] for _ in values]

        monkeypatch.setattr(patient_release_module, "query_embeddings", flaky_embeddings)
        monkeypatch.setattr(patient_release_module.time, "sleep", lambda _: None)
        candidate = build_patient_candidate_release(
            db,
            version_ids=first.version_ids,
            artifact_root=tmp_path,
            approver_id="candidate-release-test",
        )
        db.flush()
        active = db.get(KbActiveIndexRelease, "patient")
        snapshot = db.scalar(
            select(KbIndexReleasePassage).where(
                KbIndexReleasePassage.release_id == candidate.id
            )
        )
        original_passage = db.scalar(
            select(KbPassage).where(KbPassage.id == snapshot.passage_id)
        )
        assert candidate.status == "built"
        assert embedding_calls >= (candidate.passage_count + 29) // 30 + 1
        assert active.release_id == release.id
        assert snapshot.embedding_json == [0.25, 0.75]
        assert snapshot.embedding_model_version == "embedding-candidate-v2"
        assert original_passage.embedding_model_version == EMBEDDING_MODEL_VERSION


def test_new_candidate_selects_only_latest_patient_version_per_source() -> None:
    with Session(engine) as db:
        _import_translations(db, approve=True)
        promotion = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id="product-owner-confirmed-unspecified",
            findings="All translations reviewed.",
            reviewed_at=REVIEWED_AT,
        )
        original = db.get(KbSourceVersion, promotion.version_ids[0])
        newer = KbSourceVersion(
            stable_id=f"{original.stable_id}-NEWER",
            source_id=original.source_id,
            captured_at=datetime(2026, 7, 20, tzinfo=UTC),
            capture_mode=original.capture_mode,
            raw_checksum="a" * 64,
            normalized_checksum="b" * 64,
            parser_version=original.parser_version,
            valid_from=datetime(2026, 7, 20, tzinfo=UTC),
            review_decision="approved",
        )
        db.add(newer)
        db.flush()

        selected = current_patient_version_ids(
            db, [promotion.version_ids[0], newer.id]
        )

        assert selected == [newer.id]


def test_open_translation_promotion_ignores_other_chinese_artifact_providers() -> None:
    with Session(engine) as db:
        _import_translations(db, approve=True)
        original = db.scalar(select(KbTranslationArtifact))
        assert original is not None
        db.add(
            KbTranslationArtifact(
                stable_id="KBT-UNRELATED-CHINESE-PROVIDER",
                source_id=original.source_id,
                source_version_id=original.source_version_id,
                target_language="zh-Hans",
                translated_title="Unrelated provider artifact",
                provider="opencc",
                model="opencc-test",
                prompt_policy_version="unrelated-policy",
                source_checksum="a" * 64,
                translation_checksum="b" * 64,
                artifact_locator="test://unrelated",
                status="approved",
                medical_review_status="approved",
                native_language_review_status="approved",
                generated_at=REVIEWED_AT,
                approved_at=REVIEWED_AT,
            )
        )
        db.flush()
        promotion = promote_reviewed_translations_for_patient_use(
            db,
            reviewer_id="corpus-boundary-test",
            findings="The unrelated provider artifact must not enter this corpus.",
            reviewed_at=REVIEWED_AT,
        )
        assert len(promotion.version_ids) == 55
