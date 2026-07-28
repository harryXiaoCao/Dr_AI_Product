import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.care_reference_engine import (
    EvaluationContext,
    EvaluationRequest,
    ObservedLine,
)
from app.care_reference_governance import activate_release
from app.care_reference_integration import (
    CareReferenceAuthorizationError,
    evaluate_and_persist_authorized_care_reference,
    resolve_active_care_reference_bundle,
)
from app.database import SessionLocal
from app.models import (
    AuditEvent,
    CareReferenceEvaluation,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    User,
)
from app.synthetic_care_reference import (
    SYNTHETIC_CODE_SYSTEM,
    SYNTHETIC_SERVICE_CODE,
    SYNTHETIC_UNIT,
    install_all_synthetic_stage_reference_families,
    install_synthetic_care_reference_bundle,
    synthetic_active_selection,
)
from tests.helpers import auth_header, register


def _case_context(*, evaluated_on: date = date(2026, 7, 25)) -> EvaluationContext:
    return EvaluationContext(
        evaluated_on=evaluated_on,
        reference_date=date(2026, 7, 25),
        jurisdiction="CN",
        region="Synthetic Province",
        encounter_type="outpatient",
        facility_ownership="public",
        facility_level="primary",
        currency="CNY",
        patient_age=42,
    )


def _connected_case(
    client: TestClient,
    *,
    suffix: str,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, dict[str, str], str]:
    patient_email = f"reference.patient.{suffix}@example.com"
    doctor_email = f"reference.doctor.{suffix}@example.com"
    patient = register(
        client,
        email=patient_email,
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email=doctor_email,
        password="Doctor9!",
        role="doctor",
    )
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    patient_id = uuid.UUID(care["patient"]["patient_id"])
    connected = client.post(
        "/api/v1/patients/connect",
        headers=doctor_headers,
        json={"patient_code": care["patient"]["synthetic_identifier"]},
    )
    assert connected.status_code == 200, connected.text
    event = client.post(
        f"/api/v1/patients/{patient_id}/clinical-events",
        headers=doctor_headers,
        json={
            "title": "Synthetic rehabilitation integration",
            "chief_complaint": "Wholly synthetic local integration fixture.",
            "status": "active",
        },
    )
    assert event.status_code == 200, event.text
    with SessionLocal() as session:
        doctor_user_id = session.scalar(select(User.id).where(User.email == doctor_email))
    assert doctor_user_id is not None
    return (
        doctor_user_id,
        patient_id,
        uuid.UUID(event.json()["id"]),
        doctor_headers,
        care["patient"]["synthetic_identifier"],
    )


def _observed_line(
    *,
    line_id: str = "synthetic-delivered-line",
    amount_minor: int = 4200,
) -> ObservedLine:
    return ObservedLine(
        line_id=line_id,
        code_system=SYNTHETIC_CODE_SYSTEM,
        service_code=SYNTHETIC_SERVICE_CODE,
        unit=SYNTHETIC_UNIT,
        quantity=3,
        currency="CNY",
        actual_amount_minor=amount_minor,
    )


def test_persisted_active_bundle_resolves_and_evaluates_end_to_end(
    client: TestClient,
) -> None:
    actor_id, patient_id, event_id, _, _ = _connected_case(client, suffix="end-to-end")
    with SessionLocal() as session:
        releases = install_synthetic_care_reference_bundle(session)
        installed_ids = {release.id for release in releases.values()}
        bundle = resolve_active_care_reference_bundle(
            session,
            selection=synthetic_active_selection(),
        )
        assert {
            bundle.scenario.control.release_id,
            bundle.plan.control.release_id,
            bundle.pricing.control.release_id,
            bundle.utilization.control.release_id,
        } == installed_ids
        persisted = evaluate_and_persist_authorized_care_reference(
            session,
            actor_user_id=actor_id,
            patient_id=patient_id,
            clinical_event_id=event_id,
            selection=synthetic_active_selection(),
            request=EvaluationRequest(
                context=_case_context(),
                observed_lines=(_observed_line(),),
                declared_observed_total_minor=4200,
            ),
        )
        session.commit()

        assert persisted.result.status == "within_range"
        assert persisted.result.total_low_minor == 2000
        assert persisted.result.total_high_minor == 6000
        stored = session.get(CareReferenceEvaluation, persisted.row.id)
        assert stored is not None
        assert stored.clinical_event_id == event_id
        assert stored.payer_request_id is None
        assert stored.input_facts_json["release_ids"] == [
            str(bundle.scenario.control.release_id),
            str(bundle.plan.control.release_id),
            str(bundle.pricing.control.release_id),
            str(bundle.utilization.control.release_id),
        ]
        audit = session.scalar(select(AuditEvent).where(AuditEvent.resource_id == stored.id))
        assert audit is not None
        assert audit.metadata_json["content_free"] is True
        assert "observed_total_minor" not in audit.metadata_json


def test_stale_active_bundle_is_persisted_as_suppressed(
    client: TestClient,
) -> None:
    actor_id, patient_id, event_id, _, _ = _connected_case(client, suffix="stale")
    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(
            session,
            next_review_on=date(2026, 7, 24),
            activate_on=date(2026, 7, 23),
        )
        persisted = evaluate_and_persist_authorized_care_reference(
            session,
            actor_user_id=actor_id,
            patient_id=patient_id,
            clinical_event_id=event_id,
            selection=synthetic_active_selection(),
            request=EvaluationRequest(
                context=_case_context(evaluated_on=date(2026, 7, 25)),
                observed_lines=(_observed_line(),),
            ),
        )
        session.commit()

    assert persisted.result.status == "suppressed"
    assert "stale_reference_release" in persisted.result.suppression_reasons


def test_supersession_and_rollback_change_the_exact_resolved_versions() -> None:
    with SessionLocal() as session:
        version_one = install_synthetic_care_reference_bundle(
            session,
            version="v1",
            price_low_minor=1000,
            price_high_minor=1500,
        )
        version_two = install_synthetic_care_reference_bundle(
            session,
            version="v2",
            price_low_minor=1200,
            price_high_minor=1700,
        )
        resolved_v2 = resolve_active_care_reference_bundle(
            session,
            selection=synthetic_active_selection(),
        )
        assert {
            resolved_v2.scenario.control.version,
            resolved_v2.plan.control.version,
            resolved_v2.pricing.control.version,
            resolved_v2.utilization.control.version,
        } == {"v2"}
        assert resolved_v2.pricing.items[0].amount_low_minor == 1200

        for release in version_one.values():
            activate_release(
                session,
                release=release,
                scope_key=synthetic_active_selection().scope_key,
                actor_user_id=None,
                reason_code="synthetic_integration_rollback",
                on_date=date(2026, 7, 25),
                rollback=True,
            )
        resolved_v1 = resolve_active_care_reference_bundle(
            session,
            selection=synthetic_active_selection(),
        )
        assert {
            resolved_v1.scenario.control.version,
            resolved_v1.plan.control.version,
            resolved_v1.pricing.control.version,
            resolved_v1.utilization.control.version,
        } == {"v1"}
        assert resolved_v1.pricing.items[0].amount_low_minor == 1000
        actions = session.scalars(select(GovernedCareReleaseActivation.action)).all()
        assert actions.count("activate") == 4
        assert actions.count("supersede") == 4
        assert actions.count("rollback") == 4
        assert {release.lifecycle_status for release in version_two.values()} == {"reviewed"}


def test_cross_patient_and_payer_request_scope_fail_neutrally(
    client: TestClient,
) -> None:
    owner_id, patient_id, event_id, _, patient_code = _connected_case(
        client, suffix="authorization-owner"
    )
    unrelated = register(
        client,
        email="reference.doctor.unrelated@example.com",
        password="Doctor9!",
        role="doctor",
    )
    unrelated_headers = auth_header(unrelated["access_token"])
    with SessionLocal() as session:
        unrelated_id = session.scalar(
            select(User.id).where(User.email == "reference.doctor.unrelated@example.com")
        )
    assert unrelated_id is not None

    with SessionLocal() as session:
        install_synthetic_care_reference_bundle(session)
        session.commit()
        with pytest.raises(CareReferenceAuthorizationError, match="not_found"):
            evaluate_and_persist_authorized_care_reference(
                session,
                actor_user_id=unrelated_id,
                patient_id=patient_id,
                clinical_event_id=event_id,
                selection=synthetic_active_selection(),
                request=EvaluationRequest(
                    context=_case_context(),
                    observed_lines=(_observed_line(),),
                ),
            )

    connected = client.post(
        "/api/v1/patients/connect",
        headers=unrelated_headers,
        json={"patient_code": patient_code},
    )
    assert connected.status_code == 200, connected.text
    with SessionLocal() as session:
        owner = session.scalar(select(User).where(User.id == owner_id))
        assert owner is not None and owner.doctor_profile is not None
        organization = PayerOrganization(
            name="Synthetic Reference Integration Payer",
            organization_type="public_payer",
            jurisdiction_code="CN",
            verification_status="synthetic_only",
        )
        session.add(organization)
        session.flush()
        payer_request = PayerRequest(
            clinical_event_id=event_id,
            patient_id=patient_id,
            doctor_id=owner.doctor_profile.id,
            payer_organization_id=organization.id,
            status="submitted",
            currency="CNY",
            requested_total_minor=3000,
            doctor_summary="Wholly synthetic immutable request fixture.",
            ai_review_status="not_evaluated",
        )
        session.add(payer_request)
        session.flush()
        snapshot = PayerRequestLine(
            payer_request_id=payer_request.id,
            item_type="therapy",
            label="Synthetic rehabilitation sessions",
            service_date=date(2026, 7, 25),
            currency="CNY",
            actual_cost_minor=4200,
            requested_minor=3000,
            patient_responsibility_minor=1200,
        )
        session.add(snapshot)
        session.flush()
        request = EvaluationRequest(
            context=_case_context(),
            observed_lines=(_observed_line(line_id=str(snapshot.id), amount_minor=4200),),
        )
        with pytest.raises(CareReferenceAuthorizationError, match="not_found"):
            evaluate_and_persist_authorized_care_reference(
                session,
                actor_user_id=unrelated_id,
                patient_id=patient_id,
                clinical_event_id=event_id,
                payer_request_id=payer_request.id,
                selection=synthetic_active_selection(),
                request=request,
            )
        with pytest.raises(CareReferenceAuthorizationError, match="not_found"):
            evaluate_and_persist_authorized_care_reference(
                session,
                actor_user_id=owner_id,
                patient_id=patient_id,
                clinical_event_id=event_id,
                payer_request_id=payer_request.id,
                selection=synthetic_active_selection(),
                request=EvaluationRequest(
                    context=_case_context(),
                    observed_lines=(
                        _observed_line(
                            line_id=str(snapshot.id),
                            amount_minor=4300,
                        ),
                    ),
                ),
            )
        persisted = evaluate_and_persist_authorized_care_reference(
            session,
            actor_user_id=owner_id,
            patient_id=patient_id,
            clinical_event_id=event_id,
            payer_request_id=payer_request.id,
            selection=synthetic_active_selection(),
            request=request,
        )
        session.commit()
        assert persisted.row.payer_request_id == payer_request.id


def test_synthetic_bundle_install_is_idempotent() -> None:
    with SessionLocal() as session:
        first = install_synthetic_care_reference_bundle(session)
        session.commit()
        second = install_synthetic_care_reference_bundle(session)
        session.commit()
        assert {name: row.id for name, row in first.items()} == {
            name: row.id for name, row in second.items()
        }
        assert session.scalar(select(func.count()).select_from(GovernedCareRelease)) == 4
        assert session.scalar(select(func.count()).select_from(GovernedCareReleaseActivation)) == 4


def test_all_early_stage_reference_families_are_governed_and_explicitly_synthetic() -> None:
    with SessionLocal() as session:
        families = install_all_synthetic_stage_reference_families(session)
        session.commit()
        assert set(families) == {
            "rehabilitation",
            "laboratory",
            "imaging",
            "consultation",
        }
        for releases in families.values():
            assert set(releases) == {"scenario", "care_plan", "pricing", "utilization"}
            for release in releases.values():
                assert release.provenance_json["data_class"] == "wholly_synthetic"
                assert release.source_locator.startswith(
                    "urn:dr-ai:synthetic-care-reference:"
                )
                assert (
                    release.rights_status
                    == "not_required_for_early_synthetic_development"
                )
                assert release.currency == "CNY"
                assert len(release.payload_checksum_sha256) == 64
                assert all(
                    review.decision
                    == "not_required_for_early_synthetic_development"
                    for review in release.reviews
                )
