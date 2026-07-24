"""Link active care-cost rows to the clinical source that produced them.

Revision ID: 20260724_0037
Revises: 20260723_0036
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0037"
down_revision: str | None = "20260723_0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "care_cost_items",
        sa.Column(
            "pricing_state",
            sa.String(40),
            nullable=False,
            server_default="final",
        ),
    )
    op.add_column(
        "care_cost_items",
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "care_cost_items",
        sa.Column("consultation_request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_care_cost_items_medication",
        "care_cost_items",
        "medications",
        ["medication_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_care_cost_items_consultation",
        "care_cost_items",
        "consultation_requests",
        ["consultation_request_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_care_cost_items_single_source",
        "care_cost_items",
        "NOT (medication_id IS NOT NULL AND consultation_request_id IS NOT NULL)",
    )
    op.create_index(
        "uq_care_cost_items_active_medication",
        "care_cost_items",
        ["medication_id"],
        unique=True,
        postgresql_where=sa.text("medication_id IS NOT NULL"),
    )
    op.create_index(
        "uq_care_cost_items_active_consultation",
        "care_cost_items",
        ["consultation_request_id"],
        unique=True,
        postgresql_where=sa.text("consultation_request_id IS NOT NULL"),
    )


def downgrade() -> None:
    # The test/bootstrap lifecycle may reconcile metadata before a rollback.
    # IF EXISTS keeps the downgrade safe without changing the forward schema.
    op.execute("DROP INDEX IF EXISTS uq_care_cost_items_active_consultation")
    op.execute("DROP INDEX IF EXISTS uq_care_cost_items_active_medication")
    op.execute(
        "ALTER TABLE care_cost_items "
        "DROP CONSTRAINT IF EXISTS ck_care_cost_items_single_source"
    )
    op.execute(
        "ALTER TABLE care_cost_items "
        "DROP CONSTRAINT IF EXISTS fk_care_cost_items_consultation"
    )
    op.execute(
        "ALTER TABLE care_cost_items "
        "DROP CONSTRAINT IF EXISTS fk_care_cost_items_medication"
    )
    op.drop_column("care_cost_items", "consultation_request_id")
    op.drop_column("care_cost_items", "medication_id")
    op.drop_column("care_cost_items", "pricing_state")
