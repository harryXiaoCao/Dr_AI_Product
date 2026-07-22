"""Manage governed online source families, polling, freshness, and kill switches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.database import SessionLocal
from app.knowledge_freshness import (
    freshness_snapshot,
    load_source_family_manifest,
    run_due_source_families,
    set_source_family_kill_switch,
    sync_source_families,
)
from app.knowledge_ingestion import ImmutableArtifactStore

DEFAULT_MANIFEST = Path("knowledge_base/source_families/china_authorities.v1.json")
DEFAULT_ARTIFACT_ROOT = Path("knowledge_base/online_artifacts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("sync")
    poll = subparsers.add_parser("poll")
    poll.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    poll.add_argument("--max-discovered-fetches", type=int, default=8)
    poll.add_argument("--force", action="store_true")
    subparsers.add_parser("status")
    for command in ("kill", "restore"):
        action = subparsers.add_parser(command)
        action.add_argument("source_family_id")
        action.add_argument("--actor-id", required=True)
        action.add_argument("--reason-code", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "sync":
        manifest = load_source_family_manifest(args.manifest)
        with SessionLocal.begin() as db:
            publishers, families = sync_source_families(db, manifest)
        print(
            f"validated_families={len(manifest.families)} "
            f"publishers_created={publishers} families_created={families}"
        )
        return
    if args.command == "poll":
        if not 0 <= args.max_discovered_fetches <= 25:
            raise SystemExit("--max-discovered-fetches must be between 0 and 25.")
        store = ImmutableArtifactStore(args.artifact_root)
        with SessionLocal.begin() as db:
            runs = run_due_source_families(
                db,
                store,
                max_discovered_fetches=args.max_discovered_fetches,
                force=args.force,
            )
            output = [
                {
                    "run_id": run.stable_id,
                    "status": run.status,
                    "attempted": run.attempted_count,
                    "changed": run.changed_count,
                    "unchanged": run.unchanged_count,
                    "quarantined": run.quarantined_count,
                    "discovered": run.discovered_locator_count,
                    "error_code": run.error_code,
                }
                for run in runs
            ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return
    if args.command == "status":
        with SessionLocal() as db:
            output = freshness_snapshot(db)
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        return
    with SessionLocal.begin() as db:
        family = set_source_family_kill_switch(
            db,
            stable_id=args.source_family_id,
            killed=args.command == "kill",
            actor_id=args.actor_id,
            reason_code=args.reason_code,
        )
    print(
        f"source_family={family.stable_id} status={family.status} "
        f"reason_code={family.kill_reason_code or 'cleared'}"
    )


if __name__ == "__main__":
    main()
