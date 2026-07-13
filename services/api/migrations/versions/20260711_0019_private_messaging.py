"""Add connected doctor-patient private messaging.

Revision ID: 20260711_0019
Revises: 20260710_0018
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260711_0019"
down_revision: str | None = "20260710_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chat_threads", sa.Column("doctor_id", sa.Uuid(), nullable=True))
    op.add_column(
        "chat_threads",
        sa.Column("thread_type", sa.String(length=40), nullable=False, server_default="educational"),
    )
    op.create_foreign_key(
        "fk_chat_threads_doctor_id",
        "chat_threads",
        "doctor_profiles",
        ["doctor_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_chat_threads_doctor_updated", "chat_threads", ["doctor_id", "last_message_at"])
    op.add_column("chat_messages", sa.Column("content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_messages", "content")
    op.drop_index("ix_chat_threads_doctor_updated", table_name="chat_threads")
    op.drop_constraint("fk_chat_threads_doctor_id", "chat_threads", type_="foreignkey")
    op.drop_column("chat_threads", "thread_type")
    op.drop_column("chat_threads", "doctor_id")
