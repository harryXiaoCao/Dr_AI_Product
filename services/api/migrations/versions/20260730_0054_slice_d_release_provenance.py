"""Bind Slice D candidate requests to the exact governed purpose release.

Revision ID: 20260730_0054
Revises: 20260730_0053
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260730_0054"
down_revision = "20260730_0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "expected_care_candidate_requests",
        sa.Column(
            "ai_purpose_release_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "expected_care_candidate_requests",
        sa.Column(
            "ai_purpose_release_checksum_sha256",
            sa.String(64),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_expected_care_candidate_request_ai_purpose_release",
        "expected_care_candidate_requests",
        "governed_care_releases",
        ["ai_purpose_release_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_expected_care_candidate_request_ai_release_binding",
        "expected_care_candidate_requests",
        (
            "(ai_purpose_release_id IS NULL AND "
            "ai_purpose_release_checksum_sha256 IS NULL) OR "
            "(ai_purpose_release_id IS NOT NULL AND "
            "ai_purpose_release_checksum_sha256 ~ '^[0-9a-f]{64}$')"
        ),
    )
    op.create_index(
        "ix_expected_care_candidate_request_ai_release",
        "expected_care_candidate_requests",
        ["ai_purpose_release_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_expected_care_candidate_request_ai_release",
        table_name="expected_care_candidate_requests",
    )
    op.drop_constraint(
        "ck_expected_care_candidate_request_ai_release_binding",
        "expected_care_candidate_requests",
        type_="check",
    )
    op.drop_constraint(
        "fk_expected_care_candidate_request_ai_purpose_release",
        "expected_care_candidate_requests",
        type_="foreignkey",
    )
    op.drop_column(
        "expected_care_candidate_requests",
        "ai_purpose_release_checksum_sha256",
    )
    op.drop_column("expected_care_candidate_requests", "ai_purpose_release_id")
