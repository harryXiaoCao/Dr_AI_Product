from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import re
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, replace
from datetime import date
from typing import Literal

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot_contracts import (
    AuthorityTier,
    DoctorResourceSearchItem,
    DoctorResourceSearchRequest,
    DoctorResourceSearchResponse,
    EvidenceDecision,
    EvidencePassage,
    PatientEvidenceRequest,
    PatientEvidenceResponse,
    SourceCitation,
    SourceStatus,
)
from app.clinical_presentation import (
    ClinicalPresentation,
    PresentationRetrievalView,
    PresentationViewKind,
    extract_clinical_presentation,
)
from app.config import (
    PRODUCTION_EMBEDDING_MODEL,
    PRODUCTION_RERANKER_MODEL,
    get_settings,
)
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.knowledge_rights import assert_passages_provider_transmittable
from app.models import (
    KbActiveIndexRelease,
    KbIndexRelease,
    KbIndexReleasePassage,
    KbPassage,
    KbPublisher,
    KbRetrievalEvent,
    KbReview,
    KbRightsRecord,
    KbSource,
    KbSourceFamily,
    KbSourceVersion,
    UserRole,
)

router = APIRouter(prefix="/api/v1/retrieval", tags=["knowledge retrieval"])

EMBEDDING_DIMENSIONS = 96
EMBEDDING_MODEL_VERSION = "dr-ai-hashed-multilingual-v1"
LEXICAL_ANALYZER_VERSION = "dr-ai-unicode-zh-bigram-en-word-v1"
RERANKER_VERSION = "dr-ai-policy-reranker-v5-central-clinical-concepts"
PRESENTATION_FUSION_VERSION = "controlled-presentation-rrf-v1"
PRODUCTION_EMBEDDING_MODEL_VERSION = PRODUCTION_EMBEDDING_MODEL
PRODUCTION_RERANKER_VERSION = PRODUCTION_RERANKER_MODEL
MAX_CROSS_ENCODER_CANDIDATES = 30
MIN_PATIENT_LEXICAL_COVERAGE = 0.08
STRONG_SINGLE_SOURCE_COVERAGE = 0.15
MIN_MULTI_SOURCE_COVERAGE = 0.10

ENGLISH_RELEVANCE_STOPWORDS = {
    "and",
    "are",
    "can",
    "does",
    "for",
    "how",
    "the",
    "this",
    "what",
    "when",
    "why",
    "with",
}
CHINESE_RELEVANCE_STOPWORDS = {
    "不是",
    "什么",
    "作用",
    "可以",
    "多久",
    "如何",
    "应该",
    "意义",
    "是否",
    "有什",
    "没事",
    "那我",
    "需要",
    "怎么",
}
CHINESE_QUESTION_NOISE_CHARACTERS = set("是不就没事吗呢的了我你他她它们有无会能可否什么怎样")
CLINICAL_CONCEPT_ALIASES = {
    "cardiac_rhythm_symptom": (
        "心悸",
        "心慌",
        "漏跳",
        "跳空",
        "乱跳",
        "怦怦跳",
        "心跳过快",
        "心跳很快",
        "心跳不齐",
        "心跳不规律",
        "心律不齐",
        "心律失常",
        "palpitation",
        "palpitations",
        "skipped beat",
        "irregular heartbeat",
        "rapid heartbeat",
    ),
    "chest_discomfort": ("胸痛", "心绞痛", "胸闷", "chest pain", "chest pressure"),
    "breathing_difficulty": (
        "气短",
        "喘",
        "呼吸不顺",
        "呼吸困难",
        "shortness of breath",
        "difficulty breathing",
    ),
    "dizziness": ("头晕", "眩晕", "晕厥", "dizzy", "dizziness", "fainting"),
    "headache": ("头痛", "偏头痛", "headache", "migraine"),
    "fever": ("发热", "发烧", "高烧", "fever"),
    "gastrointestinal_symptom": (
        "恶心",
        "呕吐",
        "腹痛",
        "肚子痛",
        "腹泻",
        "nausea",
        "vomiting",
        "abdominal pain",
        "diarrhea",
    ),
    "neurologic_symptom": (
        "麻木",
        "无力",
        "乏力",
        "抽搐",
        "numbness",
        "weakness",
        "seizure",
    ),
    "bleeding": ("出血", "流血", "bleeding"),
}
PRIMARY_SYMPTOM_CONCEPTS = frozenset(CLINICAL_CONCEPT_ALIASES)
CLINICAL_CONCEPT_CORE_ALIASES = {
    concept: aliases for concept, aliases in CLINICAL_CONCEPT_ALIASES.items()
}

CENTRAL_QUERY_INTENTS = {
    "measurement_tracking": {
        "triggers": (
            "记录",
            "监测",
            "测量",
            "测得",
            "怎么记",
            "如何记",
            "怎样记",
            "记多久",
            "record",
            "track",
            "monitor",
            "measure",
            "check",
        ),
        "central": (
            "记录",
            "监测",
            "测量",
            "量血压",
            "record",
            "track",
            "monitor",
            "measur",
            "check",
        ),
    },
    "medication": {
        "triggers": ("药物", "用药", "服药", "降压药", "medicine", "medication", "drug"),
        "central": ("药物", "用药", "服药", "降压药", "medicine", "medication", "drug"),
    },
    "medication_mechanism": {
        "triggers": (
            "怎样帮助",
            "如何帮助",
            "怎么帮助",
            "怎样起作用",
            "如何起作用",
            "作用机制",
            "how does",
            "how do",
            "mechanism",
        ),
        "central": ("作用", "机制", "原理", "帮助", "how it works", "mechanism"),
    },
}

CENTRAL_CLINICAL_TOPICS = {
    "blood_pressure": (
        "血压",
        "高血压",
        "降压",
        "blood pressure",
        "hypertension",
    ),
    "glycemic_control": (
        "血糖",
        "糖尿病",
        "糖化血红蛋白",
        "糖基化血红蛋白",
        "hba1c",
        "a1c",
        "blood glucose",
        "diabetes",
    ),
    "blood_lipids": (
        "血脂",
        "胆固醇",
        "甘油三酯",
        "cholesterol",
        "triglyceride",
    ),
    "screening": ("筛查", "筛检", "screening"),
}

STALE_QUERY_MARKERS = (
    "撤回",
    "已撤",
    "旧版",
    "过时",
    "废止",
    "withdrawn",
    "superseded",
    "outdated",
)
CONFLICT_QUERY_MARKERS = (
    "不一致",
    "相冲突",
    "有冲突",
    "不同地区",
    "不同国家",
    "conflict",
    "inconsistent",
)


def normalize_medical_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def lexical_tokens(value: str) -> list[str]:
    normalized = normalize_medical_text(value)
    english = re.findall(r"[a-z0-9]+", normalized)
    chinese_runs = re.findall(r"[\u3400-\u9fff]+", normalized)
    chinese: list[str] = []
    for run in chinese_runs:
        chinese.extend(run)
        chinese.extend(run[index : index + 2] for index in range(len(run) - 1))
    return list(dict.fromkeys([*english, *chinese]))


def relevance_tokens(value: str) -> list[str]:
    """Return topic-bearing terms without high-noise single Chinese characters."""

    normalized = normalize_medical_text(value)
    english = [
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) >= 3 and token not in ENGLISH_RELEVANCE_STOPWORDS
    ]
    chinese_runs = re.findall(r"[\u3400-\u9fff]+", normalized)
    chinese = [
        run[index : index + 2]
        for run in chinese_runs
        for index in range(len(run) - 1)
        if run[index : index + 2] not in CHINESE_RELEVANCE_STOPWORDS
        and not set(run[index : index + 2]) & CHINESE_QUESTION_NOISE_CHARACTERS
    ]
    return list(dict.fromkeys([*english, *chinese]))


def clinical_concepts(value: str) -> set[str]:
    normalized = normalize_medical_text(value)
    return {
        concept
        for concept, aliases in CLINICAL_CONCEPT_ALIASES.items()
        if any(normalize_medical_text(alias) in normalized for alias in aliases)
    }


def central_clinical_concepts(value: str) -> set[str]:
    normalized = normalize_medical_text(value)
    return {
        concept
        for concept, aliases in CLINICAL_CONCEPT_CORE_ALIASES.items()
        if any(normalize_medical_text(alias) in normalized for alias in aliases)
    }


def embed_text(value: str) -> list[float]:
    """Local deterministic baseline behind the replaceable embedding contract."""

    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = lexical_tokens(value)
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign * (1.0 + min(len(token), 8) / 8)
    magnitude = math.sqrt(sum(component * component for component in vector))
    return [component / magnitude for component in vector] if magnitude else vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


def query_embeddings(
    values: list[str],
    model_version: str,
    *,
    timeout_seconds: float | None = None,
) -> list[list[float]]:
    if not values or len(values) > MAX_CROSS_ENCODER_CANDIDATES:
        raise ValueError("Embedding batches must contain between 1 and 30 inputs.")
    if model_version == EMBEDDING_MODEL_VERSION:
        return [embed_text(value) for value in values]
    settings = get_settings()
    if (
        settings.knowledge_embedding_backend != "http_service"
        or not settings.knowledge_embedding_service_url
        or settings.knowledge_embedding_model != model_version
    ):
        raise ApiError(
            503,
            "retrieval_unavailable",
            "The active index embedding model is not configured.",
        )
    body = json.dumps({"model": model_version, "input": values}).encode()
    request = urllib.request.Request(
        settings.knowledge_embedding_service_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds or settings.knowledge_embedding_timeout_seconds,
        ) as response:
            payload = json.loads(response.read())
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise ApiError(
            503, "retrieval_unavailable", "The embedding service is unavailable."
        ) from exc
    embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
    if embeddings is None and isinstance(payload, dict) and payload.get("data"):
        embeddings = [item.get("embedding") for item in payload["data"]]
    if (
        not isinstance(embeddings, list)
        or len(embeddings) != len(values)
        or any(not isinstance(item, list) or not item for item in embeddings)
    ):
        raise ApiError(503, "retrieval_unavailable", "The embedding response is invalid.")
    dimensions = {len(item) for item in embeddings}
    if len(dimensions) != 1:
        raise ApiError(503, "retrieval_unavailable", "Embedding dimensions are inconsistent.")
    return [[float(component) for component in item] for item in embeddings]


def query_embedding(value: str, model_version: str) -> list[float]:
    return query_embeddings([value], model_version)[0]


@dataclass(frozen=True)
class RetrievalCandidate:
    passage: KbPassage
    version: KbSourceVersion
    source: KbSource
    publisher: KbPublisher
    lexical_score: float
    topic_coverage_score: float
    matched_concepts: list[str]
    dense_score: float
    rerank_score: float
    matched_terms: list[str]
    applicable_jurisdictions: tuple[str, ...] = ()
    centrality_score: float = 0.0


@dataclass(frozen=True)
class RetrievalResult:
    request_id: str
    release: KbIndexRelease
    original_query: str
    expanded_terms: list[str]
    candidates: list[RetrievalCandidate]
    ranked_candidates: list[RetrievalCandidate]
    decision: EvidenceDecision
    next_cursor: str | None = None
    ranking_backend: str = "deterministic_fallback"
    ranking_fallback_code: str | None = None
    view_kinds: tuple[str, ...] = (PresentationViewKind.literal.value,)
    literal_candidate_count: int = 0
    latency_ms: int = 0


def _cross_encoder_rerank(
    db: Session,
    query: str,
    candidates: list[RetrievalCandidate],
    *,
    candidate_limit_override: int | None = None,
) -> tuple[list[RetrievalCandidate], str, str | None]:
    settings = get_settings()
    if settings.knowledge_reranker_backend != "http_service":
        return candidates, "deterministic_fallback", None
    candidate_limit = settings.knowledge_reranker_max_candidates
    if candidate_limit_override is not None:
        if candidate_limit_override < 1:
            raise ValueError("candidate_limit_override must be positive")
        candidate_limit = min(candidate_limit, candidate_limit_override)
    selected: list[RetrievalCandidate] = []
    selected_sources: set[str] = set()
    for candidate in candidates:
        if candidate.source.stable_id in selected_sources:
            continue
        selected_sources.add(candidate.source.stable_id)
        selected.append(candidate)
        if len(selected) == candidate_limit:
            break
    if not selected:
        return candidates, "not_applicable", None
    try:
        assert_passages_provider_transmittable(db, [item.passage.stable_id for item in selected])
    except PermissionError as exc:
        raise ApiError(
            503,
            "retrieval_unavailable",
            "Current provider-transmission rights do not permit ranking this evidence.",
        ) from exc
    body = json.dumps(
        {
            "model": settings.knowledge_reranker_model,
            "query": query,
            "documents": [
                {"id": item.passage.stable_id, "text": item.passage.text} for item in selected
            ],
        },
        ensure_ascii=False,
    ).encode()
    request = urllib.request.Request(
        settings.knowledge_reranker_service_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=settings.knowledge_reranker_timeout_seconds
        ) as response:
            payload = json.loads(response.read())
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise ValueError("missing results")
        scores = {
            str(item["id"]): float(item["score"])
            for item in results
            if isinstance(item, dict) and "id" in item and "score" in item
        }
        if set(scores) != {item.passage.stable_id for item in selected}:
            raise ValueError("reranker IDs do not match the request")
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
        return candidates, "deterministic_fallback", "reranker_unavailable"
    # The cross encoder judges passage relevance, but it must not erase the
    # structured central-topic signal that selected the candidate. This keeps a
    # generic passage with incidental query words from outranking a source whose
    # title/summary/tags are actually about the requested task.
    reranked = [
        replace(
            item,
            rerank_score=scores[item.passage.stable_id] + 0.25 * item.centrality_score,
        )
        for item in selected
    ]
    reranked.sort(
        key=lambda item: (-item.rerank_score, item.source.stable_id, item.passage.stable_id)
    )
    selected_passage_ids = {item.passage.id for item in selected}
    remainder = [item for item in candidates if item.passage.id not in selected_passage_ids]
    return [*reranked, *remainder], "cross_encoder", None


def _cursor_context(request: DoctorResourceSearchRequest, release: KbIndexRelease) -> str:
    request_fingerprint = json.dumps(
        {"query": request.query, "filters": request.filters.model_dump(mode="json")},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{release.stable_id}:{hashlib.sha256(request_fingerprint.encode()).hexdigest()}"


def _encode_cursor(context: str, offset: int) -> str:
    payload = json.dumps({"context": context, "offset": offset}, separators=(",", ":")).encode()
    signature = hmac.new(
        get_settings().jwt_secret.get_secret_value().encode(), payload, hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(payload + signature).decode().rstrip("=")


def _decode_cursor(cursor: str, expected_context: str) -> int:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode())
        payload, signature = decoded[:-32], decoded[-32:]
        expected_signature = hmac.new(
            get_settings().jwt_secret.get_secret_value().encode(), payload, hashlib.sha256
        ).digest()
        values = json.loads(payload)
        offset = int(values["offset"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, binascii.Error) as exc:
        raise ApiError(400, "bad_request", "The retrieval cursor is invalid.") from exc
    if (
        not hmac.compare_digest(signature, expected_signature)
        or values.get("context") != expected_context
        or offset < 0
    ):
        raise ApiError(400, "bad_request", "The retrieval cursor is invalid.")
    return offset


def _expanded_terms(release: KbIndexRelease, query: str) -> list[str]:
    query_tokens = set(lexical_tokens(query))
    expansions: list[str] = []
    terminology = release.build_results_json.get("terminology", [])
    if not isinstance(terminology, list):
        return []
    for term in terminology:
        if not isinstance(term, dict):
            continue
        variants = [
            str(term.get("preferred_zh") or ""),
            str(term.get("preferred_en") or ""),
            *(str(item) for item in term.get("aliases", []) if isinstance(item, str)),
        ]
        if any(query_tokens & set(lexical_tokens(variant)) for variant in variants):
            for variant in variants:
                normalized = normalize_medical_text(variant)
                if normalized and normalized not in normalize_medical_text(query):
                    expansions.append(variant)
    return list(dict.fromkeys(expansions))[:20]


def _query_has_marker(query: str, markers: tuple[str, ...]) -> bool:
    normalized = normalize_medical_text(query)
    return any(normalize_medical_text(marker) in normalized for marker in markers)


def _central_query_requirements(query: str) -> list[tuple[str, tuple[str, ...]]]:
    normalized = normalize_medical_text(query)
    requirements: list[tuple[str, tuple[str, ...]]] = []
    for intent, config in CENTRAL_QUERY_INTENTS.items():
        triggered = any(normalize_medical_text(item) in normalized for item in config["triggers"])
        if intent == "measurement_tracking" and re.search(
            r"(?:怎么|如何|怎样|咋).{0,4}(?:记|记录)", normalized
        ):
            triggered = True
        if triggered:
            requirements.append((intent, tuple(config["central"])))
    return requirements


def _central_topic_requirements(query: str) -> list[tuple[str, ...]]:
    normalized = normalize_medical_text(query)
    return [
        tuple(aliases)
        for aliases in CENTRAL_CLINICAL_TOPICS.values()
        if any(normalize_medical_text(alias) in normalized for alias in aliases)
    ]


def _specific_query_entities(query: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            normalize_medical_text(item)
            for item in re.findall(
                r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+(?![A-Za-z0-9])",
                query,
            )
        )
    )


def _release_has_historical_match(
    release: KbIndexRelease, query: str, expanded_terms: list[str]
) -> bool:
    markers = release.build_results_json.get("historical_markers", [])
    if not isinstance(markers, list):
        return False
    query_tokens = set(relevance_tokens(" ".join([query, *expanded_terms])))
    if not query_tokens:
        return False
    for marker in markers:
        if not isinstance(marker, dict) or marker.get("language") != "zh-Hans":
            continue
        searchable = normalize_medical_text(str(marker.get("search_text") or ""))
        coverage = len({token for token in query_tokens if token in searchable}) / len(query_tokens)
        if coverage >= MIN_PATIENT_LEXICAL_COVERAGE:
            return True
    return False


def _active_rows(
    db: Session,
    audience: Literal["doctor", "patient"],
) -> tuple[
    KbIndexRelease,
    list[tuple[KbPassage, KbSourceVersion, KbSource, KbPublisher, list[float] | None]],
]:
    active = db.get(KbActiveIndexRelease, audience)
    release = db.get(KbIndexRelease, active.release_id) if active else None
    if release is None or release.status != "active":
        raise ApiError(503, "retrieval_unavailable", "No approved retrieval index is active.")
    if release.build_results_json.get("audience") != audience:
        raise ApiError(503, "retrieval_unavailable", "The active retrieval index is invalid.")
    release_passages = db.execute(
        select(
            KbIndexReleasePassage.passage_id,
            KbIndexReleasePassage.embedding_json,
            KbIndexReleasePassage.embedding_model_version,
        )
        .where(KbIndexReleasePassage.release_id == release.id)
        .order_by(KbIndexReleasePassage.passage_id)
    ).all()
    if not release_passages:
        return release, []

    release_membership = {
        passage_id: (embedding_json, embedding_model_version)
        for passage_id, embedding_json, embedding_model_version in release_passages
    }
    eligible_rows = db.execute(
        select(
            KbPassage,
            KbSourceVersion,
            KbSource,
            KbPublisher,
        )
        .select_from(KbPassage)
        .join(KbSourceVersion, KbSourceVersion.id == KbPassage.version_id)
        .join(KbSource, KbSource.id == KbSourceVersion.source_id)
        .outerjoin(KbSourceFamily, KbSourceFamily.id == KbSource.source_family_id)
        .join(KbPublisher, KbPublisher.id == KbSource.publisher_id)
        .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
        .where(
            KbPassage.id.in_(release_membership),
            KbRightsRecord.decision_status == "approved",
            KbRightsRecord.embedding_allowed.is_(True),
            KbRightsRecord.excerpt_display_allowed.is_(True),
            (KbSource.source_family_id.is_(None) | (KbSourceFamily.status == "active")),
            KbSourceVersion.review_decision == "approved",
            KbPassage.lexical_eligible.is_(True),
            KbPassage.vector_eligible.is_(True),
        )
        .order_by(KbPassage.id)
    ).all()

    rows = []
    for passage, version, source, publisher in eligible_rows:
        release_embedding, release_embedding_model = release_membership[passage.id]
        if release_embedding is not None:
            if release_embedding_model != release.embedding_model_version:
                continue
            selected_embedding = release_embedding
        else:
            if (
                passage.embedding_json is None
                or passage.embedding_model_version != release.embedding_model_version
            ):
                continue
            selected_embedding = passage.embedding_json
        rows.append((passage, version, source, publisher, selected_embedding))
    return release, rows


def _matches_filters(
    source: KbSource,
    publisher: KbPublisher,
    passage: KbPassage,
    request: DoctorResourceSearchRequest | PatientEvidenceRequest,
    audience: Literal["doctor", "patient"],
) -> bool:
    if source.status != "current" or source.lifecycle_state not in {
        "doctor_approved",
        "patient_approved",
        "indexed_in_immutable_release",
        "monitored",
    }:
        return False
    if audience == "doctor":
        filters = request.filters
        if not source.doctor_eligible or "doctor" not in passage.audience_json:
            return False
        checks = (
            (filters.topics, source.topic),
            (filters.document_types, source.source_type),
            (filters.organization_ids, publisher.stable_id),
            (filters.jurisdictions, source.jurisdiction),
            (filters.languages, passage.language),
        )
        if any(values and actual not in values for values, actual in checks):
            return False
        if filters.published_from and (
            source.publication_date is None or source.publication_date < filters.published_from
        ):
            return False
        if filters.published_to and (
            source.publication_date is None or source.publication_date > filters.published_to
        ):
            return False
    else:
        if (
            not source.patient_eligible
            or "patient" not in passage.audience_json
            or passage.patient_readability_review_status != "approved"
            or passage.language != request.language
            or (request.topics and source.topic not in request.topics)
            or source.source_type in request.excluded_content_types
        ):
            return False
    return True


def _rank_candidates(
    rows: list[tuple[KbPassage, KbSourceVersion, KbSource, KbPublisher, list[float] | None]],
    query: str,
    expanded_terms: list[str],
    *,
    prefer_china: bool,
    query_vector: list[float],
    require_lexical_anchor: bool,
    source_applicable_jurisdictions: dict[str, list[str]] | None = None,
) -> list[RetrievalCandidate]:
    primary_tokens = relevance_tokens(query)
    expansion_tokens = relevance_tokens(" ".join(expanded_terms))
    required_concepts = clinical_concepts(query) & PRIMARY_SYMPTOM_CONCEPTS
    central_requirements = _central_query_requirements(query)
    central_topic_requirements = _central_topic_requirements(query)
    specific_entities = _specific_query_entities(query)
    source_applicable_jurisdictions = source_applicable_jurisdictions or {}
    candidates: list[RetrievalCandidate] = []
    for row in rows:
        passage, version, source, publisher = row[:4]
        release_embedding = row[4] if len(row) == 5 else None
        searchable = normalize_medical_text(
            " ".join(
                [
                    source.title,
                    source.catalog_summary,
                    *source.search_keywords_json,
                    *passage.clinical_concept_tags_json,
                    passage.text,
                ]
            )
        )
        normalized_title = normalize_medical_text(source.title)
        title_lexical = len({token for token in primary_tokens if token in normalized_title}) / max(
            len(set(primary_tokens)), 1
        )
        primary_matched = [token for token in primary_tokens if token in searchable]
        expansion_matched = [token for token in expansion_tokens if token in searchable]
        passage_concepts = required_concepts & clinical_concepts(searchable)
        central_searchable = " ".join(
            [
                source.title,
                source.catalog_summary,
                *source.search_keywords_json,
                *passage.clinical_concept_tags_json,
            ]
        )
        normalized_central = normalize_medical_text(central_searchable)
        if any(
            not any(normalize_medical_text(alias) in normalized_central for alias in requirement)
            for requirement in central_topic_requirements
        ):
            continue
        centrality_total = 0.0
        centrality_failed = False
        for intent, requirement in central_requirements:
            if any(normalize_medical_text(marker) in normalized_central for marker in requirement):
                centrality_total += 1.0
            elif intent == "measurement_tracking" and any(
                normalize_medical_text(marker) in searchable for marker in requirement
            ):
                # A passage can still be usable for tracking even when a broad
                # source title does not expose that focus. Retain it at lower
                # priority so reviewed jurisdiction-applicable evidence is not
                # silently lost after source-level metadata ranking.
                centrality_total += 0.20
            else:
                centrality_failed = True
                break
        if centrality_failed:
            continue
        centrality_score = centrality_total / max(len(central_requirements), 1)
        if any(entity not in searchable for entity in specific_entities):
            continue
        central_concepts = required_concepts & central_clinical_concepts(central_searchable)
        matched_concepts = sorted(passage_concepts & central_concepts)
        concept_coverage = len(matched_concepts) / max(len(required_concepts), 1)
        if (
            require_lexical_anchor
            and required_concepts
            and (not passage_concepts or (not central_concepts and title_lexical < 0.10))
        ):
            continue
        matched = list(dict.fromkeys([*primary_matched, *expansion_matched]))
        selected_embedding = release_embedding or passage.embedding_json
        if not matched and not selected_embedding:
            continue
        title_exact = normalize_medical_text(query) in normalized_title
        lexical = len(set(primary_matched)) / max(len(set(primary_tokens)), 1)
        expansion_lexical = len(set(expansion_matched)) / max(len(set(expansion_tokens)), 1)
        if not primary_matched and expansion_matched:
            lexical = min(
                MIN_MULTI_SOURCE_COVERAGE,
                len(set(expansion_matched)) / max(len(set(expansion_tokens)), 1),
            )
        technical_expansion_match = any(
            re.fullmatch(r"[a-z]+[a-z0-9]*", token) and any(char.isdigit() for char in token)
            for token in expansion_matched
        )
        topic_coverage = max(
            lexical,
            0.60 * expansion_lexical,
            0.35 if technical_expansion_match else 0.0,
            0.35 * concept_coverage,
        )
        if require_lexical_anchor and topic_coverage < MIN_PATIENT_LEXICAL_COVERAGE:
            continue
        dense = cosine_similarity(query_vector, selected_embedding or [])
        authority = {"A": 0.10, "B": 0.07, "C": 0.04, "D": 0.02}.get(source.authority_tier, 0.0)
        applicable_jurisdictions = tuple(source_applicable_jurisdictions.get(source.stable_id, []))
        china = (
            0.08
            if prefer_china and (source.jurisdiction == "CN" or "CN" in applicable_jurisdictions)
            else 0.0
        )
        exact = 0.15 if title_exact else 0.10 * title_lexical
        score = (
            0.45 * topic_coverage
            + 0.25 * max(dense, 0.0)
            + authority
            + china
            + exact
            + 0.12 * centrality_score
        )
        if score < 0.12:
            continue
        candidates.append(
            RetrievalCandidate(
                passage=passage,
                version=version,
                source=source,
                publisher=publisher,
                lexical_score=lexical,
                topic_coverage_score=topic_coverage,
                matched_concepts=matched_concepts,
                dense_score=dense,
                rerank_score=score,
                matched_terms=list(dict.fromkeys(matched))[:20],
                applicable_jurisdictions=applicable_jurisdictions,
                centrality_score=centrality_score,
            )
        )
    candidates.sort(
        key=lambda item: (-item.rerank_score, item.source.stable_id, item.passage.stable_id)
    )
    deduplicated: list[RetrievalCandidate] = []
    checksums: set[str] = set()
    source_counts: dict[str, int] = {}
    for candidate in candidates:
        source_id = candidate.source.stable_id
        if candidate.passage.content_checksum in checksums or source_counts.get(source_id, 0) >= 2:
            continue
        checksums.add(candidate.passage.content_checksum)
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
        deduplicated.append(candidate)
    return deduplicated


PRESENTATION_VIEW_WEIGHTS = {
    PresentationViewKind.literal: 1.0,
    PresentationViewKind.clinical_presentation: 0.70,
    PresentationViewKind.population_exposure: 0.45,
    PresentationViewKind.requested_action: 0.35,
}


def _candidate_centrally_matches_presentation(
    candidate: RetrievalCandidate,
    presentation: ClinicalPresentation,
) -> bool:
    context_groups = presentation.central_context_groups()
    symptom_groups = presentation.central_symptom_groups()
    if not context_groups and not symptom_groups:
        return False
    central_searchable = normalize_medical_text(
        " ".join(
            [
                candidate.source.title,
                candidate.source.catalog_summary,
                *candidate.source.search_keywords_json,
                *candidate.passage.clinical_concept_tags_json,
            ]
        )
    )
    if context_groups:
        if not all(
            any(normalize_medical_text(alias) in central_searchable for alias in group)
            for group in context_groups
        ):
            return False
        if not symptom_groups:
            return True
        passage_searchable = normalize_medical_text(
            " ".join([central_searchable, candidate.passage.text])
        )
        return any(
            any(normalize_medical_text(alias) in passage_searchable for alias in group)
            for group in symptom_groups
        )
    return any(
        any(normalize_medical_text(alias) in central_searchable for alias in group)
        for group in symptom_groups
    )


def _fuse_presentation_rankings(
    rankings: list[tuple[PresentationRetrievalView, list[RetrievalCandidate]]],
    presentation: ClinicalPresentation,
) -> list[RetrievalCandidate]:
    """Fuse controlled views while preserving literal-query dominance.

    Every patient candidate, including a literal-query hit, is admitted only
    when reviewed source metadata centrally represents the reported clinical
    presentation. Literal hits keep their relative order after that admission
    check; action or population vocabulary alone cannot introduce an unrelated
    source. When multiple pregnancy/exposure/trauma contexts are reported, all
    of them must be central rather than accepting a partial-context match.
    """

    literal_candidates = {
        candidate.passage.content_checksum: candidate
        for view, candidates in rankings
        if view.kind == PresentationViewKind.literal
        for candidate in candidates
    }
    literal_order = {
        candidate.passage.content_checksum: rank
        for view, candidates in rankings
        if view.kind == PresentationViewKind.literal
        for rank, candidate in enumerate(candidates)
    }
    by_checksum: dict[str, list[tuple[PresentationViewKind, int, RetrievalCandidate]]] = {}
    requires_presentation_centrality = bool(presentation.central_concept_groups())
    for view, candidates in rankings:
        for rank, candidate in enumerate(candidates, start=1):
            checksum = candidate.passage.content_checksum
            if requires_presentation_centrality and not (
                _candidate_centrally_matches_presentation(candidate, presentation)
            ):
                continue
            by_checksum.setdefault(checksum, []).append((view.kind, rank, candidate))

    fused: list[RetrievalCandidate] = []
    for checksum, observations in by_checksum.items():
        literal = literal_candidates.get(checksum)
        if literal is not None:
            # Preserve literal-query rank and scores among centrally admitted
            # evidence. Other views may confirm the hit, but cannot displace it
            # before case-specific relevance labels have clinical approval.
            fused.append(literal)
            continue
        best = max(
            (candidate for _, _, candidate in observations),
            key=lambda candidate: candidate.rerank_score,
        )
        reciprocal_rank_bonus = sum(
            PRESENTATION_VIEW_WEIGHTS[kind] / (40 + rank) for kind, rank, _ in observations
        )
        max_topic_coverage = max(candidate.topic_coverage_score for _, _, candidate in observations)
        max_centrality = max(candidate.centrality_score for _, _, candidate in observations)
        matched_terms = list(
            dict.fromkeys(
                term for _, _, candidate in observations for term in candidate.matched_terms
            )
        )[:20]
        fused.append(
            replace(
                best,
                rerank_score=0.82 * best.rerank_score + 2.0 * reciprocal_rank_bonus,
                topic_coverage_score=max_topic_coverage,
                centrality_score=max_centrality,
                matched_terms=matched_terms,
            )
        )
    return sorted(
        fused,
        key=lambda item: (
            0 if item.passage.content_checksum in literal_order else 1,
            literal_order.get(item.passage.content_checksum, 0),
            -item.rerank_score,
            item.source.stable_id,
            item.passage.stable_id,
        ),
    )


def _patient_evidence_has_topic_coverage(selected: list[RetrievalCandidate]) -> bool:
    if not selected:
        return False
    if max(item.topic_coverage_score for item in selected) >= STRONG_SINGLE_SOURCE_COVERAGE:
        return True
    covered_sources = {
        item.source.stable_id
        for item in selected
        if item.topic_coverage_score >= MIN_MULTI_SOURCE_COVERAGE
    }
    return len(covered_sources) >= 2


def retrieve(
    db: Session,
    request: DoctorResourceSearchRequest | PatientEvidenceRequest,
    *,
    audience: Literal["doctor", "patient"],
    reranker_candidate_limit: int | None = None,
    presentation: ClinicalPresentation | None = None,
) -> RetrievalResult:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    release, active_rows = _active_rows(db, audience)
    settings = get_settings()
    if release.reranker_version == RERANKER_VERSION:
        if settings.knowledge_reranker_backend != "local_baseline":
            raise ApiError(
                503, "retrieval_unavailable", "The active release reranker is not configured."
            )
    elif (
        settings.knowledge_reranker_backend != "http_service"
        or settings.knowledge_reranker_model != release.reranker_version
    ):
        raise ApiError(
            503, "retrieval_unavailable", "The active release reranker is not configured."
        )
    expanded = _expanded_terms(release, request.query)
    if audience == "patient":
        presentation = presentation or extract_clinical_presentation(request.query)
        views = presentation.retrieval_views(request.language)
    else:
        presentation = ClinicalPresentation(literal_query=request.query)
        views = (PresentationRetrievalView(PresentationViewKind.literal, request.query),)
    view_expansions = {
        view.kind: (
            expanded
            if view.kind == PresentationViewKind.literal
            else _expanded_terms(release, view.text)
        )
        for view in views
    }
    view_query_texts = [" ".join([view.text, *view_expansions[view.kind]]) for view in views]
    view_vectors = query_embeddings(view_query_texts, release.embedding_model_version)
    eligible_rows = [
        row for row in active_rows if _matches_filters(row[2], row[3], row[0], request, audience)
    ]
    prefer_china = audience == "patient" or (
        isinstance(request, DoctorResourceSearchRequest) and "CN" in request.filters.jurisdictions
    )
    applicability = release.build_results_json.get("source_applicable_jurisdictions", {})
    if not isinstance(applicability, dict):
        applicability = {}
    rankings = [
        (
            view,
            _rank_candidates(
                eligible_rows,
                view.text,
                view_expansions[view.kind],
                prefer_china=prefer_china,
                query_vector=query_vector,
                require_lexical_anchor=(
                    audience == "patient" and view.kind == PresentationViewKind.literal
                ),
                source_applicable_jurisdictions=applicability,
            ),
        )
        for view, query_vector in zip(views, view_vectors, strict=True)
    ]
    literal_ranked = next(
        candidates for view, candidates in rankings if view.kind == PresentationViewKind.literal
    )
    ranked = (
        _fuse_presentation_rankings(rankings, presentation)
        if audience == "patient"
        else literal_ranked
    )
    ranked, ranking_backend, ranking_fallback_code = _cross_encoder_rerank(
        db,
        request.query,
        ranked,
        candidate_limit_override=reranker_candidate_limit,
    )
    if audience == "patient":
        patient_ranked: list[RetrievalCandidate] = []
        patient_sources: set[str] = set()
        for candidate in ranked:
            if (
                candidate.topic_coverage_score < MIN_MULTI_SOURCE_COVERAGE
                or candidate.source.stable_id in patient_sources
            ):
                continue
            patient_sources.add(candidate.source.stable_id)
            patient_ranked.append(candidate)
        ranked = patient_ranked
    limit = request.limit if isinstance(request, DoctorResourceSearchRequest) else request.top_k
    offset = 0
    next_cursor = None
    if isinstance(request, DoctorResourceSearchRequest):
        context = _cursor_context(request, release)
        offset = _decode_cursor(request.cursor, context) if request.cursor else 0
        if offset + limit < len(ranked):
            next_cursor = _encode_cursor(context, offset + limit)
    selected = ranked[offset : offset + limit]
    conflict_keys: dict[str, set[str]] = {}
    for item in selected:
        if item.passage.conflict_group_key:
            conflict_keys.setdefault(item.passage.conflict_group_key, set()).add(
                item.source.stable_id
            )
    has_conflict = any(len(source_ids) > 1 for source_ids in conflict_keys.values())
    ranked_jurisdictions = {item.source.jurisdiction for item in ranked}
    explicit_cross_jurisdiction_conflict = (
        audience == "patient"
        and _query_has_marker(request.query, CONFLICT_QUERY_MARKERS)
        and len(ranked_jurisdictions) > 1
    )
    if audience == "patient" and _query_has_marker(request.query, STALE_QUERY_MARKERS):
        decision = (
            EvidenceDecision.stale_or_superseded_only
            if _release_has_historical_match(release, request.query, expanded)
            else EvidenceDecision.no_eligible_evidence
        )
    elif not selected:
        literal_vector = view_vectors[
            next(
                index
                for index, view in enumerate(views)
                if view.kind == PresentationViewKind.literal
            )
        ]
        stale_matches = _rank_candidates(
            [row for row in active_rows if row[2].status != "current"],
            request.query,
            expanded,
            prefer_china=prefer_china,
            query_vector=literal_vector,
            require_lexical_anchor=audience == "patient",
        )
        decision = (
            EvidenceDecision.stale_or_superseded_only
            if stale_matches
            else EvidenceDecision.no_eligible_evidence
        )
    elif has_conflict or explicit_cross_jurisdiction_conflict:
        decision = EvidenceDecision.conflicting
    elif audience == "patient" and not _patient_evidence_has_topic_coverage(selected):
        decision = EvidenceDecision.no_eligible_evidence
    else:
        decision = EvidenceDecision.sufficient
    released = selected if audience == "doctor" or decision == EvidenceDecision.sufficient else []
    latency_ms = max(0, round((time.perf_counter() - started) * 1000))
    db.add(
        KbRetrievalEvent(
            request_id=request_id,
            actor_role=audience,
            workflow="doctor_resources" if audience == "doctor" else "patient_evidence",
            query_sha256=hashlib.sha256(request.query.encode()).hexdigest(),
            query_length=len(request.query),
            filter_classes_json=_filter_classes(request),
            index_release_id=release.id,
            retrieved_source_ids_json=list(
                dict.fromkeys(item.source.stable_id for item in released)
            ),
            retrieved_passage_ids_json=[item.passage.stable_id for item in released],
            score_summary_json={
                "candidate_count": len(ranked),
                "returned_count": len(released),
                "max_score": round(ranked[0].rerank_score, 4) if ranked else None,
                "ranking_backend": ranking_backend,
                "ranking_fallback_code": ranking_fallback_code,
                "embedding_model_version": release.embedding_model_version,
                "reranker_version": release.reranker_version,
                "presentation_fusion_version": (
                    PRESENTATION_FUSION_VERSION if audience == "patient" else None
                ),
                "view_kinds": [view.kind.value for view in views],
                "literal_candidate_count": len(literal_ranked),
            },
            latency_ms=latency_ms,
            evidence_decision=decision.value,
            fallback_code=(None if decision == EvidenceDecision.sufficient else decision.value),
        )
    )
    return RetrievalResult(
        request_id=request_id,
        release=release,
        original_query=request.query,
        expanded_terms=expanded,
        candidates=released,
        ranked_candidates=ranked,
        decision=decision,
        next_cursor=next_cursor,
        ranking_backend=ranking_backend,
        ranking_fallback_code=ranking_fallback_code,
        view_kinds=tuple(view.kind.value for view in views),
        literal_candidate_count=len(literal_ranked),
        latency_ms=latency_ms,
    )


def _filter_classes(request: DoctorResourceSearchRequest | PatientEvidenceRequest) -> list[str]:
    if isinstance(request, DoctorResourceSearchRequest):
        dumped = request.filters.model_dump(mode="json")
        return [key for key, value in dumped.items() if value not in (None, [], {})]
    return [
        key
        for key in ("language", "jurisdiction", "topics", "excluded_content_types")
        if getattr(request, key) not in (None, [], {})
    ]


def _review_date(db: Session, candidate: RetrievalCandidate) -> date:
    review = db.scalar(
        select(KbReview)
        .where(
            KbReview.review_type == "medical",
            KbReview.decision == "approved",
            KbReview.target_stable_id.in_(
                [candidate.source.stable_id, candidate.version.stable_id]
            ),
        )
        .order_by(KbReview.reviewed_at.desc())
        .limit(1)
    )
    if review is None:
        raise ApiError(503, "retrieval_unavailable", "Approved evidence is missing review lineage.")
    return review.reviewed_at.date()


def _citation(db: Session, candidate: RetrievalCandidate) -> SourceCitation:
    return SourceCitation(
        source_id=candidate.source.stable_id,
        version_id=candidate.version.stable_id,
        passage_ids=[candidate.passage.stable_id],
        title=candidate.source.title,
        publisher=candidate.publisher.official_name_zh,
        official_locator=candidate.source.canonical_locator,
        jurisdiction=candidate.source.jurisdiction,
        original_language=candidate.passage.language,
        publication_date=candidate.source.publication_date,
        last_medical_review_date=_review_date(db, candidate),
        authority_tier=AuthorityTier(candidate.source.authority_tier),
        status=SourceStatus(candidate.source.status),
        patient_use_approved=candidate.source.patient_eligible,
    )


@router.post("/doctor/resources/search", response_model=DoctorResourceSearchResponse)
def search_doctor_resources(
    request: DoctorResourceSearchRequest,
    db: DbSession,
    user: CurrentUser,
) -> DoctorResourceSearchResponse:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise ApiError(403, "forbidden", "This resource is not available.")
    result = retrieve(db, request, audience="doctor")
    response = DoctorResourceSearchResponse(
        request_id=result.request_id,
        original_query=result.original_query,
        expanded_terms=result.expanded_terms,
        evidence_decision=result.decision,
        items=[
            DoctorResourceSearchItem(
                citation=_citation(db, candidate),
                matched_passage=candidate.passage.text,
                matched_terms=candidate.matched_terms,
            )
            for candidate in result.candidates
        ],
        next_cursor=result.next_cursor,
        index_release_id=result.release.stable_id,
    )
    db.commit()
    return response


@router.post("/patient/evidence", response_model=PatientEvidenceResponse)
def search_patient_evidence(
    request: PatientEvidenceRequest,
    db: DbSession,
    user: CurrentUser,
) -> PatientEvidenceResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise ApiError(403, "forbidden", "This resource is not available.")
    result = retrieve(db, request, audience="patient")
    passages = [
        EvidencePassage(
            passage_id=candidate.passage.stable_id,
            source_id=candidate.source.stable_id,
            version_id=candidate.version.stable_id,
            text=candidate.passage.text,
            language=candidate.passage.language,
            citation=_citation(db, candidate),
        )
        for candidate in result.candidates
    ]
    response = PatientEvidenceResponse(
        request_id=result.request_id,
        decision=result.decision,
        passages=passages,
        index_release_id=result.release.stable_id,
    )
    db.commit()
    return response
