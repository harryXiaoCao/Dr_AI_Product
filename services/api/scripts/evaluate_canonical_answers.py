from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import patient_chat as patient_chat_runtime
from app.ai_chat import DeepSeekChatError
from app.answer_evaluation import (
    CanonicalAnswerObservation,
    answer_gate_failures,
    canonical_answer_subjects,
    contract_readiness_failures,
    evaluate_answer_results,
)
from app.chatbot_contracts import PatientChatRequest
from app.clinical_presentation import (
    assess_safety,
    emergency_guidance,
    resolve_bounded_user_continuity,
)
from app.config import get_settings
from app.database import engine
from app.models import (
    ChatbotEvent,
    ChatMessage,
    KbActiveIndexRelease,
    KbIndexRelease,
    KbIndexReleasePassage,
    KbPassage,
    KbSource,
    KbSourceVersion,
    User,
)
from app.seed import seed_database

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")
RUNNER_VERSION = "canonical-complete-answer-evaluator-v3-matrix-integrity"
PREMODEL_RUNNER_VERSION = "canonical-premodel-production-path-v2"
SAFE_FALLBACK_RUNNER_VERSION = "canonical-safe-fallback-production-path-v2"
PREMODEL_ROUTES = {"emergency_120", "prohibited_medication_change"}


def _checksum(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "content_sha256"}
    return hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def _structural_failures(contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if contract.get("schema_version") != "1.2.0":
        failures.append("schema_version")
    if contract.get("content_sha256") != _checksum(contract):
        failures.append("content_sha256")
    cases = contract.get("cases")
    if not isinstance(cases, list) or len(cases) != 100:
        failures.append("case_count")
        return failures
    case_ids = [case.get("case_id") for case in cases]
    if case_ids != [f"RCQ-{number:03d}" for number in range(1, 101)]:
        failures.append("case_id_sequence")
    input_ids = [
        input_id
        for case in cases
        for input_id in [
            case.get("case_id"),
            *[variant.get("variant_id") for variant in case.get("variants", [])],
        ]
    ]
    if any(not input_id for input_id in input_ids) or len(input_ids) != len(set(input_ids)):
        failures.append("input_id_uniqueness")
    policy = contract.get("complete_answer_evaluation_policy")
    if not isinstance(policy, dict):
        failures.append("complete_answer_evaluation_policy")
    elif policy.get("evaluated_separately_from") != [
        "deterministic_safety_routing",
        "retrieval_only",
        "retrieval_rescue",
    ]:
        failures.append("evaluation_separation")
    return sorted(set(failures))


def _initial_case_ids(contract: dict[str, Any], limit: int) -> list[str]:
    selected: list[str] = []
    cases = contract["cases"]
    for route in (
        "emergency_120",
        "prohibited_medication_change",
        "urgent_same_day",
        "clinician_contact",
        "routine_education",
    ):
        match = next(case for case in cases if case["expected_urgency_route"] == route)
        selected.append(match["case_id"])
        if len(selected) == limit:
            return selected
    for case in cases:
        if case["case_id"] not in selected:
            selected.append(case["case_id"])
        if len(selected) == limit:
            break
    return selected


def _release_source_ids(db: Session) -> tuple[str | None, set[str]]:
    active = db.get(KbActiveIndexRelease, "patient")
    if active is None:
        return None, set()
    release = db.get(KbIndexRelease, active.release_id)
    assert release is not None
    source_ids = set(
        db.scalars(
            select(KbSource.stable_id)
            .join(KbSourceVersion, KbSourceVersion.source_id == KbSource.id)
            .join(KbPassage, KbPassage.version_id == KbSourceVersion.id)
            .join(
                KbIndexReleasePassage,
                KbIndexReleasePassage.passage_id == KbPassage.id,
            )
            .where(KbIndexReleasePassage.release_id == active.release_id)
        ).all()
    )
    return release.stable_id, source_ids


def build_preflight(
    contract: dict[str, Any],
    *,
    case_limit: int,
    concurrency: int,
    maximum_spend_usd: float,
) -> dict[str, Any]:
    structural = _structural_failures(contract)
    readiness = contract_readiness_failures(contract)
    policy = contract.get("complete_answer_evaluation_policy", {})
    execution = policy.get("execution", {}) if isinstance(policy, dict) else {}
    if case_limit < 1 or case_limit > int(execution.get("initial_batch_case_limit", 0)):
        readiness.append("initial_batch_case_limit_exceeded")
    if concurrency != int(execution.get("maximum_concurrency", 0)):
        readiness.append("concurrency_policy")
    policy_spend_cap = float(execution.get("maximum_estimated_spend_usd", -1))
    if maximum_spend_usd <= 0 or maximum_spend_usd > policy_spend_cap:
        readiness.append("spend_cap_policy")

    release_id = None
    release_source_ids: set[str] = set()
    with Session(engine) as db:
        release_id, release_source_ids = _release_source_ids(db)
        db.rollback()
    if release_id is None:
        readiness.append("active_patient_release_missing")
    for subject in canonical_answer_subjects(contract):
        if subject["model_allowed"] is not True:
            continue
        for source_id in subject["relevant_source_ids"]:
            if source_id not in release_source_ids:
                readiness.append(f"{subject['input_id']}:relevant_source_not_in_release")
        if set(subject["relevant_source_ids"]) & set(subject["forbidden_source_ids"]):
            readiness.append(f"{subject['input_id']}:relevant_forbidden_overlap")

    settings = get_settings()
    token_caps = execution.get("cost_estimation_token_caps", {})
    estimated_microunits_per_case = (
        int(token_caps.get("answer_input_tokens_per_case", 0))
        * settings.deepseek_input_price_per_million_usd
        + int(token_caps.get("answer_output_tokens_per_case", 0))
        * settings.deepseek_output_price_per_million_usd
        + int(token_caps.get("planner_input_tokens_per_case", 0))
        * settings.deepseek_input_price_per_million_usd
        + int(token_caps.get("planner_output_tokens_per_case", 0))
        * settings.deepseek_output_price_per_million_usd
    )
    estimated_spend_usd = estimated_microunits_per_case * case_limit / 1_000_000
    if estimated_spend_usd > maximum_spend_usd:
        readiness.append("estimated_spend_exceeds_run_cap")
    if settings.deepseek_api_key is None:
        readiness.append("provider_key_missing")
    selected = _initial_case_ids(contract, max(1, case_limit)) if not structural else []
    return {
        "runner_version": RUNNER_VERSION,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": contract.get("contract_id"),
        "contract_sha256": contract.get("content_sha256"),
        "provider": "deepseek",
        "model": settings.deepseek_model,
        "active_release_id": release_id,
        "planned_case_ids": selected,
        "planned_input_ids": selected,
        "evaluation_scope": "initial_batch",
        "case_limit": case_limit,
        "maximum_concurrency": concurrency,
        "cost_estimation_token_caps": token_caps,
        "estimated_spend_usd": estimated_spend_usd,
        "authorized_spend_cap_usd": maximum_spend_usd,
        "provider_calls": 0,
        "paid_usage_usd": 0,
        "structural_failures": structural,
        "readiness_failures": sorted(set(readiness)),
        "ready_for_initial_paid_batch": not structural and not readiness,
    }


def _input_contract_index(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {subject["input_id"]: subject for subject in canonical_answer_subjects(contract)}


def _expected_input_ids(contract: dict[str, Any], scope: str) -> list[str]:
    if scope == "initial_batch":
        limit = int(
            contract["complete_answer_evaluation_policy"]["execution"]["initial_batch_case_limit"]
        )
        return _initial_case_ids(contract, limit)
    if scope == "full_contract":
        return [subject["input_id"] for subject in canonical_answer_subjects(contract)]
    raise ValueError("Complete-answer results require initial_batch or full_contract scope.")


def _production_path_subject_inputs(contract: dict[str, Any]) -> list[dict[str, Any]]:
    subjects: list[dict[str, Any]] = []
    for case in contract.get("cases", []):
        subjects.append(
            {
                "input_id": case["case_id"],
                "parent_case_id": case["case_id"],
                "input_kind": "canonical",
                "expected_route": case.get("expected_urgency_route"),
                "turns": [case["canonical_question"]],
                "retrieval_allowed": case.get("retrieval_allowed") is True,
                "model_allowed": case.get("model_allowed") is True,
                "relevant_source_ids": list(case.get("relevant_source_ids", [])),
                "forbidden_source_ids": list(case.get("forbidden_source_ids", [])),
            }
        )
        for variant in case.get("variants", []):
            turns = list(variant.get("turns") or [variant.get("text")])
            subjects.append(
                {
                    "input_id": variant["variant_id"],
                    "parent_case_id": case["case_id"],
                    "input_kind": variant["kind"],
                    "expected_route": variant.get("expected_route"),
                    "turns": turns,
                    "retrieval_allowed": variant.get("retrieval_allowed") is True,
                    "model_allowed": variant.get("model_allowed") is True,
                    "relevant_source_ids": list(variant.get("relevant_source_ids", [])),
                    "forbidden_source_ids": list(variant.get("forbidden_source_ids", [])),
                }
            )
    return subjects


def _premodel_subject_inputs(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        subject
        for subject in _production_path_subject_inputs(contract)
        if subject["expected_route"] in PREMODEL_ROUTES
    ]


def _safe_fallback_subject_inputs(contract: dict[str, Any]) -> list[dict[str, Any]]:
    subjects = [
        subject
        for subject in _production_path_subject_inputs(contract)
        if subject["expected_route"] not in PREMODEL_ROUTES
    ]
    if any(
        subject["retrieval_allowed"] is not True or subject["model_allowed"] is not True
        for subject in subjects
    ):
        raise ValueError(
            "Every post-safety fallback subject must permit governed retrieval and generation."
        )
    return subjects


@contextmanager
def _forbid_premodel_downstream_calls():
    counts = {"retrieval": 0, "planner": 0, "answer_model": 0}

    def forbidden_retrieve(*args, **kwargs):
        del args, kwargs
        counts["retrieval"] += 1
        raise RuntimeError("retrieval ran for a pre-model answer subject")

    class ForbiddenAdapter:
        def plan_retrieval_query(self, **kwargs):
            del kwargs
            counts["planner"] += 1
            raise RuntimeError("the retrieval planner ran for a pre-model answer subject")

        def complete_grounded(self, **kwargs):
            del kwargs
            counts["answer_model"] += 1
            raise RuntimeError("the answer model ran for a pre-model answer subject")

    original_retrieve = patient_chat_runtime.retrieve
    original_planner = patient_chat_runtime.deepseek_query_planner_adapter
    original_answer = patient_chat_runtime.deepseek_chat_adapter
    patient_chat_runtime.retrieve = forbidden_retrieve
    patient_chat_runtime.deepseek_query_planner_adapter = ForbiddenAdapter()
    patient_chat_runtime.deepseek_chat_adapter = ForbiddenAdapter()
    try:
        yield counts
    finally:
        patient_chat_runtime.retrieve = original_retrieve
        patient_chat_runtime.deepseek_query_planner_adapter = original_planner
        patient_chat_runtime.deepseek_chat_adapter = original_answer


@contextmanager
def _force_safe_no_provider_path():
    counts = {
        "retrieval": 0,
        "planner_adapter": 0,
        "answer_adapter": 0,
        "provider_request": 0,
    }
    original_retrieve = patient_chat_runtime.retrieve
    original_planner = patient_chat_runtime.deepseek_query_planner_adapter
    original_answer = patient_chat_runtime.deepseek_chat_adapter

    def observed_retrieve(*args, **kwargs):
        counts["retrieval"] += 1
        return original_retrieve(*args, **kwargs)

    class NoProviderAdapter:
        def plan_retrieval_query(self, **kwargs):
            del kwargs
            counts["planner_adapter"] += 1
            raise DeepSeekChatError(
                "service_unavailable",
                diagnostic_code="evaluation_provider_disabled",
            )

        def complete_grounded(self, **kwargs):
            if not kwargs.get("evidence"):
                raise RuntimeError("The answer adapter was reached without governed evidence.")
            counts["answer_adapter"] += 1
            raise DeepSeekChatError(
                "service_unavailable",
                diagnostic_code="evaluation_provider_disabled",
            )

    patient_chat_runtime.retrieve = observed_retrieve
    patient_chat_runtime.deepseek_query_planner_adapter = NoProviderAdapter()
    patient_chat_runtime.deepseek_chat_adapter = NoProviderAdapter()
    try:
        yield counts
    finally:
        patient_chat_runtime.retrieve = original_retrieve
        patient_chat_runtime.deepseek_query_planner_adapter = original_planner
        patient_chat_runtime.deepseek_chat_adapter = original_answer


def _evaluation_settings():
    settings = get_settings()
    return settings.model_copy(
        update={
            "seed_doctor_password": SecretStr(secrets.token_urlsafe(24)),
            "seed_patient_password": SecretStr(secrets.token_urlsafe(24)),
            "seed_unrelated_patient_password": SecretStr(secrets.token_urlsafe(24)),
            "deepseek_api_key": None,
            "chat_rate_limit_messages": 1000,
        }
    )


def _prepare_evaluation_context(
    db: Session,
    *,
    user: User,
    subject: dict[str, Any],
    session_id: str,
) -> None:
    turns = subject["turns"]
    if len(turns) <= 1:
        return
    setup_body = PatientChatRequest(
        message=turns[0],
        language="zh-Hans",
        session_id=session_id,
    )
    thread = patient_chat_runtime._thread_for_message(
        db,
        body=setup_body,
        user=user,
    )
    now = datetime.now(UTC)
    for setup_index, setup_turn in enumerate(turns[:-1]):
        db.add(
            ChatMessage(
                thread_id=thread.id,
                patient_id=thread.patient_id,
                actor_user_id=user.id,
                role="user",
                content=setup_turn,
                prompt_hash=hashlib.sha256(setup_turn.encode()).hexdigest(),
                prompt_char_count=len(setup_turn),
                safety_category="evaluation_context",
                metadata_json={
                    "language": "zh-Hans",
                    "evaluation_setup": True,
                },
                created_at=now + timedelta(microseconds=setup_index),
            )
        )
    db.flush()


def execute_premodel_matrix(contract: dict[str, Any]) -> dict[str, Any]:
    structural = _structural_failures(contract)
    if structural:
        raise ValueError("The canonical contract is structurally invalid.")
    settings = _evaluation_settings()
    if settings.environment == "production" or settings.chatbot_data_mode != "synthetic_only":
        raise ValueError("Pre-model evaluation is restricted to synthetic non-production mode.")

    subjects = _premodel_subject_inputs(contract)
    observations: list[CanonicalAnswerObservation] = []
    execution_errors: list[dict[str, str]] = []
    connection = engine.connect()
    transaction = connection.begin()
    run_nonce = secrets.token_hex(4)
    try:
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as db:
            existing = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
            if existing is not None and (
                existing.patient_profile is None
                or existing.patient_profile.synthetic_identifier != "SYN-PATIENT-001"
            ):
                raise ValueError(
                    "Pre-model evaluation refuses a non-synthetic demo-account collision."
                )
            if existing is None:
                seed_database(db, settings)
                db.commit()
            user = existing or db.scalar(
                select(User).where(User.email == "patient.demo@example.com")
            )
            if user is None or user.patient_profile is None:
                raise ValueError("The synthetic evaluation patient could not be created.")

            for subject_index, subject in enumerate(subjects):
                turns = subject["turns"]
                session_id = f"premodel-{run_nonce}-{subject['input_id'].lower()}"
                _prepare_evaluation_context(
                    db,
                    user=user,
                    subject=subject,
                    session_id=session_id,
                )

                request_id = f"premodel-{subject_index:03d}-final"
                try:
                    with _forbid_premodel_downstream_calls() as counts:
                        response = patient_chat_runtime.send_patient_chat_message(
                            PatientChatRequest(
                                message=turns[-1],
                                language="zh-Hans",
                                session_id=session_id,
                            ),
                            SimpleNamespace(state=SimpleNamespace(request_id=request_id)),
                            user,
                            db,
                            settings,
                        )
                except Exception as exc:  # noqa: BLE001 - record every per-case runtime failure
                    execution_errors.append(
                        {
                            "input_id": subject["input_id"],
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
                    continue

                event = db.scalar(select(ChatbotEvent).where(ChatbotEvent.request_id == request_id))
                if event is None:
                    execution_errors.append(
                        {
                            "input_id": subject["input_id"],
                            "error_type": "MissingTelemetry",
                            "error": (
                                "The patient-chat request did not persist its content-free event."
                            ),
                        }
                    )
                    continue
                previous_turns = [str(turn) for turn in turns[:-1]]
                continuity = resolve_bounded_user_continuity(turns[-1], previous_turns)
                assessment = assess_safety(continuity.analysis_message)
                joined_answer = "\n\n".join(response.answer_sections)
                guidance_present = response.urgency_route != "emergency_120" or (
                    joined_answer == emergency_guidance("zh-Hans", assessment.guidance_code)
                )
                observations.append(
                    CanonicalAnswerObservation(
                        input_id=subject["input_id"],
                        parent_case_id=subject["parent_case_id"],
                        input_kind=subject["input_kind"],
                        expected_route=subject["expected_route"],
                        observed_safety_code=response.safety_code.value,
                        observed_urgency_route=str(response.urgency_route),
                        fallback_code=(
                            response.fallback_code.value if response.fallback_code else None
                        ),
                        evidence_decision=(
                            response.evidence_decision.value if response.evidence_decision else None
                        ),
                        cited_source_ids=(),
                        relevant_source_ids=frozenset(subject["relevant_source_ids"]),
                        forbidden_source_ids=frozenset(subject["forbidden_source_ids"]),
                        retrieval_call_count=counts["retrieval"],
                        planner_call_count=counts["planner"],
                        answer_model_call_count=counts["answer_model"],
                        claim_support_passed=True,
                        uncertainty_present=bool(response.uncertainties),
                        next_action_code=response.next_action_code.value,
                        emergency_guidance_present=guidance_present,
                        latency_ms=event.latency_ms,
                        provider_input_tokens=event.provider_input_tokens,
                        provider_output_tokens=event.provider_output_tokens,
                        provider_cost_microunits=event.provider_cost_microunits,
                        provider_failure=event.provider_error_code is not None,
                    )
                )
    finally:
        if transaction.is_active:
            transaction.rollback()
        connection.close()

    metrics, details = evaluate_answer_results(observations)
    expected_ids = [subject["input_id"] for subject in subjects]
    observed_ids = [observation.input_id for observation in observations]
    failures: list[str] = []
    if observed_ids != expected_ids:
        failures.append("premodel_input_coverage")
    if execution_errors:
        failures.append("execution_errors")
    if any(not detail["machine_passed"] for detail in details):
        failures.append("premodel_machine_behavior")
    expected_route_counts = {
        route: sum(subject["expected_route"] == route for subject in subjects)
        for route in sorted(PREMODEL_ROUTES)
    }
    return {
        "runner_version": PREMODEL_RUNNER_VERSION,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "contract_status": contract["status"],
        "mode": "synthetic_rollback_only_production_path",
        "provider": "deepseek",
        "model": settings.deepseek_model,
        "expected_input_count": len(subjects),
        "observed_input_count": len(observations),
        "expected_route_counts": expected_route_counts,
        "retrieval_calls": sum(item.retrieval_call_count for item in observations),
        "planner_calls": sum(item.planner_call_count for item in observations),
        "answer_model_calls": sum(item.answer_model_call_count for item in observations),
        "provider_reported_tokens": 0,
        "paid_usage_usd": 0,
        "setup_context_seeded_without_downstream_calls": True,
        "database_changes_rolled_back": True,
        "clinical_approval_claimed": False,
        "full_complete_answer_gate_claimed": False,
        "metrics": {
            "machine_pass_rate": metrics["machine_pass_rate"],
            "emergency_recall": metrics["emergency_recall"],
            "zero_pre_emergency_call_rate": metrics["zero_pre_emergency_call_rate"],
            "medication_gate_pass_rate": metrics["medication_gate_pass_rate"],
            "route_and_action_pass_rate": metrics["route_and_action_pass_rate"],
            "latency_p95_ms": metrics["latency_p95_ms"],
            "latency_max_ms": metrics["latency_max_ms"],
        },
        "failures": failures,
        "passed": not failures,
        "execution_errors": execution_errors,
        "observations": details,
    }


def _fallback_route_action_pass(expected_route: str, observed_route: str, action: str) -> bool:
    if observed_route != expected_route:
        return False
    if expected_route == "urgent_same_day":
        return action == "seek_local_care"
    if expected_route == "clinician_contact":
        return action in {"contact_connected_doctor", "seek_local_care"}
    return action not in {"none", "call_120"}


def _p95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)]


def execute_safe_fallback_matrix(contract: dict[str, Any]) -> dict[str, Any]:
    structural = _structural_failures(contract)
    if structural:
        raise ValueError("The canonical contract is structurally invalid.")
    settings = _evaluation_settings()
    if settings.environment == "production" or settings.chatbot_data_mode != "synthetic_only":
        raise ValueError("Safe-fallback evaluation is restricted to synthetic non-production mode.")

    subjects = _safe_fallback_subject_inputs(contract)
    observations: list[dict[str, Any]] = []
    execution_errors: list[dict[str, str]] = []
    connection = engine.connect()
    transaction = connection.begin()
    run_nonce = secrets.token_hex(4)
    try:
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as db:
            existing = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
            if existing is not None and (
                existing.patient_profile is None
                or existing.patient_profile.synthetic_identifier != "SYN-PATIENT-001"
            ):
                raise ValueError(
                    "Safe-fallback evaluation refuses a non-synthetic demo-account collision."
                )
            if existing is None:
                seed_database(db, settings)
                db.commit()
            user = existing or db.scalar(
                select(User).where(User.email == "patient.demo@example.com")
            )
            if user is None or user.patient_profile is None:
                raise ValueError("The synthetic evaluation patient could not be created.")

            for subject_index, subject in enumerate(subjects):
                turns = subject["turns"]
                session_id = f"safe-fallback-{run_nonce}-{subject['input_id'].lower()}"
                _prepare_evaluation_context(
                    db,
                    user=user,
                    subject=subject,
                    session_id=session_id,
                )
                request_id = f"safe-fallback-{subject_index:03d}-final"
                try:
                    with _force_safe_no_provider_path() as counts:
                        response = patient_chat_runtime.send_patient_chat_message(
                            PatientChatRequest(
                                message=turns[-1],
                                language="zh-Hans",
                                session_id=session_id,
                            ),
                            SimpleNamespace(state=SimpleNamespace(request_id=request_id)),
                            user,
                            db,
                            settings,
                        )
                except Exception as exc:  # noqa: BLE001 - record every per-case runtime failure
                    execution_errors.append(
                        {
                            "input_id": subject["input_id"],
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
                    continue

                event = db.scalar(select(ChatbotEvent).where(ChatbotEvent.request_id == request_id))
                if event is None:
                    execution_errors.append(
                        {
                            "input_id": subject["input_id"],
                            "error_type": "MissingTelemetry",
                            "error": (
                                "The patient-chat request did not persist its content-free event."
                            ),
                        }
                    )
                    continue

                evidence_decision = (
                    response.evidence_decision.value if response.evidence_decision else None
                )
                expected_fallback = {
                    "sufficient": "provider_unavailable",
                    "no_eligible_evidence": "no_eligible_evidence",
                    "conflicting": "conflicting_evidence",
                    "stale_or_superseded_only": "stale_evidence",
                }.get(evidence_decision)
                fallback_code = response.fallback_code.value if response.fallback_code else None
                route_action_pass = _fallback_route_action_pass(
                    subject["expected_route"],
                    str(response.urgency_route),
                    response.next_action_code.value,
                )
                call_boundary_pass = (
                    counts["retrieval"] == 1
                    and counts["planner_adapter"] <= 1
                    and counts["provider_request"] == 0
                    and (
                        (evidence_decision == "sufficient" and counts["answer_adapter"] == 1)
                        or (evidence_decision != "sufficient" and counts["answer_adapter"] == 0)
                    )
                )
                fixed_fallback_pass = (
                    expected_fallback is not None
                    and fallback_code == expected_fallback
                    and response.model_version is None
                    and len(response.answer_sections) == 1
                    and not response.sources
                    and not response.context_used
                    and not response.uncertainties
                    and not response.emergency
                )
                usage_pass = (
                    event.provider_input_tokens is None
                    and event.provider_output_tokens is None
                    and event.provider_cost_microunits is None
                    and event.rescue_input_tokens is None
                    and event.rescue_output_tokens is None
                    and event.rescue_cost_microunits in {None, 0}
                )
                observations.append(
                    {
                        "input_id": subject["input_id"],
                        "parent_case_id": subject["parent_case_id"],
                        "input_kind": subject["input_kind"],
                        "expected_route": subject["expected_route"],
                        "observed_route": response.urgency_route,
                        "safety_code": response.safety_code.value,
                        "evidence_decision": evidence_decision,
                        "fallback_code": fallback_code,
                        "next_action_code": response.next_action_code.value,
                        "retrieval_calls": counts["retrieval"],
                        "planner_adapter_invocations": counts["planner_adapter"],
                        "answer_adapter_invocations": counts["answer_adapter"],
                        "provider_requests": counts["provider_request"],
                        "route_and_action_pass": route_action_pass,
                        "call_boundary_pass": call_boundary_pass,
                        "fixed_fallback_pass": fixed_fallback_pass,
                        "usage_pass": usage_pass,
                        "latency_ms": event.latency_ms,
                        "passed": (
                            route_action_pass
                            and call_boundary_pass
                            and fixed_fallback_pass
                            and usage_pass
                        ),
                    }
                )
    finally:
        if transaction.is_active:
            transaction.rollback()
        connection.close()

    expected_ids = [subject["input_id"] for subject in subjects]
    observed_ids = [observation["input_id"] for observation in observations]
    failures: list[str] = []
    if observed_ids != expected_ids:
        failures.append("safe_fallback_input_coverage")
    if execution_errors:
        failures.append("execution_errors")
    if any(not observation["passed"] for observation in observations):
        failures.append("safe_fallback_behavior")
    latencies = [observation["latency_ms"] for observation in observations]
    decision_counts = {
        decision: sum(observation["evidence_decision"] == decision for observation in observations)
        for decision in sorted(
            {
                str(observation["evidence_decision"])
                for observation in observations
                if observation["evidence_decision"] is not None
            }
        )
    }
    return {
        "runner_version": SAFE_FALLBACK_RUNNER_VERSION,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "contract_status": contract["status"],
        "mode": "synthetic_rollback_only_forced_provider_unavailable",
        "provider": "deepseek",
        "model": settings.deepseek_model,
        "expected_input_count": len(subjects),
        "observed_input_count": len(observations),
        "expected_canonical_count": sum(
            subject["input_kind"] == "canonical" for subject in subjects
        ),
        "expected_variant_count": sum(subject["input_kind"] != "canonical" for subject in subjects),
        "observed_evidence_decision_counts": decision_counts,
        "retrieval_calls": sum(observation["retrieval_calls"] for observation in observations),
        "planner_adapter_invocations": sum(
            observation["planner_adapter_invocations"] for observation in observations
        ),
        "answer_adapter_invocations": sum(
            observation["answer_adapter_invocations"] for observation in observations
        ),
        "provider_requests": sum(observation["provider_requests"] for observation in observations),
        "provider_reported_tokens": 0,
        "paid_usage_usd": 0,
        "setup_context_seeded_without_provider_calls": True,
        "database_changes_rolled_back": True,
        "clinical_approval_claimed": False,
        "retrieval_quality_gate_claimed": False,
        "complete_answer_gate_claimed": False,
        "metrics": {
            "safe_fallback_pass_rate": (
                sum(observation["passed"] for observation in observations) / len(subjects)
            ),
            "route_and_action_pass_rate": (
                sum(observation["route_and_action_pass"] for observation in observations)
                / len(subjects)
            ),
            "zero_provider_request_rate": (
                sum(observation["provider_requests"] == 0 for observation in observations)
                / len(subjects)
            ),
            "latency_p95_ms": _p95(latencies),
            "latency_max_ms": max(latencies, default=0),
        },
        "failures": failures,
        "passed": not failures,
        "execution_errors": execution_errors,
        "observations": observations,
    }


def _validate_raw_observation(raw: dict[str, Any]) -> None:
    for field in (
        "retrieval_call_count",
        "planner_call_count",
        "answer_model_call_count",
        "latency_ms",
    ):
        value = raw.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"Complete-answer {field} must be a non-negative integer.")
    for field in (
        "provider_input_tokens",
        "provider_output_tokens",
        "provider_cost_microunits",
    ):
        value = raw.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"Complete-answer {field} must be null or non-negative.")
    for field in (
        "claim_support_passed",
        "uncertainty_present",
        "emergency_guidance_present",
    ):
        if not isinstance(raw.get(field), bool):
            raise ValueError(f"Complete-answer {field} must be boolean.")
    provider_failure = raw.get("provider_failure", False)
    if not isinstance(provider_failure, bool):
        raise ValueError("Complete-answer provider_failure must be boolean.")
    cited = raw.get("cited_source_ids", [])
    if (
        not isinstance(cited, list)
        or any(not isinstance(source_id, str) or not source_id for source_id in cited)
        or len(cited) != len(set(cited))
    ):
        raise ValueError("Complete-answer cited_source_ids must be unique source IDs.")


def score_results(contract: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    if results.get("contract_id") != contract.get("contract_id"):
        raise ValueError("Result contract ID does not match the canonical contract.")
    if results.get("contract_sha256") != contract.get("content_sha256"):
        raise ValueError("Result contract checksum does not match the canonical contract.")
    if results.get("maximum_concurrency") != 1:
        raise ValueError("Complete-answer results must come from concurrency one.")
    if not isinstance(results.get("provider"), str) or not results["provider"].strip():
        raise ValueError("Complete-answer results require a visible provider.")
    if not isinstance(results.get("model"), str) or not results["model"].strip():
        raise ValueError("Complete-answer results require a visible model.")
    if (
        not isinstance(results.get("active_release_id"), str)
        or not results["active_release_id"].strip()
    ):
        raise ValueError("Complete-answer results require an active release ID.")
    scope = str(results.get("evaluation_scope", ""))
    expected_input_ids = _expected_input_ids(contract, scope)
    planned_input_ids = results.get("planned_input_ids")
    if planned_input_ids != expected_input_ids:
        raise ValueError("Planned complete-answer inputs do not match the evaluation scope.")
    index = _input_contract_index(contract)
    raw_observations = results.get("observations")
    if not isinstance(raw_observations, list) or not raw_observations:
        raise ValueError("Complete-answer results require observations.")
    if any(not isinstance(raw, dict) for raw in raw_observations):
        raise ValueError("Complete-answer observations must be objects.")
    observation_ids = [raw.get("input_id") for raw in raw_observations]
    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError("Complete-answer result IDs must be unique.")
    if set(observation_ids) != set(expected_input_ids):
        raise ValueError("Complete-answer observations do not cover every planned input.")
    observations: list[CanonicalAnswerObservation] = []
    for raw in raw_observations:
        _validate_raw_observation(raw)
        input_id = raw.get("input_id")
        if input_id not in index:
            raise ValueError(f"Unknown complete-answer input ID: {input_id}.")
        subject = index[input_id]
        observations.append(
            CanonicalAnswerObservation(
                input_id=input_id,
                parent_case_id=subject["parent_case_id"],
                input_kind=subject["input_kind"],
                expected_route=subject["expected_route"],
                observed_safety_code=raw["observed_safety_code"],
                observed_urgency_route=raw["observed_urgency_route"],
                fallback_code=raw.get("fallback_code"),
                evidence_decision=raw.get("evidence_decision"),
                cited_source_ids=tuple(raw.get("cited_source_ids", [])),
                relevant_source_ids=frozenset(subject["relevant_source_ids"]),
                forbidden_source_ids=frozenset(subject["forbidden_source_ids"]),
                retrieval_call_count=raw["retrieval_call_count"],
                planner_call_count=raw["planner_call_count"],
                answer_model_call_count=raw["answer_model_call_count"],
                claim_support_passed=raw["claim_support_passed"],
                uncertainty_present=raw["uncertainty_present"],
                next_action_code=raw["next_action_code"],
                emergency_guidance_present=raw["emergency_guidance_present"],
                latency_ms=raw["latency_ms"],
                provider_input_tokens=raw.get("provider_input_tokens"),
                provider_output_tokens=raw.get("provider_output_tokens"),
                provider_cost_microunits=raw.get("provider_cost_microunits"),
                provider_failure=raw.get("provider_failure", False),
            )
        )
    metrics, details = evaluate_answer_results(observations)
    thresholds = contract["complete_answer_evaluation_policy"]["machine_thresholds"]
    failures = answer_gate_failures(metrics, thresholds)
    batch_machine_passed = not failures
    full_contract_machine_gate_passed = scope == "full_contract" and batch_machine_passed
    return {
        "runner_version": RUNNER_VERSION,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "contract_id": contract["contract_id"],
        "contract_sha256": contract["content_sha256"],
        "provider": results.get("provider"),
        "model": results.get("model"),
        "active_release_id": results.get("active_release_id"),
        "evaluation_scope": scope,
        "planned_input_ids": expected_input_ids,
        "expected_input_count": len(expected_input_ids),
        "observed_input_count": len(observations),
        "input_coverage_rate": len(observations) / len(expected_input_ids),
        "metrics": metrics,
        "machine_failures": failures,
        "batch_machine_passed": batch_machine_passed,
        "ready_for_full_contract_run": scope == "initial_batch" and batch_machine_passed,
        "machine_gate_passed": full_contract_machine_gate_passed,
        "human_review": {
            "status": "pending",
            "required": True,
            "independent_from_ai_judge": True,
        },
        "overall_gate_passed": False,
        "observations": details,
    }


def _write_output(path: Path | None, artifact: dict[str, Any]) -> None:
    rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    if path is not None:
        if path.exists():
            raise SystemExit(f"Output already exists; refusing to overwrite {path}.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preflight or score the separate canonical complete-answer gate."
    )
    parser.add_argument(
        "command",
        choices=("validate", "preflight", "premodel", "safe-fallback", "score"),
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case-limit", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max-spend-usd", type=float, default=0.10)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.command == "validate":
        structural = _structural_failures(contract)
        artifact = {
            "runner_version": RUNNER_VERSION,
            "contract_id": contract.get("contract_id"),
            "contract_sha256": contract.get("content_sha256"),
            "structural_failures": structural,
            "readiness_failures": contract_readiness_failures(contract),
            "structurally_valid": not structural,
            "ready_for_initial_paid_batch": (
                not structural and not contract_readiness_failures(contract)
            ),
        }
        _write_output(args.output, artifact)
        return 0 if not structural else 1
    if args.command == "preflight":
        artifact = build_preflight(
            contract,
            case_limit=args.case_limit,
            concurrency=args.concurrency,
            maximum_spend_usd=args.max_spend_usd,
        )
        _write_output(args.output, artifact)
        return 0 if artifact["ready_for_initial_paid_batch"] else 1
    if args.command == "premodel":
        if args.output is None:
            raise SystemExit("--output is required for immutable pre-model evidence.")
        if args.output.exists():
            raise SystemExit(f"Output already exists; refusing to overwrite {args.output}.")
        artifact = execute_premodel_matrix(contract)
        _write_output(args.output, artifact)
        return 0 if artifact["passed"] else 1
    if args.command == "safe-fallback":
        if args.output is None:
            raise SystemExit("--output is required for immutable safe-fallback evidence.")
        if args.output.exists():
            raise SystemExit(f"Output already exists; refusing to overwrite {args.output}.")
        artifact = execute_safe_fallback_matrix(contract)
        _write_output(args.output, artifact)
        return 0 if artifact["passed"] else 1
    if args.results is None:
        raise SystemExit("--results is required for score.")
    if _structural_failures(contract):
        raise SystemExit("The canonical contract is structurally invalid; scoring refused.")
    results = json.loads(args.results.read_text(encoding="utf-8"))
    artifact = score_results(contract, results)
    _write_output(args.output, artifact)
    return 0 if artifact["overall_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
