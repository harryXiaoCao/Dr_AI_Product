"""Phase 3 patient-chat metadata-only events.

Revision ID: 20260716_0027
Revises: 20260715_0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0027"
down_revision: str | None = "20260715_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chatbot_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(120), nullable=False),
        sa.Column("actor_role", sa.String(40), nullable=False),
        sa.Column("workflow", sa.String(80), nullable=False),
        sa.Column("query_sha256", sa.String(64), nullable=False),
        sa.Column("query_length", sa.Integer(), nullable=False),
        sa.Column("index_release_id", sa.String(160)),
        sa.Column("retrieved_source_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("retrieved_passage_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("evidence_decision", sa.String(80)),
        sa.Column("model_version", sa.String(160)),
        sa.Column("policy_version", sa.String(120), nullable=False),
        sa.Column("tool_schema_version", sa.String(120), nullable=False),
        sa.Column("safety_code", sa.String(80), nullable=False),
        sa.Column("fallback_code", sa.String(80)),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("provider_input_tokens", sa.Integer()),
        sa.Column("provider_output_tokens", sa.Integer()),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chatbot_events_request_id",
        "chatbot_events",
        ["request_id"],
        unique=True,
    )
    op.create_index("ix_chatbot_events_occurred", "chatbot_events", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_chatbot_events_occurred", table_name="chatbot_events")
    op.drop_index("ix_chatbot_events_request_id", table_name="chatbot_events")
    op.drop_table("chatbot_events")
