"""Validate or execute the frozen patient-chat product-path release gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = REPO_ROOT / "evaluation/chatbot/frozen_suite.v1.json"
DEFAULT_RESULTS = REPO_ROOT / "evaluation/chatbot/results"
REQUIRED_GATES = {
    "bilingual",
    "privacy",
    "injection",
    "malformed_output",
    "timeout",
    "quota",
    "outage",
    "context_drift",
    "cross_patient",
    "kill_switch",
    "rollback",
}


def _checksum(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def suite_checksum(suite: dict[str, object]) -> str:
    return _checksum({key: value for key, value in suite.items() if key != "content_sha256"})


def validate_suite(path: Path) -> dict[str, object]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema_version") != "1.0.0":
        raise ValueError("unsupported_suite_schema")
    if suite.get("content_sha256") != suite_checksum(suite):
        raise ValueError("suite_checksum_mismatch")
    if set(suite.get("required_gates", [])) != REQUIRED_GATES:
        raise ValueError("required_gate_contract_mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation_cases_missing")
    observed_gates = {
        gate for case in cases if isinstance(case, dict) for gate in case.get("gates", [])
    }
    if observed_gates != REQUIRED_GATES:
        raise ValueError("case_gate_coverage_mismatch")
    if any(
        not isinstance(case, dict) or not str(case.get("pytest_node_id", "")).startswith("tests/")
        for case in cases
    ):
        raise ValueError("product_path_node_missing")
    return suite


def run_suite(
    suite_path: Path,
    *,
    output_path: Path | None = None,
) -> tuple[dict[str, object], int]:
    suite = validate_suite(suite_path)
    node_ids = list(dict.fromkeys(str(case["pytest_node_id"]) for case in suite["cases"]))
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *node_ids],
        cwd=API_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    passed = completed.returncode == 0
    result = {
        "runner_version": "chatbot-product-path-gate.v1",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "suite_id": suite["suite_id"],
        "suite_checksum_sha256": suite["content_sha256"],
        "provider": "deepseek",
        "model": suite["model"],
        "execution_path": suite["execution"]["path"],
        "live_provider_calls": 0,
        "credentials_observed": False,
        "machine_gates": {gate: passed for gate in sorted(REQUIRED_GATES)},
        "passed": passed,
        "pytest_exit_code": completed.returncode,
        "test_node_ids": node_ids,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-2000:],
    }
    result["content_sha256"] = _checksum(result)
    target = output_path or (
        DEFAULT_RESULTS / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.sanitized.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return result, completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("validate", "run"))
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "validate":
        suite = validate_suite(args.suite)
        print(
            json.dumps(
                {
                    "suite_id": suite["suite_id"],
                    "content_sha256": suite["content_sha256"],
                    "status": "valid",
                },
                sort_keys=True,
            )
        )
        return 0
    result, returncode = run_suite(args.suite, output_path=args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
