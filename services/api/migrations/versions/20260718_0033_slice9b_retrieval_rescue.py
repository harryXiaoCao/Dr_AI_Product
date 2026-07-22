"""Add content-free retrieval-rescue telemetry for Slice 9B.

Revision ID: 20260718_0033
Revises: 20260718_0032
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_0033"
down_revision: str | None = "20260718_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = (
        sa.Column("provider_cost_microunits", sa.Integer()),
        sa.Column("rescue_trigger", sa.String(80)),
        sa.Column("rescue_attempted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rescue_outcome", sa.String(80)),
        sa.Column("rescue_planner_model", sa.String(160)),
        sa.Column("rescue_input_tokens", sa.Integer()),
        sa.Column("rescue_output_tokens", sa.Integer()),
        sa.Column("rescue_cache_hit_tokens", sa.Integer()),
        sa.Column("rescue_cache_miss_tokens", sa.Integer()),
        sa.Column("rescue_latency_ms", sa.Integer()),
        sa.Column("rescue_cost_microunits", sa.Integer()),
        sa.Column("rescue_retrieval_delta", sa.Float()),
        sa.Column("rescue_retry_request_id", sa.String(120)),
    )
    for column in columns:
        op.add_column("chatbot_events", column)
    op.alter_column("chatbot_events", "rescue_attempted", server_default=None)


def downgrade() -> None:
    for name in (
        "rescue_retry_request_id",
        "rescue_retrieval_delta",
        "rescue_cost_microunits",
        "rescue_latency_ms",
        "rescue_cache_miss_tokens",
        "rescue_cache_hit_tokens",
        "rescue_output_tokens",
        "rescue_input_tokens",
        "rescue_planner_model",
        "rescue_outcome",
        "rescue_attempted",
        "rescue_trigger",
        "provider_cost_microunits",
    ):
        op.drop_column("chatbot_events", name)
