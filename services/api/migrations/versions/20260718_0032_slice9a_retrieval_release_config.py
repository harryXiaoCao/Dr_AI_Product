"""Add release-specific passage embedding lineage for Slice 9A.

Revision ID: 20260718_0032
Revises: 20260717_0031
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_0032"
down_revision: str | None = "20260717_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("kb_passages", sa.Column("embedding_model_version", sa.String(160)))
    op.execute(
        "UPDATE kb_passages SET embedding_model_version = "
        "'dr-ai-hashed-multilingual-v1' WHERE embedding_json IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("kb_passages", "embedding_model_version")
