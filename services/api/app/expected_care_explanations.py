"""Role-filtered, schema-constrained explanations of deterministic facts."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import CurrentUser, DbSession
from app.errors import ApiError
from app.expected_care_comparison import (
    _checksum,
    payer_scope,
)
from app.expected_care_review import _doctor_scope
from app.expected_care_release_operations import (
    early_stage_waivers_ready,
    effective_active_release_id,
)
from app.models import (
    ExpectedCareClinicianRationale,
    ExpectedCareClinicianResponse,
    ExpectedCareComparison,
    ExpectedCareExplanationArtifact,
    ExpectedCareExplanationAttempt,
    ExpectedCareExplanationRelease,
    ExpectedCareExplanationRequest,
    ExpectedCarePublishedBaseline,
    PatientProfile,
    PayerRequest,
    PayerReview,
    UserRole,
)
from app.provider_transport import OpenAICompatibleJsonTransport, ProviderTransportError

router = APIRouter(prefix="/api/v1", tags=["expected-care explanations"])

PURPOSE_CODE = "expected_care_role_explanation"
PURPOSE_CONTRACT_VERSION = "expected-care-role-explanation-purpose.v2"
OUTPUT_SCHEMA_VERSION = "expected-care-role-explanation-claim-graph.v2"
PROMPT_VERSION = "expected-care-role-explanation-prompt.v3"
MODEL_CONFIGURATION_VERSION = "expected-care-role-explanation-deepseek.v1"
RELEASE_KEY = "expected-care-role-explanation"
DISCLAIMER_CODE = "validated_facts_explanation_not_decision_v1"
_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,119}$")
_UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)
_EMAIL = re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?%?")
_PROHIBITED = (
    "fraud",
    "fraudulent",
    "misconduct",
    "overtreatment",
    "undertreatment",
    "medically necessary",
    "not medically necessary",
    "coverage approved",
    "coverage denied",
    "reimbursement approved",
    "reimbursement denied",
    "must pay",
    "patient owes",
    "diagnosis is",
    "should take",
    "欺诈",
    "不当行为",
    "过度治疗",
    "治疗不足",
    "医学必需",
    "拒赔",
    "核赔通过",
    "患者应付",
    "诊断为",
    "应服用",
)
_EXPLANATION_SOURCE = Path(__file__).resolve()
_COMPARISON_SOURCE = _EXPLANATION_SOURCE.with_name("expected_care_comparison.py")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


ExplanationSection = Literal[
    "plain_language_range",
    "baseline_represents",
    "comparison_summary",
    "assumptions_and_missing_information",
    "uncertainty_and_limitations",
    "clinician_response_summary",
    "responsible_next_action",
]
ClaimType = Literal[
    "range_facts",
    "baseline_facts",
    "comparison_facts",
    "assumption_or_missing_facts",
    "limitation_facts",
    "clinician_response_facts",
    "responsible_next_action_fact",
]
Connective = Literal["neutral", "uncertainty", "human_review"]


class CanonicalClaimSelection(_StrictModel):
    """Provider-selected references only; protected values never enter model prose."""

    section: ExplanationSection
    claim_type: ClaimType
    fact_ids: Annotated[list[str], Field(min_length=1, max_length=40)]
    connective: Connective


class ExpectedCareExplanationOutput(_StrictModel):
    purpose_code: Literal["expected_care_role_explanation"]
    purpose_contract_version: Literal["expected-care-role-explanation-purpose.v2"]
    schema_version: Literal["expected-care-role-explanation-claim-graph.v2"]
    fact_object_checksum_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    disclaimer_code: Literal["validated_facts_explanation_not_decision_v1"]
    claims: Annotated[list[CanonicalClaimSelection], Field(min_length=7, max_length=7)]


class ExplanationInput(_StrictModel):
    locale: Literal["en", "zh-Hans"] = "en"


@dataclass(frozen=True)
class ProviderExplanationResponse:
    output: object
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_microunits: int | None


class ExplanationProviderError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class ExplanationProvider(Protocol):
    def generate(
        self,
        *,
        fact_object: dict[str, object],
        output_schema: dict[str, object],
        settings: Settings,
    ) -> ProviderExplanationResponse: ...


class DeepSeekExplanationProvider:
    """DeepSeek transport isolated to the explanation purpose."""

    def __init__(self, transport: OpenAICompatibleJsonTransport | None = None) -> None:
        self.transport = transport or OpenAICompatibleJsonTransport()

    def generate(
        self,
        *,
        fact_object: dict[str, object],
        output_schema: dict[str, object],
        settings: Settings,
    ) -> ProviderExplanationResponse:
        if settings.deepseek_api_key is None:
            raise ExplanationProviderError("provider_key_missing", retryable=False)
        request_body = {
            "model": settings.expected_care_explanation_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return one JSON object matching the schema. You are selecting a "
                        "canonical claim plan, not writing prose. Return exactly one claim "
                        "for each of the seven sections. Select only exact fact_id values "
                        "from the facts array, the section-compatible claim_type, and one "
                        "allowed connective. Never copy, spell, translate, summarize, or "
                        "invent a fact value. The server alone renders protected currencies, "
                        "minor-unit amounts, quantities, units, dates, percentages, codes, "
                        "comparison labels, source/effective dates, names, and identifiers "
                        "into English and Simplified Chinese from the same claim graph. Do "
                        "not calculate, infer, diagnose, recommend treatment, judge clinical "
                        "necessity or clinician quality, infer coverage or reimbursement, "
                        "allege misconduct or fraud, or change workflow state. When a section "
                        "has no positive fact, select its explicit *.none fact. Never cite "
                        "top-level metadata."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"role_filtered_facts": fact_object, "json_schema": output_schema},
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
            "temperature": 0.0,
            "max_tokens": settings.expected_care_explanation_max_output_tokens,
        }
        try:
            response = self.transport.request(
                endpoint=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key.get_secret_value(),
                request_body=request_body,
                timeout_seconds=settings.expected_care_explanation_timeout_seconds,
            ).payload
        except ProviderTransportError as exc:
            raise ExplanationProviderError(
                exc.code,
                retryable=exc.code in {"timeout", "malformed_envelope"},
            ) from exc
        try:
            content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            if not isinstance(content, str):
                raise TypeError
            output = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ExplanationProviderError("malformed_output", retryable=True) from exc
        usage = response.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        return ProviderExplanationResponse(
            output=output,
            provider=settings.expected_care_explanation_provider,
            model=str(response.get("model") or settings.expected_care_explanation_model),
            input_tokens=int(input_tokens) if isinstance(input_tokens, int) else None,
            output_tokens=int(output_tokens) if isinstance(output_tokens, int) else None,
            cost_microunits=(
                round(
                    int(input_tokens or 0) * settings.deepseek_input_price_per_million_usd
                    + int(output_tokens or 0) * settings.deepseek_output_price_per_million_usd
                )
                if usage
                else None
            ),
        )


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def _conflict(message: str) -> ApiError:
    return ApiError(409, "conflict", message)


def _add_fact(
    facts: list[dict[str, object]],
    *,
    fact_id: str,
    category: str,
    label: str,
    value: object,
    provenance: str,
) -> None:
    facts.append(
        {
            "fact_id": fact_id,
            "category": category,
            "label": label,
            "value": value,
            "provenance": provenance,
        }
    )


def build_role_fact_object(
    db: Session,
    *,
    comparison: ExpectedCareComparison,
    role: Literal["doctor", "patient", "payer"],
) -> dict[str, object]:
    baseline = db.get(ExpectedCarePublishedBaseline, comparison.baseline_id)
    if (
        baseline is None
        or baseline.patient_id != comparison.patient_id
        or baseline.clinical_event_id != comparison.clinical_event_id
        or baseline.payer_request_id != comparison.payer_request_id
        or comparison.input_snapshot_checksum_sha256 != _checksum(comparison.input_snapshot_json)
        or comparison.result_checksum_sha256 != _checksum(comparison.result_json)
    ):
        raise _conflict("The comparison lineage is stale or checksum-drifted.")
    facts: list[dict[str, object]] = []
    source = f"baseline_version:{baseline.version}"
    for fact_id, label, value in (
        ("baseline.currency", "Currency", baseline.currency),
        ("baseline.amount_type", "Amount type", baseline.amount_type),
        (
            "baseline.total_low_minor",
            "Baseline low amount in minor units",
            baseline.total_low_minor,
        ),
        (
            "baseline.total_high_minor",
            "Baseline high amount in minor units",
            baseline.total_high_minor,
        ),
        (
            "comparison.delivered_total_label",
            "Delivered comparison label",
            comparison.delivered_total_label,
        ),
        (
            "comparison.disclaimer_boundary",
            "Interpretation boundary",
            comparison.result_json["interpretation_boundary"],
        ),
    ):
        _add_fact(
            facts,
            fact_id=fact_id,
            category="baseline" if fact_id.startswith("baseline") else "comparison",
            label=label,
            value=value,
            provenance=(
                source
                if fact_id.startswith("baseline")
                else f"comparison_version:{comparison.version}"
            ),
        )
    for index, lineage in enumerate(baseline.release_lineage_json):
        if not isinstance(lineage, dict):
            continue
        _add_fact(
            facts,
            fact_id=f"baseline.reference.{index + 1}",
            category="reference",
            label="Synthetic reference release and effective dates",
            value={
                key: lineage.get(key)
                for key in (
                    "release_type",
                    "version",
                    "effective_from",
                    "effective_to",
                    "reference_date",
                    "source_authority",
                    "payload_checksum_sha256",
                )
                if lineage.get(key) is not None
            },
            provenance=source,
        )
    if comparison.delivered_total_minor is not None:
        _add_fact(
            facts,
            fact_id="comparison.delivered_total_minor",
            category="delivered",
            label="Delivered total in minor units",
            value=comparison.delivered_total_minor,
            provenance=f"comparison_version:{comparison.version}",
        )
    if role in {"doctor", "payer"} and comparison.submitted_total_label is not None:
        _add_fact(
            facts,
            fact_id="comparison.submitted_total_label",
            category="submitted",
            label="Submitted comparison label",
            value=comparison.submitted_total_label,
            provenance=f"comparison_version:{comparison.version}",
        )
        if comparison.submitted_total_minor is not None:
            _add_fact(
                facts,
                fact_id="comparison.submitted_total_minor",
                category="submitted",
                label="Submitted total in minor units",
                value=comparison.submitted_total_minor,
                provenance=f"comparison_version:{comparison.version}",
            )
    for index, value in enumerate(baseline.assumptions_json):
        _add_fact(
            facts,
            fact_id=f"baseline.assumption.{index + 1}",
            category="assumption",
            label="Baseline assumption",
            value=value,
            provenance=source,
        )
    if not baseline.assumptions_json:
        _add_fact(
            facts,
            fact_id="baseline.assumption.none",
            category="assumption",
            label="Baseline assumption state",
            value="none_recorded",
            provenance=source,
        )
    for index, value in enumerate(baseline.missing_information_json):
        _add_fact(
            facts,
            fact_id=f"baseline.missing.{index + 1}",
            category="missing_information",
            label="Missing information",
            value=value,
            provenance=source,
        )
    if not baseline.missing_information_json:
        _add_fact(
            facts,
            fact_id="baseline.missing.none",
            category="missing_information",
            label="Missing information state",
            value="none_recorded",
            provenance=source,
        )
    for index, value in enumerate(baseline.limitations_json):
        _add_fact(
            facts,
            fact_id=f"baseline.limitation.{index + 1}",
            category="limitation",
            label="Baseline limitation",
            value=value,
            provenance=source,
        )
    if not baseline.limitations_json:
        _add_fact(
            facts,
            fact_id="baseline.limitation.none",
            category="limitation",
            label="Baseline limitation state",
            value="none_recorded",
            provenance=source,
        )
    for index, item in enumerate(comparison.result_json.get("items", [])):
        if not isinstance(item, dict):
            continue
        safe_item = {
            "item_key": item.get("item_key"),
            "unit": item.get("unit"),
            "baseline_quantity_low": item.get("baseline_quantity_low"),
            "baseline_quantity_high": item.get("baseline_quantity_high"),
            "baseline_amount_low_minor": item.get("baseline_amount_low_minor"),
            "baseline_amount_high_minor": item.get("baseline_amount_high_minor"),
            "delivered_quantity": item.get("delivered_quantity"),
            "delivered_amount_minor": item.get("delivered_amount_minor"),
            "delivered_label": item.get("delivered_label"),
        }
        if role in {"doctor", "payer"}:
            safe_item["service_code"] = item.get("service_code")
            safe_item["submitted_amount_minor"] = item.get("submitted_amount_minor")
            safe_item["submitted_label"] = item.get("submitted_label")
        _add_fact(
            facts,
            fact_id=f"comparison.item.{index + 1}",
            category="comparison_item",
            label="Deterministic line comparison",
            value=safe_item,
            provenance=f"comparison_version:{comparison.version}",
        )
    responses = db.scalars(
        select(ExpectedCareClinicianResponse)
        .where(ExpectedCareClinicianResponse.baseline_id == baseline.id)
        .order_by(ExpectedCareClinicianResponse.resulting_head_version)
    ).all()
    for index, response in enumerate(responses):
        value: dict[str, object] = {
            "position": response.action,
            "response_version": response.resulting_head_version,
        }
        rationale = db.scalar(
            select(ExpectedCareClinicianRationale).where(
                ExpectedCareClinicianRationale.clinician_response_id == response.id
            )
        )
        if rationale is not None:
            if role in {"doctor", "payer"}:
                value["exception_code"] = rationale.exception_code
                value["rationale"] = rationale.rationale
            if rationale.patient_safe_summary:
                value["patient_safe_summary"] = rationale.patient_safe_summary
        if role == "doctor" and response.reviewer_only_note:
            value["reviewer_only_note"] = response.reviewer_only_note
        _add_fact(
            facts,
            fact_id=f"clinician.response.{index + 1}",
            category="clinician_response",
            label="Attributable clinician response",
            value=value,
            provenance=f"clinician_response_version:{response.resulting_head_version}",
        )
    if not responses:
        _add_fact(
            facts,
            fact_id="clinician.response.none",
            category="clinician_response",
            label="Clinician response state",
            value="not_recorded",
            provenance=source,
        )
    if role == "payer" and comparison.payer_request_id is not None:
        request = db.get(PayerRequest, comparison.payer_request_id)
        if request is None:
            raise _conflict("The payer request is no longer available.")
        reviews = db.scalars(
            select(PayerReview)
            .where(PayerReview.payer_request_id == request.id)
            .order_by(PayerReview.created_at)
        ).all()
        _add_fact(
            facts,
            fact_id="payer.human_state",
            category="human_payer_state",
            label="Human payer workflow state",
            value={
                "request_status": request.status,
                "review_actions": [row.action for row in reviews],
            },
            provenance="immutable_payer_request_scope",
        )
    _add_fact(
        facts,
        fact_id="policy.next_action",
        category="fixed_policy",
        label="Responsible next action",
        value=(
            "Review the structured baseline, comparison, missing information, and any "
            "clinician response with the responsible human party."
        ),
        provenance=PURPOSE_CONTRACT_VERSION,
    )
    fact_object = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "role": role,
        "facts": facts,
    }
    fact_object["fact_object_checksum_sha256"] = _checksum(fact_object)
    return fact_object


_SECTION_CLAIM_TYPES: dict[str, str] = {
    "plain_language_range": "range_facts",
    "baseline_represents": "baseline_facts",
    "comparison_summary": "comparison_facts",
    "assumptions_and_missing_information": "assumption_or_missing_facts",
    "uncertainty_and_limitations": "limitation_facts",
    "clinician_response_summary": "clinician_response_facts",
    "responsible_next_action": "responsible_next_action_fact",
}
_CLAIM_CATEGORIES: dict[str, frozenset[str]] = {
    "range_facts": frozenset({"baseline", "reference"}),
    "baseline_facts": frozenset({"baseline", "reference"}),
    "comparison_facts": frozenset({"comparison", "comparison_item", "delivered", "submitted"}),
    "assumption_or_missing_facts": frozenset({"assumption", "missing_information"}),
    "limitation_facts": frozenset({"limitation"}),
    "clinician_response_facts": frozenset({"clinician_response"}),
    "responsible_next_action_fact": frozenset({"fixed_policy"}),
}
_INJECTION = re.compile(
    r"(ignore (?:all |the )?(?:previous|prior|system)(?: system)? instructions|"
    r"system prompt|developer message|jailbreak|越狱|忽略(?:之前|以上).{0,12}(?:指令|提示))",
    re.IGNORECASE,
)
_SENSITIVE_KEYS = frozenset(
    {
        "email",
        "reviewer_only_note",
        "confidential_identifier",
        "internal_code",
        "patient_id",
        "doctor_id",
        "payer_membership_id",
    }
)
_ZH_LABELS = {
    "Currency": "币种",
    "Amount type": "金额类型",
    "Baseline low amount in minor units": "基线最低金额（最小货币单位）",
    "Baseline high amount in minor units": "基线最高金额（最小货币单位）",
    "Delivered comparison label": "已提供服务比较标签",
    "Submitted comparison label": "已提交金额比较标签",
    "Delivered total in minor units": "已提供服务总额（最小货币单位）",
    "Submitted total in minor units": "已提交总额（最小货币单位）",
    "Interpretation boundary": "解释边界",
    "Baseline assumption": "基线假设",
    "Baseline assumption state": "基线假设状态",
    "Missing information": "缺失信息",
    "Missing information state": "缺失信息状态",
    "Baseline limitation": "基线局限",
    "Baseline limitation state": "基线局限状态",
    "Deterministic line comparison": "确定性明细比较",
    "Attributable clinician response": "可追溯的临床人员回应",
    "Clinician response state": "临床人员回应状态",
    "Human payer workflow state": "人工支付方流程状态",
    "Responsible next action": "负责任的下一步",
    "Synthetic reference release and effective dates": "合成参考发布及生效日期",
}
_CONNECTIVE_TEXT = {
    "en": {
        "neutral": "The admitted structured facts are",
        "uncertainty": "The admitted facts retain this uncertainty",
        "human_review": "For responsible human review, the admitted facts are",
    },
    "zh_hans": {
        "neutral": "准入的结构化事实为",
        "uncertainty": "准入事实保留以下不确定性",
        "human_review": "供负责任的人工复核，准入事实为",
    },
}


def _sensitive_value(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in _SENSITIVE_KEYS or _sensitive_value(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_sensitive_value(item) for item in value)
    if isinstance(value, str):
        return bool(_UUID.search(value) or _EMAIL.search(value) or _INJECTION.search(value))
    return False


def _canonical_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def render_claim_graph(
    output: ExpectedCareExplanationOutput,
    *,
    fact_object: dict[str, object],
) -> dict[str, object]:
    """Render both languages from one validated graph; the provider writes no prose."""

    facts = {
        str(item["fact_id"]): item
        for item in fact_object["facts"]  # type: ignore[union-attr]
        if isinstance(item, dict) and "fact_id" in item
    }
    localized: dict[str, dict[str, object]] = {"en": {}, "zh_hans": {}}
    for claim in output.claims:
        for locale in ("en", "zh_hans"):
            rendered_facts = []
            for fact_id in claim.fact_ids:
                fact = facts[fact_id]
                label = str(fact["label"])
                if locale == "zh_hans":
                    label = _ZH_LABELS.get(label, label)
                rendered_facts.append(f"{label}: {_canonical_value(fact['value'])}")
            terminator = "." if locale == "en" else "。"
            localized[locale][claim.section] = {
                "text": (
                    f"{_CONNECTIVE_TEXT[locale][claim.connective]}: "
                    + "; ".join(rendered_facts)
                    + terminator
                ),
                "fact_ids": claim.fact_ids,
                "claim_type": claim.claim_type,
                "connective": claim.connective,
            }
    return {
        "display_mode": "validated_canonical_explanation",
        "role": fact_object["role"],
        "state": "validated",
        "fact_object_checksum_sha256": fact_object["fact_object_checksum_sha256"],
        "disclaimer_code": output.disclaimer_code,
        "claim_graph": [claim.model_dump(mode="json") for claim in output.claims],
        **localized,
    }


def validate_rendered_claim_graph(
    artifact: object,
    *,
    output: ExpectedCareExplanationOutput,
    fact_object: dict[str, object],
) -> bool:
    """Exact reconstruction makes any protected-value or bilingual mutation fail."""

    return artifact == render_claim_graph(output, fact_object=fact_object)


def validate_explanation(
    output: object, *, fact_object: dict[str, object]
) -> tuple[ExpectedCareExplanationOutput | None, dict[str, object]]:
    reasons: list[str] = []
    try:
        parsed = ExpectedCareExplanationOutput.model_validate(output)
    except ValidationError:
        return None, {"state": "rejected", "reason_codes": ["schema_invalid"]}
    if parsed.fact_object_checksum_sha256 != fact_object["fact_object_checksum_sha256"]:
        reasons.append("fact_checksum_mismatch")
    facts = {
        str(item["fact_id"]): item
        for item in fact_object["facts"]  # type: ignore[union-attr]
        if isinstance(item, dict) and "fact_id" in item
    }
    seen_sections: set[str] = set()
    for claim in parsed.claims:
        if claim.section in seen_sections:
            reasons.append("duplicate_section")
        seen_sections.add(claim.section)
        if _SECTION_CLAIM_TYPES.get(claim.section) != claim.claim_type:
            reasons.append("claim_type_section_mismatch")
        missing = sorted(set(claim.fact_ids) - facts.keys())
        if missing:
            reasons.append("unknown_fact_id")
        if len(claim.fact_ids) != len(set(claim.fact_ids)):
            reasons.append("duplicate_fact_id")
        admitted = [facts[fact_id] for fact_id in claim.fact_ids if fact_id in facts]
        if any(
            str(fact.get("category")) not in _CLAIM_CATEGORIES[claim.claim_type]
            for fact in admitted
        ):
            reasons.append("fact_category_mismatch")
        if any(_sensitive_value(fact.get("value")) for fact in admitted):
            reasons.append("unauthorized_identifier_or_prompt_injection")
    if seen_sections != set(_SECTION_CLAIM_TYPES):
        reasons.append("missing_section")
    state = "validated" if not reasons else "rejected"
    validation = {
        "state": state,
        "reason_codes": sorted(set(reasons)),
        "schema_exact": "schema_invalid" not in reasons,
        "fact_ids_valid": "unknown_fact_id" not in reasons,
        "protected_values_server_rendered": not reasons,
        "numbers_exact": not reasons,
        "bilingual_fact_references_equivalent": not reasons,
        "bilingual_rendered_from_same_claim_graph": not reasons,
        "role_visibility_rechecked": True,
        "deterministic_validation_wins": True,
    }
    return (parsed if not reasons else None), validation


def fixed_fallback(
    *, fact_object: dict[str, object], role: str, reason_code: str
) -> dict[str, object]:
    safe_facts = [
        item
        for item in fact_object["facts"]  # type: ignore[union-attr]
        if isinstance(item, dict)
    ]
    return {
        "display_mode": "structured_fallback",
        "role": role,
        "state": "explanation_unavailable",
        "reason_code": reason_code,
        "facts": safe_facts,
        "en": {
            "title": "Validated structured facts",
            "message": (
                "The AI explanation is unavailable. The immutable baseline and "
                "deterministic comparison remain available."
            ),
        },
        "zh_hans": {
            "title": "已验证的结构化事实",
            "message": "AI 解释暂不可用。不可变基线和确定性比较仍然可见。",
        },
        "disclaimer_code": DISCLAIMER_CODE,
    }


def _active_release(db: Session, settings: Settings) -> ExpectedCareExplanationRelease | None:
    active_id = effective_active_release_id(db, RELEASE_KEY)
    release = db.get(ExpectedCareExplanationRelease, active_id) if active_id else None
    if release is None:
        return None
    runtime_checksums = {
        "explanation_source_sha256": sha256(_EXPLANATION_SOURCE.read_bytes()).hexdigest(),
        "comparison_source_sha256": sha256(_COMPARISON_SOURCE.read_bytes()).hexdigest(),
        "output_schema_sha256": _checksum(ExpectedCareExplanationOutput.model_json_schema()),
    }
    if (
        release.purpose_code != PURPOSE_CODE
        or release.purpose_contract_version != PURPOSE_CONTRACT_VERSION
        or release.schema_version != OUTPUT_SCHEMA_VERSION
        or release.prompt_version != PROMPT_VERSION
        or release.model_configuration_version != MODEL_CONFIGURATION_VERSION
        or release.provider != "deepseek"
        or release.model != settings.expected_care_explanation_model
        or not early_stage_waivers_ready(db, release)
        or not all(value is True for value in release.machine_gates_json.values())
        or any(
            release.source_checksums_json.get(key) != value
            for key, value in runtime_checksums.items()
        )
    ):
        return None
    return release


def explanation_release_ready(db: Session, settings: Settings) -> bool:
    """Return a content-free readiness decision using the runtime activation gate."""

    return _active_release(db, settings) is not None


def generate_explanation(
    db: Session,
    *,
    actor_user_id: uuid.UUID,
    comparison: ExpectedCareComparison,
    role: Literal["doctor", "patient", "payer"],
    locale: Literal["en", "zh-Hans"],
    idempotency_key: str,
    settings: Settings,
    provider: ExplanationProvider | None = None,
    allow_synthetic_unreleased: bool = False,
) -> tuple[ExpectedCareExplanationRequest, ExpectedCareExplanationArtifact, bool]:
    if not _KEY.fullmatch(idempotency_key):
        raise ApiError(422, "validation_failed", "The idempotency key is invalid.")
    fact_object = build_role_fact_object(db, comparison=comparison, role=role)
    request_content = {
        "comparison_id": str(comparison.id),
        "role": role,
        "locale": locale,
        "fact_object_checksum_sha256": fact_object["fact_object_checksum_sha256"],
    }
    request_checksum = _checksum(request_content)
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"expected-care-explanation:{comparison.id}:{role}:{idempotency_key}"},
    )
    existing = db.scalar(
        select(ExpectedCareExplanationRequest).where(
            ExpectedCareExplanationRequest.actor_user_id == actor_user_id,
            ExpectedCareExplanationRequest.comparison_id == comparison.id,
            ExpectedCareExplanationRequest.role == role,
            ExpectedCareExplanationRequest.locale == locale,
            ExpectedCareExplanationRequest.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.request_checksum_sha256 != request_checksum:
            raise _conflict("The idempotency key was already used with different content.")
        artifact = db.scalar(
            select(ExpectedCareExplanationArtifact).where(
                ExpectedCareExplanationArtifact.explanation_request_id == existing.id
            )
        )
        if artifact is None:
            raise _conflict("The explanation request is still being processed.")
        return existing, artifact, True

    release = _active_release(db, settings)
    generation_allowed = (
        settings.expected_care_explanation_enabled
        and not settings.expected_care_explanation_kill_switch
        and (release is not None or allow_synthetic_unreleased)
    )
    request = ExpectedCareExplanationRequest(
        comparison_id=comparison.id,
        actor_user_id=actor_user_id,
        patient_id=comparison.patient_id,
        clinical_event_id=comparison.clinical_event_id,
        payer_request_id=comparison.payer_request_id,
        role=role,
        locale=locale,
        idempotency_key=idempotency_key,
        request_checksum_sha256=request_checksum,
        fact_object_checksum_sha256=str(fact_object["fact_object_checksum_sha256"]),
        fact_object_json=fact_object,
        purpose_code=PURPOSE_CODE,
        purpose_contract_version=PURPOSE_CONTRACT_VERSION,
        schema_version=OUTPUT_SCHEMA_VERSION,
        prompt_version=PROMPT_VERSION,
        model_configuration_version=MODEL_CONFIGURATION_VERSION,
        provider="deepseek",
        model=settings.expected_care_explanation_model,
        lifecycle_state="requested",
    )
    db.add(request)
    db.flush()
    config_lineage = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "provider": "deepseek",
        "model": settings.expected_care_explanation_model,
        "release_id": str(release.id) if release else None,
    }
    if not generation_allowed:
        validation = {
            "state": "unavailable",
            "reason_codes": ["kill_switch_or_release_gate"],
            "deterministic_validation_wins": True,
        }
        display = fixed_fallback(
            fact_object=fact_object,
            role=role,
            reason_code="kill_switch_or_release_gate",
        )
        artifact = ExpectedCareExplanationArtifact(
            explanation_request_id=request.id,
            lifecycle_state="explanation_unavailable",
            display_mode="structured_fallback",
            generated_artifact_checksum_sha256=None,
            validation_checksum_sha256=_checksum(validation),
            configuration_lineage_checksum_sha256=_checksum(config_lineage),
            validation_json=validation,
            display_artifact_json=display,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return request, artifact, False

    active_provider = provider or DeepSeekExplanationProvider()
    last_reason = "provider_unavailable"
    for attempt_number in range(1, settings.expected_care_explanation_max_attempts + 1):
        started = time.perf_counter()
        try:
            response = active_provider.generate(
                fact_object=fact_object,
                output_schema=ExpectedCareExplanationOutput.model_json_schema(),
                settings=settings,
            )
            latency_ms = round((time.perf_counter() - started) * 1000)
            parsed, validation = validate_explanation(response.output, fact_object=fact_object)
            generated_checksum = _checksum(response.output)
            if parsed is not None:
                display = render_claim_graph(parsed, fact_object=fact_object)
                if not validate_rendered_claim_graph(
                    display,
                    output=parsed,
                    fact_object=fact_object,
                ):
                    raise RuntimeError("canonical explanation rendering drifted")
                db.add(
                    ExpectedCareExplanationAttempt(
                        explanation_request_id=request.id,
                        attempt_number=attempt_number,
                        outcome="validated",
                        diagnostic_code=None,
                        latency_ms=latency_ms,
                        input_tokens=response.input_tokens,
                        output_tokens=response.output_tokens,
                        cost_microunits=response.cost_microunits,
                        artifact_checksum_sha256=generated_checksum,
                    )
                )
                artifact = ExpectedCareExplanationArtifact(
                    explanation_request_id=request.id,
                    lifecycle_state="validated_displayable",
                    display_mode="validated_canonical_explanation",
                    generated_artifact_checksum_sha256=generated_checksum,
                    validation_checksum_sha256=_checksum(validation),
                    configuration_lineage_checksum_sha256=_checksum(config_lineage),
                    validation_json=validation,
                    display_artifact_json=display,
                )
                db.add(artifact)
                db.commit()
                db.refresh(artifact)
                return request, artifact, False
            last_reason = str(validation["reason_codes"][0])
            db.add(
                ExpectedCareExplanationAttempt(
                    explanation_request_id=request.id,
                    attempt_number=attempt_number,
                    outcome="rejected",
                    diagnostic_code=last_reason,
                    latency_ms=latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost_microunits=response.cost_microunits,
                    artifact_checksum_sha256=generated_checksum,
                )
            )
            if attempt_number < settings.expected_care_explanation_max_attempts:
                continue
        except ExplanationProviderError as exc:
            last_reason = exc.code
            db.add(
                ExpectedCareExplanationAttempt(
                    explanation_request_id=request.id,
                    attempt_number=attempt_number,
                    outcome="provider_error",
                    diagnostic_code=exc.code,
                    latency_ms=round((time.perf_counter() - started) * 1000),
                    input_tokens=None,
                    output_tokens=None,
                    cost_microunits=None,
                    artifact_checksum_sha256=None,
                )
            )
            if exc.retryable and attempt_number < settings.expected_care_explanation_max_attempts:
                continue
            break
    validation = {
        "state": "rejected",
        "reason_codes": [last_reason],
        "deterministic_validation_wins": True,
    }
    display = fixed_fallback(fact_object=fact_object, role=role, reason_code=last_reason)
    artifact = ExpectedCareExplanationArtifact(
        explanation_request_id=request.id,
        lifecycle_state="rejected_structured_fallback",
        display_mode="structured_fallback",
        generated_artifact_checksum_sha256=None,
        validation_checksum_sha256=_checksum(validation),
        configuration_lineage_checksum_sha256=_checksum(config_lineage),
        validation_json=validation,
        display_artifact_json=display,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return request, artifact, False


def explanation_payload(
    request: ExpectedCareExplanationRequest,
    artifact: ExpectedCareExplanationArtifact,
    *,
    replay: bool = False,
) -> dict[str, object]:
    return {
        "explanation_id": artifact.id,
        "comparison_id": request.comparison_id,
        "role": request.role,
        "locale": request.locale,
        "state": artifact.lifecycle_state,
        "display_mode": artifact.display_mode,
        "artifact": artifact.display_artifact_json,
        "validation": artifact.validation_json,
        "created_at": artifact.created_at,
        "idempotent_replay": replay,
    }


def _comparison(
    db: Session,
    *,
    comparison_id: uuid.UUID,
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    payer_request_id: uuid.UUID | None = None,
) -> ExpectedCareComparison:
    query = select(ExpectedCareComparison).where(
        ExpectedCareComparison.id == comparison_id,
        ExpectedCareComparison.patient_id == patient_id,
        ExpectedCareComparison.clinical_event_id == event_id,
    )
    if payer_request_id is not None:
        query = query.where(ExpectedCareComparison.payer_request_id == payer_request_id)
    comparison = db.scalar(query)
    if comparison is None:
        raise _not_found()
    return comparison


def _latest_artifact(
    db: Session,
    *,
    comparison: ExpectedCareComparison,
    role: str,
) -> tuple[ExpectedCareExplanationRequest, ExpectedCareExplanationArtifact]:
    request = db.scalar(
        select(ExpectedCareExplanationRequest)
        .where(
            ExpectedCareExplanationRequest.comparison_id == comparison.id,
            ExpectedCareExplanationRequest.role == role,
        )
        .order_by(ExpectedCareExplanationRequest.created_at.desc())
    )
    artifact = (
        db.scalar(
            select(ExpectedCareExplanationArtifact).where(
                ExpectedCareExplanationArtifact.explanation_request_id == request.id
            )
        )
        if request is not None
        else None
    )
    if request is None or artifact is None:
        raise _not_found()
    return request, artifact


def _artifact_history(
    db: Session,
    *,
    comparison: ExpectedCareComparison,
    role: str,
    limit: int,
) -> list[dict[str, object]]:
    rows = db.execute(
        select(ExpectedCareExplanationRequest, ExpectedCareExplanationArtifact)
        .join(
            ExpectedCareExplanationArtifact,
            ExpectedCareExplanationArtifact.explanation_request_id
            == ExpectedCareExplanationRequest.id,
        )
        .where(
            ExpectedCareExplanationRequest.comparison_id == comparison.id,
            ExpectedCareExplanationRequest.role == role,
        )
        .order_by(ExpectedCareExplanationRequest.created_at.desc())
        .limit(limit)
    ).all()
    return [explanation_payload(request, artifact) for request, artifact in rows]


@router.post(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/"
    "{comparison_id}/explanations"
)
def doctor_generate_explanation(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    payload: ExplanationInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    comparison = db.scalar(
        select(ExpectedCareComparison).where(
            ExpectedCareComparison.id == comparison_id,
            ExpectedCareComparison.patient_id == patient_id,
            ExpectedCareComparison.clinical_event_id == event_id,
        )
    )
    if comparison is None:
        raise _not_found()
    request, artifact, replay = generate_explanation(
        db,
        actor_user_id=user.id,
        comparison=comparison,
        role="doctor",
        locale=payload.locale,
        idempotency_key=idempotency_key,
        settings=get_settings(),
    )
    return explanation_payload(request, artifact, replay=replay)


@router.get(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/"
    "{comparison_id}/explanations/latest"
)
def doctor_latest_explanation(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    comparison = db.scalar(
        select(ExpectedCareComparison).where(
            ExpectedCareComparison.id == comparison_id,
            ExpectedCareComparison.patient_id == patient_id,
            ExpectedCareComparison.clinical_event_id == event_id,
        )
    )
    if comparison is None:
        raise _not_found()
    request, artifact = _latest_artifact(db, comparison=comparison, role="doctor")
    return explanation_payload(request, artifact)


@router.get(
    "/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/"
    "{comparison_id}/explanations/history"
)
def doctor_explanation_history(
    patient_id: uuid.UUID,
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    if user.role != UserRole.doctor:
        raise _not_found()
    _doctor_scope(db, user_id=user.id, patient_id=patient_id, event_id=event_id)
    comparison = db.scalar(
        select(ExpectedCareComparison).where(
            ExpectedCareComparison.id == comparison_id,
            ExpectedCareComparison.patient_id == patient_id,
            ExpectedCareComparison.clinical_event_id == event_id,
        )
    )
    if comparison is None:
        raise _not_found()
    return {"items": _artifact_history(db, comparison=comparison, role="doctor", limit=limit)}


@router.post(
    "/patient/clinical-events/{event_id}/expected-care-comparisons/{comparison_id}/explanations"
)
def patient_generate_explanation(
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    payload: ExplanationInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    comparison = (
        _comparison(
            db,
            comparison_id=comparison_id,
            patient_id=patient.id,
            event_id=event_id,
        )
        if patient
        else None
    )
    if patient is None or comparison is None:
        raise _not_found()
    request, artifact, replay = generate_explanation(
        db,
        actor_user_id=user.id,
        comparison=comparison,
        role="patient",
        locale=payload.locale,
        idempotency_key=idempotency_key,
        settings=get_settings(),
    )
    return explanation_payload(request, artifact, replay=replay)


@router.get(
    "/patient/clinical-events/{event_id}/expected-care-comparisons/"
    "{comparison_id}/explanations/latest"
)
def patient_latest_explanation(
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    comparison = (
        _comparison(
            db,
            comparison_id=comparison_id,
            patient_id=patient.id,
            event_id=event_id,
        )
        if patient
        else None
    )
    if patient is None or comparison is None:
        raise _not_found()
    request, artifact = _latest_artifact(db, comparison=comparison, role="patient")
    return explanation_payload(request, artifact)


@router.get(
    "/patient/clinical-events/{event_id}/expected-care-comparisons/"
    "{comparison_id}/explanations/history"
)
def patient_explanation_history(
    event_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    if user.role != UserRole.patient:
        raise _not_found()
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    comparison = (
        _comparison(
            db,
            comparison_id=comparison_id,
            patient_id=patient.id,
            event_id=event_id,
        )
        if patient
        else None
    )
    if patient is None or comparison is None:
        raise _not_found()
    return {"items": _artifact_history(db, comparison=comparison, role="patient", limit=limit)}


@router.post(
    "/payer/requests/{payer_request_id}/expected-care-comparisons/{comparison_id}/explanations"
)
def payer_generate_explanation(
    payer_request_id: uuid.UUID,
    comparison_id: uuid.UUID,
    payload: ExplanationInput,
    db: DbSession,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, object]:
    if user.role != UserRole.payer:
        raise _not_found()
    _, request_scope, _ = payer_scope(db, user=user, payer_request_id=payer_request_id)
    comparison = _comparison(
        db,
        comparison_id=comparison_id,
        patient_id=request_scope.patient_id,
        event_id=request_scope.clinical_event_id,
        payer_request_id=payer_request_id,
    )
    request, artifact, replay = generate_explanation(
        db,
        actor_user_id=user.id,
        comparison=comparison,
        role="payer",
        locale=payload.locale,
        idempotency_key=idempotency_key,
        settings=get_settings(),
    )
    return explanation_payload(request, artifact, replay=replay)


@router.get(
    "/payer/requests/{payer_request_id}/expected-care-comparisons/"
    "{comparison_id}/explanations/latest"
)
def payer_latest_explanation(
    payer_request_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    if user.role != UserRole.payer:
        raise _not_found()
    _, request_scope, _ = payer_scope(db, user=user, payer_request_id=payer_request_id)
    comparison = _comparison(
        db,
        comparison_id=comparison_id,
        patient_id=request_scope.patient_id,
        event_id=request_scope.clinical_event_id,
        payer_request_id=payer_request_id,
    )
    request, artifact = _latest_artifact(db, comparison=comparison, role="payer")
    return explanation_payload(request, artifact)


@router.get(
    "/payer/requests/{payer_request_id}/expected-care-comparisons/"
    "{comparison_id}/explanations/history"
)
def payer_explanation_history(
    payer_request_id: uuid.UUID,
    comparison_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    if user.role != UserRole.payer:
        raise _not_found()
    _, request_scope, _ = payer_scope(db, user=user, payer_request_id=payer_request_id)
    comparison = _comparison(
        db,
        comparison_id=comparison_id,
        patient_id=request_scope.patient_id,
        event_id=request_scope.clinical_event_id,
        payer_request_id=payer_request_id,
    )
    return {"items": _artifact_history(db, comparison=comparison, role="payer", limit=limit)}
