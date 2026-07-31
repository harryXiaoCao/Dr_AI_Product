import hashlib
import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine
from app.models import (
    CareRelationship,
    ClinicalEvent,
    MedicationReminder,
    Notification,
    NotificationDeliveryAttempt,
    NotificationDeviceEndpoint,
    NotificationEvent,
    NotificationOutbox,
    NotificationPreference,
    PayerMembership,
    PayerRequest,
    User,
)
from app.notification_contracts import EVENT_CONTRACTS
from app.notification_delivery import DeliveryResult, operational_outcomes
from app.notification_service import (
    after_quiet_hours,
    create_notification,
    suppress_source_notifications,
)
from app.notification_worker import process_one
from tests.helpers import auth_header, register


def _patient(client: TestClient, suffix: str) -> tuple[dict[str, str], uuid.UUID]:
    session = register(
        client,
        email=f"phase6.notifications.{suffix}@example.com",
        password="Patient9!",
        role="patient",
    )
    headers = auth_header(session["access_token"])
    with Session(engine) as db:
        user = db.scalar(
            select(User).where(User.email == f"phase6.notifications.{suffix}@example.com")
        )
        assert user is not None
        return headers, user.id


def _doctor(client: TestClient, suffix: str) -> tuple[dict[str, str], uuid.UUID]:
    email = f"phase6.notifications.doctor.{suffix}@example.com"
    session = register(
        client,
        email=email,
        password="Doctor9!",
        role="doctor",
    )
    headers = auth_header(session["access_token"])
    with Session(engine) as db:
        user_id = db.scalar(select(User.id).where(User.email == email))
        assert user_id is not None
        return headers, user_id


def _payer(
    client: TestClient,
    suffix: str,
) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    email = f"phase6.notifications.payer.{suffix}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": (
                f"+1777{int(hashlib.sha1(email.encode()).hexdigest()[:10], 16) % 10_000_000:07d}"
            ),
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "Synthetic notification reviewer",
                "organization_name": f"Synthetic Notification Payer {suffix}",
                "title": "Reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201, response.text
    headers = auth_header(response.json()["access_token"])
    with Session(engine) as db:
        membership = db.scalar(
            select(PayerMembership)
            .join(User, User.id == PayerMembership.user_id)
            .where(User.email == email)
        )
        assert membership is not None
        return headers, membership.user_id, membership.payer_organization_id


def _create_patient_notification(user_id: uuid.UUID) -> uuid.UUID:
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        notification, replayed = create_notification(
            db,
            recipient=user,
            event_type="recovery_task_due",
            source_resource_id=uuid.uuid4(),
            scheduled_for=datetime(2026, 7, 30, 4, 0, tzinfo=UTC),
            patient_id=user.patient_profile.id,
            occurrence_key="scheduled:2026-07-30T04:00:00Z",
        )
        assert replayed is False
        db.commit()
        return notification.id


def test_phase6_notification_vocabulary_covers_required_patient_doctor_and_payer_events() -> None:
    required = {
        "medication_reminder",
        "refill_reminder",
        "recovery_task_due",
        "follow_up_milestone",
        "consultation_milestone",
        "care_service_milestone",
        "imaging_action_available",
        "missing_information_warning",
        "cost_variance_warning",
        "incomplete_allocation_warning",
        "payer_clarification_requested",
        "adherence_evidence_available",
        "payer_request_submitted",
        "payer_doctor_response_added",
        "payer_manual_review_transition",
        "payer_final_outcome",
        "payer_request_closed",
    }
    assert required <= EVENT_CONTRACTS.keys()


def test_lifecycle_events_and_delivery_attempts_are_database_append_only(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "append-only")
    notification_id = _create_patient_notification(user_id)
    with Session(engine) as db:
        outbox = NotificationOutbox(
            notification_id=notification_id,
            channel="web_push",
            status="failed",
            available_at=datetime.now(UTC),
            attempt_count=1,
            max_attempts=3,
        )
        db.add(outbox)
        db.flush()
        attempt = NotificationDeliveryAttempt(
            outbox_id=outbox.id,
            attempt_number=1,
            adapter_code="web_push",
            result_state="failed",
            result_code="synthetic_append_only_check",
            retryable=False,
        )
        db.add(attempt)
        db.flush()
        attempt_id = attempt.id
        db.commit()
        event_id = db.scalar(
            select(NotificationEvent.id).where(NotificationEvent.notification_id == notification_id)
        )
        assert event_id is not None
        with pytest.raises(DBAPIError):
            db.execute(
                update(NotificationEvent)
                .where(NotificationEvent.id == event_id)
                .values(to_status="tampered")
            )
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(
                update(NotificationDeliveryAttempt)
                .where(NotificationDeliveryAttempt.id == attempt_id)
                .values(result_code="tampered")
            )
            db.commit()
        db.rollback()


def test_role_scoped_inbox_mutations_are_versioned_idempotent_and_neutral(
    client: TestClient,
) -> None:
    headers, user_id = _patient(client, "owner")
    unrelated_headers, _ = _patient(client, "unrelated")
    notification_id = _create_patient_notification(user_id)

    inbox = client.get("/api/v1/notifications", headers=headers)
    assert inbox.status_code == 200, inbox.text
    assert inbox.json()["unread_count"] == 1
    item = inbox.json()["items"][0]
    assert item["id"] == str(notification_id)
    assert item["title"] == "Recovery reminder"
    assert "patient" not in str(item).lower()

    action_headers = {**headers, "Idempotency-Key": "notification-read-001"}
    read = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers=action_headers,
        json={"expected_version": item["version"]},
    )
    assert read.status_code == 200, read.text
    assert read.json()["status"] == "read"

    replay = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers=action_headers,
        json={"expected_version": item["version"]},
    )
    assert replay.status_code == 200
    assert replay.json()["version"] == read.json()["version"]

    conflict = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers=action_headers,
        json={"expected_version": read.json()["version"]},
    )
    assert conflict.status_code == 409
    denied = client.post(
        f"/api/v1/notifications/{notification_id}/unread",
        headers={**unrelated_headers, "Idempotency-Key": "cross-user-unread-001"},
        json={"expected_version": read.json()["version"]},
    )
    assert denied.status_code == 404

    unread = client.post(
        f"/api/v1/notifications/{notification_id}/unread",
        headers={**headers, "Idempotency-Key": "notification-unread-001"},
        json={"expected_version": read.json()["version"]},
    )
    assert unread.status_code == 200, unread.text
    assert unread.json()["status"] == "unread"
    assert client.get("/api/v1/notifications", headers=headers).json()["unread_count"] == 1

    dismissed = client.post(
        f"/api/v1/notifications/{notification_id}/dismiss",
        headers={**headers, "Idempotency-Key": "notification-dismiss-001"},
        json={"expected_version": unread.json()["version"]},
    )
    assert dismissed.status_code == 200, dismissed.text
    assert dismissed.json()["status"] == "dismissed"
    assert dismissed.json()["can_dismiss"] is False
    assert client.get("/api/v1/notifications", headers=headers).json()["unread_count"] == 0
    with Session(engine) as db:
        events = db.scalars(
            select(NotificationEvent)
            .where(NotificationEvent.notification_id == notification_id)
            .order_by(NotificationEvent.sequence)
        ).all()
        assert [event.event_type for event in events] == [
            "created",
            "read",
            "unread",
            "dismiss",
        ]
        assert [event.sequence for event in events] == [1, 2, 3, 4]


def test_preferences_readiness_and_endpoint_metadata_fail_closed_without_raw_token(
    client: TestClient,
) -> None:
    headers, _ = _patient(client, "preferences")
    initial = client.get("/api/v1/notification-preferences", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["version"] == 0

    body = {
        "allowed_categories": ["medication_reminder", "recovery_task_due"],
        "in_product_enabled": False,
        "external_channels": [],
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "07:00",
        "locale": "zh-Hans",
        "time_zone": "Asia/Shanghai",
        "preview_level": "generic",
        "expected_version": 0,
    }
    saved = client.put(
        "/api/v1/notification-preferences",
        headers={**headers, "Idempotency-Key": "notification-preference-001"},
        json=body,
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["in_product_enabled"] is True
    assert saved.json()["version"] == 1
    key_conflict = client.put(
        "/api/v1/notification-preferences",
        headers={**headers, "Idempotency-Key": "notification-preference-001"},
        json={**body, "locale": "en", "expected_version": 1},
    )
    assert key_conflict.status_code == 409

    readiness = client.get("/api/v1/notifications/readiness", headers=headers)
    assert readiness.status_code == 200
    channels = readiness.json()["channels"]
    assert {item["channel"] for item in channels} == {
        "apns",
        "android_emas",
        "web_push",
    }
    assert all(item["ready"] is False for item in channels)
    assert (
        next(item for item in channels if item["channel"] == "android_emas")["provider"]
        == "alibaba_cloud_emas_mobile_push"
    )

    token_hash = hashlib.sha256(b"synthetic-device-endpoint").hexdigest()
    endpoint = client.post(
        "/api/v1/notification-device-endpoints",
        headers=headers,
        json={
            "channel": "android_emas",
            "platform": "android",
            "token_hash": token_hash,
            "permission_state": "active",
        },
    )
    assert endpoint.status_code == 200, endpoint.text
    assert endpoint.json()["status"] == "unsupported"
    assert token_hash not in endpoint.text
    with Session(engine) as db:
        stored = db.scalar(select(NotificationDeviceEndpoint))
        assert stored is not None
        assert stored.token_hash == token_hash
        assert not hasattr(stored, "token")


def test_endpoint_rotation_is_exact_and_preserves_other_devices(
    client: TestClient,
) -> None:
    headers, _ = _patient(client, "endpoint-rotation")
    first_hash = hashlib.sha256(b"synthetic-device-one-v1").hexdigest()
    second_device_hash = hashlib.sha256(b"synthetic-device-two").hexdigest()
    rotated_hash = hashlib.sha256(b"synthetic-device-one-v2").hexdigest()
    for token_hash in (first_hash, second_device_hash):
        response = client.post(
            "/api/v1/notification-device-endpoints",
            headers=headers,
            json={
                "channel": "web_push",
                "platform": "web",
                "token_hash": token_hash,
                "permission_state": "active",
            },
        )
        assert response.status_code == 200, response.text

    rotated = client.post(
        "/api/v1/notification-device-endpoints",
        headers=headers,
        json={
            "channel": "web_push",
            "platform": "web",
            "token_hash": rotated_hash,
            "previous_token_hash": first_hash,
            "permission_state": "active",
        },
    )
    assert rotated.status_code == 200, rotated.text
    assert first_hash not in rotated.text
    assert rotated_hash not in rotated.text

    with Session(engine) as db:
        rows = {
            row.token_hash: row
            for row in db.scalars(
                select(NotificationDeviceEndpoint).where(
                    NotificationDeviceEndpoint.channel == "web_push"
                )
            ).all()
        }
        assert rows[first_hash].status == "stale"
        assert rows[first_hash].rotated_at is not None
        assert rows[second_device_hash].status == "unsupported"
        assert rows[second_device_hash].rotated_at is None
        assert rows[rotated_hash].status == "unsupported"


def test_three_role_inboxes_and_deep_links_recheck_exact_authorization(
    client: TestClient,
) -> None:
    patient_headers, patient_user_id = _patient(client, "scope")
    unrelated_patient_headers, _ = _patient(client, "scope-unrelated")
    doctor_headers, doctor_user_id = _doctor(client, "scope")
    unrelated_doctor_headers, _ = _doctor(client, "scope-unrelated")
    payer_headers, payer_user_id, payer_organization_id = _payer(client, "scope")
    unrelated_payer_headers, _, unrelated_organization_id = _payer(client, "scope-unrelated")

    with Session(engine) as db:
        patient = db.get(User, patient_user_id)
        doctor = db.get(User, doctor_user_id)
        payer = db.get(User, payer_user_id)
        assert patient is not None and patient.patient_profile is not None
        assert doctor is not None and doctor.doctor_profile is not None
        assert payer is not None
        relationship = CareRelationship(
            doctor_id=doctor.doctor_profile.id,
            patient_id=patient.patient_profile.id,
            is_active=True,
        )
        clinical_event = ClinicalEvent(
            patient_id=patient.patient_profile.id,
            doctor_id=doctor.doctor_profile.id,
            title="Synthetic notification authorization event",
            chief_complaint="Synthetic authorization boundary",
            status="active",
        )
        db.add_all([relationship, clinical_event])
        db.flush()
        payer_request = PayerRequest(
            clinical_event_id=clinical_event.id,
            patient_id=patient.patient_profile.id,
            doctor_id=doctor.doctor_profile.id,
            payer_organization_id=payer_organization_id,
            status="submitted",
            currency="CNY",
            requested_total_minor=1200,
            doctor_summary="CONFIDENTIAL-PAYER-SUMMARY-MUST-NOT-LEAK",
        )
        db.add(payer_request)
        db.flush()
        patient_notification, _ = create_notification(
            db,
            recipient=patient,
            event_type="payer_manual_review_transition",
            source_resource_id=payer_request.id,
            scheduled_for=datetime.now(UTC),
            patient_id=patient.patient_profile.id,
            clinical_event_id=clinical_event.id,
            payer_organization_id=payer_organization_id,
            payer_request_id=payer_request.id,
            occurrence_key="scope-patient-001",
        )
        doctor_notification, _ = create_notification(
            db,
            recipient=doctor,
            event_type="missing_information_warning",
            source_resource_id=payer_request.id,
            scheduled_for=datetime.now(UTC),
            patient_id=patient.patient_profile.id,
            clinical_event_id=clinical_event.id,
            payer_organization_id=payer_organization_id,
            payer_request_id=payer_request.id,
            occurrence_key="scope-doctor-001",
        )
        payer_notification, _ = create_notification(
            db,
            recipient=payer,
            event_type="payer_request_submitted",
            source_resource_id=payer_request.id,
            scheduled_for=datetime.now(UTC),
            patient_id=patient.patient_profile.id,
            clinical_event_id=clinical_event.id,
            payer_organization_id=payer_organization_id,
            payer_request_id=payer_request.id,
            occurrence_key="scope-payer-001",
        )
        with pytest.raises(ValueError, match="payer_notification_scope_mismatch"):
            create_notification(
                db,
                recipient=payer,
                event_type="payer_doctor_response_added",
                source_resource_id=payer_request.id,
                scheduled_for=datetime.now(UTC),
                patient_id=patient.patient_profile.id,
                clinical_event_id=clinical_event.id,
                payer_organization_id=unrelated_organization_id,
                payer_request_id=payer_request.id,
                occurrence_key="scope-payer-mismatch-001",
            )
        db.commit()
        patient_notification_id = patient_notification.id
        doctor_notification_id = doctor_notification.id
        payer_notification_id = payer_notification.id
        payer_request_id = payer_request.id
        relationship_id = relationship.id
        payer_membership_id = db.scalar(
            select(PayerMembership.id).where(
                PayerMembership.user_id == payer_user_id,
                PayerMembership.payer_organization_id == payer_organization_id,
            )
        )
        assert payer_membership_id is not None

    assert client.get("/api/v1/notifications", headers=patient_headers).json()["unread_count"] == 1
    assert client.get("/api/v1/notifications", headers=doctor_headers).json()["unread_count"] == 1
    assert client.get("/api/v1/notifications", headers=payer_headers).json()["unread_count"] == 1
    payer_inbox = client.get("/api/v1/notifications", headers=payer_headers)
    assert payer_inbox.status_code == 200
    assert "CONFIDENTIAL-PAYER-SUMMARY-MUST-NOT-LEAK" not in payer_inbox.text
    for headers in (
        unrelated_patient_headers,
        unrelated_doctor_headers,
        unrelated_payer_headers,
    ):
        assert client.get("/api/v1/notifications", headers=headers).json()["unread_count"] == 0

    patient_open = client.post(
        f"/api/v1/notifications/{patient_notification_id}/open",
        headers=patient_headers,
    )
    doctor_open = client.post(
        f"/api/v1/notifications/{doctor_notification_id}/open",
        headers=doctor_headers,
    )
    payer_open = client.post(
        f"/api/v1/notifications/{payer_notification_id}/open",
        headers=payer_headers,
    )
    assert patient_open.json()["status"] == "resolved"
    assert doctor_open.json()["status"] == "resolved"
    assert payer_open.json()["status"] == "resolved"
    assert str(payer_request_id) in payer_open.json()["route_path"]
    assert "CONFIDENTIAL-PAYER-SUMMARY-MUST-NOT-LEAK" not in payer_open.text

    assert (
        client.post(
            f"/api/v1/notifications/{payer_notification_id}/open",
            headers=unrelated_payer_headers,
        ).status_code
        == 404
    )

    with Session(engine) as db:
        relationship = db.get(CareRelationship, relationship_id)
        membership = db.get(PayerMembership, payer_membership_id)
        assert relationship is not None and membership is not None
        relationship.is_active = False
        membership.status = "revoked"
        db.commit()

    assert (
        client.post(
            f"/api/v1/notifications/{doctor_notification_id}/open",
            headers=doctor_headers,
        ).json()["status"]
        == "denied"
    )
    assert (
        client.post(
            f"/api/v1/notifications/{payer_notification_id}/open",
            headers=payer_headers,
        ).json()["status"]
        == "denied"
    )


def test_patient_deep_link_becomes_unavailable_when_authoritative_source_is_stale(
    client: TestClient,
) -> None:
    headers, user_id = _patient(client, "stale-open")
    due_at = datetime.now(UTC) + timedelta(hours=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic stale-open reminder",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="stale-open-medication-001",
        )
        db.commit()
        notification_id = notification.id
        reminder_id = reminder.id

    with Session(engine) as db:
        reminder = db.get(MedicationReminder, reminder_id)
        assert reminder is not None
        reminder.status = "cancelled"
        db.commit()

    opened = client.post(
        f"/api/v1/notifications/{notification_id}/open",
        headers=headers,
    )
    assert opened.status_code == 200
    assert opened.json()["status"] == "unavailable"


def test_quiet_hours_span_midnight_and_stale_source_is_suppressed_before_delivery(
    client: TestClient,
) -> None:
    shifted = after_quiet_hours(
        datetime(2026, 7, 30, 14, 30, tzinfo=UTC),
        time_zone="Asia/Shanghai",
        quiet_hours_start="22:00",
        quiet_hours_end="07:00",
    )
    assert shifted == datetime(2026, 7, 30, 23, 0, tzinfo=UTC)

    _, user_id = _patient(client, "worker")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["android_emas"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic schedule",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=reminder.next_due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="stale-medication-reminder-001",
        )
        reminder.status = "cancelled"
        db.commit()
        notification_id = notification.id

    with Session(engine) as db:
        assert process_one(
            db,
            get_settings(),
            deliver=lambda request: (_ for _ in ()).throw(
                AssertionError(f"delivery should not run for stale {request.channel}")
            ),
        )
    with Session(engine) as db:
        notification = db.get(Notification, notification_id)
        assert notification is not None
        assert notification.status == "cancelled"
        assert db.scalar(select(NotificationDeliveryAttempt).limit(1)) is None


def test_fail_closed_adapter_records_one_bounded_attempt_without_fake_receipt(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "delivery-fail-closed")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["android_emas"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="PRIVATE-MEDICATION-DETAIL-MUST-NOT-LEAK",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, replayed = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="fail-closed-attempt-001",
        )
        assert replayed is False
        db.commit()
        notification_id = notification.id

    with Session(engine) as db:
        assert process_one(db, get_settings()) is True

    with Session(engine) as db:
        notification = db.get(Notification, notification_id)
        outbox = db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.notification_id == notification_id)
        )
        attempt = db.scalar(
            select(NotificationDeliveryAttempt)
            .join(NotificationOutbox)
            .where(NotificationOutbox.notification_id == notification_id)
        )
        assert notification is not None and outbox is not None and attempt is not None
        assert outbox.status == "failed"
        assert outbox.attempt_count == 1
        assert attempt.result_state == "failed"
        assert attempt.retryable is False
        assert attempt.provider_receipt_hash is None
        assert attempt.result_code in {
            "external_delivery_disabled",
            "missing_app_key",
            "transport_runtime_not_activated",
        }
        bounded_evidence = " ".join(
            [
                notification.title,
                notification.body,
                notification.deduplication_key,
                notification.content_checksum,
                attempt.adapter_code,
                attempt.result_code,
            ]
        )
        assert "PRIVATE-MEDICATION-DETAIL-MUST-NOT-LEAK" not in bounded_evidence


def test_adapter_exception_is_recorded_as_bounded_retryable_attempt(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "delivery-exception")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["android_emas"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic adapter exception reminder",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="adapter-exception-001",
        )
        db.commit()
        notification_id = notification.id

    def _transport_timeout(request):
        raise TimeoutError(f"synthetic transport timeout for {request.channel}")

    with Session(engine) as db:
        assert process_one(db, get_settings(), deliver=_transport_timeout) is True

    with Session(engine) as db:
        outbox = db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.notification_id == notification_id)
        )
        attempt = db.scalar(
            select(NotificationDeliveryAttempt)
            .join(NotificationOutbox)
            .where(NotificationOutbox.notification_id == notification_id)
        )
        assert outbox is not None and attempt is not None
        assert outbox.status == "retrying"
        assert outbox.attempt_count == 1
        assert attempt.result_state == "failed"
        assert attempt.result_code == "transport_exception"
        assert attempt.retryable is True
        assert attempt.provider_receipt_hash is None


def test_delivery_idempotency_hook_is_stable_across_retry(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "delivery-idempotency")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["web_push"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic retry idempotency reminder",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="delivery-idempotency-001",
        )
        db.commit()
        notification_id = notification.id

    requests = []
    observations = []

    def retryable_failure(request):
        requests.append(request)
        return DeliveryResult(state="failed", code="synthetic_timeout", retryable=True)

    with Session(engine) as db:
        assert process_one(
            db,
            get_settings(),
            deliver=retryable_failure,
            observe=observations.append,
        )
    with Session(engine) as db:
        outbox = db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.notification_id == notification_id)
        )
        assert outbox is not None
        outbox.available_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    with Session(engine) as db:
        assert process_one(
            db,
            get_settings(),
            deliver=retryable_failure,
            observe=observations.append,
        )

    assert [request.attempt_number for request in requests] == [1, 2]
    assert requests[0].idempotency_key == requests[1].idempotency_key
    assert [observation.outcomes for observation in observations] == [
        ("attempted", "failed"),
        ("attempted", "failed"),
    ]
    assert all(
        "patient" not in str(observation).lower() and "medication" not in str(observation).lower()
        for observation in observations
    )
    assert operational_outcomes(
        DeliveryResult(state="accepted", code="synthetic_accept", retryable=False)
    ) == ("attempted", "provider_accepted")


def test_concurrent_workers_do_not_deliver_the_same_claim_twice(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "worker-concurrency")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["web_push"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic concurrent worker reminder",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="worker-concurrency-001",
        )
        db.commit()
        notification_id = notification.id

    entered = threading.Event()
    release = threading.Event()
    calls = []
    results = []

    def delayed_accept(request):
        calls.append(request)
        entered.set()
        assert release.wait(timeout=5)
        return DeliveryResult(state="accepted", code="synthetic_accept", retryable=False)

    def run_worker() -> None:
        with Session(engine) as db:
            results.append(process_one(db, get_settings(), deliver=delayed_accept))

    first = threading.Thread(target=run_worker)
    second = threading.Thread(target=run_worker)
    first.start()
    assert entered.wait(timeout=5)
    second.start()
    second.join(timeout=5)
    release.set()
    first.join(timeout=5)
    assert not first.is_alive() and not second.is_alive()
    assert calls and len(calls) == 1
    assert sorted(results) == [False, True]
    with Session(engine) as db:
        assert (
            db.scalar(
                select(func.count(NotificationDeliveryAttempt.id))
                .join(NotificationOutbox)
                .where(NotificationOutbox.notification_id == notification_id)
            )
            == 1
        )


def test_concurrent_creation_deduplicates_one_occurrence(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "creation-concurrency")
    source_id = uuid.uuid4()
    scheduled_for = datetime.now(UTC) + timedelta(hours=1)
    barrier = threading.Barrier(2)
    notification_ids = []
    replay_flags = []
    errors = []

    def create_once() -> None:
        try:
            with Session(engine) as db:
                user = db.get(User, user_id)
                assert user is not None and user.patient_profile is not None
                barrier.wait(timeout=5)
                notification, replayed = create_notification(
                    db,
                    recipient=user,
                    event_type="recovery_task_due",
                    source_resource_id=source_id,
                    scheduled_for=scheduled_for,
                    patient_id=user.patient_profile.id,
                    occurrence_key="concurrent-occurrence-001",
                )
                db.commit()
                notification_ids.append(notification.id)
                replay_flags.append(replayed)
        except Exception as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    workers = [threading.Thread(target=create_once) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
    assert all(not worker.is_alive() for worker in workers)
    assert errors == []
    assert len(set(notification_ids)) == 1
    assert sorted(replay_flags) == [False, True]
    with Session(engine) as db:
        assert (
            db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.source_resource_id == source_id
                )
            )
            == 1
        )


def test_cancellation_during_delivery_contains_local_state(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "delivery-cancellation")
    due_at = datetime.now(UTC) - timedelta(minutes=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        db.add(
            NotificationPreference(
                user_id=user.id,
                role="patient",
                allowed_categories_json=["medication_reminder"],
                external_channels_json=["web_push"],
                in_product_enabled=True,
                locale="en",
                time_zone="UTC",
                preview_level="generic",
            )
        )
        reminder = MedicationReminder(
            patient_id=user.patient_profile.id,
            schedule_label="Synthetic cancellation race reminder",
            channel="in_app",
            status="active",
            next_due_at=due_at,
            metadata_json={"reminder_type": "medication"},
        )
        db.add(reminder)
        db.flush()
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="medication_reminder",
            source_resource_id=reminder.id,
            scheduled_for=due_at,
            patient_id=user.patient_profile.id,
            occurrence_key="delivery-cancellation-001",
        )
        db.commit()
        notification_id = notification.id
        reminder_id = reminder.id

    entered = threading.Event()
    release = threading.Event()

    def delayed_accept(request):
        entered.set()
        assert release.wait(timeout=5)
        return DeliveryResult(
            state="accepted",
            code="synthetic_accept",
            retryable=False,
            provider_receipt_hash=hashlib.sha256(b"synthetic-receipt").hexdigest(),
        )

    def run_worker() -> None:
        with Session(engine) as db:
            assert process_one(db, get_settings(), deliver=delayed_accept)

    worker = threading.Thread(target=run_worker)
    worker.start()
    assert entered.wait(timeout=5)
    with Session(engine) as db:
        reminder = db.get(MedicationReminder, reminder_id)
        assert reminder is not None
        reminder.status = "cancelled"
        suppress_source_notifications(
            db,
            source_category="medication_reminder",
            source_resource_id=reminder_id,
            reason_code="synthetic_cancel_during_delivery",
            actor_user_id=None,
        )
        db.commit()
    release.set()
    worker.join(timeout=5)
    assert not worker.is_alive()

    with Session(engine) as db:
        notification = db.get(Notification, notification_id)
        outbox = db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.notification_id == notification_id)
        )
        attempt = db.scalar(
            select(NotificationDeliveryAttempt)
            .join(NotificationOutbox)
            .where(NotificationOutbox.notification_id == notification_id)
        )
        assert notification is not None and outbox is not None and attempt is not None
        assert notification.status == "cancelled"
        assert outbox.status == "cancelled"
        assert attempt.result_state == "accepted"
        assert attempt.result_code == "provider_accepted_after_cancellation"
        assert attempt.provider_receipt_hash == hashlib.sha256(b"synthetic-receipt").hexdigest()


def test_expiry_policy_begins_at_scheduled_time_not_creation_time(
    client: TestClient,
) -> None:
    _, user_id = _patient(client, "scheduled-expiry")
    scheduled_for = datetime.now(UTC) + timedelta(days=30)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        notification, _ = create_notification(
            db,
            recipient=user,
            event_type="recovery_task_due",
            source_resource_id=uuid.uuid4(),
            scheduled_for=scheduled_for,
            patient_id=user.patient_profile.id,
            occurrence_key="scheduled-expiry-001",
        )
        db.commit()
        assert notification.expires_at == scheduled_for + timedelta(hours=72)
        assert notification.expires_at > notification.scheduled_for


def test_canonical_notification_replay_conflict_supersession_and_redaction(
    client: TestClient,
) -> None:
    headers, user_id = _patient(client, "canonical")
    source_id = uuid.uuid4()
    first_due = datetime.now(UTC) + timedelta(hours=1)
    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        first, replayed = create_notification(
            db,
            recipient=user,
            event_type="recovery_task_due",
            source_resource_id=source_id,
            scheduled_for=first_due,
            patient_id=user.patient_profile.id,
            occurrence_key="canonical-occurrence-001",
        )
        assert replayed is False
        db.commit()
        first_id = first.id

    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        replay, replayed = create_notification(
            db,
            recipient=user,
            event_type="recovery_task_due",
            source_resource_id=source_id,
            scheduled_for=first_due,
            patient_id=user.patient_profile.id,
            occurrence_key="canonical-occurrence-001",
        )
        assert replayed is True
        assert replay.id == first_id
        db.commit()
        assert (
            db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.source_resource_id == source_id
                )
            )
            == 1
        )

    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        try:
            create_notification(
                db,
                recipient=user,
                event_type="recovery_task_due",
                source_resource_id=source_id,
                scheduled_for=first_due + timedelta(minutes=1),
                patient_id=user.patient_profile.id,
                occurrence_key="canonical-occurrence-001",
            )
        except RuntimeError as exc:
            assert str(exc) == "notification_deduplication_content_conflict"
            db.rollback()
        else:
            raise AssertionError("conflicting canonical replay must fail closed")

    with Session(engine) as db:
        user = db.get(User, user_id)
        assert user is not None and user.patient_profile is not None
        successor, replayed = create_notification(
            db,
            recipient=user,
            event_type="recovery_task_due",
            source_resource_id=source_id,
            scheduled_for=first_due + timedelta(days=1),
            patient_id=user.patient_profile.id,
            occurrence_key="canonical-occurrence-002",
        )
        assert replayed is False
        db.commit()
        successor_id = successor.id

    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    response_text = response.text
    assert "CONFIDENTIAL" not in response_text
    with Session(engine) as db:
        first = db.get(Notification, first_id)
        successor = db.get(Notification, successor_id)
        assert first is not None and successor is not None
        assert first.status == "superseded"
        assert first.superseded_by_id == successor.id
        assert successor.status == "unread"
        assert first.deduplication_key != successor.deduplication_key
        assert all(
            event.evidence_json.keys() <= {"event_type", "reason_code"}
            for event in [*first.events, *successor.events]
        )
