"""Add transparent care-cost items and organization-scoped payer review.

Revision ID: 20260723_0035
Revises: 20260720_0034
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0035"
down_revision: str | None = "20260720_0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'payer'")

    op.create_table(
        "payer_organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("organization_type", sa.String(40), nullable=False),
        sa.Column("jurisdiction_code", sa.String(40), nullable=False),
        sa.Column("verification_status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_payer_organizations_name"),
    )
    op.create_index("ix_payer_organizations_name", "payer_organizations", ["name"])

    op.create_table(
        "payer_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payer_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("scope", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("payer_organization_id", "user_id", name="uq_payer_membership_user"),
    )
    op.create_index("ix_payer_membership_user_status", "payer_memberships", ["user_id", "status"])

    op.create_table(
        "care_cost_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "clinical_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(60), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("actual_cost_minor", sa.Integer(), nullable=False),
        sa.Column("payer_requested_minor", sa.Integer(), nullable=False),
        sa.Column("patient_responsibility_minor", sa.Integer(), nullable=False),
        sa.Column("ai_review_score", sa.Integer()),
        sa.Column("ai_review_status", sa.String(40), nullable=False),
        sa.Column("ai_review_summary", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_care_cost_item_quantity"),
        sa.CheckConstraint("actual_cost_minor >= 0", name="ck_care_cost_item_actual"),
        sa.CheckConstraint("payer_requested_minor >= 0", name="ck_care_cost_item_requested"),
        sa.CheckConstraint("patient_responsibility_minor >= 0", name="ck_care_cost_item_patient"),
        sa.CheckConstraint(
            "ai_review_score IS NULL OR ai_review_score BETWEEN 0 AND 100",
            name="ck_care_cost_item_ai_score",
        ),
    )
    op.create_index(
        "ix_care_cost_items_event_service_date",
        "care_cost_items",
        ["clinical_event_id", "service_date"],
    )
    op.create_index(
        "ix_care_cost_items_patient_created", "care_cost_items", ["patient_id", "created_at"]
    )

    op.create_table(
        "payer_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinical_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payer_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("requested_total_minor", sa.Integer(), nullable=False),
        sa.Column("doctor_summary", sa.Text(), nullable=False),
        sa.Column("ai_review_status", sa.String(40), nullable=False),
        sa.Column("ai_review_score", sa.Integer()),
        sa.Column("ai_review_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("requested_total_minor >= 0", name="ck_payer_request_total"),
        sa.CheckConstraint(
            "ai_review_score IS NULL OR ai_review_score BETWEEN 0 AND 100",
            name="ck_payer_request_ai_score",
        ),
    )
    op.create_index(
        "ix_payer_requests_organization_status",
        "payer_requests",
        ["payer_organization_id", "status"],
    )
    op.create_index(
        "ix_payer_requests_doctor_created", "payer_requests", ["doctor_id", "created_at"]
    )

    op.create_table(
        "payer_request_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payer_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "care_cost_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("care_cost_items.id", ondelete="SET NULL"),
        ),
        sa.Column("item_type", sa.String(60), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("actual_cost_minor", sa.Integer(), nullable=False),
        sa.Column("requested_minor", sa.Integer(), nullable=False),
        sa.Column("patient_responsibility_minor", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("payer_request_id", "care_cost_item_id", name="uq_payer_request_item"),
    )

    op.create_table(
        "payer_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payer_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payer_membership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("reason_code", sa.String(80), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_payer_reviews_request_created", "payer_reviews", ["payer_request_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_payer_reviews_request_created", table_name="payer_reviews")
    op.drop_table("payer_reviews")
    op.drop_table("payer_request_lines")
    op.drop_index("ix_payer_requests_doctor_created", table_name="payer_requests")
    op.drop_index("ix_payer_requests_organization_status", table_name="payer_requests")
    op.drop_table("payer_requests")
    op.drop_index("ix_care_cost_items_patient_created", table_name="care_cost_items")
    op.drop_index("ix_care_cost_items_event_service_date", table_name="care_cost_items")
    op.drop_table("care_cost_items")
    op.drop_index("ix_payer_membership_user_status", table_name="payer_memberships")
    op.drop_table("payer_memberships")
    op.drop_index("ix_payer_organizations_name", table_name="payer_organizations")
    op.drop_table("payer_organizations")
    # PostgreSQL enum values are intentionally not removed in-place. The base
    # migration drops the type during a full teardown.
