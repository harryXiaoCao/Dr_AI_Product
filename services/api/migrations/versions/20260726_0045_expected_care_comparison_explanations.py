"""Add deterministic comparisons, validated explanations, and governed releases.

Revision ID: 20260726_0045
Revises: 20260726_0044
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260726_0045"
down_revision = "20260726_0044"
branch_labels = None
depends_on = None


def _uuid(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _json(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), nullable=nullable)


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    op.create_table(
        "expected_care_comparisons",
        _uuid("id"),
        _uuid("predecessor_comparison_id", True),
        _uuid("baseline_id"),
        _uuid("actor_user_id"),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("payer_request_id", True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("input_snapshot_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("result_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("baseline_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("delivered_snapshot_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("submitted_snapshot_checksum_sha256", sa.String(64)),
        _json("reference_release_checksums_json"),
        sa.Column("comparison_contract_version", sa.String(80), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("baseline_total_low_minor", sa.Integer(), nullable=False),
        sa.Column("baseline_total_high_minor", sa.Integer(), nullable=False),
        sa.Column("delivered_total_minor", sa.Integer()),
        sa.Column("submitted_total_minor", sa.Integer()),
        sa.Column("delivered_total_label", sa.String(60), nullable=False),
        sa.Column("submitted_total_label", sa.String(60)),
        _json("input_snapshot_json"),
        _json("result_json"),
        _json("structured_difference_json"),
        _created_at(),
        sa.CheckConstraint(
            "baseline_total_low_minor >= 0 AND "
            "baseline_total_high_minor >= baseline_total_low_minor",
            name="ck_expected_care_comparison_baseline_range",
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_comparison_id"], ["expected_care_comparisons.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["baseline_id"], ["expected_care_reviewed_envelopes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "baseline_id",
            "payer_request_id",
            "version",
            name="uq_expected_care_comparison_scope_version",
        ),
        sa.UniqueConstraint(
            "actor_user_id",
            "clinical_event_id",
            "idempotency_key",
            name="uq_expected_care_comparison_idempotency",
        ),
    )
    op.create_index(
        "ix_expected_care_comparison_scope_created",
        "expected_care_comparisons",
        ["clinical_event_id", "created_at"],
    )
    op.create_index(
        "uq_expected_care_comparison_delivered_scope_version",
        "expected_care_comparisons",
        ["baseline_id", "version"],
        unique=True,
        postgresql_where=sa.text("payer_request_id IS NULL"),
    )
    op.create_table(
        "expected_care_comparison_items",
        _uuid("id"),
        _uuid("comparison_id"),
        _uuid("baseline_item_id"),
        _uuid("clinical_service_id", True),
        _uuid("care_cost_item_id", True),
        _uuid("payer_request_line_id", True),
        sa.Column("item_key", sa.String(240), nullable=False),
        sa.Column("service_code", sa.String(160), nullable=False),
        sa.Column("unit", sa.String(120), nullable=False),
        sa.Column("baseline_quantity_low", sa.Integer(), nullable=False),
        sa.Column("baseline_quantity_high", sa.Integer(), nullable=False),
        sa.Column("delivered_quantity", sa.Integer()),
        sa.Column("baseline_amount_low_minor", sa.Integer(), nullable=False),
        sa.Column("baseline_amount_high_minor", sa.Integer(), nullable=False),
        sa.Column("delivered_amount_minor", sa.Integer()),
        sa.Column("submitted_amount_minor", sa.Integer()),
        sa.Column("delivered_label", sa.String(60), nullable=False),
        sa.Column("submitted_label", sa.String(60)),
        _json("fact_snapshot_json"),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["expected_care_comparisons.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["baseline_item_id"], ["expected_care_envelope_items.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["clinical_service_id"], ["clinical_services.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["care_cost_item_id"], ["care_cost_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["payer_request_line_id"], ["payer_request_lines.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "comparison_id",
            "baseline_item_id",
            name="uq_expected_care_comparison_item",
        ),
    )
    op.create_index(
        "ix_expected_care_comparison_item_comparison",
        "expected_care_comparison_items",
        ["comparison_id"],
    )
    op.create_table(
        "expected_care_comparison_events",
        _uuid("id"),
        _uuid("comparison_id"),
        _uuid("actor_user_id"),
        sa.Column("event_type", sa.String(60), nullable=False),
        _json("metadata_json"),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["expected_care_comparisons.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expected_care_comparison_event_created",
        "expected_care_comparison_events",
        ["comparison_id", "created_at"],
    )
    op.create_table(
        "expected_care_explanation_requests",
        _uuid("id"),
        _uuid("comparison_id"),
        _uuid("actor_user_id"),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("payer_request_id", True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("fact_object_checksum_sha256", sa.String(64), nullable=False),
        _json("fact_object_json"),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("model_configuration_version", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["expected_care_comparisons.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_user_id",
            "comparison_id",
            "role",
            "locale",
            "idempotency_key",
            name="uq_expected_care_explanation_idempotency",
        ),
    )
    op.create_index(
        "ix_expected_care_explanation_scope_created",
        "expected_care_explanation_requests",
        ["comparison_id", "role", "created_at"],
    )
    op.create_table(
        "expected_care_explanation_attempts",
        _uuid("id"),
        _uuid("explanation_request_id"),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(60), nullable=False),
        sa.Column("diagnostic_code", sa.String(120)),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_microunits", sa.Integer()),
        sa.Column("artifact_checksum_sha256", sa.String(64)),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["explanation_request_id"],
            ["expected_care_explanation_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "explanation_request_id",
            "attempt_number",
            name="uq_expected_care_explanation_attempt",
        ),
    )
    op.create_table(
        "expected_care_explanation_artifacts",
        _uuid("id"),
        _uuid("explanation_request_id"),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("display_mode", sa.String(40), nullable=False),
        sa.Column("generated_artifact_checksum_sha256", sa.String(64)),
        sa.Column("validation_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("configuration_lineage_checksum_sha256", sa.String(64), nullable=False),
        _json("validation_json"),
        _json("display_artifact_json"),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["explanation_request_id"],
            ["expected_care_explanation_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "explanation_request_id",
            name="uq_expected_care_explanation_artifact_request",
        ),
    )
    op.create_table(
        "expected_care_explanation_releases",
        _uuid("id"),
        _uuid("predecessor_release_id", True),
        _uuid("rollback_target_release_id", True),
        sa.Column("release_key", sa.String(120), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("model_configuration_version", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        _json("source_checksums_json"),
        sa.Column("evaluation_manifest_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("evaluation_result_checksum_sha256", sa.String(64), nullable=False),
        _json("review_requirements_json"),
        _json("machine_gates_json"),
        sa.Column("activation_state", sa.String(60), nullable=False),
        sa.Column("kill_switch_state", sa.String(40), nullable=False),
        _uuid("created_by_user_id", True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["predecessor_release_id"],
            ["expected_care_explanation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["rollback_target_release_id"],
            ["expected_care_explanation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_key", "version", name="uq_expected_care_explanation_release"),
    )
    op.create_table(
        "expected_care_explanation_release_events",
        _uuid("id"),
        _uuid("release_id"),
        _uuid("actor_user_id", True),
        sa.Column("event_type", sa.String(60), nullable=False),
        _json("evidence_json"),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["release_id"], ["expected_care_explanation_releases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expected_care_explanation_release_event",
        "expected_care_explanation_release_events",
        ["release_id", "created_at"],
    )
    for table in (
        "payer_request_lines",
        "expected_care_comparisons",
        "expected_care_comparison_items",
        "expected_care_comparison_events",
        "expected_care_explanation_requests",
        "expected_care_explanation_attempts",
        "expected_care_explanation_artifacts",
        "expected_care_explanation_releases",
        "expected_care_explanation_release_events",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only "
            f"BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()"
        )


def downgrade() -> None:
    for table in (
        "expected_care_explanation_release_events",
        "expected_care_explanation_releases",
        "expected_care_explanation_artifacts",
        "expected_care_explanation_attempts",
        "expected_care_explanation_requests",
        "expected_care_comparison_events",
        "expected_care_comparison_items",
        "expected_care_comparisons",
    ):
        op.drop_table(table)
    op.execute("DROP TRIGGER trg_payer_request_lines_append_only ON payer_request_lines")
