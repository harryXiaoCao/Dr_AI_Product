"""Add immutable verified imaging byte provenance.

Revision ID: 20260727_0051
Revises: 20260727_0050
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260727_0051"
down_revision = "20260727_0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medical_imaging_asset_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("medical_imaging_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_provider", sa.String(40), nullable=False),
        sa.Column("object_key", sa.String(260), nullable=False, unique=True),
        sa.Column("content_type", sa.String(80), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("asset_id", "version", name="uq_imaging_asset_version"),
        sa.UniqueConstraint(
            "asset_id", "checksum_sha256", name="uq_imaging_asset_checksum"
        ),
    )
    op.create_index(
        "ix_imaging_asset_versions_asset_created",
        "medical_imaging_asset_versions",
        ["asset_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("medical_imaging_asset_versions")
