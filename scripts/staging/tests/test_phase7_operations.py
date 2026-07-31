from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "api"))

from app.phase7_operations import (  # noqa: E402
    InvariantSnapshot,
    OperationAction,
    StagingTarget,
    build_file_inventory,
    build_operation_preview,
    presence_states,
    scan_sensitive_pattern_presence,
    verify_recovery_invariants,
)

INVARIANT_KEYS = {
    "analytics_identities",
    "clinical_events",
    "expected_care_facts",
    "financial_allocations",
    "notification_delivery_attempts",
    "notifications",
    "payer_decisions",
    "payer_submissions",
    "support_requests",
}


def _snapshot(
    *,
    row_count: int = 3,
    duplicate_overrides: dict[str, int] | None = None,
) -> InvariantSnapshot:
    duplicate_counts = dict.fromkeys(INVARIANT_KEYS, 0)
    duplicate_counts.update(duplicate_overrides or {})
    return InvariantSnapshot.validate(
        row_counts=dict.fromkeys(INVARIANT_KEYS, row_count),
        duplicate_counts=duplicate_counts,
    )


def _target() -> StagingTarget:
    return StagingTarget(
        host="staging.example.test",
        deployment_dir="/home/ubuntu/dr-ai/staging",
        live_database="dr_ai_staging",
    )


def test_inventory_is_deterministic_and_rejects_secret_or_external_paths(
    tmp_path: Path,
) -> None:
    safe = tmp_path / "compose.yaml"
    safe.write_text("services: {}\n", encoding="utf-8")
    inventory = build_file_inventory(tmp_path, [safe])

    assert inventory == [
        {
            "path": "compose.yaml",
            "size_bytes": 13,
            "sha256": "fa6ccea1ca4e3a031d9e99f25cc05db803aa9bac642c000ddab14f6d9da54b52",
        }
    ]
    secret = tmp_path / ".env"
    secret.write_text("SECRET=must-never-appear\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sensitive_inventory_path_rejected"):
        build_file_inventory(tmp_path, [secret])
    external = tmp_path.parent / "outside.txt"
    external.write_text("outside", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory_path_outside_root"):
        build_file_inventory(tmp_path, [external])


def test_presence_and_pattern_scan_never_return_values_or_matching_lines(
    tmp_path: Path,
) -> None:
    secret_value = "phase7-value-that-must-not-be-returned"
    states = presence_states(
        ["DR_AI_EMPTY", "DR_AI_MISSING", "DR_AI_SECRET"],
        environment={"DR_AI_EMPTY": "", "DR_AI_SECRET": secret_value},
    )
    assert states == {
        "DR_AI_EMPTY": "empty",
        "DR_AI_MISSING": "absent",
        "DR_AI_SECRET": "set",
    }
    assert secret_value not in json.dumps(states)

    log = tmp_path / "api.log"
    log.write_text(f"password={secret_value}\nrequest completed\n", encoding="utf-8")
    result = scan_sensitive_pattern_presence(
        [log],
        [re.compile(r"(?i)password=\S+")],
    )
    assert result.files_scanned == 1
    assert result.suspected_match_count == 1
    assert result.passed is False
    assert secret_value not in repr(result)


def test_operation_previews_are_exact_targeted_and_non_executable() -> None:
    backup = build_operation_preview(
        OperationAction.BACKUP,
        _target(),
        backup_id="20260730T120000Z-phase7-local",
    )
    assert backup.preview_only is True
    assert backup.artifacts["backup_dir"] == (
        "/home/ubuntu/dr-ai/staging/backups/20260730T120000Z-phase7-local"
    )
    assert "command" not in json.dumps(backup.to_dict())

    restore = build_operation_preview(
        OperationAction.RESTORE_REHEARSAL,
        _target(),
        backup_id="20260730T120000Z-phase7-local",
        backup_manifest_sha256="a" * 64,
        restore_database="dr_ai_phase7_restore_20260730",
    )
    assert restore.artifacts["restore_database"] == "dr_ai_phase7_restore_20260730"
    assert "restore_without_live_database_mutation" in restore.checks

    rollback = build_operation_preview(
        OperationAction.ROLLBACK,
        _target(),
        backup_id="20260730T120000Z-phase7-local",
        predecessor_api_digest="b" * 64,
        predecessor_web_sha256="c" * 64,
    )
    assert rollback.artifacts["predecessor_api_digest"] == "b" * 64
    assert "restore_exact_api_and_web_predecessors" in rollback.checks


@pytest.mark.parametrize(
    ("target", "error"),
    [
        (
            StagingTarget(
                host="staging.example.test",
                deployment_dir="/",
                live_database="dr_ai_staging",
            ),
            "deployment_dir_must_be_narrow_absolute_path",
        ),
        (
            StagingTarget(
                host="staging.example.test",
                deployment_dir="/home/ubuntu/dr-ai/staging",
                live_database="dr_ai_production",
            ),
            "live_database_must_be_explicit_staging_database",
        ),
        (
            StagingTarget(
                host="staging.example.test",
                deployment_dir="/home/ubuntu/dr-ai/staging",
                live_database="dr_ai_staging",
                environment="production",
            ),
            "target_environment_must_be_staging",
        ),
    ],
)
def test_operation_target_guards_reject_broad_or_non_staging_scope(
    target: StagingTarget,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        build_operation_preview(
            OperationAction.BACKUP,
            target,
            backup_id="20260730T120000Z-phase7-local",
        )


def test_restore_preview_requires_a_distinct_disposable_database() -> None:
    with pytest.raises(ValueError, match="restore_requires_isolated_disposable_database"):
        build_operation_preview(
            OperationAction.RESTORE_REHEARSAL,
            _target(),
            backup_id="20260730T120000Z-phase7-local",
            backup_manifest_sha256="d" * 64,
            restore_database="dr_ai_staging",
        )


def test_content_free_invariants_detect_rows_and_duplicates_without_identities() -> None:
    before = _snapshot()
    unchanged = verify_recovery_invariants(before, _snapshot())
    assert unchanged.passed is True
    assert unchanged.failed_categories == ()

    after = InvariantSnapshot.validate(
        row_counts={
            **before.row_counts,
            "notifications": before.row_counts["notifications"] + 1,
        },
        duplicate_counts={
            **before.duplicate_counts,
            "payer_decisions": 1,
        },
    )
    failed = verify_recovery_invariants(before, after)
    assert failed.passed is False
    assert failed.failed_categories == ("notifications", "payer_decisions")
    assert set(failed.row_deltas) == INVARIANT_KEYS
    assert all(isinstance(value, int) for value in failed.row_deltas.values())


def test_invariant_contract_rejects_unknown_identity_bearing_dimensions() -> None:
    with pytest.raises(ValueError, match="unknown_or_identity_bearing_invariant"):
        InvariantSnapshot.validate(
            row_counts={**dict.fromkeys(INVARIANT_KEYS, 0), "patient_id": 1},
            duplicate_counts=dict.fromkeys(INVARIANT_KEYS, 0),
        )
