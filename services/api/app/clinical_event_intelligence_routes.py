"""Request-keyed, role-authorized Clinical Event Intelligence routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Header
from pydantic import Field
from sqlalchemy import func, select, text

from app.clinical_event_intelligence_contracts import StrictModel, canonical_checksum
from app.clinical_event_intelligence_explanations import generate_role_explanation
from app.clinical_event_intelligence_governance import (
    EXPLANATION_RELEASE_KEY,
    IntelligenceReleaseError,
    active_intelligence_release,
)
from app.clinical_event_intelligence_models import (
    ClinicalEventIntelligenceArtifact,
    ClinicalEventIntelligenceExplanation,
    ClinicalEventIntelligenceLineageEvent,
)
from app.clinical_event_intelligence_service import (
    IntelligenceGenerationConflict,
    generate_clinical_event_intelligence,
)
from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.models import (
    PatientProfile,
    PayerDoctorResponse,
    PayerRequest,
    UserRole,
)
from app.payer_scope import require_active_payer_membership

router = APIRouter(prefix="/api/v1", tags=["clinical event intelligence"])


class IntelligenceGenerationInput(StrictModel):
    predecessor_artifact_id: uuid.UUID | None = None


class IntelligenceDoctorResponseInput(StrictModel):
    action: Literal["acknowledge", "concur", "disagree", "exception"]
    rationale: str | None = Field(default=None, max_length=4000)


class IntelligenceExplanationInput(StrictModel):
    locale: Literal["en", "zh-Hans"]


class IntelligenceOutcomeInput(StrictModel):
    outcome_type: Literal[
        "clinical_follow_up",
        "service_delivered",
        "patient_reported_outcome",
        "payer_resolution",
    ]
    observed_at: datetime
    summary: str = Field(min_length=3, max_length=2000)
    evaluation_use_permitted: bool = False


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _doctor_request(db: DbSession, user: CurrentUser, request_id: uuid.UUID) -> PayerRequest:
    if user.role != UserRole.doctor or user.doctor_profile is None:
        raise _not_found()
    request = db.scalar(
        select(PayerRequest).where(
            PayerRequest.id == request_id,
            PayerRequest.doctor_id == user.doctor_profile.id,
        )
    )
    if request is None:
        raise _not_found()
    return request


def _patient_request(db: DbSession, user: CurrentUser, request_id: uuid.UUID) -> PayerRequest:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    request = (
        db.scalar(
            select(PayerRequest).where(
                PayerRequest.id == request_id,
                PayerRequest.patient_id == patient.id,
            )
        )
        if patient
        else None
    )
    if request is None:
        raise _not_found()
    return request


def _payer_request(db: DbSession, user: CurrentUser, request_id: uuid.UUID) -> PayerRequest:
    membership = require_active_payer_membership(db, user)
    request = db.scalar(
        select(PayerRequest).where(
            PayerRequest.id == request_id,
            PayerRequest.payer_organization_id == membership.payer_organization_id,
        )
    )
    if request is None:
        raise _not_found()
    return request


def _latest(db: DbSession, request_id: uuid.UUID) -> ClinicalEventIntelligenceArtifact | None:
    return db.scalar(
        select(ClinicalEventIntelligenceArtifact)
        .where(ClinicalEventIntelligenceArtifact.payer_request_id == request_id)
        .order_by(ClinicalEventIntelligenceArtifact.artifact_version.desc())
    )


def _explanation_payload(
    db: DbSession,
    artifact: ClinicalEventIntelligenceArtifact,
    *,
    role: Literal["patient", "doctor", "payer"],
    locale: Literal["en", "zh-Hans"],
) -> dict[str, object]:
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"clinical-event-intelligence-explanation:{artifact.id}:{role}:{locale}"},
    )
    existing = db.scalar(
        select(ClinicalEventIntelligenceExplanation)
        .where(
            ClinicalEventIntelligenceExplanation.artifact_id == artifact.id,
            ClinicalEventIntelligenceExplanation.role == role,
            ClinicalEventIntelligenceExplanation.locale == locale,
        )
        .order_by(ClinicalEventIntelligenceExplanation.version.desc())
    )
    if existing is not None:
        return {
            "explanation_id": existing.id,
            "display_mode": existing.display_mode,
            "fact_object_checksum_sha256": existing.fact_checksum_sha256,
            "display": existing.display_json,
            "validation": existing.validation_json,
            "idempotent_replay": True,
        }
    settings = get_settings()
    release_id = None
    effective_settings = settings
    if (
        settings.clinical_event_intelligence_explanation_enabled
        and not settings.clinical_event_intelligence_explanation_kill_switch
    ):
        try:
            release = active_intelligence_release(
                db, release_key=EXPLANATION_RELEASE_KEY, settings=settings
            )
            release_id = release.release_id
        except IntelligenceReleaseError:
            effective_settings = settings.model_copy(
                update={
                    "clinical_event_intelligence_explanation_enabled": False,
                    "clinical_event_intelligence_explanation_kill_switch": True,
                }
            )
    result = generate_role_explanation(
        artifact,
        role=role,
        locale=locale,
        settings=effective_settings,
    )
    if release_id is not None:
        current = active_intelligence_release(
            db, release_key=EXPLANATION_RELEASE_KEY, settings=settings
        )
        if current.release_id != release_id:
            raise ApiError(503, "ai_purpose_unavailable", "Explanation release changed.")
    version = (
        int(
            db.scalar(
                select(func.max(ClinicalEventIntelligenceExplanation.version)).where(
                    ClinicalEventIntelligenceExplanation.artifact_id == artifact.id,
                    ClinicalEventIntelligenceExplanation.role == role,
                    ClinicalEventIntelligenceExplanation.locale == locale,
                )
            )
            or 0
        )
        + 1
    )
    row = ClinicalEventIntelligenceExplanation(
        artifact_id=artifact.id,
        purpose_release_id=release_id,
        role=role,
        locale=locale,
        version=version,
        display_mode=result.display_mode,
        fact_checksum_sha256=result.fact_object_checksum_sha256,
        display_checksum_sha256=canonical_checksum(result.display),
        validation_json=result.validation,
        display_json=result.display,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "explanation_id": row.id,
        "display_mode": row.display_mode,
        "fact_object_checksum_sha256": row.fact_checksum_sha256,
        "display": row.display_json,
        "validation": row.validation_json,
        "idempotent_replay": False,
    }


def _append_outcome(
    db: DbSession,
    artifact: ClinicalEventIntelligenceArtifact,
    *,
    actor_user_id: uuid.UUID,
    role: Literal["patient", "doctor", "payer"],
    payload: IntelligenceOutcomeInput,
    idempotency_key: str,
) -> dict[str, object]:
    allowed = {
        "patient": {"patient_reported_outcome"},
        "doctor": {"clinical_follow_up", "service_delivered"},
        "payer": {"payer_resolution"},
    }
    if payload.outcome_type not in allowed[role]:
        raise ApiError(422, "validation_failed", "Outcome type is not allowed for this role.")
    source_event_key = f"outcome:{role}:{idempotency_key}"
    checksum = canonical_checksum(
        {
            "artifact_id": str(artifact.id),
            "role": role,
            **payload.model_dump(mode="json"),
        }
    )
    replay = db.scalar(
        select(ClinicalEventIntelligenceLineageEvent).where(
            ClinicalEventIntelligenceLineageEvent.artifact_id == artifact.id,
            ClinicalEventIntelligenceLineageEvent.source_event_key == source_event_key,
        )
    )
    if replay is not None:
        if replay.source_checksum_sha256 != checksum:
            raise ApiError(409, "conflict", "Idempotency content changed.")
        return {"lineage_event_id": replay.id, "idempotent_replay": True}
    row = ClinicalEventIntelligenceLineageEvent(
        artifact_id=artifact.id,
        actor_user_id=actor_user_id,
        doctor_response_id=None,
        payer_review_id=None,
        event_type="permitted_later_outcome",
        source_event_key=source_event_key,
        source_checksum_sha256=checksum,
        occurred_at=payload.observed_at,
        metadata_json={
            "outcome_type": payload.outcome_type,
            "summary": payload.summary,
            "evaluation_use_permitted": payload.evaluation_use_permitted,
            "human_reported": True,
            "ai_ground_truth": False,
        },
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"lineage_event_id": row.id, "idempotent_replay": False}


def _payload(
    db: DbSession,
    artifact: ClinicalEventIntelligenceArtifact,
    *,
    role: Literal["patient", "doctor", "payer"],
    locale: Literal["en", "zh-Hans"] = "en",
) -> dict[str, object]:
    source = artifact.artifact_json
    snapshot = source.get("snapshot")
    requested_lines = {
        str(item.get("requested_line_id")): item
        for item in (snapshot.get("requested_lines", []) if isinstance(snapshot, dict) else [])
        if isinstance(item, dict)
    }
    facts = {
        str(item.get("fact_id")): item
        for item in (snapshot.get("facts_used", []) if isinstance(snapshot, dict) else [])
        if isinstance(item, dict)
    }
    retrieval_sources = {
        str(item.get("source_id")): item
        for item in source.get("retrieval_sources", [])
        if isinstance(item, dict)
    }
    assessments: list[dict[str, object]] = []
    counterfactuals: list[dict[str, str]] = []
    for item in source.get("requested_item_assessments", []):
        if not isinstance(item, dict):
            continue
        proposal = item.get("proposal")
        if not isinstance(proposal, dict):
            requested = requested_lines.get(str(item.get("requested_line_id")), {})
            assessments.append(
                {
                    "requested_line_id": item.get("requested_line_id"),
                    "label": requested.get("label"),
                    "requested_quantity": requested.get("quantity"),
                    "requested_unit": requested.get("unit"),
                    "requested_amount_minor": requested.get("requested_minor"),
                    "actual_cost_minor": requested.get("actual_cost_minor"),
                    "currency": requested.get("currency"),
                    "code_system": requested.get("code_system"),
                    "service_code": requested.get("service_code"),
                    "state": item.get("state"),
                    "human_review_required": True,
                    "no_automatic_action": True,
                }
            )
            continue
        counterfactuals.extend(
            {
                "title": str(proposal.get("brief_comment") or "Plausible alternative"),
                "summary": str(value),
            }
            for value in proposal.get("alternatives", [])
            if isinstance(value, str)
        )
        cost = proposal.get("estimated_cost")
        safe_cost = (
            {key: value for key, value in cost.items() if key != "source_ids"}
            if isinstance(cost, dict)
            else cost
        )
        safe: dict[str, object] = {
            "requested_line_id": proposal.get("requested_line_id"),
            "label": requested_lines.get(str(proposal.get("requested_line_id")), {}).get("label"),
            "requested_quantity": requested_lines.get(
                str(proposal.get("requested_line_id")), {}
            ).get("quantity"),
            "requested_unit": requested_lines.get(str(proposal.get("requested_line_id")), {}).get(
                "unit"
            ),
            "requested_amount_minor": requested_lines.get(
                str(proposal.get("requested_line_id")), {}
            ).get("requested_minor"),
            "actual_cost_minor": requested_lines.get(
                str(proposal.get("requested_line_id")), {}
            ).get("actual_cost_minor"),
            "currency": requested_lines.get(str(proposal.get("requested_line_id")), {}).get(
                "currency"
            ),
            "code_system": requested_lines.get(str(proposal.get("requested_line_id")), {}).get(
                "code_system"
            ),
            "service_code": requested_lines.get(str(proposal.get("requested_line_id")), {}).get(
                "service_code"
            ),
            "usefulness": proposal.get("usefulness"),
            "scores": {
                **(proposal.get("scores") or {}),
                "ai_support_score": item.get("ai_support_score"),
                "band": item.get("score_band"),
                "score_contract_version": item.get("score_contract_version"),
            },
            "cost_alignment_weight_bp": item.get("cost_alignment_weight_bp"),
            "estimated_quantity": proposal.get("estimated_quantity"),
            "estimated_cost": safe_cost,
            "missing_information": proposal.get("missing_information"),
            "confidence": proposal.get("confidence"),
            "validation_results": item.get("validation_results"),
        }
        if role in {"doctor", "payer"}:
            safe["alternatives"] = proposal.get("alternatives")
            safe["brief_comment"] = proposal.get("brief_comment")
            source_ids = cost.get("source_ids", []) if isinstance(cost, dict) else []
            safe["provenance"] = [
                {
                    "source_type": retrieval_sources.get(str(source_id), {}).get("source_type"),
                    "authority": retrieval_sources.get(str(source_id), {}).get("authority"),
                    "version": retrieval_sources.get(str(source_id), {}).get("version"),
                    "effective_from": retrieval_sources.get(str(source_id), {}).get(
                        "effective_from"
                    ),
                    "effective_to": retrieval_sources.get(str(source_id), {}).get("effective_to"),
                    "currency": retrieval_sources.get(str(source_id), {}).get("currency"),
                    "amount_type": "estimated_reference_range",
                }
                for source_id in source_ids
                if str(source_id) in retrieval_sources
            ]
        if role == "doctor":
            safe["mapped_pathway_ids"] = proposal.get("mapped_pathway_ids")
            safe["supporting_facts"] = [
                {
                    key: facts.get(str(fact_id), {}).get(key)
                    for key in ("fact_id", "category", "value", "verification_state")
                }
                for fact_id in proposal.get("supporting_fact_ids", [])
                if str(fact_id) in facts
            ]
            safe["contradicting_facts"] = [
                {
                    key: facts.get(str(fact_id), {}).get(key)
                    for key in ("fact_id", "category", "value", "verification_state")
                }
                for fact_id in proposal.get("contradicting_fact_ids", [])
                if str(fact_id) in facts
            ]
        assessments.append(safe)
    missing_documentation: list[str] = []
    if isinstance(snapshot, dict):
        missing_documentation.extend(snapshot.get("missing_information", []))
    for assessment in assessments:
        values = assessment.get("missing_information")
        if isinstance(values, list):
            missing_documentation.extend(str(value) for value in values)
    lineage_rows = db.scalars(
        select(ClinicalEventIntelligenceLineageEvent)
        .where(ClinicalEventIntelligenceLineageEvent.artifact_id == artifact.id)
        .order_by(ClinicalEventIntelligenceLineageEvent.occurred_at)
    ).all()
    explanation = db.scalar(
        select(ClinicalEventIntelligenceExplanation)
        .where(
            ClinicalEventIntelligenceExplanation.artifact_id == artifact.id,
            ClinicalEventIntelligenceExplanation.role == role,
            ClinicalEventIntelligenceExplanation.locale == locale,
        )
        .order_by(ClinicalEventIntelligenceExplanation.version.desc())
    )
    explanation_payload: dict[str, object] = {
        "display_mode": "structured_fallback",
        "locale": locale,
        "facts_frozen": True,
        "shared_numbers_unchanged": True,
    }
    if explanation is not None:
        explanation_payload.update(
            {
                "explanation_id": explanation.id,
                "display_mode": explanation.display_mode,
                "locale": explanation.locale,
                "fact_object_checksum_sha256": explanation.fact_checksum_sha256,
                "display": explanation.display_json,
                "validation": {
                    "valid": explanation.validation_json.get("valid") is True,
                    "reason_codes": explanation.validation_json.get("reason_codes", []),
                },
            }
        )
    base: dict[str, object] = {
        "artifact_id": artifact.id,
        "artifact_version": artifact.artifact_version,
        "snapshot_version": source.get("snapshot_version"),
        "lifecycle_state": artifact.lifecycle_state,
        "requested_item_set_checksum": artifact.requested_set_checksum_sha256,
        "disagreement_state": artifact.disagreement_state,
        "requested_item_assessments": assessments,
        "missing_documentation": list(dict.fromkeys(missing_documentation)),
        "counterfactuals": counterfactuals,
        "critic": {
            "state": artifact.disagreement_state,
            "summary": "Primary and critic outputs are reconciled by server policy.",
        },
        "lineage": [
            {
                "event_type": row.event_type,
                "label": "Attributable human response or permitted outcome",
                "occurred_at": row.occurred_at,
            }
            for row in lineage_rows
        ],
        "human_review_state": "required",
        "no_automatic_action": True,
        "explanation": explanation_payload,
        "created_at": artifact.created_at,
    }
    if isinstance(snapshot, dict):
        base["missing_information"] = snapshot.get("missing_information", [])
        location = snapshot.get("location")
        if isinstance(location, dict):
            base["location"] = {
                key: location.get(key)
                for key in (
                    "jurisdiction_code",
                    "province_code",
                    "city_code",
                    "facility_level",
                    "department",
                    "source",
                    "complete",
                )
            }
    if role == "doctor":
        base["pathways"] = source.get("pathways", [])
        base["validation"] = artifact.validation_json
    elif role == "payer":
        base["clarification_needs"] = base.get("missing_information", [])
        base["human_resolution_controls_separate"] = True
    else:
        base["purpose"] = "Explain support, ranges, uncertainty, and human review."
    return base


@router.post("/doctor/payer-requests/{request_id}/intelligence")
def generate_doctor_intelligence(
    request_id: uuid.UUID,
    payload: IntelligenceGenerationInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    request = _doctor_request(db, user, request_id)
    if payload.predecessor_artifact_id is not None:
        predecessor = db.scalar(
            select(ClinicalEventIntelligenceArtifact).where(
                ClinicalEventIntelligenceArtifact.id == payload.predecessor_artifact_id,
                ClinicalEventIntelligenceArtifact.payer_request_id == request.id,
            )
        )
        if predecessor is None:
            raise _not_found()
    settings = get_settings()
    if (
        not settings.clinical_event_intelligence_primary_enabled
        or settings.clinical_event_intelligence_primary_kill_switch
    ):
        raise ApiError(
            503,
            "ai_purpose_unavailable",
            "Clinical Event Intelligence generation is unavailable.",
        )
    try:
        result = generate_clinical_event_intelligence(
            db,
            actor_user_id=user.id,
            payer_request=request,
            idempotency_key=idempotency_key,
            settings=settings,
        )
    except IntelligenceGenerationConflict as exc:
        raise ApiError(409, "conflict", str(exc)) from exc
    except IntelligenceReleaseError as exc:
        raise ApiError(
            503,
            "ai_purpose_unavailable",
            "Clinical Event Intelligence release is unavailable.",
        ) from exc
    return {
        "artifact": _payload(db, result.artifact, role="doctor"),
        "idempotent_replay": result.idempotent_replay,
    }


@router.get("/doctor/payer-requests/{request_id}/intelligence")
def doctor_intelligence(
    request_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    locale: Literal["en", "zh-Hans"] = "en",
) -> dict[str, object]:
    _doctor_request(db, user, request_id)
    artifact = _latest(db, request_id)
    return {"artifact": _payload(db, artifact, role="doctor", locale=locale) if artifact else None}


@router.get("/doctor/payer-requests/{request_id}/intelligence/history")
def doctor_intelligence_history(
    request_id: uuid.UUID, db: DbSession, user: CurrentUser
) -> dict[str, object]:
    _doctor_request(db, user, request_id)
    rows = db.scalars(
        select(ClinicalEventIntelligenceArtifact)
        .where(ClinicalEventIntelligenceArtifact.payer_request_id == request_id)
        .order_by(ClinicalEventIntelligenceArtifact.artifact_version.desc())
    ).all()
    return {"items": [_payload(db, row, role="doctor") for row in rows]}


@router.get("/doctor/payer-requests/{request_id}/intelligence/artifacts/{artifact_id}")
def doctor_intelligence_detail(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    _doctor_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return {"artifact": _payload(db, artifact, role="doctor")}


@router.post("/doctor/payer-requests/{request_id}/intelligence/{artifact_id}/responses")
def append_intelligence_response(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceDoctorResponseInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> dict[str, object]:
    request = _doctor_request(db, user, request_id)
    request = db.scalar(select(PayerRequest).where(PayerRequest.id == request.id).with_for_update())
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if request is None or artifact is None:
        raise _not_found()
    checksum = canonical_checksum(payload.model_dump(mode="json"))
    replay = db.scalar(
        select(PayerDoctorResponse).where(
            PayerDoctorResponse.payer_request_id == request.id,
            PayerDoctorResponse.doctor_id == request.doctor_id,
            PayerDoctorResponse.idempotency_key == idempotency_key,
        )
    )
    if replay is not None:
        if replay.request_checksum != checksum:
            raise ApiError(409, "conflict", "Idempotency content changed.")
        return {"response_id": replay.id, "idempotent_replay": True}
    if payload.action in {"disagree", "exception"} and not (
        payload.rationale and payload.rationale.strip()
    ):
        raise ApiError(422, "validation_failed", "A rationale is required for this action.")
    if request.status in {"accepted", "rejected", "closed"}:
        raise ApiError(409, "conflict", "This payer request is in a terminal state.")
    request.version += 1
    response = PayerDoctorResponse(
        payer_request_id=request.id,
        doctor_id=request.doctor_id,
        baseline_id=None,
        comparison_id=None,
        response_type=payload.action,
        summary=(
            payload.rationale.strip()
            if payload.rationale
            else f"Clinician recorded {payload.action} for the immutable intelligence artifact."
        ),
        request_checksum=checksum,
        idempotency_key=idempotency_key,
        version=request.version,
    )
    db.add(response)
    db.flush()
    db.add(
        ClinicalEventIntelligenceLineageEvent(
            artifact_id=artifact.id,
            actor_user_id=user.id,
            doctor_response_id=response.id,
            payer_review_id=None,
            event_type="clinician_response",
            source_event_key=f"doctor-response:{response.id}",
            source_checksum_sha256=checksum,
            occurred_at=datetime.now(UTC),
            metadata_json={"action": payload.action, "human_owned": True},
        )
    )
    db.commit()
    return {"response_id": response.id, "version": response.version, "idempotent_replay": False}


@router.get("/patient/payer-requests/{request_id}/intelligence")
def patient_intelligence(
    request_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    locale: Literal["en", "zh-Hans"] = "en",
) -> dict[str, object]:
    _patient_request(db, user, request_id)
    artifact = _latest(db, request_id)
    return {"artifact": _payload(db, artifact, role="patient", locale=locale) if artifact else None}


@router.post("/patient/payer-requests/{request_id}/intelligence/{artifact_id}/explanations")
def patient_intelligence_explanation(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceExplanationInput,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    _patient_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _explanation_payload(db, artifact, role="patient", locale=payload.locale)


@router.post("/patient/payer-requests/{request_id}/intelligence/{artifact_id}/outcomes")
def patient_intelligence_outcome(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceOutcomeInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> dict[str, object]:
    _patient_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _append_outcome(
        db,
        artifact,
        actor_user_id=user.id,
        role="patient",
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.get("/payer/requests/{request_id}/intelligence")
def payer_intelligence(
    request_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    locale: Literal["en", "zh-Hans"] = "en",
) -> dict[str, object]:
    _payer_request(db, user, request_id)
    artifact = _latest(db, request_id)
    return {"artifact": _payload(db, artifact, role="payer", locale=locale) if artifact else None}


@router.post("/payer/requests/{request_id}/intelligence/{artifact_id}/explanations")
def payer_intelligence_explanation(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceExplanationInput,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    _payer_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _explanation_payload(db, artifact, role="payer", locale=payload.locale)


@router.post("/payer/requests/{request_id}/intelligence/{artifact_id}/outcomes")
def payer_intelligence_outcome(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceOutcomeInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> dict[str, object]:
    _payer_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _append_outcome(
        db,
        artifact,
        actor_user_id=user.id,
        role="payer",
        payload=payload,
        idempotency_key=idempotency_key,
    )


@router.post("/doctor/payer-requests/{request_id}/intelligence/{artifact_id}/explanations")
def doctor_intelligence_explanation(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceExplanationInput,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    _doctor_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _explanation_payload(db, artifact, role="doctor", locale=payload.locale)


@router.post("/doctor/payer-requests/{request_id}/intelligence/{artifact_id}/outcomes")
def doctor_intelligence_outcome(
    request_id: uuid.UUID,
    artifact_id: uuid.UUID,
    payload: IntelligenceOutcomeInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=120),
) -> dict[str, object]:
    _doctor_request(db, user, request_id)
    artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact).where(
            ClinicalEventIntelligenceArtifact.id == artifact_id,
            ClinicalEventIntelligenceArtifact.payer_request_id == request_id,
        )
    )
    if artifact is None:
        raise _not_found()
    return _append_outcome(
        db,
        artifact,
        actor_user_id=user.id,
        role="doctor",
        payload=payload,
        idempotency_key=idempotency_key,
    )
