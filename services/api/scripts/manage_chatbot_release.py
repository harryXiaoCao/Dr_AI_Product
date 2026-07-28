"""Register and transition checksum-bound patient-chat releases."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot_release_governance import (
    PURPOSE_CODE,
    ChatbotReleaseTransitionError,
    activate_release,
    build_release,
    record_kill_switch,
    rollback_release,
    supersede_release,
)
from app.config import get_settings
from app.database import engine
from app.models import (
    ChatbotGenerationActiveRelease,
    ChatbotGenerationRelease,
)


def _release(db: Session, version: str) -> ChatbotGenerationRelease:
    release = db.scalar(
        select(ChatbotGenerationRelease).where(
            ChatbotGenerationRelease.purpose_code == PURPOSE_CODE,
            ChatbotGenerationRelease.version == version,
        )
    )
    if release is None:
        raise ChatbotReleaseTransitionError("release_not_found")
    return release


def _register(db: Session, artifact_path: Path) -> ChatbotGenerationRelease:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    predecessor_id = (
        uuid.UUID(str(artifact["predecessor_release_id"]))
        if artifact.get("predecessor_release_id")
        else None
    )
    candidate = build_release(
        settings=get_settings(),
        version=str(artifact["version"]),
        evaluation_manifest_checksum_sha256=str(artifact["evaluation_manifest_checksum_sha256"]),
        evaluation_result_checksum_sha256=str(artifact["evaluation_result_checksum_sha256"]),
        machine_gates={
            str(key): bool(value) for key, value in dict(artifact["machine_gates"]).items()
        },
        predecessor_release_id=predecessor_id,
    )
    expected = {
        "release_key": candidate.release_key,
        "purpose_code": candidate.purpose_code,
        "purpose_contract_version": candidate.purpose_contract_version,
        "grounded_schema_version": candidate.grounded_schema_version,
        "general_schema_version": candidate.general_schema_version,
        "prompt_version": candidate.prompt_version,
        "provider": candidate.provider,
        "model": candidate.model,
        "contract_checksum_sha256": candidate.contract_checksum_sha256,
        "content_checksum_sha256": candidate.content_checksum_sha256,
    }
    if any(artifact.get(key) != value for key, value in expected.items()):
        raise ChatbotReleaseTransitionError("artifact_runtime_or_checksum_drift")
    existing = db.scalar(
        select(ChatbotGenerationRelease).where(
            ChatbotGenerationRelease.release_key == candidate.release_key,
            ChatbotGenerationRelease.version == candidate.version,
        )
    )
    if existing is not None:
        if existing.content_checksum_sha256 != candidate.content_checksum_sha256:
            raise ChatbotReleaseTransitionError("immutable_release_conflict")
        return existing
    db.add(candidate)
    db.flush()
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("register", "activate", "supersede", "rollback", "kill"),
    )
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--current-version")
    parser.add_argument("--target-version")
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--reason-code", default="controlled_operator_action")
    args = parser.parse_args()
    settings = get_settings()
    with Session(engine) as db:
        if args.action == "register":
            if args.artifact is None:
                parser.error("--artifact is required for register")
            release = _register(db, args.artifact)
            payload = {"release_id": str(release.id), "version": release.version}
        elif args.action == "activate":
            release = _release(db, str(args.version))
            event = activate_release(
                db,
                release=release,
                settings=settings,
                expected_version=release.version,
                idempotency_key=args.idempotency_key,
            )
            payload = {"event_id": str(event.id), "release_id": str(release.id)}
        elif args.action == "supersede":
            current = _release(db, str(args.current_version))
            target = _release(db, str(args.target_version))
            event = supersede_release(
                db,
                current_release=current,
                successor_release=target,
                settings=settings,
                expected_current_version=current.version,
                idempotency_key=args.idempotency_key,
            )
            payload = {"event_id": str(event.id), "release_id": str(target.id)}
        elif args.action == "rollback":
            current = _release(db, str(args.current_version))
            target = _release(db, str(args.target_version))
            event = rollback_release(
                db,
                current_release=current,
                rollback_target=target,
                expected_current_version=current.version,
                idempotency_key=args.idempotency_key,
            )
            payload = {"event_id": str(event.id), "release_id": str(target.id)}
        else:
            pointer = db.get(ChatbotGenerationActiveRelease, PURPOSE_CODE)
            active = (
                db.get(ChatbotGenerationRelease, pointer.release_id)
                if pointer is not None
                else None
            )
            event = record_kill_switch(
                db,
                active_release=active,
                idempotency_key=args.idempotency_key,
                reason_code=args.reason_code,
            )
            payload = {"event_id": str(event.id), "release_id": None}
        db.commit()
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
