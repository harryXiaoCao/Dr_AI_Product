"""Add immutable prescription, structured recovery, and service workflow fields.

Revision ID: 20260802_0058
Revises: 20260802_0057
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260802_0058"
down_revision: str | None = "20260802_0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRESCRIPTION_LINE_COLUMNS = (
    ("formulation_strength", sa.String(160)),
    ("route", sa.String(80)),
    ("recorded_directions", sa.Text()),
    ("quantity", sa.Integer()),
    ("duration_days", sa.Integer()),
    ("sort_order", sa.Integer()),
    ("pricing_state", sa.String(40)),
    ("currency", sa.String(3)),
    ("unit_amount_minor", sa.Integer()),
    ("total_amount_minor", sa.Integer()),
)


def upgrade() -> None:
    op.add_column("clinical_services", sa.Column("service_date", sa.Date(), nullable=True))
    op.add_column("clinical_services", sa.Column("facility_name", sa.String(200), nullable=True))
    op.add_column(
        "clinical_services", sa.Column("quantity", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "clinical_services",
        sa.Column("unit", sa.String(60), nullable=False, server_default="service"),
    )
    op.add_column(
        "clinical_services",
        sa.Column("documentation_state", sa.String(40), nullable=False, server_default="pending"),
    )
    op.add_column(
        "clinical_services",
        sa.Column(
            "provenance_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("clinical_services", sa.Column("idempotency_key", sa.String(120), nullable=True))
    op.create_check_constraint(
        "ck_clinical_services_quantity_positive", "clinical_services", "quantity > 0"
    )
    op.create_unique_constraint(
        "uq_clinical_service_doctor_idempotency",
        "clinical_services",
        ["ordered_by_doctor_id", "idempotency_key"],
    )

    for name, type_ in (
        ("consultation_type", sa.String(80)),
        ("clinician_provider", sa.String(200)),
        ("reason_indication", sa.Text()),
        ("outcome_summary", postgresql.JSONB()),
        ("follow_up_requirement", sa.Text()),
        ("idempotency_key", sa.String(120)),
    ):
        op.add_column("consultation_requests", sa.Column(name, type_, nullable=True))
    op.add_column("consultation_requests", sa.Column("service_date", sa.Date(), nullable=True))
    op.add_column(
        "consultation_requests",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_consultation_quantity_positive", "consultation_requests", "quantity > 0"
    )
    op.create_unique_constraint(
        "uq_consultation_actor_idempotency",
        "consultation_requests",
        ["requested_by_user_id", "idempotency_key"],
    )

    op.add_column(
        "prescriptions", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "prescriptions",
        sa.Column("supersedes_prescription_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("prescriptions", sa.Column("idempotency_key", sa.String(120), nullable=True))
    op.add_column(
        "prescriptions", sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "prescriptions", sa.Column("content_checksum_sha256", sa.String(64), nullable=True)
    )
    op.create_foreign_key(
        "fk_prescription_supersedes",
        "prescriptions",
        "prescriptions",
        ["supersedes_prescription_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_prescription_actor_idempotency",
        "prescriptions",
        ["prescribed_by_user_id", "idempotency_key"],
    )
    op.create_check_constraint("ck_prescription_version_positive", "prescriptions", "version > 0")

    for name, type_ in PRESCRIPTION_LINE_COLUMNS:
        op.add_column("prescription_medications", sa.Column(name, type_, nullable=True))
    op.execute("UPDATE prescription_medications SET recorded_directions = schedule, sort_order = 0")

    op.add_column("recovery_plans", sa.Column("indication", sa.Text(), nullable=True))
    op.add_column("recovery_plans", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column(
        "recovery_plans", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "recovery_plans",
        sa.Column("supersedes_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("recovery_plans", sa.Column("idempotency_key", sa.String(120), nullable=True))
    op.add_column(
        "recovery_plans", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "recovery_plans", sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "recovery_plans", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_recovery_plan_supersedes",
        "recovery_plans",
        "recovery_plans",
        ["supersedes_plan_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_recovery_plan_doctor_idempotency", "recovery_plans", ["doctor_id", "idempotency_key"]
    )
    op.create_check_constraint("ck_recovery_plan_version_positive", "recovery_plans", "version > 0")

    op.create_table(
        "recovery_phases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recovery_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("start_week", sa.Integer(), nullable=True),
        sa.Column("end_week", sa.Integer(), nullable=True),
        sa.Column("goals", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("precautions", sa.Text(), nullable=False, server_default=""),
        sa.Column("progression_criteria", sa.Text(), nullable=False),
        sa.Column("hold_escalation_criteria", sa.Text(), nullable=False),
        sa.Column("review_checkpoint", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("plan_id", "sort_order", name="uq_recovery_phase_order"),
        sa.CheckConstraint("sort_order >= 0", name="ck_recovery_phase_order_nonnegative"),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_recovery_phase_date_range",
        ),
    )
    op.create_index("ix_recovery_phases_plan_order", "recovery_phases", ["plan_id", "sort_order"])
    op.add_column(
        "recovery_tasks", sa.Column("phase_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column("recovery_tasks", sa.Column("frequency", sa.String(120), nullable=True))
    op.add_column("recovery_tasks", sa.Column("schedule", sa.String(200), nullable=True))
    op.add_column("recovery_tasks", sa.Column("duration", sa.String(120), nullable=True))
    op.add_column("recovery_tasks", sa.Column("responsible_person", sa.String(120), nullable=True))
    op.add_column("recovery_tasks", sa.Column("completion_criteria", sa.Text(), nullable=True))
    op.add_column(
        "recovery_tasks",
        sa.Column(
            "reminder_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_foreign_key(
        "fk_recovery_task_phase",
        "recovery_tasks",
        "recovery_phases",
        ["phase_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_recovery_tasks_phase_order", "recovery_tasks", ["phase_id", "sort_order"])


def downgrade() -> None:
    op.drop_index("ix_recovery_tasks_phase_order", table_name="recovery_tasks")
    op.drop_constraint("fk_recovery_task_phase", "recovery_tasks", type_="foreignkey")
    for name in (
        "reminder_json",
        "completion_criteria",
        "responsible_person",
        "duration",
        "schedule",
        "frequency",
        "phase_id",
    ):
        op.drop_column("recovery_tasks", name)
    op.drop_index("ix_recovery_phases_plan_order", table_name="recovery_phases")
    op.drop_table("recovery_phases")
    op.drop_constraint("ck_recovery_plan_version_positive", "recovery_plans", type_="check")
    op.drop_constraint("uq_recovery_plan_doctor_idempotency", "recovery_plans", type_="unique")
    op.drop_constraint("fk_recovery_plan_supersedes", "recovery_plans", type_="foreignkey")
    for name in (
        "cancelled_at",
        "paused_at",
        "published_at",
        "idempotency_key",
        "supersedes_plan_id",
        "version",
        "start_date",
        "indication",
    ):
        op.drop_column("recovery_plans", name)
    for name, _ in reversed(PRESCRIPTION_LINE_COLUMNS):
        op.drop_column("prescription_medications", name)
    op.drop_constraint("ck_prescription_version_positive", "prescriptions", type_="check")
    op.drop_constraint("uq_prescription_actor_idempotency", "prescriptions", type_="unique")
    op.drop_constraint("fk_prescription_supersedes", "prescriptions", type_="foreignkey")
    for name in (
        "content_checksum_sha256",
        "finalized_at",
        "idempotency_key",
        "supersedes_prescription_id",
        "version",
    ):
        op.drop_column("prescriptions", name)
    op.drop_constraint("uq_consultation_actor_idempotency", "consultation_requests", type_="unique")
    op.drop_constraint("ck_consultation_quantity_positive", "consultation_requests", type_="check")
    for name in (
        "quantity",
        "service_date",
        "idempotency_key",
        "follow_up_requirement",
        "outcome_summary",
        "reason_indication",
        "clinician_provider",
        "consultation_type",
    ):
        op.drop_column("consultation_requests", name)
    op.drop_constraint(
        "uq_clinical_service_doctor_idempotency", "clinical_services", type_="unique"
    )
    op.drop_constraint("ck_clinical_services_quantity_positive", "clinical_services", type_="check")
    for name in (
        "idempotency_key",
        "provenance_json",
        "documentation_state",
        "unit",
        "quantity",
        "facility_name",
        "service_date",
    ):
        op.drop_column("clinical_services", name)
