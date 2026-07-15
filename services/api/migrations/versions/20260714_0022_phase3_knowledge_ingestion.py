"""Add the governed Phase 3 knowledge-ingestion registry.

Revision ID: 20260714_0022
Revises: 20260714_0021
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0022"
down_revision: str | None = "20260714_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def upgrade() -> None:
    op.create_table(
        "kb_publishers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(120), nullable=False, unique=True),
        sa.Column("official_name_zh", sa.String(240), nullable=False),
        sa.Column("official_name_en", sa.String(240)),
        sa.Column("organization_type", sa.String(80), nullable=False),
        sa.Column("authority_basis", sa.Text(), nullable=False),
        sa.Column("authority_evidence_locator", sa.Text(), nullable=False),
        sa.Column("verified_domains_json", postgresql.JSONB(), nullable=False),
        sa.Column("jurisdiction", sa.String(40), nullable=False),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("allowed_content_classes_json", postgresql.JSONB(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kb_publishers_stable_id", "kb_publishers", ["stable_id"], unique=True)

    op.create_table(
        "kb_rights_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "publisher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_publishers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stable_id", sa.String(120), nullable=False, unique=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("scope", sa.String(40), nullable=False),
        sa.Column("license_name", sa.String(200)),
        sa.Column("permission_reference", sa.Text()),
        sa.Column(
            "commercial_use_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("storage_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "transformation_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("translation_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("embedding_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "excerpt_display_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "model_provider_transmission_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "redistribution_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "prior_version_retention_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("attribution_requirements", sa.Text()),
        sa.Column("evidence_checksum", sa.String(64), nullable=False),
        sa.Column("evidence_locator", sa.Text(), nullable=False),
        sa.Column("decision_status", sa.String(40), nullable=False),
        sa.Column("legal_reviewer_id", sa.String(120)),
        sa.Column("effective_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_kb_rights_records_stable_id", "kb_rights_records", ["stable_id"], unique=True
    )
    op.create_index("ix_kb_rights_records_publisher_id", "kb_rights_records", ["publisher_id"])
    op.create_index("ix_kb_rights_records_source_id", "kb_rights_records", ["source_id"])

    op.create_table(
        "kb_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(120), nullable=False, unique=True),
        sa.Column(
            "publisher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_publishers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rights_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_rights_records.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("canonical_locator", sa.Text(), nullable=False, unique=True),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("jurisdiction", sa.String(40), nullable=False),
        sa.Column("intended_audiences_json", postgresql.JSONB(), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("specialty", sa.String(120)),
        sa.Column("population", sa.String(120)),
        sa.Column("original_language", sa.String(20), nullable=False),
        sa.Column("official_translations_json", postgresql.JSONB(), nullable=False),
        sa.Column("publication_date", sa.Date()),
        sa.Column("effective_date", sa.Date()),
        sa.Column("review_due_date", sa.Date()),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("authority_tier", sa.String(4), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("medical_review_status", sa.String(40), nullable=False),
        sa.Column("native_language_review_status", sa.String(40), nullable=False),
        sa.Column("doctor_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("patient_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("catalog_visible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("catalog_verified_at", sa.DateTime(timezone=True), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_kb_sources_stable_id", "kb_sources", ["stable_id"], unique=True)
    op.create_index("ix_kb_sources_catalog_status", "kb_sources", ["catalog_visible", "status"])
    op.create_index("ix_kb_sources_publisher_topic", "kb_sources", ["publisher_id", "topic"])

    op.create_foreign_key(
        "fk_kb_rights_records_source_id",
        "kb_rights_records",
        "kb_sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "kb_index_releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(160), nullable=False, unique=True),
        sa.Column("manifest_checksum", sa.String(64), nullable=False, unique=True),
        sa.Column("manifest_artifact_locator", sa.Text(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("version_count", sa.Integer(), nullable=False),
        sa.Column("passage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model_version", sa.String(160), nullable=False),
        sa.Column("lexical_analyzer_version", sa.String(160), nullable=False),
        sa.Column("reranker_version", sa.String(160), nullable=False),
        sa.Column("build_results_json", postgresql.JSONB(), nullable=False),
        sa.Column("approver_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "rollback_predecessor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_index_releases.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_kb_index_releases_stable_id", "kb_index_releases", ["stable_id"], unique=True
    )

    op.create_table(
        "kb_source_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(160), nullable=False, unique=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("publisher_version_label", sa.String(200)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capture_mode", sa.String(40), nullable=False),
        sa.Column("raw_checksum", sa.String(64), nullable=False),
        sa.Column("normalized_checksum", sa.String(64), nullable=False),
        sa.Column("raw_artifact_locator", sa.Text()),
        sa.Column("normalized_artifact_locator", sa.Text()),
        sa.Column("parser_version", sa.String(80), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_to", sa.DateTime(timezone=True)),
        sa.Column(
            "supersedes_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_versions.id", ondelete="SET NULL"),
        ),
        sa.Column("change_summary", sa.Text()),
        sa.Column("review_decision", sa.String(40), nullable=False),
        sa.Column("quarantine_reason_code", sa.String(120)),
        sa.Column(
            "index_release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_index_releases.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("source_id", "raw_checksum", name="uq_kb_source_version_checksum"),
    )
    op.create_index(
        "ix_kb_source_versions_stable_id", "kb_source_versions", ["stable_id"], unique=True
    )
    op.create_index("ix_kb_source_versions_source_id", "kb_source_versions", ["source_id"])

    op.create_table(
        "kb_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(160), nullable=False, unique=True),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_stable_id", sa.String(160), nullable=False),
        sa.Column("review_type", sa.String(40), nullable=False),
        sa.Column("reviewer_role", sa.String(80), nullable=False),
        sa.Column("reviewer_id", sa.String(120), nullable=False),
        sa.Column("decision", sa.String(40), nullable=False),
        sa.Column("decision_code", sa.String(120), nullable=False),
        sa.Column("findings", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_review_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kb_reviews_stable_id", "kb_reviews", ["stable_id"], unique=True)
    op.create_index("ix_kb_reviews_target", "kb_reviews", ["target_type", "target_stable_id"])

    op.create_table(
        "kb_active_index_releases",
        sa.Column("audience", sa.String(40), primary_key=True),
        sa.Column(
            "release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_index_releases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("activated_by", sa.String(120), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_kb_active_index_releases_release_id", "kb_active_index_releases", ["release_id"]
    )


def downgrade() -> None:
    op.drop_table("kb_active_index_releases")
    op.drop_table("kb_reviews")
    op.drop_table("kb_source_versions")
    op.drop_table("kb_index_releases")
    op.drop_constraint("fk_kb_rights_records_source_id", "kb_rights_records", type_="foreignkey")
    op.drop_table("kb_sources")
    op.drop_table("kb_rights_records")
    op.drop_table("kb_publishers")
