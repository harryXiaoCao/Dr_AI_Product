"""Add review-gated Phase 3 derived translation artifacts.

Revision ID: 20260715_0024
Revises: 20260714_0023
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260715_0024"
down_revision: str | None = "20260714_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kb_translation_artifacts",
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
        sa.Column("target_language", sa.String(20), nullable=False),
        sa.Column("translated_title", sa.String(500), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("prompt_policy_version", sa.String(120), nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("translation_checksum", sa.String(64), nullable=False),
        sa.Column("artifact_locator", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(60), nullable=False, server_default="generated_pending_review"
        ),
        sa.Column("medical_review_status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column(
            "native_language_review_status", sa.String(40), nullable=False, server_default="pending"
        ),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "source_version_id",
            "target_language",
            "model",
            "prompt_policy_version",
            name="uq_kb_translation_artifact_generation",
        ),
    )
    op.create_index(
        "ix_kb_translation_artifacts_stable_id",
        "kb_translation_artifacts",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_translation_artifacts_source_id",
        "kb_translation_artifacts",
        ["source_id"],
    )
    op.create_index(
        "ix_kb_translation_artifacts_source_version_id",
        "kb_translation_artifacts",
        ["source_version_id"],
    )
    op.create_index(
        "ix_kb_translation_artifacts_source_status",
        "kb_translation_artifacts",
        ["source_id", "status"],
    )

    op.create_table(
        "kb_translation_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(200), nullable=False, unique=True),
        sa.Column(
            "artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_translation_artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_section_stable_id", sa.String(180), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("translated_heading", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("content_checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("artifact_id", "ordinal", name="uq_kb_translation_section_ordinal"),
    )
    op.create_index(
        "ix_kb_translation_sections_stable_id",
        "kb_translation_sections",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_translation_sections_artifact_id",
        "kb_translation_sections",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_table("kb_translation_sections")
    op.drop_table("kb_translation_artifacts")
