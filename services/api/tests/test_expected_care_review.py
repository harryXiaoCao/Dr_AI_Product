import copy
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import DBAPIError

from app.care_reference_engine import EvaluationContext, EvaluationRequest
from app.database import SessionLocal
from app.expected_care_candidates import (
    ProviderCandidateResponse,
    generate_expected_care_candidate,
)
from app.models import (
    DoctorProfile,
    ExpectedCareBaselineItem,
    ExpectedCareCandidateRequest,
    ExpectedCareCandidateResult,
    ExpectedCareClinicianResponse,
    ExpectedCarePublishedBaseline,
    GovernedActiveCareRelease,
    PayerMembership,
    PayerRequest,
    User,
)
from app.synthetic_care_reference import (
    install_synthetic_care_reference_bundle,
    synthetic_active_selection,
)
from tests.helpers import auth_header, register


class _Provider:
    def generate(self, *, provider_input, output_schema, settings):
        del output_schema, settings
        context = provider_input["context"]
        totals = provider_input["server_totals"]
        return ProviderCandidateResponse(
            output={
                "purpose_code": provider_input["purpose_code"],
                "purpose_contract_version": provider_input[
                    "purpose_contract_version"
                ],
                "schema_version": provider_input["schema_version"],
                "minimum_input_checksum_sha256": provider_input[
                    "minimum_input_checksum_sha256"
                ],
                "scenario_release_id": provider_input["scenario_release_id"],
                "reference_date": context["reference_date"],
                "jurisdiction": context["jurisdiction"],
                "region": context["region"],
                "facility_ownership": context["facility_ownership"],
                "facility_level": context["facility_level"],
                "currency": context["currency"],
                "assumptions": copy.deepcopy(
                    provider_input["allowed_assumptions"]
                ),
                "missing_information": copy.deepcopy(
                    provider_input["allowed_missing_information"]
                ),
                "attributable_exceptions": [],
                "confidence_category": "moderate",
                "confidence_limitations": copy.deepcopy(
                    provider_input["allowed_confidence_limitations"]
                ),
                "items": copy.deepcopy(provider_input["admitted_candidates"]),
                "total_low_minor": totals["total_low_minor"],
                "total_high_minor": totals["total_high_minor"],
                "release_lineage": copy.deepcopy(
                    provider_input["release_lineage"]
                ),
            },
            provider="deterministic_stub",
            model="stub-expected-care-v1",
            input_tokens=1,
            output_tokens=1,
            cost_microunits=1,
        )


def _register_payer(
    client: TestClient, email: str, organization: str
) -> tuple[dict, dict[str, str]]:
    digest = hashlib.sha1(email.encode()).hexdigest()[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": f"+1666{int(digest, 16) % 10_000_000:07d}",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "Payer reviewer",
                "organization_name": organization,
                "title": "Reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload, auth_header(payload["access_token"])


def _case(
    client: TestClient,
    settings,
    monkeypatch,
    suffix: str,
    *,
    payer_email: str | None = None,
):
    patient = register(
        client,
        email=f"baseline.patient.{suffix}@example.com",
        password="Patient9!",
        role="patient",
    )
    doctor = register(
        client,
        email=f"baseline.doctor.{suffix}@example.com",
        password="Doctor9!",
        role="doctor",
    )
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    care = client.get("/api/v1/patient/me/care", headers=patient_headers).json()
    patient_id = care["patient"]["patient_id"]
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
            "title": "Immutable expected-care baseline",
            "chief_complaint": "Synthetic baseline case",
            "status": "active",
        },
    ).json()
    monkeypatch.setattr(settings, "expected_care_candidate_enabled", True)
    monkeypatch.setattr(settings, "expected_care_provider", "deterministic_stub")
    monkeypatch.setattr(settings, "expected_care_model", "stub-expected-care-v1")
    with SessionLocal() as db:
        install_synthetic_care_reference_bundle(db)
        actor_id = db.scalar(
            select(User.id).where(
                User.email == f"baseline.doctor.{suffix}@example.com"
            )
        )
        payer_request_id = None
        if payer_email is not None:
            membership = db.scalar(
                select(PayerMembership)
                .join(User, User.id == PayerMembership.user_id)
                .where(User.email == payer_email)
            )
            doctor_profile = db.scalar(
                select(DoctorProfile).where(DoctorProfile.user_id == actor_id)
            )
            payer_request = PayerRequest(
                clinical_event_id=uuid.UUID(event["id"]),
                patient_id=uuid.UUID(patient_id),
                doctor_id=doctor_profile.id,
                payer_organization_id=membership.payer_organization_id,
                status="submitted",
                currency="CNY",
                requested_total_minor=2000,
                doctor_summary="Synthetic immutable payer request scope.",
            )
            db.add(payer_request)
            db.flush()
            payer_request_id = payer_request.id
        generated = generate_expected_care_candidate(
            db,
            actor_user_id=actor_id,
            patient_id=uuid.UUID(patient_id),
            clinical_event_id=uuid.UUID(event["id"]),
            selection=synthetic_active_selection(),
            request=EvaluationRequest(
                context=EvaluationContext(
                    evaluated_on=date(2026, 7, 25),
                    reference_date=date(2026, 7, 25),
                    jurisdiction="CN",
                    region="Synthetic Province",
                    encounter_type="outpatient",
                    facility_ownership="public",
                    facility_level="primary",
                    currency="CNY",
                    patient_age=42,
                )
            ),
            idempotency_key=f"candidate-{suffix}-001",
            settings=settings,
            provider=_Provider(),
            payer_request_id=payer_request_id,
        )
        result_id = str(generated.result.id)
        baseline_id = str(
            db.scalar(
                select(ExpectedCarePublishedBaseline.id).where(
                    ExpectedCarePublishedBaseline.candidate_result_id
                    == generated.result.id,
                    ExpectedCarePublishedBaseline.lifecycle_state
                    == "validated_baseline_published",
                )
            )
        )
        db.commit()
    return (
        patient_headers,
        doctor_headers,
        patient_id,
        event["id"],
        result_id,
        baseline_id,
        str(payer_request_id) if payer_request_id else None,
    )


def _response_url(patient_id: str, event_id: str, result_id: str) -> str:
    return (
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/"
        f"expected-care/candidates/{result_id}/responses"
    )


def test_validated_candidate_publishes_immutable_patient_visible_baseline(
    client, settings, monkeypatch
) -> None:
    patient_headers, doctor_headers, patient_id, event_id, result_id, baseline_id, _ = (
        _case(client, settings, monkeypatch, "published")
    )
    listed = client.get(
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/"
        "expected-care/candidates",
        headers=doctor_headers,
    )
    assert listed.status_code == 200
    item = listed.json()["items"][0]
    assert item["state"] == "validated_baseline_published"
    assert item["latest_clinician_position"] == "not_recorded"
    assert item["baseline_id"] == baseline_id

    patient = client.get(
        f"/api/v1/patient/clinical-events/{event_id}/expected-care-envelope",
        headers=patient_headers,
    )
    assert patient.status_code == 200
    body = patient.json()
    assert body["baseline_id"] == baseline_id
    assert body["state"] == "validated_baseline_published"
    assert body["latest_clinician_position"] == "not_recorded"
    assert "immutable system-generated" in body["disclaimer"]
    serialized = str(body)
    assert "reviewer_only_note" not in serialized
    assert "service_code" not in serialized

    with SessionLocal() as db:
        result = db.get(ExpectedCareCandidateResult, uuid.UUID(result_id))
        request = db.get(ExpectedCareCandidateRequest, result.candidate_request_id)
        baseline = db.get(ExpectedCarePublishedBaseline, uuid.UUID(baseline_id))
        assert result.lifecycle_state == "generated_pending_review"
        assert request.lifecycle_state == "generated_pending_review"
        assert baseline.legacy_doctor_review_id is None
        assert baseline.candidate_output_checksum_sha256 == result.output_checksum_sha256
        assert baseline.structured_difference_json["candidate_modified"] is False
        try:
            db.execute(
                update(ExpectedCarePublishedBaseline)
                .where(ExpectedCarePublishedBaseline.id == baseline.id)
                .values(total_low_minor=0)
            )
            db.flush()
        except DBAPIError:
            db.rollback()
        else:
            raise AssertionError("immutable baseline update unexpectedly succeeded")


def test_clinician_responses_append_without_changing_or_hiding_baseline(
    client, settings, monkeypatch
) -> None:
    patient_headers, doctor_headers, patient_id, event_id, result_id, baseline_id, _ = (
        _case(client, settings, monkeypatch, "responses")
    )
    url = _response_url(patient_id, event_id, result_id)
    original = client.get(
        f"/api/v1/patient/clinical-events/{event_id}/expected-care-envelope",
        headers=patient_headers,
    ).json()
    disagree_payload = {
        "position": "disagree",
        "expected_version": 0,
        "rationale": {
            "exception_code": "CLINICAL_CONTEXT_DIFFERS",
            "rationale": "The responsible clinician documents a different plan.",
            "patient_safe_summary": (
                "Your doctor recorded a different clinical view; the system "
                "baseline remains unchanged."
            ),
            "applies_to_item_keys": ["synthetic-therapy-course"],
        },
        "reviewer_only_note": "Visible only to the responsible clinical team.",
    }
    headers = {**doctor_headers, "Idempotency-Key": "response-disagree-0001"}
    first = client.post(url, headers=headers, json=disagree_payload)
    assert first.status_code == 200, first.text
    assert first.json()["lifecycle_state"] == "doctor_disagreed"
    replay = client.post(url, headers=headers, json=disagree_payload)
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    conflict = client.post(
        url,
        headers=headers,
        json={**disagree_payload, "reviewer_only_note": "Different content."},
    )
    assert conflict.status_code == 409

    second = client.post(
        url,
        headers={**doctor_headers, "Idempotency-Key": "response-exception-0002"},
        json={
            "position": "exception",
            "expected_version": 1,
            "rationale": {
                "exception_code": "ADDITIONAL_CARE_PROPOSED",
                "rationale": "Additional care is proposed outside this baseline.",
                "patient_safe_summary": (
                    "Additional care was proposed separately from the baseline."
                ),
                "applies_to_item_keys": [],
            },
        },
    )
    assert second.status_code == 200
    assert second.json()["lifecycle_state"] == "doctor_exception_recorded"
    assert second.json()["version"] == 2

    after = client.get(
        f"/api/v1/patient/clinical-events/{event_id}/expected-care-envelope",
        headers=patient_headers,
    )
    assert after.status_code == 200
    body = after.json()
    assert body["baseline_id"] == baseline_id
    assert body["total_low_minor"] == original["total_low_minor"]
    assert body["total_high_minor"] == original["total_high_minor"]
    assert body["items"] == original["items"]
    assert body["latest_clinician_position"] == "exception"
    assert len(body["clinician_responses"]) == 2
    assert "reviewer_only_note" not in str(body)

    with SessionLocal() as db:
        baselines = db.scalars(
            select(ExpectedCarePublishedBaseline).where(
                ExpectedCarePublishedBaseline.candidate_result_id
                == uuid.UUID(result_id),
                ExpectedCarePublishedBaseline.lifecycle_state
                == "validated_baseline_published",
            )
        ).all()
        assert len(baselines) == 1
        assert (
            db.scalar(
                select(func.count()).select_from(ExpectedCareClinicianResponse)
            )
            == 2
        )


def test_doctor_cannot_submit_edits_or_rejection_and_roles_are_isolated(
    client, settings, monkeypatch
) -> None:
    patient_headers, doctor_headers, patient_id, event_id, result_id, _, _ = _case(
        client, settings, monkeypatch, "isolation"
    )
    url = _response_url(patient_id, event_id, result_id)
    for invalid in (
        {"action": "reject", "expected_version": 0},
        {
            "position": "concur",
            "expected_version": 0,
            "items": [
                {
                    "item_key": "synthetic-therapy-course",
                    "quantity_low": 4,
                    "quantity_high": 4,
                }
            ],
        },
        {"position": "disagree", "expected_version": 0},
    ):
        response = client.post(
            url,
            headers={**doctor_headers, "Idempotency-Key": f"invalid-{uuid.uuid4()}"},
            json=invalid,
        )
        assert response.status_code == 422

    unrelated = register(
        client,
        email="baseline.unrelated.doctor@example.com",
        password="Doctor9!",
        role="doctor",
    )
    unrelated_headers = auth_header(unrelated["access_token"])
    for headers in (patient_headers, unrelated_headers):
        denied = client.post(
            url,
            headers={**headers, "Idempotency-Key": f"denied-{uuid.uuid4()}"},
            json={"position": "acknowledge", "expected_version": 0},
        )
        assert denied.status_code == 404
        assert denied.json()["error"]["code"] == "not_found"


def test_payer_sees_baseline_and_clinician_position_only_in_exact_scope(
    client, settings, monkeypatch
) -> None:
    payer, payer_headers = _register_payer(
        client, "baseline.payer.one@example.com", "Payer One"
    )
    _, other_headers = _register_payer(
        client, "baseline.payer.two@example.com", "Payer Two"
    )
    (
        _,
        doctor_headers,
        patient_id,
        event_id,
        result_id,
        baseline_id,
        payer_request_id,
    ) = _case(
        client,
        settings,
        monkeypatch,
        "payer",
        payer_email="baseline.payer.one@example.com",
    )
    concurred = client.post(
        _response_url(patient_id, event_id, result_id),
        headers={**doctor_headers, "Idempotency-Key": "response-payer-concur"},
        json={"position": "concur", "expected_version": 0},
    )
    assert concurred.status_code == 200
    authorized = client.get(
        f"/api/v1/payer/requests/{payer_request_id}/expected-care-envelope",
        headers=payer_headers,
    )
    assert authorized.status_code == 200, authorized.text
    body = authorized.json()
    assert body["system_baseline"]["baseline_id"] == baseline_id
    assert body["system_baseline"]["latest_clinician_position"] == "concur"
    assert body["ai_candidate"]["content_exposed"] is True
    assert body["deterministic_validation"]["baseline_modified"] is False
    assert body["clinician_response"]["can_modify_or_hide_baseline"] is False
    assert body["human_payer_review"]["reimbursement_decision_separate"] is True
    assert "reviewer_only_note" not in str(body)

    wrong_org = client.get(
        f"/api/v1/payer/requests/{payer_request_id}/expected-care-envelope",
        headers=other_headers,
    )
    assert wrong_org.status_code == 404
    payer_cannot_respond = client.post(
        _response_url(patient_id, event_id, result_id),
        headers={**payer_headers, "Idempotency-Key": "payer-cannot-respond"},
        json={"position": "concur", "expected_version": 1},
    )
    assert payer_cannot_respond.status_code == 404

    with SessionLocal() as db:
        db.execute(
            update(PayerMembership)
            .where(PayerMembership.user_id == uuid.UUID(payer["user"]["id"]))
            .values(status="revoked")
        )
        db.commit()
    revoked = client.get(
        f"/api/v1/payer/requests/{payer_request_id}/expected-care-envelope",
        headers=payer_headers,
    )
    assert revoked.status_code == 404


def test_response_fails_closed_on_release_drift_without_hiding_baseline(
    client, settings, monkeypatch
) -> None:
    patient_headers, doctor_headers, patient_id, event_id, result_id, _, _ = _case(
        client, settings, monkeypatch, "release-drift"
    )
    with SessionLocal() as db:
        db.execute(
            delete(GovernedActiveCareRelease).where(
                GovernedActiveCareRelease.release_type == "pricing_reference"
            )
        )
        db.commit()
    response = client.post(
        _response_url(patient_id, event_id, result_id),
        headers={
            **doctor_headers,
            "Idempotency-Key": "response-after-release-drift",
        },
        json={"position": "concur", "expected_version": 0},
    )
    assert response.status_code == 409
    assert response.json()["error"]["message"] == (
        "The admitted reference release changed or is no longer current."
    )
    patient = client.get(
        f"/api/v1/patient/clinical-events/{event_id}/expected-care-envelope",
        headers=patient_headers,
    )
    assert patient.status_code == 200
    assert patient.json()["state"] == "validated_baseline_published"
    with SessionLocal() as db:
        assert db.scalar(select(ExpectedCareClinicianResponse)) is None


def test_concurrent_responses_create_one_transition(
    client, settings, monkeypatch
) -> None:
    _, doctor_headers, patient_id, event_id, result_id, _, _ = _case(
        client, settings, monkeypatch, "concurrent"
    )

    def submit(index: int):
        return client.post(
            _response_url(patient_id, event_id, result_id),
            headers={
                **doctor_headers,
                "Idempotency-Key": f"response-concurrent-{index:04d}",
            },
            json={"position": "acknowledge", "expected_version": 0},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(submit, (1, 2)))
    assert sorted(response.status_code for response in responses) == [200, 409]
    with SessionLocal() as db:
        assert len(db.scalars(select(ExpectedCareClinicianResponse)).all()) == 1
        assert (
            len(
                db.scalars(
                    select(ExpectedCarePublishedBaseline).where(
                        ExpectedCarePublishedBaseline.lifecycle_state
                        == "validated_baseline_published"
                    )
                ).all()
            )
            == 1
        )
        assert (
            len(
                db.scalars(
                    select(ExpectedCareBaselineItem).where(
                        ExpectedCareBaselineItem.baseline_id.is_not(None)
                    )
                ).all()
            )
            >= 1
        )
