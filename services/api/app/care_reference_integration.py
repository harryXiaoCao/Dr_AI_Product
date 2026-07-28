"""Database-backed resolution and authorized deterministic care evaluation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.care_reference_engine import (
    CarePlan,
    EvaluationRequest,
    EvaluationResult,
    PlanItem,
    PriceItem,
    PricingReference,
    QuantityRule,
    ReleaseControl,
    ScenarioDefinition,
    UtilizationRules,
    evaluate_care_reference,
    persist_evaluation,
)
from app.models import (
    AuditEvent,
    CarePlanItem,
    CareReferenceEvaluation,
    CareRelationship,
    CareScenarioDefinition,
    ClinicalEvent,
    DoctorProfile,
    GovernedActiveCareRelease,
    GovernedCareRelease,
    PayerRequest,
    PayerRequestLine,
    PricingReferenceItem,
    PricingReferenceSet,
    User,
    UserRole,
    UtilizationRule,
    UtilizationRuleSet,
)
from app.models import (
    CarePlan as CarePlanRow,
)


class CareReferenceResolutionError(ValueError):
    pass


class CareReferenceAuthorizationError(ValueError):
    """Intentionally neutral authorization failure for internal callers."""

    def __init__(self) -> None:
        super().__init__("not_found")


@dataclass(frozen=True)
class ActiveReleaseSelection:
    scenario_key: str
    care_plan_key: str
    pricing_reference_key: str
    utilization_rule_key: str
    scope_key: str


@dataclass(frozen=True)
class ResolvedCareReferenceBundle:
    scenario: ScenarioDefinition
    plan: CarePlan
    pricing: PricingReference
    utilization: UtilizationRules


@dataclass(frozen=True)
class PersistedCareEvaluation:
    result: EvaluationResult
    row: CareReferenceEvaluation


def build_care_reference_scope_key(
    *,
    jurisdiction: str,
    region: str,
    facility_ownership: str,
    facility_level: str,
    currency: str,
) -> str:
    values = (
        jurisdiction.strip(),
        region.strip(),
        facility_ownership.strip(),
        facility_level.strip(),
        currency.strip().upper(),
    )
    if any(not value for value in values):
        raise CareReferenceResolutionError("invalid_release_scope")
    return "|".join(values)


def _active_release(
    session: Session,
    *,
    release_type: str,
    release_key: str,
    scope_key: str,
) -> GovernedCareRelease:
    release = session.scalar(
        select(GovernedCareRelease)
        .join(
            GovernedActiveCareRelease,
            GovernedActiveCareRelease.release_id == GovernedCareRelease.id,
        )
        .where(
            GovernedActiveCareRelease.release_type == release_type,
            GovernedActiveCareRelease.release_key == release_key,
            GovernedActiveCareRelease.scope_key == scope_key,
            GovernedCareRelease.release_type == release_type,
            GovernedCareRelease.release_key == release_key,
        )
    )
    if release is None:
        raise CareReferenceResolutionError("active_release_not_found")
    return release


def _control(release: GovernedCareRelease) -> ReleaseControl:
    return ReleaseControl(
        release_id=release.id,
        release_key=release.release_key,
        version=release.version,
        payload_checksum_sha256=release.payload_checksum_sha256,
        # Resolution through the unique active pointer is the operational state.
        # Release rows remain immutable historical content.
        lifecycle_status="active",
        effective_from=release.effective_from,
        effective_to=release.effective_to,
        next_review_on=release.next_review_on,
        rights_status=release.rights_status,
        storage_allowed=release.storage_allowed,
        derivation_allowed=release.derivation_allowed,
        jurisdiction=release.jurisdiction,
        region=release.region,
        currency=release.currency,
    )


def _string_set(payload: dict[str, object], key: str) -> frozenset[str]:
    value = payload.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CareReferenceResolutionError("invalid_release_payload")
    return frozenset(item.strip() for item in value if item.strip())


def _optional_int(payload: dict[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CareReferenceResolutionError("invalid_release_payload")
    return value


def _compatible_keys(payload: dict[str, object], key: str) -> frozenset[str]:
    value = payload.get(key)
    if isinstance(value, str):
        return frozenset({value})
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return frozenset(item for item in value if item)
    raise CareReferenceResolutionError("invalid_release_payload")


def resolve_active_care_reference_bundle(
    session: Session,
    *,
    selection: ActiveReleaseSelection,
) -> ResolvedCareReferenceBundle:
    scenario_release = _active_release(
        session,
        release_type="scenario_definition",
        release_key=selection.scenario_key,
        scope_key=selection.scope_key,
    )
    plan_release = _active_release(
        session,
        release_type="care_plan",
        release_key=selection.care_plan_key,
        scope_key=selection.scope_key,
    )
    pricing_release = _active_release(
        session,
        release_type="pricing_reference",
        release_key=selection.pricing_reference_key,
        scope_key=selection.scope_key,
    )
    utilization_release = _active_release(
        session,
        release_type="utilization_rule",
        release_key=selection.utilization_rule_key,
        scope_key=selection.scope_key,
    )

    scenario_row = session.get(CareScenarioDefinition, scenario_release.id)
    plan_row = session.get(CarePlanRow, plan_release.id)
    pricing_row = session.get(PricingReferenceSet, pricing_release.id)
    utilization_row = session.get(UtilizationRuleSet, utilization_release.id)
    if any(row is None for row in (scenario_row, plan_row, pricing_row, utilization_row)):
        raise CareReferenceResolutionError("release_specialization_missing")

    compatible = scenario_row.compatible_release_keys_json
    if (
        selection.care_plan_key not in _compatible_keys(compatible, "care_plan")
        or selection.pricing_reference_key not in _compatible_keys(compatible, "pricing_reference")
        or selection.utilization_rule_key not in _compatible_keys(compatible, "utilization_rule")
    ):
        raise CareReferenceResolutionError("incompatible_reference_release")
    if (
        plan_row.scenario_release_id != scenario_release.id
        or utilization_row.scenario_release_id != scenario_release.id
    ):
        raise CareReferenceResolutionError("incompatible_reference_release")

    plan_items = session.scalars(
        select(CarePlanItem)
        .where(CarePlanItem.care_plan_release_id == plan_release.id)
        .order_by(CarePlanItem.item_key)
    ).all()
    pricing_items = session.scalars(
        select(PricingReferenceItem)
        .where(PricingReferenceItem.pricing_reference_release_id == pricing_release.id)
        .order_by(
            PricingReferenceItem.service_code,
            PricingReferenceItem.facility_scope_key,
        )
    ).all()
    rule_rows = session.scalars(
        select(UtilizationRule)
        .where(UtilizationRule.utilization_rule_release_id == utilization_release.id)
        .order_by(UtilizationRule.rule_code)
    ).all()
    if not plan_items or not pricing_items or not rule_rows:
        raise CareReferenceResolutionError("release_items_missing")

    quantity_rules: list[QuantityRule] = []
    for rule in rule_rows:
        if rule.rule_type != "quantity_range":
            raise CareReferenceResolutionError("unsupported_utilization_rule_type")
        parameters = rule.parameters_json
        service_code = parameters.get("service_code")
        unit = parameters.get("unit")
        minimum = parameters.get("minimum")
        maximum = parameters.get("maximum")
        if (
            not isinstance(service_code, str)
            or not isinstance(unit, str)
            or isinstance(minimum, bool)
            or not isinstance(minimum, int)
            or isinstance(maximum, bool)
            or not isinstance(maximum, int)
        ):
            raise CareReferenceResolutionError("invalid_release_payload")
        quantity_rules.append(
            QuantityRule(
                service_code=service_code,
                unit=unit,
                minimum=minimum,
                maximum=maximum,
                rule_id=rule.id,
                rule_code=rule.rule_code,
            )
        )

    applicability = scenario_row.applicability_json
    required_inputs = scenario_row.required_inputs_json
    scenario = ScenarioDefinition(
        control=_control(scenario_release),
        encounter_types=_string_set(applicability, "encounter_types"),
        required_fields=_string_set(required_inputs, "fields"),
        allowed_regions=_string_set(applicability, "regions"),
        allowed_facility_ownership=_string_set(applicability, "facility_ownership"),
        allowed_facility_levels=_string_set(applicability, "facility_levels"),
        compatible_care_plan_keys=_compatible_keys(compatible, "care_plan"),
        compatible_pricing_reference_keys=_compatible_keys(compatible, "pricing_reference"),
        compatible_utilization_rule_keys=_compatible_keys(compatible, "utilization_rule"),
        minimum_age=_optional_int(applicability, "minimum_age"),
        maximum_age=_optional_int(applicability, "maximum_age"),
    )
    plan = CarePlan(
        control=_control(plan_release),
        scenario_release_id=plan_row.scenario_release_id,
        items=tuple(
            PlanItem(
                item_key=item.item_key,
                category=item.category,
                code_system=item.code_system,
                service_code=item.service_code,
                unit=item.unit,
                quantity_low=item.quantity_low,
                quantity_high=item.quantity_high,
                required=item.required,
            )
            for item in plan_items
        ),
        allowed_candidate_assumptions=tuple(
            sorted(_string_set(plan_row.assumptions_json, "allowed_candidate_assumptions"))
        ),
    )
    pricing = PricingReference(
        control=_control(pricing_release),
        comparability=pricing_row.comparability,
        items=tuple(
            PriceItem(
                code_system=item.code_system,
                service_code=item.service_code,
                unit=item.unit,
                facility_scope_key=item.facility_scope_key,
                currency=item.currency,
                amount_low_minor=item.amount_low_minor,
                amount_high_minor=item.amount_high_minor,
                economic_meaning=item.economic_meaning,
                reference_item_id=item.id,
                confidential=item.confidential,
            )
            for item in pricing_items
        ),
    )
    utilization = UtilizationRules(
        control=_control(utilization_release),
        scenario_release_id=utilization_row.scenario_release_id,
        quantity_rules=tuple(quantity_rules),
    )
    return ResolvedCareReferenceBundle(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
    )


def _authorize_context(
    session: Session,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    payer_request_id: uuid.UUID | None,
    request: EvaluationRequest,
) -> None:
    doctor = session.scalar(
        select(DoctorProfile)
        .join(User, User.id == DoctorProfile.user_id)
        .join(
            CareRelationship,
            CareRelationship.doctor_id == DoctorProfile.id,
        )
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
    if payer_request_id is None:
        return

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
    snapshot_lines = session.scalars(
        select(PayerRequestLine).where(PayerRequestLine.payer_request_id == payer_request_id)
    ).all()
    snapshots_by_id = {str(line.id): line for line in snapshot_lines}
    if set(snapshots_by_id) != {line.line_id for line in request.observed_lines}:
        raise CareReferenceAuthorizationError()
    for observed in request.observed_lines:
        snapshot = snapshots_by_id[observed.line_id]
        if (
            observed.currency != snapshot.currency
            or observed.actual_amount_minor != snapshot.actual_cost_minor
        ):
            raise CareReferenceAuthorizationError()


def evaluate_and_persist_authorized_care_reference(
    session: Session,
    *,
    actor_user_id: uuid.UUID,
    patient_id: uuid.UUID,
    clinical_event_id: uuid.UUID,
    selection: ActiveReleaseSelection,
    request: EvaluationRequest,
    payer_request_id: uuid.UUID | None = None,
    prior_evaluation_id: uuid.UUID | None = None,
) -> PersistedCareEvaluation:
    """Resolve active releases, authorize the case, evaluate, and append a result."""

    _authorize_context(
        session,
        actor_user_id=actor_user_id,
        patient_id=patient_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
        request=request,
    )
    if prior_evaluation_id is not None:
        prior = session.get(CareReferenceEvaluation, prior_evaluation_id)
        if (
            prior is None
            or prior.clinical_event_id != clinical_event_id
            or prior.payer_request_id != payer_request_id
        ):
            raise CareReferenceAuthorizationError()
    bundle = resolve_active_care_reference_bundle(session, selection=selection)
    result = evaluate_care_reference(
        scenario=bundle.scenario,
        plan=bundle.plan,
        pricing=bundle.pricing,
        utilization=bundle.utilization,
        request=request,
    )
    row = persist_evaluation(
        session,
        result=result,
        scenario_release_id=bundle.scenario.control.release_id,
        care_plan_release_id=bundle.plan.control.release_id,
        pricing_reference_release_id=bundle.pricing.control.release_id,
        utilization_rule_release_id=bundle.utilization.control.release_id,
        prior_evaluation_id=prior_evaluation_id,
        clinical_event_id=clinical_event_id,
        payer_request_id=payer_request_id,
    )
    session.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            patient_id=patient_id,
            event_type="care_reference_evaluation_created",
            resource_type="care_reference_evaluation",
            resource_id=row.id,
            metadata_json={
                "engine_contract_version": row.engine_contract_version,
                "status": row.status,
                "scenario_release_id": str(row.scenario_release_id),
                "care_plan_release_id": str(row.care_plan_release_id),
                "pricing_reference_release_id": str(row.pricing_reference_release_id),
                "utilization_rule_release_id": str(row.utilization_rule_release_id),
                "payer_request_linked": payer_request_id is not None,
                "content_free": True,
            },
        )
    )
    session.flush()
    return PersistedCareEvaluation(result=result, row=row)
