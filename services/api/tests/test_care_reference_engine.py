import hashlib
import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.care_reference_engine import (
    CarePlan,
    EvaluationContext,
    EvaluationRequest,
    JustifiedException,
    ObservedLine,
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
from app.care_reference_governance import (
    ReleaseActivationError,
    activate_release,
)
from app.database import SessionLocal
from app.models import (
    CarePlan as CarePlanRow,
)
from app.models import (
    CarePlanItem,
    CareReferenceEvaluation,
    CareScenarioDefinition,
    GovernedCareRelease,
    GovernedCareReleaseReview,
    PricingReferenceItem,
    PricingReferenceSet,
    UtilizationRule,
    UtilizationRuleSet,
)


def _control(
    release_key: str,
    *,
    status: str = "active",
    next_review_on: date | None = date(2027, 1, 1),
    rights_status: str = "approved",
    currency: str | None = "CNY",
) -> ReleaseControl:
    return ReleaseControl(
        release_id=uuid.uuid5(uuid.NAMESPACE_URL, f"dr-ai.test/{release_key}"),
        release_key=release_key,
        version="synthetic-v1",
        payload_checksum_sha256=hashlib.sha256(release_key.encode()).hexdigest(),
        lifecycle_status=status,
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
        next_review_on=next_review_on,
        rights_status=rights_status,
        storage_allowed=rights_status == "approved",
        derivation_allowed=rights_status == "approved",
        jurisdiction="CN",
        region="Synthetic Province",
        currency=currency,
    )


def _synthetic_bundle(
    *,
    code: str = "SYN-PHYSIO-01",
    unit: str = "session",
    quantity_low: int = 2,
    quantity_high: int = 4,
    amount_low_minor: int = 1000,
    amount_high_minor: int = 1500,
) -> tuple[ScenarioDefinition, CarePlan, PricingReference, UtilizationRules]:
    scenario_control = _control("synthetic-outpatient-rehabilitation")
    plan_control = _control("synthetic-rehabilitation-plan")
    pricing_control = _control("synthetic-rehabilitation-prices")
    rule_control = _control("synthetic-rehabilitation-rules")
    scenario = ScenarioDefinition(
        control=scenario_control,
        encounter_types=frozenset({"outpatient"}),
        required_fields=frozenset(
            {
                "jurisdiction",
                "region",
                "encounter_type",
                "facility_ownership",
                "facility_level",
                "currency",
                "patient_age",
            }
        ),
        allowed_regions=frozenset({"Synthetic Province"}),
        allowed_facility_ownership=frozenset({"public", "community"}),
        allowed_facility_levels=frozenset({"primary", "secondary"}),
        compatible_care_plan_keys=frozenset({plan_control.release_key}),
        compatible_pricing_reference_keys=frozenset({pricing_control.release_key}),
        compatible_utilization_rule_keys=frozenset({rule_control.release_key}),
        minimum_age=18,
    )
    plan = CarePlan(
        control=plan_control,
        scenario_release_id=scenario_control.release_id,
        items=(
            PlanItem(
                item_key="therapy-course",
                category="therapy",
                code_system="SYNTHETIC-SERVICE",
                service_code=code,
                unit=unit,
                quantity_low=quantity_low,
                quantity_high=quantity_high,
            ),
        ),
    )
    pricing = PricingReference(
        control=pricing_control,
        comparability="range",
        items=(
            PriceItem(
                code_system="SYNTHETIC-SERVICE",
                service_code=code,
                unit=unit,
                facility_scope_key="primary",
                currency="CNY",
                amount_low_minor=amount_low_minor,
                amount_high_minor=amount_high_minor,
                economic_meaning="synthetic expected range",
            ),
        ),
    )
    utilization = UtilizationRules(
        control=rule_control,
        scenario_release_id=scenario_control.release_id,
        quantity_rules=(
            QuantityRule(
                service_code=code,
                unit=unit,
                minimum=quantity_low,
                maximum=quantity_high,
            ),
        ),
    )
    return scenario, plan, pricing, utilization


def _context(**overrides: object) -> EvaluationContext:
    values: dict[str, object] = {
        "evaluated_on": date(2026, 7, 25),
        "reference_date": date(2026, 7, 25),
        "jurisdiction": "CN",
        "region": "Synthetic Province",
        "encounter_type": "outpatient",
        "facility_ownership": "public",
        "facility_level": "primary",
        "currency": "CNY",
        "patient_age": 42,
    }
    values.update(overrides)
    return EvaluationContext(**values)  # type: ignore[arg-type]


def test_blocked_ct_candidate_is_first_fixture_and_has_no_runtime_reference_data() -> None:
    blocked = _control(
        "cn-sh-outpatient-single-region-ct-plain-v1",
        status="blocked",
        rights_status="unresolved",
    )
    scenario = ScenarioDefinition(
        control=blocked,
        encounter_types=frozenset({"outpatient"}),
        required_fields=frozenset({"facility_level"}),
        allowed_regions=frozenset({"Shanghai"}),
        allowed_facility_ownership=frozenset({"public"}),
        allowed_facility_levels=frozenset({"primary", "secondary", "tertiary"}),
        compatible_care_plan_keys=frozenset({blocked.release_key}),
        compatible_pricing_reference_keys=frozenset({blocked.release_key}),
        compatible_utilization_rule_keys=frozenset({blocked.release_key}),
        minimum_age=18,
    )
    empty_plan = CarePlan(
        control=blocked,
        scenario_release_id=blocked.release_id,
        items=(),
    )
    empty_pricing = PricingReference(control=blocked, comparability="unavailable", items=())
    empty_rules = UtilizationRules(
        control=blocked,
        scenario_release_id=blocked.release_id,
        quantity_rules=(),
    )

    result = evaluate_care_reference(
        scenario=scenario,
        plan=empty_plan,
        pricing=empty_pricing,
        utilization=empty_rules,
        request=EvaluationRequest(context=_context(region="Shanghai", facility_level="tertiary")),
    )

    assert result.status == "suppressed"
    assert result.suppression_reasons == ("reference_release_unavailable",)
    assert result.lines == ()
    assert result.total_low_minor is None
    assert result.total_high_minor is None


def test_synthetic_release_calculates_exact_integer_ranges_and_reason_codes() -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle()
    result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=_context(),
            observed_lines=(
                ObservedLine(
                    line_id="synthetic-line-1",
                    code_system="SYNTHETIC-SERVICE",
                    service_code="SYN-PHYSIO-01",
                    unit="session",
                    quantity=3,
                    currency="CNY",
                    actual_amount_minor=4200,
                ),
            ),
        ),
    )

    assert result.status == "within_range"
    assert result.total_low_minor == 2000
    assert result.total_high_minor == 6000
    assert result.observed_total_minor == 4200
    assert "within_expected_range" in result.reason_codes
    assert "total_within_expected_range" in result.reason_codes
    assert result.input_checksum_sha256 != result.result_checksum_sha256


def test_second_synthetic_scenario_proves_configurability_and_justified_exception() -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle(
        code="SYN-LAB-PANEL-07",
        unit="panel",
        quantity_low=1,
        quantity_high=1,
        amount_low_minor=2000,
        amount_high_minor=3000,
    )
    result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=_context(),
            observed_lines=(
                ObservedLine(
                    line_id="synthetic-lab-line",
                    code_system="SYNTHETIC-SERVICE",
                    service_code="SYN-LAB-PANEL-07",
                    unit="panel",
                    quantity=1,
                    currency="CNY",
                    actual_amount_minor=4200,
                ),
            ),
            exception=JustifiedException(
                exception_code="synthetic_complex_processing",
                rationale="Synthetic fixture documents an authorized processing exception.",
                authorized_by="synthetic-clinician-reviewer",
                applies_to_line_ids=frozenset({"synthetic-lab-line"}),
            ),
        ),
    )

    assert result.status == "exception_recorded"
    assert "above_expected_range" in result.reason_codes
    assert "justified_exception_recorded" in result.reason_codes
    assert result.suppression_reasons == ("justified_exception",)


@pytest.mark.parametrize(
    ("context", "line", "expected_status", "expected_code"),
    [
        (
            _context(facility_level=None),
            None,
            "missing_information",
            "missing_facility_level",
        ),
        (
            _context(),
            ObservedLine(
                line_id="mixed-currency",
                code_system="SYNTHETIC-SERVICE",
                service_code="SYN-PHYSIO-01",
                unit="session",
                quantity=2,
                currency="USD",
                actual_amount_minor=3000,
            ),
            "invalid_observation",
            "mixed_currency",
        ),
        (
            _context(),
            ObservedLine(
                line_id="unsupported-code",
                code_system="SYNTHETIC-SERVICE",
                service_code="SYN-UNKNOWN",
                unit="session",
                quantity=2,
                currency="CNY",
                actual_amount_minor=3000,
            ),
            "invalid_observation",
            "unsupported_service_code_or_unit",
        ),
    ],
)
def test_engine_fails_closed_with_explicit_states(
    context: EvaluationContext,
    line: ObservedLine | None,
    expected_status: str,
    expected_code: str,
) -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle()
    result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=context,
            observed_lines=(() if line is None else (line,)),
        ),
    )
    assert result.status == expected_status
    assert expected_code in result.reason_codes


@pytest.mark.parametrize(
    ("bundle_change", "context", "expected_code"),
    [
        ("stale", _context(), "stale_reference_release"),
        (
            "unchanged",
            _context(reference_date=date(2025, 12, 31)),
            "no_applicable_reference_version",
        ),
        ("ceiling", _context(), "ceiling_only_not_comparable"),
    ],
)
def test_freshness_dates_and_economic_meaning_suppress_comparison(
    bundle_change: str,
    context: EvaluationContext,
    expected_code: str,
) -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle()
    if bundle_change == "stale":
        pricing = replace(
            pricing,
            control=replace(pricing.control, next_review_on=date(2026, 7, 24)),
        )
    if bundle_change == "ceiling":
        pricing = replace(pricing, comparability="ceiling_only")
    result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(context=context),
    )
    assert result.status == "suppressed"
    assert expected_code in result.suppression_reasons


def test_duplicate_lines_and_declared_total_mismatch_fail_closed() -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle()
    duplicate = ObservedLine(
        line_id="duplicate-line",
        code_system="SYNTHETIC-SERVICE",
        service_code="SYN-PHYSIO-01",
        unit="session",
        quantity=2,
        currency="CNY",
        actual_amount_minor=3000,
    )
    result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=_context(),
            observed_lines=(duplicate, duplicate),
            declared_observed_total_minor=3000,
        ),
    )
    assert result.status == "invalid_observation"
    assert "duplicate_observed_line_id" in result.reason_codes
    assert "unreconciled_observed_total" in result.reason_codes


def _release_row(
    release_type: str,
    release_key: str,
    version: str,
    *,
    status: str = "reviewed",
    rights_status: str = "approved",
) -> GovernedCareRelease:
    checksum = ("a" if version == "v1" else "b") * 64
    release = GovernedCareRelease(
        release_type=release_type,
        release_key=release_key,
        version=version,
        schema_version="synthetic.v1",
        lifecycle_status=status,
        jurisdiction="CN",
        region="Synthetic Province",
        facility_scope_json={"levels": ["primary"]},
        currency="CNY",
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
        source_authority="Synthetic fixture authority",
        source_locator=f"urn:dr-ai:synthetic:{release_key}:{version}",
        retrieved_at=datetime(2026, 7, 1, tzinfo=UTC),
        source_checksum_sha256=checksum,
        payload_checksum_sha256=checksum,
        provenance_json={"data_class": "synthetic"},
        required_review_types_json=["domain", "rights", "safety", "release"],
        rights_status=rights_status,
        storage_allowed=rights_status == "approved",
        derivation_allowed=rights_status == "approved",
        redistribution_allowed=False,
        provider_transmission_allowed=False,
        last_verified_on=date(2026, 7, 1),
        next_review_on=date(2026, 8, 15),
    )
    for review_type in ("domain", "rights", "safety", "release"):
        release.reviews.append(
            GovernedCareReleaseReview(
                review_type=review_type,
                decision="approved",
                reviewer_name=f"Synthetic {review_type} reviewer",
                reviewed_payload_checksum_sha256=checksum,
                rationale="Synthetic fixture approval for deterministic local tests.",
            )
        )
    return release


def _persist_complete_synthetic_bundle(
    session,
    *,
    release_ids: tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID],
) -> tuple[GovernedCareRelease, ...]:
    scenario = _release_row("scenario_definition", "synthetic-scenario", "v1")
    plan = _release_row("care_plan", "synthetic-plan", "v1")
    pricing = _release_row("pricing_reference", "synthetic-pricing", "v1")
    rules = _release_row("utilization_rule", "synthetic-rules", "v1")
    scenario.id, plan.id, pricing.id, rules.id = release_ids
    session.add_all((scenario, plan, pricing, rules))
    session.flush()
    scenario_definition = CareScenarioDefinition(
        release_id=scenario.id,
        scenario_family="synthetic rehabilitation",
        encounter_type="outpatient",
        applicability_json={"regions": ["Synthetic Province"]},
        required_inputs_json={"fields": ["facility_level", "currency"]},
        compatible_release_keys_json={
            "care_plan": plan.release_key,
            "pricing": pricing.release_key,
            "utilization": rules.release_key,
        },
    )
    session.add(scenario_definition)
    session.flush()
    session.add(
        CarePlanRow(
            release_id=plan.id,
            scenario_release_id=scenario.id,
            pathway_code="synthetic-pathway",
            assumptions_json={},
        )
    )
    session.add(
        PricingReferenceSet(
            release_id=pricing.id,
            price_type="synthetic_range",
            amount_semantics="expected_range",
            comparability="range",
        )
    )
    session.add(
        UtilizationRuleSet(
            release_id=rules.id,
            scenario_release_id=scenario.id,
            rule_contract_version="synthetic.v1",
        )
    )
    session.flush()
    session.add(
        CarePlanItem(
            care_plan_release_id=plan.id,
            item_key="therapy",
            category="therapy",
            code_system="SYNTHETIC-SERVICE",
            service_code="SYN-PHYSIO-01",
            unit="session",
            quantity_low=2,
            quantity_high=4,
            required=True,
            comparison_semantics="range",
        )
    )
    session.add(
        PricingReferenceItem(
            pricing_reference_release_id=pricing.id,
            code_system="SYNTHETIC-SERVICE",
            service_code="SYN-PHYSIO-01",
            unit="session",
            facility_scope_key="primary",
            currency="CNY",
            amount_low_minor=1000,
            amount_high_minor=1500,
            economic_meaning="synthetic expected range",
            confidential=False,
        )
    )
    session.add(
        UtilizationRule(
            utilization_rule_release_id=rules.id,
            rule_code="synthetic-quantity",
            rule_type="quantity_range",
            parameters_json={"service_code": "SYN-PHYSIO-01", "minimum": 2, "maximum": 4},
            rationale="Synthetic bounded quantity.",
        )
    )
    session.flush()
    return scenario, plan, pricing, rules


def test_release_activation_supersession_rollback_and_immutability() -> None:
    with SessionLocal() as session:
        release_v1 = _release_row("pricing_reference", "synthetic-activation", "v1")
        release_v2 = _release_row("pricing_reference", "synthetic-activation", "v2")
        blocked = _release_row(
            "pricing_reference",
            "synthetic-blocked",
            "v1",
            status="blocked",
            rights_status="unresolved",
        )
        session.add_all((release_v1, release_v2, blocked))
        session.flush()
        first = activate_release(
            session,
            release=release_v1,
            scope_key="CN|Synthetic Province|primary|CNY",
            actor_user_id=None,
            reason_code="initial_synthetic_activation",
            on_date=date(2026, 7, 25),
        )
        second = activate_release(
            session,
            release=release_v2,
            scope_key="CN|Synthetic Province|primary|CNY",
            actor_user_id=None,
            reason_code="synthetic_supersession",
            on_date=date(2026, 7, 25),
        )
        rolled_back = activate_release(
            session,
            release=release_v1,
            scope_key="CN|Synthetic Province|primary|CNY",
            actor_user_id=None,
            reason_code="synthetic_rollback",
            on_date=date(2026, 7, 25),
            rollback=True,
        )
        assert first.action == "activate"
        assert second.action == "supersede"
        assert second.prior_release_id == release_v1.id
        assert rolled_back.action == "rollback"
        assert rolled_back.prior_release_id == release_v2.id
        with pytest.raises(ReleaseActivationError, match="release_not_reviewed"):
            activate_release(
                session,
                release=blocked,
                scope_key="blocked",
                actor_user_id=None,
                reason_code="must_fail",
                on_date=date(2026, 7, 25),
            )
        session.commit()

        with pytest.raises(DBAPIError, match="children are immutable"):
            session.add(
                PricingReferenceSet(
                    release_id=release_v1.id,
                    price_type="tampered",
                    amount_semantics="tampered",
                    comparability="range",
                )
            )
            session.commit()
        session.rollback()

        with pytest.raises(DBAPIError, match="immutable"):
            session.execute(
                text(
                    "UPDATE governed_care_releases SET source_locator = 'tampered' "
                    "WHERE id = :release_id"
                ),
                {"release_id": release_v1.id},
            )
            session.commit()
        session.rollback()


def test_re_evaluation_appends_and_preserves_prior_result() -> None:
    scenario, plan, pricing, utilization = _synthetic_bundle()
    first_result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=_context(),
            observed_lines=(
                ObservedLine(
                    line_id="line-v1",
                    code_system="SYNTHETIC-SERVICE",
                    service_code="SYN-PHYSIO-01",
                    unit="session",
                    quantity=2,
                    currency="CNY",
                    actual_amount_minor=3000,
                ),
            ),
        ),
    )
    second_result = evaluate_care_reference(
        scenario=scenario,
        plan=plan,
        pricing=pricing,
        utilization=utilization,
        request=EvaluationRequest(
            context=_context(),
            observed_lines=(
                ObservedLine(
                    line_id="line-v2",
                    code_system="SYNTHETIC-SERVICE",
                    service_code="SYN-PHYSIO-01",
                    unit="session",
                    quantity=4,
                    currency="CNY",
                    actual_amount_minor=7000,
                ),
            ),
        ),
    )
    with SessionLocal() as session:
        scenario_row, plan_row, pricing_row, rules_row = _persist_complete_synthetic_bundle(
            session,
            release_ids=(
                scenario.control.release_id,
                plan.control.release_id,
                pricing.control.release_id,
                utilization.control.release_id,
            ),
        )
        first = persist_evaluation(
            session,
            result=first_result,
            scenario_release_id=scenario_row.id,
            care_plan_release_id=plan_row.id,
            pricing_reference_release_id=pricing_row.id,
            utilization_rule_release_id=rules_row.id,
        )
        first_id = first.id
        first_checksum = first.result_checksum_sha256
        second = persist_evaluation(
            session,
            result=second_result,
            scenario_release_id=scenario_row.id,
            care_plan_release_id=plan_row.id,
            pricing_reference_release_id=pricing_row.id,
            utilization_rule_release_id=rules_row.id,
            prior_evaluation_id=first.id,
        )
        session.commit()

        rows = session.scalars(
            select(CareReferenceEvaluation).order_by(CareReferenceEvaluation.created_at)
        ).all()
        assert len(rows) == 2
        assert second.prior_evaluation_id == first_id
        assert rows[0].result_checksum_sha256 == first_checksum
        assert rows[0].result_checksum_sha256 != rows[1].result_checksum_sha256
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(
                text(
                    "UPDATE care_reference_evaluations SET status = 'tampered' "
                    "WHERE id = :evaluation_id"
                ),
                {"evaluation_id": first_id},
            )
            session.commit()
