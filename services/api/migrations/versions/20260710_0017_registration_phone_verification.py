"""Allow pre-account phone verification challenges.

Revision ID: 20260710_0017
Revises: 20260710_0016
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0017"
down_revision: str | None = "20260710_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "phone_verification_challenges",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("DELETE FROM phone_verification_challenges WHERE user_id IS NULL")
    op.alter_column(
        "phone_verification_challenges",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
