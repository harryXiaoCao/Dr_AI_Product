"""Validate canonical case/source review provenance and fail closed on readiness.

This local validator makes no network or provider calls. A structurally valid
pending packet is expected to have ``passed=false`` until named reviewers have
decided every annotation and source, documented rights, and selected sections.
Even a passing review packet does not create eligible evidence: governed capture,
stable source IDs, an immutable release, and retrieval/answer gates remain separate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__:
    from .build_canonical_review_packet import (
        DEFAULT_ARTIFACT_ROOT,
        DEFAULT_CONTRACT,
        DEFAULT_QUEUE,
        REVIEW_DECISIONS,
        RIGHTS_CAPABILITIES,
        SOURCE_REVIEW_DECISIONS,
        build_packet,
    )
    from .build_canonical_review_packet import DEFAULT_OUTPUT as DEFAULT_PACKET
else:
    from build_canonical_review_packet import (
        DEFAULT_ARTIFACT_ROOT,
        DEFAULT_CONTRACT,
        DEFAULT_QUEUE,
        REVIEW_DECISIONS,
        RIGHTS_CAPABILITIES,
        SOURCE_REVIEW_DECISIONS,
        build_packet,
    )
    from build_canonical_review_packet import DEFAULT_OUTPUT as DEFAULT_PACKET

DEFAULT_OUTPUT_ROOT = Path("knowledge_base/release_artifacts/evaluation")
ALLOWED_DECISIONS = {"pending", "approved", "changes_required", "rejected"}
ALLOWED_DISPOSITIONS = ALLOWED_DECISIONS
REQUIRED_PATIENT_RIGHTS = {
    "commercial_use_allowed",
    "storage_allowed",
    "transformation_allowed",
    "embedding_allowed",
    "excerpt_display_allowed",
    "model_provider_transmission_allowed",
    "prior_version_retention_allowed",
}
FORBIDDEN_CONTENT_KEYS = {
    "raw_content",
    "passage_text",
    "excerpt",
    "article_body",
    "section_text",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _duplicates(values: list[Any]) -> bool:
    try:
        return len(values) != len(set(values))
    except TypeError:
        return True


def _contains_forbidden_content_key(value: Any) -> bool:
    if isinstance(value, dict):
        if FORBIDDEN_CONTENT_KEYS & value.keys():
            return True
        return any(_contains_forbidden_content_key(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_content_key(item) for item in value)
    return False


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_corrections(
    corrections: Any,
    *,
    owner_id: str,
    failures: list[str],
) -> None:
    if not isinstance(corrections, list):
        failures.append(f"invalid_corrections:{owner_id}")
        return
    for index, correction in enumerate(corrections):
        if not isinstance(correction, dict) or set(correction) != {
            "field",
            "proposed_value",
            "rationale",
        }:
            failures.append(f"invalid_correction:{owner_id}:{index}")
            continue
        if not isinstance(correction["field"], str) or not correction["field"].strip():
            failures.append(f"invalid_correction_field:{owner_id}:{index}")
        if not isinstance(correction["rationale"], str) or not correction["rationale"].strip():
            failures.append(f"invalid_correction_rationale:{owner_id}:{index}")


def validate_review_packet(
    contract: dict[str, Any],
    queue: dict[str, Any],
    coverage: dict[str, Any],
    packet: dict[str, Any],
    *,
    contract_file_sha256: str,
    queue_file_sha256: str,
    coverage_file_sha256: str,
) -> dict[str, Any]:
    structural_failures: list[str] = []
    readiness_failures: list[str] = []
    generated_on = packet.get("generated_on")
    if not isinstance(generated_on, str):
        generated_on = "invalid"
        structural_failures.append("invalid_generated_on")
    expected = build_packet(
        contract,
        queue,
        coverage,
        contract_file_sha256=contract_file_sha256,
        queue_file_sha256=queue_file_sha256,
        coverage_file_sha256=coverage_file_sha256,
        generated_on=generated_on,
    )

    if packet.get("packet_id") != expected["packet_id"]:
        structural_failures.append("packet_id_mismatch")
    if packet.get("schema_version") != "1.0.0":
        structural_failures.append("unsupported_packet_schema")
    if packet.get("status") not in {"pending_named_review", "review_complete"}:
        structural_failures.append("invalid_packet_status")
    for field in (
        "contract_id",
        "contract_content_sha256",
        "contract_file_sha256",
        "source_queue_id",
        "source_queue_file_sha256",
        "coverage_artifact",
        "coverage_artifact_sha256",
        "separation_policy",
        "review_instructions",
    ):
        if packet.get(field) != expected[field]:
            structural_failures.append(f"packet_binding_mismatch:{field}")
    if _contains_forbidden_content_key(packet):
        structural_failures.append("embedded_source_content_forbidden")

    reviewers = packet.get("reviewers")
    expected_reviewers = expected["reviewers"]
    if not isinstance(reviewers, dict) or set(reviewers) != set(expected_reviewers):
        structural_failures.append("reviewer_roles_mismatch")
        reviewers = {}
    for role, template in expected_reviewers.items():
        review = reviewers.get(role)
        if not isinstance(review, dict) or set(review) != set(template):
            structural_failures.append(f"invalid_reviewer_record:{role}")
            continue
        if review.get("role") != role or review.get("decision") not in ALLOWED_DECISIONS:
            structural_failures.append(f"invalid_reviewer_decision:{role}")
        if not isinstance(review.get("findings"), list):
            structural_failures.append(f"invalid_reviewer_findings:{role}")
        if review.get("decision") != "approved":
            readiness_failures.append(f"reviewer_not_approved:{role}")
        else:
            for field in ("reviewer_id", "reviewer_role_or_qualification"):
                if not isinstance(review.get(field), str) or not review[field].strip():
                    readiness_failures.append(f"reviewer_provenance_missing:{role}:{field}")
            if review.get("qualification_verified") is not True:
                readiness_failures.append(f"reviewer_qualification_not_verified:{role}")
            if not _valid_timestamp(review.get("reviewed_at")):
                readiness_failures.append(f"reviewed_at_missing:{role}")

    expected_subjects = {item["subject_id"]: item for item in expected["subject_reviews"]}
    subjects = packet.get("subject_reviews")
    if not isinstance(subjects, list):
        structural_failures.append("subject_reviews_not_list")
        subjects = []
    subject_ids = [item.get("subject_id") for item in subjects if isinstance(item, dict)]
    if (
        len(subjects) != len(expected_subjects)
        or _duplicates(subject_ids)
        or set(subject_ids) != set(expected_subjects)
    ):
        structural_failures.append("subject_review_set_mismatch")

    subject_by_id = {
        item["subject_id"]: item
        for item in subjects
        if isinstance(item, dict) and isinstance(item.get("subject_id"), str)
    }
    immutable_subject_fields = (
        "subject_type",
        "parent_case_id",
        "prompt",
        "turns",
        "domain",
        "annotation",
        "annotation_sha256",
        "retrieval_candidate_source_ids",
        "research_lead_candidate_ids",
    )
    for subject_id, expected_subject in expected_subjects.items():
        subject = subject_by_id.get(subject_id)
        if subject is None:
            continue
        for field in immutable_subject_fields:
            if subject.get(field) != expected_subject[field]:
                structural_failures.append(f"subject_binding_mismatch:{subject_id}:{field}")
        decisions = subject.get("review_decisions")
        if not isinstance(decisions, dict) or set(decisions) != set(REVIEW_DECISIONS):
            structural_failures.append(f"subject_decision_set_mismatch:{subject_id}")
            decisions = {}
        for decision_name in REVIEW_DECISIONS:
            decision = decisions.get(decision_name)
            if (
                decision_name == "scene_safety"
                and expected_subject["annotation"]["expected_urgency_route"] != "emergency_120"
            ):
                if decision != "not_applicable":
                    structural_failures.append(f"scene_safety_must_be_not_applicable:{subject_id}")
                continue
            if decision not in ALLOWED_DECISIONS:
                structural_failures.append(f"invalid_subject_decision:{subject_id}:{decision_name}")
            if decision != "approved":
                readiness_failures.append(f"subject_not_approved:{subject_id}:{decision_name}")

        retrieval_candidates = set(expected_subject["retrieval_candidate_source_ids"])
        lead_candidates = set(expected_subject["research_lead_candidate_ids"])
        approved_sources = subject.get("approved_relevant_source_ids")
        forbidden_sources = subject.get("forbidden_source_ids")
        approved_leads = subject.get("approved_research_lead_candidate_ids")
        rejected_leads = subject.get("rejected_research_lead_candidate_ids")
        for field, values in (
            ("approved_relevant_source_ids", approved_sources),
            ("forbidden_source_ids", forbidden_sources),
            ("approved_research_lead_candidate_ids", approved_leads),
            ("rejected_research_lead_candidate_ids", rejected_leads),
        ):
            if (
                not isinstance(values, list)
                or _duplicates(values)
                or not all(isinstance(value, str) for value in values)
            ):
                structural_failures.append(f"invalid_subject_source_ids:{subject_id}:{field}")
        approved_source_set = set(approved_sources or [])
        forbidden_source_set = set(forbidden_sources or [])
        approved_lead_set = set(approved_leads or [])
        rejected_lead_set = set(rejected_leads or [])
        if not approved_source_set <= retrieval_candidates:
            structural_failures.append(f"unretrieved_approved_source:{subject_id}")
        if approved_source_set & forbidden_source_set:
            structural_failures.append(f"source_both_relevant_and_forbidden:{subject_id}")
        if not all(value.startswith("KBS-") for value in forbidden_source_set):
            structural_failures.append(f"invalid_forbidden_source_id:{subject_id}")
        if not approved_lead_set <= lead_candidates or not rejected_lead_set <= lead_candidates:
            structural_failures.append(f"unknown_research_lead_decision:{subject_id}")
        if approved_lead_set & rejected_lead_set:
            structural_failures.append(f"research_lead_both_approved_and_rejected:{subject_id}")
        if expected_subject["annotation"]["retrieval_allowed"]:
            if retrieval_candidates and not approved_source_set:
                readiness_failures.append(f"relevant_source_not_selected:{subject_id}")
            if not retrieval_candidates and lead_candidates and not approved_lead_set:
                readiness_failures.append(f"research_lead_not_selected:{subject_id}")
            if not retrieval_candidates and not lead_candidates:
                readiness_failures.append(f"no_reviewable_evidence_candidate:{subject_id}")
        _validate_corrections(
            subject.get("corrections"),
            owner_id=subject_id,
            failures=structural_failures,
        )
        if subject.get("corrections"):
            readiness_failures.append(f"contract_correction_requires_regeneration:{subject_id}")

    expected_sources = {item["candidate_id"]: item for item in expected["source_reviews"]}
    sources = packet.get("source_reviews")
    if not isinstance(sources, list):
        structural_failures.append("source_reviews_not_list")
        sources = []
    source_ids = [item.get("candidate_id") for item in sources if isinstance(item, dict)]
    if (
        len(sources) != len(expected_sources)
        or _duplicates(source_ids)
        or set(source_ids) != set(expected_sources)
    ):
        structural_failures.append("source_review_set_mismatch")
    source_by_id = {
        item["candidate_id"]: item
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    for candidate_id, expected_source in expected_sources.items():
        source = source_by_id.get(candidate_id)
        if source is None:
            continue
        for field in ("candidate_snapshot", "candidate_sha256"):
            if source.get(field) != expected_source[field]:
                structural_failures.append(f"source_binding_mismatch:{candidate_id}:{field}")
        disposition = source.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            structural_failures.append(f"invalid_source_disposition:{candidate_id}")
        decisions = source.get("review_decisions")
        if not isinstance(decisions, dict) or set(decisions) != set(SOURCE_REVIEW_DECISIONS):
            structural_failures.append(f"source_decision_set_mismatch:{candidate_id}")
            decisions = {}
        for decision_name in SOURCE_REVIEW_DECISIONS:
            if decisions.get(decision_name) not in ALLOWED_DECISIONS:
                structural_failures.append(
                    f"invalid_source_decision:{candidate_id}:{decision_name}"
                )

        snapshot = expected_source["candidate_snapshot"]
        approved_cases = source.get("approved_case_ids")
        approved_variants = source.get("approved_variant_ids")
        if (
            not isinstance(approved_cases, list)
            or _duplicates(approved_cases)
            or not set(approved_cases) <= set(snapshot["intended_case_ids"])
        ):
            structural_failures.append(f"invalid_approved_cases:{candidate_id}")
            approved_cases = []
        if (
            not isinstance(approved_variants, list)
            or _duplicates(approved_variants)
            or not set(approved_variants) <= set(snapshot["intended_variant_ids"])
        ):
            structural_failures.append(f"invalid_approved_variants:{candidate_id}")
            approved_variants = []
        for field in ("selected_section_locators", "excluded_section_locators"):
            values = source.get(field)
            if (
                not isinstance(values, list)
                or _duplicates(values)
                or not all(isinstance(value, str) and value.strip() for value in values)
            ):
                structural_failures.append(f"invalid_section_locators:{candidate_id}:{field}")

        rights = source.get("rights")
        expected_rights = expected_source["rights"]
        if not isinstance(rights, dict) or set(rights) != set(expected_rights):
            structural_failures.append(f"invalid_rights_record:{candidate_id}")
            rights = {}
        capabilities = rights.get("capabilities")
        if not isinstance(capabilities, dict) or set(capabilities) != set(RIGHTS_CAPABILITIES):
            structural_failures.append(f"invalid_rights_capabilities:{candidate_id}")
            capabilities = {}
        elif not all(isinstance(value, bool) for value in capabilities.values()):
            structural_failures.append(f"non_boolean_rights_capability:{candidate_id}")
        if rights.get("decision") not in ALLOWED_DECISIONS:
            structural_failures.append(f"invalid_rights_decision:{candidate_id}")

        _validate_corrections(
            source.get("corrections"),
            owner_id=candidate_id,
            failures=structural_failures,
        )
        if source.get("corrections"):
            readiness_failures.append(f"source_correction_requires_regeneration:{candidate_id}")

        if disposition == "approved":
            for decision_name in SOURCE_REVIEW_DECISIONS:
                if decisions.get(decision_name) != "approved":
                    readiness_failures.append(f"source_not_approved:{candidate_id}:{decision_name}")
            if rights.get("decision") != "approved":
                readiness_failures.append(f"source_rights_not_approved:{candidate_id}")
            for field in (
                "license_or_permission_name",
                "permission_evidence_locator",
                "permission_evidence_sha256",
                "legal_reviewer_id",
                "effective_at",
            ):
                if not isinstance(rights.get(field), str) or not rights[field].strip():
                    readiness_failures.append(
                        f"source_rights_provenance_missing:{candidate_id}:{field}"
                    )
            if rights.get("effective_at") and not _valid_timestamp(rights["effective_at"]):
                readiness_failures.append(
                    f"source_rights_timestamp_invalid:{candidate_id}:effective_at"
                )
            if rights.get("expires_at") and not _valid_timestamp(rights["expires_at"]):
                readiness_failures.append(
                    f"source_rights_timestamp_invalid:{candidate_id}:expires_at"
                )
            evidence_sha = rights.get("permission_evidence_sha256")
            if isinstance(evidence_sha, str) and (
                len(evidence_sha) != 64
                or any(character not in "0123456789abcdef" for character in evidence_sha)
            ):
                readiness_failures.append(f"source_rights_evidence_checksum_invalid:{candidate_id}")
            for capability in REQUIRED_PATIENT_RIGHTS:
                if capabilities.get(capability) is not True:
                    readiness_failures.append(f"source_right_missing:{candidate_id}:{capability}")
            if not source.get("selected_section_locators"):
                readiness_failures.append(f"source_sections_not_selected:{candidate_id}")
            if not approved_cases and not approved_variants:
                readiness_failures.append(f"source_scope_not_approved:{candidate_id}")
        elif disposition == "rejected":
            if (
                not isinstance(source.get("rejection_reason_code"), str)
                or not source["rejection_reason_code"].strip()
            ):
                readiness_failures.append(f"source_rejection_reason_missing:{candidate_id}")
            if approved_cases or approved_variants:
                structural_failures.append(f"rejected_source_has_approved_scope:{candidate_id}")
        else:
            readiness_failures.append(f"source_disposition_incomplete:{candidate_id}")

    for subject_id, subject in subject_by_id.items():
        for candidate_id in subject.get("approved_research_lead_candidate_ids", []):
            source = source_by_id.get(candidate_id)
            if source is None or source.get("disposition") != "approved":
                readiness_failures.append(
                    f"approved_lead_source_not_approved:{subject_id}:{candidate_id}"
                )
                continue
            scope_field = (
                "approved_case_ids"
                if subject["subject_type"] == "canonical_case"
                else "approved_variant_ids"
            )
            if subject_id not in source.get(scope_field, []):
                structural_failures.append(
                    f"approved_lead_scope_mismatch:{subject_id}:{candidate_id}"
                )
    for candidate_id, source in source_by_id.items():
        for scope_field, subject_type in (
            ("approved_case_ids", "canonical_case"),
            ("approved_variant_ids", "variant"),
        ):
            for subject_id in source.get(scope_field, []):
                subject = subject_by_id.get(subject_id)
                if (
                    subject is None
                    or subject.get("subject_type") != subject_type
                    or candidate_id not in subject.get("approved_research_lead_candidate_ids", [])
                ):
                    structural_failures.append(
                        f"source_scope_subject_mismatch:{candidate_id}:{subject_id}"
                    )

    if packet.get("status") == "review_complete" and readiness_failures:
        structural_failures.append("status_claims_incomplete_review")
    if packet.get("status") == "pending_named_review" and not readiness_failures:
        structural_failures.append("status_not_advanced_after_complete_review")

    structural_failures = sorted(set(structural_failures))
    readiness_failures = sorted(set(readiness_failures))
    structurally_valid = not structural_failures
    ready_for_contract_regeneration = structurally_valid and not readiness_failures
    return {
        "validator_version": "canonical-review-packet-validator-v1",
        "contract_sha256": contract.get("content_sha256"),
        "source_queue_sha256": queue_file_sha256,
        "coverage_artifact": queue.get("coverage_snapshot", {}).get("coverage_artifact"),
        "subject_review_count": len(subjects),
        "canonical_review_count": sum(
            item.get("subject_type") == "canonical_case" for item in subjects
        ),
        "variant_review_count": sum(item.get("subject_type") == "variant" for item in subjects),
        "source_review_count": len(sources),
        "structural_failures": structural_failures,
        "readiness_failures": readiness_failures,
        "structurally_valid": structurally_valid,
        "ready_for_contract_regeneration": ready_for_contract_regeneration,
        "eligible_evidence_claimed": False,
        "provider_calls": 0,
        "paid_usage_usd": 0,
        "passed": ready_for_contract_regeneration,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = _load(args.contract)
    queue = _load(args.queue)
    artifact_name = queue.get("coverage_snapshot", {}).get("coverage_artifact")
    if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
        raise SystemExit("coverage artifact must be a plain filename")
    coverage_path = args.artifact_root / artifact_name
    result = validate_review_packet(
        contract,
        queue,
        _load(coverage_path),
        _load(args.packet),
        contract_file_sha256=_file_hash(args.contract),
        queue_file_sha256=_file_hash(args.queue),
        coverage_file_sha256=_file_hash(coverage_path),
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    output = args.output
    if output is not None:
        if not output.is_absolute():
            output = args.output_root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
