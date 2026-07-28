"""Add immutable doctor reviews and versioned expected-care envelopes.

Revision ID: 20260726_0042
Revises: 20260725_0041
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260726_0042"
down_revision = "20260725_0041"
branch_labels = None
depends_on = None


def _uuid(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    op.create_table(
        "expected_care_review_heads",
        _uuid("candidate_result_id"),
        _uuid("current_envelope_id", True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "lifecycle_state",
            sa.String(60),
            nullable=False,
            server_default="generated_pending_review",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("version >= 0", name="ck_expected_care_review_head_version"),
        sa.ForeignKeyConstraint(
            ["candidate_result_id"], ["expected_care_candidate_results.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("candidate_result_id"),
    )
    op.create_table(
        "expected_care_doctor_reviews",
        _uuid("id"),
        _uuid("candidate_result_id"),
        _uuid("actor_user_id"),
        _uuid("doctor_id"),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("payer_request_id", True),
        _uuid("predecessor_envelope_id", True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("accepted_head_version", sa.Integer(), nullable=False),
        sa.Column("resulting_head_version", sa.Integer(), nullable=False),
        sa.Column("deterministic_engine_contract_version", sa.String(80), nullable=False),
        sa.Column("deterministic_input_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("deterministic_result_checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "deterministic_validation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "release_lineage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reviewer_only_note", sa.Text()),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["candidate_result_id"], ["expected_care_candidate_results.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_user_id",
            "clinical_event_id",
            "idempotency_key",
            name="uq_expected_care_doctor_review_idempotency",
        ),
    )
    op.create_index(
        "ix_expected_care_doctor_review_candidate_created",
        "expected_care_doctor_reviews",
        ["candidate_result_id", "created_at"],
    )
    op.create_table(
        "expected_care_reviewed_envelopes",
        _uuid("id"),
        _uuid("candidate_result_id"),
        _uuid("doctor_review_id"),
        _uuid("predecessor_envelope_id", True),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("payer_request_id", True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("candidate_output_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("model_configuration_version", sa.String(80), nullable=False),
        _uuid("scenario_release_id"),
        _uuid("care_plan_release_id"),
        _uuid("pricing_reference_release_id"),
        _uuid("utilization_rule_release_id"),
        sa.Column(
            "release_lineage_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "amount_type",
            sa.String(60),
            nullable=False,
            server_default="reference_range",
        ),
        sa.Column("total_low_minor", sa.Integer(), nullable=False),
        sa.Column("total_high_minor", sa.Integer(), nullable=False),
        sa.Column(
            "assumptions_json",
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
        sa.Column(
            "limitations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "structured_difference_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        _created_at(),
        sa.CheckConstraint(
            "total_low_minor >= 0 AND total_high_minor >= total_low_minor",
            name="ck_expected_care_envelope_total_range",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_result_id"], ["expected_care_candidate_results.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["doctor_review_id"], ["expected_care_doctor_reviews.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_envelope_id"],
            ["expected_care_reviewed_envelopes.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["scenario_release_id"], ["care_scenario_definitions.release_id"], ondelete="RESTRICT"
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
        sa.UniqueConstraint("doctor_review_id", name="uq_expected_care_envelope_review"),
        sa.UniqueConstraint(
            "candidate_result_id",
            "version",
            name="uq_expected_care_envelope_candidate_version",
        ),
    )
    op.create_foreign_key(
        "fk_expected_care_review_head_current_envelope",
        "expected_care_review_heads",
        "expected_care_reviewed_envelopes",
        ["current_envelope_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "expected_care_envelope_items",
        _uuid("id"),
        _uuid("envelope_id"),
        sa.Column("item_key", sa.String(240), nullable=False),
        sa.Column("category", sa.String(240), nullable=False),
        sa.Column("code_system", sa.String(120), nullable=False),
        sa.Column("service_code", sa.String(160), nullable=False),
        sa.Column("unit", sa.String(120), nullable=False),
        sa.Column("quantity_low", sa.Integer(), nullable=False),
        sa.Column("quantity_high", sa.Integer(), nullable=False),
        sa.Column("amount_low_minor", sa.Integer(), nullable=False),
        sa.Column("amount_high_minor", sa.Integer(), nullable=False),
        _uuid("pricing_reference_item_id"),
        _uuid("utilization_rule_id"),
        _created_at(),
        sa.CheckConstraint(
            "quantity_low >= 1 AND quantity_high >= quantity_low",
            name="ck_expected_care_envelope_item_quantity",
        ),
        sa.CheckConstraint(
            "amount_low_minor >= 0 AND amount_high_minor >= amount_low_minor",
            name="ck_expected_care_envelope_item_amount",
        ),
        sa.ForeignKeyConstraint(
            ["envelope_id"], ["expected_care_reviewed_envelopes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["pricing_reference_item_id"], ["pricing_reference_items.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["utilization_rule_id"], ["utilization_rules.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("envelope_id", "item_key", name="uq_expected_care_envelope_item"),
    )
    op.create_table(
        "expected_care_clinical_rationales",
        _uuid("id"),
        _uuid("doctor_review_id"),
        _uuid("envelope_id", True),
        sa.Column("exception_code", sa.String(120), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("patient_safe_summary", sa.Text()),
        sa.Column(
            "applies_to_item_keys_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["doctor_review_id"], ["expected_care_doctor_reviews.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["envelope_id"], ["expected_care_reviewed_envelopes.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expected_care_rationale_review",
        "expected_care_clinical_rationales",
        ["doctor_review_id", "created_at"],
    )
    op.create_table(
        "expected_care_lifecycle_events",
        _uuid("id"),
        _uuid("candidate_result_id"),
        _uuid("doctor_review_id", True),
        _uuid("envelope_id", True),
        _uuid("actor_user_id"),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["candidate_result_id"], ["expected_care_candidate_results.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["doctor_review_id"], ["expected_care_doctor_reviews.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["envelope_id"], ["expected_care_reviewed_envelopes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expected_care_lifecycle_candidate_created",
        "expected_care_lifecycle_events",
        ["candidate_result_id", "created_at"],
    )

    for table in (
        "expected_care_doctor_reviews",
        "expected_care_reviewed_envelopes",
        "expected_care_envelope_items",
        "expected_care_clinical_rationales",
        "expected_care_lifecycle_events",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only "
            f"BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()"
        )


def downgrade() -> None:
    op.drop_table("expected_care_lifecycle_events")
    op.drop_table("expected_care_clinical_rationales")
    op.drop_table("expected_care_envelope_items")
    op.execute(
        "ALTER TABLE expected_care_doctor_reviews "
        "DROP CONSTRAINT IF EXISTS fk_expected_care_doctor_review_predecessor_envelope"
    )
    op.drop_constraint(
        "fk_expected_care_review_head_current_envelope",
        "expected_care_review_heads",
        type_="foreignkey",
    )
    op.drop_table("expected_care_reviewed_envelopes")
    op.drop_table("expected_care_doctor_reviews")
    op.drop_table("expected_care_review_heads")
