"""Store immutable embeddings on index release passage snapshots.

Revision ID: 20260720_0034
Revises: 20260718_0033
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0034"
down_revision: str | None = "20260718_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "kb_index_release_passages",
        sa.Column("embedding_json", postgresql.JSONB(astext_type=sa.Text())),
    )
    op.add_column(
        "kb_index_release_passages",
        sa.Column("embedding_model_version", sa.String(160)),
    )
    op.execute(
        """
        UPDATE kb_index_release_passages AS link
        SET embedding_json = passage.embedding_json,
            embedding_model_version = passage.embedding_model_version
        FROM kb_passages AS passage
        WHERE passage.id = link.passage_id
        """
    )


def downgrade() -> None:
    op.drop_column("kb_index_release_passages", "embedding_model_version")
    op.drop_column("kb_index_release_passages", "embedding_json")
