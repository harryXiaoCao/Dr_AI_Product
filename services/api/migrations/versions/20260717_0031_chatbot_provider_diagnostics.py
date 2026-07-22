"""Add content-free chatbot provider diagnostics.

Revision ID: 20260717_0031
Revises: 20260717_0030
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0031"
down_revision: str | None = "20260717_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chatbot_events",
        sa.Column("provider_error_code", sa.String(120)),
    )
    op.add_column(
        "chatbot_events",
        sa.Column("provider_attempt_count", sa.Integer()),
    )


def downgrade() -> None:
    op.drop_column("chatbot_events", "provider_attempt_count")
    op.drop_column("chatbot_events", "provider_error_code")
