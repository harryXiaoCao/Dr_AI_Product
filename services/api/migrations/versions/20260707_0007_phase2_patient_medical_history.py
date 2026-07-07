"""Add Phase 2 patient medical-history workflow models.

Revision ID: 20260707_0007
Revises: 20260707_0006
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260707_0007"
down_revision: str | None = "20260707_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.add_column("patient_profiles", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column("patient_profiles", sa.Column("sex", sa.String(length=40), nullable=True))
    op.add_column(
        "patient_profiles",
        sa.Column("preferred_language", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "patient_profiles",
        sa.Column("contact_preference", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "doctor_notes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "patient_allergies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("reaction", sa.String(length=240), nullable=True),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_allergies_patient_status",
        "patient_allergies",
        ["patient_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "chronic_diseases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("diagnosed_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chronic_diseases_patient_status",
        "chronic_diseases",
        ["patient_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "visit_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clinician_label", sa.String(length=160), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_visit_history_patient_occurred",
        "visit_history",
        ["patient_id", "occurred_at"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "diagnoses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("diagnosed_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_diagnoses_patient_status",
        "diagnoses",
        ["patient_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_diagnoses_patient_status", table_name="diagnoses")
    op.drop_table("diagnoses")
    op.drop_index("ix_visit_history_patient_occurred", table_name="visit_history")
    op.drop_table("visit_history")
    op.drop_index("ix_chronic_diseases_patient_status", table_name="chronic_diseases")
    op.drop_table("chronic_diseases")
    op.drop_index("ix_patient_allergies_patient_status", table_name="patient_allergies")
    op.drop_table("patient_allergies")
    op.drop_column("doctor_notes", "updated_at")
    op.drop_column("patient_profiles", "contact_preference")
    op.drop_column("patient_profiles", "preferred_language")
    op.drop_column("patient_profiles", "sex")
    op.drop_column("patient_profiles", "birth_year")
