"""Persist patient blood type on the profile.

Revision ID: 20260714_0020
Revises: 20260711_0019
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0020"
down_revision: str | None = "20260711_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patient_profiles",
        sa.Column("blood_type", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("patient_profiles", "blood_type")
