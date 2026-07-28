"""Publish an immutable expected-care baseline after deterministic validation."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    ExpectedCareBaselineItem,
    ExpectedCareCandidateRequest,
    ExpectedCareCandidateResult,
    ExpectedCareLifecycleEvent,
    ExpectedCarePublishedBaseline,
    ExpectedCareResponseHead,
)

PUBLISHED_BASELINE_STATE = "validated_baseline_published"


def ensure_validated_baseline(
    session: Session,
    *,
    request: ExpectedCareCandidateRequest,
    result: ExpectedCareCandidateResult,
) -> ExpectedCarePublishedBaseline | None:
    """Idempotently publish the exact validated candidate as a separate baseline."""

    existing = session.scalar(
        select(ExpectedCarePublishedBaseline).where(
            ExpectedCarePublishedBaseline.candidate_result_id == result.id,
            ExpectedCarePublishedBaseline.lifecycle_state == PUBLISHED_BASELINE_STATE,
        )
    )
    if existing is not None:
        return existing
    if (
        request.lifecycle_state != "generated_pending_review"
        or result.lifecycle_state != "generated_pending_review"
        or request.validation_outcome != "validated"
        or result.currency is None
        or result.total_low_minor is None
        or result.total_high_minor is None
    ):
        return None
    candidate = result.candidate_json
    items = candidate.get("items")
    if not isinstance(items, list) or not items:
        return None
    if sum(int(item["amount_low_minor"]) for item in items) != result.total_low_minor:
        return None
    if sum(int(item["amount_high_minor"]) for item in items) != result.total_high_minor:
        return None
    next_publication_version = (
        session.scalar(
            select(func.max(ExpectedCarePublishedBaseline.version)).where(
                ExpectedCarePublishedBaseline.candidate_result_id == result.id
            )
        )
        or 0
    ) + 1
    baseline = ExpectedCarePublishedBaseline(
        candidate_result_id=result.id,
        legacy_doctor_review_id=None,
        predecessor_envelope_id=None,
        patient_id=request.patient_id,
        clinical_event_id=request.clinical_event_id,
        payer_request_id=request.payer_request_id,
        version=next_publication_version,
        lifecycle_state=PUBLISHED_BASELINE_STATE,
        candidate_output_checksum_sha256=result.output_checksum_sha256,
        purpose_code=request.purpose_code,
        purpose_contract_version=request.purpose_contract_version,
        schema_version=request.schema_version,
        prompt_version=request.prompt_version,
        model_configuration_version=request.model_configuration_version,
        scenario_release_id=request.scenario_release_id,
        care_plan_release_id=request.care_plan_release_id,
        pricing_reference_release_id=request.pricing_reference_release_id,
        utilization_rule_release_id=request.utilization_rule_release_id,
        release_lineage_json=request.release_lineage_json,
        currency=result.currency,
        amount_type="system_expected_reference_range",
        total_low_minor=result.total_low_minor,
        total_high_minor=result.total_high_minor,
        assumptions_json=list(candidate.get("assumptions", [])),
        missing_information_json=list(candidate.get("missing_information", [])),
        limitations_json=list(candidate.get("confidence_limitations", [])),
        structured_difference_json={
            "base": "immutable_validated_candidate",
            "candidate_modified": False,
            "item_changes": [],
        },
    )
    session.add(baseline)
    session.flush()
    for item in items:
        session.add(
            ExpectedCareBaselineItem(
                baseline_id=baseline.id,
                item_key=str(item["item_key"]),
                category=str(item["category"]),
                code_system=str(item["code_system"]),
                service_code=str(item["service_code"]),
                unit=str(item["unit"]),
                quantity_low=int(item["quantity_low"]),
                quantity_high=int(item["quantity_high"]),
                amount_low_minor=int(item["amount_low_minor"]),
                amount_high_minor=int(item["amount_high_minor"]),
                pricing_reference_item_id=uuid.UUID(
                    str(item["pricing_reference_item_id"])
                ),
                utilization_rule_id=uuid.UUID(str(item["utilization_rule_id"])),
            )
        )
    head = session.get(ExpectedCareResponseHead, result.id)
    if head is None:
        head = ExpectedCareResponseHead(candidate_result_id=result.id)
        session.add(head)
    head.published_baseline_id = baseline.id
    head.lifecycle_state = PUBLISHED_BASELINE_STATE
    session.add(
        ExpectedCareLifecycleEvent(
            candidate_result_id=result.id,
            doctor_review_id=None,
            envelope_id=baseline.id,
            actor_user_id=request.actor_user_id,
            lifecycle_state=PUBLISHED_BASELINE_STATE,
            metadata_json={
                "publication_version": next_publication_version,
                "candidate_modified": False,
                "system_published": True,
            },
        )
    )
    session.add(
        AuditEvent(
            actor_user_id=request.actor_user_id,
            patient_id=request.patient_id,
            event_type="expected_care_baseline_published",
            resource_type="expected_care_published_baseline",
            resource_id=baseline.id,
            metadata_json={
                "candidate_result_id": str(result.id),
                "candidate_modified": False,
                "payer_request_linked": request.payer_request_id is not None,
                "content_free": True,
            },
        )
    )
    session.flush()
    return baseline
