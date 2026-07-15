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
    expected_status: int | set[int] = 200,
) -> ApiResponse:
    data = None
    headers = {"Accept": "application/json"}
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

    health = request_json(base_url, "GET", "/health")
    if health.body != {
        "status": "ok",
        "service": "dr-ai-api",
        "environment": "staging",
        "database": "ok",
    }:
        raise SmokeFailure(f"Unexpected health payload: {health.body}")
    ok("health reports staging database ok")

    doctor_tokens = login(base_url, doctor_email, doctor_password)
    patient_tokens = login(base_url, patient_email, patient_password)
    doctor_access = doctor_tokens["access_token"]
    patient_access = patient_tokens["access_token"]
    ok("doctor and patient login")

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
        base_url, "GET", "/api/v1/me", token=rotated.body["access_token"], expected_status=401
    )
    ok("refresh rotation and logout revocation")

    patients = request_json(
        base_url, "GET", f"/api/v1/patients?{urlencode({'q': 'Riley'})}", token=doctor_access
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
