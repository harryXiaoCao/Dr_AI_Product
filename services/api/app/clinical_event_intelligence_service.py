"""Transactional orchestration and immutable persistence for CEI."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import (
    CEI_OUTPUT_SCHEMA_VERSION,
    CEI_PROMPT_VERSION,
    CEI_PURPOSE_CODE,
    CEI_PURPOSE_CONTRACT_VERSION,
    CEI_SCORE_CONTRACT_VERSION,
    CEI_VALIDATOR_VERSION,
    canonical_checksum,
)
from app.clinical_event_intelligence_governance import (
    CRITIC_RELEASE_KEY,
    PRIMARY_RELEASE_KEY,
    IntelligenceReleaseBinding,
    active_intelligence_release,
)
from app.clinical_event_intelligence_models import (
    ClinicalEventIntelligenceArtifact,
    ClinicalEventIntelligenceItemAssessment,
    ClinicalEventIntelligencePathway,
    ClinicalEventIntelligencePathwayItem,
    ClinicalEventIntelligenceProviderAttempt,
    ClinicalEventIntelligenceRetrievalSource,
    ClinicalEventIntelligenceRun,
    ClinicalEventIntelligenceSnapshot,
)
from app.clinical_event_intelligence_provider import (
    CriticIntelligenceProvider,
    DeepSeekCriticIntelligenceProvider,
    DeepSeekPrimaryIntelligenceProvider,
    IntelligenceProviderError,
    IntelligenceProviderResponse,
    PrimaryIntelligenceProvider,
)
from app.clinical_event_intelligence_reconciliation import (
    ReconciliationResult,
    reconcile_critic,
)
from app.clinical_event_intelligence_retrieval import (
    retrieve_authorized_intelligence_sources,
)
from app.clinical_event_intelligence_validation import (
    IntelligenceValidationError,
    normalize_cost_provenance,
    normalize_tier5_uncertainty,
    validate_primary_output,
)
from app.clinical_event_snapshot import build_frozen_clinical_event_snapshot
from app.config import Settings
from app.models import PayerRequest, PayerRequestLine

MODEL_CONFIGURATION_VERSION = "clinical-event-intelligence-deepseek.v1"
SNAPSHOT_CONTRACT_VERSION = "clinical-event-intelligence-snapshot.v1"
_IDEMPOTENCY_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,119}$"


class IntelligenceGenerationConflict(ValueError):
    pass


@dataclass(frozen=True)
class IntelligenceGenerationResult:
    artifact: ClinicalEventIntelligenceArtifact
    idempotent_replay: bool


@dataclass(frozen=True)
class _Attempt:
    number: int
    outcome: str
    diagnostic_code: str | None
    latency_ms: int
    response: IntelligenceProviderResponse | None


def _next_version(db: Session, model: object, column: object, *where: object) -> int:
    return int(db.scalar(select(func.max(column)).select_from(model).where(*where)) or 0) + 1


def _persist_snapshot(
    db: Session,
    *,
    payer_request: PayerRequest,
):
    frozen = build_frozen_clinical_event_snapshot(db, payer_request=payer_request)
    previous = db.scalar(
        select(ClinicalEventIntelligenceSnapshot)
        .where(ClinicalEventIntelligenceSnapshot.payer_request_id == payer_request.id)
        .order_by(ClinicalEventIntelligenceSnapshot.snapshot_version.desc())
    )
    if (
        previous is not None
        and previous.payer_request_version == payer_request.version
        and previous.snapshot_checksum_sha256 == frozen.snapshot_checksum_sha256
    ):
        return previous, frozen
    dates = [line.service_date for line in payer_request.lines]
    row = ClinicalEventIntelligenceSnapshot(
        predecessor_snapshot_id=previous.id if previous else None,
        payer_request_id=payer_request.id,
        snapshot_version=(previous.snapshot_version + 1 if previous else 1),
        payer_request_version=payer_request.version,
        patient_id=payer_request.patient_id,
        clinical_event_id=payer_request.clinical_event_id,
        doctor_id=payer_request.doctor_id,
        payer_organization_id=payer_request.payer_organization_id,
        hospital_id=uuid.UUID(frozen.location.hospital_id) if frozen.location.hospital_id else None,
        clinic_id=uuid.UUID(frozen.location.clinic_id) if frozen.location.clinic_id else None,
        department_code=frozen.location.department,
        jurisdiction_code=frozen.location.jurisdiction_code,
        province=frozen.location.province_code,
        city=frozen.location.city_code,
        facility_level=frozen.location.facility_level,
        encounter_at=payer_request.clinical_event.encounter_at,
        service_date_from=min(dates),
        service_date_to=max(dates),
        snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
        snapshot_checksum_sha256=frozen.snapshot_checksum_sha256,
        snapshot_json=frozen.model_dump(mode="json"),
        source_lineage_json=[
            {
                "source_type": fact.source_type,
                "source_id": fact.source_id,
                "verification_state": fact.verification_state,
            }
            for fact in frozen.facts_used
        ],
        quality_flags_json=[
            {"type": "missing", "message": value} for value in frozen.missing_information
        ]
        + [{"type": "conflicting", "message": value} for value in frozen.conflicting_information],
    )
    db.add(row)
    db.flush()
    return row, frozen


def _persist_attempts(
    db: Session,
    *,
    run_id: uuid.UUID,
    pass_type: str,
    attempts: list[_Attempt],
    provider: str,
    model: str,
) -> None:
    for attempt in attempts:
        response = attempt.response
        db.add(
            ClinicalEventIntelligenceProviderAttempt(
                run_id=run_id,
                pass_type=pass_type,
                attempt_number=attempt.number,
                provider=response.provider if response else provider,
                model=response.model if response else model,
                outcome=attempt.outcome,
                diagnostic_code=attempt.diagnostic_code,
                latency_ms=attempt.latency_ms,
                input_tokens=response.input_tokens if response else None,
                output_tokens=response.output_tokens if response else None,
                cost_microunits=response.cost_microunits if response else None,
                output_checksum_sha256=(response.output_checksum_sha256 if response else None),
            )
        )


def _fallback_artifact(
    db: Session,
    *,
    run: ClinicalEventIntelligenceRun,
    snapshot_version: int,
    frozen: object,
    previous: ClinicalEventIntelligenceArtifact | None,
    reason_code: str,
) -> ClinicalEventIntelligenceArtifact:
    snapshot = frozen
    artifact_payload = {
        "artifact_version": (previous.artifact_version + 1 if previous else 1),
        "snapshot_version": snapshot_version,
        "snapshot": snapshot.model_dump(mode="json"),
        "lifecycle_state": "provider_unavailable",
        "requested_item_set_checksum": snapshot.requested_item_set_checksum_sha256,
        "requested_item_assessments": [
            {
                "requested_line_id": line.requested_line_id,
                "state": "assessment_unavailable",
                "human_review_required": True,
                "no_automatic_action": True,
            }
            for line in snapshot.requested_lines
        ],
        "reason_code": reason_code,
        "clinical_documentation_available": True,
        "pending_cost_available": True,
        "clarification_available": True,
        "human_review_available": True,
    }
    checksum = canonical_checksum(artifact_payload)
    artifact = ClinicalEventIntelligenceArtifact(
        run_id=run.id,
        predecessor_artifact_id=previous.id if previous else None,
        payer_request_id=run.payer_request_id,
        artifact_version=artifact_payload["artifact_version"],
        lifecycle_state="provider_unavailable",
        requested_set_checksum_sha256=snapshot.requested_item_set_checksum_sha256,
        snapshot_checksum_sha256=snapshot.snapshot_checksum_sha256,
        result_checksum_sha256=checksum,
        configuration_checksum_sha256=canonical_checksum(
            {"purpose": CEI_PURPOSE_CODE, "model_configuration": MODEL_CONFIGURATION_VERSION}
        ),
        reconciliation_checksum_sha256=canonical_checksum(
            {"state": "unavailable", "reason": reason_code}
        ),
        disagreement_state="unavailable",
        artifact_json=artifact_payload,
        validation_json={"valid": False, "reason_codes": [reason_code]},
    )
    db.add(artifact)
    db.flush()
    return artifact


def generate_clinical_event_intelligence(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    payer_request: PayerRequest,
    idempotency_key: str,
    settings: Settings,
    primary_provider: PrimaryIntelligenceProvider | None = None,
    critic_provider: CriticIntelligenceProvider | None = None,
    primary_release: IntelligenceReleaseBinding | None = None,
    critic_release: IntelligenceReleaseBinding | None = None,
) -> IntelligenceGenerationResult:
    import re

    if not re.fullmatch(_IDEMPOTENCY_PATTERN, idempotency_key):
        raise IntelligenceGenerationConflict("invalid_idempotency_key")
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"clinical-event-intelligence:{payer_request.id}"},
    )
    snapshot_row, frozen = _persist_snapshot(db, payer_request=payer_request)
    primary_release = primary_release or active_intelligence_release(
        db, release_key=PRIMARY_RELEASE_KEY, settings=settings
    )
    if (
        settings.clinical_event_intelligence_critic_enabled
        and not settings.clinical_event_intelligence_critic_kill_switch
    ):
        critic_release = critic_release or active_intelligence_release(
            db, release_key=CRITIC_RELEASE_KEY, settings=settings
        )
    request_payload = {
        "payer_request_id": str(payer_request.id),
        "snapshot_checksum_sha256": frozen.snapshot_checksum_sha256,
        "primary_release_id": str(primary_release.release_id),
        "critic_release_id": str(critic_release.release_id) if critic_release else None,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
    }
    request_checksum = canonical_checksum(request_payload)
    existing = db.scalar(
        select(ClinicalEventIntelligenceRun).where(
            ClinicalEventIntelligenceRun.actor_user_id == actor_user_id,
            ClinicalEventIntelligenceRun.payer_request_id == payer_request.id,
            ClinicalEventIntelligenceRun.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_checksum_sha256 != request_checksum:
            raise IntelligenceGenerationConflict("idempotency_payload_conflict")
        artifact = db.scalar(
            select(ClinicalEventIntelligenceArtifact).where(
                ClinicalEventIntelligenceArtifact.run_id == existing.id
            )
        )
        if artifact is None:
            raise IntelligenceGenerationConflict("idempotency_result_missing")
        return IntelligenceGenerationResult(artifact=artifact, idempotent_replay=True)
    previous_run = db.scalar(
        select(ClinicalEventIntelligenceRun)
        .where(ClinicalEventIntelligenceRun.payer_request_id == payer_request.id)
        .order_by(ClinicalEventIntelligenceRun.run_version.desc())
    )
    run = ClinicalEventIntelligenceRun(
        snapshot_id=snapshot_row.id,
        predecessor_run_id=previous_run.id if previous_run else None,
        actor_user_id=actor_user_id,
        payer_request_id=payer_request.id,
        run_version=(previous_run.run_version + 1 if previous_run else 1),
        idempotency_key=idempotency_key,
        request_checksum_sha256=request_checksum,
        purpose_code=CEI_PURPOSE_CODE,
        purpose_contract_version=CEI_PURPOSE_CONTRACT_VERSION,
        schema_version=CEI_OUTPUT_SCHEMA_VERSION,
        prompt_version=CEI_PROMPT_VERSION,
        model_configuration_version=MODEL_CONFIGURATION_VERSION,
        validator_version=CEI_VALIDATOR_VERSION,
        score_version=CEI_SCORE_CONTRACT_VERSION,
        primary_release_id=primary_release.release_id,
        critic_release_id=critic_release.release_id if critic_release else None,
        lifecycle_state="immutable_execution_record",
    )
    db.add(run)
    db.flush()
    retrieval = retrieve_authorized_intelligence_sources(
        db,
        snapshot=frozen,
        payer_organization_id=str(payer_request.payer_organization_id),
    )
    adapter = primary_provider or DeepSeekPrimaryIntelligenceProvider()
    attempts: list[_Attempt] = []
    validated = None
    last_reason = "provider_unavailable"
    for number in range(1, settings.clinical_event_intelligence_primary_max_attempts + 1):
        started = time.monotonic()
        try:
            response = adapter.generate(snapshot=frozen, retrieval=retrieval, settings=settings)
            if (
                response.cost_microunits is not None
                and response.cost_microunits
                > settings.clinical_event_intelligence_primary_max_cost_microunits
            ):
                raise IntelligenceProviderError("provider_budget_exceeded", retryable=False)
            try:
                normalized_output, normalizations = normalize_cost_provenance(
                    response.output,
                    snapshot=frozen,
                    retrieval=retrieval,
                )
                normalized_output, tier5_normalizations = normalize_tier5_uncertainty(
                    normalized_output
                )
                normalizations.extend(tier5_normalizations)
                validated = validate_primary_output(
                    normalized_output,
                    snapshot=frozen,
                    retrieval=retrieval,
                    server_normalizations=normalizations,
                )
            except IntelligenceValidationError as exc:
                last_reason = exc.reason_codes[0]
                attempts.append(
                    _Attempt(
                        number,
                        "rejected",
                        last_reason,
                        round((time.monotonic() - started) * 1000),
                        response,
                    )
                )
                continue
            attempts.append(
                _Attempt(
                    number, "validated", None, round((time.monotonic() - started) * 1000), response
                )
            )
            break
        except IntelligenceProviderError as exc:
            last_reason = exc.code
            attempts.append(
                _Attempt(
                    number,
                    "provider_error",
                    exc.code,
                    round((time.monotonic() - started) * 1000),
                    None,
                )
            )
            if not exc.retryable:
                break
    _persist_attempts(
        db,
        run_id=run.id,
        pass_type="primary",
        attempts=attempts,
        provider=settings.clinical_event_intelligence_primary_provider,
        model=settings.clinical_event_intelligence_primary_model,
    )
    previous_artifact = db.scalar(
        select(ClinicalEventIntelligenceArtifact)
        .where(ClinicalEventIntelligenceArtifact.payer_request_id == payer_request.id)
        .order_by(ClinicalEventIntelligenceArtifact.artifact_version.desc())
    )
    if validated is None:
        artifact = _fallback_artifact(
            db,
            run=run,
            snapshot_version=snapshot_row.snapshot_version,
            frozen=frozen,
            previous=previous_artifact,
            reason_code=last_reason,
        )
        db.commit()
        return IntelligenceGenerationResult(artifact=artifact, idempotent_replay=False)
    source_rows: dict[str, ClinicalEventIntelligenceRetrievalSource] = {}
    for ordinal, source in enumerate(retrieval.sources):
        tier = {
            "facility_price": 1,
            "payer_price": 1,
            "regional_reference": 2,
            "comparable_case": 3,
        }.get(source.source_type, 4)
        row = ClinicalEventIntelligenceRetrievalSource(
            run_id=run.id,
            ordinal=ordinal,
            source_type=source.source_type,
            governed_release_id=uuid.UUID(source.release_id) if source.release_id else None,
            pricing_reference_item_id=None,
            provenance_tier=tier,
            scope_checksum_sha256=retrieval.authorization_scope_checksum_sha256,
            lineage_checksum_sha256=source.checksum_sha256,
            source_lineage_json=source.model_dump(mode="json"),
        )
        db.add(row)
        db.flush()
        source_rows[source.source_id] = row
    pathway_rows: dict[str, ClinicalEventIntelligencePathway] = {}
    for pathway in validated.primary.pathways:
        row = ClinicalEventIntelligencePathway(
            run_id=run.id,
            pathway_key=pathway.pathway_id,
            pathway_type=pathway.pathway_type,
            usefulness=pathway.usefulness,
            confidence=pathway.confidence,
            supporting_facts_json=[{"fact_id": value} for value in pathway.trigger_fact_ids],
            contradicting_facts_json=[],
            missing_information_json=[{"text": value} for value in pathway.limitations],
            assumptions_json=[{"text": value} for value in pathway.assumptions],
        )
        db.add(row)
        db.flush()
        pathway_rows[pathway.pathway_id] = row
        for item in pathway.items:
            db.add(
                ClinicalEventIntelligencePathwayItem(
                    pathway_id=row.id,
                    item_key=item.item_key,
                    label=item.label,
                    code_system=None,
                    service_code=item.service_code,
                    unit=item.unit,
                    quantity_low=item.quantity_low,
                    quantity_high=item.quantity_high,
                    currency=item.currency,
                    cost_low_minor=item.cost_low_minor,
                    cost_high_minor=item.cost_high_minor,
                    predicted_only=True,
                )
            )
    critic_attempts: list[_Attempt] = []
    critic_output = None
    if critic_release is not None:
        started = time.monotonic()
        try:
            response = (critic_provider or DeepSeekCriticIntelligenceProvider()).review(
                snapshot=frozen, retrieval=retrieval, primary=validated, settings=settings
            )
            if (
                response.cost_microunits is not None
                and response.cost_microunits
                > settings.clinical_event_intelligence_critic_max_cost_microunits
            ):
                raise IntelligenceProviderError("provider_budget_exceeded", retryable=False)
            critic_output = response.output
            critic_attempts.append(
                _Attempt(1, "received", None, round((time.monotonic() - started) * 1000), response)
            )
        except IntelligenceProviderError as exc:
            critic_attempts.append(
                _Attempt(
                    1, "provider_error", exc.code, round((time.monotonic() - started) * 1000), None
                )
            )
        _persist_attempts(
            db,
            run_id=run.id,
            pass_type="critic",
            attempts=critic_attempts,
            provider=settings.clinical_event_intelligence_critic_provider,
            model=settings.clinical_event_intelligence_critic_model,
        )
    reconciliation: ReconciliationResult = reconcile_critic(
        critic_output, snapshot=frozen, primary=validated
    )
    line_rows = {
        str(line.id): line
        for line in db.scalars(
            select(PayerRequestLine).where(PayerRequestLine.payer_request_id == payer_request.id)
        ).all()
    }
    for assessment in validated.assessments:
        proposal = assessment.proposal
        line = line_rows[proposal.requested_line_id]
        source = (
            source_rows[proposal.estimated_cost.source_ids[0]]
            if proposal.estimated_cost.source_ids
            else None
        )
        confidence = {"low": 33, "moderate": 66, "high": 90}[proposal.confidence]
        db.add(
            ClinicalEventIntelligenceItemAssessment(
                run_id=run.id,
                payer_request_line_id=line.id,
                retrieval_source_id=source.id if source else None,
                requested_label=line.label,
                requested_code=line.service_code,
                requested_quantity=line.quantity,
                requested_unit=line.unit,
                requested_amount_minor=line.requested_minor,
                currency=line.currency,
                estimated_quantity_low=proposal.estimated_quantity.low,
                estimated_quantity_high=proposal.estimated_quantity.high,
                estimated_cost_low_minor=proposal.estimated_cost.low_minor,
                estimated_cost_high_minor=proposal.estimated_cost.high_minor,
                clinical_fit=proposal.scores.clinical_fit,
                evidence_support=proposal.scores.evidence_support,
                timing_sequence=proposal.scores.timing_sequence,
                quantity_intensity=proposal.scores.quantity_intensity,
                documentation_completeness=proposal.scores.documentation_completeness,
                cost_alignment=proposal.scores.cost_alignment,
                cost_alignment_weight_bp=assessment.cost_alignment_weight_bp,
                ai_support_score=assessment.ai_support_score,
                support_band=assessment.score_band,
                score_version=assessment.score_contract_version,
                provenance_tier=proposal.estimated_cost.provenance_tier,
                exploratory=proposal.estimated_cost.is_model_only_exploratory,
                wide_uncertainty=proposal.estimated_cost.provenance_tier == 5,
                confidence=confidence,
                usefulness=proposal.usefulness,
                mapped_pathways_json=[
                    {"pathway_id": pathway_rows[value].id.hex}
                    for value in proposal.mapped_pathway_ids
                ],
                supporting_facts_json=[
                    {"fact_id": value} for value in proposal.supporting_fact_ids
                ],
                contradicting_facts_json=[
                    {"fact_id": value} for value in proposal.contradicting_fact_ids
                ],
                missing_information_json=[
                    {"text": value} for value in proposal.missing_information
                ],
                alternatives_json=[{"text": value} for value in proposal.alternatives],
                source_lineage_json=[
                    {"source_id": value} for value in proposal.estimated_cost.source_ids
                ],
                brief_comments_json=[{"text": proposal.brief_comment}],
                validation_results_json={"results": assessment.validation_results},
                disagreement_state=reconciliation.state,
            )
        )
    # The artifact close trigger verifies normalized line coverage. Flush the
    # complete assessment set before inserting the closing artifact because
    # there is intentionally no mutable ORM relationship between these
    # append-only records that would otherwise establish insert ordering.
    db.flush()
    artifact_payload = {
        "artifact_version": previous_artifact.artifact_version + 1 if previous_artifact else 1,
        "snapshot_version": snapshot_row.snapshot_version,
        "snapshot": frozen.model_dump(mode="json"),
        "retrieval_sources": [
            {
                "source_id": source.source_id,
                "source_type": source.source_type,
                "authority": source.authority,
                "version": source.release_version,
                "effective_from": source.payload.get("effective_from"),
                "effective_to": source.payload.get("effective_to"),
                "currency": source.payload.get("currency"),
            }
            for source in retrieval.sources
        ],
        "pathways": [item.model_dump(mode="json") for item in validated.primary.pathways],
        "requested_item_assessments": [
            item.model_dump(mode="json") for item in validated.assessments
        ],
        "critic": reconciliation.__dict__,
        "server_normalizations": [
            value for value in validated.validation_results if value.startswith("server_")
        ],
        "lifecycle_state": "validated",
        "no_automatic_action": True,
    }
    artifact = ClinicalEventIntelligenceArtifact(
        run_id=run.id,
        predecessor_artifact_id=previous_artifact.id if previous_artifact else None,
        payer_request_id=payer_request.id,
        artifact_version=artifact_payload["artifact_version"],
        lifecycle_state="validated",
        requested_set_checksum_sha256=frozen.requested_item_set_checksum_sha256,
        snapshot_checksum_sha256=frozen.snapshot_checksum_sha256,
        result_checksum_sha256=canonical_checksum(artifact_payload),
        configuration_checksum_sha256=canonical_checksum(request_payload),
        reconciliation_checksum_sha256=canonical_checksum(reconciliation.__dict__),
        disagreement_state=reconciliation.state,
        artifact_json=artifact_payload,
        validation_json={"valid": True, "results": validated.validation_results},
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return IntelligenceGenerationResult(artifact=artifact, idempotent_replay=False)
