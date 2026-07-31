"""Add Phase 5 support lifecycle and content-free product analytics.

Revision ID: 20260728_0052
Revises: 20260727_0051
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260728_0052"
down_revision = "20260727_0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("support_requests", sa.Column("public_reference", sa.String(32)))
    op.add_column("support_requests", sa.Column("idempotency_key", sa.String(120)))
    op.add_column("support_requests", sa.Column("request_checksum", sa.String(64)))
    op.add_column(
        "support_requests",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "support_requests",
        sa.Column(
            "retention_boundary_code",
            sa.String(80),
            nullable=False,
            server_default="standard_support_retention",
        ),
    )
    op.add_column(
        "support_requests",
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        """
        UPDATE support_requests
        SET public_reference =
            'REQ-' || upper(substring(replace(id::text, '-', ''), 1, 12))
        WHERE public_reference IS NULL
        """
    )
    op.execute(
        """
        UPDATE support_requests
        SET retention_boundary_code = 'regulated_and_audit_retention_applies'
        WHERE request_type = 'deletion'
        """
    )
    op.alter_column("support_requests", "public_reference", nullable=False)
    op.create_unique_constraint(
        "uq_support_request_public_reference",
        "support_requests",
        ["public_reference"],
    )
    op.create_unique_constraint(
        "uq_support_request_idempotency",
        "support_requests",
        ["requester_user_id", "idempotency_key"],
    )

    op.create_table(
        "support_request_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "support_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("actor_kind", sa.String(40), nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("public_summary_code", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "support_request_id",
            "sequence",
            name="uq_support_request_event_sequence",
        ),
        sa.UniqueConstraint(
            "support_request_id",
            "idempotency_key",
            name="uq_support_request_event_idempotency",
        ),
    )
    op.create_index(
        "ix_support_request_events_request_created",
        "support_request_events",
        ["support_request_id", "created_at"],
    )
    op.execute(
        """
        INSERT INTO support_request_events (
            id,
            support_request_id,
            sequence,
            event_type,
            from_status,
            to_status,
            actor_kind,
            actor_user_id,
            public_summary_code,
            idempotency_key,
            request_checksum,
            created_at
        )
        SELECT
            gen_random_uuid(),
            id,
            1,
            'submitted',
            NULL,
            status,
            'requester',
            requester_user_id,
            'request_submitted',
            'legacy-' || id::text,
            repeat('0', 64),
            created_at
        FROM support_requests
        """
    )

    op.add_column("analytics_events", sa.Column("role", sa.String(40)))
    op.add_column("analytics_events", sa.Column("environment", sa.String(40)))
    op.add_column("analytics_events", sa.Column("schema_version", sa.String(40)))
    op.add_column("analytics_events", sa.Column("deduplication_key", sa.String(64)))
    op.add_column("analytics_events", sa.Column("event_checksum", sa.String(64)))
    op.add_column("analytics_events", sa.Column("outcome", sa.String(40)))
    op.add_column("analytics_events", sa.Column("failure_category", sa.String(60)))
    op.add_column("analytics_events", sa.Column("latency_ms", sa.Integer()))
    op.execute(
        """
        UPDATE analytics_events
        SET
            role = 'system',
            environment = 'legacy',
            schema_version = 'legacy',
            deduplication_key = 'legacy-' || id::text
        WHERE schema_version IS NULL
        """
    )
    for column in ("role", "environment", "schema_version", "deduplication_key"):
        op.alter_column("analytics_events", column, nullable=False)
    op.create_unique_constraint(
        "uq_analytics_event_environment_dedupe",
        "analytics_events",
        ["environment", "deduplication_key"],
    )
    op.create_check_constraint(
        "ck_content_free_analytics_has_no_identity",
        "analytics_events",
        """
        schema_version <> 'content_free_product_v1'
        OR (
            actor_user_id IS NULL
            AND patient_id IS NULL
            AND clinic_id IS NULL
            AND resource_id IS NULL
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_content_free_analytics_has_no_identity",
        "analytics_events",
        type_="check",
    )
    op.drop_constraint(
        "uq_analytics_event_environment_dedupe",
        "analytics_events",
        type_="unique",
    )
    for column in (
        "latency_ms",
        "failure_category",
        "outcome",
        "event_checksum",
        "deduplication_key",
        "schema_version",
        "environment",
        "role",
    ):
        op.drop_column("analytics_events", column)

    op.drop_index(
        "ix_support_request_events_request_created",
        table_name="support_request_events",
    )
    op.drop_table("support_request_events")
    op.drop_constraint(
        "uq_support_request_idempotency",
        "support_requests",
        type_="unique",
    )
    op.drop_constraint(
        "uq_support_request_public_reference",
        "support_requests",
        type_="unique",
    )
    for column in (
        "withdrawn_at",
        "retention_boundary_code",
        "version",
        "request_checksum",
        "idempotency_key",
        "public_reference",
    ):
        op.drop_column("support_requests", column)
