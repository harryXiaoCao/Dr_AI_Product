"""Add governed care references and deterministic evaluation persistence.

Revision ID: 20260725_0040
Revises: 20260724_0039
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260725_0040"
down_revision = "20260724_0039"
branch_labels = None
depends_on = None


def _uuid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _timestamps() -> tuple[sa.Column, ...]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def upgrade() -> None:
    op.create_table(
        "governed_care_releases",
        _uuid("id"),
        sa.Column("release_type", sa.String(40), nullable=False),
        sa.Column("release_key", sa.String(160), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("lifecycle_status", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("jurisdiction", sa.String(40), nullable=False),
        sa.Column("region", sa.String(120)),
        sa.Column(
            "facility_scope_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("currency", sa.String(3)),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("source_authority", sa.String(240), nullable=False),
        sa.Column("source_locator", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("payload_checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "provenance_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "required_review_types_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("rights_status", sa.String(40), nullable=False),
        sa.Column("storage_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("derivation_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "redistribution_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "provider_transmission_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("last_verified_on", sa.Date()),
        sa.Column("next_review_on", sa.Date()),
        _uuid("supersedes_release_id", nullable=True),
        _uuid("created_by_user_id", nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_governed_care_release_effective_interval",
        ),
        sa.CheckConstraint(
            "next_review_on IS NULL OR last_verified_on IS NULL "
            "OR next_review_on >= last_verified_on",
            name="ck_governed_care_release_review_interval",
        ),
        sa.CheckConstraint(
            "source_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_governed_care_release_source_checksum",
        ),
        sa.CheckConstraint(
            "payload_checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_governed_care_release_payload_checksum",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(required_review_types_json) = 'array' "
            "AND jsonb_array_length(required_review_types_json) > 0",
            name="ck_governed_care_release_required_reviews",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "release_type",
            "release_key",
            "version",
            name="uq_governed_care_release_version",
        ),
    )
    op.create_index(
        "ix_governed_care_release_lookup",
        "governed_care_releases",
        ["release_type", "release_key", "jurisdiction"],
    )

    op.create_table(
        "governed_care_release_reviews",
        _uuid("id"),
        _uuid("release_id"),
        sa.Column("review_type", sa.String(60), nullable=False),
        sa.Column("decision", sa.String(40), nullable=False),
        _uuid("reviewer_user_id", nullable=True),
        sa.Column("reviewer_name", sa.String(160), nullable=False),
        sa.Column("reviewed_payload_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "release_id",
            "review_type",
            "reviewer_user_id",
            name="uq_governed_care_release_review",
        ),
    )
    op.create_index(
        "ix_governed_care_release_review_release",
        "governed_care_release_reviews",
        ["release_id", "review_type"],
    )

    op.create_table(
        "governed_care_release_activations",
        _uuid("id"),
        _uuid("release_id"),
        sa.Column("release_type", sa.String(40), nullable=False),
        sa.Column("release_key", sa.String(160), nullable=False),
        sa.Column("scope_key", sa.String(240), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        _uuid("prior_release_id", nullable=True),
        _uuid("actor_user_id", nullable=True),
        sa.Column("reason_code", sa.String(80), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["prior_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_governed_care_release_activation_scope",
        "governed_care_release_activations",
        ["release_type", "release_key", "scope_key", "created_at"],
    )

    op.create_table(
        "governed_active_care_releases",
        _uuid("id"),
        sa.Column("release_type", sa.String(40), nullable=False),
        sa.Column("release_key", sa.String(160), nullable=False),
        sa.Column("scope_key", sa.String(240), nullable=False),
        _uuid("release_id"),
        _uuid("activation_event_id"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["activation_event_id"],
            ["governed_care_release_activations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "release_type",
            "release_key",
            "scope_key",
            name="uq_governed_active_care_release_scope",
        ),
    )

    op.create_table(
        "care_scenario_definitions",
        _uuid("release_id"),
        sa.Column("scenario_family", sa.String(120), nullable=False),
        sa.Column("encounter_type", sa.String(120), nullable=False),
        sa.Column("applicability_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("required_inputs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "compatible_release_keys_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("release_id"),
    )
    op.create_table(
        "care_plans",
        _uuid("release_id"),
        _uuid("scenario_release_id"),
        sa.Column("pathway_code", sa.String(120), nullable=False),
        sa.Column(
            "assumptions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["scenario_release_id"],
            ["care_scenario_definitions.release_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("release_id"),
    )
    op.create_table(
        "care_plan_items",
        _uuid("id"),
        _uuid("care_plan_release_id"),
        sa.Column("item_key", sa.String(120), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("code_system", sa.String(80), nullable=False),
        sa.Column("service_code", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("quantity_low", sa.Integer(), nullable=False),
        sa.Column("quantity_high", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("comparison_semantics", sa.String(60), nullable=False, server_default="range"),
        sa.CheckConstraint("quantity_low > 0", name="ck_care_plan_item_quantity_low_positive"),
        sa.CheckConstraint(
            "quantity_high >= quantity_low", name="ck_care_plan_item_quantity_range"
        ),
        sa.ForeignKeyConstraint(
            ["care_plan_release_id"], ["care_plans.release_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("care_plan_release_id", "item_key", name="uq_care_plan_item_key"),
    )
    op.create_table(
        "pricing_reference_sets",
        _uuid("release_id"),
        sa.Column("price_type", sa.String(60), nullable=False),
        sa.Column("amount_semantics", sa.String(80), nullable=False),
        sa.Column("comparability", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("release_id"),
    )
    op.create_table(
        "pricing_reference_items",
        _uuid("id"),
        _uuid("pricing_reference_release_id"),
        sa.Column("code_system", sa.String(80), nullable=False),
        sa.Column("service_code", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("facility_scope_key", sa.String(160), nullable=False, server_default="*"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount_low_minor", sa.Integer(), nullable=False),
        sa.Column("amount_high_minor", sa.Integer(), nullable=False),
        sa.Column("economic_meaning", sa.String(120), nullable=False),
        sa.Column("confidential", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("amount_low_minor >= 0", name="ck_pricing_item_low_nonnegative"),
        sa.CheckConstraint(
            "amount_high_minor >= amount_low_minor",
            name="ck_pricing_item_amount_range",
        ),
        sa.ForeignKeyConstraint(
            ["pricing_reference_release_id"],
            ["pricing_reference_sets.release_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pricing_reference_release_id",
            "code_system",
            "service_code",
            "unit",
            "facility_scope_key",
            name="uq_pricing_reference_item_scope",
        ),
    )
    op.create_table(
        "utilization_rule_sets",
        _uuid("release_id"),
        _uuid("scenario_release_id"),
        sa.Column("rule_contract_version", sa.String(80), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["governed_care_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["scenario_release_id"],
            ["care_scenario_definitions.release_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("release_id"),
    )
    op.create_table(
        "utilization_rules",
        _uuid("id"),
        _uuid("utilization_rule_release_id"),
        sa.Column("rule_code", sa.String(120), nullable=False),
        sa.Column("rule_type", sa.String(60), nullable=False),
        sa.Column("parameters_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["utilization_rule_release_id"],
            ["utilization_rule_sets.release_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "utilization_rule_release_id",
            "rule_code",
            name="uq_utilization_rule_code",
        ),
    )
    op.create_table(
        "care_reference_evaluations",
        _uuid("id"),
        _uuid("prior_evaluation_id", nullable=True),
        _uuid("clinical_event_id", nullable=True),
        _uuid("payer_request_id", nullable=True),
        _uuid("scenario_release_id"),
        _uuid("care_plan_release_id"),
        _uuid("pricing_reference_release_id"),
        _uuid("utilization_rule_release_id"),
        sa.Column("engine_contract_version", sa.String(80), nullable=False),
        sa.Column("input_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("result_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(60), nullable=False),
        sa.Column("currency", sa.String(3)),
        sa.Column("total_low_minor", sa.Integer()),
        sa.Column("total_high_minor", sa.Integer()),
        sa.Column("observed_total_minor", sa.Integer()),
        sa.Column(
            "reason_codes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "missing_information_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("exception_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "suppression_reasons_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("input_facts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "total_low_minor IS NULL OR total_high_minor IS NULL "
            "OR total_high_minor >= total_low_minor",
            name="ck_care_reference_evaluation_total_range",
        ),
        sa.ForeignKeyConstraint(
            ["prior_evaluation_id"], ["care_reference_evaluations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
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
    )
    op.create_index(
        "ix_care_reference_evaluation_event_created",
        "care_reference_evaluations",
        ["clinical_event_id", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION guard_governed_care_release_content()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND OLD.lifecycle_status IN
                ('active', 'superseded', 'withdrawn') THEN
                RAISE EXCEPTION 'activated care releases are immutable';
            END IF;
            IF TG_OP = 'UPDATE' AND OLD.lifecycle_status IN
                ('active', 'superseded', 'withdrawn')
                AND (to_jsonb(NEW) - 'lifecycle_status')
                    IS DISTINCT FROM (to_jsonb(OLD) - 'lifecycle_status') THEN
                RAISE EXCEPTION 'activated care release content is immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_governed_care_release_content
        BEFORE UPDATE OR DELETE ON governed_care_releases
        FOR EACH ROW EXECUTE FUNCTION guard_governed_care_release_content()
        """
    )
    op.execute(
        """
        CREATE FUNCTION guard_activated_care_release_child()
        RETURNS trigger AS $$
        DECLARE
            release_uuid uuid;
            release_state text;
        BEGIN
            release_uuid := ((CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD)
                                   ELSE to_jsonb(NEW) END) ->> TG_ARGV[0])::uuid;
            SELECT lifecycle_status INTO release_state
            FROM governed_care_releases WHERE id = release_uuid;
            IF release_state IN ('active', 'superseded', 'withdrawn') THEN
                RAISE EXCEPTION 'activated care release children are immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table, release_column in (
        ("care_scenario_definitions", "release_id"),
        ("care_plans", "release_id"),
        ("care_plan_items", "care_plan_release_id"),
        ("pricing_reference_sets", "release_id"),
        ("pricing_reference_items", "pricing_reference_release_id"),
        ("utilization_rule_sets", "release_id"),
        ("utilization_rules", "utilization_rule_release_id"),
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_immutable
            BEFORE INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION
                guard_activated_care_release_child('{release_column}')
            """
        )
    op.execute(
        """
        CREATE FUNCTION guard_append_only_care_record()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in (
        "governed_care_release_reviews",
        "governed_care_release_activations",
        "care_reference_evaluations",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_append_only
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()
            """
        )


def downgrade() -> None:
    for table in (
        "care_reference_evaluations",
        "utilization_rules",
        "utilization_rule_sets",
        "pricing_reference_items",
        "pricing_reference_sets",
        "care_plan_items",
        "care_plans",
        "care_scenario_definitions",
        "governed_active_care_releases",
        "governed_care_release_activations",
        "governed_care_release_reviews",
        "governed_care_releases",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION guard_append_only_care_record()")
    op.execute("DROP FUNCTION guard_activated_care_release_child()")
    op.execute("DROP FUNCTION guard_governed_care_release_content()")
