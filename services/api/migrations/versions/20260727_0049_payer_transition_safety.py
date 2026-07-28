"""Add append-only doctor responses and versioned payer transitions.

Revision ID: 20260727_0049
Revises: 20260727_0048
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260727_0049"
down_revision = "20260727_0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payer_requests",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("payer_reviews", sa.Column("request_checksum", sa.String(64), nullable=True))
    op.add_column("payer_reviews", sa.Column("idempotency_key", sa.String(120), nullable=True))
    op.add_column("payer_reviews", sa.Column("from_status", sa.String(40), nullable=True))
    op.add_column("payer_reviews", sa.Column("to_status", sa.String(40), nullable=True))
    op.add_column("payer_reviews", sa.Column("version", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE payer_reviews AS review
        SET request_checksum = repeat('0', 64),
            idempotency_key = 'legacy-' || review.id::text,
            from_status = 'legacy',
            to_status = CASE review.action
                WHEN 'request_clarification' THEN 'clarification_requested'
                WHEN 'accept' THEN 'accepted'
                WHEN 'reject' THEN 'rejected'
                WHEN 'escalate' THEN 'escalated'
                WHEN 'close' THEN 'closed'
                ELSE 'legacy'
            END,
            version = numbered.ordinal
        FROM (
            SELECT id, row_number() OVER (
                PARTITION BY payer_request_id ORDER BY created_at, id
            ) + 1 AS ordinal
            FROM payer_reviews
        ) AS numbered
        WHERE numbered.id = review.id
        """
    )
    for column in ("request_checksum", "idempotency_key", "from_status", "to_status", "version"):
        op.alter_column("payer_reviews", column, nullable=False)
    op.create_unique_constraint(
        "uq_payer_review_idempotency",
        "payer_reviews",
        ["payer_request_id", "payer_membership_id", "idempotency_key"],
    )
    op.create_table(
        "payer_doctor_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payer_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "baseline_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expected_care_reviewed_envelopes.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "comparison_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expected_care_comparisons.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("response_type", sa.String(40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("request_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "payer_request_id",
            "doctor_id",
            "idempotency_key",
            name="uq_payer_doctor_response_idempotency",
        ),
    )
    op.create_index(
        "ix_payer_doctor_response_request_created",
        "payer_doctor_responses",
        ["payer_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("payer_doctor_responses")
    op.drop_constraint("uq_payer_review_idempotency", "payer_reviews", type_="unique")
    for column in ("version", "to_status", "from_status", "idempotency_key", "request_checksum"):
        op.drop_column("payer_reviews", column)
    op.drop_column("payer_requests", "version")
