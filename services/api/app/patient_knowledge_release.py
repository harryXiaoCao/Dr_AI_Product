from __future__ import annotations

import hashlib
import logging
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ApiError
from app.hpa_health_myths_ingestion import (
    EXPECTED_ROW_COUNT as EXPECTED_HPA_ROW_COUNT,
)
from app.hpa_health_myths_ingestion import (
    HPA_PUBLISHER_ID,
)
from app.knowledge_ingestion import (
    ImmutableArtifactStore,
    activate_index_release,
    build_index_release,
)
from app.knowledge_retrieval import (
    EMBEDDING_MODEL_VERSION,
    LEXICAL_ANALYZER_VERSION,
    embed_text,
    query_embeddings,
)
from app.knowledge_rights import assert_passages_provider_transmittable
from app.knowledge_translation import (
    EXPECTED_OPEN_DOCUMENT_COUNT,
    TRANSLATION_PROMPT_POLICY_VERSION,
)
from app.models import (
    KbActiveIndexRelease,
    KbIndexReleasePassage,
    KbPassage,
    KbPublisher,
    KbReview,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
    KbTranslationArtifact,
    KbTranslationSection,
)

PATIENT_VERSION_PARSER = "reviewed-translation-patient-v1"
PATIENT_CHUNKING_VERSION = "reviewed-translation-section-v1"
PATIENT_REVIEW_DECISION_CODE = "product_owner_confirmed_patient_use_approved"
HPA_PATIENT_REVIEW_DECISION_CODE = "product_owner_confirmed_hpa_patient_use_approved"
HPA_PATIENT_VERSION_PARSER = "reviewed-hpa-script-conversion-patient-v1"
HPA_PATIENT_CHUNKING_VERSION = "reviewed-hpa-question-answer-v1"
HPA_PROVIDER_PERMISSION_REFERENCE = (
    "OGDL-Taiwan-1.0 permits reuse, transformation, redistribution, and commercial use "
    "with attribution for the released dataset text. Following confirmed human review, "
    "the Simplified-Chinese text may be embedded and transmitted as public grounded "
    "evidence to the configured model provider. Excluded third-party media remain denied."
)
HPA_APPROVED_CATALOG_SUMMARY = (
    "台湾卫生福利部国民健康署官方保健辟谣问答的简体中文适配。"
    "已完成医疗内容、原生简体中文、患者可读性及中国大陆适用性人工审核；"
    "台湾特定政策、项目、联系方式及法律要求仍保留原司法管辖区标识。"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PatientCorpusPromotion:
    version_ids: list[uuid.UUID]
    versions_created: int
    sections_created: int
    passages_created: int
    reviews_created: int


def _embedding_batches(
    passages: list[KbPassage],
    *,
    maximum_count: int,
    character_budget: int,
) -> Iterator[list[KbPassage]]:
    """Bound requests by both document count and a tokenizer-independent size proxy."""

    batch: list[KbPassage] = []
    batch_characters = 0
    for passage in passages:
        passage_characters = len(passage.text)
        if batch and (
            len(batch) >= maximum_count
            or batch_characters + passage_characters > character_budget
        ):
            yield batch
            batch = []
            batch_characters = 0
        batch.append(passage)
        batch_characters += passage_characters
    if batch:
        yield batch


def _stable_review_id(target_stable_id: str, review_type: str) -> str:
    digest = hashlib.sha256(f"{target_stable_id}:{review_type}".encode()).hexdigest()
    return f"KBRV-PATIENT-{digest[:24].upper()}"


def _add_review_if_missing(
    db: Session,
    *,
    target_stable_id: str,
    review_type: str,
    reviewer_id: str,
    findings: str,
    reviewed_at: datetime,
    decision_code: str = PATIENT_REVIEW_DECISION_CODE,
) -> bool:
    stable_id = _stable_review_id(target_stable_id, review_type)
    if db.scalar(select(KbReview).where(KbReview.stable_id == stable_id)) is not None:
        return False
    db.add(
        KbReview(
            stable_id=stable_id,
            target_type="source_version",
            target_stable_id=target_stable_id,
            review_type=review_type,
            reviewer_role="product_owner_confirmation",
            reviewer_id=reviewer_id,
            decision="approved",
            decision_code=decision_code,
            findings=findings,
            reviewed_at=reviewed_at,
        )
    )
    return True


def promote_reviewed_translations_for_patient_use(
    db: Session,
    *,
    reviewer_id: str,
    findings: str,
    reviewed_at: datetime | None = None,
) -> PatientCorpusPromotion:
    """Materialize approved translations as independently versioned patient passages."""

    timestamp = reviewed_at or datetime.now(UTC)
    artifacts = list(
        db.scalars(
            select(KbTranslationArtifact)
            .where(
                KbTranslationArtifact.target_language == "zh-Hans",
                KbTranslationArtifact.provider == "deepseek",
                KbTranslationArtifact.model == "deepseek-v4-flash",
                KbTranslationArtifact.prompt_policy_version
                == TRANSLATION_PROMPT_POLICY_VERSION,
            )
            .order_by(KbTranslationArtifact.stable_id)
        )
    )
    if len(artifacts) != EXPECTED_OPEN_DOCUMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_OPEN_DOCUMENT_COUNT} Chinese translation artifacts; "
            f"found {len(artifacts)}."
        )
    if any(
        artifact.status != "approved"
        or artifact.medical_review_status != "approved"
        or artifact.native_language_review_status != "approved"
        for artifact in artifacts
    ):
        raise ValueError("Every translation needs approved medical and native-Chinese reviews.")

    source_count_before = db.scalar(select(func.count()).select_from(KbSource)) or 0
    version_ids: list[uuid.UUID] = []
    versions_created = sections_created = passages_created = reviews_created = 0
    for artifact in artifacts:
        source = db.get(KbSource, artifact.source_id)
        original_version = db.get(KbSourceVersion, artifact.source_version_id)
        if source is None or original_version is None:
            raise ValueError(f"Translation lineage is missing for {artifact.stable_id}.")
        version_stable_id = artifact.stable_id.replace("KBT-", "KBV-PATIENT-", 1)
        version = db.scalar(
            select(KbSourceVersion).where(KbSourceVersion.stable_id == version_stable_id)
        )
        if version is None:
            version = KbSourceVersion(
                stable_id=version_stable_id,
                source_id=source.id,
                publisher_version_label="Reviewed Simplified-Chinese patient translation",
                captured_at=artifact.generated_at,
                capture_mode="reviewed_translation",
                raw_checksum=artifact.translation_checksum,
                normalized_checksum=artifact.translation_checksum,
                normalized_artifact_locator=artifact.artifact_locator,
                parser_version=PATIENT_VERSION_PARSER,
                valid_from=artifact.approved_at or timestamp,
                supersedes_version_id=original_version.id,
                change_summary=(
                    "Patient-use-approved Simplified-Chinese translation derived from "
                    f"{original_version.stable_id}."
                ),
                review_decision="approved",
            )
            db.add(version)
            db.flush()
            versions_created += 1

            translated_sections = list(
                db.scalars(
                    select(KbTranslationSection)
                    .where(KbTranslationSection.artifact_id == artifact.id)
                    .order_by(KbTranslationSection.ordinal)
                )
            )
            if not translated_sections:
                raise ValueError(f"Translation sections are missing for {artifact.stable_id}.")
            for translated in translated_sections:
                suffix = f"{artifact.translation_checksum[:10].upper()}-{translated.ordinal:03d}"
                section = KbSection(
                    stable_id=f"KBC-PATIENT-{source.stable_id.removeprefix('KBS-')}-{suffix}",
                    version_id=version.id,
                    heading_path_json=[translated.translated_heading],
                    ordinal=translated.ordinal,
                    language="zh-Hans",
                )
                db.add(section)
                db.flush()
                sections_created += 1
                text = translated.translated_text
                db.add(
                    KbPassage(
                        stable_id=(
                            f"KBPASS-PATIENT-{source.stable_id.removeprefix('KBS-')}-{suffix}"
                        ),
                        section_id=section.id,
                        version_id=version.id,
                        ordinal=0,
                        text=text,
                        language="zh-Hans",
                        character_count=len(text),
                        clinical_concept_tags_json=[],
                        audience_json=["patient"],
                        chunking_version=PATIENT_CHUNKING_VERSION,
                        patient_readability_review_status="approved",
                        lexical_eligible=True,
                        vector_eligible=True,
                        embedding_json=embed_text(text),
                        embedding_model_version=EMBEDDING_MODEL_VERSION,
                        content_checksum=hashlib.sha256(text.encode()).hexdigest(),
                    )
                )
                passages_created += 1
        elif (
            version.source_id != source.id
            or version.normalized_checksum != artifact.translation_checksum
            or version.review_decision != "approved"
        ):
            raise ValueError(f"Existing patient version drifted for {artifact.stable_id}.")

        source.lifecycle_state = "patient_approved"
        source.medical_review_status = "approved"
        source.native_language_review_status = "approved"
        source.doctor_eligible = True
        source.patient_eligible = True
        for review_type in ("medical", "native_language", "patient_readability"):
            reviews_created += int(
                _add_review_if_missing(
                    db,
                    target_stable_id=version.stable_id,
                    review_type=review_type,
                    reviewer_id=reviewer_id,
                    findings=findings,
                    reviewed_at=timestamp,
                )
            )
        version_ids.append(version.id)

    db.flush()
    source_count_after = db.scalar(select(func.count()).select_from(KbSource)) or 0
    if source_count_after != source_count_before:
        raise RuntimeError("Patient promotion changed the governed source count.")
    return PatientCorpusPromotion(
        version_ids=version_ids,
        versions_created=versions_created,
        sections_created=sections_created,
        passages_created=passages_created,
        reviews_created=reviews_created,
    )


def promote_reviewed_hpa_for_patient_use(
    db: Session,
    *,
    reviewer_id: str,
    findings: str,
    reviewed_at: datetime | None = None,
) -> PatientCorpusPromotion:
    """Promote all confirmed HPA script conversions without losing version lineage."""

    timestamp = reviewed_at or datetime.now(UTC)
    publisher = db.scalar(select(KbPublisher).where(KbPublisher.stable_id == HPA_PUBLISHER_ID))
    if publisher is None:
        raise ValueError("The HPA publisher has not been imported.")
    artifacts = list(
        db.scalars(
            select(KbTranslationArtifact)
            .join(KbSource, KbSource.id == KbTranslationArtifact.source_id)
            .where(
                KbSource.publisher_id == publisher.id,
                KbTranslationArtifact.target_language == "zh-Hans",
                KbTranslationArtifact.provider == "opencc",
                KbTranslationArtifact.prompt_policy_version
                == "deterministic-zh-hant-to-zh-hans-v1",
            )
            .order_by(KbTranslationArtifact.stable_id)
        )
    )
    if len(artifacts) != EXPECTED_HPA_ROW_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_HPA_ROW_COUNT} HPA artifacts; found {len(artifacts)}."
        )

    source_count_before = db.scalar(select(func.count()).select_from(KbSource)) or 0
    version_ids: list[uuid.UUID] = []
    versions_created = sections_created = passages_created = reviews_created = 0
    for artifact in artifacts:
        source = db.get(KbSource, artifact.source_id)
        original_version = db.get(KbSourceVersion, artifact.source_version_id)
        if source is None or original_version is None:
            raise ValueError(f"HPA conversion lineage is missing for {artifact.stable_id}.")
        rights = db.get(KbRightsRecord, source.rights_record_id)
        if rights is None or rights.decision_status != "approved":
            raise ValueError(f"HPA rights approval is missing for {artifact.stable_id}.")
        rights.embedding_allowed = True
        rights.model_provider_transmission_allowed = True
        rights.permission_reference = HPA_PROVIDER_PERMISSION_REFERENCE

        artifact.status = "approved"
        artifact.medical_review_status = "approved"
        artifact.native_language_review_status = "approved"
        artifact.approved_at = artifact.approved_at or timestamp

        version_stable_id = artifact.stable_id.replace("KBT-", "KBV-PATIENT-", 1)
        version = db.scalar(
            select(KbSourceVersion).where(KbSourceVersion.stable_id == version_stable_id)
        )
        if version is None:
            version = KbSourceVersion(
                stable_id=version_stable_id,
                source_id=source.id,
                publisher_version_label="Human-reviewed Simplified-Chinese HPA Q&A",
                captured_at=artifact.generated_at,
                capture_mode="reviewed_script_conversion",
                raw_checksum=hashlib.sha256(
                    f"{artifact.stable_id}:{artifact.translation_checksum}".encode()
                ).hexdigest(),
                normalized_checksum=artifact.translation_checksum,
                normalized_artifact_locator=artifact.artifact_locator,
                parser_version=HPA_PATIENT_VERSION_PARSER,
                valid_from=original_version.valid_from,
                supersedes_version_id=original_version.id,
                change_summary=(
                    "Human-reviewed patient-use Simplified-Chinese script conversion derived "
                    f"from {original_version.stable_id}."
                ),
                review_decision="approved",
            )
            db.add(version)
            db.flush()
            versions_created += 1

            translated_sections = list(
                db.scalars(
                    select(KbTranslationSection)
                    .where(KbTranslationSection.artifact_id == artifact.id)
                    .order_by(KbTranslationSection.ordinal)
                )
            )
            if not translated_sections:
                raise ValueError(f"HPA sections are missing for {artifact.stable_id}.")
            artifact_suffix = artifact.stable_id.removeprefix("KBT-").removesuffix("-ZH")
            for translated in translated_sections:
                suffix = f"{artifact_suffix}-{translated.ordinal:03d}"
                section = KbSection(
                    stable_id=f"KBC-PATIENT-{suffix}",
                    version_id=version.id,
                    heading_path_json=[translated.translated_heading],
                    ordinal=translated.ordinal,
                    language="zh-Hans",
                )
                db.add(section)
                db.flush()
                sections_created += 1
                text = translated.translated_text
                db.add(
                    KbPassage(
                        stable_id=f"KBPASS-PATIENT-{suffix}",
                        section_id=section.id,
                        version_id=version.id,
                        ordinal=0,
                        text=text,
                        language="zh-Hans",
                        character_count=len(text),
                        clinical_concept_tags_json=[translated.translated_heading],
                        audience_json=["patient", "doctor"],
                        chunking_version=HPA_PATIENT_CHUNKING_VERSION,
                        patient_readability_review_status="approved",
                        lexical_eligible=True,
                        vector_eligible=True,
                        embedding_json=embed_text(
                            f"{translated.translated_heading} {translated.translated_text}"
                        ),
                        embedding_model_version=EMBEDDING_MODEL_VERSION,
                        content_checksum=hashlib.sha256(text.encode()).hexdigest(),
                    )
                )
                passages_created += 1
        elif (
            version.source_id != source.id
            or version.normalized_checksum != artifact.translation_checksum
            or version.review_decision != "approved"
        ):
            raise ValueError(f"Existing HPA patient version drifted for {artifact.stable_id}.")

        source.lifecycle_state = "patient_approved"
        source.catalog_summary = HPA_APPROVED_CATALOG_SUMMARY
        source.medical_review_status = "approved"
        source.native_language_review_status = "approved"
        source.doctor_eligible = True
        source.patient_eligible = True
        for review_type in (
            "medical",
            "native_language",
            "patient_readability",
            "jurisdiction_applicability",
        ):
            reviews_created += int(
                _add_review_if_missing(
                    db,
                    target_stable_id=version.stable_id,
                    review_type=review_type,
                    reviewer_id=reviewer_id,
                    findings=findings,
                    reviewed_at=timestamp,
                    decision_code=HPA_PATIENT_REVIEW_DECISION_CODE,
                )
            )
        version_ids.append(version.id)

    db.flush()
    source_count_after = db.scalar(select(func.count()).select_from(KbSource)) or 0
    if source_count_after != source_count_before:
        raise RuntimeError("HPA patient promotion changed the governed source count.")
    return PatientCorpusPromotion(
        version_ids=version_ids,
        versions_created=versions_created,
        sections_created=sections_created,
        passages_created=passages_created,
        reviews_created=reviews_created,
    )


def active_patient_release_version_ids(db: Session) -> list[uuid.UUID]:
    active = db.get(KbActiveIndexRelease, "patient")
    if active is None:
        return []
    return list(
        dict.fromkeys(
            db.scalars(
                select(KbPassage.version_id)
                .join(
                    KbIndexReleasePassage,
                    KbIndexReleasePassage.passage_id == KbPassage.id,
                )
                .where(KbIndexReleasePassage.release_id == active.release_id)
                .order_by(KbPassage.version_id)
            )
        )
    )


def current_patient_version_ids(
    db: Session, version_ids: list[uuid.UUID]
) -> list[uuid.UUID]:
    """Choose one latest approved patient version per source for a new release."""

    versions = list(
        db.scalars(
            select(KbSourceVersion)
            .where(KbSourceVersion.id.in_(version_ids))
            .order_by(KbSourceVersion.stable_id)
        )
    )
    if len(versions) != len(set(version_ids)):
        raise ValueError("One or more patient source versions do not exist.")
    latest_by_source: dict[uuid.UUID, KbSourceVersion] = {}
    for version in versions:
        current = latest_by_source.get(version.source_id)
        version_key = (
            version.valid_from or version.captured_at,
            version.captured_at,
            version.stable_id,
        )
        current_key = (
            current.valid_from or current.captured_at,
            current.captured_at,
            current.stable_id,
        ) if current is not None else None
        if current_key is None or version_key > current_key:
            latest_by_source[version.source_id] = version
    return sorted((item.id for item in latest_by_source.values()), key=str)


def build_and_activate_patient_release(
    db: Session,
    *,
    version_ids: list[uuid.UUID],
    artifact_root: Path,
    approver_id: str,
):
    release = build_patient_candidate_release(
        db,
        version_ids=version_ids,
        artifact_root=artifact_root,
        approver_id=approver_id,
    )
    activate_index_release(db, release, audience="patient", activated_by=approver_id)
    return release


def build_patient_candidate_release(
    db: Session,
    *,
    version_ids: list[uuid.UUID],
    artifact_root: Path,
    approver_id: str,
    embedding_batch_size: int = 30,
    embedding_batch_character_budget: int = 6_000,
    embedding_timeout_seconds: float | None = None,
    embedding_max_attempts: int = 3,
):
    """Build a non-active release with immutable, release-scoped embeddings."""

    if not 1 <= embedding_batch_size <= 30:
        raise ValueError("embedding_batch_size must be between 1 and 30")
    if not 1_000 <= embedding_batch_character_budget <= 60_000:
        raise ValueError("embedding_batch_character_budget must be between 1000 and 60000")
    if not 1 <= embedding_max_attempts <= 5:
        raise ValueError("embedding_max_attempts must be between 1 and 5")
    settings = get_settings()
    embedding_model_version = settings.knowledge_embedding_model
    reranker_version = settings.knowledge_reranker_model
    requested_version_ids = list(dict.fromkeys(version_ids))
    version_ids = current_patient_version_ids(db, requested_version_ids)
    historical_version_ids = set(requested_version_ids) - set(version_ids)
    historical_markers: list[dict[str, object]] = []
    if historical_version_ids:
        historical_versions = list(
            db.scalars(
                select(KbSourceVersion)
                .where(KbSourceVersion.id.in_(historical_version_ids))
                .order_by(KbSourceVersion.stable_id)
            )
        )
        for version in historical_versions:
            source = db.get(KbSource, version.source_id)
            texts = list(
                db.scalars(
                    select(KbPassage.text)
                    .where(
                        KbPassage.version_id == version.id,
                        KbPassage.language == "zh-Hans",
                        KbPassage.patient_readability_review_status == "approved",
                    )
                    .order_by(KbPassage.stable_id)
                )
            )
            if source is None or not texts:
                continue
            search_text = " ".join([source.title, *source.search_keywords_json, *texts])
            historical_markers.append(
                {
                    "source_id": source.stable_id,
                    "version_id": version.stable_id,
                    "language": "zh-Hans",
                    "search_text": search_text,
                    "content_checksum": hashlib.sha256(search_text.encode()).hexdigest(),
                }
            )
    passages = list(
        db.scalars(
            select(KbPassage)
            .where(
                KbPassage.version_id.in_(version_ids),
                KbPassage.lexical_eligible.is_(True),
                KbPassage.vector_eligible.is_(True),
            )
            .order_by(KbPassage.stable_id)
        )
    )
    assert_passages_provider_transmittable(db, [item.stable_id for item in passages])
    embeddings: dict[uuid.UUID, list[float]] = {}
    embedding_passages = sorted(passages, key=lambda item: (len(item.text), item.stable_id))
    completed = 0
    next_progress = embedding_batch_size * 10
    for batch in _embedding_batches(
        embedding_passages,
        maximum_count=embedding_batch_size,
        character_budget=embedding_batch_character_budget,
    ):
        offset = completed
        query_options = (
            {"timeout_seconds": embedding_timeout_seconds}
            if embedding_timeout_seconds is not None
            else {}
        )
        for attempt in range(1, embedding_max_attempts + 1):
            try:
                vectors = query_embeddings(
                    [passage.text for passage in batch],
                    embedding_model_version,
                    **query_options,
                )
                break
            except ApiError as exc:
                if exc.code != "retrieval_unavailable" or attempt == embedding_max_attempts:
                    raise
                backoff_seconds = min(2 ** (attempt - 1), 4)
                logger.warning(
                    "patient_release_embedding_retry offset=%s batch_size=%s "
                    "attempt=%s max_attempts=%s backoff_seconds=%s code=%s",
                    offset,
                    len(batch),
                    attempt,
                    embedding_max_attempts,
                    backoff_seconds,
                    exc.code,
                )
                time.sleep(backoff_seconds)
        embeddings.update(
            (passage.id, vector)
            for passage, vector in zip(batch, vectors, strict=True)
        )
        completed += len(batch)
        if completed == len(embedding_passages) or completed >= next_progress:
            logger.info(
                "patient_release_embedding_progress completed=%s total=%s",
                completed,
                len(embedding_passages),
            )
            while next_progress <= completed:
                next_progress += embedding_batch_size * 10
    release = build_index_release(
        db,
        ImmutableArtifactStore(artifact_root),
        version_ids,
        audience="patient",
        embedding_model_version=embedding_model_version,
        lexical_analyzer_version=LEXICAL_ANALYZER_VERSION,
        reranker_version=reranker_version,
        approver_ids=[approver_id],
        passage_embeddings=embeddings,
        historical_markers=historical_markers,
    )
    return release
