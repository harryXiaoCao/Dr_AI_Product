#!/usr/bin/env python3
"""Run redaction-safe Dr. AI staging smoke checks over HTTPS."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://dr-ai.43.132.169.195.sslip.io"
DEFAULT_DOCTOR_EMAIL = "doctor.demo@example.com"
DEFAULT_PATIENT_EMAIL = "patient.demo@example.com"
DEFAULT_UNRELATED_EMAIL = "unrelated.patient@example.com"


class SmokeFailure(Exception):
    pass


@dataclass
class ApiResponse:
    status: int
    body: dict[str, Any] | None


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    raise SmokeFailure(f"Missing required environment variable: {name}")


def request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    additional_headers: dict[str, str] | None = None,
    expected_status: int | set[int] = 200,
) -> ApiResponse:
    data = None
    headers = {"Accept": "application/json"}
    if additional_headers is not None:
        headers.update(additional_headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - approved staging origin.
            status = response.status
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        status = exc.code
        raw_body = exc.read().decode("utf-8")
    except URLError as exc:
        raise SmokeFailure(f"{method} {path} failed to connect: {exc.reason}") from exc

    try:
        body = json.loads(raw_body) if raw_body else None
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{method} {path} returned non-JSON body with status {status}") from exc

    expected = {expected_status} if isinstance(expected_status, int) else expected_status
    if status not in expected:
        safe_code = None
        if isinstance(body, dict):
            safe_code = body.get("error", {}).get("code")
        raise SmokeFailure(
            f"{method} {path} returned {status}, expected {sorted(expected)}, code={safe_code}"
        )
    return ApiResponse(status=status, body=body)


def request_text(
    base_url: str,
    method: str,
    path: str,
    *,
    expected_status: int | set[int] = 200,
) -> tuple[int, str]:
    request = Request(
        f"{base_url.rstrip('/')}{path}", headers={"Accept": "text/html"}, method=method
    )
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - approved staging origin.
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8")
    except URLError as exc:
        raise SmokeFailure(f"{method} {path} failed to connect: {exc.reason}") from exc

    expected = {expected_status} if isinstance(expected_status, int) else expected_status
    if status not in expected:
        raise SmokeFailure(f"{method} {path} returned {status}, expected {sorted(expected)}")
    return status, body


def login(base_url: str, email: str, password: str) -> dict[str, Any]:
    response = request_json(
        base_url,
        "POST",
        "/api/v1/auth/login",
        payload={"email": email, "password": password},
    )
    assert response.body is not None
    if not response.body.get("access_token") or not response.body.get("refresh_token"):
        raise SmokeFailure(f"Login for {email} did not return both token types")
    return response.body


def ok(label: str) -> None:
    print(f"PASS {label}")


def main() -> int:
    base_url = os.environ.get("DR_AI_STAGING_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    doctor_email = os.environ.get("DR_AI_STAGING_DOCTOR_EMAIL", DEFAULT_DOCTOR_EMAIL)
    patient_email = os.environ.get("DR_AI_STAGING_PATIENT_EMAIL", DEFAULT_PATIENT_EMAIL)
    unrelated_email = os.environ.get(
        "DR_AI_STAGING_UNRELATED_PATIENT_EMAIL", DEFAULT_UNRELATED_EMAIL
    )
    doctor_password = env_required("DR_AI_STAGING_DOCTOR_PASSWORD")
    patient_password = env_required("DR_AI_STAGING_PATIENT_PASSWORD")
    unrelated_password = os.environ.get("DR_AI_STAGING_UNRELATED_PATIENT_PASSWORD")
    unrelated_patient_id = os.environ.get("DR_AI_STAGING_UNRELATED_PATIENT_ID")
    payer_email = os.environ.get("DR_AI_STAGING_PAYER_EMAIL")
    payer_password = os.environ.get("DR_AI_STAGING_PAYER_PASSWORD")
    if bool(payer_email) != bool(payer_password):
        raise SmokeFailure(
            "DR_AI_STAGING_PAYER_EMAIL and DR_AI_STAGING_PAYER_PASSWORD must "
            "either both be set or both be omitted"
        )

    health = request_json(base_url, "GET", "/health")
    required_health = {
        "status": "ok",
        "service": "dr-ai-api",
        "environment": "staging",
        "database": "ok",
    }
    if health.body is None or any(
        health.body.get(key) != value for key, value in required_health.items()
    ):
        raise SmokeFailure(f"Unexpected health payload: {health.body}")
    if health.body.get("expected_care_explanation") not in {
        None,
        "disabled",
        "kill_switched",
        "no_active_compatible_release",
        "ready",
    }:
        raise SmokeFailure("Expected-care readiness category is not content-free")
    ok("health reports staging database ok")

    doctor_tokens = login(base_url, doctor_email, doctor_password)
    patient_tokens = login(base_url, patient_email, patient_password)
    doctor_access = doctor_tokens["access_token"]
    patient_access = patient_tokens["access_token"]
    ok("doctor and patient login")

    lifecycle_id = f"phase5-lifecycle-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    lifecycle_key = f"support-{lifecycle_id}"
    lifecycle_payload = {
        "request_type": "deletion",
        "subject": "Synthetic Phase 5 deletion review",
        "message": "Verify the persisted synthetic account request lifecycle.",
    }
    created_request = request_json(
        base_url,
        "POST",
        "/api/v1/support-requests",
        token=patient_access,
        payload=lifecycle_payload,
        additional_headers={"Idempotency-Key": lifecycle_key},
        expected_status=201,
    )
    assert created_request.body is not None
    request_id = created_request.body.get("request_id")
    request_reference = created_request.body.get("reference")
    request_version = created_request.body.get("version")
    if (
        not request_id
        or not request_reference
        or request_version != 1
        or created_request.body.get("status") != "queued"
        or created_request.body.get("replayed") is not False
        or (
            created_request.body.get("retention_boundary_code")
            != "regulated_and_audit_retention_applies"
        )
        or (
            created_request.body.get("deletion_effect_code")
            != "request_only_no_immediate_deletion"
        )
        or [item.get("event_type") for item in created_request.body.get("timeline", [])]
        != ["submitted"]
    ):
        raise SmokeFailure("Phase 5 support submission did not return a persisted receipt")
    replayed_request = request_json(
        base_url,
        "POST",
        "/api/v1/support-requests",
        token=patient_access,
        payload=lifecycle_payload,
        additional_headers={"Idempotency-Key": lifecycle_key},
        expected_status=201,
    )
    if (
        replayed_request.body is None
        or replayed_request.body.get("request_id") != request_id
        or replayed_request.body.get("replayed") is not True
    ):
        raise SmokeFailure("Phase 5 support retry was not replay-safe")
    support_conflict = request_json(
        base_url,
        "POST",
        "/api/v1/support-requests",
        token=patient_access,
        payload={**lifecycle_payload, "subject": "Changed synthetic deletion review"},
        additional_headers={"Idempotency-Key": lifecycle_key},
        expected_status=409,
    )
    if (
        support_conflict.body is None
        or support_conflict.body.get("error", {}).get("code") != "conflict"
    ):
        raise SmokeFailure("Phase 5 support changed-content replay was not rejected")
    request_json(
        base_url,
        "GET",
        f"/api/v1/support-requests/{request_id}",
        token=doctor_access,
        expected_status=404,
    )
    request_history = request_json(
        base_url,
        "GET",
        "/api/v1/support-requests",
        token=patient_access,
    )
    assert request_history.body is not None
    if request_reference not in {
        item.get("reference") for item in request_history.body.get("items", [])
    }:
        raise SmokeFailure("Phase 5 support receipt was absent from requester history")
    analytics_key = f"analytics-{lifecycle_id}"
    analytics_payload = {
        "event_name": "journey_completed",
        "deduplication_key": analytics_key,
        "dimensions": {
            "journey_code": "account_deletion",
            "surface_code": "account",
            "outcome": "completed",
            "latency_bucket": "not_measured",
            "locale": "en",
            "platform": "web",
            "layout": "desktop",
        },
    }
    analytics = request_json(
        base_url,
        "POST",
        "/api/v1/product-events",
        token=patient_access,
        payload=analytics_payload,
        expected_status=202,
    )
    if (
        analytics.body is None
        or analytics.body.get("accepted") is not True
        or analytics.body.get("persisted") is not True
        or analytics.body.get("replayed") is not False
    ):
        raise SmokeFailure("Phase 5 content-free product event was not persisted")
    analytics_replay = request_json(
        base_url,
        "POST",
        "/api/v1/product-events",
        token=patient_access,
        payload=analytics_payload,
        expected_status=202,
    )
    if (
        analytics_replay.body is None
        or analytics_replay.body.get("persisted") is not True
        or analytics_replay.body.get("replayed") is not True
    ):
        raise SmokeFailure("Phase 5 product-event retry was not replay-safe")
    analytics_conflict = request_json(
        base_url,
        "POST",
        "/api/v1/product-events",
        token=patient_access,
        payload={
            **analytics_payload,
            "event_name": "workflow_replayed",
            "dimensions": {
                **analytics_payload["dimensions"],
                "outcome": "replayed",
            },
        },
        expected_status=409,
    )
    if (
        analytics_conflict.body is None
        or analytics_conflict.body.get("error", {}).get("code") != "conflict"
    ):
        raise SmokeFailure("Phase 5 product-event changed replay was not rejected")
    analytics_identity_injection = request_json(
        base_url,
        "POST",
        "/api/v1/product-events",
        token=patient_access,
        payload={
            **analytics_payload,
            "deduplication_key": f"analytics-identity-{lifecycle_id}",
            "dimensions": {
                **analytics_payload["dimensions"],
                "patient_id": request_id,
            },
        },
        expected_status=422,
    )
    if (
        analytics_identity_injection.body is None
        or analytics_identity_injection.body.get("error", {}).get("code")
        != "validation_failed"
    ):
        raise SmokeFailure("Phase 5 product-event identity injection was not rejected")
    analytics_matrix_mismatch = request_json(
        base_url,
        "POST",
        "/api/v1/product-events",
        token=patient_access,
        payload={
            **analytics_payload,
            "event_name": "workflow_failed",
            "deduplication_key": f"analytics-matrix-{lifecycle_id}",
        },
        expected_status=422,
    )
    if (
        analytics_matrix_mismatch.body is None
        or analytics_matrix_mismatch.body.get("error", {}).get("code")
        != "validation_failed"
    ):
        raise SmokeFailure("Phase 5 product-event matrix mismatch was not rejected")
    withdrawn_request = request_json(
        base_url,
        "POST",
        f"/api/v1/support-requests/{request_id}/withdraw",
        token=patient_access,
        payload={"expected_version": request_version},
        additional_headers={"Idempotency-Key": f"withdraw-{lifecycle_id}"},
    )
    if (
        withdrawn_request.body is None
        or withdrawn_request.body.get("status") != "cancelled"
        or withdrawn_request.body.get("version") != 2
        or not any(
            item.get("event_type") == "withdrawn"
            for item in withdrawn_request.body.get("timeline", [])
        )
    ):
        raise SmokeFailure("Phase 5 support withdrawal did not persist its timeline")
    withdraw_replay = request_json(
        base_url,
        "POST",
        f"/api/v1/support-requests/{request_id}/withdraw",
        token=patient_access,
        payload={"expected_version": request_version},
        additional_headers={"Idempotency-Key": f"withdraw-{lifecycle_id}"},
    )
    if (
        withdraw_replay.body is None
        or withdraw_replay.body.get("status") != "cancelled"
        or withdraw_replay.body.get("replayed") is not True
    ):
        raise SmokeFailure("Phase 5 support withdrawal retry was not replay-safe")
    withdraw_conflict = request_json(
        base_url,
        "POST",
        f"/api/v1/support-requests/{request_id}/withdraw",
        token=patient_access,
        payload={"expected_version": 2},
        additional_headers={"Idempotency-Key": f"withdraw-{lifecycle_id}"},
        expected_status=409,
    )
    if (
        withdraw_conflict.body is None
        or withdraw_conflict.body.get("error", {}).get("code") != "conflict"
    ):
        raise SmokeFailure("Phase 5 withdrawal changed-content replay was not rejected")
    final_request = request_json(
        base_url,
        "GET",
        f"/api/v1/support-requests/{request_id}",
        token=patient_access,
    )
    if (
        final_request.body is None
        or final_request.body.get("status") != "cancelled"
        or [item.get("event_type") for item in final_request.body.get("timeline", [])]
        != ["submitted", "withdrawn"]
    ):
        raise SmokeFailure("Phase 5 final support history did not match persisted transitions")
    ok("Phase 5 support conflict/isolation/history and analytics replay/redaction")

    if payer_email is None or payer_password is None:
        print("SKIP payer credentialed Phase 5 lifecycle (credentials not supplied)")
    else:
        payer_tokens = login(base_url, payer_email, payer_password)
        payer_access = payer_tokens["access_token"]
        payer_lifecycle_id = (
            f"phase5-payer-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        )
        payer_support_key = f"payer-support-{payer_lifecycle_id}"
        payer_support_payload = {
            "request_type": "support",
            "subject": "Synthetic payer workspace support",
            "message": "Verify the persisted payer account support lifecycle.",
        }
        payer_created = request_json(
            base_url,
            "POST",
            "/api/v1/support-requests",
            token=payer_access,
            payload=payer_support_payload,
            additional_headers={"Idempotency-Key": payer_support_key},
            expected_status=201,
        )
        assert payer_created.body is not None
        payer_request_id = payer_created.body.get("request_id")
        payer_reference = payer_created.body.get("reference")
        if (
            not payer_request_id
            or not payer_reference
            or payer_created.body.get("status") != "queued"
            or payer_created.body.get("replayed") is not False
        ):
            raise SmokeFailure("Payer support submission did not persist a receipt")
        payer_replay = request_json(
            base_url,
            "POST",
            "/api/v1/support-requests",
            token=payer_access,
            payload=payer_support_payload,
            additional_headers={"Idempotency-Key": payer_support_key},
            expected_status=201,
        )
        if (
            payer_replay.body is None
            or payer_replay.body.get("request_id") != payer_request_id
            or payer_replay.body.get("replayed") is not True
        ):
            raise SmokeFailure("Payer support retry was not replay-safe")
        payer_conflict = request_json(
            base_url,
            "POST",
            "/api/v1/support-requests",
            token=payer_access,
            payload={
                **payer_support_payload,
                "subject": "Changed synthetic payer workspace support",
            },
            additional_headers={"Idempotency-Key": payer_support_key},
            expected_status=409,
        )
        if (
            payer_conflict.body is None
            or payer_conflict.body.get("error", {}).get("code") != "conflict"
        ):
            raise SmokeFailure("Payer support changed-content replay was not rejected")
        payer_list = request_json(
            base_url,
            "GET",
            "/api/v1/support-requests",
            token=payer_access,
        )
        assert payer_list.body is not None
        if payer_reference not in {
            item.get("reference") for item in payer_list.body.get("items", [])
        }:
            raise SmokeFailure("Payer support receipt was absent from own history")
        payer_detail = request_json(
            base_url,
            "GET",
            f"/api/v1/support-requests/{payer_request_id}",
            token=payer_access,
        )
        if (
            payer_detail.body is None
            or payer_detail.body.get("reference") != payer_reference
            or payer_detail.body.get("status") != "queued"
        ):
            raise SmokeFailure("Payer support detail did not match its receipt")
        for role_label, role_token in (
            ("patient", patient_access),
            ("doctor", doctor_access),
        ):
            denied = request_json(
                base_url,
                "GET",
                f"/api/v1/support-requests/{payer_request_id}",
                token=role_token,
                expected_status=404,
            )
            if (
                denied.body is None
                or denied.body.get("error", {}).get("code") != "not_found"
            ):
                raise SmokeFailure(
                    f"{role_label} cross-role payer support read was not neutral"
                )
        payer_analytics = request_json(
            base_url,
            "POST",
            "/api/v1/product-events",
            token=payer_access,
            payload={
                "event_name": "journey_completed",
                "deduplication_key": f"payer-analytics-{payer_lifecycle_id}",
                "dimensions": {
                    "journey_code": "account_support",
                    "surface_code": "account",
                    "outcome": "completed",
                    "latency_bucket": "not_measured",
                    "locale": "en",
                    "platform": "web",
                    "layout": "desktop",
                },
            },
            expected_status=202,
        )
        if (
            payer_analytics.body is None
            or payer_analytics.body.get("accepted") is not True
            or payer_analytics.body.get("persisted") is not True
        ):
            raise SmokeFailure("Payer content-free analytics event was not persisted")
        payer_withdrawn = request_json(
            base_url,
            "POST",
            f"/api/v1/support-requests/{payer_request_id}/withdraw",
            token=payer_access,
            payload={"expected_version": 1},
            additional_headers={
                "Idempotency-Key": f"payer-withdraw-{payer_lifecycle_id}"
            },
        )
        if (
            payer_withdrawn.body is None
            or payer_withdrawn.body.get("status") != "cancelled"
        ):
            raise SmokeFailure("Payer support cleanup withdrawal did not persist")
        ok("payer credentialed Phase 5 support/isolation/analytics lifecycle")

    patient_care = request_json(
        base_url,
        "GET",
        "/api/v1/patient/me/care",
        token=patient_access,
    )
    assert patient_care.body is not None
    patient_profile = patient_care.body["patient"]
    profile_write = request_json(
        base_url,
        "PATCH",
        "/api/v1/patient/me/profile",
        token=patient_access,
        payload={"display_name": patient_profile["display_name"]},
    )
    if (
        profile_write.body is None
        or profile_write.body.get("display_name") != patient_profile["display_name"]
    ):
        raise SmokeFailure("Patient profile no-op write did not persist correctly")
    duplicate_email = request_json(
        base_url,
        "PATCH",
        "/api/v1/auth/account/email",
        token=patient_access,
        payload={"email": doctor_email},
        expected_status=409,
    )
    if (
        duplicate_email.body is None
        or duplicate_email.body.get("error", {}).get("code") != "email_already_in_use"
    ):
        raise SmokeFailure("Duplicate account email did not return the safe conflict response")
    ok("patient profile database write and duplicate-email conflict")

    resources = request_json(
        base_url,
        "GET",
        f"/api/v1/doctor/resources?{urlencode({'query': 'usually has no symptoms'})}",
        token=doctor_access,
    )
    assert resources.body is not None
    resource_ids = {item["source_id"] for item in resources.body.get("items", [])}
    if "KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE" not in resource_ids:
        raise SmokeFailure("Doctor resource search did not match the approved English summary")
    ok("doctor resource approved-summary search")

    rotated = request_json(
        base_url,
        "POST",
        "/api/v1/auth/refresh",
        payload={"refresh_token": patient_tokens["refresh_token"]},
    )
    assert rotated.body is not None
    if rotated.body["refresh_token"] == patient_tokens["refresh_token"]:
        raise SmokeFailure("Refresh did not rotate the refresh token")
    logout = request_json(
        base_url,
        "POST",
        "/api/v1/auth/logout",
        token=rotated.body["access_token"],
        payload={"refresh_token": rotated.body["refresh_token"]},
        expected_status=204,
    )
    if logout.body is not None:
        raise SmokeFailure("Logout returned an unexpected body")
    request_json(
        base_url,
        "GET",
        "/api/v1/me",
        token=rotated.body["access_token"],
        expected_status=401,
    )
    ok("refresh rotation and logout revocation")

    patients = request_json(
        base_url,
        "GET",
        f"/api/v1/patients?{urlencode({'q': 'Riley'})}",
        token=doctor_access,
    )
    assert patients.body is not None
    items = patients.body.get("items", [])
    if len(items) != 1:
        raise SmokeFailure(f"Expected one assigned Riley patient, got {len(items)}")
    assigned_patient_id = items[0]["patient_id"]
    ok("doctor assigned-patient search")

    if unrelated_password:
        unrelated_tokens = login(base_url, unrelated_email, unrelated_password)
        unrelated_care = request_json(
            base_url,
            "GET",
            "/api/v1/patient/me/care",
            token=unrelated_tokens["access_token"],
        )
        assert unrelated_care.body is not None
        unrelated_patient_id = unrelated_care.body["patient"]["patient_id"]
    if not unrelated_patient_id:
        raise SmokeFailure(
            "Need DR_AI_STAGING_UNRELATED_PATIENT_PASSWORD or "
            "DR_AI_STAGING_UNRELATED_PATIENT_ID for true cross-patient denial"
        )
    cross_patient = request_json(
        base_url,
        "GET",
        f"/api/v1/patients/{unrelated_patient_id}/care",
        token=doctor_access,
        expected_status=404,
    )
    if cross_patient.body is None or cross_patient.body.get("error", {}).get("code") != "not_found":
        raise SmokeFailure("Cross-patient probe did not return neutral not_found")
    ok("neutral cross-patient denial")

    request_json(
        base_url,
        "POST",
        f"/api/v1/patients/{assigned_patient_id}/assets/presign",
        token=doctor_access,
        payload={
            "filename": "synthetic-ct-demo.png",
            "content_type": "image/png",
            "size_bytes": 2048,
        },
    )
    ok("demo upload presign metadata")

    smoke_id = f"staging-smoke-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    assessment = request_json(
        base_url,
        "POST",
        f"/api/v1/patients/{assigned_patient_id}/assessments",
        token=doctor_access,
        payload={
            "mode": "simulated",
            "fixture_id": "synthetic_lung_case_001",
            "idempotency_key": smoke_id,
        },
    )
    if (
        assessment.body is None
        or assessment.body.get("safety_label") != "Research simulation - not for diagnosis."
    ):
        raise SmokeFailure("Assessment response did not include the simulation safety label")
    ok("simulated assessment")

    plan_payload = {
        "title": f"Synthetic Staging Smoke Plan {smoke_id}",
        "instructions": "Demo-only recovery plan for staging smoke verification.",
        "tasks": [
            {
                "category": "medication",
                "title": "Demo medication reminder",
                "detail": "Review the synthetic medication fixture only.",
                "due_label": "Today",
                "notification_time": "09:00",
            },
            {
                "category": "exercise",
                "title": "Light demo mobility",
                "detail": "Short synthetic mobility task.",
                "due_label": "Today",
            },
            {
                "category": "diet",
                "title": "Demo hydration check",
                "detail": "Synthetic hydration reminder.",
                "due_label": "Today",
            },
            {
                "category": "follow_up",
                "title": "Synthetic follow-up preparation",
                "detail": "Prepare demo questions.",
                "due_label": "Today",
            },
        ],
    }
    plan = request_json(
        base_url,
        "POST",
        f"/api/v1/patients/{assigned_patient_id}/recovery-plans",
        token=doctor_access,
        payload=plan_payload,
    )
    assert plan.body is not None
    activated = request_json(
        base_url,
        "POST",
        f"/api/v1/patients/{assigned_patient_id}/recovery-plans/{plan.body['plan_id']}/activate",
        token=doctor_access,
    )
    if activated.body is None or activated.body.get("status") != "active":
        raise SmokeFailure("Recovery plan activation did not return active status")
    ok("doctor recovery plan save and activation")

    patient_tokens = login(base_url, patient_email, patient_password)
    patient_access = patient_tokens["access_token"]
    today = request_json(base_url, "GET", "/api/v1/patient/me/today", token=patient_access)
    assert today.body is not None
    data = today.body.get("data", {})
    tasks = data.get("today_tasks", [])
    if not tasks:
        raise SmokeFailure("Patient Today returned no tasks after plan activation")
    completion = request_json(
        base_url,
        "POST",
        f"/api/v1/patient/me/tasks/{tasks[0]['task_id']}/completion",
        token=patient_access,
        payload={"completed": True},
    )
    if completion.body is None or not completion.body.get("task", {}).get("is_completed"):
        raise SmokeFailure("Task completion did not return completed task")
    ok("patient Today readback and task completion")

    chat = request_json(
        base_url,
        "POST",
        "/api/v1/chat/threads/patient-education/messages",
        token=patient_access,
        payload={"message": "What general questions should I prepare for my clinician?"},
    )
    if chat.body is None or chat.body.get("response_mode") != "stream_ready":
        raise SmokeFailure("Ask Dr. AI did not return stream-ready educational response")
    if chat.body.get("is_red_flag"):
        raise SmokeFailure("Normal educational chat was incorrectly classified as red flag")
    ok("patient Ask Dr. AI educational response")

    consultation = request_json(
        base_url,
        "POST",
        "/api/v1/consultations",
        token=doctor_access,
        payload={
            "patient_id": assigned_patient_id,
            "specialty": "Pulmonology demo review",
            "question_summary": "Synthetic review of recovery-plan education questions.",
            "priority": "routine",
        },
    )
    if consultation.body is None or consultation.body.get("status") != "requested":
        raise SmokeFailure("Consultation request did not return requested status")
    patient_status = request_json(base_url, "GET", "/api/v1/consultations", token=patient_access)
    assert patient_status.body is not None
    consultation_ids = {item["consultation_id"] for item in patient_status.body.get("items", [])}
    if consultation.body["consultation_id"] not in consultation_ids:
        raise SmokeFailure("Patient consultation status did not include the new request")
    ok("doctor consultation request and patient status readback")

    patient_contacts = request_json(
        base_url,
        "GET",
        "/api/v1/patient/me/contacts",
        token=patient_access,
    )
    assert patient_contacts.body is not None
    contact_items = patient_contacts.body.get("items", [])
    if not contact_items:
        raise SmokeFailure("Connected patient did not receive a doctor contact")
    doctor_id = contact_items[0]["doctor_id"]
    private_message = f"Synthetic staging message {smoke_id}"
    sent_message = request_json(
        base_url,
        "POST",
        f"/api/v1/private-chats/{doctor_id}/messages",
        token=patient_access,
        payload={"message": private_message},
    )
    assert sent_message.body is not None
    message_id = sent_message.body.get("message_id")
    if sent_message.body.get("sender_role") != "patient" or not message_id:
        raise SmokeFailure("Patient private message did not return its identifier and role")
    doctor_messages = request_json(
        base_url,
        "GET",
        f"/api/v1/private-chats/{assigned_patient_id}/messages",
        token=doctor_access,
    )
    assert doctor_messages.body is not None
    delivered_ids = {item["message_id"] for item in doctor_messages.body.get("items", [])}
    if message_id not in delivered_ids:
        raise SmokeFailure("Doctor did not receive the patient's private message")
    request_json(
        base_url,
        "POST",
        f"/api/v1/private-chats/{unrelated_patient_id}/messages",
        token=doctor_access,
        payload={"message": "This synthetic message must not be delivered."},
        expected_status=404,
    )
    ok("connected private messaging and unconnected-patient denial")

    privacy_status, privacy_body = request_text(base_url, "GET", "/privacy")
    has_flutter_shell = "flutter_bootstrap.js" in privacy_body
    has_app_title = "<title>Dr. AI</title>" in privacy_body
    if privacy_status != 200 or not has_flutter_shell or not has_app_title:
        raise SmokeFailure("Privacy deep link did not return the Flutter web shell")
    ok("privacy web deep link")

    print("STAGING SMOKE PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from None
