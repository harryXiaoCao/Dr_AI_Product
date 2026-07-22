"""Reconcile care-cost constraints with the SQLAlchemy model.

Revision ID: 20260723_0036
Revises: 20260723_0035
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0036"
down_revision: str | None = "20260723_0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name, column_names in (
        ("payer_organizations", ("created_at",)),
        ("payer_memberships", ("created_at",)),
        ("care_cost_items", ("created_at", "updated_at")),
        ("payer_requests", ("created_at", "updated_at")),
        ("payer_request_lines", ("created_at",)),
        ("payer_reviews", ("created_at",)),
    ):
        for column_name in column_names:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=True),
                nullable=False,
            )

    op.drop_constraint(
        "uq_payer_organizations_name",
        "payer_organizations",
        type_="unique",
    )
    op.drop_index("ix_payer_organizations_name", table_name="payer_organizations")
    op.create_index(
        "ix_payer_organizations_name",
        "payer_organizations",
        ["name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_payer_organizations_name", table_name="payer_organizations")
    op.create_index(
        "ix_payer_organizations_name",
        "payer_organizations",
        ["name"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_payer_organizations_name",
        "payer_organizations",
        ["name"],
    )

    for table_name, column_names in (
        ("payer_organizations", ("created_at",)),
        ("payer_memberships", ("created_at",)),
        ("care_cost_items", ("created_at", "updated_at")),
        ("payer_requests", ("created_at", "updated_at")),
        ("payer_request_lines", ("created_at",)),
        ("payer_reviews", ("created_at",)),
    ):
        for column_name in column_names:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
