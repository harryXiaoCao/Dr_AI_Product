#!/usr/bin/env python3
"""Print credential presence and sensitive-pattern counts without values."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPOSITORY_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.phase7_operations import (  # noqa: E402
    presence_states,
    scan_sensitive_pattern_presence,
)

DEFAULT_NAMES = (
    "DR_AI_DATABASE_URL",
    "DR_AI_DEEPSEEK_API_KEY",
    "DR_AI_IMAGE",
    "DR_AI_JWT_SECRET",
    "DR_AI_NOTIFICATION_APNS_PRIVATE_KEY",
    "DR_AI_NOTIFICATION_EMAS_APP_SECRET",
    "DR_AI_NOTIFICATION_WEB_PUSH_VAPID_PRIVATE_KEY",
    "DR_AI_RETRIEVAL_IMAGE",
    "DR_AI_STAGING_HOST",
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\bauthorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"(?i)\b(?:password|private_key|refresh_token)\s*[:=]\s*\S+"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{8,}\b"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--scan-file", action="append", type=Path, default=[])
    args = parser.parse_args()

    names = args.name or list(DEFAULT_NAMES)
    states = (
        presence_states(names, env_file=args.env_file)
        if args.env_file is not None
        else presence_states(names, environment=os.environ)
    )
    scan = scan_sensitive_pattern_presence(args.scan_file, SENSITIVE_PATTERNS)
    report = {
        "schema_version": "phase7-presence-check-v1",
        "presence": states,
        "sensitive_pattern_scan": asdict(scan),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if scan.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
