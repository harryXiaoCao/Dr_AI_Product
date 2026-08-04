# ruff: noqa: E501
"""Add immutable Clinical Event Intelligence persistence.

Revision ID: 20260801_0055
Revises: 20260730_0054
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260801_0055"
down_revision = "20260730_0054"
branch_labels = None
depends_on = None


def _uuid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _json(name: str, default: str | None = None) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(default) if default else None,
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    for table, columns in (
        (
            "hospitals",
            [
                sa.Column("organization_code", sa.String(80)),
                sa.Column("jurisdiction_code", sa.String(40)),
                sa.Column("country_code", sa.String(8)),
                sa.Column("province", sa.String(80)),
                sa.Column("city", sa.String(80)),
            ],
        ),
        (
            "clinics",
            [
                sa.Column("facility_code", sa.String(80)),
                sa.Column("facility_level", sa.String(60)),
                sa.Column("department_code", sa.String(80)),
            ],
        ),
        (
            "clinical_events",
            [
                sa.Column("hospital_id", postgresql.UUID(as_uuid=True)),
                sa.Column("clinic_id", postgresql.UUID(as_uuid=True)),
                sa.Column("department_code", sa.String(80)),
                sa.Column("encounter_at", sa.DateTime(timezone=True)),
            ],
        ),
    ):
        for column in columns:
            op.add_column(table, column)
    op.create_foreign_key(
        "fk_clinical_event_hospital",
        "clinical_events",
        "hospitals",
        ["hospital_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_clinical_event_clinic",
        "clinical_events",
        "clinics",
        ["clinic_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_clinical_event_facility", "clinical_events", ["hospital_id", "clinic_id"])
    op.add_column("payer_request_lines", sa.Column("code_system", sa.String(80)))
    op.add_column("payer_request_lines", sa.Column("service_code", sa.String(120)))
    op.add_column(
        "payer_request_lines",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "payer_request_lines",
        sa.Column("unit", sa.String(80), nullable=False, server_default="item"),
    )
    op.create_check_constraint(
        "ck_payer_request_line_quantity", "payer_request_lines", "quantity > 0"
    )
    op.create_check_constraint(
        "ck_payer_request_line_unit", "payer_request_lines", "length(btrim(unit)) > 0"
    )

    op.create_table(
        "clinical_event_intelligence_snapshots",
        _uuid("id"),
        _uuid("predecessor_snapshot_id", nullable=True),
        _uuid("payer_request_id"),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("payer_request_version", sa.Integer(), nullable=False),
        _uuid("patient_id"),
        _uuid("clinical_event_id"),
        _uuid("doctor_id"),
        _uuid("payer_organization_id"),
        _uuid("hospital_id", nullable=True),
        _uuid("clinic_id", nullable=True),
        sa.Column("department_code", sa.String(80)),
        sa.Column("jurisdiction_code", sa.String(40)),
        sa.Column("province", sa.String(80)),
        sa.Column("city", sa.String(80)),
        sa.Column("facility_level", sa.String(60)),
        sa.Column("encounter_at", sa.DateTime(timezone=True)),
        sa.Column("service_date_from", sa.Date(), nullable=False),
        sa.Column("service_date_to", sa.Date(), nullable=False),
        sa.Column("snapshot_contract_version", sa.String(80), nullable=False),
        sa.Column("snapshot_checksum_sha256", sa.String(64), nullable=False),
        _json("snapshot_json"),
        _json("source_lineage_json", "'[]'::jsonb"),
        _json("quality_flags_json", "'[]'::jsonb"),
        _created(),
        sa.ForeignKeyConstraint(
            ["predecessor_snapshot_id"],
            ["clinical_event_intelligence_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_event_id"], ["clinical_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["payer_organization_id"], ["payer_organizations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "payer_request_id", "snapshot_version", name="uq_cei_snapshot_request_version"
        ),
        sa.CheckConstraint(
            "snapshot_version > 0 AND payer_request_version > 0", name="ck_cei_snapshot_version"
        ),
        sa.CheckConstraint(
            "service_date_to >= service_date_from", name="ck_cei_snapshot_service_dates"
        ),
        sa.CheckConstraint(
            "snapshot_checksum_sha256 ~ '^[0-9a-f]{64}$'", name="ck_cei_snapshot_checksum"
        ),
    )
    op.create_index(
        "ix_cei_snapshot_scope",
        "clinical_event_intelligence_snapshots",
        ["clinical_event_id", "created_at"],
    )

    op.create_table(
        "clinical_event_intelligence_runs",
        _uuid("id"),
        _uuid("snapshot_id"),
        _uuid("predecessor_run_id", nullable=True),
        _uuid("actor_user_id"),
        _uuid("payer_request_id"),
        sa.Column("run_version", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("request_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("purpose_code", sa.String(80), nullable=False),
        sa.Column("purpose_contract_version", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(80), nullable=False),
        sa.Column("model_configuration_version", sa.String(80), nullable=False),
        sa.Column("validator_version", sa.String(80), nullable=False),
        sa.Column("score_version", sa.String(80), nullable=False),
        _uuid("primary_release_id"),
        _uuid("critic_release_id", nullable=True),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        _created(),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["clinical_event_intelligence_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["primary_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["critic_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_user_id", "payer_request_id", "idempotency_key", name="uq_cei_run_idempotency"
        ),
        sa.UniqueConstraint("snapshot_id", "run_version", name="uq_cei_run_snapshot_version"),
        sa.CheckConstraint("run_version > 0", name="ck_cei_run_version"),
        sa.CheckConstraint(
            "request_checksum_sha256 ~ '^[0-9a-f]{64}$'", name="ck_cei_run_checksum"
        ),
    )

    op.create_table(
        "clinical_event_intelligence_retrieval_sources",
        _uuid("id"),
        _uuid("run_id"),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(60), nullable=False),
        _uuid("governed_release_id", nullable=True),
        _uuid("pricing_reference_item_id", nullable=True),
        sa.Column("provenance_tier", sa.Integer(), nullable=False),
        sa.Column("scope_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("lineage_checksum_sha256", sa.String(64), nullable=False),
        _json("source_lineage_json"),
        _created(),
        sa.ForeignKeyConstraint(
            ["run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["governed_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["pricing_reference_item_id"], ["pricing_reference_items.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "ordinal", name="uq_cei_retrieval_ordinal"),
        sa.CheckConstraint("ordinal >= 0", name="ck_cei_retrieval_ordinal"),
        sa.CheckConstraint("provenance_tier BETWEEN 1 AND 4", name="ck_cei_retrieval_tier"),
    )
    op.create_table(
        "clinical_event_intelligence_pathways",
        _uuid("id"),
        _uuid("run_id"),
        sa.Column("pathway_key", sa.String(120), nullable=False),
        sa.Column("pathway_type", sa.String(40), nullable=False),
        sa.Column("usefulness", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        _json("supporting_facts_json", "'[]'::jsonb"),
        _json("contradicting_facts_json", "'[]'::jsonb"),
        _json("missing_information_json", "'[]'::jsonb"),
        _json("assumptions_json", "'[]'::jsonb"),
        _created(),
        sa.ForeignKeyConstraint(
            ["run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "pathway_key", name="uq_cei_pathway_key"),
        sa.CheckConstraint(
            "pathway_type IN ('typical_first_line','reasonable_alternative','escalated')",
            name="ck_cei_pathway_type",
        ),
        sa.CheckConstraint("confidence BETWEEN 0 AND 100", name="ck_cei_pathway_confidence"),
        sa.CheckConstraint("length(btrim(usefulness)) > 0", name="ck_cei_pathway_usefulness"),
    )
    op.create_table(
        "clinical_event_intelligence_pathway_items",
        _uuid("id"),
        _uuid("pathway_id"),
        sa.Column("item_key", sa.String(160), nullable=False),
        sa.Column("label", sa.String(240), nullable=False),
        sa.Column("code_system", sa.String(80)),
        sa.Column("service_code", sa.String(120)),
        sa.Column("unit", sa.String(80), nullable=False),
        sa.Column("quantity_low", sa.Integer(), nullable=False),
        sa.Column("quantity_high", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("cost_low_minor", sa.Integer(), nullable=False),
        sa.Column("cost_high_minor", sa.Integer(), nullable=False),
        sa.Column("predicted_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created(),
        sa.ForeignKeyConstraint(
            ["pathway_id"], ["clinical_event_intelligence_pathways.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pathway_id", "item_key", name="uq_cei_pathway_item"),
        sa.CheckConstraint(
            "quantity_low >= 0 AND quantity_high >= quantity_low",
            name="ck_cei_pathway_item_quantity",
        ),
        sa.CheckConstraint(
            "cost_low_minor >= 0 AND cost_high_minor >= cost_low_minor",
            name="ck_cei_pathway_item_cost",
        ),
        sa.CheckConstraint("predicted_only", name="ck_cei_pathway_item_predicted"),
    )
    op.create_table(
        "clinical_event_intelligence_provider_attempts",
        _uuid("id"),
        _uuid("run_id"),
        sa.Column("pass_type", sa.String(20), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("outcome", sa.String(60), nullable=False),
        sa.Column("diagnostic_code", sa.String(120)),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_microunits", sa.Integer()),
        sa.Column("output_checksum_sha256", sa.String(64)),
        _created(),
        sa.ForeignKeyConstraint(
            ["run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "pass_type", "attempt_number", name="uq_cei_provider_attempt"
        ),
        sa.CheckConstraint("pass_type IN ('primary','critic')", name="ck_cei_attempt_pass"),
        sa.CheckConstraint(
            "attempt_number > 0 AND (pass_type <> 'critic' OR attempt_number = 1)",
            name="ck_cei_attempt_number",
        ),
        sa.CheckConstraint("latency_ms >= 0", name="ck_cei_attempt_latency"),
    )
    op.create_table(
        "clinical_event_intelligence_item_assessments",
        _uuid("id"),
        _uuid("run_id"),
        _uuid("payer_request_line_id"),
        _uuid("retrieval_source_id", nullable=True),
        sa.Column("requested_label", sa.String(240), nullable=False),
        sa.Column("requested_code", sa.String(120)),
        sa.Column("requested_quantity", sa.Integer(), nullable=False),
        sa.Column("requested_unit", sa.String(80), nullable=False),
        sa.Column("requested_amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("estimated_quantity_low", sa.Integer(), nullable=False),
        sa.Column("estimated_quantity_high", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_low_minor", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_high_minor", sa.Integer(), nullable=False),
        sa.Column("clinical_fit", sa.Integer(), nullable=False),
        sa.Column("evidence_support", sa.Integer(), nullable=False),
        sa.Column("timing_sequence", sa.Integer(), nullable=False),
        sa.Column("quantity_intensity", sa.Integer(), nullable=False),
        sa.Column("documentation_completeness", sa.Integer(), nullable=False),
        sa.Column("cost_alignment", sa.Integer(), nullable=False),
        sa.Column("cost_alignment_weight_bp", sa.Integer(), nullable=False),
        sa.Column("ai_support_score", sa.Integer(), nullable=False),
        sa.Column("support_band", sa.String(80), nullable=False),
        sa.Column("score_version", sa.String(80), nullable=False),
        sa.Column("provenance_tier", sa.Integer(), nullable=False),
        sa.Column("exploratory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("wide_uncertainty", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("usefulness", sa.Text(), nullable=False),
        _json("mapped_pathways_json", "'[]'::jsonb"),
        _json("supporting_facts_json", "'[]'::jsonb"),
        _json("contradicting_facts_json", "'[]'::jsonb"),
        _json("missing_information_json", "'[]'::jsonb"),
        _json("alternatives_json", "'[]'::jsonb"),
        _json("source_lineage_json", "'[]'::jsonb"),
        _json("brief_comments_json", "'[]'::jsonb"),
        _json("validation_results_json"),
        sa.Column("disagreement_state", sa.String(40), nullable=False),
        _created(),
        sa.ForeignKeyConstraint(
            ["run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["payer_request_line_id"], ["payer_request_lines.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_source_id"],
            ["clinical_event_intelligence_retrieval_sources.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "payer_request_line_id", name="uq_cei_assessment_request_line"
        ),
        sa.CheckConstraint(
            "requested_quantity > 0 AND requested_amount_minor >= 0",
            name="ck_cei_assessment_requested",
        ),
        sa.CheckConstraint(
            "estimated_quantity_low >= 0 AND estimated_quantity_high >= estimated_quantity_low",
            name="ck_cei_assessment_quantity",
        ),
        sa.CheckConstraint(
            "estimated_cost_low_minor >= 0 AND estimated_cost_high_minor >= estimated_cost_low_minor",
            name="ck_cei_assessment_cost",
        ),
        sa.CheckConstraint(
            "clinical_fit BETWEEN 0 AND 100 AND evidence_support BETWEEN 0 AND 100 AND timing_sequence BETWEEN 0 AND 100 AND quantity_intensity BETWEEN 0 AND 100 AND documentation_completeness BETWEEN 0 AND 100 AND cost_alignment BETWEEN 0 AND 100 AND ai_support_score BETWEEN 0 AND 100 AND confidence BETWEEN 0 AND 100",
            name="ck_cei_assessment_scores",
        ),
        sa.CheckConstraint(
            "cost_alignment_weight_bp BETWEEN 0 AND 10000", name="ck_cei_assessment_weight"
        ),
        sa.CheckConstraint("provenance_tier BETWEEN 1 AND 5", name="ck_cei_assessment_tier"),
        sa.CheckConstraint(
            "(provenance_tier = 5 AND exploratory AND wide_uncertainty AND retrieval_source_id IS NULL AND cost_alignment_weight_bp = 0) OR (provenance_tier < 5 AND NOT exploratory AND retrieval_source_id IS NOT NULL)",
            name="ck_cei_assessment_provenance",
        ),
        sa.CheckConstraint("length(btrim(usefulness)) > 0", name="ck_cei_assessment_usefulness"),
        sa.CheckConstraint(
            "disagreement_state IN ('agreement','partial_disagreement','material_disagreement','unavailable')",
            name="ck_cei_assessment_disagreement",
        ),
    )
    op.create_table(
        "clinical_event_intelligence_artifacts",
        _uuid("id"),
        _uuid("run_id"),
        _uuid("predecessor_artifact_id", nullable=True),
        _uuid("payer_request_id"),
        sa.Column("artifact_version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_state", sa.String(60), nullable=False),
        sa.Column("requested_set_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("snapshot_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("result_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("configuration_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("reconciliation_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("disagreement_state", sa.String(40), nullable=False),
        _json("artifact_json"),
        _json("validation_json"),
        _created(),
        sa.ForeignKeyConstraint(
            ["run_id"], ["clinical_event_intelligence_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["predecessor_artifact_id"],
            ["clinical_event_intelligence_artifacts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["payer_request_id"], ["payer_requests.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_cei_artifact_run"),
        sa.UniqueConstraint(
            "payer_request_id", "artifact_version", name="uq_cei_artifact_request_version"
        ),
        sa.CheckConstraint("artifact_version > 0", name="ck_cei_artifact_version"),
        sa.CheckConstraint(
            "disagreement_state IN ('agreement','partial_disagreement','material_disagreement','unavailable')",
            name="ck_cei_artifact_disagreement",
        ),
    )
    op.create_table(
        "clinical_event_intelligence_explanations",
        _uuid("id"),
        _uuid("artifact_id"),
        _uuid("purpose_release_id", nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("display_mode", sa.String(40), nullable=False),
        sa.Column("fact_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("display_checksum_sha256", sa.String(64), nullable=False),
        _json("validation_json"),
        _json("display_json"),
        _created(),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["clinical_event_intelligence_artifacts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["purpose_release_id"], ["governed_care_releases.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "artifact_id",
            "role",
            "locale",
            "version",
            name="uq_cei_explanation_role_locale_version",
        ),
        sa.CheckConstraint("role IN ('patient','doctor','payer')", name="ck_cei_explanation_role"),
        sa.CheckConstraint("locale IN ('en','zh-Hans')", name="ck_cei_explanation_locale"),
    )
    op.create_table(
        "clinical_event_intelligence_lineage_events",
        _uuid("id"),
        _uuid("artifact_id"),
        _uuid("actor_user_id", nullable=True),
        _uuid("doctor_response_id", nullable=True),
        _uuid("payer_review_id", nullable=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("source_event_key", sa.String(160), nullable=False),
        sa.Column("source_checksum_sha256", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        _json("metadata_json", "'{}'::jsonb"),
        _created(),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["clinical_event_intelligence_artifacts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["doctor_response_id"], ["payer_doctor_responses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["payer_review_id"], ["payer_reviews.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "source_event_key", name="uq_cei_lineage_source"),
        sa.CheckConstraint(
            "NOT (doctor_response_id IS NOT NULL AND payer_review_id IS NOT NULL)",
            name="ck_cei_lineage_single_source",
        ),
    )

    op.execute("""
        CREATE FUNCTION validate_cei_clinical_event_location() RETURNS trigger AS $$
        BEGIN
          IF NEW.clinic_id IS NOT NULL AND NEW.hospital_id IS NULL THEN RAISE EXCEPTION 'clinic requires hospital'; END IF;
          IF NEW.clinic_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM clinics c WHERE c.id=NEW.clinic_id AND c.hospital_id=NEW.hospital_id) THEN RAISE EXCEPTION 'clinic does not belong to hospital'; END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_cei_clinical_event_location BEFORE INSERT OR UPDATE OF hospital_id, clinic_id ON clinical_events FOR EACH ROW EXECUTE FUNCTION validate_cei_clinical_event_location();
        CREATE FUNCTION validate_cei_snapshot_scope() RETURNS trigger AS $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM payer_requests pr
            JOIN clinical_events ce ON ce.id=pr.clinical_event_id
            WHERE pr.id=NEW.payer_request_id
              AND pr.version=NEW.payer_request_version
              AND pr.patient_id=NEW.patient_id
              AND pr.doctor_id=NEW.doctor_id
              AND pr.payer_organization_id=NEW.payer_organization_id
              AND ce.id=NEW.clinical_event_id
          ) THEN RAISE EXCEPTION 'clinical intelligence snapshot scope mismatch'; END IF;
          IF NEW.clinic_id IS NOT NULL AND (
            NEW.hospital_id IS NULL
            OR NOT EXISTS (SELECT 1 FROM clinics c WHERE c.id=NEW.clinic_id AND c.hospital_id=NEW.hospital_id)
            OR NOT (
              EXISTS (SELECT 1 FROM clinical_events ce WHERE ce.id=NEW.clinical_event_id AND ce.clinic_id=NEW.clinic_id AND ce.hospital_id=NEW.hospital_id)
              OR EXISTS (SELECT 1 FROM clinical_services cs JOIN clinics c ON c.id=cs.clinic_id WHERE cs.clinical_event_id=NEW.clinical_event_id AND cs.clinic_id=NEW.clinic_id AND c.hospital_id=NEW.hospital_id)
              OR EXISTS (SELECT 1 FROM doctor_profiles dp JOIN role_assignments ra ON ra.user_id=dp.user_id LEFT JOIN clinics c ON c.id=ra.clinic_id WHERE dp.id=NEW.doctor_id AND ra.status='active' AND ra.revoked_at IS NULL AND (ra.clinic_id=NEW.clinic_id OR (ra.clinic_id IS NULL AND ra.hospital_id=NEW.hospital_id)) AND (ra.clinic_id IS NULL OR c.hospital_id=NEW.hospital_id))
            )
          ) THEN RAISE EXCEPTION 'clinical intelligence snapshot facility scope mismatch'; END IF;
          IF NEW.clinic_id IS NULL AND NEW.hospital_id IS NOT NULL AND NOT (
            EXISTS (SELECT 1 FROM clinical_events ce WHERE ce.id=NEW.clinical_event_id AND ce.hospital_id=NEW.hospital_id)
            OR EXISTS (SELECT 1 FROM clinical_services cs JOIN clinics c ON c.id=cs.clinic_id WHERE cs.clinical_event_id=NEW.clinical_event_id AND c.hospital_id=NEW.hospital_id)
            OR EXISTS (SELECT 1 FROM doctor_profiles dp JOIN role_assignments ra ON ra.user_id=dp.user_id LEFT JOIN clinics c ON c.id=ra.clinic_id WHERE dp.id=NEW.doctor_id AND ra.status='active' AND ra.revoked_at IS NULL AND (ra.hospital_id=NEW.hospital_id OR c.hospital_id=NEW.hospital_id))
          ) THEN RAISE EXCEPTION 'clinical intelligence snapshot facility scope mismatch'; END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_cei_snapshot_scope BEFORE INSERT ON clinical_event_intelligence_snapshots FOR EACH ROW EXECUTE FUNCTION validate_cei_snapshot_scope();
        CREATE FUNCTION guard_cei_run_open() RETURNS trigger AS $$
        DECLARE target_run uuid;
        BEGIN
          IF TG_TABLE_NAME = 'clinical_event_intelligence_pathway_items' THEN
            SELECT run_id INTO target_run
              FROM clinical_event_intelligence_pathways
              WHERE id = NEW.pathway_id;
          ELSE
            target_run := NEW.run_id;
          END IF;
          IF EXISTS (SELECT 1 FROM clinical_event_intelligence_artifacts WHERE run_id=target_run) THEN RAISE EXCEPTION 'clinical intelligence run is closed'; END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_cei_retrieval_run_open BEFORE INSERT ON clinical_event_intelligence_retrieval_sources FOR EACH ROW EXECUTE FUNCTION guard_cei_run_open();
        CREATE TRIGGER trg_cei_pathway_run_open BEFORE INSERT ON clinical_event_intelligence_pathways FOR EACH ROW EXECUTE FUNCTION guard_cei_run_open();
        CREATE TRIGGER trg_cei_pathway_item_run_open BEFORE INSERT ON clinical_event_intelligence_pathway_items FOR EACH ROW EXECUTE FUNCTION guard_cei_run_open();
        CREATE TRIGGER trg_cei_attempt_run_open BEFORE INSERT ON clinical_event_intelligence_provider_attempts FOR EACH ROW EXECUTE FUNCTION guard_cei_run_open();
        CREATE TRIGGER trg_cei_assessment_run_open BEFORE INSERT ON clinical_event_intelligence_item_assessments FOR EACH ROW EXECUTE FUNCTION guard_cei_run_open();
        CREATE FUNCTION validate_cei_assessment_source_scope() RETURNS trigger AS $$
        BEGIN
          IF NEW.retrieval_source_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM clinical_event_intelligence_retrieval_sources source
            WHERE source.id=NEW.retrieval_source_id AND source.run_id=NEW.run_id
          ) THEN RAISE EXCEPTION 'assessment retrieval source belongs to another run'; END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_cei_assessment_source_scope BEFORE INSERT ON clinical_event_intelligence_item_assessments FOR EACH ROW EXECUTE FUNCTION validate_cei_assessment_source_scope();
        CREATE FUNCTION validate_cei_artifact_close() RETURNS trigger AS $$
        DECLARE request_count integer; assessment_count integer; fallback_count integer; fallback_valid_count integer; fallback_distinct_count integer;
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM clinical_event_intelligence_runs r JOIN clinical_event_intelligence_snapshots s ON s.id=r.snapshot_id WHERE r.id=NEW.run_id AND r.payer_request_id=NEW.payer_request_id AND s.payer_request_id=NEW.payer_request_id AND s.snapshot_checksum_sha256=NEW.snapshot_checksum_sha256) THEN RAISE EXCEPTION 'artifact run scope mismatch'; END IF;
          SELECT count(*) INTO request_count FROM payer_request_lines WHERE payer_request_id=NEW.payer_request_id;
          SELECT count(*) INTO assessment_count FROM clinical_event_intelligence_item_assessments a JOIN payer_request_lines l ON l.id=a.payer_request_line_id WHERE a.run_id=NEW.run_id AND l.payer_request_id=NEW.payer_request_id;
          IF request_count=0 THEN RAISE EXCEPTION 'artifact requires requested lines'; END IF;
          IF NEW.lifecycle_state = 'provider_unavailable' THEN
            IF assessment_count <> 0 OR EXISTS (SELECT 1 FROM clinical_event_intelligence_item_assessments WHERE run_id=NEW.run_id) THEN RAISE EXCEPTION 'provider unavailable artifact cannot contain normalized assessments'; END IF;
            IF jsonb_typeof(NEW.artifact_json->'requested_item_assessments') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'provider unavailable artifact requires fallback assessments'; END IF;
            SELECT count(*), count(DISTINCT item->>'requested_line_id'), count(*) FILTER (WHERE l.id IS NOT NULL AND item->>'state'='assessment_unavailable' AND item->'human_review_required'='true'::jsonb AND item->'no_automatic_action'='true'::jsonb)
              INTO fallback_count, fallback_distinct_count, fallback_valid_count
              FROM jsonb_array_elements(NEW.artifact_json->'requested_item_assessments') item
              LEFT JOIN payer_request_lines l ON l.id::text=item->>'requested_line_id' AND l.payer_request_id=NEW.payer_request_id;
            IF fallback_count<>request_count OR fallback_distinct_count<>request_count OR fallback_valid_count<>request_count THEN RAISE EXCEPTION 'provider unavailable artifact must represent every requested line exactly once'; END IF;
          ELSIF assessment_count<>request_count OR EXISTS (SELECT 1 FROM clinical_event_intelligence_item_assessments a JOIN payer_request_lines l ON l.id=a.payer_request_line_id WHERE a.run_id=NEW.run_id AND l.payer_request_id<>NEW.payer_request_id) THEN
            RAISE EXCEPTION 'artifact must assess every requested line exactly once';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_cei_artifact_close BEFORE INSERT ON clinical_event_intelligence_artifacts FOR EACH ROW EXECUTE FUNCTION validate_cei_artifact_close();
    """)
    immutable = [
        "clinical_event_intelligence_snapshots",
        "clinical_event_intelligence_runs",
        "clinical_event_intelligence_retrieval_sources",
        "clinical_event_intelligence_pathways",
        "clinical_event_intelligence_pathway_items",
        "clinical_event_intelligence_provider_attempts",
        "clinical_event_intelligence_item_assessments",
        "clinical_event_intelligence_artifacts",
        "clinical_event_intelligence_explanations",
        "clinical_event_intelligence_lineage_events",
    ]
    for table in immutable:
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION guard_append_only_care_record()"
        )
    op.execute(
        "CREATE TRIGGER trg_payer_doctor_responses_append_only "
        "BEFORE UPDATE OR DELETE ON payer_doctor_responses FOR EACH ROW "
        "EXECUTE FUNCTION guard_append_only_care_record()"
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_payer_doctor_responses_append_only ON payer_doctor_responses"
    )
    for table in reversed(
        [
            "clinical_event_intelligence_snapshots",
            "clinical_event_intelligence_runs",
            "clinical_event_intelligence_retrieval_sources",
            "clinical_event_intelligence_pathways",
            "clinical_event_intelligence_pathway_items",
            "clinical_event_intelligence_provider_attempts",
            "clinical_event_intelligence_item_assessments",
            "clinical_event_intelligence_artifacts",
            "clinical_event_intelligence_explanations",
            "clinical_event_intelligence_lineage_events",
        ]
    ):
        op.drop_table(table)
    op.execute(
        "DROP FUNCTION IF EXISTS validate_cei_artifact_close(); DROP FUNCTION IF EXISTS validate_cei_assessment_source_scope(); DROP FUNCTION IF EXISTS guard_cei_run_open(); DROP FUNCTION IF EXISTS validate_cei_snapshot_scope(); DROP TRIGGER IF EXISTS trg_cei_clinical_event_location ON clinical_events; DROP FUNCTION IF EXISTS validate_cei_clinical_event_location();"
    )
    op.drop_index("ix_clinical_event_facility", table_name="clinical_events")
    op.drop_constraint("fk_clinical_event_clinic", "clinical_events", type_="foreignkey")
    op.drop_constraint("fk_clinical_event_hospital", "clinical_events", type_="foreignkey")
    op.drop_constraint("ck_payer_request_line_unit", "payer_request_lines", type_="check")
    op.drop_constraint("ck_payer_request_line_quantity", "payer_request_lines", type_="check")
    for column in ("unit", "quantity", "service_code", "code_system"):
        op.drop_column("payer_request_lines", column)
    for column in ("encounter_at", "department_code", "clinic_id", "hospital_id"):
        op.drop_column("clinical_events", column)
    for column in ("department_code", "facility_level", "facility_code"):
        op.drop_column("clinics", column)
    for column in ("city", "province", "country_code", "jurisdiction_code", "organization_code"):
        op.drop_column("hospitals", column)
