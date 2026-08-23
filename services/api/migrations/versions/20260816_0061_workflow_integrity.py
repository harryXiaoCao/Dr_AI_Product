"""Add consent, independent recovery review, and structured task scheduling.

Revision ID: 20260816_0061
Revises: 20260813_0060
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260816_0061"
down_revision: str | None = "20260813_0060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("care_relationships", sa.Column("status", sa.String(40), nullable=True))
    op.add_column(
        "care_relationships",
        sa.Column("request_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "care_relationships",
        sa.Column(
            "can_review_recovery_plans", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "care_relationships",
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("care_relationships", sa.Column("responded_at", sa.DateTime(timezone=True)))
    op.add_column("care_relationships", sa.Column("approved_at", sa.DateTime(timezone=True)))
    op.add_column("care_relationships", sa.Column("rejected_at", sa.DateTime(timezone=True)))
    op.execute(
        """
        UPDATE care_relationships
        SET status = CASE WHEN is_active THEN 'active' ELSE 'revoked' END,
            requested_at = created_at,
            responded_at = CASE
                WHEN is_active THEN created_at ELSE COALESCE(revoked_at, created_at)
            END,
            approved_at = CASE WHEN is_active THEN created_at ELSE NULL END,
            revoked_at = CASE WHEN is_active THEN NULL ELSE COALESCE(revoked_at, created_at) END,
            can_review_recovery_plans = is_active
        """
    )
    op.alter_column("care_relationships", "status", nullable=False)
    op.alter_column("care_relationships", "requested_at", nullable=False)
    op.create_check_constraint(
        "ck_care_relationship_status",
        "care_relationships",
        "status IN ('pending_patient_approval','active','rejected','revoked')",
    )
    op.create_check_constraint(
        "ck_care_relationship_version", "care_relationships", "request_version > 0"
    )
    op.create_index(
        "ix_care_relationship_patient_status", "care_relationships", ["patient_id", "status"]
    )

    op.add_column(
        "recovery_plans",
        sa.Column("assigned_reviewer_doctor_id", postgresql.UUID(as_uuid=True)),
    )
    op.add_column("recovery_plans", sa.Column("submitted_version", sa.Integer()))
    op.add_column("recovery_plans", sa.Column("review_comment", sa.Text()))
    op.create_foreign_key(
        "fk_recovery_plan_assigned_reviewer",
        "recovery_plans",
        "doctor_profiles",
        ["assigned_reviewer_doctor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "recovery_plan_review_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recovery_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column(
            "reviewer_doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("plan_id", "plan_version", "action", name="uq_recovery_review_action"),
    )
    op.create_index(
        "ix_recovery_review_plan_created",
        "recovery_plan_review_decisions",
        ["plan_id", "created_at"],
    )

    op.add_column("recovery_tasks", sa.Column("scheduled_date", sa.Date()))
    op.add_column("recovery_tasks", sa.Column("scheduled_time", sa.String(5)))
    op.add_column(
        "recovery_tasks",
        sa.Column("time_zone", sa.String(64), nullable=False, server_default="Asia/Shanghai"),
    )
    # Legacy display-only due labels are not parsed. Existing tasks remain unscheduled.


def downgrade() -> None:
    for name in ("time_zone", "scheduled_time", "scheduled_date"):
        op.drop_column("recovery_tasks", name)
    op.drop_index("ix_recovery_review_plan_created", table_name="recovery_plan_review_decisions")
    op.drop_table("recovery_plan_review_decisions")
    op.drop_constraint("fk_recovery_plan_assigned_reviewer", "recovery_plans", type_="foreignkey")
    for name in ("review_comment", "submitted_version", "assigned_reviewer_doctor_id"):
        op.drop_column("recovery_plans", name)
    op.drop_index("ix_care_relationship_patient_status", table_name="care_relationships")
    op.drop_constraint("ck_care_relationship_version", "care_relationships", type_="check")
    op.drop_constraint("ck_care_relationship_status", "care_relationships", type_="check")
    for name in (
        "rejected_at",
        "approved_at",
        "responded_at",
        "requested_at",
        "can_review_recovery_plans",
        "request_version",
        "status",
    ):
        op.drop_column("care_relationships", name)
