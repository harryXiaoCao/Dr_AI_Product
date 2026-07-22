from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.canonical_retrieval_evaluation import evaluate_canonical_retrieval

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")
DEFAULT_POLICY = Path("knowledge_base/evaluation/canonical_rural_symptom_retrieval_gate.v1.json")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Score the release-matched canonical retrieval-only gate. Pending source "
            "labels fail closed and are never counted as clinical support."
        )
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    contract = _load(args.contract)
    policy = _load(args.policy)
    coverage = _load(args.coverage)
    evaluation = evaluate_canonical_retrieval(contract, policy, coverage)
    artifact = {
        "evaluator_version": "canonical-retrieval-only-gate-v1",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": contract.get("contract_id"),
        "contract_sha256": contract.get("content_sha256"),
        "contract_file_sha256": _file_sha256(args.contract),
        "policy_id": policy.get("gate_id"),
        "policy_file_sha256": _file_sha256(args.policy),
        "coverage_artifact": args.coverage.name,
        "coverage_file_sha256": _file_sha256(args.coverage),
        "active_release_ids": coverage.get("active_release_ids", []),
        "provider_calls": coverage.get("provider_calls", 0),
        "paid_usage_usd": coverage.get("paid_usage_usd", 0),
        **evaluation,
    }
    rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if args.require_pass and not artifact["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
