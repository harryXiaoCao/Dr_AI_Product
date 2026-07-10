"""Add patient profile height and weight.

Revision ID: 20260710_0015
Revises: 20260709_0014
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260710_0015"
down_revision: str | None = "20260709_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patient_profiles", sa.Column("height_cm", sa.Float(), nullable=True))
    op.add_column("patient_profiles", sa.Column("weight_kg", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("patient_profiles", "weight_kg")
    op.drop_column("patient_profiles", "height_cm")
