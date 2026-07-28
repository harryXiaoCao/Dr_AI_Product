"""Make governed care releases append-only after operational state moved to events.

Revision ID: 20260726_0047
Revises: 20260726_0046
"""

from alembic import op

revision = "20260726_0047"
down_revision = "20260726_0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_governed_care_release_content()
        RETURNS trigger AS $$
        DECLARE
            has_activation boolean;
        BEGIN
            SELECT EXISTS (
                SELECT 1
                FROM governed_care_release_activations
                WHERE release_id = OLD.id
            ) INTO has_activation;
            IF has_activation THEN
                RAISE EXCEPTION 'activated governed care releases are immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_activated_care_release_child()
        RETURNS trigger AS $$
        DECLARE
            release_uuid uuid;
            has_activation boolean;
        BEGIN
            release_uuid := ((CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD)
                                   ELSE to_jsonb(NEW) END) ->> TG_ARGV[0])::uuid;
            SELECT EXISTS (
                SELECT 1
                FROM governed_care_release_activations
                WHERE release_id = release_uuid
            ) INTO has_activation;
            IF has_activation THEN
                RAISE EXCEPTION 'activated care release children are immutable';
            END IF;
            RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$ LANGUAGE plpgsql
        """
    )


def downgrade() -> None:
    # Restoring lifecycle-derived mutability would make operational correctness
    # depend on mutable release rows again. A full downgrade through migration
    # 0040 removes these functions with their tables.
    pass
