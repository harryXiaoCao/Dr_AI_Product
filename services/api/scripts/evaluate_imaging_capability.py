"""Run the no-network, fail-closed imaging capability scaffold."""

from __future__ import annotations

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.imaging_ai_capability import evaluate_imaging_capability  # noqa: E402

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = (
    API_ROOT.parents[1]
    if API_ROOT.name == "api" and API_ROOT.parent.name == "services"
    else API_ROOT
)
SUITE = REPO_ROOT / "evaluation/imaging/frozen_suite.v1.json"


def main() -> None:
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    observations = []
    for case in suite["cases"]:
        result = evaluate_imaging_capability(
            provider="deepseek",
            model="deepseek-v4-flash",
            declared_input_modalities=tuple(case["declared_input_modalities"]),
        )
        passed = (
            result.status == case["expected_status"]
            and result.provider_call_attempted == case["expected_provider_call_attempted"]
            and result.release_registration_allowed == case["expected_release_registration_allowed"]
        )
        observations.append(
            {
                "case_id": case["case_id"],
                "status": result.status,
                "diagnostic_code": result.diagnostic_code,
                "provider_call_attempted": result.provider_call_attempted,
                "release_registration_allowed": result.release_registration_allowed,
                "evaluation_checksum_sha256": result.evaluation_checksum_sha256,
                "passed": passed,
            }
        )
    print(
        json.dumps(
            {
                "suite_id": suite["suite_id"],
                "machine_gate_passed": all(item["passed"] for item in observations),
                "observations": observations,
                "content_free": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
