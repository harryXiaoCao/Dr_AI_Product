"""Add patient chatbot grounding-mode telemetry.

Revision ID: 20260724_0039
Revises: 20260724_0038
"""

import sqlalchemy as sa
from alembic import op

revision = "20260724_0039"
down_revision = "20260724_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chatbot_events", sa.Column("grounding_mode", sa.String(80)))
    op.add_column("chatbot_events", sa.Column("original_retrieval_adequate", sa.Boolean()))
    op.add_column(
        "chatbot_events",
        sa.Column("searched_query_variant_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("chatbot_events", sa.Column("retrieval_decision", sa.String(80)))
    op.add_column(
        "chatbot_events",
        sa.Column(
            "general_knowledge_eligible", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column("chatbot_events", sa.Column("general_knowledge_outcome", sa.String(80)))
    op.add_column("chatbot_events", sa.Column("answer_schema_version", sa.String(120)))
    op.add_column(
        "chatbot_events",
        sa.Column(
            "structured_output_repair_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.alter_column("chatbot_events", "searched_query_variant_count", server_default=None)
    op.alter_column("chatbot_events", "general_knowledge_eligible", server_default=None)
    op.alter_column("chatbot_events", "structured_output_repair_count", server_default=None)


def downgrade() -> None:
    for column in (
        "structured_output_repair_count",
        "answer_schema_version",
        "general_knowledge_outcome",
        "general_knowledge_eligible",
        "retrieval_decision",
        "searched_query_variant_count",
        "original_retrieval_adequate",
        "grounding_mode",
    ):
        op.drop_column("chatbot_events", column)
