"""Add canonical clinical services and link imaging evidence.

Revision ID: 20260724_0038
Revises: 20260724_0037
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0038"
down_revision: str | None = "20260724_0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinical_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "clinical_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("service_subtype", sa.String(80), nullable=True),
        sa.Column("body_region", sa.String(120), nullable=True),
        sa.Column("service_code", sa.String(80), nullable=True),
        sa.Column(
            "ordered_by_doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("performing_provider_name", sa.String(160), nullable=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(40), nullable=False, server_default="ordered"),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indication_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "scheduled_at IS NULL OR ordered_at IS NULL OR scheduled_at >= ordered_at",
            name="ck_clinical_services_schedule_after_order",
        ),
    )
    op.create_index(
        "ix_clinical_services_patient_status",
        "clinical_services",
        ["patient_id", "status"],
    )
    op.create_index(
        "ix_clinical_services_event_category",
        "clinical_services",
        ["clinical_event_id", "category"],
    )
    op.create_index(
        "ix_clinical_services_appointment",
        "clinical_services",
        ["appointment_id"],
    )

    op.add_column(
        "consultation_requests",
        sa.Column("clinical_service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_consultations_clinical_service",
        "consultation_requests",
        "clinical_services",
        ["clinical_service_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_consultations_clinical_service",
        "consultation_requests",
        ["clinical_service_id"],
    )

    op.add_column(
        "medical_imaging_assets",
        sa.Column("clinical_service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_medical_imaging_clinical_service",
        "medical_imaging_assets",
        "clinical_services",
        ["clinical_service_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_medical_imaging_clinical_service",
        "medical_imaging_assets",
        ["clinical_service_id"],
    )

    op.add_column(
        "care_cost_items",
        sa.Column("clinical_service_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_care_cost_items_clinical_service",
        "care_cost_items",
        "clinical_services",
        ["clinical_service_id"],
        ["id"],
        ondelete="CASCADE",
    )

    connection = op.get_bind()
    consultations = connection.execute(
        sa.text(
            """
            SELECT c.id, c.patient_id, c.clinical_event_id, c.requested_by_user_id,
                   c.specialty, c.status, c.created_at, c.updated_at, d.id AS doctor_id
            FROM consultation_requests AS c
            JOIN doctor_profiles AS d ON d.user_id = c.requested_by_user_id
            WHERE c.clinical_event_id IS NOT NULL
            ORDER BY c.created_at, c.id
            """
        )
    ).mappings()
    for consultation in consultations:
        service_id = uuid.uuid4()
        source_status = consultation["status"]
        service_status = {
            "requested": "requested",
            "accepted": "scheduled",
            "completed": "completed",
            "cancelled": "cancelled",
        }.get(source_status, "requested")
        performed_at = (
            consultation["updated_at"] or datetime.now(UTC)
            if service_status == "completed"
            else None
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO clinical_services (
                    id, patient_id, clinical_event_id, category, name, service_subtype,
                    ordered_by_doctor_id, status, ordered_at, performed_at,
                    created_at, updated_at
                ) VALUES (
                    :id, :patient_id, :clinical_event_id, 'consultation', :name, :subtype,
                    :doctor_id, :status, :ordered_at, :performed_at,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": service_id,
                "patient_id": consultation["patient_id"],
                "clinical_event_id": consultation["clinical_event_id"],
                "name": f"{consultation['specialty']} consultation",
                "subtype": consultation["specialty"],
                "doctor_id": consultation["doctor_id"],
                "status": service_status,
                "ordered_at": consultation["created_at"],
                "performed_at": performed_at,
                "created_at": consultation["created_at"],
                "updated_at": consultation["updated_at"],
            },
        )
        connection.execute(
            sa.text(
                "UPDATE consultation_requests "
                "SET clinical_service_id = :service_id WHERE id = :consultation_id"
            ),
            {"service_id": service_id, "consultation_id": consultation["id"]},
        )
        connection.execute(
            sa.text(
                "UPDATE care_cost_items SET clinical_service_id = :service_id "
                "WHERE consultation_request_id = :consultation_id"
            ),
            {"service_id": service_id, "consultation_id": consultation["id"]},
        )

    op.execute("DROP INDEX IF EXISTS uq_care_cost_items_active_consultation")
    op.drop_constraint("ck_care_cost_items_single_source", "care_cost_items", type_="check")
    op.drop_constraint("fk_care_cost_items_consultation", "care_cost_items", type_="foreignkey")
    op.drop_column("care_cost_items", "consultation_request_id")
    op.create_check_constraint(
        "ck_care_cost_items_single_source",
        "care_cost_items",
        "NOT (medication_id IS NOT NULL AND clinical_service_id IS NOT NULL)",
    )
    op.create_index(
        "uq_care_cost_items_active_service",
        "care_cost_items",
        ["clinical_service_id"],
        unique=True,
        postgresql_where=sa.text("clinical_service_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.add_column(
        "care_cost_items",
        sa.Column("consultation_request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_care_cost_items_consultation",
        "care_cost_items",
        "consultation_requests",
        ["consultation_request_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        UPDATE care_cost_items AS item
        SET consultation_request_id = consultation.id
        FROM consultation_requests AS consultation
        WHERE consultation.clinical_service_id = item.clinical_service_id
        """
    )
    op.execute("DROP INDEX IF EXISTS uq_care_cost_items_active_service")
    op.drop_constraint("ck_care_cost_items_single_source", "care_cost_items", type_="check")
    op.create_check_constraint(
        "ck_care_cost_items_single_source",
        "care_cost_items",
        "NOT (medication_id IS NOT NULL AND consultation_request_id IS NOT NULL)",
    )
    op.create_index(
        "uq_care_cost_items_active_consultation",
        "care_cost_items",
        ["consultation_request_id"],
        unique=True,
        postgresql_where=sa.text("consultation_request_id IS NOT NULL"),
    )
    op.drop_constraint("fk_care_cost_items_clinical_service", "care_cost_items", type_="foreignkey")
    op.drop_column("care_cost_items", "clinical_service_id")

    op.drop_index("ix_medical_imaging_clinical_service", table_name="medical_imaging_assets")
    op.drop_constraint(
        "fk_medical_imaging_clinical_service",
        "medical_imaging_assets",
        type_="foreignkey",
    )
    op.drop_column("medical_imaging_assets", "clinical_service_id")

    op.drop_constraint(
        "uq_consultations_clinical_service",
        "consultation_requests",
        type_="unique",
    )
    op.drop_constraint(
        "fk_consultations_clinical_service",
        "consultation_requests",
        type_="foreignkey",
    )
    op.drop_column("consultation_requests", "clinical_service_id")

    op.drop_index("ix_clinical_services_appointment", table_name="clinical_services")
    op.drop_index("ix_clinical_services_event_category", table_name="clinical_services")
    op.drop_index("ix_clinical_services_patient_status", table_name="clinical_services")
    op.drop_table("clinical_services")
