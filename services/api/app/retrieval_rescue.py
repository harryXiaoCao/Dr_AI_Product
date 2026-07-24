from __future__ import annotations

import re
import time
from dataclasses import dataclass, replace
from enum import StrEnum

from sqlalchemy.orm import Session

from app.ai_chat import DeepSeekChatAdapter, DeepSeekChatError
from app.chatbot_contracts import EvidenceDecision, PatientEvidenceRequest, RetrievalQueryPlan
from app.clinical_presentation import ClinicalPresentation, extract_clinical_presentation
from app.config import Settings
from app.errors import ApiError
from app.knowledge_retrieval import (
    MIN_MULTI_SOURCE_COVERAGE,
    STRONG_SINGLE_SOURCE_COVERAGE,
    RetrievalCandidate,
    RetrievalResult,
    clinical_concepts,
    normalize_medical_text,
    relevance_tokens,
    retrieve,
)


class RescueTrigger(StrEnum):
    short_reference = "short_reference"
    colloquial = "colloquial"
    ambiguous = "ambiguous"
    weak_initial_retrieval = "weak_initial_retrieval"


class RescueOutcome(StrEnum):
    not_triggered = "not_triggered"
    disabled = "disabled"
    improved = "improved"
    clarification_needed = "clarification_needed"
    planner_timeout = "planner_timeout"
    planner_quota = "planner_quota"
    planner_unavailable = "planner_unavailable"
    malformed = "malformed"
    meaning_drift = "meaning_drift"
    retry_unavailable = "retry_unavailable"
    no_improvement = "no_improvement"
    latency_exceeded = "latency_exceeded"
    cost_exceeded = "cost_exceeded"
    budget_exceeded = "budget_exceeded"


@dataclass(frozen=True)
class RescueMetadata:
    trigger: RescueTrigger | None = None
    attempted: bool = False
    outcome: RescueOutcome = RescueOutcome.not_triggered
    planner_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit_tokens: int | None = None
    cache_miss_tokens: int | None = None
    latency_ms: int = 0
    cost_microunits: int | None = None
    retrieval_delta: float | None = None
    retry_request_id: str | None = None
    clarification_needed: bool = False
    context_dominant: bool | None = None
    resolved_topic_evidence_only: bool | None = None
    planner_latency_ms: int = 0
    retry_latency_ms: int = 0
    searched_query_variant_count: int = 1


@dataclass(frozen=True)
class RescueResult:
    retrieval: RetrievalResult
    metadata: RescueMetadata


SHORT_REFERENCE_PATTERN = re.compile(
    r"^((?:这|那)(?:个|种|项|次|份)?[\u4e00-\u9fffA-Za-z0-9]{0,8}"
    r"(?:呢|怎么样|怎么办|可以吗|是什么)?|它|这样|那样|怎么办|然后呢|还有呢|"
    r"this|that|it|this one|that one|what about (?:this|that)(?: [a-z0-9]+){0,3}|"
    r"and then)\s*[?？]?$",
    re.IGNORECASE,
)
AMBIGUOUS_PATTERN = re.compile(
    r"(怎么回事|正常吗|要紧吗|怎么办|有问题吗|怎样才算|怎么才算|这样.{0,8}可以吗|"
    r"what does this mean|is this normal|"
    r"should i worry)",
    re.IGNORECASE,
)
COLLOQUIAL_PATTERN = re.compile(
    r"(跳空|漏跳|心慌|怦怦跳|上火|发虚|脑袋发懵|喘不上气|肚子不舒服|"
    r"skipped beat|heart flutter|feel off|tummy|winded)",
    re.IGNORECASE,
)
DRIFT_BLOCK_PATTERN = re.compile(
    r"(停药|加药|减药|换药|剂量|确诊|诊断为|处方|stop medication|change dose|diagnose)",
    re.IGNORECASE,
)

CONDITION_TERMS = {
    "一氧化碳中毒",
    "乙肝",
    "低血压",
    "低血糖",
    "偏头痛",
    "内出血",
    "农药中毒",
    "哮喘",
    "子痫前期",
    "宫外孕",
    "心力衰竭",
    "心肌梗死",
    "心肌梗塞",
    "心脏病",
    "感染",
    "气道堵塞",
    "热射病",
    "肺炎",
    "肺结核",
    "胃出血",
    "脑卒中",
    "胆囊结石",
    "胰腺炎",
    "贫血",
    "高血压",
    "mastitis",
    "anemia",
    "appendicitis",
    "asthma",
    "carbon monoxide poisoning",
    "ectopic pregnancy",
    "heart attack",
    "heart failure",
    "heatstroke",
    "hepatitis b",
    "hypertension",
    "hypoglycemia",
    "hypotension",
    "infection",
    "internal bleeding",
    "migraine",
    "myocardial infarction",
    "pancreatitis",
    "pesticide poisoning",
    "pneumonia",
    "preeclampsia",
    "stroke",
    "tuberculosis",
}

CONDITION_ALIAS_GROUPS = {
    "anemia": ("贫血", "anemia"),
    "appendicitis": ("阑尾炎", "appendicitis"),
    "asthma": ("哮喘", "asthma"),
    "carbon_monoxide_poisoning": ("一氧化碳中毒", "carbon monoxide poisoning"),
    "ectopic_pregnancy": ("宫外孕", "异位妊娠", "ectopic pregnancy"),
    "heart_failure": ("心衰", "心力衰竭", "heart failure"),
    "heatstroke": ("中暑", "热射病", "heatstroke"),
    "hypertension": ("高血压", "血压高", "hypertension", "high blood pressure"),
    "hypoglycemia": ("低血糖", "hypoglycemia", "low blood sugar"),
    "hypotension": ("低血压", "血压低", "hypotension", "low blood pressure"),
    "migraine": ("偏头痛", "migraine"),
    "myocardial_infarction": (
        "心肌梗死",
        "心肌梗塞",
        "心梗",
        "heart attack",
        "myocardial infarction",
    ),
    "pancreatitis": ("胰腺炎", "pancreatitis"),
    "pesticide_poisoning": ("农药中毒", "pesticide poisoning"),
    "pneumonia": ("肺炎", "pneumonia"),
    "preeclampsia": ("子痫前期", "妊娠高血压", "preeclampsia"),
    "stroke": ("脑卒中", "中风", "stroke"),
    "tuberculosis": ("肺结核", "结核", "tuberculosis"),
}
GROUPED_CONDITION_TERMS = {term for aliases in CONDITION_ALIAS_GROUPS.values() for term in aliases}

PRESENTATION_MEANING_FIELDS = (
    "symptoms",
    "anatomy",
    "onset",
    "duration",
    "trajectory",
    "severity",
    "associated_signs",
    "measurements",
    "population",
    "pregnancy",
    "exposures",
    "trauma",
    "requested_actions",
    "danger_signals",
    "negated_concepts",
    "hypothetical_concepts",
)


def mentioned_conditions(value: str) -> set[str]:
    normalized = normalize_medical_text(value)
    grouped = {
        code
        for code, aliases in CONDITION_ALIAS_GROUPS.items()
        if any(normalize_medical_text(alias) in normalized for alias in aliases)
    }
    ungrouped = {
        term
        for term in CONDITION_TERMS - GROUPED_CONDITION_TERMS
        if normalize_medical_text(term) in normalized
    }
    return grouped | ungrouped


def _presentation_values(presentation: ClinicalPresentation, field: str) -> set[str]:
    return set(getattr(presentation, field))


def _rewrite_preserves_presentation(
    candidate: str,
    *,
    original_message: str,
    trusted_presentation: ClinicalPresentation,
    trusted_context_message: str,
) -> bool:
    required = extract_clinical_presentation(original_message)
    proposed = extract_clinical_presentation(candidate)
    for field in PRESENTATION_MEANING_FIELDS:
        proposed_values = _presentation_values(proposed, field)
        trusted_values = _presentation_values(trusted_presentation, field)
        if not proposed_values <= trusted_values:
            return False
        required_values = _presentation_values(required, field) | trusted_values
        if required_values and not required_values <= proposed_values:
            return False
    allowed_conditions = mentioned_conditions(trusted_context_message)
    proposed_conditions = mentioned_conditions(candidate)
    if not proposed_conditions <= allowed_conditions:
        return False
    required_conditions = allowed_conditions | mentioned_conditions(original_message)
    return not required_conditions or required_conditions <= proposed_conditions


def choose_trigger(
    message: str, result: RetrievalResult, settings: Settings
) -> RescueTrigger | None:
    normalized = message.strip()
    if SHORT_REFERENCE_PATTERN.fullmatch(normalized):
        return RescueTrigger.short_reference
    if len(normalized) <= 40 and AMBIGUOUS_PATTERN.search(normalized):
        presentation = extract_clinical_presentation(normalized)
        if not presentation.central_concept_groups() and not mentioned_conditions(normalized):
            return RescueTrigger.ambiguous
    max_score = max((item.rerank_score for item in result.ranked_candidates), default=0.0)
    weak = result.decision != EvidenceDecision.sufficient or (
        max_score < settings.retrieval_rescue_weak_score_threshold
    )
    if weak and COLLOQUIAL_PATTERN.search(normalized):
        return RescueTrigger.colloquial
    if weak:
        return RescueTrigger.weak_initial_retrieval
    return None


def validate_rewrite(
    plan: RetrievalQueryPlan,
    *,
    original_message: str,
    recent_user_messages: list[str],
    language: str,
    require_recent_anchor: bool = False,
    trusted_presentation: ClinicalPresentation | None = None,
    trusted_context_message: str | None = None,
) -> str | None:
    queries = _validated_queries(
        plan,
        original_message=original_message,
        recent_user_messages=recent_user_messages,
        language=language,
        require_recent_anchor=require_recent_anchor,
        trusted_presentation=trusted_presentation,
        trusted_context_message=trusted_context_message,
    )
    return queries[0] if queries else None


def _validated_queries(
    plan: RetrievalQueryPlan,
    *,
    original_message: str,
    recent_user_messages: list[str],
    language: str,
    require_recent_anchor: bool = False,
    trusted_presentation: ClinicalPresentation | None = None,
    trusted_context_message: str | None = None,
) -> list[str]:
    if plan.language != language or plan.jurisdiction != "CN" or plan.clarification_needed:
        return []
    basis = trusted_context_message or " ".join([*recent_user_messages[-1:], original_message])
    trusted_presentation = trusted_presentation or extract_clinical_presentation(basis)
    basis_concepts = clinical_concepts(basis)
    basis_tokens = set(relevance_tokens(basis))
    recent_basis = " ".join(recent_user_messages[-1:])
    recent_concepts = clinical_concepts(recent_basis)
    recent_tokens = set(relevance_tokens(recent_basis))
    accepted: list[str] = []
    for candidate in plan.candidate_queries:
        if DRIFT_BLOCK_PATTERN.search(candidate) and not DRIFT_BLOCK_PATTERN.search(basis):
            continue
        if not _rewrite_preserves_presentation(
            candidate,
            original_message=original_message,
            trusted_presentation=trusted_presentation,
            trusted_context_message=basis,
        ):
            continue
        candidate_concepts = clinical_concepts(candidate)
        if candidate_concepts - basis_concepts:
            continue
        candidate_tokens = set(relevance_tokens(candidate))
        shared_concept = bool(candidate_concepts & basis_concepts)
        shared_token = bool(candidate_tokens & basis_tokens)
        if not shared_concept and not shared_token:
            continue
        if require_recent_anchor and not (
            candidate_concepts & recent_concepts or candidate_tokens & recent_tokens
        ):
            continue
        normalized_candidate = normalize_medical_text(candidate)
        normalized_original = normalize_medical_text(original_message)
        if not normalized_candidate or normalized_candidate == normalized_original:
            continue
        accepted.append(candidate)
    return list(dict.fromkeys(accepted))[:2]


def _contextual_query(original_message: str, recent_user_messages: list[str]) -> str | None:
    previous = next((item.strip() for item in reversed(recent_user_messages) if item.strip()), None)
    if previous is None:
        return None
    remaining = 300 - len(original_message) - 1
    if remaining < 2:
        return None
    candidate = f"{previous[:remaining]} {original_message}".strip()
    if normalize_medical_text(candidate) == normalize_medical_text(original_message):
        return None
    return candidate


CONTEXT_RESOLVED_TRIGGERS = {
    RescueTrigger.short_reference,
    RescueTrigger.ambiguous,
}


def _without_evidence(result: RetrievalResult) -> RetrievalResult:
    return replace(
        result,
        candidates=[],
        ranked_candidates=[],
        decision=EvidenceDecision.no_eligible_evidence,
    )


def _fallback_for_trigger(initial: RetrievalResult, trigger: RescueTrigger) -> RetrievalResult:
    if trigger in CONTEXT_RESOLVED_TRIGGERS:
        return _without_evidence(initial)
    return initial


def _resolved_topic_quality(result: RetrievalResult) -> float:
    if result.decision != EvidenceDecision.sufficient or not result.candidates:
        return 0.0
    strong_coverage = max((item.topic_coverage_score for item in result.candidates), default=0.0)
    covered_sources = {
        item.source.stable_id
        for item in result.candidates
        if item.topic_coverage_score >= MIN_MULTI_SOURCE_COVERAGE
    }
    if strong_coverage < STRONG_SINGLE_SOURCE_COVERAGE and len(covered_sources) < 2:
        return 0.0
    return round(strong_coverage + min(len(covered_sources), 3) * 0.02, 4)


def _fuse(initial: RetrievalResult, retry: RetrievalResult, top_k: int) -> RetrievalResult:
    return _fuse_many(initial, [retry], top_k, context_authoritative=True)


def _fuse_many(
    initial: RetrievalResult,
    retries: list[RetrievalResult],
    top_k: int,
    *,
    context_authoritative: bool,
) -> RetrievalResult:
    if not retries or any(initial.release.id != retry.release.id for retry in retries):
        return _without_evidence(initial)
    result_lists = retries if context_authoritative else [initial, *retries]
    rank_scores: dict[str, float] = {}
    by_checksum: dict[str, RetrievalCandidate] = {}
    for result in result_lists:
        for rank, item in enumerate(result.ranked_candidates, start=1):
            checksum = item.passage.content_checksum
            rank_scores[checksum] = rank_scores.get(checksum, 0.0) + 1.0 / (60 + rank)
            current = by_checksum.get(checksum)
            if current is None or item.rerank_score > current.rerank_score:
                by_checksum[checksum] = item
    if context_authoritative:
        initial_ranks = {
            item.passage.content_checksum: rank
            for rank, item in enumerate(initial.ranked_candidates, start=1)
        }
        for checksum in tuple(rank_scores):
            if checksum in initial_ranks:
                rank_scores[checksum] += 0.5 / (60 + initial_ranks[checksum])
    ordered = sorted(
        by_checksum.values(),
        key=lambda item: (
            -rank_scores[item.passage.content_checksum],
            -item.rerank_score,
            item.source.stable_id,
            item.passage.stable_id,
        ),
    )
    selected: list[RetrievalCandidate] = []
    source_counts: dict[str, int] = {}
    for item in ordered:
        source_id = item.source.stable_id
        if source_counts.get(source_id, 0) >= 2:
            continue
        selected.append(item)
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
        if len(selected) >= top_k:
            break
    conflict_groups: dict[str, set[str]] = {}
    for item in selected:
        if item.passage.conflict_group_key:
            conflict_groups.setdefault(item.passage.conflict_group_key, set()).add(
                item.source.stable_id
            )
    conflicting = any(len(source_ids) > 1 for source_ids in conflict_groups.values())
    sufficient = bool(selected) and (
        max(item.topic_coverage_score for item in selected) >= STRONG_SINGLE_SOURCE_COVERAGE
        or len(
            {
                item.source.stable_id
                for item in selected
                if item.topic_coverage_score >= MIN_MULTI_SOURCE_COVERAGE
            }
        )
        >= 2
    )
    decision = (
        EvidenceDecision.conflicting
        if conflicting
        else EvidenceDecision.sufficient
        if sufficient
        else EvidenceDecision.no_eligible_evidence
    )
    return replace(
        initial,
        candidates=selected if decision == EvidenceDecision.sufficient else [],
        ranked_candidates=selected,
        decision=decision,
    )


def _cost_microunits(
    settings: Settings, input_tokens: int | None, output_tokens: int | None
) -> int | None:
    if input_tokens is None or output_tokens is None:
        return None
    return round(
        input_tokens * settings.deepseek_input_price_per_million_usd
        + output_tokens * settings.deepseek_output_price_per_million_usd
    )


def attempt_retrieval_rescue(
    db: Session,
    *,
    original_message: str,
    language: str,
    request: PatientEvidenceRequest,
    initial: RetrievalResult,
    recent_user_messages: list[str],
    trusted_presentation: ClinicalPresentation,
    trusted_context_message: str,
    settings: Settings,
    adapter: DeepSeekChatAdapter,
) -> RescueResult:
    trigger = choose_trigger(original_message, initial, settings)
    if trigger is None:
        return RescueResult(initial, RescueMetadata())
    if not settings.retrieval_rescue_enabled:
        return RescueResult(
            initial, RescueMetadata(trigger=trigger, outcome=RescueOutcome.disabled)
        )
    started = time.perf_counter()
    safe_fallback = _fallback_for_trigger(initial, trigger)
    rewritten = (
        _contextual_query(original_message, recent_user_messages)
        if trigger == RescueTrigger.short_reference
        else None
    )
    rewritten_queries = [rewritten] if rewritten is not None else []
    common: dict[str, object] = {
        "trigger": trigger,
        "attempted": True,
        "latency_ms": 0,
        "cost_microunits": 0 if rewritten is not None else None,
        "planner_latency_ms": 0,
        "retry_latency_ms": 0,
        "searched_query_variant_count": 1,
    }
    if rewritten is None:
        try:
            planned = adapter.plan_retrieval_query(
                message=original_message,
                language=language,
                excluded_content_classes=request.excluded_content_types,
                recent_user_messages=recent_user_messages,
                settings=settings,
            )
        except DeepSeekChatError as exc:
            outcome = {
                "timeout": RescueOutcome.planner_timeout,
                "quota": RescueOutcome.planner_quota,
                "malformed": RescueOutcome.malformed,
                "budget": RescueOutcome.cost_exceeded,
            }.get(exc.fallback_reason, RescueOutcome.planner_unavailable)
            return RescueResult(
                safe_fallback,
                RescueMetadata(
                    trigger=trigger,
                    attempted=True,
                    outcome=outcome,
                    latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
                ),
            )
        planner_latency_ms = max(0, round((time.perf_counter() - started) * 1000))
        cost = _cost_microunits(settings, planned.input_tokens, planned.output_tokens)
        common.update(
            planner_model=planned.model,
            input_tokens=planned.input_tokens,
            output_tokens=planned.output_tokens,
            cache_hit_tokens=planned.cache_hit_tokens,
            cache_miss_tokens=planned.cache_miss_tokens,
            latency_ms=planner_latency_ms,
            planner_latency_ms=planner_latency_ms,
            cost_microunits=cost,
        )
        if planner_latency_ms > settings.retrieval_rescue_max_latency_ms:
            return RescueResult(
                safe_fallback,
                RescueMetadata(**common, outcome=RescueOutcome.latency_exceeded),
            )
        if cost is not None and cost > settings.retrieval_rescue_max_cost_microunits:
            return RescueResult(
                safe_fallback,
                RescueMetadata(**common, outcome=RescueOutcome.cost_exceeded),
            )
        rewritten_queries = _validated_queries(
            planned.output,
            original_message=original_message,
            recent_user_messages=recent_user_messages,
            language=language,
            require_recent_anchor=trigger == RescueTrigger.ambiguous,
            trusted_presentation=trusted_presentation,
            trusted_context_message=trusted_context_message,
        )
        if not rewritten_queries and trigger == RescueTrigger.ambiguous:
            contextual = _contextual_query(original_message, recent_user_messages)
            rewritten_queries = [contextual] if contextual else []
        if planned.output.clarification_needed and not rewritten_queries:
            return RescueResult(
                safe_fallback,
                RescueMetadata(
                    **common,
                    outcome=RescueOutcome.clarification_needed,
                    clarification_needed=True,
                ),
            )
    if not rewritten_queries:
        return RescueResult(
            safe_fallback, RescueMetadata(**common, outcome=RescueOutcome.meaning_drift)
        )
    retry_started = time.perf_counter()
    retries: list[RetrievalResult] = []
    try:
        for rewritten_query in rewritten_queries:
            retries.append(
                retrieve(
                    db,
                    request.model_copy(update={"query": rewritten_query}),
                    audience="patient",
                    reranker_candidate_limit=1,
                    presentation=replace(
                        trusted_presentation,
                        literal_query=rewritten_query,
                    ),
                )
            )
    except ApiError as exc:
        if exc.code != "retrieval_unavailable":
            raise
        return RescueResult(
            safe_fallback,
            RescueMetadata(**common, outcome=RescueOutcome.retry_unavailable),
        )
    common["searched_query_variant_count"] = 1 + len(retries)
    common["retry_latency_ms"] = max(0, round((time.perf_counter() - retry_started) * 1000))
    context_authoritative = trigger in CONTEXT_RESOLVED_TRIGGERS
    fused = _fuse_many(
        initial,
        retries,
        request.top_k,
        context_authoritative=context_authoritative,
    )
    retry_checksums = {
        item.passage.content_checksum for retry in retries for item in retry.ranked_candidates
    }
    fused_checksums = {item.passage.content_checksum for item in fused.candidates}
    resolved_topic_evidence_only = bool(fused_checksums) and fused_checksums.issubset(
        retry_checksums
    )
    context_dominant = (
        resolved_topic_evidence_only if trigger in CONTEXT_RESOLVED_TRIGGERS else None
    )
    total_latency_ms = max(0, round((time.perf_counter() - started) * 1000))
    common["latency_ms"] = total_latency_ms
    if total_latency_ms > settings.retrieval_rescue_max_latency_ms:
        return RescueResult(
            safe_fallback,
            RescueMetadata(**common, outcome=RescueOutcome.latency_exceeded),
        )
    resolved_quality = _resolved_topic_quality(fused)
    initial_quality = _resolved_topic_quality(initial)
    delta = (
        resolved_quality
        if trigger in CONTEXT_RESOLVED_TRIGGERS
        else round(resolved_quality - initial_quality, 4)
    )
    if (
        not any(retry.decision == EvidenceDecision.sufficient for retry in retries)
        or resolved_quality <= 0
        or delta <= 0
    ):
        return RescueResult(
            safe_fallback,
            RescueMetadata(
                **common,
                outcome=RescueOutcome.no_improvement,
                retrieval_delta=delta,
                retry_request_id=",".join(retry.request_id for retry in retries)[:120],
                context_dominant=context_dominant,
                resolved_topic_evidence_only=resolved_topic_evidence_only,
            ),
        )
    return RescueResult(
        fused,
        RescueMetadata(
            **common,
            outcome=RescueOutcome.improved,
            retrieval_delta=delta,
            retry_request_id=",".join(retry.request_id for retry in retries)[:120],
            context_dominant=context_dominant,
            resolved_topic_evidence_only=resolved_topic_evidence_only,
        ),
    )
