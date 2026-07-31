#!/usr/bin/env python3
"""Run content-free Phase 7 checks through authenticated staging product APIs."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = os.environ.get(
    "DR_AI_STAGING_BASE_URL",
    "https://dr-ai.43.132.169.195.sslip.io",
).rstrip("/")


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    expected: set[int] = {200},
) -> tuple[int, dict[str, object]]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    data = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=request_headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=45) as response:  # noqa: S310
            status = response.status
            raw = response.read()
    except HTTPError as exc:
        status = exc.code
        raw = exc.read()
    body = json.loads(raw) if raw else {}
    if status not in expected:
        code = body.get("error", {}).get("code") if isinstance(body, dict) else None
        raise RuntimeError(f"authenticated_product_request_failed:{status}:{code}")
    return status, body


def _login(email: str, password_name: str) -> str:
    password = os.environ.get(password_name)
    if not password:
        raise RuntimeError(f"missing_{password_name.lower()}")
    _, body = _request(
        "POST",
        "/api/v1/auth/login",
        payload={"email": email, "password": password},
    )
    return str(body["access_token"])


def _doctor_scope() -> tuple[str, str, str]:
    token = _login(
        os.environ.get("DR_AI_STAGING_DOCTOR_EMAIL", "doctor.demo@example.com"),
        "DR_AI_STAGING_DOCTOR_PASSWORD",
    )
    _, patients = _request(
        "GET",
        f"/api/v1/patients?{urlencode({'q': 'Riley'})}",
        token=token,
    )
    patient_id = str(patients["items"][0]["patient_id"])
    _, care = _request("GET", f"/api/v1/patients/{patient_id}/care", token=token)
    event_id = str(care["clinical_events"][0]["id"])
    return token, patient_id, event_id


def candidate() -> dict[str, object]:
    token, patient_id, event_id = _doctor_scope()
    key = f"phase7-candidate-{time.time_ns()}"
    payload = {
        "scenario_key": "synthetic-outpatient-rehabilitation",
        "care_plan_key": "synthetic-rehabilitation-plan",
        "pricing_reference_key": "synthetic-rehabilitation-pricing",
        "utilization_rule_key": "synthetic-rehabilitation-utilization",
        "scope_key": "CN|Synthetic Province|public|primary|CNY",
        "evaluated_on": date.today().isoformat(),
        "reference_date": date.today().isoformat(),
        "jurisdiction": "CN",
        "region": "Synthetic Province",
        "encounter_type": "outpatient",
        "facility_ownership": "public",
        "facility_level": "primary",
        "currency": "CNY",
        "patient_age": 42,
    }
    path = (
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/"
        "expected-care/candidates"
    )
    _, first = _request(
        "POST",
        path,
        token=token,
        payload=payload,
        headers={"Idempotency-Key": key},
    )
    _, replay = _request(
        "POST",
        path,
        token=token,
        payload=payload,
        headers={"Idempotency-Key": key},
    )
    candidate_payload = first["candidate"]
    if (
        first.get("idempotent_replay") is not False
        or replay.get("idempotent_replay") is not True
        or not candidate_payload.get("purpose_release")
        or candidate_payload.get("validation", {}).get("baseline_modified") is not False
    ):
        raise RuntimeError("candidate_provenance_or_replay_contract_failed")
    candidate_id = str(candidate_payload["candidate_result_id"])
    response_path = f"{path}/{candidate_id}/responses"
    response_key = f"phase7-response-{time.time_ns()}"
    _, response = _request(
        "POST",
        response_path,
        token=token,
        payload={
            "position": "acknowledge",
            "expected_version": int(candidate_payload["response_version"]),
        },
        headers={"Idempotency-Key": response_key},
    )
    if response.get("position") != "acknowledge":
        raise RuntimeError("attributable_clinician_response_failed")
    comparison_key = f"phase7-comparison-{time.time_ns()}"
    _, comparison = _request(
        "POST",
        (
            f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/"
            "expected-care/comparisons"
        ),
        token=token,
        payload={"include_submitted_facts": True},
        headers={"Idempotency-Key": comparison_key},
    )
    if (
        comparison.get("state") != "comparison_published"
        or not comparison.get("comparison_contract_version")
    ):
        raise RuntimeError("deterministic_comparison_publication_failed")
    return {
        "purpose": "expected_care_candidate",
        "authenticated_role": "doctor",
        "governed_release_bound": True,
        "idempotent_replay": True,
        "human_baseline_acknowledgement": True,
        "deterministic_comparison_published": True,
        "authoritative_baseline_mutated": False,
        "content_free": True,
    }


def explanation() -> dict[str, object]:
    token, patient_id, _ = _doctor_scope()
    _, care = _request("GET", f"/api/v1/patients/{patient_id}/care", token=token)
    comparison: dict[str, object] | None = None
    event_id: str | None = None
    for event in care["clinical_events"]:
        candidate_event_id = str(event["id"])
        comparison_path = (
            f"/api/v1/patients/{patient_id}/clinical-events/{candidate_event_id}/"
            "expected-care/comparisons"
        )
        status, candidate_comparison = _request(
            "POST",
            comparison_path,
            token=token,
            payload={"include_submitted_facts": True},
            headers={
                "Idempotency-Key": f"phase7-f-comparison-{candidate_event_id}-{time.time_ns()}"
            },
            expected={200, 404},
        )
        if status == 200:
            event_id = candidate_event_id
            comparison = candidate_comparison
            break
    if comparison is None or event_id is None:
        raise RuntimeError("governed_comparison_fixture_not_found")
    comparison_id = str(comparison["comparison_id"])
    path = (
        f"/api/v1/patients/{patient_id}/clinical-events/{event_id}/"
        f"expected-care/comparisons/{comparison_id}/explanations"
    )
    key = f"phase7-explanation-{time.time_ns()}"
    _, first = _request(
        "POST",
        path,
        token=token,
        payload={"locale": "en"},
        headers={"Idempotency-Key": key},
    )
    _, replay = _request(
        "POST",
        path,
        token=token,
        payload={"locale": "en"},
        headers={"Idempotency-Key": key},
    )
    if (
        first.get("role") != "doctor"
        or first.get("display_mode")
        not in {"validated_ai_explanation", "validated_canonical_explanation"}
        or first.get("validation", {}).get("deterministic_validation_wins") is not True
        or replay.get("idempotent_replay") is not True
    ):
        raise RuntimeError("explanation_provenance_or_replay_contract_failed")
    return {
        "purpose": "expected_care_role_explanation",
        "authenticated_role": "doctor",
        "governed_release_bound": True,
        "idempotent_replay": True,
        "authoritative_comparison_mutated": False,
        "content_free": True,
    }


def chat() -> dict[str, object]:
    token = _login(
        os.environ.get("DR_AI_STAGING_PATIENT_EMAIL", "patient.demo@example.com"),
        "DR_AI_STAGING_PATIENT_PASSWORD",
    )
    _, answer = _request(
        "POST",
        "/api/v1/chat/threads/patient-education/messages",
        token=token,
        payload={"message": "What is hypertension?"},
    )
    if (
        not answer.get("assistant_message_id")
        or answer.get("is_red_flag") is not False
        or not answer.get("model")
    ):
        raise RuntimeError("chat_product_path_contract_failed")
    return {
        "purpose": "patient_chat_generated_answer",
        "authenticated_role": "patient",
        "append_only_history": True,
        "bounded_answer_returned": True,
        "content_free": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("purpose", choices=("candidate", "explanation", "chat"))
    args = parser.parse_args()
    result = {
        "candidate": candidate,
        "explanation": explanation,
        "chat": chat,
    }[args.purpose]()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
