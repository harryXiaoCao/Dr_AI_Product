"""Add the Phase 3 approved retrieval baseline.

Revision ID: 20260714_0023
Revises: 20260714_0022
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0023"
down_revision: str | None = "20260714_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "kb_sources", sa.Column("catalog_summary", sa.Text(), nullable=False, server_default="")
    )
    op.add_column(
        "kb_sources",
        sa.Column(
            "search_keywords_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.create_table(
        "kb_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(180), nullable=False, unique=True),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("heading_path_json", postgresql.JSONB(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("version_id", "ordinal", name="uq_kb_section_version_ordinal"),
    )
    op.create_index("ix_kb_sections_stable_id", "kb_sections", ["stable_id"], unique=True)
    op.create_index("ix_kb_sections_version_id", "kb_sections", ["version_id"])

    op.create_table(
        "kb_passages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(200), nullable=False, unique=True),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("source_offset_start", sa.Integer()),
        sa.Column("source_offset_end", sa.Integer()),
        sa.Column("clinical_concept_tags_json", postgresql.JSONB(), nullable=False),
        sa.Column("audience_json", postgresql.JSONB(), nullable=False),
        sa.Column("contraindication_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("red_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("chunking_version", sa.String(100), nullable=False),
        sa.Column(
            "patient_readability_review_status",
            sa.String(40),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("lexical_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vector_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("embedding_json", postgresql.JSONB()),
        sa.Column("content_checksum", sa.String(64), nullable=False),
        sa.Column("conflict_group_key", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("section_id", "ordinal", name="uq_kb_passage_section_ordinal"),
    )
    op.create_index("ix_kb_passages_stable_id", "kb_passages", ["stable_id"], unique=True)
    op.create_index("ix_kb_passages_section_id", "kb_passages", ["section_id"])
    op.create_index("ix_kb_passages_version_id", "kb_passages", ["version_id"])
    op.create_index("ix_kb_passages_conflict_group_key", "kb_passages", ["conflict_group_key"])
    op.create_index(
        "ix_kb_passages_version_eligibility",
        "kb_passages",
        ["version_id", "lexical_eligible"],
    )

    op.create_table(
        "kb_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(160), nullable=False, unique=True),
        sa.Column("preferred_zh", sa.String(240), nullable=False),
        sa.Column("preferred_en", sa.String(240)),
        sa.Column("aliases_json", postgresql.JSONB(), nullable=False),
        sa.Column("concept_type", sa.String(80), nullable=False),
        sa.Column("disambiguation_notes", sa.Text()),
        sa.Column("provenance_source_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("prohibited_expansions_json", postgresql.JSONB(), nullable=False),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kb_terms_stable_id", "kb_terms", ["stable_id"], unique=True)

    op.create_table(
        "kb_index_release_passages",
        sa.Column(
            "release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_index_releases.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "passage_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_passages.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_kb_index_release_passages_passage_id",
        "kb_index_release_passages",
        ["passage_id"],
    )

    op.create_table(
        "kb_retrieval_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(120), nullable=False, unique=True),
        sa.Column("actor_role", sa.String(40), nullable=False),
        sa.Column("workflow", sa.String(80), nullable=False),
        sa.Column("query_sha256", sa.String(64), nullable=False),
        sa.Column("query_length", sa.Integer(), nullable=False),
        sa.Column("filter_classes_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "index_release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_index_releases.id", ondelete="SET NULL"),
        ),
        sa.Column("retrieved_source_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("retrieved_passage_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("score_summary_json", postgresql.JSONB(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("evidence_decision", sa.String(80), nullable=False),
        sa.Column("fallback_code", sa.String(80)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_kb_retrieval_events_request_id",
        "kb_retrieval_events",
        ["request_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_retrieval_events_index_release_id",
        "kb_retrieval_events",
        ["index_release_id"],
    )
    op.create_index("ix_kb_retrieval_events_occurred", "kb_retrieval_events", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("kb_retrieval_events")
    op.drop_table("kb_index_release_passages")
    op.drop_table("kb_terms")
    op.drop_table("kb_passages")
    op.drop_table("kb_sections")
    op.drop_column("kb_sources", "search_keywords_json")
    op.drop_column("kb_sources", "catalog_summary")
