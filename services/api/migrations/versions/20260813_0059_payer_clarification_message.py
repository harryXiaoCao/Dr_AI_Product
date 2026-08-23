"""Separate doctor-visible clarification messages from payer-private notes.

Revision ID: 20260813_0059
Revises: 20260802_0058
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0059"
down_revision: str | None = "20260802_0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payer_reviews",
        sa.Column("clarification_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payer_reviews", "clarification_message")
