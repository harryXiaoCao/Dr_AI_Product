"""Add Phase 2.5 signup profile onboarding fields.

Revision ID: 20260709_0013
Revises: 20260708_0012
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_0013"
down_revision: str | None = "20260708_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=True)
    op.add_column("users", sa.Column("phone_number", sa.String(length=40), nullable=True))
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)

    op.add_column("doctor_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("doctor_profiles", sa.Column("gender", sa.String(length=40), nullable=True))
    op.add_column(
        "doctor_profiles",
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
    )
    op.add_column("doctor_profiles", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column("doctor_profiles", sa.Column("country", sa.String(length=80), nullable=True))
    op.add_column("doctor_profiles", sa.Column("province", sa.String(length=80), nullable=True))
    op.add_column("doctor_profiles", sa.Column("city", sa.String(length=80), nullable=True))

    op.add_column("patient_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("patient_profiles", sa.Column("gender", sa.String(length=40), nullable=True))
    op.add_column(
        "patient_profiles",
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "patient_profiles",
        sa.Column("emergency_contact_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "patient_profiles",
        sa.Column("emergency_contact_phone", sa.String(length=40), nullable=True),
    )
    op.add_column("patient_profiles", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column("patient_profiles", sa.Column("country", sa.String(length=80), nullable=True))
    op.add_column("patient_profiles", sa.Column("province", sa.String(length=80), nullable=True))
    op.add_column("patient_profiles", sa.Column("city", sa.String(length=80), nullable=True))
    op.add_column(
        "patient_profiles",
        sa.Column("home_address", sa.String(length=240), nullable=True),
    )
    op.add_column(
        "patient_profiles",
        sa.Column(
            "medical_history_setup_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("patient_profiles", "medical_history_setup_completed", server_default=None)


def downgrade() -> None:
    op.drop_column("patient_profiles", "medical_history_setup_completed")
    op.drop_column("patient_profiles", "home_address")
    op.drop_column("patient_profiles", "city")
    op.drop_column("patient_profiles", "province")
    op.drop_column("patient_profiles", "country")
    op.drop_column("patient_profiles", "avatar_url")
    op.drop_column("patient_profiles", "emergency_contact_phone")
    op.drop_column("patient_profiles", "emergency_contact_name")
    op.drop_column("patient_profiles", "contact_phone")
    op.drop_column("patient_profiles", "gender")
    op.drop_column("patient_profiles", "birth_date")

    op.drop_column("doctor_profiles", "city")
    op.drop_column("doctor_profiles", "province")
    op.drop_column("doctor_profiles", "country")
    op.drop_column("doctor_profiles", "avatar_url")
    op.drop_column("doctor_profiles", "contact_phone")
    op.drop_column("doctor_profiles", "gender")
    op.drop_column("doctor_profiles", "birth_date")

    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_column("users", "phone_number")
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=False)
