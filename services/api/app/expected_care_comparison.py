"""Immutable, model-free expected-care comparisons over admitted facts."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.expected_care_review import _doctor_scope
from app.models import (
    AuditEvent,
    CareCostItem,
    ClinicalEvent,
    ClinicalService,
    ExpectedCareBaselineItem,
    ExpectedCareComparison,
    ExpectedCareComparisonEvent,
    ExpectedCareComparisonItem,
    ExpectedCarePublishedBaseline,
    GovernedCareRelease,
    GovernedActiveCareRelease,
    PatientProfile,
    PayerMembership,
    PayerRequest,
    PayerRequestLine,
    User,
    UserRole,
)
from app.payer_scope import require_active_payer_membership

router = APIRouter(prefix="/api/v1", tags=["expected-care comparison"])

COMPARISON_CONTRACT_VERSION = "expected-care-comparison-v1-2026-07-26"
PUBLISHED_BASELINE_STATE = "validated_baseline_published"
COMPARISON_LABELS = {
    "within_reference_range",
    "below_reference_range",
    "above_reference_range",
    "not_comparable",
    "missing_cost",
}
_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,119}$")


class ComparisonInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    include_submitted_facts: bool = True


def _checksum(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _conflict(message: str) -> ApiError:
    return ApiError(409, "conflict", message)


def _label(value: int | None, low: int, high: int) -> str:
    if value is None:
        return "not_comparable"
    if value < low:
        return "below_reference_range"
    if value > high:
        return "above_reference_range"
    return "within_reference_range"


def _baseline(
    db: Session,
    *,
    baseline_id: uuid.UUID,
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
) -> ExpectedCarePublishedBaseline:
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline).where(
            ExpectedCarePublishedBaseline.id == baseline_id,
            ExpectedCarePublishedBaseline.patient_id == patient_id,
            ExpectedCarePublishedBaseline.clinical_event_id == event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
    )
    if baseline is None:
        raise _not_found()
    return baseline


def _verify_reference_lineage(
    db: Session, baseline: ExpectedCarePublishedBaseline
) -> list[dict[str, object]]:
    checksums: list[dict[str, object]] = []
    for value in baseline.release_lineage_json:
        if not isinstance(value, dict):
            raise _conflict("The baseline reference lineage is invalid.")
        try:
            release_id = uuid.UUID(str(value["release_id"]))
            expected_checksum = str(value["payload_checksum_sha256"])
        except (KeyError, TypeError, ValueError):
            raise _conflict("The baseline reference lineage is invalid.") from None
        release = db.get(GovernedCareRelease, release_id)
        active_pointer = (
            db.scalar(
                select(GovernedActiveCareRelease.id).where(
                    GovernedActiveCareRelease.release_id == release_id
                )
            )
            if release is not None
            else None
        )
        if (
            release is None
            or release.payload_checksum_sha256 != expected_checksum
            or active_pointer is None
        ):
            raise _conflict(
                "The baseline reference release is stale, inactive, or checksum-drifted."
            )
        checksums.append(
            {
                "release_type": release.release_type,
                "release_id": str(release.id),
                "version": release.version,
                "payload_checksum_sha256": release.payload_checksum_sha256,
            }
        )
    return checksums


def _scope_snapshots(
    db: Session,
    *,
    baseline: ExpectedCarePublishedBaseline,
    include_submitted_facts: bool,
) -> tuple[
    list[ExpectedCareBaselineItem],
    list[dict[str, object]],
    list[dict[str, object]],
    PayerRequest | None,
]:
    items = db.scalars(
        select(ExpectedCareBaselineItem)
        .where(ExpectedCareBaselineItem.baseline_id == baseline.id)
        .order_by(ExpectedCareBaselineItem.item_key)
    ).all()
    if not items:
        raise _conflict("The immutable baseline has no comparable items.")

    services = db.scalars(
        select(ClinicalService)
        .where(
            ClinicalService.patient_id == baseline.patient_id,
            ClinicalService.clinical_event_id == baseline.clinical_event_id,
            ClinicalService.status.in_(("completed", "delivered", "performed")),
        )
        .order_by(ClinicalService.created_at, ClinicalService.id)
    ).all()
    costs = db.scalars(
        select(CareCostItem).where(
            CareCostItem.patient_id == baseline.patient_id,
            CareCostItem.clinical_event_id == baseline.clinical_event_id,
        )
    ).all()
    cost_by_service = {
        row.clinical_service_id: row for row in costs if row.clinical_service_id is not None
    }
    delivered = []
    for service in services:
        cost = cost_by_service.get(service.id)
        delivered.append(
            {
                "clinical_service_id": str(service.id),
                "service_code": service.service_code,
                "status": service.status,
                "performed_at": (
                    service.performed_at.isoformat() if service.performed_at else None
                ),
                "care_cost_item_id": str(cost.id) if cost else None,
                "pricing_state": cost.pricing_state if cost else "missing",
                "quantity": cost.quantity if cost else None,
                "currency": cost.currency if cost else None,
                "actual_cost_minor": cost.actual_cost_minor if cost else None,
            }
        )

    request = None
    submitted: list[dict[str, object]] = []
    if baseline.payer_request_id is not None:
        request = db.get(PayerRequest, baseline.payer_request_id)
        if (
            request is None
            or request.patient_id != baseline.patient_id
            or request.clinical_event_id != baseline.clinical_event_id
        ):
            raise _conflict("The payer-request scope does not match the baseline.")
    if include_submitted_facts and request is not None:
        lines = db.scalars(
            select(PayerRequestLine)
            .where(PayerRequestLine.payer_request_id == request.id)
            .order_by(PayerRequestLine.created_at, PayerRequestLine.id)
        ).all()
        for line in lines:
            cost = db.get(CareCostItem, line.care_cost_item_id) if line.care_cost_item_id else None
            service = (
                db.get(ClinicalService, cost.clinical_service_id)
                if cost is not None and cost.clinical_service_id is not None
                else None
            )
            if (
                cost is None
                or service is None
                or cost.patient_id != baseline.patient_id
                or cost.clinical_event_id != baseline.clinical_event_id
                or service.patient_id != baseline.patient_id
                or service.clinical_event_id != baseline.clinical_event_id
            ):
                raise _conflict("A submitted line is not bound to the exact admitted event.")
            if line.requested_minor + line.patient_responsibility_minor != line.actual_cost_minor:
                raise _conflict("A submitted line has an incomplete cost allocation.")
            submitted.append(
                {
                    "payer_request_line_id": str(line.id),
                    "care_cost_item_id": str(cost.id),
                    "clinical_service_id": str(service.id),
                    "service_code": service.service_code,
                    "service_date": line.service_date.isoformat(),
                    "currency": line.currency,
                    "actual_cost_minor": line.actual_cost_minor,
                    "requested_minor": line.requested_minor,
                    "patient_responsibility_minor": line.patient_responsibility_minor,
                }
            )
        if sum(int(row["requested_minor"]) for row in submitted) != request.requested_total_minor:
            raise _conflict("The submitted-line total does not match the immutable request.")
    return list(items), delivered, submitted, request


def _result_rows(
    *,
    baseline: ExpectedCarePublishedBaseline,
    items: list[ExpectedCareBaselineItem],
    delivered: list[dict[str, object]],
    submitted: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        matching_delivered = [row for row in delivered if row["service_code"] == item.service_code]
        matching_submitted = [row for row in submitted if row["service_code"] == item.service_code]
        currency_values = {
            str(row["currency"])
            for row in matching_delivered + matching_submitted
            if row.get("currency") is not None
        }
        if any(value != baseline.currency for value in currency_values):
            raise _conflict("Comparison inputs use an incompatible currency.")
        delivered_missing_cost = any(
            row["pricing_state"] == "pending_cost" or row["actual_cost_minor"] is None
            for row in matching_delivered
        )
        delivered_quantity = (
            sum(int(row["quantity"]) for row in matching_delivered if row["quantity"] is not None)
            if matching_delivered
            else None
        )
        delivered_amount = (
            sum(int(row["actual_cost_minor"]) for row in matching_delivered)
            if matching_delivered and not delivered_missing_cost
            else None
        )
        if delivered_missing_cost:
            delivered_label = "missing_cost"
        elif delivered_quantity is None or not (
            item.quantity_low <= delivered_quantity <= item.quantity_high
        ):
            delivered_label = "not_comparable"
        else:
            delivered_label = _label(
                delivered_amount, item.amount_low_minor, item.amount_high_minor
            )
        submitted_amount = (
            sum(int(row["requested_minor"]) for row in matching_submitted)
            if matching_submitted
            else None
        )
        submitted_label = (
            _label(submitted_amount, item.amount_low_minor, item.amount_high_minor)
            if submitted
            else None
        )
        row = {
            "baseline_item_id": str(item.id),
            "item_key": item.item_key,
            "service_code": item.service_code,
            "unit": item.unit,
            "baseline_quantity_low": item.quantity_low,
            "baseline_quantity_high": item.quantity_high,
            "baseline_amount_low_minor": item.amount_low_minor,
            "baseline_amount_high_minor": item.amount_high_minor,
            "delivered_quantity": delivered_quantity,
            "delivered_amount_minor": delivered_amount,
            "delivered_label": delivered_label,
            "submitted_amount_minor": submitted_amount,
            "submitted_label": submitted_label,
            "delivered_source_ids": [
                {
                    "clinical_service_id": value["clinical_service_id"],
                    "care_cost_item_id": value["care_cost_item_id"],
                }
                for value in matching_delivered
            ],
            "submitted_source_ids": [
                {"payer_request_line_id": value["payer_request_line_id"]}
                for value in matching_submitted
            ],
        }
        if delivered_label not in COMPARISON_LABELS or (
            submitted_label is not None and submitted_label not in COMPARISON_LABELS
        ):
            raise RuntimeError("unsupported_comparison_label")
        rows.append(row)
    return rows


def create_comparison(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    baseline: ExpectedCarePublishedBaseline,
    idempotency_key: str,
    include_submitted_facts: bool,
) -> tuple[ExpectedCareComparison, bool]:
    if not _KEY.fullmatch(idempotency_key):
        raise ApiError(422, "validation_failed", "The idempotency key is invalid.")
    request_content = {
        "baseline_id": str(baseline.id),
        "include_submitted_facts": include_submitted_facts,
    }
    request_checksum = _checksum(request_content)
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"expected-care-comparison:{baseline.id}:{idempotency_key}"},
    )
    existing = db.scalar(
        select(ExpectedCareComparison).where(
            ExpectedCareComparison.actor_user_id == actor_user_id,
            ExpectedCareComparison.clinical_event_id == baseline.clinical_event_id,
            ExpectedCareComparison.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_checksum_sha256 != request_checksum:
            raise _conflict("The idempotency key was already used with different content.")
        return existing, True

    reference_checksums = _verify_reference_lineage(db, baseline)
    items, delivered, submitted, payer_request = _scope_snapshots(
        db,
        baseline=baseline,
        include_submitted_facts=include_submitted_facts,
    )
    baseline_snapshot = {
        "baseline_id": str(baseline.id),
        "candidate_output_checksum_sha256": baseline.candidate_output_checksum_sha256,
        "version": baseline.version,
        "currency": baseline.currency,
        "total_low_minor": baseline.total_low_minor,
        "total_high_minor": baseline.total_high_minor,
        "items": [
            {
                "id": str(item.id),
                "item_key": item.item_key,
                "service_code": item.service_code,
                "unit": item.unit,
                "quantity_low": item.quantity_low,
                "quantity_high": item.quantity_high,
                "amount_low_minor": item.amount_low_minor,
                "amount_high_minor": item.amount_high_minor,
            }
            for item in items
        ],
    }
    input_snapshot = {
        "patient_id": str(baseline.patient_id),
        "clinical_event_id": str(baseline.clinical_event_id),
        "payer_request_id": str(payer_request.id) if payer_request else None,
        "baseline": baseline_snapshot,
        "delivered": delivered,
        "submitted": submitted,
        "reference_releases": reference_checksums,
    }
    rows = _result_rows(baseline=baseline, items=items, delivered=delivered, submitted=submitted)
    comparable_delivered = [
        row for row in rows if row["delivered_label"] not in {"not_comparable", "missing_cost"}
    ]
    delivered_total = (
        sum(int(row["delivered_amount_minor"]) for row in comparable_delivered)
        if len(comparable_delivered) == len(rows)
        else None
    )
    submitted_total = (
        sum(int(row["submitted_amount_minor"]) for row in rows)
        if submitted and all(row["submitted_amount_minor"] is not None for row in rows)
        else None
    )
    result = {
        "currency": baseline.currency,
        "baseline_total_low_minor": baseline.total_low_minor,
        "baseline_total_high_minor": baseline.total_high_minor,
        "delivered_total_minor": delivered_total,
        "submitted_total_minor": submitted_total,
        "delivered_total_label": _label(
            delivered_total, baseline.total_low_minor, baseline.total_high_minor
        ),
        "submitted_total_label": (
            _label(submitted_total, baseline.total_low_minor, baseline.total_high_minor)
            if submitted
            else None
        ),
        "items": rows,
        "interpretation_boundary": (
            "Numeric range labels do not determine clinical appropriateness, necessity, "
            "misconduct, fraud, coverage, reimbursement, payment, or patient liability."
        ),
    }
    input_checksum = _checksum(input_snapshot)
    predecessor = db.scalar(
        select(ExpectedCareComparison)
        .where(
            ExpectedCareComparison.baseline_id == baseline.id,
            ExpectedCareComparison.payer_request_id
            == (payer_request.id if payer_request else None),
        )
        .order_by(ExpectedCareComparison.version.desc())
    )
    if predecessor is not None and predecessor.input_snapshot_checksum_sha256 == input_checksum:
        return predecessor, True
    version = (predecessor.version if predecessor else 0) + 1
    difference = {
        "predecessor_comparison_id": str(predecessor.id) if predecessor else None,
        "changed_input_sections": (
            []
            if predecessor is None
            else [
                key
                for key in ("baseline", "delivered", "submitted", "reference_releases")
                if predecessor.input_snapshot_json.get(key) != input_snapshot.get(key)
            ]
        ),
    }
    comparison = ExpectedCareComparison(
        predecessor_comparison_id=predecessor.id if predecessor else None,
        baseline_id=baseline.id,
        actor_user_id=actor_user_id,
        patient_id=baseline.patient_id,
        clinical_event_id=baseline.clinical_event_id,
        payer_request_id=payer_request.id if payer_request else None,
        version=version,
        idempotency_key=idempotency_key,
        request_checksum_sha256=request_checksum,
        input_snapshot_checksum_sha256=input_checksum,
        result_checksum_sha256=_checksum(result),
        baseline_checksum_sha256=_checksum(baseline_snapshot),
        delivered_snapshot_checksum_sha256=_checksum(delivered),
        submitted_snapshot_checksum_sha256=_checksum(submitted) if submitted else None,
        reference_release_checksums_json=reference_checksums,
        comparison_contract_version=COMPARISON_CONTRACT_VERSION,
        lifecycle_state="comparison_published",
        currency=baseline.currency,
        baseline_total_low_minor=baseline.total_low_minor,
        baseline_total_high_minor=baseline.total_high_minor,
        delivered_total_minor=delivered_total,
        submitted_total_minor=submitted_total,
        delivered_total_label=str(result["delivered_total_label"]),
        submitted_total_label=(
            str(result["submitted_total_label"])
            if result["submitted_total_label"] is not None
            else None
        ),
        input_snapshot_json=input_snapshot,
        result_json=result,
        structured_difference_json=difference,
    )
    db.add(comparison)
    db.flush()
    for item, row in zip(items, rows, strict=True):
        delivered_ids = row["delivered_source_ids"]
        submitted_ids = row["submitted_source_ids"]
        db.add(
            ExpectedCareComparisonItem(
                comparison_id=comparison.id,
                baseline_item_id=item.id,
                clinical_service_id=(
                    uuid.UUID(str(delivered_ids[0]["clinical_service_id"]))
                    if len(delivered_ids) == 1
                    else None
                ),
                care_cost_item_id=(
                    uuid.UUID(str(delivered_ids[0]["care_cost_item_id"]))
                    if len(delivered_ids) == 1 and delivered_ids[0]["care_cost_item_id"] is not None
                    else None
                ),
                payer_request_line_id=(
                    uuid.UUID(str(submitted_ids[0]["payer_request_line_id"]))
                    if len(submitted_ids) == 1
                    else None
                ),
                item_key=item.item_key,
                service_code=item.service_code,
                unit=item.unit,
                baseline_quantity_low=item.quantity_low,
                baseline_quantity_high=item.quantity_high,
                delivered_quantity=row["delivered_quantity"],
                baseline_amount_low_minor=item.amount_low_minor,
                baseline_amount_high_minor=item.amount_high_minor,
                delivered_amount_minor=row["delivered_amount_minor"],
                submitted_amount_minor=row["submitted_amount_minor"],
                delivered_label=str(row["delivered_label"]),
                submitted_label=(
                    str(row["submitted_label"]) if row["submitted_label"] is not None else None
                ),
                fact_snapshot_json=row,
            )
        )
    db.add(
        ExpectedCareComparisonEvent(
            comparison_id=comparison.id,
            actor_user_id=actor_user_id,
            event_type="comparison_published",
            metadata_json={
                "version": version,
                "predecessor_comparison_id": (str(predecessor.id) if predecessor else None),
                "content_free": True,
            },
        )
    )
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            patient_id=baseline.patient_id,
            event_type="expected_care_comparison_published",
            resource_type="expected_care_comparison",
            resource_id=comparison.id,
            metadata_json={
                "version": version,
                "payer_request_scoped": payer_request is not None,
                "content_free": True,
            },
        )
    )
    db.commit()
    db.refresh(comparison)
    return comparison, False


def comparison_payload(
    comparison: ExpectedCareComparison, *, role: Literal["doctor", "patient", "payer"]
) -> dict[str, object]:
    result = dict(comparison.result_json)
    if role == "patient":
        for item in result.get("items", []):
            if isinstance(item, dict):
                item.pop("service_code", None)
                item.pop("baseline_item_id", None)
                item.pop("delivered_source_ids", None)
                item.pop("submitted_source_ids", None)
    return {
        "comparison_id": comparison.id,
        "baseline_id": comparison.baseline_id,
        "clinical_event_id": comparison.clinical_event_id,
        "payer_request_id": comparison.payer_request_id,
        "version": comparison.version,
        "state": comparison.lifecycle_state,
        "comparison_contract_version": comparison.comparison_contract_version,
        "result": result,
        "structured_difference": comparison.structured_difference_json,
        "created_at": comparison.created_at,
        "disclaimer": (
            "This deterministic numeric comparison is not a clinical-necessity, "
            "coverage, reimbursement, payment, misconduct, fraud, or patient-liability decision."
        ),
    }


def latest_comparison(
    db: Session,
    *,
    baseline: ExpectedCarePublishedBaseline,
) -> ExpectedCareComparison:
    comparison = db.scalar(
        select(ExpectedCareComparison)
        .where(
            ExpectedCareComparison.baseline_id == baseline.id,
            ExpectedCareComparison.payer_request_id == baseline.payer_request_id,
        )
        .order_by(ExpectedCareComparison.version.desc())
    )
    if comparison is None:
        raise _not_found()
    return comparison


@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/baselines/"
    "{baseline_id}/comparisons"
)
def create_doctor_comparison(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    baseline_id: uuid.UUID,
    payload: ComparisonInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    baseline = _baseline(db, baseline_id=baseline_id, patient_id=patient_id, event_id=event_id)
    comparison, replay = create_comparison(
        db,
        actor_user_id=user.id,
        baseline=baseline,
        idempotency_key=idempotency_key,
        include_submitted_facts=payload.include_submitted_facts,
    )
    return {**comparison_payload(comparison, role="doctor"), "idempotent_replay": replay}


@router.post("/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons")
def create_doctor_comparison_from_latest_baseline(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    payload: ComparisonInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline)
        .where(
            ExpectedCarePublishedBaseline.patient_id == patient_id,
            ExpectedCarePublishedBaseline.clinical_event_id == event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
        .order_by(ExpectedCarePublishedBaseline.version.desc())
    )
    if baseline is None:
        raise _not_found()
    comparison, replay = create_comparison(
        db,
        actor_user_id=user.id,
        baseline=baseline,
        idempotency_key=idempotency_key,
        include_submitted_facts=payload.include_submitted_facts,
    )
    return {**comparison_payload(comparison, role="doctor"), "idempotent_replay": replay}


@router.get("/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/latest")
def doctor_latest_comparison(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline)
        .where(
            ExpectedCarePublishedBaseline.patient_id == patient_id,
            ExpectedCarePublishedBaseline.clinical_event_id == event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
        .order_by(ExpectedCarePublishedBaseline.created_at.desc())
    )
    if baseline is None:
        raise _not_found()
    return comparison_payload(latest_comparison(db, baseline=baseline), role="doctor")


@router.get("/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/history")
def doctor_comparison_history(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    rows = db.scalars(
        select(ExpectedCareComparison)
        .where(
            ExpectedCareComparison.patient_id == patient_id,
            ExpectedCareComparison.clinical_event_id == event_id,
        )
        .order_by(ExpectedCareComparison.created_at.desc())
    ).all()
    return {"items": [comparison_payload(row, role="doctor") for row in rows]}


@router.get("/patient/clinical-events/{event_id}/expected-care-comparison")
def patient_comparison(event_id: uuid.UUID, db: DbSession, user: CurrentUser) -> dict[str, object]:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    event = (
        db.scalar(
            select(ClinicalEvent).where(
                ClinicalEvent.id == event_id,
                ClinicalEvent.patient_id == patient.id,
            )
        )
        if patient
        else None
    )
    if patient is None or event is None:
        raise _not_found()
    baseline = db.scalar(
        select(ExpectedCarePublishedBaseline)
        .where(
            ExpectedCarePublishedBaseline.patient_id == patient.id,
            ExpectedCarePublishedBaseline.clinical_event_id == event_id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
        .order_by(ExpectedCarePublishedBaseline.created_at.desc())
    )
    if baseline is None:
        raise _not_found()
    return comparison_payload(latest_comparison(db, baseline=baseline), role="patient")


def payer_scope(
    db: Session, *, user: User, payer_request_id: uuid.UUID
) -> tuple[PayerMembership, PayerRequest, ExpectedCarePublishedBaseline]:
    membership = require_active_payer_membership(db, user)
    request = db.get(PayerRequest, payer_request_id)
    baseline = (
        db.scalar(
            select(ExpectedCarePublishedBaseline).where(
                ExpectedCarePublishedBaseline.payer_request_id == payer_request_id,
                ExpectedCarePublishedBaseline.patient_id == request.patient_id,
                ExpectedCarePublishedBaseline.clinical_event_id == request.clinical_event_id,
                ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
            )
        )
        if request is not None
        else None
    )
    if (
        request is None
        or baseline is None
        or request.payer_organization_id != membership.payer_organization_id
    ):
        raise _not_found()
    return membership, request, baseline


@router.get("/payer/requests/{payer_request_id}/expected-care-comparison")
def payer_comparison(
    payer_request_id: uuid.UUID, db: DbSession, user: CurrentUser
) -> dict[str, object]:
    if user.role != UserRole.payer:
        raise _not_found()
    _, _, baseline = payer_scope(db, user=user, payer_request_id=payer_request_id)
    return comparison_payload(latest_comparison(db, baseline=baseline), role="payer")
