"""Install and operate the three content-free CEI governed releases."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import select

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.clinical_event_intelligence_governance import (  # noqa: E402
    PURPOSE_SPECS,
    RELEASE_TYPE,
    SCOPE_KEY,
    activate_intelligence_release,
    engage_intelligence_kill_switch,
    intelligence_readiness,
    rollback_intelligence_release,
)
from app.clinical_event_intelligence_release_installation import (  # noqa: E402
    DEFAULT_ARTIFACT_ROOT,
    install_intelligence_releases,
)
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import GovernedActiveCareRelease, GovernedCareRelease  # noqa: E402


def _release(db, release_id: str) -> GovernedCareRelease:
    release = db.get(GovernedCareRelease, uuid.UUID(release_id))
    if release is None or release.release_key not in PURPOSE_SPECS:
        raise SystemExit("release_not_found")
    return release


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=("install", "status", "activate", "kill-switch", "rollback")
    )
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--version")
    parser.add_argument("--predecessor-version")
    parser.add_argument("--release-id")
    parser.add_argument("--target-release-id")
    parser.add_argument("--expected-version")
    parser.add_argument("--expected-checksum")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--actor-user-id")
    parser.add_argument("--reason-code", default="controlled_synthetic_operator_action")
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    settings = get_settings()
    actor_id = uuid.UUID(args.actor_user_id) if args.actor_user_id else None
    with SessionLocal() as db:
        if args.action == "install":
            releases = install_intelligence_releases(
                db,
                settings=settings,
                artifact_root=args.artifact_root,
                version=args.version or "v1-controlled-synthetic-20260802",
                predecessor_version=args.predecessor_version,
            )
            payload = {
                "installed": [
                    {
                        "release_id": str(release.id),
                        "release_key": release.release_key,
                        "version": release.version,
                        "payload_checksum_sha256": release.payload_checksum_sha256,
                    }
                    for release in releases
                ],
                "scope_key": SCOPE_KEY,
                "content_free": True,
            }
        elif args.action == "status":
            pointers = {
                pointer.release_key: pointer
                for pointer in db.scalars(
                    select(GovernedActiveCareRelease).where(
                        GovernedActiveCareRelease.release_type == RELEASE_TYPE,
                        GovernedActiveCareRelease.scope_key == SCOPE_KEY,
                        GovernedActiveCareRelease.release_key.in_(PURPOSE_SPECS),
                    )
                )
            }
            payload = {
                "scope_key": SCOPE_KEY,
                "readiness": intelligence_readiness(db, settings),
                "purposes": {
                    key: {
                        "active_release_id": (
                            str(pointers[key].release_id) if key in pointers else None
                        )
                    }
                    for key in PURPOSE_SPECS
                },
                "content_free": True,
            }
        else:
            if not all(
                (
                    args.release_id,
                    args.expected_version,
                    args.expected_checksum,
                    args.idempotency_key,
                )
            ):
                parser.error(
                    "--release-id, --expected-version, --expected-checksum, and "
                    "--idempotency-key are required"
                )
            release = _release(db, args.release_id)
            common = {
                "settings": settings,
                "idempotency_key": args.idempotency_key,
                "actor_user_id": actor_id,
                "reason_code": args.reason_code,
            }
            if args.action == "activate":
                result = activate_intelligence_release(
                    db,
                    release=release,
                    expected_version=args.expected_version,
                    expected_payload_checksum_sha256=args.expected_checksum,
                    on_date=date.today(),
                    **common,
                )
            elif args.action == "kill-switch":
                result = engage_intelligence_kill_switch(
                    db,
                    release=release,
                    expected_version=args.expected_version,
                    expected_payload_checksum_sha256=args.expected_checksum,
                    **common,
                )
            else:
                target = _release(db, args.target_release_id) if args.target_release_id else None
                result = rollback_intelligence_release(
                    db,
                    current_release=release,
                    rollback_target=target,
                    expected_current_version=args.expected_version,
                    expected_current_payload_checksum_sha256=args.expected_checksum,
                    on_date=date.today(),
                    **common,
                )
            payload = {
                "event_id": str(result.event.id),
                "release_id": str(result.event.release_id),
                "release_key": result.event.release_key,
                "action": result.event.action,
                "idempotent_replay": result.idempotent_replay,
                "content_free": True,
            }
        db.commit()
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
