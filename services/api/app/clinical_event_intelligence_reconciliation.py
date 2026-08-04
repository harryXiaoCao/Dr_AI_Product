"""Bounded critic validation and deterministic disagreement reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import ValidationError

from app.clinical_event_intelligence_contracts import (
    CEI_RECONCILIATION_VERSION,
    CriticOutput,
    FrozenClinicalEventSnapshot,
    ValidatedIntelligence,
    canonical_checksum,
)


@dataclass(frozen=True)
class ReconciliationResult:
    state: Literal["agreement", "partial_disagreement", "material_disagreement", "unavailable"]
    reconciliation_version: str
    discrepancy_categories: tuple[str, ...]
    critic_output_checksum_sha256: str | None
    deterministic_primary_preserved: bool = True


def reconcile_critic(
    output: object | None,
    *,
    snapshot: FrozenClinicalEventSnapshot,
    primary: ValidatedIntelligence,
) -> ReconciliationResult:
    if output is None:
        return ReconciliationResult(
            state="unavailable",
            reconciliation_version=CEI_RECONCILIATION_VERSION,
            discrepancy_categories=(),
            critic_output_checksum_sha256=None,
        )
    try:
        critic = CriticOutput.model_validate(output, strict=True)
    except ValidationError:
        return ReconciliationResult(
            state="unavailable",
            reconciliation_version=CEI_RECONCILIATION_VERSION,
            discrepancy_categories=("malformed_critic",),
            critic_output_checksum_sha256=canonical_checksum(output),
        )
    if (
        critic.snapshot_checksum_sha256 != snapshot.snapshot_checksum_sha256
        or critic.primary_output_checksum_sha256 != primary.output_checksum_sha256
    ):
        return ReconciliationResult(
            state="unavailable",
            reconciliation_version=CEI_RECONCILIATION_VERSION,
            discrepancy_categories=("critic_lineage_mismatch",),
            critic_output_checksum_sha256=canonical_checksum(output),
        )
    categories = tuple(sorted({item.category for item in critic.discrepancies}))
    if not critic.discrepancies:
        state = "agreement"
    elif any(item.severity == "material" for item in critic.discrepancies):
        state = "material_disagreement"
    else:
        state = "partial_disagreement"
    return ReconciliationResult(
        state=state,
        reconciliation_version=CEI_RECONCILIATION_VERSION,
        discrepancy_categories=categories,
        critic_output_checksum_sha256=canonical_checksum(output),
    )
