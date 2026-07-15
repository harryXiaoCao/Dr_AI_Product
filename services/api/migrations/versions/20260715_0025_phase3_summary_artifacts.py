"""Add reviewed bilingual knowledge-summary artifacts.

Revision ID: 20260715_0025
Revises: 20260715_0024
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260715_0025"
down_revision: str | None = "20260715_0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kb_summary_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(180), nullable=False, unique=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "translation_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_translation_artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("english_summary", sa.Text(), nullable=False),
        sa.Column("chinese_summary", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("prompt_policy_version", sa.String(120), nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("translation_checksum", sa.String(64), nullable=False),
        sa.Column("summary_checksum", sa.String(64), nullable=False),
        sa.Column("artifact_locator", sa.Text(), nullable=False),
        sa.Column("status", sa.String(60), nullable=False, server_default="approved"),
        sa.Column("reviewer_id", sa.String(160), nullable=False),
        sa.Column("review_findings", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "source_version_id",
            "model",
            "prompt_policy_version",
            name="uq_kb_summary_artifact_generation",
        ),
    )
    op.create_index(
        "ix_kb_summary_artifacts_stable_id",
        "kb_summary_artifacts",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_summary_artifacts_source_id",
        "kb_summary_artifacts",
        ["source_id"],
    )
    op.create_index(
        "ix_kb_summary_artifacts_source_version_id",
        "kb_summary_artifacts",
        ["source_version_id"],
    )
    op.create_index(
        "ix_kb_summary_artifacts_translation_artifact_id",
        "kb_summary_artifacts",
        ["translation_artifact_id"],
    )
    op.create_index(
        "ix_kb_summary_artifacts_source_status",
        "kb_summary_artifacts",
        ["source_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("kb_summary_artifacts")
