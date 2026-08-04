"""Resolve CEI run-open trigger fields only for the firing table.

Revision ID: 20260802_0057
Revises: 20260802_0056
"""

from alembic import op

revision = "20260802_0057"
down_revision = "20260802_0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_cei_run_open() RETURNS trigger AS $$
        DECLARE target_run uuid;
        BEGIN
          IF TG_TABLE_NAME = 'clinical_event_intelligence_pathway_items' THEN
            SELECT run_id INTO target_run
              FROM clinical_event_intelligence_pathways
              WHERE id = NEW.pathway_id;
          ELSE
            target_run := NEW.run_id;
          END IF;
          IF EXISTS (
            SELECT 1 FROM clinical_event_intelligence_artifacts WHERE run_id=target_run
          ) THEN
            RAISE EXCEPTION 'clinical intelligence run is closed';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_cei_run_open() RETURNS trigger AS $$
        DECLARE target_run uuid;
        BEGIN
          target_run := CASE
            WHEN TG_TABLE_NAME = 'clinical_event_intelligence_pathway_items'
              THEN NEW.pathway_id
            ELSE NEW.run_id
          END;
          IF TG_TABLE_NAME = 'clinical_event_intelligence_pathway_items' THEN
            SELECT run_id INTO target_run
              FROM clinical_event_intelligence_pathways
              WHERE id = NEW.pathway_id;
          END IF;
          IF EXISTS (
            SELECT 1 FROM clinical_event_intelligence_artifacts WHERE run_id=target_run
          ) THEN
            RAISE EXCEPTION 'clinical intelligence run is closed';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        """
    )
