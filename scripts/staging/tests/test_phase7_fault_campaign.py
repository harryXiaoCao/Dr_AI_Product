from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "api"))

from app.phase7_operations import (  # noqa: E402
    CampaignStage,
    FaultCampaign,
    FaultCase,
    default_fault_campaign,
)


def test_default_campaign_includes_every_required_fault_as_content_free_plan() -> None:
    campaign = default_fault_campaign()

    assert {event.fault_case for event in campaign.events} == {
        fault_case.value for fault_case in FaultCase
    }
    assert all(event.stage == "planned" for event in campaign.events)
    assert all(event.result_code == "control_planned" for event in campaign.events)
    assert all(campaign.stage(fault_case) is CampaignStage.PLANNED for fault_case in FaultCase)


def test_fault_recovery_state_machine_is_ordered_and_idempotent() -> None:
    campaign = FaultCampaign([FaultCase.PROVIDER_OUTAGE])

    injected = campaign.transition(
        FaultCase.PROVIDER_OUTAGE,
        CampaignStage.INJECTED,
        result_code="fault_observed",
    )
    replay = campaign.transition(
        FaultCase.PROVIDER_OUTAGE,
        CampaignStage.INJECTED,
        result_code="fault_observed",
    )
    assert replay is injected
    campaign.transition(
        FaultCase.PROVIDER_OUTAGE,
        CampaignStage.CONTAINED,
        result_code="fallback_observed",
    )
    campaign.transition(
        FaultCase.PROVIDER_OUTAGE,
        CampaignStage.RECOVERED,
        result_code="recovery_completed",
    )
    campaign.transition(
        FaultCase.PROVIDER_OUTAGE,
        CampaignStage.VERIFIED,
        result_code="invariants_passed",
    )
    assert campaign.stage(FaultCase.PROVIDER_OUTAGE) is CampaignStage.VERIFIED


def test_fault_campaign_rejects_skips_conflicts_and_content_bearing_results() -> None:
    campaign = FaultCampaign([FaultCase.API_ROLLBACK])

    with pytest.raises(ValueError, match="invalid_campaign_transition"):
        campaign.transition(
            FaultCase.API_ROLLBACK,
            CampaignStage.RECOVERED,
            result_code="recovery_completed",
        )
    with pytest.raises(ValueError, match="content_bearing_or_unknown_result_code"):
        campaign.transition(
            FaultCase.API_ROLLBACK,
            CampaignStage.INJECTED,
            result_code="patient-specific failure detail",
        )
    campaign.transition(
        FaultCase.API_ROLLBACK,
        CampaignStage.INJECTED,
        result_code="fault_observed",
    )
    with pytest.raises(ValueError, match="campaign_idempotency_content_conflict"):
        campaign.transition(
            FaultCase.API_ROLLBACK,
            CampaignStage.INJECTED,
            result_code="rollback_completed",
        )


def test_fault_campaign_requires_unique_cases_and_rejects_out_of_scope_case() -> None:
    with pytest.raises(ValueError, match="fault_campaign_requires_unique_cases"):
        FaultCampaign([FaultCase.API_ROLLBACK, FaultCase.API_ROLLBACK])

    campaign = FaultCampaign([FaultCase.API_ROLLBACK])
    with pytest.raises(ValueError, match="fault_case_not_in_campaign"):
        campaign.stage(FaultCase.PROVIDER_OUTAGE)
