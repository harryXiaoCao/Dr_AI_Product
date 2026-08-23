from datetime import date, datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Text, case, cast, exists, or_, select

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    KbPassage,
    KbPublisher,
    KbRightsRecord,
    KbSection,
    KbSource,
    KbSourceVersion,
    KbSummaryArtifact,
    KbTranslationArtifact,
    KbTranslationSection,
    UserRole,
)

router = APIRouter(prefix="/api/v1/doctor/resources", tags=["doctor resources"])


class KnowledgeCatalogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    title_en: str | None
    catalog_summary: str
    search_keywords: list[str]
    official_locator: str
    english_official_locator: str | None
    available_languages: list[str]
    is_bilingual: bool
    publisher_id: str
    publisher_name: str
    source_type: str
    topic: str
    jurisdiction: str
    original_language: str
    authority_tier: str
    publication_date: date | None
    catalog_verified_at: datetime
    lifecycle_state: str
    medical_review_status: str
    rights_decision_status: str
    rights_mode: str
    license_name: str | None
    rights_evidence_locator: str
    attribution_requirements: str | None
    publisher_date_text: str | None
    zh_translation_status: str | None


class KnowledgeResourceSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    original_text: str


class KnowledgeResourceTranslation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str
    title: str
    translation_type: str
    review_status: str
    sections: list[KnowledgeResourceSection]


class KnowledgeResourceDetail(KnowledgeCatalogItem):
    sections: list[KnowledgeResourceSection]
    translations: list[KnowledgeResourceTranslation]


class KnowledgeCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    items: list[KnowledgeCatalogItem]


def _original_text_display_allowed(rights: KbRightsRecord) -> bool:
    return (
        rights.decision_status == "approved"
        and rights.storage_allowed
        and rights.excerpt_display_allowed
        and rights.redistribution_allowed
    )


def _translation_display_allowed(
    source: KbSource,
    translation: KbTranslationArtifact | None,
) -> bool:
    if translation is None:
        return False
    if translation.status == "approved":
        return True
    return (
        source.stable_id.startswith("KBS-HPA-")
        and translation.provider == "opencc"
        and translation.prompt_policy_version == "deterministic-zh-hant-to-zh-hans-v1"
        and translation.status == "generated_pending_review"
    )


def _latest_translation(
    db: DbSession,
    version: KbSourceVersion | None,
) -> KbTranslationArtifact | None:
    if version is None:
        return None
    return db.scalar(
        select(KbTranslationArtifact)
        .where(
            KbTranslationArtifact.source_version_id == version.id,
            KbTranslationArtifact.target_language == "zh-Hans",
        )
        .order_by(KbTranslationArtifact.generated_at.desc())
        .limit(1)
    )


def _catalog_language_fields(
    source: KbSource,
    generated_translation: KbTranslationArtifact | None,
) -> tuple[str, str | None, list[str], bool, str | None]:
    official_english = next(
        (
            translation
            for translation in source.official_translations_json
            if translation.get("language") == "en"
        ),
        None,
    )
    displayable_translation = (
        generated_translation
        if _translation_display_allowed(source, generated_translation)
        else None
    )
    languages = [source.original_language]
    languages.extend(translation["language"] for translation in source.official_translations_json)
    if displayable_translation is not None:
        languages.append(displayable_translation.target_language)
    languages = list(dict.fromkeys(languages))
    title = (
        displayable_translation.translated_title
        if displayable_translation is not None and source.original_language in {"en", "zh-Hant"}
        else source.title
    )
    title_en = (
        official_english.get("title")
        if official_english
        else source.title
        if source.original_language == "en"
        else None
    )
    translation_status = generated_translation.status if generated_translation else None
    return title, title_en, languages, len(languages) > 1, translation_status


@router.get("", response_model=KnowledgeCatalogResponse)
def list_doctor_resource_catalog(
    db: DbSession,
    user: CurrentUser,
    query: str | None = Query(default=None, min_length=2, max_length=200),
    topic: str | None = Query(default=None, max_length=120),
    publisher_id: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> KnowledgeCatalogResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise ApiError(403, "forbidden", "This resource is not available.")

    conditions = [KbSource.catalog_visible.is_(True), KbSource.status == "current"]
    if query:
        search = f"%{query.strip()}%"
        conditions.append(
            or_(
                KbSource.title.ilike(search),
                KbSource.topic.ilike(search),
                cast(KbSource.official_translations_json, Text).ilike(search),
                KbSource.catalog_summary.ilike(search),
                cast(KbSource.search_keywords_json, Text).ilike(search),
                exists(
                    select(KbTranslationArtifact.id).where(
                        KbTranslationArtifact.source_id == KbSource.id,
                        KbTranslationArtifact.target_language == "zh-Hans",
                        KbTranslationArtifact.status == "approved",
                        KbTranslationArtifact.translated_title.ilike(search),
                    )
                ),
                exists(
                    select(KbSummaryArtifact.id).where(
                        KbSummaryArtifact.source_id == KbSource.id,
                        KbSummaryArtifact.status == "approved",
                        or_(
                            KbSummaryArtifact.english_summary.ilike(search),
                            KbSummaryArtifact.chinese_summary.ilike(search),
                        ),
                    )
                ),
            )
        )
    if topic:
        conditions.append(KbSource.topic == topic)
    if publisher_id:
        conditions.append(KbPublisher.stable_id == publisher_id)

    joined = (
        select(KbSource, KbPublisher, KbRightsRecord)
        .join(KbPublisher, KbPublisher.id == KbSource.publisher_id)
        .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
        .where(*conditions)
    )
    source_rows = db.execute(joined.order_by(KbSource.title, KbSource.stable_id)).all()
    source_ids = [source.id for source, _, _ in source_rows]
    versions_by_source: dict[object, list[KbSourceVersion]] = {}
    if source_ids:
        all_versions = db.scalars(
            select(KbSourceVersion)
            .where(KbSourceVersion.source_id.in_(source_ids))
            .order_by(
                KbSourceVersion.valid_from,
                case((KbSourceVersion.capture_mode == "metadata_only", 0), else_=1),
                KbSourceVersion.stable_id,
            )
        ).all()
        for version in all_versions:
            versions_by_source.setdefault(version.source_id, []).append(version)
    rows: list[tuple[KbSource, KbPublisher, KbRightsRecord, KbSourceVersion | None]] = []
    for source, publisher, rights in source_rows:
        versions = versions_by_source.get(source.id, [])
        if publisher.stable_id == "KBP-TW-HPA":
            rows.extend((source, publisher, rights, version) for version in versions)
        else:
            rows.append((source, publisher, rights, versions[-1] if versions else None))
    total = len(rows)
    rows = rows[offset : offset + limit]
    version_ids = [version.id for _, _, _, version in rows if version is not None]
    translations_by_version: dict[object, KbTranslationArtifact] = {}
    if version_ids:
        page_translations = db.scalars(
            select(KbTranslationArtifact)
            .where(
                KbTranslationArtifact.source_version_id.in_(version_ids),
                KbTranslationArtifact.target_language == "zh-Hans",
            )
            .order_by(KbTranslationArtifact.generated_at)
        ).all()
        for translation in page_translations:
            translations_by_version[translation.source_version_id] = translation
    items: list[KnowledgeCatalogItem] = []
    for source, publisher, rights, latest_version in rows:
        english = next(
            (
                translation
                for translation in source.official_translations_json
                if translation.get("language") == "en"
            ),
            None,
        )
        generated_translation = (
            translations_by_version.get(latest_version.id) if latest_version is not None else None
        )
        title, title_en, languages, is_bilingual, translation_status = _catalog_language_fields(
            source, generated_translation
        )
        items.append(
            KnowledgeCatalogItem(
                source_id=(
                    latest_version.stable_id
                    if publisher.stable_id == "KBP-TW-HPA" and latest_version is not None
                    else source.stable_id
                ),
                title=title,
                title_en=title_en,
                catalog_summary=source.catalog_summary,
                search_keywords=source.search_keywords_json,
                official_locator=source.canonical_locator,
                english_official_locator=(
                    english.get("official_locator")
                    if english
                    else source.canonical_locator
                    if source.original_language == "en"
                    else None
                ),
                available_languages=languages,
                is_bilingual=is_bilingual,
                publisher_id=publisher.stable_id,
                publisher_name=publisher.official_name_zh,
                source_type=source.source_type,
                topic=source.topic,
                jurisdiction=source.jurisdiction,
                original_language=source.original_language,
                authority_tier=source.authority_tier,
                publication_date=(
                    latest_version.valid_from.date()
                    if publisher.stable_id == "KBP-TW-HPA"
                    and latest_version is not None
                    and latest_version.valid_from is not None
                    else source.publication_date
                ),
                catalog_verified_at=source.catalog_verified_at,
                lifecycle_state=source.lifecycle_state,
                medical_review_status=source.medical_review_status,
                rights_decision_status=rights.decision_status,
                rights_mode=(
                    "stored_text"
                    if _original_text_display_allowed(rights)
                    else "official_link_only"
                ),
                license_name=rights.license_name,
                rights_evidence_locator=rights.evidence_locator,
                attribution_requirements=rights.attribution_requirements,
                publisher_date_text=(
                    latest_version.publisher_version_label if latest_version else None
                ),
                zh_translation_status=translation_status,
            )
        )
    return KnowledgeCatalogResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/{source_id}", response_model=KnowledgeResourceDetail)
def get_doctor_resource(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
) -> KnowledgeResourceDetail:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise ApiError(403, "forbidden", "This resource is not available.")
    requested_version = db.scalar(
        select(KbSourceVersion).where(KbSourceVersion.stable_id == source_id)
    )
    row = db.execute(
        select(KbSource, KbPublisher, KbRightsRecord)
        .join(KbPublisher, KbPublisher.id == KbSource.publisher_id)
        .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
        .where(
            KbSource.id == requested_version.source_id
            if requested_version is not None
            else KbSource.stable_id == source_id,
            KbSource.catalog_visible.is_(True),
            KbSource.status == "current",
        )
    ).one_or_none()
    if row is None:
        raise ApiError(404, "resource_not_found", "The resource was not found.")
    source, publisher, rights = row
    version = requested_version or db.scalar(
        select(KbSourceVersion)
        .where(KbSourceVersion.source_id == source.id)
        .order_by(
            KbSourceVersion.captured_at.desc(),
            case((KbSourceVersion.capture_mode == "metadata_only", 1), else_=0),
            KbSourceVersion.stable_id.desc(),
        )
        .limit(1)
    )
    sections: list[KnowledgeResourceSection] = []
    if (
        version
        and version.capture_mode in {"publisher_original_text", "licensed_dataset_original_text"}
        and _original_text_display_allowed(rights)
    ):
        section_rows = db.execute(
            select(KbSection, KbPassage)
            .join(KbPassage, KbPassage.section_id == KbSection.id)
            .where(KbSection.version_id == version.id)
            .order_by(KbSection.ordinal, KbPassage.ordinal)
        ).all()
        for section, passage in section_rows:
            if passage.language != source.original_language:
                continue
            sections.append(
                KnowledgeResourceSection(
                    heading=(section.heading_path_json[-1] if section.heading_path_json else ""),
                    original_text=passage.text,
                )
            )
    english = next(
        (
            translation
            for translation in source.official_translations_json
            if translation.get("language") == "en"
        ),
        None,
    )
    generated_translation = _latest_translation(db, version)
    title, title_en, languages, is_bilingual, translation_status = _catalog_language_fields(
        source, generated_translation
    )
    translations: list[KnowledgeResourceTranslation] = []
    if (
        publisher.stable_id == "KBP-WHO"
        and version is not None
        and _original_text_display_allowed(rights)
    ):
        official_languages = {
            translation["language"] for translation in source.official_translations_json
        }
        for language in sorted(official_languages):
            official_rows = db.execute(
                select(KbSection, KbPassage)
                .join(KbPassage, KbPassage.section_id == KbSection.id)
                .where(
                    KbSection.version_id == version.id,
                    KbPassage.language == language,
                )
                .order_by(KbSection.ordinal, KbPassage.ordinal)
            ).all()
            if not official_rows:
                continue
            official = next(
                item for item in source.official_translations_json if item["language"] == language
            )
            translations.append(
                KnowledgeResourceTranslation(
                    language=language,
                    title=official["title"],
                    translation_type="official_publisher_version",
                    review_status="official_text_medical_review_pending",
                    sections=[
                        KnowledgeResourceSection(
                            heading=(
                                section.heading_path_json[-1] if section.heading_path_json else ""
                            ),
                            original_text=passage.text,
                        )
                        for section, passage in official_rows
                    ],
                )
            )
    if _translation_display_allowed(source, generated_translation):
        assert generated_translation is not None
        translated_sections = db.scalars(
            select(KbTranslationSection)
            .where(KbTranslationSection.artifact_id == generated_translation.id)
            .order_by(KbTranslationSection.ordinal)
        ).all()
        translations.append(
            KnowledgeResourceTranslation(
                language=generated_translation.target_language,
                title=generated_translation.translated_title,
                translation_type=(
                    "deterministic_script_conversion"
                    if generated_translation.provider == "opencc"
                    else "ai_generated_unofficial"
                ),
                review_status=(
                    "medical_and_native_chinese_approved"
                    if generated_translation.status == "approved"
                    else "pending_medical_and_native_simplified_chinese_review"
                ),
                sections=[
                    KnowledgeResourceSection(
                        heading=section.translated_heading,
                        original_text=section.translated_text,
                    )
                    for section in translated_sections
                ],
            )
        )
    return KnowledgeResourceDetail(
        source_id=source_id,
        title=title,
        title_en=title_en,
        catalog_summary=source.catalog_summary,
        search_keywords=source.search_keywords_json,
        official_locator=source.canonical_locator,
        english_official_locator=(
            english.get("official_locator")
            if english
            else source.canonical_locator
            if source.original_language == "en"
            else None
        ),
        available_languages=languages,
        is_bilingual=is_bilingual,
        publisher_id=publisher.stable_id,
        publisher_name=publisher.official_name_zh,
        source_type=source.source_type,
        topic=source.topic,
        jurisdiction=source.jurisdiction,
        original_language=source.original_language,
        authority_tier=source.authority_tier,
        publication_date=(
            version.valid_from.date()
            if publisher.stable_id == "KBP-TW-HPA"
            and version is not None
            and version.valid_from is not None
            else source.publication_date
        ),
        catalog_verified_at=source.catalog_verified_at,
        lifecycle_state=source.lifecycle_state,
        medical_review_status=source.medical_review_status,
        rights_decision_status=rights.decision_status,
        rights_mode=(
            "stored_text" if _original_text_display_allowed(rights) else "official_link_only"
        ),
        license_name=rights.license_name,
        rights_evidence_locator=rights.evidence_locator,
        attribution_requirements=rights.attribution_requirements,
        publisher_date_text=version.publisher_version_label if version else None,
        zh_translation_status=translation_status,
        sections=sections,
        translations=translations,
    )
