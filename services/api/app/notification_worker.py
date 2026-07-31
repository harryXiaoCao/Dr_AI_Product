"""Concurrency-safe outbox claiming with source revalidation."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.models import (
    ClinicalEventUpdate,
    ExpectedCareComparison,
    MedicationReminder,
    Notification,
    NotificationDeliveryAttempt,
    NotificationOutbox,
    PayerMembership,
    PayerRequest,
    RecoveryPlan,
    RecoveryTask,
    RecoveryTaskCompletion,
)
from app.notification_delivery import (
    DeliveryObservation,
    DeliveryRequest,
    DeliveryResult,
    adapter_for,
    operational_outcomes,
)
from app.notification_service import _event


def _source_is_current(db: Session, outbox: NotificationOutbox) -> tuple[bool, str]:
    notification = outbox.notification
    if notification.status in {"cancelled", "expired", "superseded", "dismissed"}:
        return False, f"notification_{notification.status}"
    now = datetime.now(UTC)
    if notification.expires_at is not None and notification.expires_at <= now:
        return False, "notification_expired"
    if notification.source_category == "medication_reminder":
        reminder = db.get(MedicationReminder, notification.source_resource_id)
        if reminder is None or reminder.status != "active":
            return False, "medication_reminder_inactive"
        if reminder.next_due_at != notification.scheduled_for:
            return False, "medication_schedule_changed"
    elif notification.source_category == "recovery_task":
        task = db.scalar(
            select(RecoveryTask)
            .join(RecoveryPlan)
            .where(
                RecoveryTask.id == notification.source_resource_id,
                RecoveryPlan.status == "active",
            )
        )
        completion = db.scalar(
            select(RecoveryTaskCompletion).where(
                RecoveryTaskCompletion.task_id == notification.source_resource_id
            )
        )
        if task is None or completion is not None:
            return False, "recovery_task_not_actionable"
    elif notification.source_category == "payer_request":
        payer_request = db.get(PayerRequest, notification.payer_request_id)
        if (
            payer_request is None
            or payer_request.id != notification.source_resource_id
            or payer_request.payer_organization_id != notification.payer_organization_id
        ):
            return False, "payer_request_scope_changed"
        if notification.audience_role == "payer":
            membership = db.scalar(
                select(PayerMembership).where(
                    PayerMembership.user_id == notification.user_id,
                    PayerMembership.payer_organization_id == notification.payer_organization_id,
                    PayerMembership.status == "active",
                )
            )
            if membership is None:
                return False, "payer_membership_revoked"
    elif notification.source_category == "expected_care_comparison":
        comparison = db.get(ExpectedCareComparison, notification.source_resource_id)
        if (
            comparison is None
            or comparison.lifecycle_state != "comparison_published"
            or comparison.patient_id != notification.patient_id
            or comparison.payer_request_id != notification.payer_request_id
        ):
            return False, "comparison_scope_changed"
    elif notification.source_category == "clinical_event_update":
        update = db.get(ClinicalEventUpdate, notification.source_resource_id)
        if update is None or update.patient_id != notification.patient_id:
            return False, "adherence_evidence_unavailable"
    return True, "current"


def _suppress_claimed_notification(
    notification: Notification, outbox: NotificationOutbox, reason: str
) -> None:
    previous = notification.status
    notification.status = "cancelled"
    notification.cancelled_at = datetime.now(UTC)
    notification.version += 1
    _event(
        notification,
        event_type="suppressed",
        from_status=previous,
        to_status="cancelled",
        actor_kind="system",
        actor_user_id=None,
        idempotency_key=f"suppress:{outbox.id}:{outbox.attempt_count}",
        evidence={"reason_code": reason},
    )
    for entry in notification.outbox_entries:
        if entry.status in {"pending", "retrying", "claimed"}:
            entry.status = "suppressed"
            entry.last_result_code = reason


def process_one(
    db: Session,
    settings: Settings,
    *,
    deliver: Callable[[DeliveryRequest], DeliveryResult] | None = None,
    observe: Callable[[DeliveryObservation], None] | None = None,
) -> bool:
    now = datetime.now(UTC)
    outbox = db.scalar(
        select(NotificationOutbox)
        .options(selectinload(NotificationOutbox.notification))
        .where(
            (
                NotificationOutbox.status.in_({"pending", "retrying"})
                | (
                    (NotificationOutbox.status == "claimed")
                    & (NotificationOutbox.claim_expires_at <= now)
                )
            ),
            NotificationOutbox.available_at <= now,
        )
        .order_by(NotificationOutbox.available_at, NotificationOutbox.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if outbox is None:
        db.rollback()
        return False
    outbox.status = "claimed"
    outbox.claimed_at = now
    outbox.claim_expires_at = now + timedelta(minutes=2)
    current, reason = _source_is_current(db, outbox)
    if not current:
        _suppress_claimed_notification(outbox.notification, outbox, reason)
        db.commit()
        return True
    outbox.attempt_count += 1
    request = DeliveryRequest(
        channel=outbox.channel,
        idempotency_key=f"notification:{outbox.id}:{outbox.channel}",
        attempt_number=outbox.attempt_count,
    )
    outbox_id = outbox.id
    # Release the claim transaction before provider I/O. This lets source
    # completion, user cancellation, and endpoint revocation proceed while a
    # bounded transport call is in flight.
    db.commit()
    try:
        result = (
            deliver(request)
            if deliver is not None
            else adapter_for(settings, request.channel).deliver(request)
        )
    except Exception:
        # Provider exceptions are deliberately collapsed to a bounded,
        # content-free result. The attempt remains auditable and retryable.
        result = DeliveryResult(
            state="failed",
            code="transport_exception",
            retryable=True,
        )
    outbox = db.scalar(
        select(NotificationOutbox)
        .options(selectinload(NotificationOutbox.notification))
        .where(NotificationOutbox.id == outbox_id)
        .with_for_update()
    )
    if outbox is None:
        db.rollback()
        return True
    current, reason = _source_is_current(db, outbox)
    cancelled_while_in_flight = outbox.status in {"cancelled", "suppressed", "expired"}
    if not current or cancelled_while_in_flight:
        result = DeliveryResult(
            state=result.state,
            code=(
                f"provider_{result.state}_after_cancellation"
                if cancelled_while_in_flight
                else f"provider_{result.state}_after_{reason}"
            ),
            retryable=False,
            provider_receipt_hash=result.provider_receipt_hash,
        )
    db.add(
        NotificationDeliveryAttempt(
            outbox_id=outbox.id,
            attempt_number=outbox.attempt_count,
            adapter_code=outbox.channel,
            result_state=result.state,
            result_code=result.code,
            provider_receipt_hash=result.provider_receipt_hash,
            retryable=result.retryable,
        )
    )
    outbox.last_result_code = result.code
    if cancelled_while_in_flight:
        pass
    elif not current:
        _suppress_claimed_notification(outbox.notification, outbox, reason)
    elif result.state in {"accepted", "delivered"}:
        outbox.status = result.state
        outbox.notification.sent_at = now
    elif result.retryable and outbox.attempt_count < outbox.max_attempts:
        outbox.status = "retrying"
        outbox.available_at = now + timedelta(minutes=2**outbox.attempt_count)
    else:
        outbox.status = "failed"
    db.commit()
    if observe is not None:
        observation = DeliveryObservation(
            channel=request.channel,
            idempotency_key=request.idempotency_key,
            attempt_number=request.attempt_number,
            outcomes=operational_outcomes(result),
            result_code=result.code,
            retryable=result.retryable,
        )
        try:
            observe(observation)
        except Exception:
            # Observability must not change a persisted delivery outcome.
            pass
    return True
