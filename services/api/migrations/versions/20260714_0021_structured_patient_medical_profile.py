"""Persist the editable patient medical profile as one structured record.

Revision ID: 20260714_0021
Revises: 20260714_0020
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0021"
down_revision: str | None = "20260714_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patient_profiles", sa.Column("systolic_blood_pressure", sa.Integer()))
    op.add_column("patient_profiles", sa.Column("diastolic_blood_pressure", sa.Integer()))
    op.add_column("patient_profiles", sa.Column("smoking_status", sa.String(length=40)))
    op.add_column("patient_profiles", sa.Column("alcohol_consumption", sa.String(length=40)))
    op.add_column("patient_profiles", sa.Column("heart_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("endocrine_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("neuro_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("digestive_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("respiratory_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("kidney_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("cancer_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("patient_reported_medications", sa.Text()))
    op.add_column("patient_profiles", sa.Column("surgery_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("family_history", sa.Text()))
    op.add_column("patient_profiles", sa.Column("lifestyle_notes", sa.Text()))
    op.add_column("patient_profiles", sa.Column("pregnancy_status", sa.String(length=40)))


def downgrade() -> None:
    for column_name in (
        "pregnancy_status",
        "lifestyle_notes",
        "family_history",
        "surgery_history",
        "patient_reported_medications",
        "cancer_history",
        "kidney_history",
        "respiratory_history",
        "digestive_history",
        "neuro_history",
        "endocrine_history",
        "heart_history",
        "alcohol_consumption",
        "smoking_status",
        "diastolic_blood_pressure",
        "systolic_blood_pressure",
    ):
        op.drop_column("patient_profiles", column_name)
