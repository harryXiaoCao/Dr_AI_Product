import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import pytest
from pydantic import SecretStr
from sqlalchemy import func, select

from app.database import SessionLocal
from app.expected_care_candidate_governance import (
    RELEASE_KEY,
    RELEASE_TYPE,
    SCOPE_KEY,
    CandidateReleaseTransitionError,
    activate_candidate_release,
    active_candidate_release,
    candidate_runtime_contract_checksum,
    candidate_source_checksum_sha256,
    engage_candidate_kill_switch,
    rollback_candidate_release,
)
from app.expected_care_candidates import (
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
    DeepSeekExpectedCareProvider,
    ProviderCandidateResponse,
    _checksum,
)
from app.models import (
    ExpectedCareCandidateRequest,
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
    GovernedCareReleaseReview,
)
from app.synthetic_care_reference import (
    install_synthetic_care_reference_bundle,
    synthetic_active_selection,
)
from tests.helpers import auth_header, register


def _release(settings, version: str, predecessor: uuid.UUID | None = None):
    source_checksum = candidate_source_checksum_sha256()
    payload_checksum = _checksum(
        {
            "version": version,
            "source_checksum_sha256": source_checksum,
            "runtime_contract_checksum_sha256": candidate_runtime_contract_checksum(settings),
        }
    )
    release = GovernedCareRelease(
        release_type=RELEASE_TYPE,
        release_key=RELEASE_KEY,
        version=version,
        schema_version=OUTPUT_SCHEMA_VERSION,
        lifecycle_status="reviewed",
        jurisdiction="synthetic_only",
        region="Synthetic Province",
        facility_scope_json={"stage": SCOPE_KEY},
        currency="CNY",
        effective_from=date(2026, 7, 1),
        effective_to=date(2027, 7, 1),
        source_authority="Dr. AI deterministic test",
        source_locator=f"urn:dr-ai:test:{version}",
        retrieved_at=datetime(2026, 7, 30, tzinfo=UTC),
        source_checksum_sha256=source_checksum,
        payload_checksum_sha256=payload_checksum,
        provenance_json={
            "data_class": "wholly_synthetic",
            "purpose_code": PURPOSE_CODE,
            "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "prompt_version": PROMPT_VERSION,
            "model_configuration_version": MODEL_CONFIGURATION_VERSION,
            "provider": settings.expected_care_provider,
            "model": settings.expected_care_model,
            "runtime_contract_checksum_sha256": candidate_runtime_contract_checksum(settings),
            "candidate_source_sha256": source_checksum,
            "machine_gates": {
                "schema_valid": True,
                "deterministic_exactness": True,
                "fallback": True,
            },
        },
        required_review_types_json=["security"],
        rights_status="product_owner_waived_for_current_stage",
        storage_allowed=True,
        derivation_allowed=True,
        redistribution_allowed=False,
        provider_transmission_allowed=True,
        last_verified_on=date(2026, 7, 30),
        next_review_on=date(2027, 1, 30),
        supersedes_release_id=predecessor,
    )
    release.reviews.append(
        GovernedCareReleaseReview(
            review_type="security",
            decision="product_owner_waived_for_current_stage",
            reviewer_name="Synthetic test owner",
            reviewed_payload_checksum_sha256=payload_checksum,
            rationale="Wholly synthetic deterministic test.",
        )
    )
    return release


def test_activation_kill_switch_and_exact_predecessor_rollback(settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "expected_care_candidate_enabled", True)
    with SessionLocal() as db:
        v1 = _release(settings, "v1-current")
        db.add(v1)
        db.flush()
        activate_candidate_release(
            db,
            release=v1,
            settings=settings,
            actor_user_id=None,
            reason_code="synthetic_activate",
            on_date=date(2026, 7, 30),
            expected_version=v1.version,
        )
        assert active_candidate_release(db, settings).release_id == v1.id

        v2 = _release(settings, "v2-current", v1.id)
        db.add(v2)
        db.flush()
        activate_candidate_release(
            db,
            release=v2,
            settings=settings,
            actor_user_id=None,
            reason_code="synthetic_supersede",
            on_date=date(2026, 7, 30),
            expected_version=v2.version,
        )
        assert active_candidate_release(db, settings).release_id == v2.id

        unrelated = _release(settings, "unrelated")
        db.add(unrelated)
        db.flush()
        with pytest.raises(CandidateReleaseTransitionError, match="predecessor_mismatch"):
            rollback_candidate_release(
                db,
                current_release=v2,
                rollback_target=unrelated,
                settings=settings,
                actor_user_id=None,
                reason_code="invalid_rollback",
                on_date=date(2026, 7, 30),
                expected_current_version=v2.version,
            )
        rollback = rollback_candidate_release(
            db,
            current_release=v2,
            rollback_target=v1,
            settings=settings,
            actor_user_id=None,
            reason_code="exact_rollback",
            on_date=date(2026, 7, 30),
            expected_current_version=v2.version,
        )
        assert rollback.action == "rollback"
        assert active_candidate_release(db, settings).release_id == v1.id

        killed = engage_candidate_kill_switch(
            db,
            actor_user_id=None,
            reason_code="synthetic_kill",
        )
        assert killed.action == "kill_switch"
        assert (
            db.scalar(
                select(GovernedActiveCareRelease).where(
                    GovernedActiveCareRelease.release_key == RELEASE_KEY
                )
            )
            is None
        )
        with pytest.raises(CandidateReleaseTransitionError, match="inactive_release"):
            active_candidate_release(db, settings)
        actions = db.scalars(
            select(GovernedCareReleaseActivation.action)
            .where(GovernedCareReleaseActivation.release_key == RELEASE_KEY)
            .order_by(GovernedCareReleaseActivation.created_at)
        ).all()
        assert actions == ["activate", "supersede", "rollback", "kill_switch"]


def test_stale_and_checksum_drifted_releases_fail_closed(settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "expected_care_candidate_enabled", True)
    with SessionLocal() as db:
        drifted = _release(settings, "drifted")
        drifted.provenance_json = {
            **drifted.provenance_json,
            "candidate_source_sha256": "0" * 64,
        }
        db.add(drifted)
        db.flush()
        with pytest.raises(
            CandidateReleaseTransitionError,
            match="purpose_or_runtime_incompatible",
        ):
            activate_candidate_release(
                db,
                release=drifted,
                settings=settings,
                actor_user_id=None,
                reason_code="must_fail",
                on_date=date(2026, 7, 30),
                expected_version=drifted.version,
            )

    with SessionLocal() as db:
        stale = _release(settings, "stale")
        stale.last_verified_on = date(2026, 7, 28)
        stale.next_review_on = date(2026, 7, 29)
        db.add(stale)
        db.flush()
        with pytest.raises(ValueError, match="release_stale"):
            activate_candidate_release(
                db,
                release=stale,
                settings=settings,
                actor_user_id=None,
                reason_code="must_fail",
                on_date=date(2026, 7, 30),
                expected_version=stale.version,
            )


def test_concurrent_activation_creates_one_effective_pointer(settings) -> None:
    with SessionLocal() as db:
        release = _release(settings, "concurrent-v1")
        db.add(release)
        db.commit()
        release_id = release.id

    def _activate(reason_code: str) -> str:
        with SessionLocal() as db:
            release = db.get(GovernedCareRelease, release_id)
            assert release is not None
            try:
                event = activate_candidate_release(
                    db,
                    release=release,
                    settings=settings,
                    actor_user_id=None,
                    reason_code=reason_code,
                    on_date=date(2026, 7, 30),
                    expected_version=release.version,
                )
                db.commit()
                return event.action
            except ValueError as exc:
                db.rollback()
                return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(_activate, ("concurrent_a", "concurrent_b")))
    assert sorted(outcomes) == ["activate", "release_already_active"]
    with SessionLocal() as db:
        pointer = db.scalar(
            select(GovernedActiveCareRelease).where(
                GovernedActiveCareRelease.release_key == RELEASE_KEY
            )
        )
        assert pointer is not None and pointer.release_id == release_id
        assert (
            db.scalar(
                select(func.count())
                .select_from(GovernedCareReleaseActivation)
                .where(GovernedCareReleaseActivation.release_key == RELEASE_KEY)
            )
            == 1
        )


def test_doctor_generation_route_binds_exact_purpose_release(
    client,
    settings,
    monkeypatch,
) -> None:
    patient = register(
        client,
        email="slice-d-route-patient@example.com",
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email="slice-d-route-doctor@example.com",
        password="Doctor9!",
        role="doctor",
    )
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    patient_id = uuid.UUID(care["patient"]["patient_id"])
    assert (
        client.post(
            "/api/v1/patients/connect",
            headers=doctor_headers,
            json={"patient_code": care["patient"]["synthetic_identifier"]},
        ).status_code
        == 200
    )
    event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Governed Slice D route",
            "chief_complaint": "Synthetic only.",
            "status": "active",
        },
    ).json()
    event_id = uuid.UUID(event["id"])
    monkeypatch.setattr(settings, "expected_care_candidate_enabled", True)
    monkeypatch.setattr(settings, "deepseek_api_key", SecretStr("synthetic-not-sent"))
    with SessionLocal() as db:
        install_synthetic_care_reference_bundle(db)
        purpose_release = _release(settings, "route-v1")
        db.add(purpose_release)
        db.flush()
        activate_candidate_release(
            db,
            release=purpose_release,
            settings=settings,
            actor_user_id=None,
            reason_code="route_test",
            on_date=date(2026, 7, 30),
            expected_version=purpose_release.version,
        )
        release_id = purpose_release.id
        release_checksum = purpose_release.payload_checksum_sha256
        db.commit()

    def _generate(self, *, provider_input, output_schema, settings):
        del self, output_schema
        context = provider_input["context"]
        totals = provider_input["server_totals"]
        return ProviderCandidateResponse(
            output={
                "purpose_code": provider_input["purpose_code"],
                "purpose_contract_version": provider_input["purpose_contract_version"],
                "schema_version": provider_input["schema_version"],
                "minimum_input_checksum_sha256": provider_input["minimum_input_checksum_sha256"],
                "scenario_release_id": provider_input["scenario_release_id"],
                "reference_date": context["reference_date"],
                "jurisdiction": context["jurisdiction"],
                "region": context["region"],
                "facility_ownership": context["facility_ownership"],
                "facility_level": context["facility_level"],
                "currency": context["currency"],
                "assumptions": provider_input["allowed_assumptions"],
                "missing_information": provider_input["allowed_missing_information"],
                "attributable_exceptions": [],
                "confidence_category": "moderate",
                "confidence_limitations": provider_input["allowed_confidence_limitations"],
                "items": provider_input["admitted_candidates"],
                "total_low_minor": totals["total_low_minor"],
                "total_high_minor": totals["total_high_minor"],
                "release_lineage": provider_input["release_lineage"],
            },
            provider="deepseek",
            model=settings.expected_care_model,
            input_tokens=10,
            output_tokens=10,
            cost_microunits=1,
        )

    monkeypatch.setattr(DeepSeekExpectedCareProvider, "generate", _generate)
    selection = synthetic_active_selection()
    payload = {
        "scenario_key": selection.scenario_key,
        "care_plan_key": selection.care_plan_key,
        "pricing_reference_key": selection.pricing_reference_key,
        "utilization_rule_key": selection.utilization_rule_key,
        "scope_key": selection.scope_key,
        "evaluated_on": "2026-07-30",
        "reference_date": "2026-07-25",
        "jurisdiction": "CN",
        "region": "Synthetic Province",
        "encounter_type": "outpatient",
        "facility_ownership": "public",
        "facility_level": "primary",
        "currency": "CNY",
        "patient_age": 42,
    }
    path = f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates"
    assert (
        client.post(
            path,
            headers={**patient_headers, "Idempotency-Key": "slice-d-route-patient"},
            json=payload,
        ).status_code
        == 404
    )
    response = client.post(
        path,
        headers={**doctor_headers, "Idempotency-Key": "slice-d-route-doctor"},
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.json()["idempotent_replay"] is False
    assert response.json()["candidate"]["purpose_release"] == {
        "release_id": str(release_id),
        "payload_checksum_sha256": release_checksum,
    }
    replay = client.post(
        path,
        headers={**doctor_headers, "Idempotency-Key": "slice-d-route-doctor"},
        json=payload,
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    with SessionLocal() as db:
        request = db.scalar(
            select(ExpectedCareCandidateRequest).where(
                ExpectedCareCandidateRequest.idempotency_key == "slice-d-route-doctor"
            )
        )
        assert request is not None
        assert request.ai_purpose_release_id == release_id
        assert request.ai_purpose_release_checksum_sha256 == release_checksum
        assert request.minimum_input_json["ai_purpose_release"] == {
            "release_id": str(release_id),
            "version": "route-v1",
            "payload_checksum_sha256": release_checksum,
        }
        assert (
            db.scalar(
                select(func.count())
                .select_from(ExpectedCareCandidateRequest)
                .where(ExpectedCareCandidateRequest.idempotency_key == "slice-d-route-doctor")
            )
            == 1
        )
