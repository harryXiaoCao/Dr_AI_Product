"""Content-free helpers for bounded Phase 7 operational rehearsals.

This module does not connect to staging, execute shell commands, mutate a
database, or expose configuration values. It provides deterministic inventory,
preview, invariant, and campaign contracts for separately authorized tooling.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

PRESENCE_STATES = frozenset({"set", "empty", "absent"})
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
HOST_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{2,252}$")
DATABASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,62}$")
BACKUP_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[a-z0-9._-]{3,80}$")

SENSITIVE_FILE_SUFFIXES = frozenset(
    {".jks", ".keystore", ".mobileprovision", ".p12", ".p8", ".pem"}
)
SECRET_NAME_MARKERS = (
    "api_key",
    "app_secret",
    "auth_token",
    "database_url",
    "jwt_secret",
    "password",
    "private_key",
    "refresh_token",
    "subscription",
)

RECOVERY_INVARIANT_KEYS = frozenset(
    {
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
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_safe_path(root: Path, path: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("inventory_path_outside_root") from exc
    lowered_name = resolved_path.name.lower()
    if (
        resolved_path.suffix.lower() in SENSITIVE_FILE_SUFFIXES
        or lowered_name == ".env"
        or any(marker in lowered_name for marker in SECRET_NAME_MARKERS)
    ):
        raise ValueError("sensitive_inventory_path_rejected")
    return relative


def build_file_inventory(root: Path, paths: Sequence[Path]) -> list[dict[str, object]]:
    """Return path, size, and checksum only for explicitly selected safe files."""

    inventory: list[dict[str, object]] = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        relative = _relative_safe_path(root, path)
        if not path.is_file():
            raise ValueError("inventory_path_not_file")
        inventory.append(
            {
                "path": relative.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return inventory


def presence_states(
    names: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
    env_file: Path | None = None,
) -> dict[str, str]:
    """Report only set, empty, or absent for allow-listed configuration names."""

    if environment is not None and env_file is not None:
        raise ValueError("choose_environment_or_env_file")
    values: dict[str, str] = {}
    if environment is not None:
        values = {name: environment[name] for name in names if name in environment}
    elif env_file is not None and env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            normalized_name = name.strip()
            if normalized_name in names:
                values[normalized_name] = value.strip()
    return {
        name: "set" if values.get(name) else ("empty" if name in values else "absent")
        for name in sorted(set(names))
    }


@dataclass(frozen=True)
class PresenceScanResult:
    files_scanned: int
    suspected_match_count: int
    passed: bool


def scan_sensitive_pattern_presence(
    paths: Sequence[Path],
    patterns: Sequence[re.Pattern[str]],
) -> PresenceScanResult:
    """Count suspected pattern matches without returning lines or matched values."""

    files_scanned = 0
    suspected_match_count = 0
    for path in paths:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        files_scanned += 1
        suspected_match_count += sum(
            1 for pattern in patterns for _match in pattern.finditer(content)
        )
    return PresenceScanResult(
        files_scanned=files_scanned,
        suspected_match_count=suspected_match_count,
        passed=suspected_match_count == 0,
    )


@dataclass(frozen=True)
class StagingTarget:
    host: str
    deployment_dir: str
    live_database: str
    environment: str = "staging"

    def validate(self) -> None:
        if self.environment != "staging":
            raise ValueError("target_environment_must_be_staging")
        if not HOST_PATTERN.fullmatch(self.host):
            raise ValueError("invalid_explicit_host")
        path = PurePosixPath(self.deployment_dir)
        if not path.is_absolute() or len(path.parts) < 5:
            raise ValueError("deployment_dir_must_be_narrow_absolute_path")
        if path in {
            PurePosixPath("/"),
            PurePosixPath("/home"),
            PurePosixPath("/home/ubuntu"),
            PurePosixPath("/home/ubuntu/dr-ai"),
        }:
            raise ValueError("deployment_dir_too_broad")
        if not DATABASE_PATTERN.fullmatch(self.live_database) or "staging" not in (
            self.live_database
        ):
            raise ValueError("live_database_must_be_explicit_staging_database")


class OperationAction(StrEnum):
    BACKUP = "backup"
    RESTORE_REHEARSAL = "restore_rehearsal"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class OperationPreview:
    schema_version: str
    preview_only: bool
    action: str
    target: dict[str, str]
    checks: tuple[str, ...]
    artifacts: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_operation_preview(
    action: OperationAction,
    target: StagingTarget,
    *,
    backup_id: str,
    backup_manifest_sha256: str | None = None,
    restore_database: str | None = None,
    predecessor_api_digest: str | None = None,
    predecessor_web_sha256: str | None = None,
) -> OperationPreview:
    """Build a non-executable, exact-target operation plan."""

    target.validate()
    if not BACKUP_ID_PATTERN.fullmatch(backup_id):
        raise ValueError("invalid_backup_id")
    backup_dir = f"{target.deployment_dir}/backups/{backup_id}"
    artifacts = {"backup_id": backup_id, "backup_dir": backup_dir}
    checks = (
        "resolve_exact_target",
        "verify_staging_boundary",
        "verify_content_free_evidence",
    )
    if action is OperationAction.BACKUP:
        checks += (
            "capture_deployment_identity",
            "create_host_only_custom_dump",
            "checksum_every_backup_artifact",
            "verify_custom_dump_catalog",
        )
    elif action is OperationAction.RESTORE_REHEARSAL:
        if not backup_manifest_sha256 or not SHA256_PATTERN.fullmatch(backup_manifest_sha256):
            raise ValueError("restore_requires_manifest_sha256")
        if (
            not restore_database
            or not DATABASE_PATTERN.fullmatch(restore_database)
            or not restore_database.startswith("dr_ai_phase7_restore_")
            or restore_database == target.live_database
        ):
            raise ValueError("restore_requires_isolated_disposable_database")
        artifacts.update(
            {
                "backup_manifest_sha256": backup_manifest_sha256,
                "restore_database": restore_database,
            }
        )
        checks += (
            "create_fresh_isolated_database",
            "restore_without_live_database_mutation",
            "verify_schema_and_content_free_invariants",
            "run_bounded_smoke_against_restored_target",
        )
    elif action is OperationAction.ROLLBACK:
        if not predecessor_api_digest or not SHA256_PATTERN.fullmatch(predecessor_api_digest):
            raise ValueError("rollback_requires_exact_api_digest")
        if not predecessor_web_sha256 or not SHA256_PATTERN.fullmatch(predecessor_web_sha256):
            raise ValueError("rollback_requires_exact_web_checksum")
        artifacts.update(
            {
                "predecessor_api_digest": predecessor_api_digest,
                "predecessor_web_sha256": predecessor_web_sha256,
            }
        )
        checks += (
            "verify_predecessor_schema_compatibility",
            "restore_exact_api_and_web_predecessors",
            "verify_health_smoke_and_invariants",
            "record_rollback_completion",
        )
    else:
        raise ValueError("unsupported_operation_action")
    return OperationPreview(
        schema_version="phase7-operation-preview-v1",
        preview_only=True,
        action=action.value,
        target={
            "environment": target.environment,
            "host": target.host,
            "deployment_dir": target.deployment_dir,
            "live_database": target.live_database,
        },
        checks=checks,
        artifacts=artifacts,
    )


@dataclass(frozen=True)
class InvariantSnapshot:
    row_counts: dict[str, int]
    duplicate_counts: dict[str, int]

    @classmethod
    def validate(
        cls,
        *,
        row_counts: Mapping[str, int],
        duplicate_counts: Mapping[str, int],
    ) -> InvariantSnapshot:
        all_keys = set(row_counts) | set(duplicate_counts)
        if not all_keys <= RECOVERY_INVARIANT_KEYS:
            raise ValueError("unknown_or_identity_bearing_invariant")
        if set(row_counts) != RECOVERY_INVARIANT_KEYS:
            raise ValueError("incomplete_recovery_row_counts")
        if set(duplicate_counts) != RECOVERY_INVARIANT_KEYS:
            raise ValueError("incomplete_recovery_duplicate_counts")
        if any(
            type(value) is not int or value < 0
            for value in (*row_counts.values(), *duplicate_counts.values())
        ):
            raise ValueError("invariant_counts_must_be_non_negative_integers")
        return cls(dict(row_counts), dict(duplicate_counts))


@dataclass(frozen=True)
class InvariantResult:
    passed: bool
    failed_categories: tuple[str, ...]
    row_deltas: dict[str, int]


def verify_recovery_invariants(
    before: InvariantSnapshot,
    after: InvariantSnapshot,
    *,
    allowed_row_deltas: Mapping[str, int] | None = None,
) -> InvariantResult:
    allowed = dict(allowed_row_deltas or {})
    if not set(allowed) <= RECOVERY_INVARIANT_KEYS:
        raise ValueError("unknown_allowed_delta_category")
    failed: list[str] = []
    row_deltas: dict[str, int] = {}
    for key in sorted(RECOVERY_INVARIANT_KEYS):
        delta = after.row_counts[key] - before.row_counts[key]
        row_deltas[key] = delta
        if delta != allowed.get(key, 0) or after.duplicate_counts[key] != 0:
            failed.append(key)
    return InvariantResult(
        passed=not failed,
        failed_categories=tuple(failed),
        row_deltas=row_deltas,
    )


class FaultCase(StrEnum):
    PROVIDER_OUTAGE = "provider_outage"
    REVOKED_PROVIDER_CREDENTIAL = "revoked_provider_credential"
    RELEASE_CHECKSUM_DRIFT = "release_checksum_drift"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    MALFORMED_MODEL_OUTPUT = "malformed_model_output"
    PROVIDER_TIMEOUT = "provider_timeout"
    QUOTA_EXHAUSTION = "quota_exhaustion"
    CONCURRENT_AI_REQUESTS = "concurrent_ai_requests"
    CONCURRENT_NOTIFICATION_WORKERS = "concurrent_notification_workers"
    DUPLICATE_SCHEDULER = "duplicate_scheduler"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    OPTIMISTIC_VERSION_CONFLICT = "optimistic_version_conflict"
    ADVISORY_LOCK_CONTENTION = "advisory_lock_contention"
    DATABASE_CONTENTION = "database_contention"
    INTERRUPTED_MIGRATION = "interrupted_migration"
    INTERRUPTED_DEPLOYMENT = "interrupted_deployment"
    NOTIFICATION_DELIVERY_FAILURE = "notification_delivery_failure"
    ENDPOINT_ROTATION_DURING_DELIVERY = "endpoint_rotation_during_delivery"
    CANCELLATION_DURING_DELIVERY = "cancellation_during_delivery"
    BACKUP_RESTORATION = "backup_restoration"
    API_ROLLBACK = "api_rollback"
    FLUTTER_WEB_ROLLBACK = "flutter_web_rollback"
    AI_KILL_SWITCH = "ai_kill_switch"
    EXACT_PREDECESSOR_RECOVERY = "exact_predecessor_recovery"
    PARTIAL_SERVICE_RECOVERY = "partial_service_recovery"


class CampaignStage(StrEnum):
    PLANNED = "planned"
    INJECTED = "injected"
    CONTAINED = "contained"
    RECOVERED = "recovered"
    VERIFIED = "verified"


ALLOWED_CAMPAIGN_RESULTS = frozenset(
    {
        "control_planned",
        "fallback_observed",
        "fault_observed",
        "invariants_passed",
        "kill_switch_engaged",
        "recovery_completed",
        "rollback_completed",
    }
)
NEXT_CAMPAIGN_STAGE = {
    CampaignStage.PLANNED: CampaignStage.INJECTED,
    CampaignStage.INJECTED: CampaignStage.CONTAINED,
    CampaignStage.CONTAINED: CampaignStage.RECOVERED,
    CampaignStage.RECOVERED: CampaignStage.VERIFIED,
}


@dataclass(frozen=True)
class CampaignEvent:
    sequence: int
    fault_case: str
    stage: str
    result_code: str


class FaultCampaign:
    """In-memory, content-free state machine for deterministic fault rehearsals."""

    def __init__(self, cases: Sequence[FaultCase]) -> None:
        if not cases or len(set(cases)) != len(cases):
            raise ValueError("fault_campaign_requires_unique_cases")
        self._stages = {case: CampaignStage.PLANNED for case in cases}
        self._events = [
            CampaignEvent(
                sequence=index,
                fault_case=case.value,
                stage=CampaignStage.PLANNED.value,
                result_code="control_planned",
            )
            for index, case in enumerate(cases, start=1)
        ]

    @property
    def events(self) -> tuple[CampaignEvent, ...]:
        return tuple(self._events)

    def stage(self, fault_case: FaultCase) -> CampaignStage:
        if fault_case not in self._stages:
            raise ValueError("fault_case_not_in_campaign")
        return self._stages[fault_case]

    def transition(
        self,
        fault_case: FaultCase,
        stage: CampaignStage,
        *,
        result_code: str,
    ) -> CampaignEvent:
        current = self.stage(fault_case)
        if result_code not in ALLOWED_CAMPAIGN_RESULTS:
            raise ValueError("content_bearing_or_unknown_result_code")
        if stage == current:
            existing = next(
                event
                for event in reversed(self._events)
                if event.fault_case == fault_case.value and event.stage == stage.value
            )
            if existing.result_code != result_code:
                raise ValueError("campaign_idempotency_content_conflict")
            return existing
        if NEXT_CAMPAIGN_STAGE.get(current) != stage:
            raise ValueError("invalid_campaign_transition")
        event = CampaignEvent(
            sequence=len(self._events) + 1,
            fault_case=fault_case.value,
            stage=stage.value,
            result_code=result_code,
        )
        self._stages[fault_case] = stage
        self._events.append(event)
        return event


def default_fault_campaign() -> FaultCampaign:
    return FaultCampaign(list(FaultCase))
