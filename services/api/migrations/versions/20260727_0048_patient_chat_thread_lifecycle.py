"""Add retention-preserving patient chat thread lifecycle state.

Revision ID: 20260727_0048
Revises: 20260726_0047
"""

import sqlalchemy as sa
from alembic import op

revision = "20260727_0048"
down_revision = "20260726_0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_threads",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "chat_threads",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_chat_threads_archived_at",
        "chat_threads",
        ["archived_at"],
        unique=False,
    )
    op.create_index(
        "ix_chat_threads_deleted_at",
        "chat_threads",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chat_threads_deleted_at", table_name="chat_threads")
    op.drop_index("ix_chat_threads_archived_at", table_name="chat_threads")
    op.drop_column("chat_threads", "deleted_at")
    op.drop_column("chat_threads", "archived_at")
