"""Add Phase 2 clinical events and event links.

Revision ID: 20260708_0010
Revises: 20260708_0009
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260708_0010"
down_revision: str | None = "20260708_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVENT_LINK_TABLES: tuple[str, ...] = (
    "medications",
    "doctor_notes",
    "visit_history",
    "diagnoses",
    "medical_imaging_assets",
    "recovery_plans",
    "consultation_requests",
    "prescriptions",
    "medication_reminders",
    "notifications",
)


def _event_link_index_name(table_name: str) -> str:
    overrides = {
        "consultation_requests": "ix_consultations_clinical_event",
        "medical_imaging_assets": "ix_medical_imaging_clinical_event",
    }
    if table_name in overrides:
        return overrides[table_name]
    return f"ix_{table_name}_clinical_event"


def _event_link_fk_name(table_name: str) -> str:
    return f"fk_{table_name}_clinical_event_id_clinical_events"


def _legacy_event_link_index_name(table_name: str) -> str | None:
    legacy_names = {
        "consultation_requests": "ix_consultation_requests_clinical_event",
        "medical_imaging_assets": "ix_medical_imaging_assets_clinical_event",
    }
    return legacy_names.get(table_name)


def upgrade() -> None:
    op.create_table(
        "clinical_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("chief_complaint", sa.String(length=240), nullable=False),
        sa.Column("symptom_summary", sa.Text(), nullable=True),
        sa.Column("diagnosis_summary", sa.Text(), nullable=True),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clinical_events_patient_status",
        "clinical_events",
        ["patient_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_events_doctor_updated",
        "clinical_events",
        ["doctor_id", "updated_at"],
        unique=False,
    )

    for table_name in EVENT_LINK_TABLES:
        op.add_column(
            table_name,
            sa.Column("clinical_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            _event_link_fk_name(table_name),
            table_name,
            "clinical_events",
            ["clinical_event_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            _event_link_index_name(table_name),
            table_name,
            ["clinical_event_id"],
            unique=False,
        )


def downgrade() -> None:
    for table_name in reversed(EVENT_LINK_TABLES):
        op.drop_index(_event_link_index_name(table_name), table_name=table_name, if_exists=True)
        legacy_index_name = _legacy_event_link_index_name(table_name)
        if legacy_index_name is not None:
            op.drop_index(legacy_index_name, table_name=table_name, if_exists=True)
        op.drop_constraint(_event_link_fk_name(table_name), table_name, type_="foreignkey")
        op.drop_column(table_name, "clinical_event_id")

    op.drop_index("ix_clinical_events_doctor_updated", table_name="clinical_events")
    op.drop_index("ix_clinical_events_patient_status", table_name="clinical_events")
    op.drop_table("clinical_events")
