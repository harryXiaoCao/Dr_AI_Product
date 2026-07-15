"""Reconcile knowledge-table database metadata with SQLAlchemy models.

Revision ID: 20260715_0026
Revises: 20260715_0025
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260715_0026"
down_revision: str | None = "20260715_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP_COLUMNS = (
    ("kb_index_releases", "created_at"),
    ("kb_passages", "created_at"),
    ("kb_publishers", "created_at"),
    ("kb_retrieval_events", "occurred_at"),
    ("kb_reviews", "created_at"),
    ("kb_rights_records", "created_at"),
    ("kb_sections", "created_at"),
    ("kb_source_versions", "created_at"),
    ("kb_sources", "created_at"),
    ("kb_sources", "updated_at"),
    ("kb_summary_artifacts", "created_at"),
    ("kb_terms", "created_at"),
    ("kb_translation_artifacts", "created_at"),
    ("kb_translation_sections", "created_at"),
)

REDUNDANT_UNIQUE_CONSTRAINTS = (
    ("kb_index_releases_stable_id_key", "kb_index_releases", "stable_id"),
    ("kb_passages_stable_id_key", "kb_passages", "stable_id"),
    ("kb_publishers_stable_id_key", "kb_publishers", "stable_id"),
    ("kb_retrieval_events_request_id_key", "kb_retrieval_events", "request_id"),
    ("kb_reviews_stable_id_key", "kb_reviews", "stable_id"),
    ("kb_rights_records_stable_id_key", "kb_rights_records", "stable_id"),
    ("kb_sections_stable_id_key", "kb_sections", "stable_id"),
    ("kb_source_versions_stable_id_key", "kb_source_versions", "stable_id"),
    ("kb_sources_stable_id_key", "kb_sources", "stable_id"),
    ("kb_summary_artifacts_stable_id_key", "kb_summary_artifacts", "stable_id"),
    ("kb_terms_stable_id_key", "kb_terms", "stable_id"),
    ("kb_translation_artifacts_stable_id_key", "kb_translation_artifacts", "stable_id"),
    ("kb_translation_sections_stable_id_key", "kb_translation_sections", "stable_id"),
)


def upgrade() -> None:
    for table_name, column_name in TIMESTAMP_COLUMNS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
    for constraint_name, table_name, _ in REDUNDANT_UNIQUE_CONSTRAINTS:
        op.drop_constraint(constraint_name, table_name, type_="unique")


def downgrade() -> None:
    for constraint_name, table_name, column_name in REDUNDANT_UNIQUE_CONSTRAINTS:
        op.create_unique_constraint(constraint_name, table_name, [column_name])
    for table_name, column_name in reversed(TIMESTAMP_COLUMNS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )
