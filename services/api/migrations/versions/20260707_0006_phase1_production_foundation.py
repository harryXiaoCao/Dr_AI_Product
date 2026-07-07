"""Add Phase 1 production foundation models.

Revision ID: 20260707_0006
Revises: 20260705_0005
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260707_0006"
down_revision: str | None = "20260705_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM(
    "doctor",
    "patient",
    "specialist",
    "admin",
    name="user_role",
    create_type=False,
)


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


def _json_metadata_column(name: str = "metadata_json") -> sa.Column[postgresql.JSONB]:
    return sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), nullable=False)


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'specialist'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'admin'")

    created_at, updated_at = _timestamps()
    op.create_table(
        "hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("legal_name", sa.String(length=240), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hospitals_status", "hospitals", ["status"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hospital_id", "name", name="uq_clinic_hospital_name"),
    )
    op.create_index(
        "ix_clinics_hospital_status",
        "clinics",
        ["hospital_id", "status"],
        unique=False,
    )

    op.create_table(
        "role_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_role_assignments_clinic_role",
        "role_assignments",
        ["clinic_id", "role"],
        unique=False,
    )
    op.create_index(
        "ix_role_assignments_user_status",
        "role_assignments",
        ["user_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "doctor_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "name", name="uq_doctor_team_clinic_name"),
    )
    op.create_index(
        "ix_doctor_teams_clinic_status",
        "doctor_teams",
        ["clinic_id", "status"],
        unique=False,
    )

    op.create_table(
        "doctor_team_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["doctor_teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_doctor_team_membership_user"),
    )
    op.create_index(
        "ix_doctor_team_memberships_user_status",
        "doctor_team_memberships",
        ["user_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "clinic_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("capacity_current", sa.Integer(), nullable=True),
        sa.Column("capacity_total", sa.Integer(), nullable=True),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clinic_resources_clinic_type_status",
        "clinic_resources",
        ["clinic_id", "resource_type", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "equipment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("equipment_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("location_label", sa.String(length=160), nullable=True),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["clinic_resources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_clinic_status", "equipment", ["clinic_id", "status"])

    created_at, updated_at = _timestamps()
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("specialist_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["specialist_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appointments_clinic_status_start",
        "appointments",
        ["clinic_id", "status", "scheduled_start"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_patient_start",
        "appointments",
        ["patient_id", "scheduled_start"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "equipment_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purpose", sa.String(length=160), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_equipment_bookings_equipment_start",
        "equipment_bookings",
        ["equipment_id", "start_at"],
        unique=False,
    )
    op.create_index("ix_equipment_bookings_status", "equipment_bookings", ["status"])

    created_at, updated_at = _timestamps()
    op.create_table(
        "prescriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prescribed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prescribed_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prescriptions_patient_status",
        "prescriptions",
        ["patient_id", "status"],
        unique=False,
    )

    op.create_table(
        "prescription_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prescription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("dosage", sa.String(length=120), nullable=False),
        sa.Column("schedule", sa.String(length=160), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        _json_metadata_column(),
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prescription_medications_prescription",
        "prescription_medications",
        ["prescription_id"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "medication_reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prescription_medication_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("schedule_label", sa.String(length=160), nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["medication_id"], ["medications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["prescription_medication_id"],
            ["prescription_medications.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_medication_reminders_next_due",
        "medication_reminders",
        ["next_due_at"],
        unique=False,
    )
    op.create_index(
        "ix_medication_reminders_patient_status",
        "medication_reminders",
        ["patient_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notification_type", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_patient_type",
        "notifications",
        ["patient_id", "notification_type"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_user_status",
        "notifications",
        ["user_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_clinic_status", "invoices", ["clinic_id", "status"])
    op.create_index("ix_invoices_patient_status", "invoices", ["patient_id", "status"])

    created_at, updated_at = _timestamps()
    op.create_table(
        "payment_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_statuses_invoice_status",
        "payment_statuses",
        ["invoice_id", "status"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "revenue_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("invoiced_cents", sa.Integer(), nullable=False),
        sa.Column("paid_cents", sa.Integer(), nullable=False),
        sa.Column("outstanding_cents", sa.Integer(), nullable=False),
        _json_metadata_column(),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id",
            "period_start",
            "period_end",
            name="uq_revenue_summary_period",
        ),
    )
    op.create_index(
        "ix_revenue_summaries_clinic_period",
        "revenue_summaries",
        ["clinic_id", "period_start", "period_end"],
        unique=False,
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        _json_metadata_column(),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_events_clinic_occurred",
        "analytics_events",
        ["clinic_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_events_patient_occurred",
        "analytics_events",
        ["patient_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_events_type_occurred",
        "analytics_events",
        ["event_type", "occurred_at"],
        unique=False,
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "support_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=160), nullable=False),
        sa.Column("body_redacted", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        _json_metadata_column("audit_metadata_json"),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_requests_created", "support_requests", ["created_at"])
    op.create_index(
        "ix_support_requests_patient_type_status",
        "support_requests",
        ["patient_id", "request_type", "status"],
        unique=False,
    )
    op.create_index(
        "ix_support_requests_requester_status",
        "support_requests",
        ["requester_user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_requests_requester_status", table_name="support_requests")
    op.drop_index("ix_support_requests_patient_type_status", table_name="support_requests")
    op.drop_index("ix_support_requests_created", table_name="support_requests")
    op.drop_table("support_requests")
    op.drop_index("ix_analytics_events_type_occurred", table_name="analytics_events")
    op.drop_index("ix_analytics_events_patient_occurred", table_name="analytics_events")
    op.drop_index("ix_analytics_events_clinic_occurred", table_name="analytics_events")
    op.drop_table("analytics_events")
    op.drop_index("ix_revenue_summaries_clinic_period", table_name="revenue_summaries")
    op.drop_table("revenue_summaries")
    op.drop_index("ix_payment_statuses_invoice_status", table_name="payment_statuses")
    op.drop_table("payment_statuses")
    op.drop_index("ix_invoices_patient_status", table_name="invoices")
    op.drop_index("ix_invoices_clinic_status", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_notifications_user_status", table_name="notifications")
    op.drop_index("ix_notifications_patient_type", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_medication_reminders_patient_status", table_name="medication_reminders")
    op.drop_index("ix_medication_reminders_next_due", table_name="medication_reminders")
    op.drop_table("medication_reminders")
    op.drop_index(
        "ix_prescription_medications_prescription",
        table_name="prescription_medications",
    )
    op.drop_table("prescription_medications")
    op.drop_index("ix_prescriptions_patient_status", table_name="prescriptions")
    op.drop_table("prescriptions")
    op.drop_index("ix_equipment_bookings_status", table_name="equipment_bookings")
    op.drop_index(
        "ix_equipment_bookings_equipment_start",
        table_name="equipment_bookings",
    )
    op.drop_table("equipment_bookings")
    op.drop_index("ix_appointments_patient_start", table_name="appointments")
    op.drop_index("ix_appointments_clinic_status_start", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_equipment_clinic_status", table_name="equipment")
    op.drop_table("equipment")
    op.drop_index(
        "ix_clinic_resources_clinic_type_status",
        table_name="clinic_resources",
    )
    op.drop_table("clinic_resources")
    op.drop_index(
        "ix_doctor_team_memberships_user_status",
        table_name="doctor_team_memberships",
    )
    op.drop_table("doctor_team_memberships")
    op.drop_index("ix_doctor_teams_clinic_status", table_name="doctor_teams")
    op.drop_table("doctor_teams")
    op.drop_index("ix_role_assignments_user_status", table_name="role_assignments")
    op.drop_index("ix_role_assignments_clinic_role", table_name="role_assignments")
    op.drop_table("role_assignments")
    op.drop_index("ix_clinics_hospital_status", table_name="clinics")
    op.drop_table("clinics")
    op.drop_index("ix_hospitals_status", table_name="hospitals")
    op.drop_table("hospitals")
