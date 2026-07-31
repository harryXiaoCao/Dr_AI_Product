"""Build a portable, checksum-bound pending Slice F release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.expected_care_explanations import (
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
    RELEASE_KEY,
)

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = (
    API_ROOT.parents[1]
    if API_ROOT.name == "api" and API_ROOT.parent.name == "services"
    else API_ROOT
)
SUITE = REPO_ROOT / "evaluation/expected_care/frozen_suite.v1.json"
EXPLANATION_SOURCE = REPO_ROOT / "services/api/app/expected_care_explanations.py"
COMPARISON_SOURCE = REPO_ROOT / "services/api/app/expected_care_comparison.py"
REVIEW_TYPES = (
    "clinical",
    "pricing",
    "native_simplified_chinese",
    "privacy",
    "security",
    "legal",
    "payer_workflow",
    "regulatory",
)


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--predecessor-version", required=True)
    parser.add_argument("--rollback-target-version")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text())
    if (
        result.get("execution_mode") != "live_deepseek"
        or result.get("provider") != "deepseek"
        or result.get("machine_gate_passed") is not True
        or not isinstance(result.get("machine_gates"), dict)
        or not all(value is True for value in result["machine_gates"].values())
    ):
        raise SystemExit("A passing live DeepSeek result is required.")

    artifact: dict[str, object] = {
        "release_key": RELEASE_KEY,
        "version": args.version,
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "provider": "deepseek",
        "model": result["model"],
        "source_checksums": {
            "frozen_suite_file_sha256": _checksum(SUITE),
            "sanitized_result_file_sha256": _checksum(args.result),
            "explanation_source_sha256": _checksum(EXPLANATION_SOURCE),
            "comparison_source_sha256": _checksum(COMPARISON_SOURCE),
            "output_schema_sha256": result["output_schema_checksum_sha256"],
        },
        "evaluation_manifest_checksum_sha256": result["suite_checksum_sha256"],
        "evaluation_result_checksum_sha256": _checksum(args.result),
        "review_requirements": [
            {
                "review_type": review_type,
                "status": "pending",
                "scope": "early_synthetic_development_and_controlled_staging_only",
                "future_real_world_gate_preserved": True,
            }
            for review_type in REVIEW_TYPES
        ],
        "machine_gates": result["machine_gates"],
        "activation_state": "blocked_pending_external_reviews",
        "kill_switch_state": "on",
        "predecessor_release_version": args.predecessor_version,
        "rollback_target": (
            "exact_predecessor" if args.rollback_target_version else "fixed_structured_fallback"
        ),
        "real_world_activation_allowed": False,
        "rollback_evidence": {
            "required": True,
            "target": args.rollback_target_version or "fixed_structured_fallback",
            "content_free": True,
        },
    }
    if args.rollback_target_version:
        artifact["rollback_target_release_version"] = args.rollback_target_version
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
