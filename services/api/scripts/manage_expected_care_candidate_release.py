"""Content-free governed operations for the Slice D purpose release."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.expected_care_candidate_governance import (  # noqa: E402
    RELEASE_KEY,
    RELEASE_TYPE,
    SCOPE_KEY,
    activate_candidate_release,
    engage_candidate_kill_switch,
    rollback_candidate_release,
)
from app.expected_care_comparison import _checksum  # noqa: E402
from app.models import (  # noqa: E402
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseReview,
)

WAIVER_STATUS = "product_owner_waived_for_current_stage"


def _release(db, release_id: str) -> GovernedCareRelease:
    release = db.get(GovernedCareRelease, uuid.UUID(release_id))
    if release is None:
        raise SystemExit("release_not_found")
    return release


def _register(
    db,
    artifact_path: Path,
    *,
    evidence_root: Path | None = None,
) -> GovernedCareRelease:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    existing = db.scalar(
        select(GovernedCareRelease).where(
            GovernedCareRelease.release_type == RELEASE_TYPE,
            GovernedCareRelease.release_key == RELEASE_KEY,
            GovernedCareRelease.version == artifact["version"],
        )
    )
    payload_checksum = _checksum(artifact)
    if existing is not None:
        if existing.payload_checksum_sha256 != payload_checksum:
            raise SystemExit("immutable_release_conflict")
        return existing
    predecessor = None
    predecessor_version = artifact.get("predecessor_release_version")
    if predecessor_version:
        predecessor = db.scalar(
            select(GovernedCareRelease).where(
                GovernedCareRelease.release_type == RELEASE_TYPE,
                GovernedCareRelease.release_key == RELEASE_KEY,
                GovernedCareRelease.version == predecessor_version,
            )
        )
        if predecessor is None:
            raise SystemExit("predecessor_release_not_found")
    result_path = Path(str(artifact["evaluation_result_path"]))
    if not result_path.is_absolute():
        api_root = Path(__file__).resolve().parents[1]
        repo_root = (
            api_root.parents[1]
            if api_root.name == "api" and api_root.parent.name == "services"
            else api_root
        )
        result_path = (evidence_root or repo_root) / result_path
    if (
        hashlib.sha256(result_path.read_bytes()).hexdigest()
        != artifact["evaluation_result_checksum_sha256"]
    ):
        raise SystemExit("evaluation_result_checksum_drift")
    release = GovernedCareRelease(
        supersedes_release_id=predecessor.id if predecessor else None,
        release_type=RELEASE_TYPE,
        release_key=RELEASE_KEY,
        version=str(artifact["version"]),
        schema_version=str(artifact["schema_version"]),
        lifecycle_status="reviewed",
        jurisdiction="synthetic_only",
        region="Synthetic Province",
        facility_scope_json={"stage": "controlled_synthetic_staging"},
        currency="CNY",
        effective_from=date.today(),
        effective_to=date(date.today().year + 1, date.today().month, date.today().day),
        source_authority="Dr. AI synthetic product fixture",
        source_locator=f"urn:dr-ai:synthetic-ai-purpose:{RELEASE_KEY}:{artifact['version']}",
        retrieved_at=datetime.now(UTC),
        source_checksum_sha256=str(artifact["evaluation_result_checksum_sha256"]),
        payload_checksum_sha256=payload_checksum,
        provenance_json={
            "data_class": "wholly_synthetic",
            "purpose_code": artifact["purpose_code"],
            "purpose_contract_version": artifact["purpose_contract_version"],
            "schema_version": artifact["schema_version"],
            "prompt_version": artifact["prompt_version"],
            "model_configuration_version": artifact["model_configuration_version"],
            "provider": artifact["provider"],
            "model": artifact["model"],
            "runtime_contract_checksum_sha256": artifact["runtime_contract_checksum_sha256"],
            "candidate_source_sha256": artifact["candidate_source_sha256"],
            "evaluation_manifest_checksum_sha256": artifact["evaluation_manifest_checksum_sha256"],
            "evaluation_result_checksum_sha256": artifact["evaluation_result_checksum_sha256"],
            "machine_gates": artifact["machine_gates"],
            "stage_review_status": WAIVER_STATUS,
            "future_real_world_gates_preserved": True,
        },
        required_review_types_json=list(artifact["review_types"]),
        rights_status=WAIVER_STATUS,
        storage_allowed=True,
        derivation_allowed=True,
        redistribution_allowed=False,
        provider_transmission_allowed=True,
        last_verified_on=date.today(),
        next_review_on=date(date.today().year + 1, date.today().month, date.today().day),
    )
    db.add(release)
    db.flush()
    for review_type in artifact["review_types"]:
        release.reviews.append(
            GovernedCareReleaseReview(
                review_type=str(review_type),
                decision=WAIVER_STATUS,
                reviewer_name="Dr. AI product-owner early-stage policy",
                reviewed_payload_checksum_sha256=payload_checksum,
                rationale=(
                    "Synthetic development and controlled staging only; "
                    "future real-world review remains required."
                ),
            )
        )
    db.flush()
    return release


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("register", "status", "activate", "kill-switch", "rollback"),
    )
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--release-id")
    parser.add_argument("--target-release-id")
    parser.add_argument("--expected-version")
    parser.add_argument("--actor-user-id")
    parser.add_argument("--reason-code", default="controlled_operator_action")
    args = parser.parse_args()
    actor_id = uuid.UUID(args.actor_user_id) if args.actor_user_id else None
    with SessionLocal() as db:
        if args.action == "register":
            if args.artifact is None:
                parser.error("--artifact is required")
            release = _register(db, args.artifact, evidence_root=args.evidence_root)
            payload = {
                "release_id": str(release.id),
                "version": release.version,
                "content_free": True,
            }
        elif args.action == "status":
            pointer = db.scalar(
                select(GovernedActiveCareRelease).where(
                    GovernedActiveCareRelease.release_type == RELEASE_TYPE,
                    GovernedActiveCareRelease.release_key == RELEASE_KEY,
                    GovernedActiveCareRelease.scope_key == SCOPE_KEY,
                )
            )
            payload = {
                "active_release_id": str(pointer.release_id) if pointer else None,
                "content_free": True,
            }
        elif args.action == "kill-switch":
            event = engage_candidate_kill_switch(
                db,
                actor_user_id=actor_id,
                reason_code=args.reason_code,
            )
            payload = {"event_id": str(event.id), "action": event.action, "content_free": True}
        else:
            if not args.release_id or not args.expected_version:
                parser.error("--release-id and --expected-version are required")
            release = _release(db, args.release_id)
            if args.action == "activate":
                event = activate_candidate_release(
                    db,
                    release=release,
                    settings=get_settings(),
                    actor_user_id=actor_id,
                    reason_code=args.reason_code,
                    on_date=date.today(),
                    expected_version=args.expected_version,
                )
            else:
                if not args.target_release_id:
                    parser.error("--target-release-id is required")
                event = rollback_candidate_release(
                    db,
                    current_release=release,
                    rollback_target=_release(db, args.target_release_id),
                    settings=get_settings(),
                    actor_user_id=actor_id,
                    reason_code=args.reason_code,
                    on_date=date.today(),
                    expected_current_version=args.expected_version,
                )
            payload = {
                "event_id": str(event.id),
                "release_id": str(event.release_id),
                "action": event.action,
                "content_free": True,
            }
        db.commit()
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
