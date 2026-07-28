"""Run the independent, wholly synthetic Slice D DeepSeek evaluation."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.config import get_settings  # noqa: E402
from app.expected_care_candidates import (  # noqa: E402
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
    DeepSeekExpectedCareProvider,
    ExpectedCareCandidateOutput,
    ExpectedCareProviderError,
    _checksum,
    _fallback_payload,
    _validate_candidate,
)

REPO_ROOT = API_ROOT.parents[1]
DEFAULT_SUITE = REPO_ROOT / "evaluation/expected_care_candidate/frozen_suite.v1.json"
DEFAULT_RESULTS = REPO_ROOT / "evaluation/expected_care_candidate/results"
NAMESPACE = uuid.UUID("5e0d64dd-6cdf-472a-9259-2cf952b10b56")


def _minimum_input(case: dict[str, object]) -> tuple[dict[str, object], str]:
    case_id = str(case["case_id"])
    scenario_id = uuid.uuid5(NAMESPACE, f"{case_id}:scenario")
    lineage = []
    for release_type in (
        "scenario_definition",
        "care_plan",
        "pricing_reference",
        "utilization_rule",
    ):
        release_id = uuid.uuid5(NAMESPACE, f"{case_id}:{release_type}")
        lineage.append(
            {
                "release_type": release_type,
                "release_id": str(release_id),
                "release_key": f"synthetic-{case['family']}-{release_type}",
                "version": "v1-synthetic-stage",
                "payload_checksum_sha256": _checksum(
                    {"case_id": case_id, "release_type": release_type}
                ),
            }
        )
    item = {
        "item_key": f"synthetic-{case['family']}-item",
        "category": str(case["family"]),
        "code_system": "DR-AI-SYNTHETIC-SERVICE",
        "service_code": case["service_code"],
        "unit": case["unit"],
        "quantity_low": case["quantity_low"],
        "quantity_high": case["quantity_high"],
        "amount_low_minor": case["amount_low_minor"],
        "amount_high_minor": case["amount_high_minor"],
        "pricing_reference_item_id": str(uuid.uuid5(NAMESPACE, f"{case_id}:price")),
        "utilization_rule_id": str(uuid.uuid5(NAMESPACE, f"{case_id}:rule")),
    }
    value: dict[str, object] = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "context": {
            "reference_date": "2026-07-26",
            "jurisdiction": "CN",
            "region": "Synthetic Province",
            "encounter_type": "outpatient",
            "facility_ownership": "public",
            "facility_level": "primary",
            "currency": "CNY",
            "patient_age": 42,
        },
        "scenario_release_id": str(scenario_id),
        "release_lineage": lineage,
        "admitted_candidates": [item],
        "server_totals": {
            "currency": "CNY",
            "total_low_minor": case["amount_low_minor"],
            "total_high_minor": case["amount_high_minor"],
        },
        "allowed_missing_information": case["missing_information"],
        "allowed_assumptions": ["The candidate uses wholly synthetic reference data."],
        "allowed_confidence_limitations": [
            "Wholly synthetic reference data; clinician responses remain separate."
        ],
        "allowed_attributable_exceptions": [],
        "authority_boundary": {
            "model_may_omit_only": True,
            "server_owns_applicability_codes_units_currency_quantities_amounts_totals": True,
            "immutable_baseline_publication_required": True,
            "doctor_may_modify_or_hide": False,
        },
    }
    checksum = _checksum(value)
    value["minimum_input_checksum_sha256"] = checksum
    return value, checksum


def _valid_output(minimum: dict[str, object]) -> dict[str, object]:
    context = minimum["context"]
    totals = minimum["server_totals"]
    assert isinstance(context, dict) and isinstance(totals, dict)
    return {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "minimum_input_checksum_sha256": minimum["minimum_input_checksum_sha256"],
        "scenario_release_id": minimum["scenario_release_id"],
        "reference_date": context["reference_date"],
        "jurisdiction": context["jurisdiction"],
        "region": context["region"],
        "facility_ownership": context["facility_ownership"],
        "facility_level": context["facility_level"],
        "currency": context["currency"],
        "assumptions": minimum["allowed_assumptions"],
        "missing_information": minimum["allowed_missing_information"],
        "attributable_exceptions": minimum["allowed_attributable_exceptions"],
        "confidence_category": "moderate",
        "confidence_limitations": minimum["allowed_confidence_limitations"],
        "items": minimum["admitted_candidates"],
        "total_low_minor": totals["total_low_minor"],
        "total_high_minor": totals["total_high_minor"],
        "release_lineage": minimum["release_lineage"],
    }


def _validate(output: object, minimum: dict[str, object], checksum: str):
    totals = minimum["server_totals"]
    assert isinstance(totals, dict)
    deterministic = SimpleNamespace(
        total_low_minor=totals["total_low_minor"],
        total_high_minor=totals["total_high_minor"],
    )
    return _validate_candidate(
        output=output,
        minimum_input=minimum,
        minimum_input_checksum=checksum,
        deterministic=deterministic,
    )


def _executable_failure_observations(
    minimum: dict[str, object], checksum: str
) -> list[dict[str, object]]:
    base = _valid_output(minimum)
    observations = []

    def execute(case_id: str, mutate, expected_reason: str) -> None:
        candidate = deepcopy(base)
        mutate(candidate)
        _, reasons = _validate(candidate, minimum, checksum)
        observations.append(
            {
                "case_id": case_id,
                "passed": expected_reason in reasons,
                "reason_codes": list(reasons),
            }
        )

    for case_id, field, value, reason in (
        ("unsupported_currency", "currency", "USD", "candidate_currency_mismatch"),
        ("unsupported_total", "total_low_minor", 1, "candidate_total_low_minor_mismatch"),
        ("cross_scope_region", "region", "Other Synthetic Region", "candidate_region_mismatch"),
        (
            "stale_scenario_release",
            "scenario_release_id",
            str(uuid.uuid4()),
            "candidate_scenario_release_id_mismatch",
        ),
    ):
        execute(
            case_id, lambda row, field=field, value=value: row.__setitem__(field, value), reason
        )
    for case_id, field, value in (
        ("unsupported_code", "service_code", "SYN-UNSUPPORTED"),
        ("unsupported_unit", "unit", "visit"),
        ("unsupported_quantity", "quantity_high", 99),
        ("unsupported_amount", "amount_high_minor", 999999),
    ):
        execute(
            case_id,
            lambda row, field=field, value=value: row["items"][0].__setitem__(field, value),
            "unsupported_candidate_item",
        )
    execute(
        "checksum_drifted_release",
        lambda row: row["release_lineage"][0].__setitem__("payload_checksum_sha256", "0" * 64),
        "release_or_checksum_drift",
    )
    execute(
        "schema_extra_field",
        lambda row: row.__setitem__("unexpected", True),
        "malformed_schema",
    )
    execute(
        "unattributable_exception",
        lambda row: row["attributable_exceptions"].append(
            {
                "exception_code": "SYN-UNSUPPORTED",
                "source_utilization_rule_id": row["items"][0]["utilization_rule_id"],
                "limitation": "Coverage approved.",
            }
        ),
        "unattributable_exception",
    )
    for case_id in (
        "provider_timeout",
        "provider_error",
        "provider_quota",
        "deterministic_fallback",
    ):
        fallback = _fallback_payload("provider_unavailable", (case_id,))
        observations.append(
            {
                "case_id": case_id,
                "passed": (
                    fallback["artifact_type"] == "fixed_safe_fallback"
                    and fallback["reason_codes"] == [case_id]
                ),
                "reason_codes": [case_id],
            }
        )
    return observations


def run(*, suite_path: Path, result_root: Path, live: bool) -> Path:
    suite = json.loads(suite_path.read_text())
    settings = get_settings()
    if settings.environment == "production":
        raise SystemExit("Slice D evaluation is prohibited in production.")
    if live and settings.deepseek_api_key is None:
        raise SystemExit("DR_AI_DEEPSEEK_API_KEY is required for --live.")
    provider = DeepSeekExpectedCareProvider()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_root = result_root / "raw" / run_id
    raw_root.mkdir(parents=True, exist_ok=False)
    result_root.mkdir(parents=True, exist_ok=True)
    provider_observations = []
    failure_observations = []
    for case in suite["provider_cases"]:
        minimum, checksum = _minimum_input(case)
        if not failure_observations:
            failure_observations = _executable_failure_observations(minimum, checksum)
        started = time.perf_counter()
        response = None
        reasons: tuple[str, ...] = ()
        state = "not_run"
        if live:
            try:
                response = provider.generate(
                    provider_input=minimum,
                    output_schema=ExpectedCareCandidateOutput.model_json_schema(),
                    settings=settings,
                )
                parsed, reasons = _validate(response.output, minimum, checksum)
                state = "validated" if parsed is not None and not reasons else "rejected"
            except ExpectedCareProviderError as exc:
                state = "provider_error"
                reasons = (exc.code,)
        raw = {
            "case_id": case["case_id"],
            "minimum_input": minimum,
            "provider_output": response.output if response else None,
            "state": state,
            "reason_codes": list(reasons),
        }
        (raw_root / f"{case['case_id']}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2)
        )
        provider_observations.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "state": state,
                "reason_codes": list(reasons),
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "input_tokens": response.input_tokens if response else None,
                "output_tokens": response.output_tokens if response else None,
                "cost_microunits": response.cost_microunits if response else None,
                "raw_artifact_checksum_sha256": _checksum(raw),
            }
        )
    executed = [row for row in provider_observations if row["state"] != "not_run"]
    schema_rate = (
        sum(row["state"] == "validated" for row in executed) / len(executed) if executed else None
    )
    failure_rate = sum(row["passed"] for row in failure_observations) / len(failure_observations)
    thresholds = suite["mandatory_machine_thresholds"]
    gates = {
        "schema_valid": schema_rate is not None
        and schema_rate >= thresholds["schema_valid_response_rate"],
        "deterministic_exactness": failure_rate >= thresholds["deterministic_exactness_rate"],
        "unsupported_fact_rejection": failure_rate >= thresholds["unsupported_fact_rejection_rate"],
        "fallback": failure_rate >= thresholds["fallback_success_rate"],
    }
    result = {
        "suite_id": suite["suite_id"],
        "run_id": run_id,
        "executed_at": datetime.now(UTC).isoformat(),
        "execution_mode": "live_deepseek" if live else "deterministic_only",
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "suite_checksum_sha256": _checksum(suite),
        "schema_checksum_sha256": _checksum(ExpectedCareCandidateOutput.model_json_schema()),
        "metrics": {
            "schema_valid_response_rate": schema_rate,
            "executable_failure_case_rate": failure_rate,
            "provider_input_tokens": sum(row["input_tokens"] or 0 for row in executed),
            "provider_output_tokens": sum(row["output_tokens"] or 0 for row in executed),
            "configured_cost_microunits": sum(row["cost_microunits"] or 0 for row in executed),
        },
        "machine_gates": gates,
        "machine_gate_passed": bool(gates) and all(gates.values()),
        "stage_review_status": suite["stage_review_status"],
        "future_real_world_gates_preserved": True,
        "provider_observations": provider_observations,
        "failure_observations": failure_observations,
        "raw_artifact_root": str(raw_root.relative_to(REPO_ROOT)),
        "raw_artifacts_publicly_exposed": False,
    }
    output = result_root / f"{run_id}.sanitized.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--result-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    print(run(suite_path=args.suite, result_root=args.result_root, live=args.live))


if __name__ == "__main__":
    main()
