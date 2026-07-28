"""Authorized responses to immutable, system-published expected-care baselines.

No clinician or payer can alter, reject, or hide a validated baseline. A doctor
may append an attributable position or clinical exception after deterministic
revalidation. Payer adjudication remains a separate human workflow.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.care_reference_engine import (
    ENGINE_CONTRACT_VERSION,
    EvaluationContext,
    EvaluationRequest,
    evaluate_care_reference,
)
from app.care_reference_integration import (
    ActiveReleaseSelection,
    CareReferenceResolutionError,
    build_care_reference_scope_key,
    resolve_active_care_reference_bundle,
)
from app.cost_estimation_facts import serialize_cost_fact_snapshot
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.expected_care_baseline import (
    PUBLISHED_BASELINE_STATE,
    ensure_validated_baseline,
)
from app.expected_care_candidates import _checksum, _lineage, _release_rows, _validate_candidate
from app.models import (
    AuditEvent,
    CareRelationship,
    ClinicalEvent,
    DoctorProfile,
    ExpectedCareBaselineItem,
    ExpectedCareCandidateRequest,
    ExpectedCareCandidateResult,
    ExpectedCareClinicianRationale,
    ExpectedCareClinicianResponse,
    ExpectedCareLifecycleEvent,
    ExpectedCarePublishedBaseline,
    ExpectedCareResponseHead,
    GovernedCareRelease,
    PatientProfile,
    PayerRequest,
    UserRole,
)
from app.payer_scope import require_active_payer_membership

router = APIRouter(prefix="/api/v1", tags=["expected-care baseline"])

_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,119}$")
_INVALID = "This expected-care baseline did not pass deterministic validation."
_STALE = "The admitted reference release changed or is no longer current."
_CONFLICT = "The clinician-response state changed. Refresh before trying again."
_POSITION_STATE = {
    "acknowledge": "doctor_acknowledged",
    "concur": "doctor_concurred",
    "disagree": "doctor_disagreed",
    "exception": "doctor_exception_recorded",
}


class ClinicalRationaleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    exception_code: str = Field(min_length=2, max_length=120)
    rationale: str = Field(min_length=4, max_length=4000)
    patient_safe_summary: str | None = Field(default=None, max_length=1000)
    applies_to_item_keys: list[str] = Field(default_factory=list, max_length=40)


class ClinicianResponseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    position: Literal["acknowledge", "concur", "disagree", "exception"]
    expected_version: int = Field(ge=0)
    rationale: ClinicalRationaleInput | None = None
    reviewer_only_note: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def position_shape(self) -> ClinicianResponseInput:
        if self.position in {"disagree", "exception"} and self.rationale is None:
            raise ValueError(
                "Disagreement and clinical exceptions require an attributable rationale."
            )
        return self


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _conflict(message: str = _CONFLICT) -> ApiError:
    return ApiError(409, "conflict", message)


def _lineage_release(db: Session, item: dict[str, object]) -> GovernedCareRelease | None:
    try:
        return db.get(GovernedCareRelease, uuid.UUID(str(item["release_id"])))
    except (KeyError, TypeError, ValueError):
        return None


def _doctor_scope(
    db: Session,
    *,
    user_id: uuid.UUID,
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
) -> tuple[DoctorProfile, ClinicalEvent]:
    doctor = db.scalar(
        select(DoctorProfile)
        .join(CareRelationship, CareRelationship.doctor_id == DoctorProfile.id)
        .where(
            DoctorProfile.user_id == user_id,
            CareRelationship.patient_id == patient_id,
            CareRelationship.is_active.is_(True),
        )
    )
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == event_id,
            ClinicalEvent.patient_id == patient_id,
        )
    )
    if doctor is None or event is None or event.doctor_id != doctor.id:
        raise _not_found()
    return doctor, event


def _candidate(
    db: Session,
    *,
    candidate_result_id: uuid.UUID,
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
) -> tuple[ExpectedCareCandidateRequest, ExpectedCareCandidateResult]:
    result = db.get(ExpectedCareCandidateResult, candidate_result_id)
    request = (
        db.get(ExpectedCareCandidateRequest, result.candidate_request_id)
        if result is not None
        else None
    )
    if (
        result is None
        or request is None
        or request.patient_id != patient_id
        or request.clinical_event_id != event_id
    ):
        raise _not_found()
    return request, result


def _selection(request: ExpectedCareCandidateRequest) -> ActiveReleaseSelection:
    keys = {
        str(item["release_type"]): str(item["release_key"])
        for item in request.release_lineage_json
        if isinstance(item, dict) and "release_type" in item and "release_key" in item
    }
    context = request.minimum_input_json.get("context")
    if not isinstance(context, dict):
        raise _conflict(_INVALID)
    try:
        return ActiveReleaseSelection(
            scenario_key=keys["scenario_definition"],
            care_plan_key=keys["care_plan"],
            pricing_reference_key=keys["pricing_reference"],
            utilization_rule_key=keys["utilization_rule"],
            scope_key=build_care_reference_scope_key(
                jurisdiction=str(context["jurisdiction"]),
                region=str(context["region"]),
                facility_ownership=str(context["facility_ownership"]),
                facility_level=str(context["facility_level"]),
                currency=str(context["currency"]),
            ),
        )
    except (KeyError, TypeError, ValueError):
        raise _conflict(_INVALID) from None


def _context(request: ExpectedCareCandidateRequest) -> EvaluationContext:
    value = request.minimum_input_json.get("context")
    if not isinstance(value, dict):
        raise _conflict(_INVALID)
    try:
        return EvaluationContext(
            evaluated_on=datetime.now(UTC).date(),
            reference_date=date.fromisoformat(str(value["reference_date"])),
            jurisdiction=str(value["jurisdiction"]),
            region=str(value["region"]),
            encounter_type=str(value["encounter_type"]),
            facility_ownership=str(value["facility_ownership"]),
            facility_level=str(value["facility_level"]),
            currency=str(value["currency"]),
            patient_age=(
                int(value["patient_age"]) if value.get("patient_age") is not None else None
            ),
        )
    except (KeyError, TypeError, ValueError):
        raise _conflict(_INVALID) from None


def _deterministic_revalidation(
    db: Session,
    *,
    request: ExpectedCareCandidateRequest,
    result: ExpectedCareCandidateResult,
    baseline: ExpectedCarePublishedBaseline,
):
    if (
        request.lifecycle_state != "generated_pending_review"
        or result.lifecycle_state != "generated_pending_review"
        or request.validation_outcome != "validated"
        or baseline.lifecycle_state != PUBLISHED_BASELINE_STATE
        or baseline.candidate_output_checksum_sha256 != result.output_checksum_sha256
    ):
        raise _conflict(_INVALID)
    if _checksum(result.candidate_json) != result.output_checksum_sha256:
        raise _conflict(_INVALID)
    try:
        bundle = resolve_active_care_reference_bundle(db, selection=_selection(request))
    except CareReferenceResolutionError:
        raise _conflict(_STALE) from None
    current_lineage = _lineage(_release_rows(db, bundle))
    if (
        current_lineage != request.release_lineage_json
        or current_lineage != baseline.release_lineage_json
    ):
        raise _conflict(_STALE)
    deterministic = evaluate_care_reference(
        scenario=bundle.scenario,
        plan=bundle.plan,
        pricing=bundle.pricing,
        utilization=bundle.utilization,
        request=EvaluationRequest(context=_context(request)),
    )
    if deterministic.status != "comparison_not_ready" or not deterministic.lines:
        raise _conflict(_INVALID)
    candidate, reasons = _validate_candidate(
        output=result.candidate_json,
        minimum_input=request.minimum_input_json,
        minimum_input_checksum=request.minimum_input_checksum_sha256,
        deterministic=deterministic,
    )
    if candidate is None or reasons:
        raise _conflict(_INVALID)
    baseline_items = db.scalars(
        select(ExpectedCareBaselineItem)
        .where(ExpectedCareBaselineItem.baseline_id == baseline.id)
        .order_by(ExpectedCareBaselineItem.item_key)
    ).all()
    candidate_items = sorted(candidate.items, key=lambda item: item.item_key)
    if len(baseline_items) != len(candidate_items):
        raise _conflict(_INVALID)
    for stored, admitted in zip(baseline_items, candidate_items, strict=True):
        if (
            stored.item_key != admitted.item_key
            or stored.code_system != admitted.code_system
            or stored.service_code != admitted.service_code
            or stored.unit != admitted.unit
            or stored.quantity_low != admitted.quantity_low
            or stored.quantity_high != admitted.quantity_high
            or stored.amount_low_minor != admitted.amount_low_minor
            or stored.amount_high_minor != admitted.amount_high_minor
        ):
            raise _conflict(_INVALID)
    if baseline.total_low_minor != sum(
        item.amount_low_minor for item in candidate.items
    ) or baseline.total_high_minor != sum(item.amount_high_minor for item in candidate.items):
        raise _conflict(_INVALID)
    return deterministic, candidate, current_lineage


def _head(
    db: Session,
    *,
    result: ExpectedCareCandidateResult,
    baseline: ExpectedCarePublishedBaseline,
) -> ExpectedCareResponseHead:
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"expected-care-response:{result.id}"},
    )
    row = db.get(ExpectedCareResponseHead, result.id)
    if row is None:
        row = ExpectedCareResponseHead(
            candidate_result_id=result.id,
            published_baseline_id=baseline.id,
            lifecycle_state=PUBLISHED_BASELINE_STATE,
        )
        db.add(row)
        db.flush()
    if row.published_baseline_id != baseline.id or row.lifecycle_state != PUBLISHED_BASELINE_STATE:
        raise _conflict(_INVALID)
    return row


def _response_result(response: ExpectedCareClinicianResponse, *, replay: bool) -> dict[str, object]:
    return {
        "response_id": response.id,
        "review_id": response.id,
        "position": response.action,
        "lifecycle_state": _POSITION_STATE[response.action],
        "version": response.resulting_head_version,
        "baseline_id": response.baseline_id,
        "idempotent_replay": replay,
        "created_at": response.created_at,
    }


@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/"
    "{candidate_result_id}/responses"
)
@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/"
    "{candidate_result_id}/reviews",
    include_in_schema=False,
)
def submit_clinician_response(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    candidate_result_id: uuid.UUID,
    payload: ClinicianResponseInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    if idempotency_key is None or not _KEY.fullmatch(idempotency_key):
        raise ApiError(
            422,
            "validation_failed",
            "A valid Idempotency-Key header is required.",
        )
    doctor, _ = _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    request, result = _candidate(
        db,
        candidate_result_id=candidate_result_id,
        patient_id=patient_id,
        event_id=event_id,
    )
    if request.payer_request_id is not None:
        payer_request = db.get(PayerRequest, request.payer_request_id)
        if (
            payer_request is None
            or payer_request.patient_id != patient_id
            or payer_request.clinical_event_id != event_id
            or payer_request.doctor_id != doctor.id
        ):
            raise _not_found()
    baseline = ensure_validated_baseline(db, request=request, result=result)
    if baseline is None:
        raise _conflict(_INVALID)
    checksum = _checksum(payload.model_dump(mode="json", exclude_none=True))
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"expected-care-idempotency:{user.id}:{event_id}:{idempotency_key}"},
    )
    existing = db.scalar(
        select(ExpectedCareClinicianResponse).where(
            ExpectedCareClinicianResponse.actor_user_id == user.id,
            ExpectedCareClinicianResponse.clinical_event_id == event_id,
            ExpectedCareClinicianResponse.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_checksum_sha256 != checksum:
            raise _conflict("The idempotency key was already used with different content.")
        return _response_result(existing, replay=True)
    head = _head(db, result=result, baseline=baseline)
    if head.version != payload.expected_version:
        raise _conflict()
    deterministic, candidate, lineage = _deterministic_revalidation(
        db,
        request=request,
        result=result,
        baseline=baseline,
    )
    if payload.rationale is not None:
        allowed_keys = {item.item_key for item in candidate.items}
        if not set(payload.rationale.applies_to_item_keys).issubset(allowed_keys):
            raise ApiError(
                422,
                "deterministic_disagreement",
                "The rationale refers to an item outside the immutable baseline.",
            )
    next_version = head.version + 1
    response = ExpectedCareClinicianResponse(
        candidate_result_id=result.id,
        actor_user_id=user.id,
        doctor_id=doctor.id,
        patient_id=patient_id,
        clinical_event_id=event_id,
        payer_request_id=request.payer_request_id,
        baseline_id=baseline.id,
        action=payload.position,
        idempotency_key=idempotency_key,
        request_checksum_sha256=checksum,
        accepted_head_version=head.version,
        resulting_head_version=next_version,
        deterministic_engine_contract_version=ENGINE_CONTRACT_VERSION,
        deterministic_input_checksum_sha256=deterministic.input_checksum_sha256,
        deterministic_result_checksum_sha256=deterministic.result_checksum_sha256,
        deterministic_validation_json={
            "status": "validated",
            "validated_at": datetime.now(UTC).isoformat(),
            "reason_codes": list(deterministic.reason_codes),
            "integer_minor_unit_arithmetic": True,
            "deterministic_wins": True,
            "baseline_modified": False,
        },
        release_lineage_json=lineage,
        reviewer_only_note=payload.reviewer_only_note,
    )
    db.add(response)
    db.flush()
    if payload.rationale is not None:
        db.add(
            ExpectedCareClinicianRationale(
                clinician_response_id=response.id,
                baseline_id=baseline.id,
                exception_code=payload.rationale.exception_code,
                rationale=payload.rationale.rationale,
                patient_safe_summary=payload.rationale.patient_safe_summary,
                applies_to_item_keys_json=payload.rationale.applies_to_item_keys,
            )
        )
    state = _POSITION_STATE[payload.position]
    db.add(
        ExpectedCareLifecycleEvent(
            candidate_result_id=result.id,
            doctor_review_id=response.id,
            envelope_id=baseline.id,
            actor_user_id=user.id,
            lifecycle_state=state,
            metadata_json={
                "response_version": next_version,
                "position": payload.position,
                "baseline_modified": False,
                "baseline_visible": True,
            },
        )
    )
    head.version = next_version
    head.published_baseline_id = baseline.id
    head.lifecycle_state = PUBLISHED_BASELINE_STATE
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            patient_id=patient_id,
            event_type="expected_care_clinician_response_submitted",
            resource_type="expected_care_clinician_response",
            resource_id=response.id,
            metadata_json={
                "position": payload.position,
                "lifecycle_state": state,
                "response_version": next_version,
                "baseline_modified": False,
                "payer_request_linked": request.payer_request_id is not None,
                "content_free": True,
            },
        )
    )
    db.commit()
    db.refresh(response)
    return _response_result(response, replay=False)


def _response_payload(
    db: Session,
    response: ExpectedCareClinicianResponse,
    *,
    role: str,
) -> dict[str, object]:
    rationale = db.scalar(
        select(ExpectedCareClinicianRationale).where(
            ExpectedCareClinicianRationale.clinician_response_id == response.id
        )
    )
    payload: dict[str, object] = {
        "response_id": response.id,
        "position": response.action,
        "state": _POSITION_STATE.get(response.action, response.action),
        "version": response.resulting_head_version,
        "created_at": response.created_at,
        "baseline_modified": False,
    }
    if rationale is not None:
        payload["patient_safe_summary"] = rationale.patient_safe_summary
        if role in {"doctor", "payer"}:
            payload["clinical_rationale"] = {
                "exception_code": rationale.exception_code,
                "rationale": rationale.rationale,
                "applies_to_item_keys": rationale.applies_to_item_keys_json,
            }
    if role == "doctor" and response.reviewer_only_note:
        payload["reviewer_only_note"] = response.reviewer_only_note
    return payload


def _responses(
    db: Session,
    baseline: ExpectedCarePublishedBaseline,
    *,
    role: str,
) -> list[dict[str, object]]:
    rows = db.scalars(
        select(ExpectedCareClinicianResponse)
        .where(ExpectedCareClinicianResponse.baseline_id == baseline.id)
        .order_by(ExpectedCareClinicianResponse.resulting_head_version)
    ).all()
    return [_response_payload(db, row, role=role) for row in rows]


def _candidate_public(
    db: Session,
    request: ExpectedCareCandidateRequest,
    result: ExpectedCareCandidateResult,
) -> dict[str, object]:
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline).where(
            ExpectedCarePublishedBaseline.candidate_result_id == result.id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
    )
    head = db.get(ExpectedCareResponseHead, result.id)
    responses = _responses(db, baseline, role="doctor") if baseline else []
    candidate = result.candidate_json
    fact_snapshot = request.minimum_input_json.get("clinical_event_fact_snapshot")
    return {
        "candidate_result_id": result.id,
        "candidate_request_id": request.id,
        "baseline_id": baseline.id if baseline else None,
        "state": baseline.lifecycle_state if baseline else result.lifecycle_state,
        "response_version": head.version if head else 0,
        "review_version": head.version if head else 0,
        "latest_clinician_position": (responses[-1]["position"] if responses else "not_recorded"),
        "clinician_responses": responses,
        "created_at": result.created_at,
        "currency": result.currency,
        "total_low_minor": result.total_low_minor,
        "total_high_minor": result.total_high_minor,
        "assumptions": candidate.get("assumptions", []),
        "missing_information": candidate.get("missing_information", []),
        "limitations": candidate.get("confidence_limitations", []),
        "items": candidate.get("items", []),
        "references": [
            {
                **item,
                "effective_from": (str(release.effective_from) if release is not None else None),
                "effective_to": (
                    str(release.effective_to)
                    if release is not None and release.effective_to is not None
                    else None
                ),
                "source_authority": (release.source_authority if release is not None else None),
            }
            for item in request.release_lineage_json
            if isinstance(item, dict)
            for release in [_lineage_release(db, item)]
        ],
        "reference_date": candidate.get("reference_date"),
        "validation": {
            "state": request.validation_outcome,
            "deterministic_engine_contract_version": (result.deterministic_engine_contract_version),
            "candidate_checksum_sha256": result.output_checksum_sha256,
            "baseline_modified": False,
        },
        "cost_estimation_fact_snapshot": serialize_cost_fact_snapshot(
            fact_snapshot,
            role="doctor",
        ),
    }


@router.get("/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates")
def list_expected_care_baselines(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    requests = db.scalars(
        select(ExpectedCareCandidateRequest)
        .where(
            ExpectedCareCandidateRequest.patient_id == patient_id,
            ExpectedCareCandidateRequest.clinical_event_id == event_id,
            ExpectedCareCandidateRequest.lifecycle_state == "generated_pending_review",
        )
        .order_by(ExpectedCareCandidateRequest.created_at.desc())
    ).all()
    items = []
    for request in requests:
        result = db.scalar(
            select(ExpectedCareCandidateResult).where(
                ExpectedCareCandidateResult.candidate_request_id == request.id
            )
        )
        if result is not None:
            items.append(_candidate_public(db, request, result))
    return {"items": items}


@router.get(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/"
    "{candidate_result_id}"
)
def read_expected_care_baseline(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    candidate_result_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    request, result = _candidate(
        db,
        candidate_result_id=candidate_result_id,
        patient_id=patient_id,
        event_id=event_id,
    )
    return _candidate_public(db, request, result)


def _baseline_payload(
    db: Session,
    baseline: ExpectedCarePublishedBaseline,
    *,
    role: str,
) -> dict[str, object]:
    result = db.get(ExpectedCareCandidateResult, baseline.candidate_result_id)
    request = (
        db.get(ExpectedCareCandidateRequest, result.candidate_request_id)
        if result is not None
        else None
    )
    fact_snapshot = (
        request.minimum_input_json.get("clinical_event_fact_snapshot")
        if request is not None
        else None
    )
    items = db.scalars(
        select(ExpectedCareBaselineItem)
        .where(ExpectedCareBaselineItem.baseline_id == baseline.id)
        .order_by(ExpectedCareBaselineItem.item_key)
    ).all()
    responses = _responses(db, baseline, role=role)
    source_dates = []
    for lineage_item in baseline.release_lineage_json:
        if not isinstance(lineage_item, dict):
            continue
        release = _lineage_release(db, lineage_item)
        source_dates.append(
            {
                "release_type": lineage_item.get("release_type"),
                "release_id": lineage_item.get("release_id"),
                "version": lineage_item.get("version"),
                "payload_checksum_sha256": lineage_item.get("payload_checksum_sha256"),
                "effective_from": str(release.effective_from) if release else None,
                "effective_to": (
                    str(release.effective_to)
                    if release is not None and release.effective_to is not None
                    else None
                ),
                "source_authority": (release.source_authority if release is not None else None),
            }
        )
    latest_safe_summary = next(
        (
            str(item["patient_safe_summary"])
            for item in reversed(responses)
            if item.get("patient_safe_summary")
        ),
        None,
    )
    base: dict[str, object] = {
        "baseline_id": baseline.id,
        "envelope_id": baseline.id,
        "clinical_event_id": baseline.clinical_event_id,
        "version": baseline.version,
        "state": baseline.lifecycle_state,
        "currency": baseline.currency,
        "amount_type": baseline.amount_type,
        "total_low_minor": baseline.total_low_minor,
        "total_high_minor": baseline.total_high_minor,
        "assumptions": baseline.assumptions_json,
        "missing_information": baseline.missing_information_json,
        "limitations": baseline.limitations_json,
        "source_effective_dates": source_dates,
        "items": [
            {
                "item_key": item.item_key,
                "category": item.category,
                "unit": item.unit,
                "quantity_low": item.quantity_low,
                "quantity_high": item.quantity_high,
                "amount_low_minor": item.amount_low_minor,
                "amount_high_minor": item.amount_high_minor,
            }
            for item in items
        ],
        "latest_clinician_position": (responses[-1]["position"] if responses else "not_recorded"),
        "clinician_responses": responses,
        "patient_safe_rationale": latest_safe_summary,
        "responsible_next_action": (
            "Discuss the baseline and any clinician difference with the responsible "
            "doctor; payer reimbursement remains a separate decision."
        ),
        "disclaimer": (
            "This immutable system-generated reference range is not a quote, bill, "
            "coverage determination, reimbursement amount, prescribed care plan, or "
            "final patient responsibility."
        ),
        "created_at": baseline.created_at,
        "cost_estimation_fact_snapshot": serialize_cost_fact_snapshot(
            fact_snapshot,
            role=role if role in {"doctor", "patient", "payer"} else "patient",
        ),
    }
    if role in {"doctor", "payer"}:
        base["release_lineage"] = baseline.release_lineage_json
        base["candidate_output_checksum_sha256"] = baseline.candidate_output_checksum_sha256
        base["baseline_modified"] = False
    return base


@router.get(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/"
    "{candidate_result_id}/history"
)
def doctor_history(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    candidate_result_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    request, result = _candidate(
        db,
        candidate_result_id=candidate_result_id,
        patient_id=patient_id,
        event_id=event_id,
    )
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline).where(
            ExpectedCarePublishedBaseline.candidate_result_id == result.id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
    )
    if baseline is None:
        raise _not_found()
    legacy = db.scalars(
        select(ExpectedCarePublishedBaseline)
        .where(
            ExpectedCarePublishedBaseline.candidate_result_id == result.id,
            ExpectedCarePublishedBaseline.lifecycle_state == "legacy_doctor_review_record",
        )
        .order_by(ExpectedCarePublishedBaseline.version)
    ).all()
    return {
        "candidate": _candidate_public(db, request, result),
        "published_baseline": _baseline_payload(db, baseline, role="doctor"),
        "clinician_responses": _responses(db, baseline, role="doctor"),
        "legacy_doctor_review_records": [
            {
                "record_id": row.id,
                "version": row.version,
                "state": row.lifecycle_state,
                "created_at": row.created_at,
            }
            for row in legacy
        ],
    }


def _active_baseline_for_event(
    db: Session, *, patient_id: uuid.UUID, event_id: uuid.UUID
) -> ExpectedCarePublishedBaseline | None:
    return db.scalar(
        select(ExpectedCarePublishedBaseline)
        .where(
            ExpectedCarePublishedBaseline.patient_id == patient_id,
            ExpectedCarePublishedBaseline.clinical_event_id == event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
        .order_by(ExpectedCarePublishedBaseline.created_at.desc())
    )


@router.get("/patient/clinical-events/{event_id}/expected-care-envelope")
def patient_baseline(event_id: uuid.UUID, db: DbSession, user: CurrentUser) -> dict[str, object]:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    if patient is None:
        raise _not_found()
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == event_id,
            ClinicalEvent.patient_id == patient.id,
        )
    )
    if event is None:
        raise _not_found()
    baseline = _active_baseline_for_event(db, patient_id=patient.id, event_id=event_id)
    if baseline is None:
        raise _not_found()
    return _baseline_payload(db, baseline, role="patient")


@router.get("/payer/requests/{payer_request_id}/expected-care-envelope")
def payer_baseline(
    payer_request_id: uuid.UUID, db: DbSession, user: CurrentUser
) -> dict[str, object]:
    membership = require_active_payer_membership(db, user)
    request = db.get(PayerRequest, payer_request_id)
    if request is None or request.payer_organization_id != membership.payer_organization_id:
        raise _not_found()
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline).where(
            ExpectedCarePublishedBaseline.payer_request_id == request.id,
            ExpectedCarePublishedBaseline.patient_id == request.patient_id,
            ExpectedCarePublishedBaseline.clinical_event_id == request.clinical_event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
    )
    if baseline is None:
        raise _not_found()
    return {
        "system_baseline": _baseline_payload(db, baseline, role="payer"),
        "ai_candidate": {
            "state": "validated_and_preserved",
            "content_exposed": True,
            "candidate_output_checksum_sha256": (baseline.candidate_output_checksum_sha256),
        },
        "deterministic_validation": {
            "state": "validated",
            "authority": "server",
            "integer_minor_unit_arithmetic": True,
            "baseline_modified": False,
        },
        "clinician_response": {
            "latest_position": _baseline_payload(db, baseline, role="payer")[
                "latest_clinician_position"
            ],
            "can_modify_or_hide_baseline": False,
        },
        "submitted_facts": {
            "payer_request_id": request.id,
            "state": request.status,
            "currency": request.currency,
            "requested_total_minor": request.requested_total_minor,
        },
        "human_payer_review": {
            "state": request.status,
            "automated_decision": False,
            "clinical_approval_control": False,
            "reimbursement_decision_separate": True,
        },
    }
