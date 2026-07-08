"""Add Phase 2 manual imaging findings.

Revision ID: 20260708_0011
Revises: 20260708_0010
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_0011"
down_revision: str | None = "20260708_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "medical_imaging_assets",
        sa.Column("finding_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "medical_imaging_assets",
        sa.Column("measurement_summary", sa.String(length=240), nullable=True),
    )
    op.add_column(
        "medical_imaging_assets",
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "medical_imaging_assets",
        sa.Column("treatment_relevance_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("medical_imaging_assets", "treatment_relevance_date")
    op.drop_column("medical_imaging_assets", "observed_at")
    op.drop_column("medical_imaging_assets", "measurement_summary")
    op.drop_column("medical_imaging_assets", "finding_summary")
