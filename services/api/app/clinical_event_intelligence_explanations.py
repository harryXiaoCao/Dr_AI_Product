"""Role-filtered CEI fact objects and bounded explanation rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pydantic import ValidationError

from app.clinical_event_intelligence_contracts import (
    CEI_EXPLANATION_PURPOSE_CODE,
    RoleExplanationPlan,
    canonical_checksum,
)
from app.config import Settings
from app.provider_transport import OpenAICompatibleJsonTransport, ProviderTransportError

if TYPE_CHECKING:
    from app.clinical_event_intelligence_models import ClinicalEventIntelligenceArtifact


@dataclass(frozen=True)
class ExplanationResult:
    display_mode: str
    fact_object_checksum_sha256: str
    display: dict[str, object]
    validation: dict[str, object]


def build_role_fact_object(
    artifact: ClinicalEventIntelligenceArtifact,
    *,
    role: Literal["patient", "doctor", "payer"],
    locale: Literal["en", "zh-Hans"],
) -> dict[str, object]:
    payload = artifact.artifact_json
    facts: list[dict[str, object]] = [
        {"fact_id": "artifact.version", "value": artifact.artifact_version},
        {"fact_id": "artifact.lifecycle", "value": artifact.lifecycle_state},
        {"fact_id": "artifact.disagreement", "value": artifact.disagreement_state},
        {"fact_id": "policy.no_automatic_action", "value": True},
    ]
    for index, assessment in enumerate(payload.get("requested_item_assessments", []), 1):
        if not isinstance(assessment, dict):
            continue
        safe = {
            key: assessment.get(key)
            for key in (
                "ai_support_score",
                "score_band",
                "score_contract_version",
                "cost_alignment_weight_bp",
            )
        }
        proposal = assessment.get("proposal")
        if isinstance(proposal, dict):
            estimated_cost = proposal.get("estimated_cost")
            safe_estimated_cost = (
                {key: value for key, value in estimated_cost.items() if key != "source_ids"}
                if isinstance(estimated_cost, dict)
                else estimated_cost
            )
            safe.update(
                {
                    "requested_line_alias": f"requested_line_{index:03d}",
                    "usefulness": proposal.get("usefulness"),
                    "scores": proposal.get("scores"),
                    "estimated_quantity": proposal.get("estimated_quantity"),
                    "estimated_cost": safe_estimated_cost,
                    "missing_information": proposal.get("missing_information"),
                    "alternatives": proposal.get("alternatives"),
                    "confidence": proposal.get("confidence"),
                }
            )
            if role in {"doctor", "payer"}:
                safe["brief_comment"] = proposal.get("brief_comment")
            if role == "doctor":
                safe["supporting_fact_ids"] = proposal.get("supporting_fact_ids")
                safe["contradicting_fact_ids"] = proposal.get("contradicting_fact_ids")
                safe["mapped_pathway_ids"] = proposal.get("mapped_pathway_ids")
        facts.append({"fact_id": f"assessment.{index}", "value": safe})
    if role == "doctor":
        facts.append({"fact_id": "pathways", "value": payload.get("pathways", [])})
    snapshot = payload.get("snapshot")
    if isinstance(snapshot, dict):
        facts.append(
            {
                "fact_id": "snapshot.missing_information",
                "value": snapshot.get("missing_information", []),
            }
        )
    result = {
        "purpose_code": CEI_EXPLANATION_PURPOSE_CODE,
        "role": role,
        "locale": locale,
        "facts": facts,
    }
    result["fact_object_checksum_sha256"] = canonical_checksum(result)
    return result


def _render(fact_object: dict[str, object], selected_ids: list[str]) -> dict[str, object]:
    facts = {
        str(item["fact_id"]): item["value"]
        for item in fact_object["facts"]  # type: ignore[union-attr]
        if isinstance(item, dict) and "fact_id" in item and "value" in item
    }
    return {
        "locale": fact_object["locale"],
        "sections": [
            {"fact_id": fact_id, "value": facts[fact_id]}
            for fact_id in selected_ids
            if fact_id in facts
        ],
        "human_review_state": "required",
        "no_automatic_action": True,
    }


def generate_role_explanation(
    artifact: ClinicalEventIntelligenceArtifact,
    *,
    role: Literal["patient", "doctor", "payer"],
    locale: Literal["en", "zh-Hans"],
    settings: Settings,
    transport: OpenAICompatibleJsonTransport | None = None,
) -> ExplanationResult:
    facts = build_role_fact_object(artifact, role=role, locale=locale)
    checksum = str(facts["fact_object_checksum_sha256"])
    fallback_ids = [str(item["fact_id"]) for item in facts["facts"]]  # type: ignore[index]
    if (
        not settings.clinical_event_intelligence_explanation_enabled
        or settings.clinical_event_intelligence_explanation_kill_switch
        or settings.deepseek_api_key is None
    ):
        return ExplanationResult(
            display_mode="structured_fallback",
            fact_object_checksum_sha256=checksum,
            display=_render(facts, fallback_ids),
            validation={"valid": True, "reason_codes": ["purpose_unavailable"]},
        )
    body = {
        "model": settings.clinical_event_intelligence_explanation_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return one JSON object. Select only exact fact_id values for emphasis. "
                    "The requested display locale is included only as a selection context; "
                    "do not translate or rewrite protected facts. "
                    "Do not write prose, change "
                    "numbers, infer decisions, diagnose, approve, deny, or expose hidden data."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "role_filtered_facts": facts,
                        "json_schema": RoleExplanationPlan.model_json_schema(),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "temperature": 0.0,
        "stream": False,
        "max_tokens": settings.clinical_event_intelligence_explanation_max_output_tokens,
    }
    diagnostics: list[dict[str, object]] = []
    plan = None
    adapter = transport or OpenAICompatibleJsonTransport()
    for attempt_number in range(
        1, settings.clinical_event_intelligence_explanation_max_attempts + 1
    ):
        try:
            response = adapter.request(
                endpoint=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key.get_secret_value(),
                request_body=body,
                timeout_seconds=settings.clinical_event_intelligence_explanation_timeout_seconds,
            ).payload
            usage = response.get("usage")
            input_tokens = usage.get("prompt_tokens") if isinstance(usage, dict) else None
            output_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
            cost = round(
                int(input_tokens or 0)
                * settings.clinical_event_intelligence_explanation_input_price_per_million_usd
                + int(output_tokens or 0)
                * settings.clinical_event_intelligence_explanation_output_price_per_million_usd
            )
            diagnostics.append(
                {
                    "attempt_number": attempt_number,
                    "provider": settings.clinical_event_intelligence_explanation_provider,
                    "model": response.get("model"),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_microunits": cost,
                    "output_checksum_sha256": canonical_checksum(response.get("choices", [])),
                }
            )
            if cost > settings.clinical_event_intelligence_explanation_max_cost_microunits:
                raise ValueError("provider_budget_exceeded")
            if response.get("model") != settings.clinical_event_intelligence_explanation_model:
                raise ValueError("provider_model_drift")
            content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            candidate = RoleExplanationPlan.model_validate_json(content, strict=True)
            allowed = set(fallback_ids)
            if candidate.fact_object_checksum_sha256 != checksum or any(
                value not in allowed for value in candidate.selected_fact_ids
            ):
                raise ValueError("explanation_fact_drift")
            plan = candidate
            break
        except (
            ProviderTransportError,
            ValidationError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ):
            continue
    if plan is None:
        return ExplanationResult(
            display_mode="structured_fallback",
            fact_object_checksum_sha256=checksum,
            display=_render(facts, fallback_ids),
            validation={
                "valid": True,
                "reason_codes": ["provider_or_validation_failure"],
                "provider_diagnostics": diagnostics,
            },
        )
    return ExplanationResult(
        display_mode="validated_fact_selection",
        fact_object_checksum_sha256=checksum,
        display=_render(facts, plan.selected_fact_ids),
        validation={"valid": True, "reason_codes": [], "provider_diagnostics": diagnostics},
    )
