"""Add immutable patient-chat generation release governance.

Revision ID: 20260727_0050
Revises: 20260727_0049
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260727_0050"
down_revision = "20260727_0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chatbot_generation_releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "predecessor_release_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("release_key", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=120), nullable=False),
        sa.Column("purpose_code", sa.String(length=80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(length=120), nullable=False),
        sa.Column("grounded_schema_version", sa.String(length=120), nullable=False),
        sa.Column("general_schema_version", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("contract_checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "evaluation_manifest_checksum_sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "evaluation_result_checksum_sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "machine_gates_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("content_checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_release_id"],
            ["chatbot_generation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "content_checksum_sha256",
            name="uq_chatbot_generation_release_content_checksum",
        ),
        sa.UniqueConstraint(
            "release_key",
            "version",
            name="uq_chatbot_generation_release_version",
        ),
    )
    op.create_index(
        "ix_chatbot_generation_releases_purpose_code",
        "chatbot_generation_releases",
        ["purpose_code"],
        unique=False,
    )
    op.create_table(
        "chatbot_generation_active_releases",
        sa.Column("purpose_code", sa.String(length=80), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["chatbot_generation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("purpose_code"),
        sa.UniqueConstraint(
            "release_id",
            name="uq_chatbot_generation_active_release_id",
        ),
    )
    op.create_table(
        "chatbot_generation_release_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose_code", sa.String(length=80), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_release_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column(
            "evidence_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("content_checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["chatbot_generation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_release_id"],
            ["chatbot_generation_releases.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "purpose_code",
            "event_type",
            "idempotency_key",
            name="uq_chatbot_generation_release_event_idempotency",
        ),
    )
    op.create_index(
        "ix_chatbot_generation_release_event_occurred",
        "chatbot_generation_release_events",
        ["purpose_code", "occurred_at"],
        unique=False,
    )
    op.execute(
        """
        CREATE FUNCTION guard_immutable_chatbot_generation_rows()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'chatbot generation release evidence is immutable';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in (
        "chatbot_generation_releases",
        "chatbot_generation_release_events",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_guard_{table}
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION guard_immutable_chatbot_generation_rows()
            """
        )


def downgrade() -> None:
    for table in (
        "chatbot_generation_release_events",
        "chatbot_generation_releases",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_guard_{table} ON {table}")
    op.execute("DROP FUNCTION IF EXISTS guard_immutable_chatbot_generation_rows()")
    op.drop_index(
        "ix_chatbot_generation_release_event_occurred",
        table_name="chatbot_generation_release_events",
    )
    op.drop_table("chatbot_generation_release_events")
    op.drop_table("chatbot_generation_active_releases")
    op.drop_index(
        "ix_chatbot_generation_releases_purpose_code",
        table_name="chatbot_generation_releases",
    )
    op.drop_table("chatbot_generation_releases")
