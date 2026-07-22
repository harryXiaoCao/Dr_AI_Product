from __future__ import annotations

import hashlib
import re
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.ai_chat import (
    ConversationTurn,
    DeepSeekChatAdapter,
    DeepSeekChatError,
    deepseek_chat_adapter,
)
from app.chatbot_contracts import (
    CHATBOT_POLICY_VERSION,
    CHATBOT_TOOL_SCHEMA_VERSION,
    EvidenceDecision,
    EvidencePassage,
    FallbackCode,
    NextActionCode,
    PatientChatContextCard,
    PatientChatHistory,
    PatientChatHistoryMessage,
    PatientChatRequest,
    PatientChatResponse,
    PatientChatSourceCard,
    PatientChatThreadList,
    PatientChatThreadSummary,
    PatientContextBundle,
    PatientEvidenceRequest,
    SafetyCode,
    StructuredModelOutput,
)
from app.claim_support import validate_claim_support
from app.clinical_presentation import (
    SafetyAssessment,
    UrgencyRoute,
    assess_safety,
    emergency_guidance,
    extract_clinical_presentation,
    resolve_bounded_user_continuity,
)
from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.knowledge_retrieval import _citation, retrieve
from app.knowledge_rights import assert_passages_provider_transmittable
from app.models import ChatbotEvent, ChatMessage, ChatRateLimit, ChatThread, UserRole
from app.patient_context import select_patient_context
from app.retrieval_rescue import RescueMetadata, attempt_retrieval_rescue

router = APIRouter(prefix="/api/v1/patient/chat", tags=["patient RAG chat"])

AI_THREAD_TYPE = "ai_educational"
MINIMUM_CHAT_RETENTION_DAYS = 60
CONTINUITY_MESSAGE_LIMIT = 8
deepseek_query_planner_adapter = DeepSeekChatAdapter()


class PatientChatIntent(StrEnum):
    education = "education"
    symptom_guidance = "symptom_guidance"
    medication_education = "medication_education"
    question_preparation = "question_preparation"


DIAGNOSIS_ORIENTATION_PATTERNS = (
    r"\b(diagnos(?:e|is)|what disease|what condition do i have)\b",
    r"(给我诊断|诊断我|我得了什么病|我是什么病)",
)
SYMPTOM_ORIENTATION_PATTERNS = (
    r"\b(symptom|feel(?:ing)?|pain|ache|dizz(?:y|iness)|fever|nausea|vomit|"
    r"palpitation|skipped beat|irregular heartbeat|shortness of breath|numb|weakness)\b",
    r"(心悸|心慌|漏跳|跳空|乱跳|怦怦跳|心跳(?:过快|很快|不齐|不规律)|"
    r"胸闷|气短|喘|呼吸不顺|呼吸困难|头晕|眩晕|头痛|发热|发烧|"
    r"恶心|呕吐|腹痛|腹泻|乏力|麻木|抽搐|出血|肿|疼|痛|不舒服)",
    r"(感觉|出现|经常|一直|偶尔).{0,18}(怎么回事|什么原因|正常吗|要紧吗)",
)
MEDICATION_CHANGE_PATTERNS = (
    r"\b(stop|start|increase|decrease|double|halve|change).{0,24}\b(medicine|medication|dose|drug|pill)\b",
    r"\b(can i|should i).{0,20}(take|use|continue|keep taking).{0,20}"
    r"(medicine|medication|drug|pill|antibiotic)\b",
    r"(停药|加药|减药|换药|改药|加量|减量|剂量翻倍|自己再加.{0,8}抗生素)",
    r"(药|阿司匹林|抗生素|止痛药|吸入药|打虫药).{0,48}"
    r"(停几天|不吃了|能不能停|继续吃|只在.{0,8}使用)",
    r"(能不能|可以|还能|要不要).{0,12}(直接买|吃|用|继续).{0,12}"
    r"(药|阿司匹林|抗生素|止痛药|吸入药|打虫药)",
)
MEDICATION_CONTEXT_PATTERNS = (
    r"\b(medicine|medication|drug|pill|antibiotic|aspirin|insulin)\b",
    r"(药|阿司匹林|抗生素|止痛药|吸入药|打虫药|胰岛素)",
)
PROMPT_ATTACK_PATTERNS = (
    r"\b(ignore previous|system prompt|developer message|hidden instruction|reveal prompt)\b",
    r"(忽略之前|系统提示词|开发者消息|隐藏指令|泄露提示词)",
)
UNSUPPORTED_PATTERNS = (
    r"\b(send a message|book an appointment|write to my record|place an order)\b",
    r"\b(?:\+?\d[\d -]{7,}\d)\b",
    r"(替我发消息|替我预约|写入病历|帮我下单)",
    r"(?:手机号|电话).{0,8}\d{7,}",
)
DIAGNOSTIC_ASSERTION_PATTERNS = (
    r"\b(you (?:definitely|certainly|clearly) have|this confirms|the diagnosis is)\b",
    r"(你(?:肯定|一定|明确)(?:是|得了|患有)|已经确诊|可以确诊|诊断就是|完全排除)",
)
OUTPUT_PROHIBITED_PATTERNS = (*DIAGNOSTIC_ASSERTION_PATTERNS, *MEDICATION_CHANGE_PATTERNS)
MIN_GROUNDED_ANSWER_SECTIONS = 3
MAX_GROUNDED_ANSWER_SECTIONS = 5
PERMITTED_SAFETY_CODES = {
    SafetyCode.permitted_education,
    SafetyCode.permitted_symptom_guidance,
}


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _is_symptom_oriented(message: str) -> bool:
    presentation = extract_clinical_presentation(message)
    return (
        _matches(message, DIAGNOSIS_ORIENTATION_PATTERNS)
        or _matches(message, SYMPTOM_ORIENTATION_PATTERNS)
        or bool(
            presentation.symptoms
            or presentation.pregnancy
            or presentation.exposures
            or presentation.trauma
        )
    )


def _safety_route(message: str, assessment: SafetyAssessment | None = None) -> SafetyCode:
    assessment = assessment or assess_safety(message)
    if assessment.safety_code == SafetyCode.emergency:
        return SafetyCode.emergency
    if _matches(message, PROMPT_ATTACK_PATTERNS):
        return SafetyCode.prompt_attack
    medication_change_from_presentation = bool(
        assessment.presentation
        and "medication_change" in assessment.presentation.requested_actions
        and _matches(message, MEDICATION_CONTEXT_PATTERNS)
    )
    if _matches(message, MEDICATION_CHANGE_PATTERNS) or medication_change_from_presentation:
        return SafetyCode.prohibited_medication_change
    if _is_symptom_oriented(message):
        return SafetyCode.permitted_symptom_guidance
    if _matches(message, UNSUPPORTED_PATTERNS):
        return SafetyCode.unsupported_input
    return SafetyCode.permitted_education


def _effective_urgency_route(
    safety_code: SafetyCode,
    assessment: SafetyAssessment,
) -> str:
    if safety_code == SafetyCode.emergency:
        return UrgencyRoute.emergency_120.value
    if safety_code == SafetyCode.prohibited_medication_change:
        return "prohibited_medication_change"
    return assessment.urgency_route.value


def _allowed_next_actions(urgency_route: str) -> frozenset[NextActionCode]:
    if urgency_route == UrgencyRoute.urgent_same_day.value:
        return frozenset({NextActionCode.seek_local_care})
    if urgency_route == UrgencyRoute.clinician_contact.value:
        return frozenset({NextActionCode.contact_connected_doctor, NextActionCode.seek_local_care})
    return frozenset(
        action
        for action in NextActionCode
        if action
        not in {
            NextActionCode.none,
            NextActionCode.call_120,
            NextActionCode.seek_local_care,
        }
    )


def _classify_intent(message: str) -> PatientChatIntent:
    normalized = message.casefold()
    if _is_symptom_oriented(message):
        return PatientChatIntent.symptom_guidance
    if any(term in normalized for term in ("question", "ask my doctor", "问医生", "要问")):
        return PatientChatIntent.question_preparation
    if any(term in normalized for term in ("medicine", "medication", "drug", "药物", "用药")):
        return PatientChatIntent.medication_education
    return PatientChatIntent.education


def _plan_retrieval(body: PatientChatRequest, intent: PatientChatIntent) -> PatientEvidenceRequest:
    excluded = ["clinical_guideline_doctor_only", "raw_clinical_record"]
    if intent != PatientChatIntent.medication_education:
        excluded.append("prescriber_only_medicine_content")
    return PatientEvidenceRequest(
        query=body.message,
        language=body.language,
        jurisdiction="CN",
        excluded_content_types=excluded,
    )


def _fixed_copy(language: str, code: FallbackCode) -> tuple[str, NextActionCode]:
    zh = {
        FallbackCode.emergency: (
            "这可能是紧急情况。请立即拨打 120，或尽快前往最近的急诊。Dr. AI 不能评估紧急情况。",
            NextActionCode.call_120,
        ),
        FallbackCode.prohibited_request: (
            "我不能为你诊断，也不能建议开始、停止或更改药物。你可以让我帮你整理要向医生询问的问题。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.no_eligible_evidence: (
            "目前没有足够且已批准用于患者回答的资料。我不会用模型记忆补充答案。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.conflicting_evidence: (
            "现有资料存在无法安全解释的冲突，请向已连接的医生确认。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.stale_evidence: (
            "目前只找到已过期或被取代的资料，因此不能据此回答。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.retrieval_unavailable: (
            "经审核的患者资料暂时不可用。为了安全，我不会在没有资料支持时生成医学回答。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.provider_timeout: (
            "回答服务暂时超时。没有显示未经验证的内容，请稍后重试或联系医生。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.provider_quota: (
            "回答服务暂时不可用。没有显示未经验证的内容，请稍后重试或联系医生。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.provider_unavailable: (
            "回答服务暂时不可用。没有显示未经验证的内容，请稍后重试或联系医生。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.malformed_model_output: (
            "生成的回答未通过格式检查，因此未向你显示。请稍后重试或联系医生。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.unsupported_citation: (
            "生成的回答未能由已审核资料完整支持，因此未向你显示。",
            NextActionCode.contact_connected_doctor,
        ),
        FallbackCode.policy_validation_failed: (
            "生成的回答未通过安全检查，因此未向你显示。",
            NextActionCode.contact_connected_doctor,
        ),
    }
    if language == "zh-Hans":
        return zh[code]
    en = {
        FallbackCode.emergency: (
            "This may be an emergency. Call 120 now or go to the nearest emergency "
            "department. Dr. AI cannot assess emergencies."
        ),
        FallbackCode.prohibited_request: (
            "I cannot diagnose you or advise starting, stopping, or changing medication. "
            "I can help prepare questions for your doctor."
        ),
        FallbackCode.no_eligible_evidence: (
            "There is not enough patient-approved evidence to answer safely. "
            "I will not fill the gap with model memory."
        ),
        FallbackCode.conflicting_evidence: (
            "The available evidence conflicts in a way I cannot explain safely. "
            "Please confirm with your connected doctor."
        ),
        FallbackCode.stale_evidence: (
            "Only stale or superseded evidence is available, so I cannot use it to answer."
        ),
        FallbackCode.retrieval_unavailable: (
            "Reviewed patient evidence is temporarily unavailable. "
            "I will not generate a medical answer without evidence."
        ),
        FallbackCode.provider_timeout: (
            "The answer service timed out. No unverified answer was shown; "
            "try later or contact your doctor."
        ),
        FallbackCode.provider_quota: (
            "The answer service is temporarily unavailable. No unverified answer was shown; "
            "try later or contact your doctor."
        ),
        FallbackCode.provider_unavailable: (
            "The answer service is temporarily unavailable. No unverified answer was shown; "
            "try later or contact your doctor."
        ),
        FallbackCode.malformed_model_output: (
            "The generated answer failed format checks and was not shown. "
            "Try later or contact your doctor."
        ),
        FallbackCode.unsupported_citation: (
            "The generated answer was not fully supported by reviewed evidence and was not shown."
        ),
        FallbackCode.policy_validation_failed: (
            "The generated answer failed safety checks and was not shown."
        ),
    }
    return en[code], zh[code][1]


def _provider_fallback(reason: str) -> FallbackCode:
    return {
        "timeout": FallbackCode.provider_timeout,
        "quota": FallbackCode.provider_quota,
        "service_unavailable": FallbackCode.provider_unavailable,
        "malformed": FallbackCode.malformed_model_output,
    }.get(reason, FallbackCode.provider_unavailable)


def _validate_output(
    output: StructuredModelOutput,
    evidence: list[EvidencePassage],
    patient_context: PatientContextBundle,
    language: str,
    safety_code: SafetyCode,
    urgency_route: str,
    original_message: str,
) -> tuple[FallbackCode, str] | None:
    available_ids = {item.passage_id for item in evidence}
    available_context_ids = {item.context_id for item in patient_context.items}
    if output.answer_language != language:
        return FallbackCode.policy_validation_failed, "policy_answer_language"
    if not set(output.used_patient_context_ids).issubset(available_context_ids):
        return FallbackCode.policy_validation_failed, "policy_patient_context_id"
    if safety_code == SafetyCode.permitted_symptom_guidance and (
        not output.uncertainties or output.next_action_code == NextActionCode.none
    ):
        return FallbackCode.policy_validation_failed, "policy_symptom_guidance_structure"
    if output.next_action_code not in _allowed_next_actions(urgency_route):
        return FallbackCode.policy_validation_failed, "policy_urgency_next_action"
    if (
        not MIN_GROUNDED_ANSWER_SECTIONS
        <= len(output.answer_sections)
        <= (MAX_GROUNDED_ANSWER_SECTIONS)
    ):
        return FallbackCode.policy_validation_failed, "policy_answer_section_count"
    for section in output.answer_sections:
        if not set(section.supporting_passage_ids).issubset(available_ids):
            return FallbackCode.unsupported_citation, "unsupported_passage_id"
        if _matches(section.text, OUTPUT_PROHIBITED_PATTERNS):
            return FallbackCode.policy_validation_failed, "policy_prohibited_output"
    if any(_matches(text, OUTPUT_PROHIBITED_PATTERNS) for text in output.uncertainties):
        return FallbackCode.policy_validation_failed, "policy_prohibited_uncertainty"
    claim_failure = validate_claim_support(
        output,
        evidence,
        patient_context,
        original_message=original_message,
    )
    if claim_failure is not None:
        return (
            FallbackCode.unsupported_citation,
            f"claim_support_{claim_failure.value}",
        )
    return None


def _check_rate_limit(db: DbSession, user: CurrentUser, settings: AppSettings) -> None:
    now = datetime.now(UTC)
    limit = db.get(ChatRateLimit, user.id)
    if limit is None:
        db.add(ChatRateLimit(user_id=user.id, window_start=now, message_count=1))
        return
    if (now - limit.window_start).total_seconds() >= settings.chat_rate_limit_window_seconds:
        limit.window_start = now
        limit.message_count = 1
    elif limit.message_count >= settings.chat_rate_limit_messages:
        raise ApiError(429, "rate_limited", "Patient chat is temporarily rate limited.")
    else:
        limit.message_count += 1


def _thread_summary(thread: ChatThread) -> PatientChatThreadSummary:
    last_message_at = thread.last_message_at or thread.created_at
    retention_until = thread.retention_until or (
        last_message_at + timedelta(days=MINIMUM_CHAT_RETENTION_DAYS)
    )
    return PatientChatThreadSummary(
        thread_id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        last_message_at=last_message_at,
        retention_until=retention_until,
    )


def _patient_thread(
    db: DbSession,
    *,
    patient_id: uuid.UUID,
    thread_id: str,
) -> ChatThread:
    try:
        parsed_id = uuid.UUID(thread_id)
    except ValueError as exc:
        raise ApiError(404, "not_found", "The requested resource was not found.") from exc
    thread = db.scalar(
        select(ChatThread).where(
            ChatThread.id == parsed_id,
            ChatThread.patient_id == patient_id,
            ChatThread.thread_type == AI_THREAD_TYPE,
        )
    )
    if thread is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    return thread


def _thread_for_message(
    db: DbSession,
    *,
    body: PatientChatRequest,
    user: CurrentUser,
) -> ChatThread:
    profile = user.patient_profile
    assert profile is not None
    if body.session_id:
        legacy_thread_key = (
            body.session_id
            if len(body.session_id) <= 80
            else f"legacy-{hashlib.sha256(body.session_id.encode()).hexdigest()}"
        )
        try:
            parsed_id = uuid.UUID(body.session_id)
        except ValueError:
            parsed_id = None
        if parsed_id is not None:
            existing_by_id = db.scalar(
                select(ChatThread).where(
                    ChatThread.id == parsed_id,
                    ChatThread.patient_id == profile.id,
                    ChatThread.thread_type.in_((AI_THREAD_TYPE, "educational")),
                )
            )
            if existing_by_id is not None:
                return existing_by_id
            raise ApiError(404, "not_found", "The requested resource was not found.")
        if parsed_id is None:
            # Pre-Slice-8 clients used an opaque per-page session key. Preserve that
            # compatibility, but never let it address another patient's thread.
            existing = db.scalar(
                select(ChatThread).where(
                    ChatThread.patient_id == profile.id,
                    ChatThread.thread_key == legacy_thread_key,
                    ChatThread.thread_type == AI_THREAD_TYPE,
                )
            )
            if existing is not None:
                return existing
    now = datetime.now(UTC)
    clean_title = re.sub(r"\s+", " ", body.message).strip()
    if len(clean_title) > 38:
        clean_title = f"{clean_title[:38].rstrip()}…"
    thread = ChatThread(
        patient_id=profile.id,
        created_by_user_id=user.id,
        thread_key=(legacy_thread_key if body.session_id else f"ai-{uuid.uuid4()}"),
        thread_type=AI_THREAD_TYPE,
        title=clean_title,
        created_at=now,
        last_message_at=now,
        retention_until=now + timedelta(days=MINIMUM_CHAT_RETENTION_DAYS),
    )
    db.add(thread)
    db.flush()
    return thread


def _conversation(db: DbSession, thread: ChatThread) -> list[ConversationTurn]:
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.thread_id == thread.id,
                ChatMessage.role.in_(("user", "assistant")),
                ChatMessage.content.is_not(None),
            )
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(CONTINUITY_MESSAGE_LIMIT)
        ).all()
    )
    messages.reverse()
    return [
        ConversationTurn(role=message.role, content=message.content or "") for message in messages
    ]


def _follow_up_question(
    message: str,
    language: str,
    conversation: list[ConversationTurn],
) -> str | None:
    normalized = message.casefold()
    if any(
        term in normalized
        for term in ("blood pressure", "measurement", "reading", "血压", "测量", "读数")
    ):
        candidate = (
            "这个读数是什么时候、在什么状态下测得的，你有重复测量吗？"
            if language == "zh-Hans"
            else "When and under what conditions was this reading taken, and did you repeat it?"
        )
    elif any(
        term in normalized for term in ("medicine", "medication", "dose", "药", "用药", "剂量")
    ):
        candidate = (
            "你想了解哪一种药，以及药袋或处方上哪一部分不清楚？"
            if language == "zh-Hans"
            else "Which medicine are you asking about, and what part of its label or "
            "prescription is unclear?"
        )
    elif any(
        term in normalized for term in ("symptom", "pain", "dizzy", "症状", "疼", "晕", "不舒服")
    ):
        candidate = (
            "这种不舒服从什么时候开始，最近有变重、变轻或出现新症状吗？"
            if language == "zh-Hans"
            else "When did this start, and has it become worse, improved, or changed "
            "with any new symptoms?"
        )
    else:
        return None
    previous_assistant_text = " ".join(
        turn.content for turn in conversation if turn.role == "assistant"
    )
    return None if candidate in previous_assistant_text else candidate


def _suggested_actions(
    safety_code: SafetyCode,
    next_action: NextActionCode,
    follow_up_question: str | None,
    message: str,
) -> list[NextActionCode]:
    actions: list[NextActionCode] = []
    if safety_code == SafetyCode.emergency:
        return [NextActionCode.call_120]
    if follow_up_question:
        actions.append(NextActionCode.ask_clarifying_question)
    normalized = message.casefold()
    if safety_code == SafetyCode.permitted_symptom_guidance:
        actions.append(NextActionCode.prepare_symptom_summary)
    if any(term in normalized for term in ("blood pressure", "measurement", "血压", "测量")):
        actions.extend(
            (NextActionCode.review_measurement_guidance, NextActionCode.track_measurements)
        )
    elif any(term in normalized for term in ("doctor", "question", "医生", "问题")):
        actions.append(NextActionCode.prepare_doctor_questions)
    if next_action != NextActionCode.none and next_action not in actions:
        actions = actions[:3]
        actions.append(next_action)
    return actions[:4]


def _persist_exchange(
    db: DbSession,
    *,
    thread: ChatThread,
    user: CurrentUser,
    body: PatientChatRequest,
    response: PatientChatResponse,
) -> PatientChatResponse:
    now = datetime.now(UTC)
    user_message = ChatMessage(
        thread_id=thread.id,
        patient_id=thread.patient_id,
        actor_user_id=user.id,
        role="user",
        content=body.message,
        prompt_hash=hashlib.sha256(body.message.encode()).hexdigest(),
        prompt_char_count=len(body.message),
        safety_category=response.safety_code.value,
        metadata_json={"language": body.language},
        created_at=now,
    )
    assistant_message = ChatMessage(
        thread_id=thread.id,
        patient_id=thread.patient_id,
        actor_user_id=None,
        role="assistant",
        content="\n\n".join(response.answer_sections),
        safety_category=response.safety_code.value,
        fallback_reason=response.fallback_code.value if response.fallback_code else None,
        model=response.model_version,
        metadata_json={"patient_chat_response": response.model_dump(mode="json")},
        created_at=now + timedelta(microseconds=1),
    )
    thread.last_message_at = now
    thread.retention_until = now + timedelta(days=MINIMUM_CHAT_RETENTION_DAYS)
    db.add_all((user_message, assistant_message))
    db.commit()
    return response


def _observe(
    db: DbSession,
    *,
    request_id: str,
    message: str,
    safety_code: SafetyCode,
    started: float,
    evidence_decision: EvidenceDecision | None = None,
    evidence: list[EvidencePassage] | None = None,
    index_release_id: str | None = None,
    fallback_code: FallbackCode | None = None,
    model_version: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    provider_error_code: str | None = None,
    provider_attempt_count: int | None = None,
    provider_cost_microunits: int | None = None,
    rescue: RescueMetadata | None = None,
) -> None:
    evidence = evidence or []
    rescue = rescue or RescueMetadata()
    db.add(
        ChatbotEvent(
            request_id=request_id,
            actor_role="patient",
            workflow="patient_chat",
            query_sha256=hashlib.sha256(message.encode()).hexdigest(),
            query_length=len(message),
            index_release_id=index_release_id,
            retrieved_source_ids_json=list(dict.fromkeys(item.source_id for item in evidence)),
            retrieved_passage_ids_json=[item.passage_id for item in evidence],
            evidence_decision=evidence_decision.value if evidence_decision else None,
            model_version=model_version,
            policy_version=CHATBOT_POLICY_VERSION,
            tool_schema_version=CHATBOT_TOOL_SCHEMA_VERSION,
            safety_code=safety_code.value,
            fallback_code=fallback_code.value if fallback_code else None,
            latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
            provider_input_tokens=input_tokens,
            provider_output_tokens=output_tokens,
            provider_error_code=provider_error_code,
            provider_attempt_count=provider_attempt_count,
            provider_cost_microunits=provider_cost_microunits,
            rescue_trigger=rescue.trigger.value if rescue.trigger else None,
            rescue_attempted=rescue.attempted,
            rescue_outcome=rescue.outcome.value if rescue.trigger else None,
            rescue_planner_model=rescue.planner_model,
            rescue_input_tokens=rescue.input_tokens,
            rescue_output_tokens=rescue.output_tokens,
            rescue_cache_hit_tokens=rescue.cache_hit_tokens,
            rescue_cache_miss_tokens=rescue.cache_miss_tokens,
            rescue_latency_ms=rescue.latency_ms if rescue.attempted else None,
            rescue_cost_microunits=rescue.cost_microunits,
            rescue_retrieval_delta=rescue.retrieval_delta,
            rescue_retry_request_id=rescue.retry_request_id,
        )
    )
    db.commit()


def _provider_cost_microunits(
    settings: AppSettings, input_tokens: int | None, output_tokens: int | None
) -> int | None:
    if input_tokens is None or output_tokens is None:
        return None
    return round(
        input_tokens * settings.deepseek_input_price_per_million_usd
        + output_tokens * settings.deepseek_output_price_per_million_usd
    )


def _fallback_response(
    request: PatientChatRequest,
    request_id: str,
    session_id: str,
    safety_code: SafetyCode,
    fallback_code: FallbackCode,
    *,
    urgency_route: str,
    evidence_decision: EvidenceDecision | None = None,
    clarification_needed: bool = False,
    emergency_guidance_code: str | None = None,
) -> PatientChatResponse:
    text, next_action = _fixed_copy(request.language, fallback_code)
    if fallback_code == FallbackCode.emergency:
        text = emergency_guidance(request.language, emergency_guidance_code)
    elif urgency_route == UrgencyRoute.urgent_same_day.value:
        timing_copy = (
            "这组表现需要当天尽快到线下医疗点评估；如果途中明显加重，请立即拨打120。"
            if request.language == "zh-Hans"
            else "This presentation needs in-person assessment today. If it clearly worsens "
            "on the way, call 120 immediately."
        )
        text = f"{timing_copy}\n\n{text}"
        next_action = NextActionCode.seek_local_care
    elif urgency_route == UrgencyRoute.clinician_contact.value:
        next_action = NextActionCode.contact_connected_doctor
    limitation = (
        "Dr. AI 是 AI 助手，可能会出错；重要信息请通过权威来源或医生核实。"
        if request.language == "zh-Hans"
        else "Dr. AI is an AI assistant and can make mistakes. Verify important details "
        "with authoritative sources or a qualified clinician."
    )
    clarification = None
    if clarification_needed:
        clarification = (
            "你具体想了解哪种症状、检查结果或健康问题？"
            if request.language == "zh-Hans"
            else "Which symptom, test result, or health topic do you mean?"
        )
    return PatientChatResponse(
        request_id=request_id,
        session_id=session_id,
        answer_language=request.language,
        answer_sections=[text],
        limitation=limitation,
        next_action_code=next_action,
        safety_code=safety_code,
        urgency_route=urgency_route,
        evidence_decision=evidence_decision,
        fallback_code=fallback_code,
        emergency=fallback_code == FallbackCode.emergency,
        follow_up_question=clarification,
        suggested_action_codes=_suggested_actions(
            safety_code,
            next_action,
            None,
            request.message,
        ),
    )


@router.get("/threads", response_model=PatientChatThreadList)
def list_patient_chat_threads(user: CurrentUser, db: DbSession) -> PatientChatThreadList:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    threads = db.scalars(
        select(ChatThread)
        .where(
            ChatThread.patient_id == user.patient_profile.id,
            ChatThread.thread_type == AI_THREAD_TYPE,
        )
        .order_by(ChatThread.last_message_at.desc(), ChatThread.created_at.desc())
    ).all()
    return PatientChatThreadList(items=[_thread_summary(thread) for thread in threads])


@router.get("/threads/{thread_id}", response_model=PatientChatHistory)
def get_patient_chat_thread(
    thread_id: str,
    user: CurrentUser,
    db: DbSession,
) -> PatientChatHistory:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    thread = _patient_thread(db, patient_id=user.patient_profile.id, thread_id=thread_id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread.id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    ).all()
    history = []
    for message in messages:
        if message.role not in {"user", "assistant"} or message.content is None:
            continue
        response_payload = message.metadata_json.get("patient_chat_response")
        history.append(
            PatientChatHistoryMessage(
                message_id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                response=(
                    PatientChatResponse.model_validate(response_payload)
                    if isinstance(response_payload, dict)
                    else None
                ),
            )
        )
    return PatientChatHistory(thread=_thread_summary(thread), messages=history)


@router.post("/messages", response_model=PatientChatResponse)
def send_patient_chat_message(
    body: PatientChatRequest,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> PatientChatResponse:
    if user.role != UserRole.patient or user.patient_profile is None:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    thread = _thread_for_message(db, body=body, user=user)
    conversation = _conversation(db, thread)
    thread_id = str(thread.id)
    started = time.perf_counter()
    request_id = request.state.request_id
    continuity = resolve_bounded_user_continuity(
        body.message,
        tuple(turn.content for turn in conversation if turn.role == "user"),
    )
    continuity_message = continuity.analysis_message
    safety_assessment = assess_safety(continuity_message)
    if safety_assessment.presentation is not None and continuity_message != body.message:
        safety_assessment = replace(
            safety_assessment,
            presentation=replace(
                safety_assessment.presentation,
                literal_query=body.message,
            ),
        )
    safety_code = _safety_route(continuity_message, safety_assessment)
    urgency_route = _effective_urgency_route(safety_code, safety_assessment)
    if safety_code == SafetyCode.emergency:
        fallback = FallbackCode.emergency
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            fallback_code=fallback,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
                emergency_guidance_code=safety_assessment.guidance_code,
            ),
        )
    if safety_code not in PERMITTED_SAFETY_CODES:
        fallback = FallbackCode.prohibited_request
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            fallback_code=fallback,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
            ),
        )

    _check_rate_limit(db, user, settings)
    intent = _classify_intent(continuity_message)
    patient_context = select_patient_context(
        db,
        profile=user.patient_profile,
        message=continuity_message,
        settings=settings,
    )
    evidence_request = _plan_retrieval(body, intent)
    try:
        result = retrieve(
            db,
            evidence_request,
            audience="patient",
            presentation=safety_assessment.presentation,
        )
    except ApiError as exc:
        if exc.code != "retrieval_unavailable":
            raise
        fallback = FallbackCode.retrieval_unavailable
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            fallback_code=fallback,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
            ),
        )

    recent_user_messages = [turn.content for turn in conversation if turn.role == "user"]
    bounded_rescue_context = (
        recent_user_messages[-1:] if continuity.carried_previous_user_turn else []
    )
    assert safety_assessment.presentation is not None
    rescue_result = attempt_retrieval_rescue(
        db,
        original_message=body.message,
        language=body.language,
        request=evidence_request,
        initial=result,
        recent_user_messages=bounded_rescue_context,
        trusted_presentation=safety_assessment.presentation,
        trusted_context_message=continuity_message,
        settings=settings,
        adapter=deepseek_query_planner_adapter,
    )
    result = rescue_result.retrieval
    rescue = rescue_result.metadata

    evidence = [
        EvidencePassage(
            passage_id=item.passage.stable_id,
            source_id=item.source.stable_id,
            version_id=item.version.stable_id,
            text=item.passage.text,
            language=item.passage.language,
            citation=_citation(db, item),
        )
        for item in result.candidates
    ]
    decision_fallback = {
        EvidenceDecision.no_eligible_evidence: FallbackCode.no_eligible_evidence,
        EvidenceDecision.conflicting: FallbackCode.conflicting_evidence,
        EvidenceDecision.stale_or_superseded_only: FallbackCode.stale_evidence,
    }
    if result.decision != EvidenceDecision.sufficient:
        fallback = decision_fallback[result.decision]
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            evidence_decision=result.decision,
            index_release_id=result.release.stable_id,
            fallback_code=fallback,
            rescue=rescue,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
                evidence_decision=result.decision,
                clarification_needed=rescue.clarification_needed,
            ),
        )

    try:
        assert_passages_provider_transmittable(db, [item.passage_id for item in evidence])
    except PermissionError:
        fallback = FallbackCode.retrieval_unavailable
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            evidence_decision=result.decision,
            index_release_id=result.release.stable_id,
            fallback_code=fallback,
            rescue=rescue,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
                evidence_decision=result.decision,
            ),
        )

    try:
        provider = deepseek_chat_adapter.complete_grounded(
            message=body.message,
            language=body.language,
            response_mode=safety_code.value,
            urgency_route=urgency_route,
            evidence=evidence,
            patient_context=patient_context,
            conversation=conversation,
            settings=settings,
        )
    except DeepSeekChatError as exc:
        fallback = _provider_fallback(exc.fallback_reason)
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            evidence_decision=result.decision,
            evidence=evidence,
            index_release_id=result.release.stable_id,
            fallback_code=fallback,
            provider_error_code=exc.diagnostic_code,
            provider_attempt_count=exc.attempt_count,
            rescue=rescue,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback,
                urgency_route=urgency_route,
                evidence_decision=result.decision,
            ),
        )

    validation_failure = _validate_output(
        provider.output,
        evidence,
        patient_context,
        body.language,
        safety_code,
        urgency_route,
        body.message,
    )
    if validation_failure is not None:
        fallback_code, validation_diagnostic = validation_failure
        _observe(
            db,
            request_id=request_id,
            message=body.message,
            safety_code=safety_code,
            started=started,
            evidence_decision=result.decision,
            evidence=evidence,
            index_release_id=result.release.stable_id,
            fallback_code=fallback_code,
            model_version=provider.model,
            input_tokens=provider.input_tokens,
            output_tokens=provider.output_tokens,
            provider_attempt_count=provider.attempt_count,
            provider_cost_microunits=_provider_cost_microunits(
                settings, provider.input_tokens, provider.output_tokens
            ),
            provider_error_code=validation_diagnostic,
            rescue=rescue,
        )
        return _persist_exchange(
            db,
            thread=thread,
            user=user,
            body=body,
            response=_fallback_response(
                body,
                request_id,
                thread_id,
                safety_code,
                fallback_code,
                urgency_route=urgency_route,
                evidence_decision=result.decision,
            ),
        )

    cited_ids = list(
        dict.fromkeys(
            passage_id
            for section in provider.output.answer_sections
            for passage_id in section.supporting_passage_ids
        )
    )
    evidence_by_id = {item.passage_id: item for item in evidence}
    context_by_id = {item.context_id: item for item in patient_context.items}
    sources = [
        PatientChatSourceCard(
            number=index,
            passage_id=passage_id,
            title=evidence_by_id[passage_id].citation.title,
            publisher=evidence_by_id[passage_id].citation.publisher,
            publication_date=evidence_by_id[passage_id].citation.publication_date,
            last_medical_review_date=evidence_by_id[passage_id].citation.last_medical_review_date,
            official_locator=evidence_by_id[passage_id].citation.official_locator,
        )
        for index, passage_id in enumerate(cited_ids, start=1)
    ]
    context_cards = []
    seen_context_cards = set()
    for context_id in provider.output.used_patient_context_ids:
        item = context_by_id[context_id]
        card_key = (item.category, item.provenance, item.recorded_on)
        if card_key in seen_context_cards:
            continue
        seen_context_cards.add(card_key)
        context_cards.append(
            PatientChatContextCard(
                category=item.category,
                provenance=item.provenance,
                recorded_on=item.recorded_on,
            )
        )
    _observe(
        db,
        request_id=request_id,
        message=body.message,
        safety_code=safety_code,
        started=started,
        evidence_decision=result.decision,
        evidence=evidence,
        index_release_id=result.release.stable_id,
        model_version=provider.model,
        input_tokens=provider.input_tokens,
        output_tokens=provider.output_tokens,
        provider_attempt_count=provider.attempt_count,
        provider_cost_microunits=_provider_cost_microunits(
            settings, provider.input_tokens, provider.output_tokens
        ),
        rescue=rescue,
    )
    follow_up_question = _follow_up_question(body.message, body.language, conversation)
    response = PatientChatResponse(
        request_id=request_id,
        session_id=thread_id,
        answer_language=body.language,
        answer_sections=[section.text for section in provider.output.answer_sections],
        sources=sources,
        context_used=context_cards,
        uncertainties=provider.output.uncertainties,
        limitation=(
            "Dr. AI 是 AI 助手，可能会出错；重要信息请通过权威来源或医生核实。"
            if body.language == "zh-Hans"
            else "Dr. AI is an AI assistant and can make mistakes. Verify important details "
            "with authoritative sources or a qualified clinician."
        ),
        next_action_code=provider.output.next_action_code,
        safety_code=safety_code,
        urgency_route=urgency_route,
        evidence_decision=result.decision,
        model_version=provider.model,
        suggested_action_codes=_suggested_actions(
            safety_code,
            provider.output.next_action_code,
            follow_up_question,
            body.message,
        ),
        follow_up_question=follow_up_question,
    )
    return _persist_exchange(db, thread=thread, user=user, body=body, response=response)
