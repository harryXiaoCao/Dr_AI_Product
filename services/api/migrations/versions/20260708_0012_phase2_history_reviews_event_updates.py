"""Add Phase 2 history reviews and event updates.

Revision ID: 20260708_0012
Revises: 20260708_0011
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260708_0012"
down_revision: str | None = "20260708_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medical_history_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("amendment_summary", sa.Text(), nullable=True),
        sa.Column("correction_request", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_medical_history_reviews_patient_created",
        "medical_history_reviews",
        ["patient_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_medical_history_reviews_target",
        "medical_history_reviews",
        ["target_type", "target_id"],
        unique=False,
    )

    op.create_table(
        "clinical_event_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinical_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("update_type", sa.String(length=60), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clinical_event_updates_event_created",
        "clinical_event_updates",
        ["clinical_event_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_event_updates_patient_created",
        "clinical_event_updates",
        ["patient_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_clinical_event_updates_patient_created",
        table_name="clinical_event_updates",
    )
    op.drop_index(
        "ix_clinical_event_updates_event_created",
        table_name="clinical_event_updates",
    )
    op.drop_table("clinical_event_updates")

    op.drop_index("ix_medical_history_reviews_target", table_name="medical_history_reviews")
    op.drop_index(
        "ix_medical_history_reviews_patient_created",
        table_name="medical_history_reviews",
    )
    op.drop_table("medical_history_reviews")
