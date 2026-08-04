from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.clinical_event_intelligence_governance import (
    CRITIC_RELEASE_KEY,
    EXPLANATION_RELEASE_KEY,
    FIXED_FALLBACK_TARGET,
    PRIMARY_RELEASE_KEY,
    PURPOSE_SPECS,
    IntelligenceReleaseError,
    activate_intelligence_release,
    engage_intelligence_kill_switch,
    intelligence_readiness,
    rollback_intelligence_release,
    verify_intelligence_release,
)
from app.clinical_event_intelligence_release_installation import (
    RELEASE_VERSION,
    install_intelligence_releases,
)
from app.database import SessionLocal
from app.models import (
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
)


def _enabled(settings):
    return settings.model_copy(
        update={
            "clinical_event_intelligence_primary_enabled": True,
            "clinical_event_intelligence_primary_kill_switch": False,
            "clinical_event_intelligence_critic_enabled": True,
            "clinical_event_intelligence_critic_kill_switch": False,
            "clinical_event_intelligence_explanation_enabled": True,
            "clinical_event_intelligence_explanation_kill_switch": False,
        }
    )


def _install(settings, artifact_root):
    with SessionLocal() as db:
        releases = install_intelligence_releases(
            db,
            settings=settings,
            artifact_root=artifact_root,
        )
        identities = {
            release.release_key: (
                release.id,
                release.version,
                release.payload_checksum_sha256,
            )
            for release in releases
        }
        db.commit()
    return identities


def test_installer_is_idempotent_and_binds_three_exact_purpose_contracts(
    settings,
    tmp_path,
) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    assert set(identities) == {
        PRIMARY_RELEASE_KEY,
        CRITIC_RELEASE_KEY,
        EXPLANATION_RELEASE_KEY,
    }
    assert len(list(tmp_path.glob("*.json"))) == 3
    replay = _install(governed, tmp_path)
    assert replay == identities

    with SessionLocal() as db:
        for release_key, (release_id, version, checksum) in identities.items():
            release = db.get(GovernedCareRelease, release_id)
            assert release is not None
            verify_intelligence_release(release, settings=governed)
            payload = release.provenance_json["release_payload"]
            runtime = payload["runtime_contract"]
            spec = PURPOSE_SPECS[release_key]
            assert version == RELEASE_VERSION
            assert checksum == release.payload_checksum_sha256
            assert runtime["purpose_code"] == spec.purpose_code
            assert runtime["purpose_contract_version"] == spec.purpose_contract_version
            assert runtime["prompt_version"] == spec.prompt_version
            assert runtime["schema_version"] == spec.schema_version
            assert runtime["validator_version"] == spec.validator_version
            assert runtime["scoring_aggregation_version"] == spec.scoring_aggregation_version
            assert payload["rollback_target"] == FIXED_FALLBACK_TARGET
            assert payload["predecessor_version"] is None
            assert payload["data_class"] == "wholly_synthetic"
            assert payload["real_world_activation_allowed"] is False
        assert (
            db.scalar(
                select(func.count())
                .select_from(GovernedCareReleaseActivation)
                .where(GovernedCareReleaseActivation.action == "register")
            )
            == 3
        )


def test_activation_replay_conflict_kill_switch_and_fixed_fallback_rollback(
    settings,
    tmp_path,
) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    with SessionLocal() as db:
        primary = db.get(GovernedCareRelease, identities[PRIMARY_RELEASE_KEY][0])
        assert primary is not None
        first = activate_intelligence_release(
            db,
            release=primary,
            settings=governed,
            expected_version=primary.version,
            expected_payload_checksum_sha256=primary.payload_checksum_sha256,
            idempotency_key="activate-primary-v1",
            actor_user_id=None,
            reason_code="synthetic_activation",
        )
        replay = activate_intelligence_release(
            db,
            release=primary,
            settings=governed,
            expected_version=primary.version,
            expected_payload_checksum_sha256=primary.payload_checksum_sha256,
            idempotency_key="activate-primary-v1",
            actor_user_id=None,
            reason_code="synthetic_activation",
        )
        assert replay.idempotent_replay is True
        assert replay.event.id == first.event.id
        with pytest.raises(IntelligenceReleaseError, match="idempotency_content_conflict"):
            activate_intelligence_release(
                db,
                release=primary,
                settings=governed,
                expected_version=primary.version,
                expected_payload_checksum_sha256=primary.payload_checksum_sha256,
                idempotency_key="activate-primary-v1",
                actor_user_id=None,
                reason_code="changed_reason",
            )
        rollback = rollback_intelligence_release(
            db,
            current_release=primary,
            rollback_target=None,
            settings=governed,
            expected_current_version=primary.version,
            expected_current_payload_checksum_sha256=primary.payload_checksum_sha256,
            idempotency_key="rollback-primary-v1",
            actor_user_id=None,
            reason_code="rollback_rehearsal",
        )
        replayed_rollback = rollback_intelligence_release(
            db,
            current_release=primary,
            rollback_target=None,
            settings=governed,
            expected_current_version=primary.version,
            expected_current_payload_checksum_sha256=primary.payload_checksum_sha256,
            idempotency_key="rollback-primary-v1",
            actor_user_id=None,
            reason_code="rollback_rehearsal",
        )
        assert rollback.event.action == "rollback_to_fallback"
        assert replayed_rollback.idempotent_replay is True
        assert (
            db.scalar(
                select(GovernedActiveCareRelease).where(
                    GovernedActiveCareRelease.release_key == PRIMARY_RELEASE_KEY
                )
            )
            is None
        )

        critic = db.get(GovernedCareRelease, identities[CRITIC_RELEASE_KEY][0])
        assert critic is not None
        activate_intelligence_release(
            db,
            release=critic,
            settings=governed,
            expected_version=critic.version,
            expected_payload_checksum_sha256=critic.payload_checksum_sha256,
            idempotency_key="activate-critic-v1",
            actor_user_id=None,
            reason_code="synthetic_activation",
        )
        killed = engage_intelligence_kill_switch(
            db,
            release=critic,
            settings=governed,
            expected_version=critic.version,
            expected_payload_checksum_sha256=critic.payload_checksum_sha256,
            idempotency_key="kill-critic-v1",
            actor_user_id=None,
            reason_code="kill_switch_rehearsal",
        )
        replayed_kill = engage_intelligence_kill_switch(
            db,
            release=critic,
            settings=governed,
            expected_version=critic.version,
            expected_payload_checksum_sha256=critic.payload_checksum_sha256,
            idempotency_key="kill-critic-v1",
            actor_user_id=None,
            reason_code="kill_switch_rehearsal",
        )
        assert killed.event.action == "kill_switch"
        assert replayed_kill.idempotent_replay is True
        db.commit()


def test_all_three_activate_independently_and_readiness_is_exact(settings, tmp_path) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    with SessionLocal() as db:
        for release_key, (release_id, version, checksum) in identities.items():
            release = db.get(GovernedCareRelease, release_id)
            assert release is not None
            activate_intelligence_release(
                db,
                release=release,
                settings=governed,
                expected_version=version,
                expected_payload_checksum_sha256=checksum,
                idempotency_key=f"activate:{release_key}",
                actor_user_id=None,
                reason_code="synthetic_activation",
                on_date=date(2026, 8, 2),
            )
        assert intelligence_readiness(db, governed) == {
            "primary": "ready",
            "critic": "ready",
            "explanation": "ready",
        }
        db.commit()


def test_release_and_operation_evidence_are_database_immutable(settings, tmp_path) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    release_id = identities[PRIMARY_RELEASE_KEY][0]
    with SessionLocal() as db:
        with pytest.raises(SQLAlchemyError, match="immutable"):
            db.execute(
                update(GovernedCareRelease)
                .where(GovernedCareRelease.id == release_id)
                .values(version="rewritten")
            )
            db.commit()
        db.rollback()
        event = db.scalar(
            select(GovernedCareReleaseActivation).where(
                GovernedCareReleaseActivation.release_id == release_id
            )
        )
        assert event is not None
        with pytest.raises(SQLAlchemyError, match="append-only"):
            db.execute(
                update(GovernedCareReleaseActivation)
                .where(GovernedCareReleaseActivation.id == event.id)
                .values(action="rewritten")
            )
            db.commit()


def test_concurrent_same_key_activation_creates_one_operational_event(
    settings,
    tmp_path,
) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    release_id, version, checksum = identities[EXPLANATION_RELEASE_KEY]

    def worker() -> bool:
        with SessionLocal() as db:
            release = db.get(GovernedCareRelease, release_id)
            assert release is not None
            result = activate_intelligence_release(
                db,
                release=release,
                settings=governed,
                expected_version=version,
                expected_payload_checksum_sha256=checksum,
                idempotency_key="concurrent-explanation-activation",
                actor_user_id=None,
                reason_code="synthetic_concurrency_test",
            )
            db.commit()
            return result.idempotent_replay

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: worker(), range(2)))
    assert sorted(outcomes) == [False, True]
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(GovernedCareReleaseActivation)
                .where(
                    GovernedCareReleaseActivation.release_key == EXPLANATION_RELEASE_KEY,
                    GovernedCareReleaseActivation.idempotency_key
                    == "concurrent-explanation-activation",
                )
            )
            == 1
        )


def test_expected_version_and_checksum_are_required(settings, tmp_path) -> None:
    governed = _enabled(settings)
    identities = _install(governed, tmp_path)
    with SessionLocal() as db:
        release = db.get(GovernedCareRelease, identities[PRIMARY_RELEASE_KEY][0])
        assert release is not None
        with pytest.raises(IntelligenceReleaseError, match="expected_version_conflict"):
            activate_intelligence_release(
                db,
                release=release,
                settings=governed,
                expected_version="stale-version",
                expected_payload_checksum_sha256=release.payload_checksum_sha256,
                idempotency_key="stale-version-attempt",
                actor_user_id=None,
                reason_code="must_fail",
            )
        with pytest.raises(IntelligenceReleaseError, match="expected_checksum_conflict"):
            activate_intelligence_release(
                db,
                release=release,
                settings=governed,
                expected_version=release.version,
                expected_payload_checksum_sha256="0" * 64,
                idempotency_key="drifted-checksum-attempt",
                actor_user_id=None,
                reason_code="must_fail",
            )


def test_successor_requires_exact_predecessor_and_rolls_back_to_it(settings, tmp_path) -> None:
    governed = _enabled(settings)
    v1_identities = _install(governed, tmp_path)
    with SessionLocal() as db:
        for release_key, (release_id, version, checksum) in v1_identities.items():
            release = db.get(GovernedCareRelease, release_id)
            assert release is not None
            activate_intelligence_release(
                db,
                release=release,
                settings=governed,
                expected_version=version,
                expected_payload_checksum_sha256=checksum,
                idempotency_key=f"activate-v1:{release_key}",
                actor_user_id=None,
                reason_code="predecessor_test",
            )
        db.commit()
    with SessionLocal() as db:
        v2_releases = install_intelligence_releases(
            db,
            settings=governed,
            artifact_root=tmp_path,
            version="v2-controlled-synthetic-test",
            predecessor_version=RELEASE_VERSION,
        )
        for successor in v2_releases:
            predecessor = db.get(GovernedCareRelease, successor.supersedes_release_id)
            assert predecessor is not None
            assert successor.provenance_json["release_payload"]["rollback_target"] == (
                predecessor.version
            )
            activate_intelligence_release(
                db,
                release=successor,
                settings=governed,
                expected_version=successor.version,
                expected_payload_checksum_sha256=successor.payload_checksum_sha256,
                idempotency_key=f"activate-v2:{successor.release_key}",
                actor_user_id=None,
                reason_code="successor_test",
            )
            rolled_back = rollback_intelligence_release(
                db,
                current_release=successor,
                rollback_target=predecessor,
                settings=governed,
                expected_current_version=successor.version,
                expected_current_payload_checksum_sha256=(successor.payload_checksum_sha256),
                idempotency_key=f"rollback-v2:{successor.release_key}",
                actor_user_id=None,
                reason_code="exact_predecessor_test",
            )
            assert rolled_back.event.release_id == predecessor.id
            pointer = db.scalar(
                select(GovernedActiveCareRelease).where(
                    GovernedActiveCareRelease.release_key == successor.release_key
                )
            )
            assert pointer is not None and pointer.release_id == predecessor.id
        db.commit()
