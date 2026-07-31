#!/usr/bin/env python3
"""Print a machine-readable, content-free local Phase 7 inventory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPOSITORY_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.phase7_operations import build_file_inventory  # noqa: E402

DEFAULT_ARTIFACTS = (
    "deploy/tencent/staging/.env.example",
    "deploy/tencent/staging/Caddyfile",
    "deploy/tencent/staging/README.md",
    "deploy/tencent/staging/compose.yaml",
    "services/api/Dockerfile",
    "services/api/alembic.ini",
)


def _git(*arguments: str, root: Path) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _migration_heads(root: Path) -> list[str]:
    versions = root / "services" / "api" / "migrations" / "versions"
    revisions: list[str] = []
    for path in versions.glob("*.py"):
        prefix = path.name.split("_", 2)
        if len(prefix) >= 2 and prefix[0].isdigit() and prefix[1].isdigit():
            revisions.append(f"{prefix[0]}_{prefix[1]}")
    return sorted(revisions)[-1:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()

    root = args.repo_root.resolve(strict=True)
    artifact_names = args.artifact or list(DEFAULT_ARTIFACTS)
    artifacts = [root / name for name in artifact_names]
    status_lines = _git("status", "--short", "--untracked-files=all", root=root).splitlines()
    manifest = {
        "schema_version": "phase7-local-inventory-v1",
        "scope": "local_read_only",
        "source_revision": _git("rev-parse", "HEAD", root=root),
        "branch": _git("branch", "--show-current", root=root),
        "dirty_path_count": len(status_lines),
        "migration_heads_from_filenames": _migration_heads(root),
        "artifacts": build_file_inventory(root, artifacts),
    }
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
