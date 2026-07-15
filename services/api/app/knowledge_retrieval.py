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
from dataclasses import dataclass
from datetime import date
from typing import Literal

from fastapi import APIRouter
from sqlalchemy import and_, select
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
from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
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
    KbSourceVersion,
    KbTerm,
    UserRole,
)

router = APIRouter(prefix="/api/v1/retrieval", tags=["knowledge retrieval"])

EMBEDDING_DIMENSIONS = 96
EMBEDDING_MODEL_VERSION = "dr-ai-hashed-multilingual-v1"
LEXICAL_ANALYZER_VERSION = "dr-ai-unicode-zh-bigram-en-word-v1"
RERANKER_VERSION = "dr-ai-policy-reranker-v1"


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


def query_embedding(value: str, model_version: str) -> list[float]:
    if model_version == EMBEDDING_MODEL_VERSION:
        return embed_text(value)
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
    body = json.dumps({"model": model_version, "input": [value]}).encode()
    request = urllib.request.Request(
        settings.knowledge_embedding_service_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=settings.knowledge_embedding_timeout_seconds
        ) as response:
            payload = json.loads(response.read())
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise ApiError(
            503, "retrieval_unavailable", "The embedding service is unavailable."
        ) from exc
    embedding = (
        payload.get("embeddings", [None])[0]
        if isinstance(payload, dict) and payload.get("embeddings")
        else payload.get("data", [{}])[0].get("embedding")
        if isinstance(payload, dict) and payload.get("data")
        else None
    )
    if not isinstance(embedding, list) or not embedding:
        raise ApiError(503, "retrieval_unavailable", "The embedding response is invalid.")
    return [float(component) for component in embedding]


@dataclass(frozen=True)
class RetrievalCandidate:
    passage: KbPassage
    version: KbSourceVersion
    source: KbSource
    publisher: KbPublisher
    lexical_score: float
    dense_score: float
    rerank_score: float
    matched_terms: list[str]


@dataclass(frozen=True)
class RetrievalResult:
    request_id: str
    release: KbIndexRelease
    original_query: str
    expanded_terms: list[str]
    candidates: list[RetrievalCandidate]
    decision: EvidenceDecision
    next_cursor: str | None = None


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


def _expanded_terms(db: Session, query: str) -> list[str]:
    query_tokens = set(lexical_tokens(query))
    expansions: list[str] = []
    for term in db.scalars(select(KbTerm).where(KbTerm.review_status == "approved")):
        variants = [term.preferred_zh, term.preferred_en or "", *term.aliases_json]
        if any(query_tokens & set(lexical_tokens(variant)) for variant in variants):
            for variant in variants:
                normalized = normalize_medical_text(variant)
                if normalized and normalized not in normalize_medical_text(query):
                    expansions.append(variant)
    return list(dict.fromkeys(expansions))[:20]


def _active_rows(
    db: Session,
    audience: Literal["doctor", "patient"],
) -> tuple[KbIndexRelease, list[tuple[KbPassage, KbSourceVersion, KbSource, KbPublisher]]]:
    active = db.get(KbActiveIndexRelease, audience)
    release = db.get(KbIndexRelease, active.release_id) if active else None
    if release is None or release.status != "active":
        raise ApiError(503, "retrieval_unavailable", "No approved retrieval index is active.")
    if release.build_results_json.get("audience") != audience:
        raise ApiError(503, "retrieval_unavailable", "The active retrieval index is invalid.")
    rows = db.execute(
        select(KbPassage, KbSourceVersion, KbSource, KbPublisher)
        .join(
            KbIndexReleasePassage,
            and_(
                KbIndexReleasePassage.passage_id == KbPassage.id,
                KbIndexReleasePassage.release_id == release.id,
            ),
        )
        .join(KbSourceVersion, KbSourceVersion.id == KbPassage.version_id)
        .join(KbSource, KbSource.id == KbSourceVersion.source_id)
        .join(KbPublisher, KbPublisher.id == KbSource.publisher_id)
        .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
        .where(
            KbRightsRecord.decision_status == "approved",
            KbRightsRecord.embedding_allowed.is_(True),
            KbRightsRecord.excerpt_display_allowed.is_(True),
            KbSourceVersion.review_decision == "approved",
            KbPassage.lexical_eligible.is_(True),
            KbPassage.vector_eligible.is_(True),
            KbPassage.embedding_json.is_not(None),
        )
    ).all()
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
            or source.jurisdiction != request.jurisdiction
            or passage.language != request.language
            or (request.topics and source.topic not in request.topics)
            or source.source_type in request.excluded_content_types
        ):
            return False
    return True


def _rank_candidates(
    rows: list[tuple[KbPassage, KbSourceVersion, KbSource, KbPublisher]],
    query: str,
    expanded_terms: list[str],
    *,
    prefer_china: bool,
    query_vector: list[float],
) -> list[RetrievalCandidate]:
    query_text = " ".join([query, *expanded_terms])
    tokens = lexical_tokens(query_text)
    candidates: list[RetrievalCandidate] = []
    for passage, version, source, publisher in rows:
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
        matched = [token for token in tokens if token in searchable]
        if not matched and not passage.embedding_json:
            continue
        title_exact = normalize_medical_text(query) in normalize_medical_text(source.title)
        lexical = len(set(matched)) / max(len(set(tokens)), 1)
        dense = cosine_similarity(query_vector, passage.embedding_json or [])
        authority = {"A": 0.10, "B": 0.07, "C": 0.04, "D": 0.02}.get(source.authority_tier, 0.0)
        china = 0.08 if prefer_china and source.jurisdiction == "CN" else 0.0
        exact = 0.15 if title_exact else 0.0
        score = 0.50 * lexical + 0.30 * max(dense, 0.0) + authority + china + exact
        if score < 0.12:
            continue
        candidates.append(
            RetrievalCandidate(
                passage=passage,
                version=version,
                source=source,
                publisher=publisher,
                lexical_score=lexical,
                dense_score=dense,
                rerank_score=score,
                matched_terms=list(dict.fromkeys(matched))[:20],
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


def retrieve(
    db: Session,
    request: DoctorResourceSearchRequest | PatientEvidenceRequest,
    *,
    audience: Literal["doctor", "patient"],
) -> RetrievalResult:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    release, active_rows = _active_rows(db, audience)
    expanded = _expanded_terms(db, request.query)
    query_text = " ".join([request.query, *expanded])
    query_vector = query_embedding(query_text, release.embedding_model_version)
    eligible_rows = [
        row for row in active_rows if _matches_filters(row[2], row[3], row[0], request, audience)
    ]
    prefer_china = audience == "patient" or (
        isinstance(request, DoctorResourceSearchRequest) and "CN" in request.filters.jurisdictions
    )
    ranked = _rank_candidates(
        eligible_rows,
        request.query,
        expanded,
        prefer_china=prefer_china,
        query_vector=query_vector,
    )
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
    if not selected:
        stale_matches = _rank_candidates(
            [row for row in active_rows if row[2].status != "current"],
            request.query,
            expanded,
            prefer_china=prefer_china,
            query_vector=query_vector,
        )
        decision = (
            EvidenceDecision.stale_or_superseded_only
            if stale_matches
            else EvidenceDecision.no_eligible_evidence
        )
    elif has_conflict:
        decision = EvidenceDecision.conflicting
    elif audience == "patient" and len({item.source.stable_id for item in selected}) < 2:
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
        decision=decision,
        next_cursor=next_cursor,
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
        original_language=candidate.source.original_language,
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
