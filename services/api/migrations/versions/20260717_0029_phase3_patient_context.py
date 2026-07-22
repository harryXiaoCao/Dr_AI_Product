"""Add patient-profile context provenance timestamp.

Revision ID: 20260717_0029
Revises: 20260716_0028
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0029"
down_revision: str | None = "20260716_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patient_profiles",
        sa.Column(
            "context_recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "patient_profiles",
        sa.Column("measurements_recorded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE patient_profiles SET measurements_recorded_at = context_recorded_at "
        "WHERE systolic_blood_pressure IS NOT NULL OR diastolic_blood_pressure IS NOT NULL "
        "OR height_cm IS NOT NULL OR weight_kg IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("patient_profiles", "measurements_recorded_at")
    op.drop_column("patient_profiles", "context_recorded_at")
