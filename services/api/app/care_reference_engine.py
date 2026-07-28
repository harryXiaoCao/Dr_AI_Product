"""Provider-neutral deterministic care-reference validation and comparison.

This module deliberately has no model/provider dependency. It accepts only
versioned structured facts, performs integer-minor-unit arithmetic, and returns
transparent machine reason codes.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models import CareReferenceEvaluation

ENGINE_CONTRACT_VERSION = "care-reference-deterministic.v1"


def _checksum(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, uuid.UUID)):
        return str(value)
    return value


@dataclass(frozen=True)
class ReleaseControl:
    release_id: uuid.UUID
    release_key: str
    version: str
    payload_checksum_sha256: str
    lifecycle_status: str
    effective_from: date
    effective_to: date | None
    next_review_on: date | None
    rights_status: str
    storage_allowed: bool
    derivation_allowed: bool
    jurisdiction: str
    region: str | None
    currency: str | None


@dataclass(frozen=True)
class ScenarioDefinition:
    control: ReleaseControl
    encounter_types: frozenset[str]
    required_fields: frozenset[str]
    allowed_regions: frozenset[str]
    allowed_facility_ownership: frozenset[str]
    allowed_facility_levels: frozenset[str]
    compatible_care_plan_keys: frozenset[str]
    compatible_pricing_reference_keys: frozenset[str]
    compatible_utilization_rule_keys: frozenset[str]
    minimum_age: int | None = None
    maximum_age: int | None = None


@dataclass(frozen=True)
class PlanItem:
    item_key: str
    category: str
    code_system: str
    service_code: str
    unit: str
    quantity_low: int
    quantity_high: int
    required: bool = True


@dataclass(frozen=True)
class CarePlan:
    control: ReleaseControl
    scenario_release_id: uuid.UUID
    items: tuple[PlanItem, ...]
    allowed_candidate_assumptions: tuple[str, ...] = ()


@dataclass(frozen=True)
class PriceItem:
    code_system: str
    service_code: str
    unit: str
    facility_scope_key: str
    currency: str
    amount_low_minor: int
    amount_high_minor: int
    economic_meaning: str
    reference_item_id: uuid.UUID | None = None
    confidential: bool = False


@dataclass(frozen=True)
class PricingReference:
    control: ReleaseControl
    comparability: str
    items: tuple[PriceItem, ...]


@dataclass(frozen=True)
class QuantityRule:
    service_code: str
    unit: str
    minimum: int
    maximum: int
    rule_id: uuid.UUID | None = None
    rule_code: str | None = None


@dataclass(frozen=True)
class UtilizationRules:
    control: ReleaseControl
    scenario_release_id: uuid.UUID
    quantity_rules: tuple[QuantityRule, ...]


@dataclass(frozen=True)
class EvaluationContext:
    evaluated_on: date
    reference_date: date
    jurisdiction: str | None
    region: str | None
    encounter_type: str | None
    facility_ownership: str | None
    facility_level: str | None
    currency: str | None
    patient_age: int | None


@dataclass(frozen=True)
class ObservedLine:
    line_id: str
    code_system: str | None
    service_code: str | None
    unit: str | None
    quantity: int | None
    currency: str | None
    actual_amount_minor: int | None
    delivered: bool = True


@dataclass(frozen=True)
class JustifiedException:
    exception_code: str
    rationale: str
    authorized_by: str
    applies_to_line_ids: frozenset[str] = field(default_factory=frozenset)

    @property
    def is_usable(self) -> bool:
        return bool(
            self.exception_code.strip() and self.rationale.strip() and self.authorized_by.strip()
        )


def _exception_payload(exception: JustifiedException | None) -> dict[str, object] | None:
    if exception is None:
        return None
    return {
        "exception_code": exception.exception_code,
        "rationale": exception.rationale,
        "authorized_by": exception.authorized_by,
        "applies_to_line_ids": sorted(exception.applies_to_line_ids),
    }


@dataclass(frozen=True)
class EvaluationRequest:
    context: EvaluationContext
    observed_lines: tuple[ObservedLine, ...] = ()
    declared_observed_total_minor: int | None = None
    exception: JustifiedException | None = None


@dataclass(frozen=True)
class EvaluatedLine:
    item_key: str
    service_code: str
    unit: str
    quantity_low: int
    quantity_high: int
    amount_low_minor: int
    amount_high_minor: int
    observed_amount_minor: int | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    currency: str | None
    total_low_minor: int | None
    total_high_minor: int | None
    observed_total_minor: int | None
    reason_codes: tuple[str, ...]
    missing_information: tuple[str, ...]
    suppression_reasons: tuple[str, ...]
    lines: tuple[EvaluatedLine, ...]
    input_checksum_sha256: str
    result_checksum_sha256: str
    input_facts: dict[str, Any] = field(repr=False)
    exception: JustifiedException | None = None

    def input_payload(self) -> dict[str, Any]:
        return self.input_facts

    def persisted_payload(self) -> dict[str, Any]:
        return {
            "engine_contract_version": ENGINE_CONTRACT_VERSION,
            "status": self.status,
            "currency": self.currency,
            "total_low_minor": self.total_low_minor,
            "total_high_minor": self.total_high_minor,
            "observed_total_minor": self.observed_total_minor,
            "reason_codes": list(self.reason_codes),
            "missing_information": list(self.missing_information),
            "suppression_reasons": list(self.suppression_reasons),
            "lines": [asdict(line) for line in self.lines],
            "exception": _exception_payload(self.exception),
        }


def _release_suppression(
    control: ReleaseControl,
    *,
    reference_date: date,
    evaluated_on: date,
) -> str | None:
    if control.lifecycle_status != "active":
        return "reference_release_unavailable"
    if control.rights_status not in {
        "approved",
        "not_required_for_early_synthetic_development",
        "product_owner_waived_for_current_stage",
    } or not (
        control.storage_allowed and control.derivation_allowed
    ):
        return "reference_rights_unavailable"
    if reference_date < control.effective_from or (
        control.effective_to is not None and reference_date > control.effective_to
    ):
        return "no_applicable_reference_version"
    if control.next_review_on is not None and evaluated_on > control.next_review_on:
        return "stale_reference_release"
    return None


def _finalize(
    *,
    request: EvaluationRequest,
    releases: tuple[ReleaseControl, ...],
    status: str,
    currency: str | None,
    total_low_minor: int | None = None,
    total_high_minor: int | None = None,
    observed_total_minor: int | None = None,
    reason_codes: set[str] | None = None,
    missing_information: set[str] | None = None,
    suppression_reasons: set[str] | None = None,
    lines: list[EvaluatedLine] | None = None,
) -> EvaluationResult:
    input_object = {
        "request": _json_safe(asdict(request)),
        "release_ids": [str(control.release_id) for control in releases],
        "release_versions": [control.version for control in releases],
        "release_payload_checksums": [control.payload_checksum_sha256 for control in releases],
    }
    result_object = {
        "status": status,
        "currency": currency,
        "total_low_minor": total_low_minor,
        "total_high_minor": total_high_minor,
        "observed_total_minor": observed_total_minor,
        "reason_codes": sorted(reason_codes or ()),
        "missing_information": sorted(missing_information or ()),
        "suppression_reasons": sorted(suppression_reasons or ()),
        "lines": [asdict(line) for line in (lines or ())],
        "exception": _exception_payload(request.exception),
    }
    return EvaluationResult(
        status=status,
        currency=currency,
        total_low_minor=total_low_minor,
        total_high_minor=total_high_minor,
        observed_total_minor=observed_total_minor,
        reason_codes=tuple(result_object["reason_codes"]),
        missing_information=tuple(result_object["missing_information"]),
        suppression_reasons=tuple(result_object["suppression_reasons"]),
        lines=tuple(lines or ()),
        input_checksum_sha256=_checksum(input_object),
        result_checksum_sha256=_checksum(result_object),
        input_facts=input_object,
        exception=request.exception,
    )


def evaluate_care_reference(
    *,
    scenario: ScenarioDefinition,
    plan: CarePlan,
    pricing: PricingReference,
    utilization: UtilizationRules,
    request: EvaluationRequest,
) -> EvaluationResult:
    """Validate and compare one structured case without any model call."""

    controls = (scenario.control, plan.control, pricing.control, utilization.control)
    suppressions = {
        suppression
        for control in controls
        if (
            suppression := _release_suppression(
                control,
                reference_date=request.context.reference_date,
                evaluated_on=request.context.evaluated_on,
            )
        )
    }
    if suppressions:
        return _finalize(
            request=request,
            releases=controls,
            status="suppressed",
            currency=request.context.currency,
            reason_codes=set(suppressions),
            suppression_reasons=suppressions,
        )

    if plan.scenario_release_id != scenario.control.release_id or (
        utilization.scenario_release_id != scenario.control.release_id
    ):
        return _finalize(
            request=request,
            releases=controls,
            status="suppressed",
            currency=request.context.currency,
            reason_codes={"incompatible_reference_release"},
            suppression_reasons={"incompatible_reference_release"},
        )
    if (
        plan.control.release_key not in scenario.compatible_care_plan_keys
        or pricing.control.release_key not in scenario.compatible_pricing_reference_keys
        or utilization.control.release_key not in scenario.compatible_utilization_rule_keys
    ):
        return _finalize(
            request=request,
            releases=controls,
            status="suppressed",
            currency=request.context.currency,
            reason_codes={"incompatible_reference_release"},
            suppression_reasons={"incompatible_reference_release"},
        )

    context = request.context
    context_values = asdict(context)
    missing = {
        field_name
        for field_name in scenario.required_fields
        if context_values.get(field_name) is None
    }
    if missing:
        return _finalize(
            request=request,
            releases=controls,
            status="missing_information",
            currency=context.currency,
            reason_codes={f"missing_{field_name}" for field_name in missing},
            missing_information=missing,
            suppression_reasons={"insufficient_applicability_information"},
        )

    unsupported: set[str] = set()
    if context.jurisdiction != scenario.control.jurisdiction:
        unsupported.add("unsupported_jurisdiction")
    if scenario.allowed_regions and context.region not in scenario.allowed_regions:
        unsupported.add("unsupported_region")
    if scenario.encounter_types and context.encounter_type not in scenario.encounter_types:
        unsupported.add("unsupported_encounter_type")
    if (
        scenario.allowed_facility_ownership
        and context.facility_ownership not in scenario.allowed_facility_ownership
    ):
        unsupported.add("unsupported_facility_ownership")
    if (
        scenario.allowed_facility_levels
        and context.facility_level not in scenario.allowed_facility_levels
    ):
        unsupported.add("unsupported_facility_level")
    if scenario.minimum_age is not None and (
        context.patient_age is None or context.patient_age < scenario.minimum_age
    ):
        unsupported.add("unsupported_population")
    if scenario.maximum_age is not None and (
        context.patient_age is None or context.patient_age > scenario.maximum_age
    ):
        unsupported.add("unsupported_population")

    expected_currency = scenario.control.currency or pricing.control.currency
    if context.currency != expected_currency:
        unsupported.add("unsupported_currency")
    if unsupported:
        return _finalize(
            request=request,
            releases=controls,
            status="unsupported",
            currency=context.currency,
            reason_codes=unsupported,
            suppression_reasons={"scenario_not_applicable"},
        )

    if pricing.comparability != "range":
        reason = (
            "ceiling_only_not_comparable"
            if pricing.comparability == "ceiling_only"
            else "pricing_reference_not_comparable"
        )
        return _finalize(
            request=request,
            releases=controls,
            status="suppressed",
            currency=context.currency,
            reason_codes={reason},
            suppression_reasons={reason},
        )

    prices = {
        (item.code_system, item.service_code, item.unit, item.facility_scope_key): item
        for item in pricing.items
    }
    quantity_rules = {(rule.service_code, rule.unit): rule for rule in utilization.quantity_rules}
    evaluated: list[EvaluatedLine] = []
    validation_errors: set[str] = set()
    total_low = 0
    total_high = 0

    for item in plan.items:
        if item.quantity_low <= 0 or item.quantity_high < item.quantity_low:
            validation_errors.add("invalid_quantity_range")
            continue
        rule = quantity_rules.get((item.service_code, item.unit))
        if rule is None:
            validation_errors.add("missing_utilization_rule")
            continue
        if (
            item.quantity_low < rule.minimum
            or item.quantity_high > rule.maximum
            or rule.minimum <= 0
            or rule.maximum < rule.minimum
        ):
            validation_errors.add("unsupported_quantity")
            continue
        facility_keys = (
            context.facility_level or "",
            context.facility_ownership or "",
            "*",
        )
        price = next(
            (
                prices[(item.code_system, item.service_code, item.unit, scope)]
                for scope in facility_keys
                if (item.code_system, item.service_code, item.unit, scope) in prices
            ),
            None,
        )
        if price is None:
            validation_errors.add("unsupported_service_code_or_unit")
            continue
        if price.currency != context.currency:
            validation_errors.add("mixed_currency")
            continue
        if price.amount_low_minor < 0 or price.amount_high_minor < price.amount_low_minor:
            validation_errors.add("invalid_price_range")
            continue
        amount_low = item.quantity_low * price.amount_low_minor
        amount_high = item.quantity_high * price.amount_high_minor
        total_low += amount_low
        total_high += amount_high
        evaluated.append(
            EvaluatedLine(
                item_key=item.item_key,
                service_code=item.service_code,
                unit=item.unit,
                quantity_low=item.quantity_low,
                quantity_high=item.quantity_high,
                amount_low_minor=amount_low,
                amount_high_minor=amount_high,
                observed_amount_minor=None,
                reason_codes=(),
            )
        )

    if validation_errors:
        return _finalize(
            request=request,
            releases=controls,
            status="invalid_reference",
            currency=context.currency,
            reason_codes=validation_errors,
            suppression_reasons={"deterministic_validation_failed"},
        )

    delivered = [line for line in request.observed_lines if line.delivered]
    if not delivered:
        return _finalize(
            request=request,
            releases=controls,
            status="comparison_not_ready",
            currency=context.currency,
            total_low_minor=total_low,
            total_high_minor=total_high,
            reason_codes={"not_a_delivered_cost_item"},
            missing_information={"delivered_cost_lines"},
            suppression_reasons={"comparison_not_ready"},
            lines=evaluated,
        )

    observed_validation: set[str] = set()
    observed_by_code: dict[tuple[str, str, str], list[ObservedLine]] = {}
    observed_line_ids: set[str] = set()
    for observed in delivered:
        if observed.line_id in observed_line_ids:
            observed_validation.add("duplicate_observed_line_id")
        observed_line_ids.add(observed.line_id)
        if observed.code_system is None or observed.service_code is None:
            observed_validation.add("missing_service_code")
        if observed.unit is None:
            observed_validation.add("missing_unit")
        if observed.quantity is None:
            observed_validation.add("missing_quantity")
        elif observed.quantity <= 0:
            observed_validation.add("unsupported_quantity")
        if observed.currency is None:
            observed_validation.add("missing_currency")
        elif observed.currency != context.currency:
            observed_validation.add("mixed_currency")
        if observed.actual_amount_minor is None:
            observed_validation.add("missing_actual_amount")
        elif observed.actual_amount_minor < 0:
            observed_validation.add("invalid_actual_amount")
        if (
            observed.code_system is not None
            and observed.service_code is not None
            and observed.unit is not None
        ):
            observed_by_code.setdefault(
                (observed.code_system, observed.service_code, observed.unit), []
            ).append(observed)

    plan_codes = {(item.code_system, item.service_code, item.unit) for item in plan.items}
    if set(observed_by_code) - plan_codes:
        observed_validation.add("unsupported_service_code_or_unit")
    for key, observed_group in observed_by_code.items():
        rule = quantity_rules.get((key[1], key[2]))
        if rule and sum(line.quantity or 0 for line in observed_group) > rule.maximum:
            observed_validation.add("unsupported_quantity")
    calculated_observed_total = sum(line.actual_amount_minor or 0 for line in delivered)
    if (
        request.declared_observed_total_minor is not None
        and request.declared_observed_total_minor != calculated_observed_total
    ):
        observed_validation.add("unreconciled_observed_total")

    if observed_validation:
        missing_codes = {
            code.removeprefix("missing_")
            for code in observed_validation
            if code.startswith("missing_")
        }
        return _finalize(
            request=request,
            releases=controls,
            status="missing_information" if missing_codes else "invalid_observation",
            currency=context.currency,
            total_low_minor=total_low,
            total_high_minor=total_high,
            reason_codes=observed_validation,
            missing_information=missing_codes,
            suppression_reasons={"comparison_not_ready"},
            lines=evaluated,
        )

    comparison_codes: set[str] = set()
    compared_lines: list[EvaluatedLine] = []
    observed_total = calculated_observed_total
    for planned, plan_item in zip(evaluated, plan.items, strict=True):
        matching = observed_by_code.get(
            (plan_item.code_system, plan_item.service_code, plan_item.unit), []
        )
        observed_amount = sum(line.actual_amount_minor or 0 for line in matching)
        if observed_amount < planned.amount_low_minor:
            line_code = "below_expected_range"
        elif observed_amount > planned.amount_high_minor:
            line_code = "above_expected_range"
        else:
            line_code = "within_expected_range"
        comparison_codes.add(line_code)
        compared_lines.append(
            EvaluatedLine(
                **{
                    **asdict(planned),
                    "observed_amount_minor": observed_amount,
                    "reason_codes": (line_code,),
                }
            )
        )

    if observed_total < total_low:
        comparison_codes.add("total_below_expected_range")
    elif observed_total > total_high:
        comparison_codes.add("total_above_expected_range")
    else:
        comparison_codes.add("total_within_expected_range")

    variance = bool({"above_expected_range", "below_expected_range"} & comparison_codes)
    suppression_reasons: set[str] = set()
    status = "review_recommended" if variance else "within_range"
    if request.exception is not None:
        if request.exception.is_usable and variance:
            comparison_codes.add("justified_exception_recorded")
            suppression_reasons.add("justified_exception")
            status = "exception_recorded"
        elif not request.exception.is_usable:
            comparison_codes.add("invalid_exception")
            suppression_reasons.add("exception_requires_authorized_rationale")
            status = "missing_information"

    return _finalize(
        request=request,
        releases=controls,
        status=status,
        currency=context.currency,
        total_low_minor=total_low,
        total_high_minor=total_high,
        observed_total_minor=observed_total,
        reason_codes=comparison_codes,
        suppression_reasons=suppression_reasons,
        lines=compared_lines,
    )


def persist_evaluation(
    session: Session,
    *,
    result: EvaluationResult,
    scenario_release_id: uuid.UUID,
    care_plan_release_id: uuid.UUID,
    pricing_reference_release_id: uuid.UUID,
    utilization_rule_release_id: uuid.UUID,
    prior_evaluation_id: uuid.UUID | None = None,
    clinical_event_id: uuid.UUID | None = None,
    payer_request_id: uuid.UUID | None = None,
) -> CareReferenceEvaluation:
    """Append an immutable result; callers cannot update or reuse an existing row."""

    persisted_release_ids = [
        str(scenario_release_id),
        str(care_plan_release_id),
        str(pricing_reference_release_id),
        str(utilization_rule_release_id),
    ]
    if result.input_payload()["release_ids"] != persisted_release_ids:
        raise ValueError("evaluation_release_binding_mismatch")

    row = CareReferenceEvaluation(
        prior_evaluation_id=prior_evaluation_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
        scenario_release_id=scenario_release_id,
        care_plan_release_id=care_plan_release_id,
        pricing_reference_release_id=pricing_reference_release_id,
        utilization_rule_release_id=utilization_rule_release_id,
        engine_contract_version=ENGINE_CONTRACT_VERSION,
        input_checksum_sha256=result.input_checksum_sha256,
        result_checksum_sha256=result.result_checksum_sha256,
        status=result.status,
        currency=result.currency,
        total_low_minor=result.total_low_minor,
        total_high_minor=result.total_high_minor,
        observed_total_minor=result.observed_total_minor,
        reason_codes_json=list(result.reason_codes),
        missing_information_json=list(result.missing_information),
        exception_json=_exception_payload(result.exception),
        suppression_reasons_json=list(result.suppression_reasons),
        input_facts_json=result.input_payload(),
        result_json=result.persisted_payload(),
    )
    session.add(row)
    session.flush()
    return row
