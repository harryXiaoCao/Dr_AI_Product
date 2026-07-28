"""Harden append-only release sequencing and synthetic-stage statuses.

Revision ID: 20260726_0046
Revises: 20260726_0045
"""

import sqlalchemy as sa
from alembic import op

revision = "20260726_0046"
down_revision = "20260726_0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "governed_care_releases",
        "rights_status",
        existing_type=sa.String(length=40),
        type_=sa.String(length=80),
        existing_nullable=False,
    )
    op.alter_column(
        "governed_care_release_reviews",
        "decision",
        existing_type=sa.String(length=40),
        type_=sa.String(length=80),
        existing_nullable=False,
    )
    op.add_column(
        "expected_care_explanation_release_events",
        sa.Column(
            "sequence",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_expected_care_explanation_release_event_sequence",
        "expected_care_explanation_release_events",
        ["sequence"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_expected_care_explanation_release_event_sequence",
        "expected_care_explanation_release_events",
        type_="unique",
    )
    op.drop_column("expected_care_explanation_release_events", "sequence")
    # Width is intentionally not narrowed: rows may contain the exact
    # synthetic-stage waiver states. Migration 0040 removes these tables on a
    # full downgrade.
