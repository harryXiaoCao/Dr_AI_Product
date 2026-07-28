"""Add immutable expected-care candidate request, attempt, and result records.

Revision ID: 20260725_0041
Revises: 20260725_0040
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260725_0041"
down_revision = "20260725_0040"
branch_labels = None
depends_on = None


def _uuid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "expected_care_candidate_requests",
        _uuid("id"),
        _uuid("actor_user_id"),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("payer_request_id", nullable=True),
        _uuid("predecessor_request_id", nullable=True),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("model_configuration_version", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        _uuid("scenario_release_id"),
        _uuid("care_plan_release_id"),
        _uuid("pricing_reference_release_id"),
        _uuid("utilization_rule_release_id"),
        sa.Column("release_lineage_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("minimum_input_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("minimum_input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_outcome", sa.String(60), nullable=False),
        sa.Column(
            "validation_reason_codes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("output_checksum_sha256", sa.String(64)),
        sa.Column("provider_attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_input_tokens", sa.Integer()),
        sa.Column("provider_output_tokens", sa.Integer()),
        sa.Column("provider_cost_microunits", sa.Integer()),
        _created_at(),
        sa.CheckConstraint(
            "request_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_expected_care_candidate_request_checksum",
        ),
        sa.CheckConstraint(
            "minimum_input_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_expected_care_candidate_input_checksum",
        ),
        sa.CheckConstraint(
            "output_checksum_sha256 IS NULL OR output_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_expected_care_candidate_output_checksum",
        ),
        sa.CheckConstraint(
            "provider_attempt_count >= 0 AND provider_attempt_count <= 2",
            name="ck_expected_care_candidate_attempt_bound",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["predecessor_request_id"],
            ["expected_care_candidate_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_release_id"],
            ["care_scenario_definitions.release_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["care_plan_release_id"], ["care_plans.release_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["pricing_reference_release_id"],
            ["pricing_reference_sets.release_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilization_rule_release_id"],
            ["utilization_rule_sets.release_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_user_id",
            "clinical_event_id",
            "idempotency_key",
            name="uq_expected_care_candidate_request_idempotency",
        ),
    )
    op.create_index(
        "ix_expected_care_candidate_request_event_created",
        "expected_care_candidate_requests",
        ["clinical_event_id", "created_at"],
    )

    op.create_table(
        "expected_care_candidate_attempts",
        _uuid("id"),
        _uuid("candidate_request_id"),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("outcome", sa.String(60), nullable=False),
        sa.Column("diagnostic_code", sa.String(120)),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_microunits", sa.Integer()),
        sa.Column("output_checksum_sha256", sa.String(64)),
        _created_at(),
        sa.CheckConstraint(
            "attempt_number >= 1 AND attempt_number <= 2",
            name="ck_expected_care_candidate_attempt_number",
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name="ck_expected_care_candidate_attempt_latency",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_request_id"],
            ["expected_care_candidate_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_request_id",
            "attempt_number",
            name="uq_expected_care_candidate_attempt_number",
        ),
    )
    op.create_index(
        "ix_expected_care_candidate_attempt_request",
        "expected_care_candidate_attempts",
        ["candidate_request_id", "attempt_number"],
    )

    op.create_table(
        "expected_care_candidate_results",
        _uuid("id"),
        _uuid("candidate_request_id"),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("output_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("deterministic_result_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("deterministic_engine_contract_version", sa.String(80), nullable=False),
        sa.Column("currency", sa.String(3)),
        sa.Column("total_low_minor", sa.Integer()),
        sa.Column("total_high_minor", sa.Integer()),
        sa.Column("candidate_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        _created_at(),
        sa.CheckConstraint(
            "total_low_minor IS NULL OR total_high_minor IS NULL "
            "OR total_high_minor >= total_low_minor",
            name="ck_expected_care_candidate_total_range",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_request_id"],
            ["expected_care_candidate_requests.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_request_id",
            name="uq_expected_care_candidate_result_request",
        ),
    )

    for table in (
        "expected_care_candidate_requests",
        "expected_care_candidate_attempts",
        "expected_care_candidate_results",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_append_only
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()
            """
        )


def downgrade() -> None:
    op.drop_table("expected_care_candidate_results")
    op.drop_table("expected_care_candidate_attempts")
    op.drop_index(
        "ix_expected_care_candidate_request_event_created",
        table_name="expected_care_candidate_requests",
    )
    op.drop_table("expected_care_candidate_requests")
