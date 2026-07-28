"""Checksum-bound release governance for the patient-chat generation purpose."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.chatbot_contracts import (
    CHATBOT_POLICY_VERSION,
    CHATBOT_TOOL_SCHEMA_VERSION,
    GeneralModelOutput,
    StructuredModelOutput,
)
from app.config import Settings
from app.models import (
    ChatbotGenerationActiveRelease,
    ChatbotGenerationRelease,
    ChatbotGenerationReleaseEvent,
)

PURPOSE_CODE = "patient_chat_generated_answer"
RELEASE_KEY = "patient-chat-generated-answer"
PURPOSE_CONTRACT_VERSION = "patient-chat-generated-answer-purpose.v1"
PROMPT_VERSION = "patient-chat-deepseek-prompts.v1"
MANDATORY_MACHINE_GATES = frozenset(
    {
        "bilingual",
        "privacy",
        "injection",
        "malformed_output",
        "timeout",
        "quota",
        "outage",
        "context_drift",
        "cross_patient",
        "kill_switch",
        "rollback",
    }
)


class ChatbotReleaseTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class ChatbotReadiness:
    ready: bool
    code: str
    release_id: uuid.UUID | None = None
    release_version: str | None = None


def _checksum(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def chatbot_contract_checksum(settings: Settings) -> str:
    return _checksum(
        {
            "purpose_code": PURPOSE_CODE,
            "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
            "policy_version": CHATBOT_POLICY_VERSION,
            "tool_schema_version": CHATBOT_TOOL_SCHEMA_VERSION,
            "grounded_schema_version": settings.chatbot_grounded_answer_schema_version,
            "general_schema_version": settings.chatbot_general_answer_schema_version,
            "grounded_output_schema": StructuredModelOutput.model_json_schema(),
            "general_output_schema": GeneralModelOutput.model_json_schema(),
        }
    )


def release_content_checksum(release: ChatbotGenerationRelease) -> str:
    return _checksum(
        {
            "predecessor_release_id": (
                str(release.predecessor_release_id)
                if release.predecessor_release_id is not None
                else None
            ),
            "release_key": release.release_key,
            "version": release.version,
            "purpose_code": release.purpose_code,
            "purpose_contract_version": release.purpose_contract_version,
            "grounded_schema_version": release.grounded_schema_version,
            "general_schema_version": release.general_schema_version,
            "prompt_version": release.prompt_version,
            "provider": release.provider,
            "model": release.model,
            "contract_checksum_sha256": release.contract_checksum_sha256,
            "evaluation_manifest_checksum_sha256": (release.evaluation_manifest_checksum_sha256),
            "evaluation_result_checksum_sha256": (release.evaluation_result_checksum_sha256),
            "machine_gates": release.machine_gates_json,
        }
    )


def build_release(
    *,
    settings: Settings,
    version: str,
    evaluation_manifest_checksum_sha256: str,
    evaluation_result_checksum_sha256: str,
    machine_gates: dict[str, bool],
    predecessor_release_id: uuid.UUID | None = None,
) -> ChatbotGenerationRelease:
    release = ChatbotGenerationRelease(
        predecessor_release_id=predecessor_release_id,
        release_key=RELEASE_KEY,
        version=version,
        purpose_code=PURPOSE_CODE,
        purpose_contract_version=PURPOSE_CONTRACT_VERSION,
        grounded_schema_version=settings.chatbot_grounded_answer_schema_version,
        general_schema_version=settings.chatbot_general_answer_schema_version,
        prompt_version=PROMPT_VERSION,
        provider=settings.chatbot_provider,
        model=settings.deepseek_model,
        contract_checksum_sha256=chatbot_contract_checksum(settings),
        evaluation_manifest_checksum_sha256=evaluation_manifest_checksum_sha256,
        evaluation_result_checksum_sha256=evaluation_result_checksum_sha256,
        machine_gates_json=dict(machine_gates),
        content_checksum_sha256="pending",
    )
    release.content_checksum_sha256 = release_content_checksum(release)
    return release


def verify_compatible_release(
    release: ChatbotGenerationRelease,
    settings: Settings,
) -> None:
    if (
        release.release_key != RELEASE_KEY
        or release.purpose_code != PURPOSE_CODE
        or release.purpose_contract_version != PURPOSE_CONTRACT_VERSION
        or release.grounded_schema_version != settings.chatbot_grounded_answer_schema_version
        or release.general_schema_version != settings.chatbot_general_answer_schema_version
        or release.prompt_version != PROMPT_VERSION
        or release.provider != "deepseek"
        or release.provider != settings.chatbot_provider
        or release.model != settings.deepseek_model
    ):
        raise ChatbotReleaseTransitionError("purpose_or_runtime_incompatible")
    if release.contract_checksum_sha256 != chatbot_contract_checksum(settings):
        raise ChatbotReleaseTransitionError("contract_checksum_drift")
    if release.content_checksum_sha256 != release_content_checksum(release):
        raise ChatbotReleaseTransitionError("release_content_checksum_drift")
    gates = release.machine_gates_json
    if set(gates) != MANDATORY_MACHINE_GATES or not all(
        gates.get(name) is True for name in MANDATORY_MACHINE_GATES
    ):
        raise ChatbotReleaseTransitionError("mandatory_machine_gate_failed")
    for value in (
        release.evaluation_manifest_checksum_sha256,
        release.evaluation_result_checksum_sha256,
    ):
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ChatbotReleaseTransitionError("evaluation_checksum_invalid")


def chatbot_generation_readiness(
    session: Session,
    settings: Settings,
) -> ChatbotReadiness:
    if settings.environment == "test" and settings.chatbot_release_governance_bypass_for_tests:
        return ChatbotReadiness(True, "ready_test_bypass")
    if not settings.chatbot_purpose_enabled:
        return ChatbotReadiness(False, "disabled")
    if settings.chatbot_kill_switch:
        return ChatbotReadiness(False, "kill_switched")
    pointer = session.get(ChatbotGenerationActiveRelease, PURPOSE_CODE)
    if pointer is None:
        return ChatbotReadiness(False, "blocked_no_compatible_release")
    release = session.get(ChatbotGenerationRelease, pointer.release_id)
    if release is None:
        return ChatbotReadiness(False, "blocked_no_compatible_release")
    try:
        verify_compatible_release(release, settings)
    except ChatbotReleaseTransitionError:
        return ChatbotReadiness(False, "blocked_incompatible_release")
    return ChatbotReadiness(True, "ready", release.id, release.version)


def _lock(session: Session) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"chatbot-generation-release:{PURPOSE_CODE}"},
    )


def _append_event(
    session: Session,
    *,
    event_type: str,
    idempotency_key: str,
    release_id: uuid.UUID | None,
    target_release_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    evidence: dict[str, object],
) -> ChatbotGenerationReleaseEvent:
    payload = {
        **evidence,
        "content_free_readiness_evidence": True,
    }
    checksum = _checksum(
        {
            "event_type": event_type,
            "release_id": str(release_id) if release_id else None,
            "target_release_id": str(target_release_id) if target_release_id else None,
            "evidence": payload,
        }
    )
    existing = session.scalar(
        select(ChatbotGenerationReleaseEvent).where(
            ChatbotGenerationReleaseEvent.purpose_code == PURPOSE_CODE,
            ChatbotGenerationReleaseEvent.event_type == event_type,
            ChatbotGenerationReleaseEvent.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if (
            existing.release_id != release_id
            or existing.target_release_id != target_release_id
            or existing.evidence_json != payload
            or existing.content_checksum_sha256 != checksum
        ):
            raise ChatbotReleaseTransitionError("idempotency_content_conflict")
        return existing
    event = ChatbotGenerationReleaseEvent(
        purpose_code=PURPOSE_CODE,
        release_id=release_id,
        target_release_id=target_release_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        idempotency_key=idempotency_key,
        evidence_json=payload,
        content_checksum_sha256=checksum,
    )
    session.add(event)
    session.flush()
    return event


def activate_release(
    session: Session,
    *,
    release: ChatbotGenerationRelease,
    settings: Settings,
    expected_version: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None = None,
) -> ChatbotGenerationReleaseEvent:
    _lock(session)
    if release.version != expected_version:
        raise ChatbotReleaseTransitionError("expected_version_conflict")
    verify_compatible_release(release, settings)
    pointer = session.get(ChatbotGenerationActiveRelease, PURPOSE_CODE)
    if pointer is not None and pointer.release_id != release.id:
        raise ChatbotReleaseTransitionError("conflicting_active_release")
    if pointer is None:
        pointer = ChatbotGenerationActiveRelease(
            purpose_code=PURPOSE_CODE,
            release_id=release.id,
            activated_at=datetime.now(UTC),
        )
        session.add(pointer)
    return _append_event(
        session,
        event_type="release_activated",
        idempotency_key=idempotency_key,
        release_id=release.id,
        target_release_id=None,
        actor_user_id=actor_user_id,
        evidence={
            "expected_version": expected_version,
            "content_checksum_sha256": release.content_checksum_sha256,
        },
    )


def supersede_release(
    session: Session,
    *,
    current_release: ChatbotGenerationRelease,
    successor_release: ChatbotGenerationRelease,
    settings: Settings,
    expected_current_version: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None = None,
) -> ChatbotGenerationReleaseEvent:
    _lock(session)
    pointer = session.get(ChatbotGenerationActiveRelease, PURPOSE_CODE)
    if (
        current_release.version != expected_current_version
        or pointer is None
        or pointer.release_id != current_release.id
    ):
        raise ChatbotReleaseTransitionError("expected_active_release_conflict")
    if successor_release.predecessor_release_id != current_release.id:
        raise ChatbotReleaseTransitionError("predecessor_mismatch")
    verify_compatible_release(successor_release, settings)
    pointer.release_id = successor_release.id
    pointer.activated_at = datetime.now(UTC)
    return _append_event(
        session,
        event_type="release_superseded",
        idempotency_key=idempotency_key,
        release_id=current_release.id,
        target_release_id=successor_release.id,
        actor_user_id=actor_user_id,
        evidence={"expected_current_version": expected_current_version},
    )


def rollback_release(
    session: Session,
    *,
    current_release: ChatbotGenerationRelease,
    rollback_target: ChatbotGenerationRelease,
    expected_current_version: str,
    idempotency_key: str,
    actor_user_id: uuid.UUID | None = None,
) -> ChatbotGenerationReleaseEvent:
    _lock(session)
    pointer = session.get(ChatbotGenerationActiveRelease, PURPOSE_CODE)
    if (
        current_release.version != expected_current_version
        or pointer is None
        or pointer.release_id != current_release.id
    ):
        raise ChatbotReleaseTransitionError("expected_active_release_conflict")
    if current_release.predecessor_release_id != rollback_target.id:
        raise ChatbotReleaseTransitionError("exact_predecessor_required")
    pointer.release_id = rollback_target.id
    pointer.activated_at = datetime.now(UTC)
    return _append_event(
        session,
        event_type="release_rolled_back",
        idempotency_key=idempotency_key,
        release_id=current_release.id,
        target_release_id=rollback_target.id,
        actor_user_id=actor_user_id,
        evidence={"expected_current_version": expected_current_version},
    )


def record_kill_switch(
    session: Session,
    *,
    active_release: ChatbotGenerationRelease | None,
    idempotency_key: str,
    reason_code: str,
    actor_user_id: uuid.UUID | None = None,
) -> ChatbotGenerationReleaseEvent:
    _lock(session)
    return _append_event(
        session,
        event_type="purpose_kill_switch_engaged",
        idempotency_key=idempotency_key,
        release_id=active_release.id if active_release else None,
        target_release_id=None,
        actor_user_id=actor_user_id,
        evidence={"reason_code": reason_code},
    )
