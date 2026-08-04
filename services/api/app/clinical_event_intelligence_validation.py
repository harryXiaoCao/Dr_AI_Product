"""Deterministic validation and AI support score aggregation."""

from __future__ import annotations

import json
from copy import deepcopy

from pydantic import ValidationError

from app.clinical_event_intelligence_contracts import (
    CEI_SCORE_CONTRACT_VERSION,
    FrozenClinicalEventSnapshot,
    PrimaryIntelligenceOutput,
    RetrievalManifest,
    ScoreDimensions,
    ValidatedIntelligence,
    ValidatedRequestedItem,
    canonical_checksum,
)

_WEIGHTS_BP = {
    "clinical_fit": 2500,
    "evidence_support": 2000,
    "timing_sequence": 1500,
    "quantity_intensity": 1500,
    "documentation_completeness": 1500,
    "cost_alignment": 1000,
}
_PROHIBITED = (
    "approve",
    "approved",
    "deny",
    "denied",
    "fraud",
    "fraudulent",
    "medical necessity score",
    "risk score",
    "must reduce",
    "must delay",
    "remove care",
    "批准",
    "拒赔",
    "欺诈",
    "必须削减",
    "延误治疗",
)


class IntelligenceValidationError(ValueError):
    def __init__(self, reason_codes: list[str]) -> None:
        self.reason_codes = sorted(set(reason_codes))
        super().__init__(",".join(self.reason_codes))


_PROVENANCE_TIER_BY_SOURCE_TYPE = {
    "facility_price": 1,
    "payer_price": 1,
    "regional_reference": 2,
    "comparable_case": 3,
    "care_pathway": 4,
}


def normalize_cost_provenance(
    output: object,
    *,
    snapshot: FrozenClinicalEventSnapshot,
    retrieval: RetrievalManifest,
) -> tuple[object, list[str]]:
    """Bind model-selected cost evidence to admitted, line-matched sources.

    The server never invents evidence. Unsupported selections are discarded and
    become explicit model-only tier 5 estimates; mixed valid selections use the
    least authoritative selected tier and retain only sources valid for it.
    """

    if not isinstance(output, dict):
        return output, []
    normalized = deepcopy(output)
    assessments = normalized.get("requested_item_assessments")
    if not isinstance(assessments, list):
        return normalized, []
    line_by_id = {line.requested_line_id: line for line in snapshot.requested_lines}
    source_by_id = {source.source_id: source for source in retrieval.sources}
    results: list[str] = []
    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue
        line_id = assessment.get("requested_line_id")
        estimate = assessment.get("estimated_cost")
        line = line_by_id.get(line_id) if isinstance(line_id, str) else None
        if line is None or not isinstance(estimate, dict):
            continue
        selected_ids = estimate.get("source_ids")
        selected_ids = selected_ids if isinstance(selected_ids, list) else []
        eligible_by_tier: dict[int, list[str]] = {}
        for selected_id in selected_ids:
            if not isinstance(selected_id, str):
                continue
            source = source_by_id.get(selected_id)
            tier = _PROVENANCE_TIER_BY_SOURCE_TYPE.get(source.source_type) if source else None
            if tier is None or not _source_matches_requested_line(
                source,
                code_system=line.code_system,
                service_code=line.service_code,
                unit=line.unit,
                currency=line.currency,
            ):
                continue
            eligible_by_tier.setdefault(tier, []).append(selected_id)
        if eligible_by_tier:
            derived_tier = max(eligible_by_tier)
            estimate["provenance_tier"] = derived_tier
            estimate["source_ids"] = eligible_by_tier[derived_tier]
            estimate["is_model_only_exploratory"] = False
            result = f"server_bound_cost_provenance:{line_id}:tier_{derived_tier}"
        else:
            estimate["provenance_tier"] = 5
            estimate["source_ids"] = []
            estimate["is_model_only_exploratory"] = True
            result = f"server_forced_tier5_no_admitted_cost_source:{line_id}"
        results.append(result)
    return normalized, results


def normalize_tier5_uncertainty(output: object) -> tuple[object, list[str]]:
    """Safely widen only narrow model-only ranges before strict validation."""

    if not isinstance(output, dict):
        return output, []
    normalized = deepcopy(output)
    assessments = normalized.get("requested_item_assessments")
    if not isinstance(assessments, list):
        return normalized, []
    widened = False
    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue
        estimate = assessment.get("estimated_cost")
        if not isinstance(estimate, dict) or estimate.get("provenance_tier") != 5:
            continue
        low = estimate.get("low_minor")
        high = estimate.get("high_minor")
        if not isinstance(low, int) or isinstance(low, bool):
            continue
        if not isinstance(high, int) or isinstance(high, bool):
            continue
        safe_high = low + max(1000, low)
        if high < safe_high:
            estimate["high_minor"] = safe_high
            widened = True
    return normalized, (["server_widened_tier5_uncertainty"] if widened else [])


def aggregate_ai_support_score(
    scores: ScoreDimensions,
    *,
    provenance_tier: int,
) -> tuple[int, int]:
    """Aggregate independent dimensions; tier 5 receives zero cost weight."""

    weights = dict(_WEIGHTS_BP)
    cost_weight = 0 if provenance_tier == 5 else weights["cost_alignment"]
    weights["cost_alignment"] = cost_weight
    denominator = sum(weights.values())
    numerator = sum(getattr(scores, name) * weight for name, weight in weights.items())
    return round(numerator / denominator), cost_weight


def score_band(score: int) -> str:
    if score >= 80:
        return "strongly_supported"
    if score >= 60:
        return "plausible"
    if score >= 40:
        return "materially_uncertain"
    return "weakly_supported_human_review"


def _all_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str).lower()


def _source_matches_requested_line(
    source: object,
    *,
    code_system: str | None,
    service_code: str | None,
    unit: str,
    currency: str,
) -> bool:
    payload = getattr(source, "payload", {})
    if not isinstance(payload, dict):
        return False
    price_items = payload.get("price_items")
    cost_analogues = payload.get("cost_analogues")
    candidates = [
        *(price_items if isinstance(price_items, list) else []),
        *(cost_analogues if isinstance(cost_analogues, list) else []),
    ]
    return isinstance(candidates, list) and any(
        isinstance(candidate, dict)
        and candidate.get("code_system") == code_system
        and candidate.get("service_code") == service_code
        and candidate.get("unit") == unit
        and candidate.get("currency") == currency
        for candidate in candidates
    )


def validate_primary_output(
    output: object,
    *,
    snapshot: FrozenClinicalEventSnapshot,
    retrieval: RetrievalManifest,
    server_normalizations: list[str] | None = None,
) -> ValidatedIntelligence:
    normalization_results = list(server_normalizations or [])
    try:
        primary = PrimaryIntelligenceOutput.model_validate(output, strict=True)
    except ValidationError as exc:
        raise IntelligenceValidationError(["malformed_schema"]) from exc
    reasons: list[str] = []
    if primary.snapshot_checksum_sha256 != snapshot.snapshot_checksum_sha256:
        reasons.append("snapshot_checksum_mismatch")
    if primary.retrieval_manifest_checksum_sha256 != retrieval.manifest_checksum_sha256:
        reasons.append("retrieval_checksum_mismatch")
    if any(term in _all_text(primary.model_dump(mode="json")) for term in _PROHIBITED):
        reasons.append("prohibited_decision_language")
    requested_ids = [line.requested_line_id for line in snapshot.requested_lines]
    assessed_ids = [item.requested_line_id for item in primary.requested_item_assessments]
    if len(assessed_ids) != len(set(assessed_ids)):
        reasons.append("duplicate_requested_line_assessment")
    if set(assessed_ids) != set(requested_ids) or len(assessed_ids) != len(requested_ids):
        reasons.append("requested_line_coverage_mismatch")
    fact_ids = {fact.fact_id for fact in snapshot.facts_used}
    source_ids = {source.source_id for source in retrieval.sources}
    source_by_id = {source.source_id: source for source in retrieval.sources}
    pathway_ids = [pathway.pathway_id for pathway in primary.pathways]
    if len(pathway_ids) != len(set(pathway_ids)):
        reasons.append("duplicate_pathway_id")
    pathway_id_set = set(pathway_ids)
    pathway_item_keys = {item.item_key for pathway in primary.pathways for item in pathway.items}
    if pathway_item_keys & set(requested_ids):
        reasons.append("predicted_pathway_item_uses_requested_line_identity")
    for pathway in primary.pathways:
        if any(fact_id not in fact_ids for fact_id in pathway.trigger_fact_ids):
            reasons.append("unsupported_pathway_fact")
        for item in pathway.items:
            if any(fact_id not in fact_ids for fact_id in item.rationale_fact_ids):
                reasons.append("unsupported_pathway_item_fact")
    validated: list[ValidatedRequestedItem] = []
    line_by_id = {line.requested_line_id: line for line in snapshot.requested_lines}
    for item in primary.requested_item_assessments:
        line = line_by_id.get(item.requested_line_id)
        if line is None:
            continue
        if any(pathway_id not in pathway_id_set for pathway_id in item.mapped_pathway_ids):
            reasons.append("unknown_mapped_pathway")
        if any(
            fact_id not in fact_ids
            for fact_id in item.supporting_fact_ids + item.contradicting_fact_ids
        ):
            reasons.append("unsupported_assessment_fact")
        if item.estimated_quantity.unit != line.unit:
            reasons.append("requested_quantity_unit_mismatch")
        estimate = item.estimated_cost
        if estimate.currency != line.currency:
            reasons.append("requested_cost_currency_mismatch")
        if estimate.provenance_tier == 5:
            if estimate.source_ids or not estimate.is_model_only_exploratory:
                reasons.append("tier5_source_or_label_violation")
            minimum_width = max(1000, estimate.low_minor)
            if estimate.high_minor - estimate.low_minor < minimum_width:
                reasons.append("tier5_uncertainty_not_wide")
        else:
            if not estimate.source_ids or estimate.is_model_only_exploratory:
                reasons.append("authoritative_tier_source_missing")
            if any(source_id not in source_ids for source_id in estimate.source_ids):
                reasons.append("unadmitted_cost_source")
            allowed_source_types = {
                1: {"facility_price", "payer_price"},
                2: {"regional_reference"},
                3: {"comparable_case"},
                4: {"care_pathway"},
            }[estimate.provenance_tier]
            admitted_sources = [
                source_by_id[source_id]
                for source_id in estimate.source_ids
                if source_id in source_by_id
            ]
            if any(source.source_type not in allowed_source_types for source in admitted_sources):
                reasons.append("cost_provenance_tier_source_mismatch")
            for source in admitted_sources:
                if not _source_matches_requested_line(
                    source,
                    code_system=line.code_system,
                    service_code=line.service_code,
                    unit=line.unit,
                    currency=line.currency,
                ):
                    reasons.append("cost_reference_line_mismatch")
        score, cost_weight = aggregate_ai_support_score(
            item.scores,
            provenance_tier=estimate.provenance_tier,
        )
        validated.append(
            ValidatedRequestedItem(
                proposal=item,
                ai_support_score=score,
                score_band=score_band(score),  # type: ignore[arg-type]
                score_contract_version=CEI_SCORE_CONTRACT_VERSION,
                cost_alignment_weight_bp=cost_weight,  # type: ignore[arg-type]
                validation_results=[
                    "Every score dimension is independently bounded from 0 to 100.",
                    "The AI support score cannot trigger a clinical or payer action.",
                    (
                        "Tier 5 cost alignment has zero aggregation weight."
                        if estimate.provenance_tier == 5
                        else "Cost provenance is bound to an admitted retrieval source."
                    ),
                    *normalization_results,
                ],
            )
        )
    if reasons:
        raise IntelligenceValidationError(reasons)
    body = {
        "primary": primary.model_dump(mode="json"),
        "assessments": [item.model_dump(mode="json") for item in validated],
        "validation_results": [
            "Every immutable requested line appears exactly once.",
            "Predicted pathway items remain separate from requested lines.",
            "No score or band causes an automatic clinical or payer action.",
            *normalization_results,
        ],
    }
    return ValidatedIntelligence(
        primary=primary,
        assessments=validated,
        validation_results=body["validation_results"],
        output_checksum_sha256=canonical_checksum(body),
    )
