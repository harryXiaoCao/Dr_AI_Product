#!/usr/bin/env python3
"""Print the deterministic, content-free Phase 7 fault campaign plan."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPOSITORY_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.phase7_operations import default_fault_campaign  # noqa: E402


def main() -> int:
    campaign = default_fault_campaign()
    report = {
        "schema_version": "phase7-fault-campaign-v1",
        "execution_mode": "plan_only",
        "events": [asdict(event) for event in campaign.events],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
