import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from app.chatbot_release_governance import (
    MANDATORY_MACHINE_GATES,
    PURPOSE_CODE,
    ChatbotReleaseTransitionError,
    activate_release,
    build_release,
    chatbot_generation_readiness,
    record_kill_switch,
    rollback_release,
    supersede_release,
)
from app.config import Settings
from app.database import SessionLocal
from app.models import (
    ChatbotGenerationActiveRelease,
    ChatbotGenerationRelease,
    ChatbotGenerationReleaseEvent,
)
from app.seed import seed_database
from tests.helpers import auth_header, login

PASSING_GATES = {name: True for name in MANDATORY_MACHINE_GATES}


def _governed_settings(settings) -> Settings:
    return settings.model_copy(
        update={
            "chatbot_release_governance_bypass_for_tests": False,
            "chatbot_purpose_enabled": True,
            "chatbot_kill_switch": False,
        }
    )


def _release(
    settings: Settings,
    version: str,
    *,
    predecessor_release_id: uuid.UUID | None = None,
) -> ChatbotGenerationRelease:
    return build_release(
        settings=settings,
        version=version,
        evaluation_manifest_checksum_sha256="a" * 64,
        evaluation_result_checksum_sha256="b" * 64,
        machine_gates=PASSING_GATES,
        predecessor_release_id=predecessor_release_id,
    )


def test_chatbot_provider_is_deepseek_only_and_governance_defaults_fail_closed() -> None:
    defaults = Settings(
        _env_file=None,
        environment="test",
        jwt_secret="test-secret-value-with-enough-entropy-123",
    )
    assert defaults.chatbot_provider == "deepseek"
    assert defaults.chatbot_purpose_enabled is False
    assert defaults.chatbot_kill_switch is True
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="test",
            jwt_secret="test-secret-value-with-enough-entropy-123",
            chatbot_provider="another-provider",
        )
    staging = Settings(
        _env_file=None,
        environment="staging",
        jwt_secret="test-secret-value-with-enough-entropy-123",
        chatbot_release_governance_bypass_for_tests=True,
    )
    with SessionLocal() as db:
        assert chatbot_generation_readiness(db, staging).ready is False


def test_checksum_bound_activation_supersession_kill_switch_and_exact_rollback(
    settings,
) -> None:
    governed = _governed_settings(settings)
    with SessionLocal() as db:
        assert chatbot_generation_readiness(db, governed).code == ("blocked_no_compatible_release")
        v1 = _release(governed, "v1")
        db.add(v1)
        db.flush()
        first = activate_release(
            db,
            release=v1,
            settings=governed,
            expected_version="v1",
            idempotency_key="activate-v1",
        )
        replay = activate_release(
            db,
            release=v1,
            settings=governed,
            expected_version="v1",
            idempotency_key="activate-v1",
        )
        assert replay.id == first.id
        assert chatbot_generation_readiness(db, governed).release_id == v1.id

        v2 = _release(governed, "v2", predecessor_release_id=v1.id)
        db.add(v2)
        db.flush()
        supersede_release(
            db,
            current_release=v1,
            successor_release=v2,
            settings=governed,
            expected_current_version="v1",
            idempotency_key="supersede-v1-v2",
        )
        assert db.get(ChatbotGenerationActiveRelease, PURPOSE_CODE).release_id == v2.id

        unrelated = _release(governed, "unrelated")
        db.add(unrelated)
        db.flush()
        with pytest.raises(
            ChatbotReleaseTransitionError,
            match="exact_predecessor_required",
        ):
            rollback_release(
                db,
                current_release=v2,
                rollback_target=unrelated,
                expected_current_version="v2",
                idempotency_key="invalid-rollback",
            )
        rollback_release(
            db,
            current_release=v2,
            rollback_target=v1,
            expected_current_version="v2",
            idempotency_key="rollback-v2-v1",
        )
        assert db.get(ChatbotGenerationActiveRelease, PURPOSE_CODE).release_id == v1.id
        killed = record_kill_switch(
            db,
            active_release=v1,
            idempotency_key="kill-v1",
            reason_code="synthetic_rehearsal",
        )
        assert killed.event_type == "purpose_kill_switch_engaged"
        assert (
            chatbot_generation_readiness(
                db,
                governed.model_copy(update={"chatbot_kill_switch": True}),
            ).code
            == "kill_switched"
        )
        db.commit()

    with SessionLocal() as db:
        with pytest.raises(SQLAlchemyError, match="immutable"):
            db.execute(
                update(ChatbotGenerationRelease)
                .where(ChatbotGenerationRelease.version == "v1")
                .values(version="rewritten")
            )
            db.commit()
        db.rollback()
        event = db.query(ChatbotGenerationReleaseEvent).first()
        assert event is not None
        with pytest.raises(SQLAlchemyError, match="immutable"):
            db.execute(
                update(ChatbotGenerationReleaseEvent)
                .where(ChatbotGenerationReleaseEvent.id == event.id)
                .values(event_type="rewritten")
            )
            db.commit()


def test_checksum_or_machine_gate_drift_blocks_activation(settings) -> None:
    governed = _governed_settings(settings)
    with SessionLocal() as db:
        release = _release(governed, "drifted")
        release.machine_gates_json = {**PASSING_GATES, "privacy": False}
        release.content_checksum_sha256 = "0" * 64
        db.add(release)
        db.flush()
        with pytest.raises(
            ChatbotReleaseTransitionError,
            match="release_content_checksum_drift|mandatory_machine_gate_failed",
        ):
            activate_release(
                db,
                release=release,
                settings=governed,
                expected_version="drifted",
                idempotency_key="activate-drifted",
            )


def test_kill_switch_real_route_keeps_emergency_fallback_and_health_available(
    client,
    settings,
    monkeypatch,
) -> None:
    with SessionLocal() as db:
        seed_database(db, settings)
        db.commit()
    monkeypatch.setattr(settings, "chatbot_release_governance_bypass_for_tests", False)
    monkeypatch.setattr(settings, "chatbot_purpose_enabled", True)
    monkeypatch.setattr(settings, "chatbot_kill_switch", True)
    token = login(
        client,
        "patient.demo@example.com",
        settings.seed_patient_password.get_secret_value(),
    )
    headers = auth_header(token["access_token"])

    emergency = client.post(
        "/api/v1/patient/chat/messages",
        headers=headers,
        json={
            "message": "I have chest pain and cannot breathe.",
            "language": "en",
        },
    )
    assert emergency.status_code == 200
    assert emergency.json()["fallback_code"] == "emergency"
    assert emergency.json()["next_action_code"] == "call_120"

    def provider_must_not_run(*args, **kwargs):
        del args, kwargs
        pytest.fail("provider ran while chatbot kill switch was engaged")

    monkeypatch.setattr(
        "app.patient_chat.deepseek_chat_adapter.complete_general_knowledge",
        provider_must_not_run,
    )
    ordinary = client.post(
        "/api/v1/patient/chat/messages",
        headers=headers,
        json={
            "message": "What is blood pressure?",
            "language": "en",
        },
    )
    assert ordinary.status_code == 200
    assert ordinary.json()["grounding_mode"] == "fixed_safety_response"
    assert ordinary.json()["fallback_code"] is not None

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["patient_chat_generation"] == "kill_switched"
