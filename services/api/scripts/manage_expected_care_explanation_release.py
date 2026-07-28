"""Content-free command workflow for expected-care explanation release operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path

from app.database import SessionLocal
from app.expected_care_release_operations import (
    activate_release,
    effective_active_release_id,
    engage_purpose_kill_switch,
    mark_release_unsuitable,
    register_early_stage_waivers,
    rollback_release,
    supersede_release,
)
from app.models import ExpectedCareExplanationRelease


def _uuid(value: str | None) -> uuid.UUID | None:
    return uuid.UUID(value) if value else None


def _release(db, release_id: str) -> ExpectedCareExplanationRelease:
    release = db.get(ExpectedCareExplanationRelease, uuid.UUID(release_id))
    if release is None:
        raise SystemExit("release_not_found")
    return release


def _artifact(path: str) -> dict[str, object]:
    artifact_path = Path(path)
    payload = json.loads(artifact_path.read_text())
    if not isinstance(payload, dict):
        raise SystemExit("release_artifact_must_be_an_object")
    payload["_artifact_checksum_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    return payload


def _assert_artifact(
    release: ExpectedCareExplanationRelease,
    artifact: dict[str, object],
) -> None:
    expected = {
        "release_key": release.release_key,
        "version": release.version,
        "purpose_code": release.purpose_code,
        "purpose_contract_version": release.purpose_contract_version,
        "schema_version": release.schema_version,
        "prompt_version": release.prompt_version,
        "model_configuration_version": release.model_configuration_version,
        "provider": release.provider,
        "model": release.model,
        "source_checksums": release.source_checksums_json,
        "machine_gates": release.machine_gates_json,
    }
    if any(artifact.get(key) != value for key, value in expected.items()):
        raise SystemExit("release_artifact_database_mismatch")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "status",
            "waive",
            "activate",
            "supersede",
            "kill-switch",
            "rollback",
            "mark-unsuitable",
        ),
    )
    parser.add_argument("--release-id")
    parser.add_argument("--target-release-id")
    parser.add_argument("--expected-version")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--actor-user-id")
    parser.add_argument("--artifact")
    parser.add_argument("--reason-code", action="append", default=[])
    return parser


def main() -> None:
    args = _parser().parse_args()
    if not args.release_id:
        raise SystemExit("--release-id is required")
    with SessionLocal() as db:
        release = _release(db, args.release_id)
        if args.action == "status":
            print(
                json.dumps(
                    {
                        "release_id": str(release.id),
                        "release_key": release.release_key,
                        "version": release.version,
                        "effective_active_release_id": (
                            str(active_id)
                            if (active_id := effective_active_release_id(db, release.release_key))
                            else None
                        ),
                        "content_free": True,
                    },
                    sort_keys=True,
                )
            )
            return
        if not args.expected_version or not args.idempotency_key:
            raise SystemExit("--expected-version and --idempotency-key are required")
        actor_id = _uuid(args.actor_user_id)
        if args.action == "waive":
            requirements = {
                str(item["review_type"]): "product_owner_waived_for_current_stage"
                for item in release.review_requirements_json
            }
            result = register_early_stage_waivers(
                db,
                release=release,
                expected_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
                statuses=requirements,
            )
        elif args.action == "activate":
            if not args.artifact:
                raise SystemExit("--artifact is required")
            artifact = _artifact(args.artifact)
            _assert_artifact(release, artifact)
            result = activate_release(
                db,
                release=release,
                expected_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
                expected_source_checksums=dict(artifact["source_checksums"]),
                purpose_code=str(artifact["purpose_code"]),
                purpose_contract_version=str(artifact["purpose_contract_version"]),
                schema_version=str(artifact["schema_version"]),
                prompt_version=str(artifact["prompt_version"]),
                model_configuration_version=str(artifact["model_configuration_version"]),
                rollback_target=str(artifact["rollback_target"]),
            )
        elif args.action == "supersede":
            if not args.target_release_id or not args.artifact:
                raise SystemExit("--target-release-id and --artifact are required")
            successor = _release(db, args.target_release_id)
            artifact = _artifact(args.artifact)
            _assert_artifact(successor, artifact)
            _, result = supersede_release(
                db,
                active_release=release,
                successor=successor,
                expected_active_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
                rollback_target=str(artifact["rollback_target"]),
            )
        elif args.action == "kill-switch":
            result = engage_purpose_kill_switch(
                db,
                active_release=release,
                expected_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
                reason_code=(args.reason_code or ["operator_engaged"])[0],
            )
        elif args.action == "rollback":
            if not args.target_release_id:
                raise SystemExit("--target-release-id is required")
            _, result = rollback_release(
                db,
                current_release=release,
                rollback_target=_release(db, args.target_release_id),
                expected_current_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
            )
        else:
            result = mark_release_unsuitable(
                db,
                release=release,
                expected_version=args.expected_version,
                actor_user_id=actor_id,
                idempotency_key=args.idempotency_key,
                reason_codes=args.reason_code,
            )
        db.commit()
        print(
            json.dumps(
                {
                    "release_id": str(release.id),
                    "version": release.version,
                    "event_type": result.event.event_type,
                    "idempotent_replay": result.idempotent_replay,
                    "content_free": True,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
