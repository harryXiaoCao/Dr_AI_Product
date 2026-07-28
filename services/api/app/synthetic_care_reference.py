"""Wholly synthetic governed care-reference bundle for local integration tests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.care_reference_governance import activate_release
from app.care_reference_integration import (
    ActiveReleaseSelection,
    build_care_reference_scope_key,
)
from app.models import (
    CarePlan,
    CarePlanItem,
    CareScenarioDefinition,
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseReview,
    PricingReferenceItem,
    PricingReferenceSet,
    UtilizationRule,
    UtilizationRuleSet,
)

SYNTHETIC_SCENARIO_KEY = "synthetic-outpatient-rehabilitation"
SYNTHETIC_CARE_PLAN_KEY = "synthetic-rehabilitation-plan"
SYNTHETIC_PRICING_KEY = "synthetic-rehabilitation-pricing"
SYNTHETIC_UTILIZATION_KEY = "synthetic-rehabilitation-utilization"
SYNTHETIC_SERVICE_CODE = "SYN-REHAB-SESSION-01"
SYNTHETIC_CODE_SYSTEM = "DR-AI-SYNTHETIC-SERVICE"
SYNTHETIC_UNIT = "session"
SYNTHETIC_LAB_SCENARIO_KEY = "synthetic-outpatient-laboratory"
SYNTHETIC_LAB_CARE_PLAN_KEY = "synthetic-laboratory-plan"
SYNTHETIC_LAB_PRICING_KEY = "synthetic-laboratory-pricing"
SYNTHETIC_LAB_UTILIZATION_KEY = "synthetic-laboratory-utilization"
SYNTHETIC_LAB_SERVICE_CODE = "SYN-LAB-PANEL-07"
SYNTHETIC_LAB_UNIT = "panel"
SYNTHETIC_IMAGING_SCENARIO_KEY = "synthetic-outpatient-imaging"
SYNTHETIC_IMAGING_CARE_PLAN_KEY = "synthetic-imaging-plan"
SYNTHETIC_IMAGING_PRICING_KEY = "synthetic-imaging-pricing"
SYNTHETIC_IMAGING_UTILIZATION_KEY = "synthetic-imaging-utilization"
SYNTHETIC_CONSULTATION_SCENARIO_KEY = "synthetic-outpatient-consultation"
SYNTHETIC_CONSULTATION_CARE_PLAN_KEY = "synthetic-consultation-pathway"
SYNTHETIC_CONSULTATION_PRICING_KEY = "synthetic-consultation-pricing"
SYNTHETIC_CONSULTATION_UTILIZATION_KEY = "synthetic-consultation-utilization"
SYNTHETIC_SCOPE_KEY = build_care_reference_scope_key(
    jurisdiction="CN",
    region="Synthetic Province",
    facility_ownership="public",
    facility_level="primary",
    currency="CNY",
)


def synthetic_active_selection() -> ActiveReleaseSelection:
    return ActiveReleaseSelection(
        scenario_key=SYNTHETIC_SCENARIO_KEY,
        care_plan_key=SYNTHETIC_CARE_PLAN_KEY,
        pricing_reference_key=SYNTHETIC_PRICING_KEY,
        utilization_rule_key=SYNTHETIC_UTILIZATION_KEY,
        scope_key=SYNTHETIC_SCOPE_KEY,
    )


def synthetic_laboratory_selection() -> ActiveReleaseSelection:
    return ActiveReleaseSelection(
        scenario_key=SYNTHETIC_LAB_SCENARIO_KEY,
        care_plan_key=SYNTHETIC_LAB_CARE_PLAN_KEY,
        pricing_reference_key=SYNTHETIC_LAB_PRICING_KEY,
        utilization_rule_key=SYNTHETIC_LAB_UTILIZATION_KEY,
        scope_key=SYNTHETIC_SCOPE_KEY,
    )


def synthetic_imaging_selection() -> ActiveReleaseSelection:
    return ActiveReleaseSelection(
        scenario_key=SYNTHETIC_IMAGING_SCENARIO_KEY,
        care_plan_key=SYNTHETIC_IMAGING_CARE_PLAN_KEY,
        pricing_reference_key=SYNTHETIC_IMAGING_PRICING_KEY,
        utilization_rule_key=SYNTHETIC_IMAGING_UTILIZATION_KEY,
        scope_key=SYNTHETIC_SCOPE_KEY,
    )


def synthetic_consultation_selection() -> ActiveReleaseSelection:
    return ActiveReleaseSelection(
        scenario_key=SYNTHETIC_CONSULTATION_SCENARIO_KEY,
        care_plan_key=SYNTHETIC_CONSULTATION_CARE_PLAN_KEY,
        pricing_reference_key=SYNTHETIC_CONSULTATION_PRICING_KEY,
        utilization_rule_key=SYNTHETIC_CONSULTATION_UTILIZATION_KEY,
        scope_key=SYNTHETIC_SCOPE_KEY,
    )


def _checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _release(
    session: Session,
    *,
    release_type: str,
    release_key: str,
    version: str,
    payload: dict[str, object],
    effective_from: date,
    effective_to: date,
    next_review_on: date,
    provider_transmission_allowed: bool,
) -> tuple[GovernedCareRelease, bool]:
    checksum = _checksum(
        {
            "content": payload,
            "provider_transmission_allowed": provider_transmission_allowed,
        }
    )
    existing = session.scalar(
        select(GovernedCareRelease).where(
            GovernedCareRelease.release_type == release_type,
            GovernedCareRelease.release_key == release_key,
            GovernedCareRelease.version == version,
        )
    )
    if existing is not None:
        if existing.payload_checksum_sha256 != checksum:
            raise ValueError("synthetic_release_checksum_conflict")
        return existing, False
    release = GovernedCareRelease(
        release_type=release_type,
        release_key=release_key,
        version=version,
        schema_version="care-reference.synthetic.v1",
        lifecycle_status="draft",
        jurisdiction="CN",
        region="Synthetic Province",
        facility_scope_json={
            "ownership": ["public"],
            "levels": ["primary"],
        },
        currency="CNY",
        effective_from=effective_from,
        effective_to=effective_to,
        source_authority="Dr. AI synthetic integration fixture",
        source_locator=f"urn:dr-ai:synthetic-care-reference:{release_key}:{version}",
        retrieved_at=datetime.now(UTC),
        source_checksum_sha256=checksum,
        payload_checksum_sha256=checksum,
        provenance_json={
            "data_class": "wholly_synthetic",
            "fixture_purpose": "local_deterministic_and_candidate_integration",
        },
        required_review_types_json=["domain", "rights", "safety", "release"],
        rights_status="not_required_for_early_synthetic_development",
        storage_allowed=True,
        derivation_allowed=True,
        redistribution_allowed=False,
        provider_transmission_allowed=provider_transmission_allowed,
        last_verified_on=effective_from,
        next_review_on=next_review_on,
    )
    session.add(release)
    session.flush()
    return release, True


def _review(release: GovernedCareRelease) -> None:
    for review_type in release.required_review_types_json:
        release.reviews.append(
            GovernedCareReleaseReview(
                review_type=review_type,
                decision="not_required_for_early_synthetic_development",
                reviewer_name="Dr. AI product-owner synthetic-stage policy",
                reviewed_payload_checksum_sha256=release.payload_checksum_sha256,
                rationale=(
                    "External review is not required for the current wholly synthetic "
                    "development and controlled-staging stage. This is not a professional "
                    "approval and grants no real-patient, live-payer, public-production, "
                    "commercial, clinical, pricing, legal, or regulatory authority."
                ),
            )
        )
    release.lifecycle_status = "reviewed"


def install_synthetic_care_reference_bundle(
    session: Session,
    *,
    version: str = "v3-slice-d",
    effective_from: date = date(2026, 1, 1),
    effective_to: date = date(2027, 12, 31),
    next_review_on: date = date(2027, 1, 1),
    price_low_minor: int = 1000,
    price_high_minor: int = 1500,
    activate_on: date = date(2026, 7, 25),
    provider_transmission_allowed: bool = True,
    selection: ActiveReleaseSelection | None = None,
    scenario_family: str = "synthetic outpatient rehabilitation",
    pathway_code: str = "synthetic-rehabilitation-standard",
    item_key: str = "synthetic-therapy-course",
    category: str = "therapy",
    code_system: str = SYNTHETIC_CODE_SYSTEM,
    service_code: str = SYNTHETIC_SERVICE_CODE,
    unit: str = SYNTHETIC_UNIT,
    quantity_low: int = 2,
    quantity_high: int = 4,
) -> dict[str, GovernedCareRelease]:
    """Install and activate one idempotent, wholly synthetic release bundle."""

    selected = selection or synthetic_active_selection()
    scenario_payload: dict[str, object] = {
        "scenario_family": scenario_family,
        "encounter_type": "outpatient",
        "applicability": {
            "encounter_types": ["outpatient"],
            "regions": ["Synthetic Province"],
            "facility_ownership": ["public"],
            "facility_levels": ["primary"],
            "minimum_age": 18,
        },
        "required_inputs": {
            "fields": [
                "jurisdiction",
                "region",
                "encounter_type",
                "facility_ownership",
                "facility_level",
                "currency",
                "patient_age",
            ]
        },
        "compatible_release_keys": {
            "care_plan": [selected.care_plan_key],
            "pricing_reference": [selected.pricing_reference_key],
            "utilization_rule": [selected.utilization_rule_key],
        },
    }
    scenario, scenario_created = _release(
        session,
        release_type="scenario_definition",
        release_key=selected.scenario_key,
        version=version,
        payload=scenario_payload,
        effective_from=effective_from,
        effective_to=effective_to,
        next_review_on=next_review_on,
        provider_transmission_allowed=provider_transmission_allowed,
    )
    if scenario_created:
        session.add(
            CareScenarioDefinition(
                release_id=scenario.id,
                scenario_family=str(scenario_payload["scenario_family"]),
                encounter_type=str(scenario_payload["encounter_type"]),
                applicability_json=scenario_payload["applicability"],
                required_inputs_json=scenario_payload["required_inputs"],
                compatible_release_keys_json=scenario_payload["compatible_release_keys"],
            )
        )
        _review(scenario)
        session.flush()

    plan_payload: dict[str, object] = {
        "scenario_release_id": str(scenario.id),
        "pathway_code": pathway_code,
        "assumptions": {
            "data_class": "wholly_synthetic",
            "allowed_candidate_assumptions": [
                "The candidate uses wholly synthetic reference data."
            ],
        },
        "items": [
            {
                "item_key": item_key,
                "category": category,
                "code_system": code_system,
                "service_code": service_code,
                "unit": unit,
                "quantity_low": quantity_low,
                "quantity_high": quantity_high,
            }
        ],
    }
    plan, plan_created = _release(
        session,
        release_type="care_plan",
        release_key=selected.care_plan_key,
        version=version,
        payload=plan_payload,
        effective_from=effective_from,
        effective_to=effective_to,
        next_review_on=next_review_on,
        provider_transmission_allowed=provider_transmission_allowed,
    )
    if plan_created:
        session.add(
            CarePlan(
                release_id=plan.id,
                scenario_release_id=scenario.id,
                pathway_code=pathway_code,
                assumptions_json=plan_payload["assumptions"],
            )
        )
        session.flush()
        session.add(
            CarePlanItem(
                care_plan_release_id=plan.id,
                item_key=item_key,
                category=category,
                code_system=code_system,
                service_code=service_code,
                unit=unit,
                quantity_low=quantity_low,
                quantity_high=quantity_high,
                required=True,
                comparison_semantics="range",
            )
        )
        _review(plan)
        session.flush()

    pricing_payload: dict[str, object] = {
        "price_type": "synthetic_expected_range",
        "amount_semantics": "synthetic_expected_range",
        "comparability": "range",
        "items": [
            {
                "code_system": code_system,
                "service_code": service_code,
                "unit": unit,
                "facility_scope_key": "primary",
                "currency": "CNY",
                "amount_low_minor": price_low_minor,
                "amount_high_minor": price_high_minor,
            }
        ],
    }
    pricing, pricing_created = _release(
        session,
        release_type="pricing_reference",
        release_key=selected.pricing_reference_key,
        version=version,
        payload=pricing_payload,
        effective_from=effective_from,
        effective_to=effective_to,
        next_review_on=next_review_on,
        provider_transmission_allowed=provider_transmission_allowed,
    )
    if pricing_created:
        session.add(
            PricingReferenceSet(
                release_id=pricing.id,
                price_type="synthetic_expected_range",
                amount_semantics="synthetic_expected_range",
                comparability="range",
            )
        )
        session.flush()
        session.add(
            PricingReferenceItem(
                pricing_reference_release_id=pricing.id,
                code_system=code_system,
                service_code=service_code,
                unit=unit,
                facility_scope_key="primary",
                currency="CNY",
                amount_low_minor=price_low_minor,
                amount_high_minor=price_high_minor,
                economic_meaning="wholly synthetic expected range",
                confidential=False,
            )
        )
        _review(pricing)
        session.flush()

    utilization_payload: dict[str, object] = {
        "scenario_release_id": str(scenario.id),
        "rule_contract_version": "synthetic.quantity-range.v1",
        "rules": [
            {
                "rule_code": f"{item_key}-quantity",
                "rule_type": "quantity_range",
                "service_code": service_code,
                "unit": unit,
                "minimum": quantity_low,
                "maximum": quantity_high,
            }
        ],
    }
    utilization, utilization_created = _release(
        session,
        release_type="utilization_rule",
        release_key=selected.utilization_rule_key,
        version=version,
        payload=utilization_payload,
        effective_from=effective_from,
        effective_to=effective_to,
        next_review_on=next_review_on,
        provider_transmission_allowed=provider_transmission_allowed,
    )
    if utilization_created:
        session.add(
            UtilizationRuleSet(
                release_id=utilization.id,
                scenario_release_id=scenario.id,
                rule_contract_version="synthetic.quantity-range.v1",
            )
        )
        session.flush()
        session.add(
            UtilizationRule(
                utilization_rule_release_id=utilization.id,
                rule_code=f"{item_key}-quantity",
                rule_type="quantity_range",
                parameters_json={
                    "service_code": service_code,
                    "unit": unit,
                    "minimum": quantity_low,
                    "maximum": quantity_high,
                },
                rationale="Wholly synthetic bounded quantity for local tests.",
            )
        )
        _review(utilization)
        session.flush()

    releases = {
        "scenario": scenario,
        "care_plan": plan,
        "pricing": pricing,
        "utilization": utilization,
    }
    for release in releases.values():
        active_id = session.scalar(
            select(GovernedActiveCareRelease.release_id).where(
                GovernedActiveCareRelease.release_type == release.release_type,
                GovernedActiveCareRelease.release_key == release.release_key,
                GovernedActiveCareRelease.scope_key == selected.scope_key,
            )
        )
        if active_id != release.id:
            activate_release(
                session,
                release=release,
                scope_key=selected.scope_key,
                actor_user_id=None,
                reason_code="synthetic_local_integration_activation",
                on_date=activate_on,
            )
    session.flush()
    return releases


def install_synthetic_laboratory_reference_bundle(
    session: Session,
    *,
    version: str = "v1-slice-d",
) -> dict[str, GovernedCareRelease]:
    """Install an unrelated synthetic scenario through the same release contract."""

    return install_synthetic_care_reference_bundle(
        session,
        version=version,
        price_low_minor=700,
        price_high_minor=900,
        selection=synthetic_laboratory_selection(),
        scenario_family="synthetic outpatient laboratory",
        pathway_code="synthetic-laboratory-standard",
        item_key="synthetic-laboratory-panel",
        category="laboratory",
        service_code=SYNTHETIC_LAB_SERVICE_CODE,
        unit=SYNTHETIC_LAB_UNIT,
        quantity_low=1,
        quantity_high=1,
    )


def install_synthetic_imaging_reference_bundle(
    session: Session,
    *,
    version: str = "v1-synthetic-stage",
) -> dict[str, GovernedCareRelease]:
    """Install a non-official imaging fixture with deterministic ranges."""

    return install_synthetic_care_reference_bundle(
        session,
        version=version,
        price_low_minor=8800,
        price_high_minor=12600,
        selection=synthetic_imaging_selection(),
        scenario_family="synthetic outpatient imaging",
        pathway_code="synthetic-imaging-standard-or-observation",
        item_key="synthetic-imaging-study",
        category="imaging",
        service_code="SYN-IMG-STUDY-11",
        unit="study",
        quantity_low=1,
        quantity_high=2,
    )


def install_synthetic_consultation_reference_bundle(
    session: Session,
    *,
    version: str = "v1-synthetic-stage",
) -> dict[str, GovernedCareRelease]:
    """Install a consultation/treatment-session pathway fixture."""

    return install_synthetic_care_reference_bundle(
        session,
        version=version,
        price_low_minor=2400,
        price_high_minor=4800,
        selection=synthetic_consultation_selection(),
        scenario_family="synthetic consultation or treatment-session pathway",
        pathway_code="synthetic-consultation-follow-up-alternative",
        item_key="synthetic-consultation-session",
        category="consultation",
        service_code="SYN-CONSULT-SESSION-21",
        unit="session",
        quantity_low=1,
        quantity_high=3,
    )


def install_all_synthetic_stage_reference_families(
    session: Session,
) -> dict[str, dict[str, GovernedCareRelease]]:
    """Install every governed synthetic family used by early-stage workflows."""

    return {
        "rehabilitation": install_synthetic_care_reference_bundle(
            session, version="v4-synthetic-stage"
        ),
        "laboratory": install_synthetic_laboratory_reference_bundle(
            session, version="v2-synthetic-stage"
        ),
        "imaging": install_synthetic_imaging_reference_bundle(session),
        "consultation": install_synthetic_consultation_reference_bundle(session),
    }
