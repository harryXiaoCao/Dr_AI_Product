"""Register the checksum-bound pending Slice G release in the local database."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ExpectedCareExplanationRelease,
    ExpectedCareExplanationReleaseEvent,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT = (
    REPO_ROOT / "evaluation/expected_care/releases/expected-care-role-explanation.v2.pending.json"
)
SUITE = REPO_ROOT / "evaluation/expected_care/frozen_suite.v1.json"
RESULT = REPO_ROOT / "evaluation/expected_care/results/20260726T111243Z.sanitized.json"
EXPLANATION_SOURCE = REPO_ROOT / "services/api/app/expected_care_explanations.py"
COMPARISON_SOURCE = REPO_ROOT / "services/api/app/expected_care_comparison.py"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text())
    checksums = artifact["source_checksums"]
    expected = {
        "frozen_suite_file_sha256": _file_checksum(SUITE),
        "sanitized_result_file_sha256": _file_checksum(RESULT),
        "explanation_source_sha256": _file_checksum(EXPLANATION_SOURCE),
        "comparison_source_sha256": _file_checksum(COMPARISON_SOURCE),
    }
    if any(checksums.get(key) != value for key, value in expected.items()):
        raise SystemExit("Release source checksum drifted; registration refused.")
    result = json.loads(RESULT.read_text())
    if (
        not result["machine_gate_passed"]
        or result["suite_checksum_sha256"] != artifact["evaluation_manifest_checksum_sha256"]
        or any(value["status"] != "pending" for value in artifact["review_requirements"])
        or artifact["activation_state"] != "blocked_pending_external_reviews"
        or artifact["kill_switch_state"] != "on"
    ):
        raise SystemExit("Pending release gates are inconsistent; registration refused.")
    with SessionLocal() as db:
        existing = db.scalar(
            select(ExpectedCareExplanationRelease).where(
                ExpectedCareExplanationRelease.release_key == artifact["release_key"],
                ExpectedCareExplanationRelease.version == artifact["version"],
            )
        )
        if existing is not None:
            if existing.source_checksums_json != checksums:
                raise SystemExit("Registered release content conflicts with the artifact.")
            print(existing.id)
            return
        predecessor_release_id = artifact["predecessor_release_id"]
        predecessor_version = artifact.get("predecessor_release_version")
        if predecessor_version is not None:
            predecessor = db.scalar(
                select(ExpectedCareExplanationRelease).where(
                    ExpectedCareExplanationRelease.release_key == artifact["release_key"],
                    ExpectedCareExplanationRelease.version == predecessor_version,
                )
            )
            if predecessor is None:
                raise SystemExit("Declared predecessor release is not registered.")
            predecessor_release_id = predecessor.id
        release = ExpectedCareExplanationRelease(
            predecessor_release_id=predecessor_release_id,
            rollback_target_release_id=artifact["rollback_target_release_id"],
            release_key=artifact["release_key"],
            version=artifact["version"],
            purpose_code=artifact["purpose_code"],
            purpose_contract_version=artifact["purpose_contract_version"],
            schema_version=artifact["schema_version"],
            prompt_version=artifact["prompt_version"],
            model_configuration_version=artifact["model_configuration_version"],
            provider=artifact["provider"],
            model=artifact["model"],
            source_checksums_json=checksums,
            evaluation_manifest_checksum_sha256=artifact["evaluation_manifest_checksum_sha256"],
            evaluation_result_checksum_sha256=artifact["evaluation_result_checksum_sha256"],
            review_requirements_json=artifact["review_requirements"],
            machine_gates_json=artifact["machine_gates"],
            activation_state=artifact["activation_state"],
            kill_switch_state=artifact["kill_switch_state"],
            created_by_user_id=None,
        )
        db.add(release)
        db.flush()
        db.add(
            ExpectedCareExplanationReleaseEvent(
                release_id=release.id,
                actor_user_id=None,
                event_type="release_registered_pending",
                evidence_json={
                    "rollback_evidence": artifact["rollback_evidence"],
                    "external_activation_performed": False,
                    "content_free": True,
                },
            )
        )
        db.commit()
        print(release.id)


if __name__ == "__main__":
    main()
