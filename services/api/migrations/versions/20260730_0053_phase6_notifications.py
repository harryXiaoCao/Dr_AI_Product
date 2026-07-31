"""Add the canonical Phase 6 notification lifecycle.

Revision ID: 20260730_0053
Revises: 20260728_0052
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260730_0053"
down_revision = "20260728_0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("severity", sa.String(40), nullable=False, server_default="information"),
    )
    op.add_column(
        "notifications",
        sa.Column("audience_role", sa.String(40), nullable=False, server_default="patient"),
    )
    op.add_column(
        "notifications",
        sa.Column("source_category", sa.String(60), nullable=False, server_default="legacy"),
    )
    op.add_column("notifications", sa.Column("source_resource_id", postgresql.UUID(as_uuid=True)))
    op.add_column(
        "notifications",
        sa.Column(
            "payer_organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_organizations.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "payer_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payer_requests.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column("notifications", sa.Column("deduplication_key", sa.String(64)))
    op.add_column("notifications", sa.Column("content_checksum", sa.String(64)))
    op.add_column(
        "notifications",
        sa.Column(
            "template_code", sa.String(80), nullable=False, server_default="legacy_notification"
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("locale", sa.String(20), nullable=False, server_default="en"),
    )
    op.add_column(
        "notifications",
        sa.Column("time_zone", sa.String(64), nullable=False, server_default="UTC"),
    )
    op.add_column(
        "notifications",
        sa.Column("privacy_class", sa.String(40), nullable=False, server_default="generic"),
    )
    op.add_column(
        "notifications",
        sa.Column("title", sa.String(160), nullable=False, server_default="Update available"),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "body",
            sa.String(280),
            nullable=False,
            server_default="Open Dr. AI to review this update.",
        ),
    )
    op.add_column("notifications", sa.Column("deep_link_code", sa.String(80)))
    op.add_column("notifications", sa.Column("expires_at", sa.DateTime(timezone=True)))
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True)))
    op.add_column("notifications", sa.Column("dismissed_at", sa.DateTime(timezone=True)))
    op.add_column("notifications", sa.Column("cancelled_at", sa.DateTime(timezone=True)))
    op.add_column("notifications", sa.Column("superseded_at", sa.DateTime(timezone=True)))
    op.add_column(
        "notifications",
        sa.Column(
            "superseded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.execute(
        """
        UPDATE notifications
        SET
            deduplication_key =
                md5('legacy-notification:' || id::text) ||
                md5('legacy-notification:2:' || id::text),
            content_checksum =
                md5(notification_type || ':' || status || ':' || id::text) ||
                md5(notification_type || ':2:' || status || ':' || id::text),
            template_code = 'legacy_notification',
            source_category = 'legacy',
            audience_role = 'patient',
            privacy_class = 'generic',
            title = 'Update available',
            body = 'Open Dr. AI to review this update.'
        """
    )
    op.alter_column("notifications", "deduplication_key", nullable=False)
    op.alter_column("notifications", "content_checksum", nullable=False)
    op.create_unique_constraint(
        "uq_notifications_occurrence",
        "notifications",
        [
            "user_id",
            "notification_type",
            "source_category",
            "source_resource_id",
            "deduplication_key",
        ],
    )
    op.create_check_constraint(
        "ck_notifications_status",
        "notifications",
        "status IN ('queued','sent','scheduled','unread','read','dismissed',"
        "'cancelled','expired','superseded')",
    )
    op.create_check_constraint(
        "ck_notifications_audience_role",
        "notifications",
        "audience_role IN ('patient','doctor','payer')",
    )
    op.create_check_constraint(
        "ck_notifications_severity",
        "notifications",
        "severity IN ('information','action','warning')",
    )
    op.create_check_constraint(
        "ck_notifications_privacy_class",
        "notifications",
        "privacy_class IN ('generic','private_in_app')",
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column(
            "allowed_categories_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("in_product_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "external_channels_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("quiet_hours_start", sa.String(5)),
        sa.Column("quiet_hours_end", sa.String(5)),
        sa.Column("locale", sa.String(20), nullable=False, server_default="en"),
        sa.Column("time_zone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("preview_level", sa.String(40), nullable=False, server_default="generic"),
        sa.Column("last_idempotency_key", sa.String(120)),
        sa.Column("last_request_checksum", sa.String(64)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "role", name="uq_notification_preference_user_role"),
        sa.CheckConstraint(
            "role IN ('patient','doctor','payer')",
            name="ck_notification_preference_role",
        ),
        sa.CheckConstraint(
            "locale IN ('en','zh-Hans')",
            name="ck_notification_preference_locale",
        ),
        sa.CheckConstraint(
            "preview_level IN ('generic','private_in_app')",
            name="ck_notification_preference_preview",
        ),
        sa.CheckConstraint(
            "(quiet_hours_start IS NULL) = (quiet_hours_end IS NULL)",
            name="ck_notification_preference_quiet_pair",
        ),
    )
    op.create_table(
        "notification_device_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("platform", sa.String(40), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(40),
            nullable=False,
            server_default="permission_not_requested",
        ),
        sa.Column("readiness_code", sa.String(80), nullable=False, server_default="not_registered"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("rotated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "user_id",
            "channel",
            "token_hash",
            name="uq_notification_endpoint_user_channel_token",
        ),
        sa.CheckConstraint(
            "channel IN ('apns','android_emas','web_push')",
            name="ck_notification_endpoint_channel",
        ),
        sa.CheckConstraint(
            "status IN ('permission_not_requested','permission_denied','active',"
            "'revoked','stale','signed_out','unsupported')",
            name="ck_notification_endpoint_status",
        ),
    )
    op.create_index(
        "ix_notification_endpoint_user_status",
        "notification_device_endpoints",
        ["user_id", "status"],
    )
    op.create_table(
        "notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("claim_expires_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_result_code", sa.String(80)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("notification_id", "channel", name="uq_notification_outbox_channel"),
        sa.CheckConstraint(
            "channel IN ('apns','android_emas','web_push')",
            name="ck_notification_outbox_channel",
        ),
        sa.CheckConstraint(
            "status IN ('pending','claimed','retrying','accepted','delivered',"
            "'failed','suppressed','cancelled','expired','unknown')",
            name="ck_notification_outbox_status",
        ),
    )
    op.create_index(
        "ix_notification_outbox_status_available",
        "notification_outbox",
        ["status", "available_at"],
    )
    op.create_table(
        "notification_delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "outbox_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_outbox.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("adapter_code", sa.String(40), nullable=False),
        sa.Column("result_state", sa.String(40), nullable=False),
        sa.Column("result_code", sa.String(80), nullable=False),
        sa.Column("provider_receipt_hash", sa.String(64)),
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("outbox_id", "attempt_number", name="uq_notification_attempt_number"),
        sa.CheckConstraint(
            "result_state IN ('accepted','delivered','failed','unknown')",
            name="ck_notification_attempt_result",
        ),
        sa.CheckConstraint(
            "provider_receipt_hash IS NULL OR result_state IN ('accepted','delivered')",
            name="ck_notification_attempt_receipt_state",
        ),
    )
    op.create_index(
        "ix_notification_attempt_outbox_created",
        "notification_delivery_attempts",
        ["outbox_id", "created_at"],
    )
    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("actor_kind", sa.String(40), nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("event_checksum", sa.String(64), nullable=False),
        sa.Column(
            "evidence_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("notification_id", "sequence", name="uq_notification_event_sequence"),
        sa.UniqueConstraint(
            "notification_id", "idempotency_key", name="uq_notification_event_idempotency"
        ),
    )
    op.create_index(
        "ix_notification_event_notification_created",
        "notification_events",
        ["notification_id", "created_at"],
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_phase6_notification_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_notification_attempts_append_only
        BEFORE UPDATE OR DELETE ON notification_delivery_attempts
        FOR EACH ROW EXECUTE FUNCTION guard_phase6_notification_append_only();

        CREATE TRIGGER trg_notification_events_append_only
        BEFORE UPDATE OR DELETE ON notification_events
        FOR EACH ROW EXECUTE FUNCTION guard_phase6_notification_append_only();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_notification_events_append_only
            ON notification_events;
        DROP TRIGGER IF EXISTS trg_notification_attempts_append_only
            ON notification_delivery_attempts;
        DROP FUNCTION IF EXISTS guard_phase6_notification_append_only();
        """
    )
    op.drop_index("ix_notification_event_notification_created", table_name="notification_events")
    op.drop_table("notification_events")
    op.drop_index(
        "ix_notification_attempt_outbox_created",
        table_name="notification_delivery_attempts",
    )
    op.drop_table("notification_delivery_attempts")
    op.drop_index("ix_notification_outbox_status_available", table_name="notification_outbox")
    op.drop_table("notification_outbox")
    op.drop_index(
        "ix_notification_endpoint_user_status",
        table_name="notification_device_endpoints",
    )
    op.drop_table("notification_device_endpoints")
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    for constraint in (
        "ck_notifications_privacy_class",
        "ck_notifications_severity",
        "ck_notifications_audience_role",
        "ck_notifications_status",
    ):
        op.drop_constraint(constraint, "notifications", type_="check")
    op.drop_constraint("uq_notifications_occurrence", "notifications", type_="unique")
    for column in (
        "version",
        "superseded_by_id",
        "superseded_at",
        "cancelled_at",
        "dismissed_at",
        "read_at",
        "expires_at",
        "deep_link_code",
        "body",
        "title",
        "privacy_class",
        "time_zone",
        "locale",
        "template_code",
        "content_checksum",
        "deduplication_key",
        "payer_request_id",
        "payer_organization_id",
        "source_resource_id",
        "source_category",
        "audience_role",
        "severity",
    ):
        op.drop_column("notifications", column)
