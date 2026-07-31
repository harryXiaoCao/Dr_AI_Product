#!/usr/bin/env python3
"""Print guarded backup, restore-rehearsal, or rollback previews only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPOSITORY_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.phase7_operations import (  # noqa: E402
    OperationAction,
    StagingTarget,
    build_operation_preview,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=[action.value for action in OperationAction])
    parser.add_argument("--host", required=True)
    parser.add_argument("--deployment-dir", required=True)
    parser.add_argument("--live-database", required=True)
    parser.add_argument("--backup-id", required=True)
    parser.add_argument("--backup-manifest-sha256")
    parser.add_argument("--restore-database")
    parser.add_argument("--predecessor-api-digest")
    parser.add_argument("--predecessor-web-sha256")
    args = parser.parse_args()

    preview = build_operation_preview(
        OperationAction(args.action),
        StagingTarget(
            host=args.host,
            deployment_dir=args.deployment_dir,
            live_database=args.live_database,
        ),
        backup_id=args.backup_id,
        backup_manifest_sha256=args.backup_manifest_sha256,
        restore_database=args.restore_database,
        predecessor_api_digest=args.predecessor_api_digest,
        predecessor_web_sha256=args.predecessor_web_sha256,
    )
    print(json.dumps(preview.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
