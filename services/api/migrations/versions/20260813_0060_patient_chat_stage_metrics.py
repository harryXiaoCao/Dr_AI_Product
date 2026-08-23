"""Add content-free stage telemetry for the staged patient-chat workflow.

Revision ID: 20260813_0060
Revises: 20260813_0059
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260813_0060"
down_revision: str | None = "20260813_0059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chatbot_events",
        sa.Column("provider_call_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chatbot_events",
        sa.Column(
            "provider_stage_metrics_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("chatbot_events", "provider_stage_metrics_json")
    op.drop_column("chatbot_events", "provider_call_count")
