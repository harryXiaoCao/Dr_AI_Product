"""Schema-constrained, deterministically validated expected-care candidates.

This purpose is intentionally independent from patient chat. The model can only
echo or omit admitted structured candidates and add bounded uncertainty text.
Applicability, identifiers, releases, codes, units, currency, quantities,
amounts, totals, arithmetic, authorization, and lifecycle state remain
server-owned.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.care_reference_engine import (
    ENGINE_CONTRACT_VERSION,
    EvaluationRequest,
    EvaluationResult,
    evaluate_care_reference,
)
from app.care_reference_integration import (
    ActiveReleaseSelection,
    CareReferenceAuthorizationError,
    ResolvedCareReferenceBundle,
    resolve_active_care_reference_bundle,
)
from app.config import Settings
from app.cost_estimation_facts import (
    build_cost_estimation_fact_snapshot,
    serialize_cost_fact_snapshot,
)
from app.models import (
    AuditEvent,
    CareRelationship,
    ClinicalEvent,
    DoctorProfile,
    ExpectedCareCandidateAttempt,
    ExpectedCareCandidateRequest,
    ExpectedCareCandidateResult,
    GovernedCareRelease,
    PayerRequest,
    User,
    UserRole,
)
from app.provider_transport import OpenAICompatibleJsonTransport, ProviderTransportError

PURPOSE_CODE = "expected_care_candidate"
PURPOSE_CONTRACT_VERSION = "expected-care-candidate-purpose.v1"
OUTPUT_SCHEMA_VERSION = "expected-care-candidate-output.v1"
PROMPT_VERSION = "expected-care-candidate-prompt.v1"
MODEL_CONFIGURATION_VERSION = "expected-care-candidate-config.v1"
MAX_TEXT_LENGTH = 240
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,119}$")


def _checksum(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


StrictText = Annotated[str, Field(min_length=1, max_length=MAX_TEXT_LENGTH)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CandidateReleaseLineage(_StrictModel):
    release_type: Literal[
        "scenario_definition",
        "care_plan",
        "pricing_reference",
        "utilization_rule",
    ]
    release_id: uuid.UUID
    release_key: StrictText
    version: StrictText
    payload_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class CandidateItem(_StrictModel):
    item_key: StrictText
    category: StrictText
    code_system: StrictText
    service_code: StrictText
    unit: StrictText
    quantity_low: Annotated[int, Field(ge=1)]
    quantity_high: Annotated[int, Field(ge=1)]
    amount_low_minor: Annotated[int, Field(ge=0)]
    amount_high_minor: Annotated[int, Field(ge=0)]
    pricing_reference_item_id: uuid.UUID
    utilization_rule_id: uuid.UUID


class CandidateException(_StrictModel):
    exception_code: StrictText
    source_utilization_rule_id: uuid.UUID
    limitation: StrictText


class ExpectedCareCandidateOutput(_StrictModel):
    purpose_code: Literal["expected_care_candidate"]
    purpose_contract_version: Literal["expected-care-candidate-purpose.v1"]
    schema_version: Literal["expected-care-candidate-output.v1"]
    minimum_input_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    scenario_release_id: uuid.UUID
    reference_date: str
    jurisdiction: StrictText
    region: StrictText
    facility_ownership: StrictText
    facility_level: StrictText
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    assumptions: Annotated[list[StrictText], Field(max_length=12)]
    missing_information: Annotated[list[StrictText], Field(max_length=12)]
    attributable_exceptions: Annotated[list[CandidateException], Field(max_length=12)]
    confidence_category: Literal["low", "moderate"]
    confidence_limitations: Annotated[list[StrictText], Field(min_length=1, max_length=12)]
    items: Annotated[list[CandidateItem], Field(min_length=1, max_length=40)]
    total_low_minor: Annotated[int, Field(ge=0)]
    total_high_minor: Annotated[int, Field(ge=0)]
    release_lineage: Annotated[list[CandidateReleaseLineage], Field(min_length=4, max_length=4)]


@dataclass(frozen=True)
class ProviderCandidateResponse:
    output: object
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_microunits: int | None


class ExpectedCareProviderError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class ExpectedCareProvider(Protocol):
    def generate(
        self,
        *,
        provider_input: dict[str, object],
        output_schema: dict[str, object],
        settings: Settings,
    ) -> ProviderCandidateResponse: ...


class DeepSeekExpectedCareProvider:
    """DeepSeek adapter for this purpose; prompts and schema are not shared with chat."""

    def __init__(self, transport: OpenAICompatibleJsonTransport | None = None) -> None:
        self.transport = transport or OpenAICompatibleJsonTransport()

    def generate(
        self,
        *,
        provider_input: dict[str, object],
        output_schema: dict[str, object],
        settings: Settings,
    ) -> ProviderCandidateResponse:
        if settings.deepseek_api_key is None:
            raise ExpectedCareProviderError("provider_key_missing", retryable=False)
        body = {
            "model": settings.expected_care_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return exactly one JSON object matching the supplied schema. "
                        "Use only the structured admitted candidates in the request. "
                        "Do not invent or modify identifiers, releases, codes, units, "
                        "currencies, quantities, amounts, dates, facility scope, totals, "
                        "or applicability. Do not make clinical, coverage, reimbursement, "
                        "fraud, authorization, or workflow-state decisions. If uncertainty "
                        "exists, select only exact allowed_confidence_limitations. Do not "
                        "write free-form protected values or conclusions."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "purpose_input": provider_input,
                            "json_schema": output_schema,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
            "max_tokens": settings.expected_care_max_output_tokens,
            "temperature": 0.0,
        }
        try:
            response = self.transport.request(
                endpoint=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key.get_secret_value(),
                request_body=body,
                timeout_seconds=settings.expected_care_timeout_seconds,
            ).payload
        except ProviderTransportError as exc:
            raise ExpectedCareProviderError(
                exc.code,
                retryable=exc.code in {"timeout", "malformed_envelope"},
            ) from exc
        try:
            content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            if not isinstance(content, str):
                raise TypeError
            output = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ExpectedCareProviderError("malformed_output", retryable=True) from exc
        usage = response.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        return ProviderCandidateResponse(
            output=output,
            provider=settings.expected_care_provider,
            model=str(response.get("model") or settings.expected_care_model),
            input_tokens=usage.get("prompt_tokens"),  # type: ignore[arg-type]
            output_tokens=usage.get("completion_tokens"),  # type: ignore[arg-type]
            cost_microunits=(
                round(
                    int(usage.get("prompt_tokens", 0))
                    * settings.deepseek_input_price_per_million_usd
                    + int(usage.get("completion_tokens", 0))
                    * settings.deepseek_output_price_per_million_usd
                )
                if usage
                else None
            ),
        )


@dataclass(frozen=True)
class CandidateGenerationResult:
    request: ExpectedCareCandidateRequest
    result: ExpectedCareCandidateResult
    idempotent_replay: bool


@dataclass(frozen=True)
class _Attempt:
    number: int
    outcome: str
    diagnostic_code: str | None
    latency_ms: int
    response: ProviderCandidateResponse | None
    output_checksum_sha256: str | None


class ExpectedCareCandidateConflict(ValueError):
    pass


def _authorize(
    session: Session,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    payer_request_id: uuid.UUID | None,
) -> None:
    doctor = session.scalar(
        select(DoctorProfile)
        .join(User, User.id == DoctorProfile.user_id)
        .join(CareRelationship, CareRelationship.doctor_id == DoctorProfile.id)
        .where(
            User.id == actor_user_id,
            User.role == UserRole.doctor,
            User.is_active.is_(True),
            CareRelationship.patient_id == patient_id,
            CareRelationship.is_active.is_(True),
        )
    )
    event = session.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.id == clinical_event_id,
            ClinicalEvent.patient_id == patient_id,
        )
    )
    if doctor is None or event is None:
        raise CareReferenceAuthorizationError()
    if payer_request_id is not None:
        payer_request = session.scalar(
            select(PayerRequest).where(
                PayerRequest.id == payer_request_id,
                PayerRequest.patient_id == patient_id,
                PayerRequest.clinical_event_id == clinical_event_id,
                PayerRequest.doctor_id == doctor.id,
            )
        )
        if payer_request is None:
            raise CareReferenceAuthorizationError()


def _release_rows(
    session: Session,
    bundle: ResolvedCareReferenceBundle,
) -> tuple[GovernedCareRelease, ...]:
    ids = (
        bundle.scenario.control.release_id,
        bundle.plan.control.release_id,
        bundle.pricing.control.release_id,
        bundle.utilization.control.release_id,
    )
    rows = tuple(session.get(GovernedCareRelease, release_id) for release_id in ids)
    if any(row is None for row in rows):
        raise ValueError("release_lineage_missing")
    return rows  # type: ignore[return-value]


def _lineage(rows: tuple[GovernedCareRelease, ...]) -> list[dict[str, object]]:
    return [
        {
            "release_type": row.release_type,
            "release_id": str(row.id),
            "release_key": row.release_key,
            "version": row.version,
            "payload_checksum_sha256": row.payload_checksum_sha256,
        }
        for row in rows
    ]


def _minimum_input(
    *,
    bundle: ResolvedCareReferenceBundle,
    deterministic: EvaluationResult,
    release_lineage: list[dict[str, object]],
    ai_purpose_release: dict[str, str] | None,
    request: EvaluationRequest,
    clinical_fact_snapshot: dict[str, object],
) -> tuple[dict[str, object], str]:
    context = request.context
    prices = {
        (item.code_system, item.service_code, item.unit): item for item in bundle.pricing.items
    }
    rules = {(rule.service_code, rule.unit): rule for rule in bundle.utilization.quantity_rules}
    candidates: list[dict[str, object]] = []
    deterministic_lines = {line.item_key: line for line in deterministic.lines}
    for plan_item in bundle.plan.items:
        price = prices[(plan_item.code_system, plan_item.service_code, plan_item.unit)]
        rule = rules[(plan_item.service_code, plan_item.unit)]
        line = deterministic_lines.get(plan_item.item_key)
        if line is None:
            continue
        if price.reference_item_id is None or rule.rule_id is None:
            raise ValueError("source_lineage_missing")
        candidates.append(
            {
                "item_key": plan_item.item_key,
                "category": plan_item.category,
                "code_system": plan_item.code_system,
                "service_code": plan_item.service_code,
                "unit": plan_item.unit,
                "quantity_low": plan_item.quantity_low,
                "quantity_high": plan_item.quantity_high,
                "amount_low_minor": line.amount_low_minor,
                "amount_high_minor": line.amount_high_minor,
                "pricing_reference_item_id": str(price.reference_item_id),
                "utilization_rule_id": str(rule.rule_id),
            }
        )
    payload: dict[str, object] = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "context": {
            "reference_date": str(context.reference_date),
            "jurisdiction": context.jurisdiction,
            "region": context.region,
            "encounter_type": context.encounter_type,
            "facility_ownership": context.facility_ownership,
            "facility_level": context.facility_level,
            "currency": context.currency,
            "patient_age": context.patient_age,
        },
        "scenario_release_id": str(bundle.scenario.control.release_id),
        "release_lineage": release_lineage,
        "ai_purpose_release": ai_purpose_release,
        "admitted_candidates": candidates,
        "server_totals": {
            "currency": deterministic.currency,
            "total_low_minor": deterministic.total_low_minor,
            "total_high_minor": deterministic.total_high_minor,
        },
        "allowed_missing_information": list(deterministic.missing_information),
        "allowed_assumptions": list(bundle.plan.allowed_candidate_assumptions),
        "allowed_confidence_limitations": [
            "Wholly synthetic reference data; clinician responses remain separate."
        ],
        "allowed_attributable_exceptions": [],
        "clinical_event_fact_snapshot": serialize_cost_fact_snapshot(
            clinical_fact_snapshot,
            role="provider",
        ),
        "authority_boundary": {
            "model_may_omit_only": True,
            "server_owns_applicability_codes_units_currency_quantities_amounts_totals": True,
            "immutable_baseline_publication_required": True,
            "doctor_may_modify_or_hide": False,
        },
    }
    checksum = _checksum(payload)
    payload["minimum_input_checksum_sha256"] = checksum
    return payload, checksum


def _preflight(
    bundle: ResolvedCareReferenceBundle,
    request: EvaluationRequest,
) -> EvaluationResult:
    without_observations = EvaluationRequest(context=request.context)
    result = evaluate_care_reference(
        scenario=bundle.scenario,
        plan=bundle.plan,
        pricing=bundle.pricing,
        utilization=bundle.utilization,
        request=without_observations,
    )
    return result


def _validate_candidate(
    *,
    output: object,
    minimum_input: dict[str, object],
    minimum_input_checksum: str,
    deterministic: EvaluationResult,
) -> tuple[ExpectedCareCandidateOutput | None, tuple[str, ...]]:
    try:
        candidate = ExpectedCareCandidateOutput.model_validate_json(
            json.dumps(output),
            strict=True,
        )
    except ValidationError:
        return None, ("malformed_schema",)
    reasons: set[str] = set()
    context = minimum_input["context"]
    server_totals = minimum_input["server_totals"]
    if not isinstance(context, dict) or not isinstance(server_totals, dict):
        raise ValueError("invalid_minimum_input")
    exact_scalar_fields = {
        "minimum_input_checksum_sha256": minimum_input_checksum,
        "scenario_release_id": uuid.UUID(str(minimum_input["scenario_release_id"])),
        "reference_date": context["reference_date"],
        "jurisdiction": context["jurisdiction"],
        "region": context["region"],
        "facility_ownership": context["facility_ownership"],
        "facility_level": context["facility_level"],
        "currency": context["currency"],
        "total_low_minor": server_totals["total_low_minor"],
        "total_high_minor": server_totals["total_high_minor"],
    }
    for field_name, expected in exact_scalar_fields.items():
        if getattr(candidate, field_name) != expected:
            reasons.add(f"candidate_{field_name}_mismatch")
    expected_lineage = minimum_input["release_lineage"]
    if [item.model_dump(mode="json") for item in candidate.release_lineage] != expected_lineage:
        reasons.add("release_or_checksum_drift")
    expected_items = minimum_input["admitted_candidates"]
    if [item.model_dump(mode="json") for item in candidate.items] != expected_items:
        reasons.add("unsupported_candidate_item")
    if candidate.missing_information != minimum_input["allowed_missing_information"]:
        reasons.add("missing_information_mismatch")
    if any(
        assumption not in minimum_input["allowed_assumptions"]
        for assumption in candidate.assumptions
    ):
        reasons.add("assumption_not_admitted")
    if any(
        limitation not in minimum_input["allowed_confidence_limitations"]
        for limitation in candidate.confidence_limitations
    ):
        reasons.add("confidence_limitation_not_admitted")
    if [item.model_dump(mode="json") for item in candidate.attributable_exceptions] != (
        minimum_input["allowed_attributable_exceptions"]
    ):
        reasons.add("unattributable_exception")
    allowed_rule_ids = {
        uuid.UUID(str(item["utilization_rule_id"]))
        for item in expected_items  # type: ignore[union-attr]
    }
    if any(
        exception.source_utilization_rule_id not in allowed_rule_ids
        for exception in candidate.attributable_exceptions
    ):
        reasons.add("unattributable_exception")
    calculated_low = sum(item.amount_low_minor for item in candidate.items)
    calculated_high = sum(item.amount_high_minor for item in candidate.items)
    if (
        calculated_low != candidate.total_low_minor
        or calculated_high != candidate.total_high_minor
        or candidate.total_low_minor != deterministic.total_low_minor
        or candidate.total_high_minor != deterministic.total_high_minor
    ):
        reasons.add("unreconciled_candidate_total")
    return candidate, tuple(sorted(reasons))


def _worst_case_cost(settings: Settings, minimum_input: dict[str, object]) -> int:
    input_tokens = max(1, len(json.dumps(minimum_input, ensure_ascii=False)) // 4)
    usd = (
        input_tokens * settings.deepseek_input_price_per_million_usd
        + settings.expected_care_max_output_tokens * settings.deepseek_output_price_per_million_usd
    ) / 1_000_000
    return max(1, round(usd * 1_000_000)) * settings.expected_care_max_attempts


def _request_fingerprint(
    *,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    payer_request_id: uuid.UUID | None,
    selection: ActiveReleaseSelection,
    request: EvaluationRequest,
    predecessor_request_id: uuid.UUID | None,
    clinical_fact_snapshot_checksum: str,
    ai_purpose_release_id: uuid.UUID | None,
    ai_purpose_release_checksum_sha256: str | None,
) -> str:
    return _checksum(
        {
            "patient_id": str(patient_id),
            "clinical_event_id": str(clinical_event_id),
            "payer_request_id": str(payer_request_id) if payer_request_id else None,
            "selection": asdict(selection),
            "context": asdict(request.context),
            "predecessor_request_id": (
                str(predecessor_request_id) if predecessor_request_id else None
            ),
            "clinical_fact_snapshot_checksum": clinical_fact_snapshot_checksum,
            "ai_purpose_release_id": (
                str(ai_purpose_release_id) if ai_purpose_release_id is not None else None
            ),
            "ai_purpose_release_checksum_sha256": ai_purpose_release_checksum_sha256,
        }
    )


def _persist(
    session: Session,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    payer_request_id: uuid.UUID | None,
    predecessor_request_id: uuid.UUID | None,
    idempotency_key: str,
    request_checksum: str,
    bundle: ResolvedCareReferenceBundle,
    release_lineage: list[dict[str, object]],
    minimum_input: dict[str, object],
    minimum_input_checksum: str,
    state: str,
    validation_outcome: str,
    reason_codes: tuple[str, ...],
    provider: str,
    model: str,
    attempts: list[_Attempt],
    candidate_payload: dict[str, object],
    deterministic: EvaluationResult,
    ai_purpose_release_id: uuid.UUID | None,
    ai_purpose_release_checksum_sha256: str | None,
) -> CandidateGenerationResult:
    output_checksum = _checksum(candidate_payload)
    successful = [attempt.response for attempt in attempts if attempt.response is not None]
    input_tokens = sum(response.input_tokens or 0 for response in successful)
    output_tokens = sum(response.output_tokens or 0 for response in successful)
    costs = [response.cost_microunits for response in successful]
    row = ExpectedCareCandidateRequest(
        actor_user_id=actor_user_id,
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
        predecessor_request_id=predecessor_request_id,
        idempotency_key=idempotency_key,
        request_checksum_sha256=request_checksum,
        lifecycle_state=state,
        purpose_code=PURPOSE_CODE,
        purpose_contract_version=PURPOSE_CONTRACT_VERSION,
        schema_version=OUTPUT_SCHEMA_VERSION,
        prompt_version=PROMPT_VERSION,
        model_configuration_version=MODEL_CONFIGURATION_VERSION,
        provider=provider,
        model=model,
        ai_purpose_release_id=ai_purpose_release_id,
        ai_purpose_release_checksum_sha256=ai_purpose_release_checksum_sha256,
        scenario_release_id=bundle.scenario.control.release_id,
        care_plan_release_id=bundle.plan.control.release_id,
        pricing_reference_release_id=bundle.pricing.control.release_id,
        utilization_rule_release_id=bundle.utilization.control.release_id,
        release_lineage_json=release_lineage,
        minimum_input_checksum_sha256=minimum_input_checksum,
        minimum_input_json=minimum_input,
        validation_outcome=validation_outcome,
        validation_reason_codes_json=list(reason_codes),
        output_checksum_sha256=output_checksum,
        provider_attempt_count=len(attempts),
        provider_input_tokens=input_tokens if successful else None,
        provider_output_tokens=output_tokens if successful else None,
        provider_cost_microunits=(
            sum(cost for cost in costs if cost is not None)
            if successful and all(cost is not None for cost in costs)
            else None
        ),
    )
    session.add(row)
    session.flush()
    for attempt in attempts:
        response = attempt.response
        session.add(
            ExpectedCareCandidateAttempt(
                candidate_request_id=row.id,
                attempt_number=attempt.number,
                provider=response.provider if response else provider,
                model=response.model if response else model,
                outcome=attempt.outcome,
                diagnostic_code=attempt.diagnostic_code,
                latency_ms=attempt.latency_ms,
                input_tokens=response.input_tokens if response else None,
                output_tokens=response.output_tokens if response else None,
                cost_microunits=response.cost_microunits if response else None,
                output_checksum_sha256=attempt.output_checksum_sha256,
            )
        )
    result = ExpectedCareCandidateResult(
        candidate_request_id=row.id,
        lifecycle_state=state,
        output_checksum_sha256=output_checksum,
        deterministic_result_checksum_sha256=deterministic.result_checksum_sha256,
        deterministic_engine_contract_version=ENGINE_CONTRACT_VERSION,
        currency=deterministic.currency if state == "generated_pending_review" else None,
        total_low_minor=(
            deterministic.total_low_minor if state == "generated_pending_review" else None
        ),
        total_high_minor=(
            deterministic.total_high_minor if state == "generated_pending_review" else None
        ),
        candidate_json=candidate_payload,
        validation_json={
            "outcome": validation_outcome,
            "reason_codes": list(reason_codes),
            "deterministic_wins": True,
            "immutable_baseline_published": True,
            "doctor_may_modify_or_hide": False,
        },
    )
    session.add(result)
    session.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            patient_id=patient_id,
            event_type="expected_care_candidate_created",
            resource_type="expected_care_candidate_request",
            resource_id=row.id,
            metadata_json={
                "purpose_code": PURPOSE_CODE,
                "lifecycle_state": state,
                "validation_outcome": validation_outcome,
                "provider_attempt_count": len(attempts),
                "payer_request_linked": payer_request_id is not None,
                "ai_purpose_release_bound": ai_purpose_release_id is not None,
                "content_free": True,
            },
        )
    )
    session.flush()
    if state == "generated_pending_review" and validation_outcome == "validated":
        from app.expected_care_baseline import ensure_validated_baseline

        ensure_validated_baseline(session, request=row, result=result)
    return CandidateGenerationResult(request=row, result=result, idempotent_replay=False)


def _fallback_payload(state: str, reasons: tuple[str, ...]) -> dict[str, object]:
    return {
        "artifact_type": "fixed_safe_fallback",
        "lifecycle_state": state,
        "reason_codes": list(reasons),
        "manual_workflow_available": True,
        "pending_cost_workflow_available": True,
        "immutable_baseline_published": False,
    }


def generate_expected_care_candidate(
    session: Session,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    selection: ActiveReleaseSelection,
    request: EvaluationRequest,
    idempotency_key: str,
    settings: Settings,
    provider: ExpectedCareProvider | None = None,
    payer_request_id: uuid.UUID | None = None,
    predecessor_request_id: uuid.UUID | None = None,
) -> CandidateGenerationResult:
    """Generate one immutable candidate or fixed safe fallback."""

    if not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        raise ExpectedCareCandidateConflict("invalid_idempotency_key")
    ai_purpose_release = None
    if settings.expected_care_candidate_enabled and not (
        settings.environment == "test"
        and (provider is not None or settings.expected_care_provider != "deepseek")
    ):
        from app.expected_care_candidate_governance import active_candidate_release

        ai_purpose_release = active_candidate_release(session, settings)
    _authorize(
        session,
        actor_user_id=actor_user_id,
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
    )
    clinical_fact_snapshot = build_cost_estimation_fact_snapshot(
        session,
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
    )
    clinical_fact_snapshot_checksum = str(clinical_fact_snapshot["snapshot_checksum_sha256"])
    request_checksum = _request_fingerprint(
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
        selection=selection,
        request=request,
        predecessor_request_id=predecessor_request_id,
        clinical_fact_snapshot_checksum=clinical_fact_snapshot_checksum,
        ai_purpose_release_id=(
            ai_purpose_release.release_id if ai_purpose_release is not None else None
        ),
        ai_purpose_release_checksum_sha256=(
            ai_purpose_release.payload_checksum_sha256 if ai_purpose_release is not None else None
        ),
    )
    lock_key = f"{actor_user_id}:{clinical_event_id}:{idempotency_key}"
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": lock_key},
    )
    existing = session.scalar(
        select(ExpectedCareCandidateRequest).where(
            ExpectedCareCandidateRequest.actor_user_id == actor_user_id,
            ExpectedCareCandidateRequest.clinical_event_id == clinical_event_id,
            ExpectedCareCandidateRequest.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_checksum_sha256 != request_checksum:
            raise ExpectedCareCandidateConflict("idempotency_payload_conflict")
        existing_result = session.scalar(
            select(ExpectedCareCandidateResult).where(
                ExpectedCareCandidateResult.candidate_request_id == existing.id
            )
        )
        if existing_result is None:
            raise ExpectedCareCandidateConflict("idempotency_result_missing")
        from app.expected_care_baseline import ensure_validated_baseline

        ensure_validated_baseline(
            session,
            request=existing,
            result=existing_result,
        )
        return CandidateGenerationResult(
            request=existing,
            result=existing_result,
            idempotent_replay=True,
        )
    if predecessor_request_id is not None:
        predecessor = session.get(ExpectedCareCandidateRequest, predecessor_request_id)
        if (
            predecessor is None
            or predecessor.patient_id != patient_id
            or predecessor.clinical_event_id != clinical_event_id
            or predecessor.payer_request_id != payer_request_id
        ):
            raise CareReferenceAuthorizationError()

    bundle = resolve_active_care_reference_bundle(session, selection=selection)
    releases = _release_rows(session, bundle)
    release_lineage = _lineage(releases)
    deterministic = _preflight(bundle, request)
    minimum_input, minimum_input_checksum = _minimum_input(
        bundle=bundle,
        deterministic=deterministic,
        release_lineage=release_lineage,
        ai_purpose_release=(
            {
                "release_id": str(ai_purpose_release.release_id),
                "version": ai_purpose_release.version,
                "payload_checksum_sha256": ai_purpose_release.payload_checksum_sha256,
            }
            if ai_purpose_release is not None
            else None
        ),
        request=request,
        clinical_fact_snapshot=clinical_fact_snapshot,
    )
    common = {
        "session": session,
        "actor_user_id": actor_user_id,
        "patient_id": patient_id,
        "clinical_event_id": clinical_event_id,
        "payer_request_id": payer_request_id,
        "predecessor_request_id": predecessor_request_id,
        "idempotency_key": idempotency_key,
        "request_checksum": request_checksum,
        "bundle": bundle,
        "release_lineage": release_lineage,
        "minimum_input": minimum_input,
        "minimum_input_checksum": minimum_input_checksum,
        "provider": settings.expected_care_provider,
        "model": settings.expected_care_model,
        "attempts": [],
        "deterministic": deterministic,
        "ai_purpose_release_id": (
            ai_purpose_release.release_id if ai_purpose_release is not None else None
        ),
        "ai_purpose_release_checksum_sha256": (
            ai_purpose_release.payload_checksum_sha256 if ai_purpose_release is not None else None
        ),
    }
    if deterministic.status != "comparison_not_ready" or not deterministic.lines:
        reasons = tuple(
            sorted(set(deterministic.reason_codes) | {"deterministic_preflight_failed"})
        )
        return _persist(
            **common,
            state="suppressed",
            validation_outcome="deterministic_rejected",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("suppressed", reasons),
        )
    if not settings.expected_care_candidate_enabled:
        reasons = ("kill_switch_disabled",)
        return _persist(
            **common,
            state="suppressed",
            validation_outcome="not_called",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("suppressed", reasons),
        )
    if settings.environment not in {"local", "test", "staging"}:
        reasons = ("synthetic_environment_required",)
        return _persist(
            **common,
            state="suppressed",
            validation_outcome="not_called",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("suppressed", reasons),
        )
    if any(not release.provider_transmission_allowed for release in releases) or any(
        item.confidential for item in bundle.pricing.items
    ):
        reasons = ("provider_transmission_denied",)
        return _persist(
            **common,
            state="suppressed",
            validation_outcome="rights_denied",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("suppressed", reasons),
        )
    if _worst_case_cost(settings, minimum_input) > settings.expected_care_max_cost_microunits:
        reasons = ("budget_exhausted",)
        return _persist(
            **common,
            state="provider_unavailable",
            validation_outcome="budget_rejected",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("provider_unavailable", reasons),
        )

    if provider is None and settings.expected_care_provider != "deepseek":
        reasons = ("unsupported_provider_configuration",)
        return _persist(
            **common,
            state="provider_unavailable",
            validation_outcome="provider_configuration_rejected",
            reason_codes=reasons,
            candidate_payload=_fallback_payload("provider_unavailable", reasons),
        )
    adapter = provider or DeepSeekExpectedCareProvider()
    attempts: list[_Attempt] = []
    candidate: ExpectedCareCandidateOutput | None = None
    validation_reasons: tuple[str, ...] = ()
    last_error: str | None = None
    for number in range(1, settings.expected_care_max_attempts + 1):
        started = time.monotonic()
        try:
            response = adapter.generate(
                provider_input=minimum_input,
                output_schema=ExpectedCareCandidateOutput.model_json_schema(),
                settings=settings,
            )
            candidate, validation_reasons = _validate_candidate(
                output=response.output,
                minimum_input=minimum_input,
                minimum_input_checksum=minimum_input_checksum,
                deterministic=deterministic,
            )
            metadata_reasons: set[str] = set(validation_reasons)
            if (
                response.provider != settings.expected_care_provider
                or response.model != settings.expected_care_model
            ):
                metadata_reasons.add("provider_configuration_drift")
            usage_values = (
                response.input_tokens,
                response.output_tokens,
                response.cost_microunits,
            )
            if any(value is not None and value < 0 for value in usage_values):
                metadata_reasons.add("invalid_provider_usage")
            if (
                response.cost_microunits is not None
                and response.cost_microunits > settings.expected_care_max_cost_microunits
            ):
                metadata_reasons.add("provider_budget_exceeded")
            validation_reasons = tuple(sorted(metadata_reasons))
            output_checksum = _checksum(response.output)
            malformed = candidate is None
            attempts.append(
                _Attempt(
                    number=number,
                    outcome="malformed" if malformed else "received",
                    diagnostic_code="malformed_schema" if malformed else None,
                    latency_ms=max(0, round((time.monotonic() - started) * 1000)),
                    response=response,
                    output_checksum_sha256=output_checksum,
                )
            )
            if not malformed:
                break
            last_error = "malformed_schema"
        except ExpectedCareProviderError as exc:
            last_error = exc.code
            attempts.append(
                _Attempt(
                    number=number,
                    outcome="provider_error",
                    diagnostic_code=exc.code,
                    latency_ms=max(0, round((time.monotonic() - started) * 1000)),
                    response=None,
                    output_checksum_sha256=None,
                )
            )
            if not exc.retryable:
                break

    common["attempts"] = attempts
    if candidate is None:
        reasons = (last_error or "provider_unavailable",)
        state = "invalid" if reasons == ("malformed_schema",) else "provider_unavailable"
        return _persist(
            **common,
            state=state,
            validation_outcome="schema_invalid" if state == "invalid" else "provider_failed",
            reason_codes=reasons,
            candidate_payload=_fallback_payload(state, reasons),
        )
    resolved_after_call = resolve_active_care_reference_bundle(session, selection=selection)
    if _lineage(_release_rows(session, resolved_after_call)) != release_lineage:
        validation_reasons = tuple(
            sorted(set(validation_reasons) | {"active_release_changed_during_generation"})
        )
    if ai_purpose_release is not None:
        from app.expected_care_candidate_governance import (
            CandidateReleaseTransitionError,
            active_candidate_release,
        )

        try:
            resolved_purpose = active_candidate_release(session, settings)
        except CandidateReleaseTransitionError:
            resolved_purpose = None
        if resolved_purpose != ai_purpose_release:
            validation_reasons = tuple(
                sorted(set(validation_reasons) | {"ai_purpose_release_changed_during_generation"})
            )
    payload = candidate.model_dump(mode="json")
    if validation_reasons:
        return _persist(
            **common,
            state="invalid",
            validation_outcome="deterministic_rejected",
            reason_codes=validation_reasons,
            candidate_payload=payload,
        )
    return _persist(
        **common,
        state="generated_pending_review",
        validation_outcome="validated",
        reason_codes=(),
        candidate_payload=payload,
    )
