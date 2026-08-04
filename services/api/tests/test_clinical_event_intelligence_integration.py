import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import canonical_checksum
from app.clinical_event_intelligence_governance import IntelligenceReleaseBinding
from app.clinical_event_intelligence_models import (
    ClinicalEventIntelligenceArtifact,
    ClinicalEventIntelligenceExplanation,
    ClinicalEventIntelligenceLineageEvent,
    ClinicalEventIntelligenceProviderAttempt,
    ClinicalEventIntelligenceRun,
)
from app.clinical_event_intelligence_provider import (
    IntelligenceProviderError,
    IntelligenceProviderResponse,
)
from app.clinical_event_intelligence_retrieval import retrieve_authorized_intelligence_sources
from app.clinical_event_intelligence_routes import (
    IntelligenceOutcomeInput,
    _append_outcome,
    _explanation_payload,
)
from app.clinical_event_intelligence_service import (
    IntelligenceGenerationConflict,
    generate_clinical_event_intelligence,
)
from app.clinical_event_snapshot import build_frozen_clinical_event_snapshot
from app.database import engine
from app.models import (
    ClinicalEvent,
    DoctorProfile,
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
    PatientProfile,
    PayerMembership,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    PricingReferenceItem,
    PricingReferenceSet,
)
from app.synthetic_clinical_event_intelligence import (
    DOCTOR_EMAIL,
    LOCAL_ONLY_PASSWORD,
    PATIENT_EMAIL,
    PAYER_EMAIL,
    bootstrap_synthetic_clinical_event_intelligence,
)
from tests.helpers import auth_header, register


class _UnavailableProvider:
    def generate(self, **_kwargs):
        raise IntelligenceProviderError("provider_timeout", retryable=True)


class _QuotaProvider:
    def generate(self, **_kwargs):
        raise IntelligenceProviderError("provider_quota", retryable=False)


class _ValidTier5Provider:
    def generate(self, *, snapshot, retrieval, settings):
        del settings
        pathway_id = "synthetic_pathway_primary"
        fact_id = snapshot.facts_used[0].fact_id
        output = {
            "purpose_code": "clinical_event_intelligence_primary",
            "purpose_contract_version": "clinical-event-intelligence-primary.v1",
            "schema_version": "clinical-event-intelligence-output.v1",
            "snapshot_checksum_sha256": snapshot.snapshot_checksum_sha256,
            "retrieval_manifest_checksum_sha256": retrieval.manifest_checksum_sha256,
            "pathways": [
                {
                    "pathway_id": pathway_id,
                    "pathway_type": "typical_first_line",
                    "trigger_fact_ids": [fact_id],
                    "usefulness": "Wholly synthetic comparison hypothesis.",
                    "confidence": 60,
                    "assumptions": [],
                    "limitations": ["Human review remains required."],
                    "items": [
                        {
                            "item_key": "synthetic_predicted_follow_up",
                            "label": "Synthetic predicted follow-up",
                            "category": "follow_up",
                            "service_code": None,
                            "quantity_low": 1,
                            "quantity_high": 2,
                            "unit": "visit",
                            "currency": "CNY",
                            "cost_low_minor": 1000,
                            "cost_high_minor": 3000,
                            "rationale_fact_ids": [fact_id],
                        }
                    ],
                }
            ],
            "requested_item_assessments": [
                {
                    "requested_line_id": line.requested_line_id,
                    "usefulness": "Synthetic support assessment for human review.",
                    "mapped_pathway_ids": [pathway_id],
                    "scores": {
                        "clinical_fit": 70,
                        "evidence_support": 60,
                        "timing_sequence": 55,
                        "quantity_intensity": 50,
                        "documentation_completeness": 40,
                        "cost_alignment": 30,
                    },
                    "estimated_quantity": {"low": 1, "high": 2, "unit": line.unit},
                    "estimated_cost": {
                        "low_minor": 1000,
                        "high_minor": 12000,
                        "currency": line.currency,
                        "provenance_tier": 5,
                        "source_ids": [],
                        "is_model_only_exploratory": True,
                    },
                    "supporting_fact_ids": [fact_id],
                    "contradicting_fact_ids": [],
                    "missing_information": list(snapshot.missing_information),
                    "alternatives": ["Request more synthetic documentation."],
                    "confidence": "moderate",
                    "brief_comment": "No automatic action is permitted.",
                }
                for line in snapshot.requested_lines
            ],
            "unresolved_questions": list(snapshot.missing_information),
            "overall_confidence": "moderate",
        }
        return IntelligenceProviderResponse(
            output=output,
            provider="synthetic_provider",
            model="synthetic_primary",
            input_tokens=10,
            output_tokens=10,
            cost_microunits=1,
            output_checksum_sha256=canonical_checksum(output),
        )


class _UnavailableCritic:
    def review(self, **_kwargs):
        raise IntelligenceProviderError("provider_timeout", retryable=False)


def _payer(client: TestClient, suffix: str) -> tuple[dict, dict[str, str]]:
    email = f"cei.payer.{suffix}@example.com"
    phone_suffix = int(hashlib.sha1(email.encode()).hexdigest()[:10], 16) % 10_000_000
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": f"+1666{phone_suffix:07d}",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "CEI payer reviewer",
                "organization_name": f"CEI synthetic payer {suffix}",
                "title": "Reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body, auth_header(body["access_token"])


def _case(client: TestClient, suffix: str):
    patient = register(
        client, email=f"cei.patient.{suffix}@example.com", password="Patient9!", role="patient"
    )
    doctor = register(
        client, email=f"cei.doctor.{suffix}@example.com", password="Doctor9!", role="doctor"
    )
    payer, payer_headers = _payer(client, suffix)
    _, unrelated_payer_headers = _payer(client, f"other-{suffix}")
    unrelated_patient = register(
        client,
        email=f"cei.other.patient.{suffix}@example.com",
        password="Patient9!",
        role="patient",
    )
    unrelated_doctor = register(
        client,
        email=f"cei.other.doctor.{suffix}@example.com",
        password="Doctor9!",
        role="doctor",
    )
    with Session(engine) as db:
        patient_profile = db.scalar(
            select(PatientProfile).where(PatientProfile.user_id == uuid.UUID(patient["user"]["id"]))
        )
        doctor_profile = db.scalar(
            select(DoctorProfile).where(DoctorProfile.user_id == uuid.UUID(doctor["user"]["id"]))
        )
        payer_membership = db.scalar(
            select(PayerMembership).where(PayerMembership.user_id == uuid.UUID(payer["user"]["id"]))
        )
        assert patient_profile and doctor_profile and payer_membership
        event = ClinicalEvent(
            patient_id=patient_profile.id,
            doctor_id=doctor_profile.id,
            title="Wholly synthetic CEI event",
            chief_complaint="Synthetic symptoms only",
            symptom_summary="Synthetic intermittent symptom",
            encounter_at=datetime(2026, 8, 1, tzinfo=UTC),
            metadata_json={
                "location": {
                    "jurisdiction_code": "CN",
                    "province_code": "CN-SYN",
                    "city_code": "CN-SYN-001",
                    "facility_level": "synthetic_tertiary",
                }
            },
        )
        request = PayerRequest(
            clinical_event=event,
            patient_id=patient_profile.id,
            doctor_id=doctor_profile.id,
            payer_organization_id=payer_membership.payer_organization_id,
            status="submitted",
            currency="CNY",
            requested_total_minor=10_000,
            doctor_summary="Synthetic immutable request.",
        )
        request.lines.append(
            PayerRequestLine(
                item_type="laboratory",
                label="Synthetic panel",
                code_system="DR-AI-SYNTHETIC",
                service_code="SYN-LAB-01",
                quantity=1,
                unit="panel",
                service_date=date(2026, 8, 1),
                currency="CNY",
                actual_cost_minor=10_000,
                requested_minor=10_000,
                patient_responsibility_minor=0,
            )
        )
        db.add(request)
        db.commit()
        request_id = request.id
        actor_user_id = uuid.UUID(doctor["user"]["id"])
        payer_org_id = payer_membership.payer_organization_id
        payer_user_id = payer_membership.user_id
    return {
        "request_id": request_id,
        "actor_user_id": actor_user_id,
        "payer_org_id": payer_org_id,
        "payer_user_id": payer_user_id,
        "patient_headers": auth_header(patient["access_token"]),
        "doctor_headers": auth_header(doctor["access_token"]),
        "payer_headers": payer_headers,
        "other_patient_headers": auth_header(unrelated_patient["access_token"]),
        "other_doctor_headers": auth_header(unrelated_doctor["access_token"]),
        "other_payer_headers": unrelated_payer_headers,
    }


def _release(
    db: Session,
    *,
    release_key: str = "clinical-event-intelligence-primary",
    version: str = "v1-integration",
) -> GovernedCareRelease:
    release = GovernedCareRelease(
        release_type="ai_purpose",
        release_key=release_key,
        version=version,
        schema_version="clinical-event-intelligence-output.v1",
        lifecycle_status="reviewed",
        jurisdiction="CN",
        facility_scope_json={},
        effective_from=date(2026, 8, 1),
        source_authority="Wholly synthetic integration fixture",
        source_locator="urn:dr-ai:synthetic:cei-integration",
        retrieved_at=datetime(2026, 8, 1, tzinfo=UTC),
        source_checksum_sha256="a" * 64,
        payload_checksum_sha256="b" * 64,
        required_review_types_json=["synthetic_stage"],
        rights_status="product_owner_waived_for_current_stage",
        storage_allowed=True,
        derivation_allowed=True,
        provider_transmission_allowed=True,
    )
    db.add(release)
    db.flush()
    return release


def _active_payer_price(
    db: Session,
    *,
    release_key: str,
    payer_organization_id: uuid.UUID,
    effective_from: date,
    effective_to: date | None = None,
    confidential: bool = False,
    rights_status: str = "product_owner_waived_for_current_stage",
    storage_allowed: bool = True,
    derivation_allowed: bool = True,
) -> GovernedCareRelease:
    release = GovernedCareRelease(
        release_type="payer_pricing_reference",
        release_key=release_key,
        version="v1-integration",
        schema_version="pricing-reference.v1",
        lifecycle_status="reviewed",
        jurisdiction="CN",
        facility_scope_json={"payer_organization_ids": [str(payer_organization_id)]},
        currency="CNY",
        effective_from=effective_from,
        effective_to=effective_to,
        source_authority="Wholly synthetic payer price fixture",
        source_locator=f"urn:dr-ai:synthetic:{release_key}",
        retrieved_at=datetime(2026, 8, 1, tzinfo=UTC),
        source_checksum_sha256="c" * 64,
        payload_checksum_sha256="d" * 64,
        required_review_types_json=["synthetic_stage"],
        rights_status=rights_status,
        storage_allowed=storage_allowed,
        derivation_allowed=derivation_allowed,
        provider_transmission_allowed=True,
    )
    db.add(release)
    db.flush()
    db.add(
        PricingReferenceSet(
            release_id=release.id,
            price_type="range",
            amount_semantics="service_date",
            comparability="exact",
        )
    )
    db.flush()
    db.add(
        PricingReferenceItem(
            pricing_reference_release_id=release.id,
            code_system="DR-AI-SYNTHETIC",
            service_code="SYN-LAB-01",
            unit="panel",
            facility_scope_key="*",
            currency="CNY",
            amount_low_minor=8_000,
            amount_high_minor=12_000,
            economic_meaning="wholly_synthetic_reference",
            confidential=confidential,
        )
    )
    db.flush()
    activation = GovernedCareReleaseActivation(
        release_id=release.id,
        release_type=release.release_type,
        release_key=release.release_key,
        scope_key=f"integration:{release_key}",
        action="activate",
        reason_code="synthetic_test",
    )
    db.add(activation)
    db.flush()
    db.add(
        GovernedActiveCareRelease(
            release_type=release.release_type,
            release_key=release.release_key,
            scope_key=activation.scope_key,
            release_id=release.id,
            activation_event_id=activation.id,
        )
    )
    return release


def test_request_routes_fail_closed_across_roles_and_revoked_membership(client: TestClient) -> None:
    case = _case(client, "authorization")
    request_id = case["request_id"]
    for prefix, headers in (
        ("doctor/payer-requests", case["doctor_headers"]),
        ("patient/payer-requests", case["patient_headers"]),
        ("payer/requests", case["payer_headers"]),
    ):
        response = client.get(f"/api/v1/{prefix}/{request_id}/intelligence", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"artifact": None}
    assert (
        client.get(
            f"/api/v1/doctor/payer-requests/{request_id}/intelligence",
            headers=case["other_doctor_headers"],
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/patient/payer-requests/{request_id}/intelligence",
            headers=case["other_patient_headers"],
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/payer/requests/{request_id}/intelligence",
            headers=case["other_payer_headers"],
        ).status_code
        == 404
    )
    with engine.begin() as connection:
        connection.execute(
            update(PayerMembership)
            .where(PayerMembership.payer_organization_id == case["payer_org_id"])
            .values(status="revoked")
        )
    assert (
        client.get(
            f"/api/v1/payer/requests/{request_id}/intelligence",
            headers=case["payer_headers"],
        ).status_code
        == 404
    )


def test_cei_payer_with_ambiguous_active_organization_fails_closed(
    client: TestClient,
) -> None:
    case = _case(client, "ambiguous-membership")
    with Session(engine) as db:
        organization = PayerOrganization(
            name=f"CEI second synthetic payer {uuid.uuid4()}",
            organization_type="public_payer",
            jurisdiction_code="CN",
            verification_status="synthetic_only",
        )
        db.add(organization)
        db.flush()
        db.add(
            PayerMembership(
                payer_organization_id=organization.id,
                user_id=case["payer_user_id"],
                display_name="Ambiguous CEI reviewer",
                title="Reviewer",
                status="active",
                scope="synthetic_review",
            )
        )
        db.commit()
    response = client.get(
        f"/api/v1/payer/requests/{case['request_id']}/intelligence",
        headers=case["payer_headers"],
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payer_organization_context_ambiguous"


def test_timeout_fallback_commits_exact_lines_and_replays_idempotently(
    client: TestClient, settings
) -> None:
    case = _case(client, "fallback")
    settings = settings.model_copy(update={"clinical_event_intelligence_critic_enabled": False})
    with Session(engine) as db:
        release = _release(db)
        db.commit()
        binding = IntelligenceReleaseBinding(
            release_id=release.id,
            release_key=release.release_key,
            version=release.version,
            payload_checksum_sha256=release.payload_checksum_sha256,
        )
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        original_state = (request.status, request.ai_review_status, request.ai_review_score)
        result = generate_clinical_event_intelligence(
            db,
            actor_user_id=case["actor_user_id"],
            payer_request=request,
            idempotency_key="cei-fallback-0001",
            settings=settings,
            primary_provider=_UnavailableProvider(),
            primary_release=binding,
        )
        assert result.idempotent_replay is False
        assert result.artifact.lifecycle_state == "provider_unavailable"
        fallback = result.artifact.artifact_json["requested_item_assessments"]
        assert len(fallback) == 1
        assert fallback[0]["human_review_required"] is True
        assert fallback[0]["no_automatic_action"] is True
        assert "snapshot" in result.artifact.artifact_json
        replay = generate_clinical_event_intelligence(
            db,
            actor_user_id=case["actor_user_id"],
            payer_request=db.get(PayerRequest, case["request_id"]),
            idempotency_key="cei-fallback-0001",
            settings=settings,
            primary_provider=_UnavailableProvider(),
            primary_release=binding,
        )
        assert replay.idempotent_replay is True
        assert replay.artifact.id == result.artifact.id
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        assert (request.status, request.ai_review_status, request.ai_review_score) == original_state
        assert len(db.scalars(select(ClinicalEventIntelligenceRun)).all()) == 1
        assert len(db.scalars(select(ClinicalEventIntelligenceArtifact)).all()) == 1
        attempts = db.scalars(select(ClinicalEventIntelligenceProviderAttempt)).all()
        assert len(attempts) == settings.clinical_event_intelligence_primary_max_attempts
        assert all(attempt.diagnostic_code == "provider_timeout" for attempt in attempts)

        explanation = _explanation_payload(db, result.artifact, role="doctor", locale="en")
        assert explanation["display_mode"] == "structured_fallback"
        assert explanation["idempotent_replay"] is False
        explanation_replay = _explanation_payload(db, result.artifact, role="doctor", locale="en")
        assert explanation_replay["idempotent_replay"] is True
        stored_explanation = db.scalar(select(ClinicalEventIntelligenceExplanation))
        assert stored_explanation is not None
        assert stored_explanation.purpose_release_id is None

        outcome = _append_outcome(
            db,
            result.artifact,
            actor_user_id=case["actor_user_id"],
            role="doctor",
            payload=IntelligenceOutcomeInput(
                outcome_type="clinical_follow_up",
                observed_at=datetime(2026, 8, 2, tzinfo=UTC),
                summary="Wholly synthetic follow-up remained stable.",
                evaluation_use_permitted=True,
            ),
            idempotency_key="cei-outcome-0001",
        )
        assert outcome["idempotent_replay"] is False
        outcome_replay = _append_outcome(
            db,
            result.artifact,
            actor_user_id=case["actor_user_id"],
            role="doctor",
            payload=IntelligenceOutcomeInput(
                outcome_type="clinical_follow_up",
                observed_at=datetime(2026, 8, 2, tzinfo=UTC),
                summary="Wholly synthetic follow-up remained stable.",
                evaluation_use_permitted=True,
            ),
            idempotency_key="cei-outcome-0001",
        )
        assert outcome_replay["idempotent_replay"] is True
        lineage = db.scalars(select(ClinicalEventIntelligenceLineageEvent)).all()
        assert len(lineage) == 1
        assert lineage[0].metadata_json["ai_ground_truth"] is False


def test_quota_failure_is_non_retrying_and_preserves_safe_workflows(
    client: TestClient, settings
) -> None:
    case = _case(client, "quota")
    settings = settings.model_copy(update={"clinical_event_intelligence_critic_enabled": False})
    with Session(engine) as db:
        release = _release(db)
        db.flush()
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        result = generate_clinical_event_intelligence(
            db,
            actor_user_id=case["actor_user_id"],
            payer_request=request,
            idempotency_key="cei-quota-fallback-0001",
            settings=settings,
            primary_provider=_QuotaProvider(),
            primary_release=IntelligenceReleaseBinding(
                release_id=release.id,
                release_key=release.release_key,
                version=release.version,
                payload_checksum_sha256=release.payload_checksum_sha256,
            ),
        )
        assert result.artifact.lifecycle_state == "provider_unavailable"
        assert result.artifact.artifact_json["clinical_documentation_available"] is True
        assert result.artifact.artifact_json["pending_cost_available"] is True
        assert result.artifact.artifact_json["clarification_available"] is True
        assert result.artifact.artifact_json["human_review_available"] is True
        attempts = db.scalars(select(ClinicalEventIntelligenceProviderAttempt)).all()
        assert len(attempts) == 1
        assert attempts[0].diagnostic_code == "provider_quota"


def test_critic_failure_persists_valid_primary_and_unavailable_reconciliation(
    client: TestClient, settings
) -> None:
    case = _case(client, "critic-failure")
    with Session(engine) as db:
        primary = _release(db)
        critic = _release(db, release_key="clinical-event-intelligence-critic")
        db.flush()
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        result = generate_clinical_event_intelligence(
            db,
            actor_user_id=case["actor_user_id"],
            payer_request=request,
            idempotency_key="cei-critic-fallback-0001",
            settings=settings,
            primary_provider=_ValidTier5Provider(),
            critic_provider=_UnavailableCritic(),
            primary_release=IntelligenceReleaseBinding(
                release_id=primary.id,
                release_key=primary.release_key,
                version=primary.version,
                payload_checksum_sha256=primary.payload_checksum_sha256,
            ),
            critic_release=IntelligenceReleaseBinding(
                release_id=critic.id,
                release_key=critic.release_key,
                version=critic.version,
                payload_checksum_sha256=critic.payload_checksum_sha256,
            ),
        )
        assert result.artifact.lifecycle_state == "validated"
        assert result.artifact.disagreement_state == "unavailable"
        assert result.artifact.artifact_json["no_automatic_action"] is True
        attempts = db.scalars(
            select(ClinicalEventIntelligenceProviderAttempt).order_by(
                ClinicalEventIntelligenceProviderAttempt.pass_type
            )
        ).all()
        assert {(attempt.pass_type, attempt.outcome) for attempt in attempts} == {
            ("primary", "validated"),
            ("critic", "provider_error"),
        }


def test_different_idempotency_keys_serialize_request_versions(
    client: TestClient, settings
) -> None:
    case = _case(client, "concurrency")
    settings = settings.model_copy(update={"clinical_event_intelligence_critic_enabled": False})
    with Session(engine) as db:
        release = _release(db)
        db.commit()
        binding = IntelligenceReleaseBinding(
            release_id=release.id,
            release_key=release.release_key,
            version=release.version,
            payload_checksum_sha256=release.payload_checksum_sha256,
        )

    def run(key: str) -> tuple[int, int]:
        with Session(engine) as db:
            request = db.get(PayerRequest, case["request_id"])
            assert request is not None
            result = generate_clinical_event_intelligence(
                db,
                actor_user_id=case["actor_user_id"],
                payer_request=request,
                idempotency_key=key,
                settings=settings,
                primary_provider=_UnavailableProvider(),
                primary_release=binding,
            )
            run_row = db.scalar(
                select(ClinicalEventIntelligenceRun).where(
                    ClinicalEventIntelligenceRun.id == result.artifact.run_id
                )
            )
            assert run_row is not None
            return run_row.run_version, result.artifact.artifact_version

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(run, "cei-concurrent-key-0001"),
            executor.submit(run, "cei-concurrent-key-0002"),
        ]
        versions = sorted(future.result(timeout=30) for future in futures)
    assert versions == [(1, 1), (2, 2)]
    with Session(engine) as db:
        artifacts = db.scalars(
            select(ClinicalEventIntelligenceArtifact).order_by(
                ClinicalEventIntelligenceArtifact.artifact_version
            )
        ).all()
        assert artifacts[1].predecessor_artifact_id == artifacts[0].id
    response = client.get(
        f"/api/v1/doctor/payer-requests/{case['request_id']}/intelligence",
        headers=case["doctor_headers"],
    )
    assert response.status_code == 200
    rendered = response.json()["artifact"]["requested_item_assessments"][0]
    assert rendered["state"] == "assessment_unavailable"
    assert rendered["label"] == "Synthetic panel"
    assert "scores" not in rendered
    assert "estimated_cost" not in rendered


def test_same_idempotency_key_concurrency_creates_one_artifact(
    client: TestClient, settings
) -> None:
    case = _case(client, "same-key-concurrency")
    settings = settings.model_copy(update={"clinical_event_intelligence_critic_enabled": False})
    with Session(engine) as db:
        release = _release(db)
        db.commit()
        binding = IntelligenceReleaseBinding(
            release_id=release.id,
            release_key=release.release_key,
            version=release.version,
            payload_checksum_sha256=release.payload_checksum_sha256,
        )

    def run() -> tuple[uuid.UUID, bool]:
        with Session(engine) as db:
            request = db.get(PayerRequest, case["request_id"])
            assert request is not None
            result = generate_clinical_event_intelligence(
                db,
                actor_user_id=case["actor_user_id"],
                payer_request=request,
                idempotency_key="cei-concurrent-same-key-0001",
                settings=settings,
                primary_provider=_UnavailableProvider(),
                primary_release=binding,
            )
            return result.artifact.id, result.idempotent_replay

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run), executor.submit(run)]
        results = [future.result(timeout=30) for future in futures]
    assert len({artifact_id for artifact_id, _ in results}) == 1
    assert sorted(replayed for _, replayed in results) == [False, True]
    with Session(engine) as db:
        assert len(db.scalars(select(ClinicalEventIntelligenceRun)).all()) == 1
        assert len(db.scalars(select(ClinicalEventIntelligenceArtifact)).all()) == 1


def test_idempotency_payload_conflict_after_exact_release_binding_change(
    client: TestClient, settings
) -> None:
    case = _case(client, "idempotency-conflict")
    settings = settings.model_copy(update={"clinical_event_intelligence_critic_enabled": False})
    with Session(engine) as db:
        first_release = _release(db, version="v1-idempotency")
        second_release = _release(db, version="v2-idempotency")
        db.flush()
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        first = generate_clinical_event_intelligence(
            db,
            actor_user_id=case["actor_user_id"],
            payer_request=request,
            idempotency_key="cei-binding-conflict-0001",
            settings=settings,
            primary_provider=_UnavailableProvider(),
            primary_release=IntelligenceReleaseBinding(
                release_id=first_release.id,
                release_key=first_release.release_key,
                version=first_release.version,
                payload_checksum_sha256=first_release.payload_checksum_sha256,
            ),
        )
        assert first.idempotent_replay is False
        with pytest.raises(IntelligenceGenerationConflict, match="idempotency_payload_conflict"):
            generate_clinical_event_intelligence(
                db,
                actor_user_id=case["actor_user_id"],
                payer_request=db.get(PayerRequest, case["request_id"]),
                idempotency_key="cei-binding-conflict-0001",
                settings=settings,
                primary_provider=_UnavailableProvider(),
                primary_release=IntelligenceReleaseBinding(
                    release_id=second_release.id,
                    release_key=second_release.release_key,
                    version=second_release.version,
                    payload_checksum_sha256=second_release.payload_checksum_sha256,
                ),
            )
        assert len(db.scalars(select(ClinicalEventIntelligenceRun)).all()) == 1
        assert len(db.scalars(select(ClinicalEventIntelligenceArtifact)).all()) == 1


def test_retrieval_enforces_payer_date_and_confidentiality_scope(client: TestClient) -> None:
    case = _case(client, "retrieval")
    with Session(engine) as db:
        request = db.get(PayerRequest, case["request_id"])
        assert request is not None
        frozen = build_frozen_clinical_event_snapshot(db, payer_request=request)
        admitted = _active_payer_price(
            db,
            release_key="cei-price-admitted",
            payer_organization_id=case["payer_org_id"],
            effective_from=date(2026, 1, 1),
        )
        _active_payer_price(
            db,
            release_key="cei-price-wrong-payer",
            payer_organization_id=uuid.uuid4(),
            effective_from=date(2026, 1, 1),
        )
        _active_payer_price(
            db,
            release_key="cei-price-stale",
            payer_organization_id=case["payer_org_id"],
            effective_from=date(2025, 1, 1),
            effective_to=date(2025, 12, 31),
        )
        _active_payer_price(
            db,
            release_key="cei-price-confidential",
            payer_organization_id=case["payer_org_id"],
            effective_from=date(2026, 1, 1),
            confidential=True,
        )
        _active_payer_price(
            db,
            release_key="cei-price-rights-denied",
            payer_organization_id=case["payer_org_id"],
            effective_from=date(2026, 1, 1),
            rights_status="denied",
        )
        _active_payer_price(
            db,
            release_key="cei-price-derivation-denied",
            payer_organization_id=case["payer_org_id"],
            effective_from=date(2026, 1, 1),
            derivation_allowed=False,
        )
        db.flush()
        manifest = retrieve_authorized_intelligence_sources(
            db,
            snapshot=frozen,
            payer_organization_id=str(case["payer_org_id"]),
        )
        assert [source.release_id for source in manifest.sources] == [str(admitted.id)]
        assert manifest.sources[0].source_type == "payer_price"
        assert len(manifest.sources[0].payload["price_items"]) == 1


def test_dedicated_local_fixture_is_idempotent_located_and_login_ready(
    client: TestClient, settings
) -> None:
    with Session(engine) as db:
        first = bootstrap_synthetic_clinical_event_intelligence(db, settings)
    with Session(engine) as db:
        second = bootstrap_synthetic_clinical_event_intelligence(db, settings)
        assert second.payer_request_id == first.payer_request_id
        request = db.get(PayerRequest, first.payer_request_id)
        assert request is not None
        assert request.clinical_event.metadata_json["data_class"] == "wholly_synthetic"
        assert request.clinical_event.hospital_id is not None
        assert request.clinical_event.clinic_id is not None
        assert len(request.lines) == 2
        frozen = build_frozen_clinical_event_snapshot(db, payer_request=request)
        manifest = retrieve_authorized_intelligence_sources(
            db,
            snapshot=frozen,
            payer_organization_id=str(request.payer_organization_id),
        )
        price_sources = [
            source for source in manifest.sources if source.source_type == "payer_price"
        ]
        assert len(price_sources) == 1
        assert len(price_sources[0].payload["price_items"]) == 1
        assert {line.service_code for line in frozen.requested_lines} == {
            "SYN-CEI-LAB-001",
            "SYN-CEI-EXPLORATORY-001",
        }
    for email, role in (
        (DOCTOR_EMAIL, "doctor"),
        (PATIENT_EMAIL, "patient"),
        (PAYER_EMAIL, "payer"),
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": LOCAL_ONLY_PASSWORD},
        )
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == role
