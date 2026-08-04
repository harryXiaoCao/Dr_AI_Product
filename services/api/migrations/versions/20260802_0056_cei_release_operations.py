"""Add content-bound idempotency to governed release operations.

Revision ID: 20260802_0056
Revises: 20260801_0055
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260802_0056"
down_revision = "20260801_0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "governed_care_release_activations",
        sa.Column("idempotency_key", sa.String(120), nullable=True),
    )
    op.add_column(
        "governed_care_release_activations",
        sa.Column("operation_checksum_sha256", sa.String(64), nullable=True),
    )
    op.add_column(
        "governed_care_release_activations",
        sa.Column(
            "evidence_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_unique_constraint(
        "uq_governed_care_release_activation_idempotency",
        "governed_care_release_activations",
        ["release_type", "release_key", "scope_key", "idempotency_key"],
    )
    op.create_check_constraint(
        "ck_governed_care_release_activation_idempotency",
        "governed_care_release_activations",
        "(idempotency_key IS NULL AND operation_checksum_sha256 IS NULL) OR "
        "(length(btrim(idempotency_key)) > 0 AND "
        "operation_checksum_sha256 ~ '^[0-9a-f]{64}$')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_governed_care_release_activation_idempotency",
        "governed_care_release_activations",
        type_="check",
    )
    op.drop_constraint(
        "uq_governed_care_release_activation_idempotency",
        "governed_care_release_activations",
        type_="unique",
    )
    op.drop_column("governed_care_release_activations", "evidence_json")
    op.drop_column("governed_care_release_activations", "operation_checksum_sha256")
    op.drop_column("governed_care_release_activations", "idempotency_key")
