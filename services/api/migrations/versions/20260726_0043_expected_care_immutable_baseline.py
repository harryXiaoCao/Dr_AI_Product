"""Replace doctor-controlled envelopes with immutable published baselines.

Revision ID: 20260726_0043
Revises: 20260726_0042
"""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260726_0043"
down_revision = "20260726_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing Slice E artifacts remain immutable audit history. They are not
    # promoted to baselines because an edited envelope may differ from the
    # original candidate.
    op.execute(
        "DROP TRIGGER trg_expected_care_reviewed_envelopes_append_only "
        "ON expected_care_reviewed_envelopes"
    )
    op.execute(
        """
        UPDATE expected_care_reviewed_envelopes
        SET lifecycle_state = 'legacy_doctor_review_record'
        WHERE lifecycle_state IN ('doctor_approved', 'doctor_edited')
        """
    )
    op.execute(
        """
        UPDATE expected_care_review_heads
        SET current_envelope_id = NULL,
            lifecycle_state = 'generated_pending_validation'
        """
    )
    op.alter_column(
        "expected_care_reviewed_envelopes",
        "doctor_review_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.execute(
        "CREATE TRIGGER trg_expected_care_reviewed_envelopes_append_only "
        "BEFORE UPDATE OR DELETE ON expected_care_reviewed_envelopes "
        "FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()"
    )


def downgrade() -> None:
    # Remove only records introduced by this revision before restoring the
    # former non-null relationship. Legacy Slice E audit rows are preserved.
    for table in (
        "expected_care_clinical_rationales",
        "expected_care_lifecycle_events",
        "expected_care_doctor_reviews",
        "expected_care_envelope_items",
        "expected_care_reviewed_envelopes",
    ):
        op.execute(f"DROP TRIGGER trg_{table}_append_only ON {table}")
    op.execute(
        """
        DELETE FROM expected_care_clinical_rationales
        WHERE doctor_review_id IN (
            SELECT id FROM expected_care_doctor_reviews
            WHERE action IN ('acknowledge', 'concur', 'disagree', 'exception')
        )
        """
    )
    op.execute(
        """
        DELETE FROM expected_care_lifecycle_events
        WHERE doctor_review_id IN (
            SELECT id FROM expected_care_doctor_reviews
            WHERE action IN ('acknowledge', 'concur', 'disagree', 'exception')
        )
        OR envelope_id IN (
            SELECT id FROM expected_care_reviewed_envelopes
            WHERE doctor_review_id IS NULL
        )
        """
    )
    op.execute(
        """
        DELETE FROM expected_care_doctor_reviews
        WHERE action IN ('acknowledge', 'concur', 'disagree', 'exception')
        """
    )
    op.execute(
        """
        DELETE FROM expected_care_envelope_items
        WHERE envelope_id IN (
            SELECT id FROM expected_care_reviewed_envelopes
            WHERE doctor_review_id IS NULL
        )
        """
    )
    op.execute(
        """
        UPDATE expected_care_review_heads
        SET current_envelope_id = NULL
        WHERE current_envelope_id IN (
            SELECT id FROM expected_care_reviewed_envelopes
            WHERE doctor_review_id IS NULL
        )
        """
    )
    op.execute(
        "DELETE FROM expected_care_reviewed_envelopes "
        "WHERE doctor_review_id IS NULL"
    )
    op.alter_column(
        "expected_care_reviewed_envelopes",
        "doctor_review_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    for table in (
        "expected_care_clinical_rationales",
        "expected_care_lifecycle_events",
        "expected_care_doctor_reviews",
        "expected_care_envelope_items",
        "expected_care_reviewed_envelopes",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only "
            f"BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()"
        )
