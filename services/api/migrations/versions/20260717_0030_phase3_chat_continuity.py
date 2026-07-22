"""Add patient AI-chat continuity and minimum retention metadata.

Revision ID: 20260717_0030
Revises: 20260717_0029
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0030"
down_revision: str | None = "20260717_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chat_threads",
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_chat_threads_retention_until",
        "chat_threads",
        ["retention_until"],
        unique=False,
    )
    op.alter_column("chat_messages", "actor_user_id", nullable=True)


def downgrade() -> None:
    op.execute(
        "DELETE FROM chat_messages WHERE actor_user_id IS NULL"
    )
    op.alter_column("chat_messages", "actor_user_id", nullable=False)
    op.drop_index("ix_chat_threads_retention_until", table_name="chat_threads")
    op.drop_column("chat_threads", "retention_until")
