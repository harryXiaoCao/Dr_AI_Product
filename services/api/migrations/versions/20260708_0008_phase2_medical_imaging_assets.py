"""Add Phase 2 medical imaging asset workflow models.

Revision ID: 20260708_0008
Revises: 20260707_0007
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260708_0008"
down_revision: str | None = "20260707_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medical_imaging_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_provider", sa.String(length=40), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("file_extension", sa.String(length=16), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_size_bytes", sa.Integer(), nullable=True),
        sa.Column("object_key", sa.String(length=260), nullable=False),
        sa.Column("upload_status", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("etag", sa.String(length=128), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(
        "ix_medical_imaging_patient_created",
        "medical_imaging_assets",
        ["patient_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_medical_imaging_patient_review",
        "medical_imaging_assets",
        ["patient_id", "review_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_medical_imaging_patient_review", table_name="medical_imaging_assets")
    op.drop_index("ix_medical_imaging_patient_created", table_name="medical_imaging_assets")
    op.drop_table("medical_imaging_assets")
