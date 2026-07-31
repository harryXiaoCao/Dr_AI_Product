import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import (
    AnalyticsEvent,
    AuditEvent,
    SupportRequest,
    SupportRequestEvent,
    User,
    UserRole,
)
from app.security import hash_password
from app.support_operations import SupportTransitionError, transition_support_request
from tests.helpers import auth_header, register


def _payer(client: TestClient) -> dict[str, str]:
    email = "phase5.payer@example.com"
    digest = hashlib.sha1(email.encode("utf-8")).hexdigest()[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "phone_number": f"+1666{int(digest, 16) % 10_000_000:07d}",
            "password": "PayerReview9!",
            "role": "payer",
            "verification_code": "123456",
            "terms_accepted": True,
            "payer_profile": {
                "display_name": "Phase 5 Reviewer",
                "organization_name": "Phase 5 Synthetic Payer",
                "title": "Reviewer",
                "organization_type": "public_payer",
            },
        },
    )
    assert response.status_code == 201, response.text
    return auth_header(response.json()["access_token"])


def _analytics_body(
    *,
    event_name: str = "journey_completed",
    key: str = "patient-support-complete-001",
) -> dict[str, object]:
    return {
        "event_name": event_name,
        "deduplication_key": key,
        "dimensions": {
            "journey_code": "account_support",
            "surface_code": "account",
            "outcome": "completed",
            "latency_bucket": "250_999ms",
            "locale": "zh-Hans",
            "platform": "web",
            "layout": "mobile",
        },
    }


def _operational_actor() -> uuid.UUID:
    with Session(engine) as db:
        actor = User(
            email=f"phase5.support.ops.{uuid.uuid4().hex}@example.com",
            password_hash=hash_password("generated test passphrase"),
            role=UserRole.admin,
        )
        db.add(actor)
        db.commit()
        return actor.id


def test_support_lifecycle_replays_conflicts_withdraws_and_isolates_requesters(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.support.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    unrelated = register(
        client,
        email="phase5.support.unrelated@example.com",
        password="Patient9!",
        role="patient",
    )
    headers = {
        **auth_header(patient["access_token"]),
        "Idempotency-Key": "deletion-submit-001",
    }
    payload = {
        "request_type": "deletion",
        "subject": "Account deletion review",
        "message": "Please review my account deletion request.",
    }

    created = client.post("/api/v1/support-requests", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["reference"].startswith("REQ-")
    assert body["version"] == 1
    assert body["retention_boundary_code"] == "regulated_and_audit_retention_applies"
    assert body["deletion_effect_code"] == "request_only_no_immediate_deletion"
    assert body["available_actions"] == ["withdraw"]
    assert body["timeline"][0]["summary_code"] == "request_submitted"
    assert "requester_user_id" not in body

    replay = client.post("/api/v1/support-requests", headers=headers, json=payload)
    assert replay.status_code == 201
    assert replay.json()["request_id"] == body["request_id"]
    assert replay.json()["replayed"] is True

    changed = client.post(
        "/api/v1/support-requests",
        headers=headers,
        json={**payload, "subject": "Changed deletion request"},
    )
    assert changed.status_code == 409
    assert changed.json()["error"]["code"] == "conflict"

    unrelated_read = client.get(
        f"/api/v1/support-requests/{body['request_id']}",
        headers=auth_header(unrelated["access_token"]),
    )
    assert unrelated_read.status_code == 404

    withdraw_headers = {
        **auth_header(patient["access_token"]),
        "Idempotency-Key": "deletion-withdraw-001",
    }
    withdrawn = client.post(
        f"/api/v1/support-requests/{body['request_id']}/withdraw",
        headers=withdraw_headers,
        json={"expected_version": 1},
    )
    assert withdrawn.status_code == 200, withdrawn.text
    withdrawn_body = withdrawn.json()
    assert withdrawn_body["status"] == "cancelled"
    assert withdrawn_body["version"] == 2
    assert withdrawn_body["available_actions"] == []
    assert [event["event_type"] for event in withdrawn_body["timeline"]] == [
        "submitted",
        "withdrawn",
    ]

    withdraw_replay = client.post(
        f"/api/v1/support-requests/{body['request_id']}/withdraw",
        headers=withdraw_headers,
        json={"expected_version": 1},
    )
    assert withdraw_replay.status_code == 200
    assert withdraw_replay.json()["replayed"] is True

    with Session(engine) as db:
        stored = db.scalar(select(SupportRequest))
        assert stored is not None
        assert stored.body_redacted == payload["message"]
        assert stored.request_checksum != payload["message"]
        assert db.scalar(select(func.count()).select_from(SupportRequest)) == 1
        assert db.scalar(select(func.count()).select_from(SupportRequestEvent)) == 2
        audits = db.scalars(
            select(AuditEvent).where(AuditEvent.resource_id == stored.id)
        ).all()
        assert {event.event_type for event in audits} >= {
            "support_request_queued",
            "support_request_withdrawn",
        }
        for audit in audits:
            serialized = str(audit.metadata_json)
            assert payload["message"] not in serialized
            assert payload["subject"] not in serialized


def test_payer_can_submit_feedback_without_editing_organization_identity(
    client: TestClient,
) -> None:
    payer_headers = _payer(client)
    created = client.post(
        "/api/v1/support-requests",
        headers={**payer_headers, "Idempotency-Key": "payer-feedback-submit-001"},
        json={
            "request_type": "feedback",
            "subject": "Review workspace feedback",
            "message": "Please keep the review history easier to scan.",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["request_type"] == "feedback"
    assert created.json()["retention_boundary_code"] == "standard_support_retention"
    assert created.json()["deletion_effect_code"] == "not_a_deletion_request"

    profile = client.get("/api/v1/payer/me/profile", headers=payer_headers)
    assert profile.status_code == 200
    assert profile.json()["organization"]["verification_status"] == "synthetic_only"


def test_product_analytics_is_allow_listed_identity_free_and_deduplicated(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.analytics.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    headers = auth_header(patient["access_token"])
    payload = _analytics_body()

    created = client.post("/api/v1/product-events", headers=headers, json=payload)
    assert created.status_code == 202, created.text
    assert created.json() == {"accepted": True, "persisted": True, "replayed": False}

    replay = client.post("/api/v1/product-events", headers=headers, json=payload)
    assert replay.status_code == 202
    assert replay.json() == {"accepted": True, "persisted": True, "replayed": True}

    conflict_payload = _analytics_body(event_name="journey_started")
    conflict_payload["dimensions"]["outcome"] = "started"  # type: ignore[index]
    conflict = client.post(
        "/api/v1/product-events",
        headers=headers,
        json=conflict_payload,
    )
    assert conflict.status_code == 409

    identity_attempt = _analytics_body(key="identity-injection-attempt-001")
    identity_attempt["dimensions"]["patient_id"] = "patient-secret"  # type: ignore[index]
    rejected = client.post(
        "/api/v1/product-events",
        headers=headers,
        json=identity_attempt,
    )
    assert rejected.status_code == 422

    with Session(engine) as db:
        event = db.scalar(select(AnalyticsEvent))
        assert event is not None
        assert event.actor_user_id is None
        assert event.patient_id is None
        assert event.clinic_id is None
        assert event.resource_id is None
        assert event.role == "patient"
        assert event.environment == "test"
        assert event.schema_version == "content_free_product_v1"
        assert event.deduplication_key == hashlib.sha256(
            payload["deduplication_key"].encode("utf-8")  # type: ignore[union-attr]
        ).hexdigest()
        assert payload["deduplication_key"] not in event.deduplication_key
        assert set(event.metadata_json) == {
            "journey_code",
            "surface_code",
            "outcome",
            "failure_category",
            "latency_bucket",
            "locale",
            "platform",
            "layout",
        }
        serialized = str(event.metadata_json)
        assert "phase5.analytics.patient@example.com" not in serialized
        assert "patient-secret" not in serialized
        stored_fields = {
            "actor_user_id": event.actor_user_id,
            "patient_id": event.patient_id,
            "clinic_id": event.clinic_id,
            "resource_id": event.resource_id,
            "event_type": event.event_type,
            "resource_type": event.resource_type,
            "role": event.role,
            "environment": event.environment,
            "schema_version": event.schema_version,
            "deduplication_key": event.deduplication_key,
            "event_checksum": event.event_checksum,
            "outcome": event.outcome,
            "failure_category": event.failure_category,
            "latency_ms": event.latency_ms,
            "metadata_json": event.metadata_json,
        }
        all_stored_content = str(stored_fields)
        assert payload["deduplication_key"] not in all_stored_content
        assert patient["user"]["id"] not in all_stored_content
        assert patient["user"]["email"] not in all_stored_content


def test_product_analytics_role_boundary_and_storage_failure_are_non_blocking(
    client: TestClient,
    monkeypatch,
) -> None:
    payer_headers = _payer(client)
    denied_payload = _analytics_body(key="payer-patient-chat-denied-001")
    denied_payload["dimensions"]["journey_code"] = "patient_chat"  # type: ignore[index]
    denied_payload["dimensions"]["surface_code"] = "chat"  # type: ignore[index]
    denied = client.post(
        "/api/v1/product-events",
        headers=payer_headers,
        json=denied_payload,
    )
    assert denied.status_code == 422

    original_commit = Session.commit

    def fail_commit(session: Session) -> None:
        if any(isinstance(item, AnalyticsEvent) for item in session.new):
            raise OperationalError("INSERT", {}, RuntimeError("analytics unavailable"))
        original_commit(session)

    monkeypatch.setattr(Session, "commit", fail_commit)
    payload = _analytics_body(key="payer-storage-failure-001")
    payload["dimensions"]["journey_code"] = "payer_manual_review"  # type: ignore[index]
    payload["dimensions"]["surface_code"] = "payer_request"  # type: ignore[index]
    result = client.post("/api/v1/product-events", headers=payer_headers, json=payload)
    assert result.status_code == 202
    assert result.json() == {"accepted": True, "persisted": False, "replayed": False}


def test_product_analytics_rejects_inconsistent_event_outcome_and_surface(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.analytics.consistency@example.com",
        password="Patient9!",
        role="patient",
    )
    headers = auth_header(patient["access_token"])

    wrong_outcome = _analytics_body(
        event_name="workflow_failed",
        key="wrong-outcome-event-001",
    )
    failed_outcome = client.post(
        "/api/v1/product-events",
        headers=headers,
        json=wrong_outcome,
    )
    assert failed_outcome.status_code == 422

    wrong_surface = _analytics_body(key="wrong-surface-event-001")
    wrong_surface["dimensions"]["surface_code"] = "chat"  # type: ignore[index]
    failed_surface = client.post(
        "/api/v1/product-events",
        headers=headers,
        json=wrong_surface,
    )
    assert failed_surface.status_code == 422

    wrong_notification_journey = _analytics_body(
        event_name="notification_inbox_opened",
        key="wrong-notification-journey-001",
    )
    wrong_notification_journey["dimensions"]["outcome"] = "opened"  # type: ignore[index]
    failed_notification = client.post(
        "/api/v1/product-events",
        headers=headers,
        json=wrong_notification_journey,
    )
    assert failed_notification.status_code == 422


def test_non_public_support_operations_are_idempotent_attributable_and_visible(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.operations.patient@example.com",
        password="Patient9!",
        role="patient",
    )
    patient_headers = auth_header(patient["access_token"])
    created = client.post(
        "/api/v1/support-requests",
        headers={
            **patient_headers,
            "Idempotency-Key": "operations-support-create-001",
        },
        json={
            "request_type": "support",
            "subject": "Account access support",
            "message": "Please review this account access workflow.",
        },
    )
    assert created.status_code == 201
    reference = created.json()["reference"]
    actor_id = _operational_actor()

    with Session(engine) as db:
        reviewing = transition_support_request(
            db,
            public_reference=reference,
            action="start_review",
            expected_version=1,
            idempotency_key="operations-start-review-001",
            actor_user_id=actor_id,
        )
    assert reviewing.status == "reviewing"
    assert reviewing.version == 2
    assert reviewing.replayed is False

    with Session(engine) as db:
        replay = transition_support_request(
            db,
            public_reference=reference,
            action="start_review",
            expected_version=1,
            idempotency_key="operations-start-review-001",
            actor_user_id=actor_id,
        )
    assert replay.replayed is True
    assert replay.status == "reviewing"

    with Session(engine) as db:
        resolved = transition_support_request(
            db,
            public_reference=reference,
            action="resolve",
            expected_version=2,
            idempotency_key="operations-resolve-001",
            actor_user_id=actor_id,
        )
    assert resolved.status == "resolved"
    assert resolved.version == 3

    readback = client.get(
        f"/api/v1/support-requests/{created.json()['request_id']}",
        headers=patient_headers,
    )
    assert readback.status_code == 200
    body = readback.json()
    assert body["status"] == "resolved"
    assert body["version"] == 3
    assert [event["summary_code"] for event in body["timeline"]] == [
        "request_submitted",
        "support_review_started",
        "support_request_resolved",
    ]
    assert [event["actor_kind"] for event in body["timeline"]] == [
        "requester",
        "support_team",
        "support_team",
    ]
    assert all("actor_user_id" not in event for event in body["timeline"])

    with Session(engine) as db:
        audits = db.scalars(
            select(AuditEvent).where(
                AuditEvent.resource_id == uuid.UUID(body["request_id"]),
                AuditEvent.event_type == "support_request_status_changed",
            )
        ).all()
    assert len(audits) == 2
    assert {event.metadata_json["to_status"] for event in audits} == {
        "reviewing",
        "resolved",
    }


def test_non_public_support_operation_serializes_concurrent_transitions(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.operations.concurrent@example.com",
        password="Patient9!",
        role="patient",
    )
    created = client.post(
        "/api/v1/support-requests",
        headers={
            **auth_header(patient["access_token"]),
            "Idempotency-Key": "operations-concurrent-create-001",
        },
        json={
            "request_type": "feedback",
            "subject": "Concurrent transition feedback",
            "message": "Please verify concurrent transition handling.",
        },
    )
    assert created.status_code == 201
    reference = created.json()["reference"]
    actor_id = _operational_actor()

    def apply(index: int) -> str:
        with SessionLocal() as db:
            try:
                transition_support_request(
                    db,
                    public_reference=reference,
                    action="start_review",
                    expected_version=1,
                    idempotency_key=f"operations-concurrent-{index:03d}",
                    actor_user_id=actor_id,
                )
            except SupportTransitionError as exc:
                db.rollback()
                return str(exc)
            return "applied"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(apply, range(2)))
    assert outcomes.count("applied") == 1
    assert outcomes.count("stale_expected_version") == 1

    with Session(engine) as db:
        request = db.scalar(
            select(SupportRequest).where(SupportRequest.public_reference == reference)
        )
        assert request is not None
        assert request.status == "reviewing"
        assert request.version == 2
        event_count = db.scalar(
            select(func.count())
            .select_from(SupportRequestEvent)
            .where(SupportRequestEvent.support_request_id == request.id)
        )
        assert event_count == 2


def test_non_public_support_operation_recovers_failed_request_to_queue(
    client: TestClient,
) -> None:
    patient = register(
        client,
        email="phase5.operations.retry@example.com",
        password="Patient9!",
        role="patient",
    )
    headers = auth_header(patient["access_token"])
    created = client.post(
        "/api/v1/support-requests",
        headers={**headers, "Idempotency-Key": "operations-retry-create-001"},
        json={
            "request_type": "support",
            "subject": "Recoverable processing request",
            "message": "Please process this recoverable account request.",
        },
    )
    assert created.status_code == 201
    reference = created.json()["reference"]
    actor_id = _operational_actor()

    transitions = (
        ("start_review", 1, "operations-retry-review-001", "reviewing"),
        ("mark_failed", 2, "operations-retry-failed-001", "failed"),
        ("retry_queue", 3, "operations-retry-queue-001", "queued"),
    )
    for action, version, key, expected_status in transitions:
        with Session(engine) as db:
            result = transition_support_request(
                db,
                public_reference=reference,
                action=action,
                expected_version=version,
                idempotency_key=key,
                actor_user_id=actor_id,
                actor_kind="system",
            )
        assert result.status == expected_status

    readback = client.get(
        f"/api/v1/support-requests/{created.json()['request_id']}",
        headers=headers,
    )
    assert readback.status_code == 200
    body = readback.json()
    assert body["status"] == "queued"
    assert body["version"] == 4
    assert [event["summary_code"] for event in body["timeline"]] == [
        "request_submitted",
        "support_review_started",
        "support_processing_failed",
        "support_requeued_after_failure",
    ]
