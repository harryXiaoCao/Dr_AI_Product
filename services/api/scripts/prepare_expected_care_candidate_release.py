"""Build a portable current-source Slice D governed release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.config import get_settings
from app.expected_care_candidate_governance import (
    candidate_runtime_contract_checksum,
    candidate_source_checksum_sha256,
)
from app.expected_care_candidates import (
    MODEL_CONFIGURATION_VERSION,
    OUTPUT_SCHEMA_VERSION,
    PROMPT_VERSION,
    PURPOSE_CODE,
    PURPOSE_CONTRACT_VERSION,
)

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = (
    API_ROOT.parents[1]
    if API_ROOT.name == "api" and API_ROOT.parent.name == "services"
    else API_ROOT
)
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--predecessor-version")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    if (
        result.get("execution_mode") != "live_deepseek"
        or result.get("machine_gate_passed") is not True
        or not all(result.get("machine_gates", {}).values())
    ):
        raise SystemExit("A passing live DeepSeek result is required.")
    settings = get_settings()
    try:
        result_path = args.result.resolve().relative_to(REPO_ROOT)
    except ValueError as exc:
        raise SystemExit("Result must be inside the repository.") from exc
    artifact = {
        "release_key": "expected-care-candidate",
        "version": args.version,
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model_configuration_version": MODEL_CONFIGURATION_VERSION,
        "provider": settings.expected_care_provider,
        "model": settings.expected_care_model,
        "runtime_contract_checksum_sha256": candidate_runtime_contract_checksum(settings),
        "candidate_source_sha256": candidate_source_checksum_sha256(),
        "evaluation_result_path": str(result_path),
        "evaluation_manifest_checksum_sha256": result["suite_checksum_sha256"],
        "evaluation_result_checksum_sha256": hashlib.sha256(args.result.read_bytes()).hexdigest(),
        "machine_gates": result["machine_gates"],
        "review_types": list(REVIEW_TYPES),
        "stage_review_status": "product_owner_waived_for_current_stage",
        "future_real_world_gates_preserved": True,
        "predecessor_release_version": args.predecessor_version,
        "real_world_activation_allowed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
