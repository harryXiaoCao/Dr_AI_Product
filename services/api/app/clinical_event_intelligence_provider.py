"""Purpose-separated DeepSeek adapters for primary and critic inference."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from app.clinical_event_intelligence_contracts import (
    CriticOutput,
    FrozenClinicalEventSnapshot,
    PrimaryIntelligenceOutput,
    RetrievalManifest,
    ValidatedIntelligence,
    canonical_checksum,
)
from app.config import Settings
from app.provider_transport import OpenAICompatibleJsonTransport, ProviderTransportError


class IntelligenceProviderError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class IntelligenceProviderResponse:
    output: object
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_microunits: int | None
    output_checksum_sha256: str


class PrimaryIntelligenceProvider(Protocol):
    def generate(
        self,
        *,
        snapshot: FrozenClinicalEventSnapshot,
        retrieval: RetrievalManifest,
        settings: Settings,
    ) -> IntelligenceProviderResponse: ...


class CriticIntelligenceProvider(Protocol):
    def review(
        self,
        *,
        snapshot: FrozenClinicalEventSnapshot,
        retrieval: RetrievalManifest,
        primary: ValidatedIntelligence,
        settings: Settings,
    ) -> IntelligenceProviderResponse: ...


def _usage(
    response: dict[str, object],
    *,
    input_price_per_million_usd: float,
    output_price_per_million_usd: float,
) -> tuple[int | None, int | None, int | None]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return None, None, None
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    input_value = int(input_tokens) if isinstance(input_tokens, int) else None
    output_value = int(output_tokens) if isinstance(output_tokens, int) else None
    cost = round(
        int(input_value or 0) * input_price_per_million_usd
        + int(output_value or 0) * output_price_per_million_usd
    )
    return input_value, output_value, cost


def _parse(response: dict[str, object]) -> object:
    try:
        choices = response["choices"]
        if not isinstance(choices, list) or not choices:
            raise TypeError
        message = choices[0]["message"]
        content = message["content"]
        if not isinstance(content, str) or not content.strip():
            raise TypeError
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise IntelligenceProviderError("malformed_output", retryable=True) from exc


def provider_safe_snapshot(
    snapshot: FrozenClinicalEventSnapshot,
) -> tuple[dict[str, object], dict[str, str]]:
    """Remove scope/source IDs and substitute request-local opaque line aliases."""

    payload = snapshot.model_dump(mode="json")
    for field in ("patient_id", "clinical_event_id", "payer_request_id"):
        payload.pop(field, None)
    payload.pop("facts_not_used", None)
    location = payload.get("location")
    if isinstance(location, dict):
        location.pop("hospital_id", None)
        location.pop("clinic_id", None)
    facts = payload.get("facts_used", [])
    if isinstance(facts, list):
        for fact in facts:
            if isinstance(fact, dict):
                fact.pop("source_id", None)
    aliases: dict[str, str] = {}
    requested_lines = payload.get("requested_lines", [])
    if isinstance(requested_lines, list):
        for index, line in enumerate(requested_lines, 1):
            if not isinstance(line, dict):
                continue
            actual = str(line.get("requested_line_id"))
            alias = f"requested_line_{index:03d}"
            aliases[alias] = actual
            line["requested_line_id"] = alias
    return payload, aliases


def provider_safe_retrieval(
    retrieval: RetrievalManifest,
) -> tuple[dict[str, object], dict[str, str]]:
    payload = retrieval.model_dump(mode="json")
    aliases: dict[str, str] = {}
    sources = payload.get("sources", [])
    if isinstance(sources, list):
        for index, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                continue
            actual = str(source.get("source_id"))
            alias = f"retrieval_source_{index:03d}"
            aliases[alias] = actual
            source["source_id"] = alias
            source.pop("release_id", None)
            source_payload = source.get("payload")
            if isinstance(source_payload, dict):
                source_payload.pop("scope_key", None)
                facility_scope = source_payload.get("facility_scope")
                if isinstance(facility_scope, dict):
                    for key in (
                        "payer_organization_ids",
                        "hospital_ids",
                        "clinic_ids",
                    ):
                        facility_scope.pop(key, None)
                for item in source_payload.get("price_items", []):
                    if isinstance(item, dict):
                        item.pop("source_item_id", None)
    return payload, aliases


def _translate_output_aliases(
    output: object,
    line_aliases: dict[str, str],
    source_aliases: dict[str, str],
) -> object:
    if not isinstance(output, dict):
        return output
    assessments = output.get("requested_item_assessments")
    if isinstance(assessments, list):
        for assessment in assessments:
            if isinstance(assessment, dict):
                alias = assessment.get("requested_line_id")
                if isinstance(alias, str) and alias in line_aliases:
                    assessment["requested_line_id"] = line_aliases[alias]
                estimate = assessment.get("estimated_cost")
                if isinstance(estimate, dict) and isinstance(estimate.get("source_ids"), list):
                    estimate["source_ids"] = [
                        source_aliases.get(str(value), str(value))
                        for value in estimate["source_ids"]
                    ]
    discrepancies = output.get("discrepancies")
    if isinstance(discrepancies, list):
        for discrepancy in discrepancies:
            if isinstance(discrepancy, dict):
                alias = discrepancy.get("requested_line_id")
                if isinstance(alias, str) and alias in line_aliases:
                    discrepancy["requested_line_id"] = line_aliases[alias]
    return output


class DeepSeekPrimaryIntelligenceProvider:
    def __init__(self, transport: OpenAICompatibleJsonTransport | None = None) -> None:
        self.transport = transport or OpenAICompatibleJsonTransport()

    def generate(
        self,
        *,
        snapshot: FrozenClinicalEventSnapshot,
        retrieval: RetrievalManifest,
        settings: Settings,
    ) -> IntelligenceProviderResponse:
        if settings.deepseek_api_key is None:
            raise IntelligenceProviderError("provider_key_missing", retryable=False)
        snapshot_payload, aliases = provider_safe_snapshot(snapshot)
        retrieval_payload, source_aliases = provider_safe_retrieval(retrieval)
        body = {
            "model": settings.clinical_event_intelligence_primary_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return one JSON object matching the schema. Use only admitted fact IDs, "
                        "frozen requested lines, and retrieved source IDs. Generate plausible "
                        "typical, alternative, and escalated hypotheses where supported; never "
                        "Present none as prescriptions. Assess every requested_line_id once. "
                        "Never approve, deny, reduce, delay, remove care, diagnose, allege fraud, "
                        "guess location, or invent a price source. When no admitted price exists, "
                        "use provenance tier 5, no source IDs, and an exploratory cost range where "
                        "high_minor - low_minor >= max(1000, low_minor). A requested amount is "
                        "context, not an estimated range. Cost provenance maps exactly as follows: "
                        "facility_price or payer_price is tier 1; regional_reference is tier 2; "
                        "comparable_case is tier 3; care_pathway is tier 4. Cite only source IDs "
                        "whose price_items or cost_analogues exactly match that requested line's "
                        "code system, service code, unit, and currency."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "snapshot": snapshot_payload,
                            "retrieval": retrieval_payload,
                            "json_schema": PrimaryIntelligenceOutput.model_json_schema(),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "temperature": 0.0,
            "stream": False,
            "max_tokens": settings.clinical_event_intelligence_primary_max_output_tokens,
        }
        try:
            response = self.transport.request(
                endpoint=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key.get_secret_value(),
                request_body=body,
                timeout_seconds=settings.clinical_event_intelligence_primary_timeout_seconds,
            ).payload
        except ProviderTransportError as exc:
            raise IntelligenceProviderError(
                exc.code,
                retryable=exc.code in {"timeout", "malformed_envelope"},
            ) from exc
        if response.get("model") != settings.clinical_event_intelligence_primary_model:
            raise IntelligenceProviderError("provider_model_drift", retryable=False)
        output = _translate_output_aliases(_parse(response), aliases, source_aliases)
        input_tokens, output_tokens, cost = _usage(
            response,
            input_price_per_million_usd=(
                settings.clinical_event_intelligence_primary_input_price_per_million_usd
            ),
            output_price_per_million_usd=(
                settings.clinical_event_intelligence_primary_output_price_per_million_usd
            ),
        )
        return IntelligenceProviderResponse(
            output=output,
            provider=settings.clinical_event_intelligence_primary_provider,
            model=str(response.get("model") or settings.clinical_event_intelligence_primary_model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_microunits=cost,
            output_checksum_sha256=canonical_checksum(output),
        )


class DeepSeekCriticIntelligenceProvider:
    def __init__(self, transport: OpenAICompatibleJsonTransport | None = None) -> None:
        self.transport = transport or OpenAICompatibleJsonTransport()

    def review(
        self,
        *,
        snapshot: FrozenClinicalEventSnapshot,
        retrieval: RetrievalManifest,
        primary: ValidatedIntelligence,
        settings: Settings,
    ) -> IntelligenceProviderResponse:
        if settings.deepseek_api_key is None:
            raise IntelligenceProviderError("provider_key_missing", retryable=False)
        snapshot_payload, aliases = provider_safe_snapshot(snapshot)
        retrieval_payload, source_aliases = provider_safe_retrieval(retrieval)
        primary_payload = primary.model_dump(mode="json")
        reverse_aliases = {actual: alias for alias, actual in aliases.items()}
        reverse_source_aliases = {actual: alias for alias, actual in source_aliases.items()}
        for assessment in primary_payload.get("primary", {}).get("requested_item_assessments", []):
            if isinstance(assessment, dict):
                actual = assessment.get("requested_line_id")
                if isinstance(actual, str) and actual in reverse_aliases:
                    assessment["requested_line_id"] = reverse_aliases[actual]
                estimate = assessment.get("estimated_cost")
                if isinstance(estimate, dict) and isinstance(estimate.get("source_ids"), list):
                    estimate["source_ids"] = [
                        reverse_source_aliases.get(str(value), str(value))
                        for value in estimate["source_ids"]
                    ]
        for assessment in primary_payload.get("assessments", []):
            if isinstance(assessment, dict):
                proposal = assessment.get("proposal")
                if isinstance(proposal, dict):
                    actual = proposal.get("requested_line_id")
                    if isinstance(actual, str) and actual in reverse_aliases:
                        proposal["requested_line_id"] = reverse_aliases[actual]
                    estimate = proposal.get("estimated_cost")
                    if isinstance(estimate, dict) and isinstance(estimate.get("source_ids"), list):
                        estimate["source_ids"] = [
                            reverse_source_aliases.get(str(value), str(value))
                            for value in estimate["source_ids"]
                        ]
        body = {
            "model": settings.clinical_event_intelligence_critic_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Independently inspect the frozen facts, admitted sources, and validated "
                        "proposal. Return only structured discrepancy categories with concise "
                        "fact references. Do not provide chain-of-thought or new conclusions, "
                        "prices, approval, denial, fraud, or workflow actions."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "snapshot": snapshot_payload,
                            "retrieval": retrieval_payload,
                            "primary": primary_payload,
                            "json_schema": CriticOutput.model_json_schema(),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "temperature": 0.0,
            "stream": False,
            "max_tokens": settings.clinical_event_intelligence_critic_max_output_tokens,
        }
        try:
            response = self.transport.request(
                endpoint=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key.get_secret_value(),
                request_body=body,
                timeout_seconds=settings.clinical_event_intelligence_critic_timeout_seconds,
            ).payload
        except ProviderTransportError as exc:
            raise IntelligenceProviderError(exc.code, retryable=False) from exc
        if response.get("model") != settings.clinical_event_intelligence_critic_model:
            raise IntelligenceProviderError("provider_model_drift", retryable=False)
        output = _translate_output_aliases(_parse(response), aliases, source_aliases)
        input_tokens, output_tokens, cost = _usage(
            response,
            input_price_per_million_usd=(
                settings.clinical_event_intelligence_critic_input_price_per_million_usd
            ),
            output_price_per_million_usd=(
                settings.clinical_event_intelligence_critic_output_price_per_million_usd
            ),
        )
        return IntelligenceProviderResponse(
            output=output,
            provider=settings.clinical_event_intelligence_critic_provider,
            model=str(response.get("model") or settings.clinical_event_intelligence_critic_model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_microunits=cost,
            output_checksum_sha256=canonical_checksum(output),
        )
