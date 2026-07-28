import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.expected_care_release_operations import (
    ExplanationReleaseTransitionError,
    activate_release,
    effective_active_release_id,
    engage_purpose_kill_switch,
    mark_release_unsuitable,
    register_early_stage_waivers,
    rollback_release,
    supersede_release,
)
from app.models import (
    ExpectedCareExplanationRelease,
    ExpectedCareExplanationReleaseEvent,
)

REVIEWS = [
    {"review_type": value, "status": "pending"}
    for value in ("clinical", "pricing", "privacy", "security", "legal", "regulatory")
]
WAIVERS = {str(value["review_type"]): "product_owner_waived_for_current_stage" for value in REVIEWS}
CHECKSUMS = {
    "explanation_source_sha256": "1" * 64,
    "comparison_source_sha256": "2" * 64,
    "output_schema_sha256": "3" * 64,
}


def _release(
    *,
    version: str,
    predecessor_id: uuid.UUID | None = None,
    rollback_target_id: uuid.UUID | None = None,
) -> ExpectedCareExplanationRelease:
    return ExpectedCareExplanationRelease(
        predecessor_release_id=predecessor_id,
        rollback_target_release_id=rollback_target_id,
        release_key="expected-care-role-explanation-operation-test",
        version=version,
        purpose_code="expected_care_role_explanation",
        purpose_contract_version="expected-care-role-explanation-purpose.v2",
        schema_version="expected-care-role-explanation-claim-graph.v2",
        prompt_version="expected-care-role-explanation-prompt.v3",
        model_configuration_version="expected-care-role-explanation-deepseek.v1",
        provider="deepseek",
        model="deepseek-v4-flash",
        source_checksums_json=CHECKSUMS,
        evaluation_manifest_checksum_sha256="4" * 64,
        evaluation_result_checksum_sha256="5" * 64,
        review_requirements_json=REVIEWS,
        machine_gates_json={"schema": True, "exactness": True, "authorization": True},
        activation_state="pending",
        kill_switch_state="on",
    )


def _activate(db, release, key):
    return activate_release(
        db,
        release=release,
        expected_version=release.version,
        actor_user_id=None,
        idempotency_key=key,
        expected_source_checksums=CHECKSUMS,
        purpose_code=release.purpose_code,
        purpose_contract_version=release.purpose_contract_version,
        schema_version=release.schema_version,
        prompt_version=release.prompt_version,
        model_configuration_version=release.model_configuration_version,
        rollback_target=(
            str(release.rollback_target_release_id)
            if release.rollback_target_release_id is not None
            else "fixed_structured_fallback"
        ),
    )


def test_append_only_transition_conflict_drift_kill_switch_and_exact_rollback() -> None:
    with SessionLocal() as db:
        v3 = _release(version="v3")
        db.add(v3)
        db.flush()
        v4 = _release(
            version="v4",
            predecessor_id=v3.id,
            rollback_target_id=v3.id,
        )
        db.add(v4)
        db.flush()
        for release in (v3, v4):
            register_early_stage_waivers(
                db,
                release=release,
                expected_version=release.version,
                actor_user_id=None,
                idempotency_key=f"waiver-{release.version}",
                statuses=WAIVERS,
            )
        first = _activate(db, v3, "activate-v3")
        replay = _activate(db, v3, "activate-v3")
        assert replay.idempotent_replay is True
        assert replay.event.id == first.event.id
        with pytest.raises(ExplanationReleaseTransitionError, match="conflicting_active_release"):
            _activate(db, v4, "activate-v4-conflict")
        with pytest.raises(ExplanationReleaseTransitionError, match="release_checksum_drift"):
            activate_release(
                db,
                release=v3,
                expected_version="v3",
                actor_user_id=None,
                idempotency_key="activate-drift",
                expected_source_checksums={**CHECKSUMS, "output_schema_sha256": "0" * 64},
                purpose_code=v3.purpose_code,
                purpose_contract_version=v3.purpose_contract_version,
                schema_version=v3.schema_version,
                prompt_version=v3.prompt_version,
                model_configuration_version=v3.model_configuration_version,
                rollback_target="fixed_structured_fallback",
            )
        supersede_release(
            db,
            active_release=v3,
            successor=v4,
            expected_active_version="v3",
            actor_user_id=None,
            idempotency_key="supersede-v3-v4",
            rollback_target=str(v3.id),
        )
        assert effective_active_release_id(db, v3.release_key) == v4.id
        rollback_release(
            db,
            current_release=v4,
            rollback_target=v3,
            expected_current_version="v4",
            actor_user_id=None,
            idempotency_key="rollback-v4-v3",
        )
        assert effective_active_release_id(db, v3.release_key) == v3.id
        engage_purpose_kill_switch(
            db,
            active_release=v3,
            expected_version="v3",
            actor_user_id=None,
            idempotency_key="kill-v3",
            reason_code="synthetic_stage_drill",
        )
        assert effective_active_release_id(db, v3.release_key) is None
        assert v3.activation_state == "pending"
        assert v4.activation_state == "pending"
        db.commit()


def test_v2_unsuitable_correction_is_idempotent_append_only_evidence() -> None:
    with SessionLocal() as db:
        v2 = _release(version="v2")
        db.add(v2)
        db.flush()
        first = mark_release_unsuitable(
            db,
            release=v2,
            expected_version="v2",
            actor_user_id=None,
            idempotency_key="v2-executable-gate-correction",
            reason_codes=[
                "factual_contradiction_validator_gap",
                "hard_coded_machine_gate_counts",
            ],
        )
        replay = mark_release_unsuitable(
            db,
            release=v2,
            expected_version="v2",
            actor_user_id=None,
            idempotency_key="v2-executable-gate-correction",
            reason_codes=[
                "factual_contradiction_validator_gap",
                "hard_coded_machine_gate_counts",
            ],
        )
        assert replay.idempotent_replay is True
        assert replay.event.id == first.event.id
        assert v2.activation_state == "pending"
        assert (
            len(
                db.scalars(
                    select(ExpectedCareExplanationReleaseEvent).where(
                        ExpectedCareExplanationReleaseEvent.release_id == v2.id
                    )
                ).all()
            )
            == 1
        )


def test_concurrent_activation_creates_one_event_and_one_replay() -> None:
    with SessionLocal() as db:
        release = _release(version="v3-concurrent")
        db.add(release)
        db.flush()
        release_id = release.id
        register_early_stage_waivers(
            db,
            release=release,
            expected_version=release.version,
            actor_user_id=None,
            idempotency_key="waiver-concurrent",
            statuses=WAIVERS,
        )
        db.commit()

    def worker():
        with SessionLocal() as db:
            release = db.get(ExpectedCareExplanationRelease, release_id)
            result = _activate(db, release, "activate-concurrent")
            db.commit()
            return result.idempotent_replay

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: worker(), range(2)))
    assert sorted(outcomes) == [False, True]
    with SessionLocal() as db:
        events = db.scalars(
            select(ExpectedCareExplanationReleaseEvent).where(
                ExpectedCareExplanationReleaseEvent.release_id == release_id,
                ExpectedCareExplanationReleaseEvent.event_type == "release_activated",
            )
        ).all()
        assert len(events) == 1
