"""Add governed online-source expansion and freshness controls.

Revision ID: 20260716_0028
Revises: 20260716_0027
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0028"
down_revision: str | None = "20260716_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kb_source_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(120), nullable=False),
        sa.Column(
            "publisher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_publishers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("jurisdiction", sa.String(40), nullable=False),
        sa.Column("seed_locators_json", postgresql.JSONB(), nullable=False),
        sa.Column("allowed_domains_json", postgresql.JSONB(), nullable=False),
        sa.Column("allowed_path_prefixes_json", postgresql.JSONB(), nullable=False),
        sa.Column("content_classes_json", postgresql.JSONB(), nullable=False),
        sa.Column("parser_version", sa.String(120), nullable=False),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("max_response_bytes", sa.Integer(), nullable=False),
        sa.Column("capture_policy", sa.String(40), nullable=False),
        sa.Column("rights_gate_status", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("next_check_at", sa.DateTime(timezone=True)),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("killed_at", sa.DateTime(timezone=True)),
        sa.Column("killed_by", sa.String(120)),
        sa.Column("kill_reason_code", sa.String(120)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_kb_source_families_stable_id",
        "kb_source_families",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_source_families_publisher_id",
        "kb_source_families",
        ["publisher_id"],
    )
    op.create_index(
        "ix_kb_source_families_status_due",
        "kb_source_families",
        ["status", "next_check_at"],
    )
    op.add_column(
        "kb_sources",
        sa.Column("source_family_id", postgresql.UUID(as_uuid=True)),
    )
    op.create_foreign_key(
        "fk_kb_sources_source_family_id",
        "kb_sources",
        "kb_source_families",
        ["source_family_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_kb_sources_source_family_id", "kb_sources", ["source_family_id"])

    op.create_table(
        "kb_source_fetch_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(160), nullable=False),
        sa.Column(
            "source_family_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_families.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("attempted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unchanged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quarantined_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discovered_locator_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(120)),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_kb_source_fetch_runs_stable_id",
        "kb_source_fetch_runs",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_source_fetch_runs_source_family_id",
        "kb_source_fetch_runs",
        ["source_family_id"],
    )
    op.create_index(
        "ix_kb_source_fetch_runs_family_started",
        "kb_source_fetch_runs",
        ["source_family_id", "started_at"],
    )

    op.create_table(
        "kb_source_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stable_id", sa.String(180), nullable=False),
        sa.Column(
            "source_family_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_families.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fetch_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_fetch_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kb_source_versions.id", ondelete="SET NULL"),
        ),
        sa.Column("canonical_locator", sa.Text(), nullable=False),
        sa.Column("content_class", sa.String(80), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(160), nullable=False),
        sa.Column("etag", sa.String(500)),
        sa.Column("last_modified", sa.String(200)),
        sa.Column("body_checksum", sa.String(64), nullable=False),
        sa.Column("body_bytes", sa.Integer(), nullable=False),
        sa.Column("raw_artifact_locator", sa.Text()),
        sa.Column("normalized_artifact_locator", sa.Text()),
        sa.Column("parser_version", sa.String(120), nullable=False),
        sa.Column("change_state", sa.String(40), nullable=False),
        sa.Column("quarantine_status", sa.String(40), nullable=False),
        sa.Column("quarantine_reason_code", sa.String(120)),
        sa.Column("review_gates_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_family_id",
            "canonical_locator",
            "body_checksum",
            name="uq_kb_source_candidate_capture",
        ),
    )
    op.create_index(
        "ix_kb_source_candidates_stable_id",
        "kb_source_candidates",
        ["stable_id"],
        unique=True,
    )
    op.create_index(
        "ix_kb_source_candidates_source_family_id",
        "kb_source_candidates",
        ["source_family_id"],
    )
    op.create_index(
        "ix_kb_source_candidates_fetch_run_id",
        "kb_source_candidates",
        ["fetch_run_id"],
    )
    op.create_index(
        "ix_kb_source_candidates_source_version_id",
        "kb_source_candidates",
        ["source_version_id"],
    )
    op.create_index(
        "ix_kb_source_candidates_review_queue",
        "kb_source_candidates",
        ["source_family_id", "quarantine_status", "captured_at"],
    )


def downgrade() -> None:
    op.drop_table("kb_source_candidates")
    op.drop_table("kb_source_fetch_runs")
    op.drop_index("ix_kb_sources_source_family_id", table_name="kb_sources")
    op.drop_constraint(
        "fk_kb_sources_source_family_id",
        "kb_sources",
        type_="foreignkey",
    )
    op.drop_column("kb_sources", "source_family_id")
    op.drop_table("kb_source_families")
