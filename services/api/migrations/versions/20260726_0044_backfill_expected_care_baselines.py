"""Backfill immutable baselines for previously validated candidates.

Revision ID: 20260726_0044
Revises: 20260726_0043
"""

from alembic import op

revision = "20260726_0044"
down_revision = "20260726_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only candidates that already passed the Slice D deterministic contract
    # and whose item sums still match the persisted integer totals qualify.
    op.execute(
        """
        INSERT INTO expected_care_reviewed_envelopes (
            id,
            candidate_result_id,
            doctor_review_id,
            predecessor_envelope_id,
            patient_id,
            clinical_event_id,
            payer_request_id,
            version,
            lifecycle_state,
            candidate_output_checksum_sha256,
            purpose_code,
            purpose_contract_version,
            schema_version,
            prompt_version,
            model_configuration_version,
            scenario_release_id,
            care_plan_release_id,
            pricing_reference_release_id,
            utilization_rule_release_id,
            release_lineage_json,
            currency,
            amount_type,
            total_low_minor,
            total_high_minor,
            assumptions_json,
            missing_information_json,
            limitations_json,
            structured_difference_json
        )
        SELECT
            gen_random_uuid(),
            result.id,
            NULL,
            NULL,
            request.patient_id,
            request.clinical_event_id,
            request.payer_request_id,
            COALESCE(
                (
                    SELECT MAX(previous.version)
                    FROM expected_care_reviewed_envelopes previous
                    WHERE previous.candidate_result_id = result.id
                ),
                0
            ) + 1,
            'validated_baseline_published',
            result.output_checksum_sha256,
            request.purpose_code,
            request.purpose_contract_version,
            request.schema_version,
            request.prompt_version,
            request.model_configuration_version,
            request.scenario_release_id,
            request.care_plan_release_id,
            request.pricing_reference_release_id,
            request.utilization_rule_release_id,
            request.release_lineage_json,
            result.currency,
            'system_expected_reference_range',
            result.total_low_minor,
            result.total_high_minor,
            COALESCE(result.candidate_json -> 'assumptions', '[]'::jsonb),
            COALESCE(result.candidate_json -> 'missing_information', '[]'::jsonb),
            COALESCE(result.candidate_json -> 'confidence_limitations', '[]'::jsonb),
            jsonb_build_object(
                'base', 'immutable_validated_candidate',
                'candidate_modified', false,
                'item_changes', '[]'::jsonb,
                'backfilled', true
            )
        FROM expected_care_candidate_results result
        JOIN expected_care_candidate_requests request
          ON request.id = result.candidate_request_id
        CROSS JOIN LATERAL (
            SELECT
                COUNT(*) AS item_count,
                SUM((item ->> 'amount_low_minor')::integer) AS low_sum,
                SUM((item ->> 'amount_high_minor')::integer) AS high_sum
            FROM jsonb_array_elements(result.candidate_json -> 'items') item
        ) totals
        WHERE request.lifecycle_state = 'generated_pending_review'
          AND result.lifecycle_state = 'generated_pending_review'
          AND request.validation_outcome = 'validated'
          AND result.currency IS NOT NULL
          AND result.total_low_minor IS NOT NULL
          AND result.total_high_minor IS NOT NULL
          AND jsonb_typeof(result.candidate_json -> 'items') = 'array'
          AND totals.item_count > 0
          AND totals.low_sum = result.total_low_minor
          AND totals.high_sum = result.total_high_minor
          AND NOT EXISTS (
              SELECT 1
              FROM expected_care_reviewed_envelopes baseline
              WHERE baseline.candidate_result_id = result.id
                AND baseline.lifecycle_state = 'validated_baseline_published'
          )
        """
    )
    op.execute(
        """
        INSERT INTO expected_care_envelope_items (
            id,
            envelope_id,
            item_key,
            category,
            code_system,
            service_code,
            unit,
            quantity_low,
            quantity_high,
            amount_low_minor,
            amount_high_minor,
            pricing_reference_item_id,
            utilization_rule_id
        )
        SELECT
            gen_random_uuid(),
            baseline.id,
            item ->> 'item_key',
            item ->> 'category',
            item ->> 'code_system',
            item ->> 'service_code',
            item ->> 'unit',
            (item ->> 'quantity_low')::integer,
            (item ->> 'quantity_high')::integer,
            (item ->> 'amount_low_minor')::integer,
            (item ->> 'amount_high_minor')::integer,
            (item ->> 'pricing_reference_item_id')::uuid,
            (item ->> 'utilization_rule_id')::uuid
        FROM expected_care_reviewed_envelopes baseline
        JOIN expected_care_candidate_results result
          ON result.id = baseline.candidate_result_id
        CROSS JOIN LATERAL jsonb_array_elements(result.candidate_json -> 'items') item
        WHERE baseline.lifecycle_state = 'validated_baseline_published'
          AND NOT EXISTS (
              SELECT 1
              FROM expected_care_envelope_items existing
              WHERE existing.envelope_id = baseline.id
                AND existing.item_key = item ->> 'item_key'
          )
        """
    )
    op.execute(
        """
        INSERT INTO expected_care_review_heads (
            candidate_result_id,
            current_envelope_id,
            version,
            lifecycle_state
        )
        SELECT
            baseline.candidate_result_id,
            baseline.id,
            0,
            'validated_baseline_published'
        FROM expected_care_reviewed_envelopes baseline
        WHERE baseline.lifecycle_state = 'validated_baseline_published'
        ON CONFLICT (candidate_result_id) DO UPDATE
        SET current_envelope_id = EXCLUDED.current_envelope_id,
            lifecycle_state = EXCLUDED.lifecycle_state,
            updated_at = now()
        """
    )
    op.execute(
        """
        INSERT INTO expected_care_lifecycle_events (
            id,
            candidate_result_id,
            doctor_review_id,
            envelope_id,
            actor_user_id,
            lifecycle_state,
            metadata_json
        )
        SELECT
            gen_random_uuid(),
            baseline.candidate_result_id,
            NULL,
            baseline.id,
            request.actor_user_id,
            'validated_baseline_published',
            jsonb_build_object(
                'publication_version', baseline.version,
                'candidate_modified', false,
                'system_published', true,
                'backfilled', true
            )
        FROM expected_care_reviewed_envelopes baseline
        JOIN expected_care_candidate_results result
          ON result.id = baseline.candidate_result_id
        JOIN expected_care_candidate_requests request
          ON request.id = result.candidate_request_id
        WHERE baseline.lifecycle_state = 'validated_baseline_published'
          AND NOT EXISTS (
              SELECT 1
              FROM expected_care_lifecycle_events event
              WHERE event.envelope_id = baseline.id
                AND event.lifecycle_state = 'validated_baseline_published'
          )
        """
    )
    op.execute(
        """
        INSERT INTO audit_events (
            id,
            actor_user_id,
            patient_id,
            event_type,
            resource_type,
            resource_id,
            metadata_json
        )
        SELECT
            gen_random_uuid(),
            request.actor_user_id,
            request.patient_id,
            'expected_care_baseline_published',
            'expected_care_published_baseline',
            baseline.id,
            jsonb_build_object(
                'candidate_result_id', baseline.candidate_result_id::text,
                'candidate_modified', false,
                'payer_request_linked', request.payer_request_id IS NOT NULL,
                'content_free', true,
                'backfilled', true
            )
        FROM expected_care_reviewed_envelopes baseline
        JOIN expected_care_candidate_results result
          ON result.id = baseline.candidate_result_id
        JOIN expected_care_candidate_requests request
          ON request.id = result.candidate_request_id
        WHERE baseline.lifecycle_state = 'validated_baseline_published'
          AND NOT EXISTS (
              SELECT 1
              FROM audit_events audit
              WHERE audit.resource_id = baseline.id
                AND audit.event_type = 'expected_care_baseline_published'
          )
        """
    )


def downgrade() -> None:
    # Append-only clinical/financial evidence is deliberately not deleted.
    # A full downgrade through 0043 removes system baselines safely while its
    # append-only triggers are suspended.
    pass
