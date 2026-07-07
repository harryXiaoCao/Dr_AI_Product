"""Add Phase 2 recovery plan review workflow metadata.

Revision ID: 20260708_0009
Revises: 20260708_0008
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_0009"
down_revision: str | None = "20260708_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recovery_plans",
        sa.Column(
            "review_status",
            sa.String(length=40),
            server_default="draft",
            nullable=False,
        ),
    )
    op.add_column(
        "recovery_plans",
        sa.Column("review_actor_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "recovery_plans",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "recovery_plans",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "recovery_plans",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "recovery_plans",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_recovery_plans_review_actor_user_id_users",
        "recovery_plans",
        "users",
        ["review_actor_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_recovery_plans_patient_review",
        "recovery_plans",
        ["patient_id", "review_status"],
        unique=False,
    )
    op.alter_column("recovery_plans", "review_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_recovery_plans_patient_review", table_name="recovery_plans")
    op.drop_constraint(
        "fk_recovery_plans_review_actor_user_id_users",
        "recovery_plans",
        type_="foreignkey",
    )
    op.drop_column("recovery_plans", "completed_at")
    op.drop_column("recovery_plans", "approved_at")
    op.drop_column("recovery_plans", "reviewed_at")
    op.drop_column("recovery_plans", "submitted_at")
    op.drop_column("recovery_plans", "review_actor_user_id")
    op.drop_column("recovery_plans", "review_status")
