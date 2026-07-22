"""Build the separated review packet for the rural symptom-first contract.

The packet contains evaluation prompts and link metadata only. It never captures
article bodies, creates retrieval passages, changes approval state, or activates
a knowledge release. Human reviewers edit decisions in a copy of the generated
packet; the companion validator binds every decision to the exact contract and
source-candidate queue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")
DEFAULT_QUEUE = Path("knowledge_base/evaluation/canonical_rural_symptom_source_candidates.v1.json")
DEFAULT_OUTPUT = Path("knowledge_base/evaluation/canonical_rural_symptom_review_packet.v1.json")
DEFAULT_ARTIFACT_ROOT = Path("knowledge_base/release_artifacts/evaluation")

REVIEW_DECISIONS = (
    "route",
    "presentation",
    "required_behavior",
    "source_labels",
    "scene_safety",
)
SOURCE_REVIEW_DECISIONS = (
    "authority",
    "clinical_scope",
    "native_simplified_chinese",
    "patient_readability",
    "product",
)
RIGHTS_CAPABILITIES = (
    "commercial_use_allowed",
    "storage_allowed",
    "transformation_allowed",
    "translation_allowed",
    "embedding_allowed",
    "excerpt_display_allowed",
    "model_provider_transmission_allowed",
    "redistribution_allowed",
    "prior_version_retention_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reviewer_template(role: str) -> dict[str, Any]:
    return {
        "role": role,
        "decision": "pending",
        "reviewer_id": None,
        "reviewer_role_or_qualification": None,
        "qualification_verified": False,
        "reviewed_at": None,
        "findings": [],
    }


def _subject_review(
    *,
    subject_id: str,
    subject_type: str,
    parent_case_id: str | None,
    prompt: str,
    turns: list[str],
    domain: str,
    annotation: dict[str, Any],
    retrieval_candidate_source_ids: list[str],
    research_lead_candidate_ids: list[str],
) -> dict[str, Any]:
    scene_safety = (
        "pending" if annotation["expected_urgency_route"] == "emergency_120" else "not_applicable"
    )
    decisions = {name: "pending" for name in REVIEW_DECISIONS}
    decisions["scene_safety"] = scene_safety
    return {
        "subject_id": subject_id,
        "subject_type": subject_type,
        "parent_case_id": parent_case_id,
        "prompt": prompt,
        "turns": turns,
        "domain": domain,
        "annotation": annotation,
        "annotation_sha256": _canonical_hash(annotation),
        "retrieval_candidate_source_ids": retrieval_candidate_source_ids,
        "research_lead_candidate_ids": research_lead_candidate_ids,
        "review_decisions": decisions,
        "approved_relevant_source_ids": [],
        "forbidden_source_ids": [],
        "approved_research_lead_candidate_ids": [],
        "rejected_research_lead_candidate_ids": [],
        "corrections": [],
    }


def _annotation(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "expected_urgency_route": item.get("expected_urgency_route", item.get("expected_route")),
        "presentation_concepts": item["presentation_concepts"],
        "source_policy_profile": item["source_policy_profile"],
        "relevant_source_ids": item["relevant_source_ids"],
        "forbidden_source_ids": item["forbidden_source_ids"],
        "required_answer_behavior_profile": item["required_answer_behavior_profile"],
        "retrieval_allowed": item["retrieval_allowed"],
        "model_allowed": item["model_allowed"],
    }


def build_packet(
    contract: dict[str, Any],
    queue: dict[str, Any],
    coverage: dict[str, Any],
    *,
    contract_file_sha256: str,
    queue_file_sha256: str,
    coverage_file_sha256: str,
    generated_on: str,
) -> dict[str, Any]:
    case_candidates: dict[str, list[str]] = {}
    variant_candidates: dict[str, list[str]] = {}
    for source in queue["sources"]:
        candidate_id = source["candidate_id"]
        for case_id in source["intended_case_ids"]:
            case_candidates.setdefault(case_id, []).append(candidate_id)
        for variant_id in source["intended_variant_ids"]:
            variant_candidates.setdefault(variant_id, []).append(candidate_id)

    retrieval_candidates = {
        item["case_id"]: sorted(item.get("candidate_source_ids", []))
        for item in coverage["observations"]
    }
    retrieval_variant_candidates = {
        item["variant_id"]: sorted(item.get("candidate_source_ids", []))
        for item in coverage["variant_observations"]
    }

    subject_reviews: list[dict[str, Any]] = []
    for case in contract["cases"]:
        case_id = case["case_id"]
        subject_reviews.append(
            _subject_review(
                subject_id=case_id,
                subject_type="canonical_case",
                parent_case_id=None,
                prompt=case["canonical_question"],
                turns=[],
                domain=case["domain"],
                annotation=_annotation(case),
                retrieval_candidate_source_ids=retrieval_candidates.get(case_id, []),
                research_lead_candidate_ids=sorted(case_candidates.get(case_id, [])),
            )
        )
        for variant in case["variants"]:
            variant_id = variant["variant_id"]
            subject_reviews.append(
                _subject_review(
                    subject_id=variant_id,
                    subject_type="variant",
                    parent_case_id=case_id,
                    prompt=variant["text"],
                    turns=variant["turns"],
                    domain=case["domain"],
                    annotation=_annotation(variant),
                    retrieval_candidate_source_ids=retrieval_variant_candidates.get(variant_id, []),
                    research_lead_candidate_ids=sorted(variant_candidates.get(variant_id, [])),
                )
            )

    source_reviews: list[dict[str, Any]] = []
    for source in queue["sources"]:
        snapshot = {
            key: source[key]
            for key in (
                "candidate_id",
                "publisher",
                "title",
                "canonical_locator",
                "jurisdiction",
                "language",
                "content_class",
                "intended_case_ids",
                "intended_variant_ids",
                "candidate_coverage",
                "known_limitations",
            )
        }
        source_reviews.append(
            {
                "candidate_id": source["candidate_id"],
                "candidate_snapshot": snapshot,
                "candidate_sha256": _canonical_hash(snapshot),
                "disposition": "pending",
                "review_decisions": {name: "pending" for name in SOURCE_REVIEW_DECISIONS},
                "approved_case_ids": [],
                "approved_variant_ids": [],
                "selected_section_locators": [],
                "excluded_section_locators": [],
                "rights": {
                    "decision": "pending",
                    "license_or_permission_name": None,
                    "permission_evidence_locator": None,
                    "permission_evidence_sha256": None,
                    "legal_reviewer_id": None,
                    "effective_at": None,
                    "expires_at": None,
                    "capabilities": {name: False for name in RIGHTS_CAPABILITIES},
                },
                "rejection_reason_code": None,
                "corrections": [],
            }
        )

    return {
        "packet_id": "dr-ai-rural-symptom-review-packet-v1",
        "schema_version": "1.0.0",
        "status": "pending_named_review",
        "generated_on": generated_on,
        "contract_id": contract["contract_id"],
        "contract_content_sha256": contract["content_sha256"],
        "contract_file_sha256": contract_file_sha256,
        "source_queue_id": queue["queue_id"],
        "source_queue_file_sha256": queue_file_sha256,
        "coverage_artifact": queue["coverage_snapshot"]["coverage_artifact"],
        "coverage_artifact_sha256": coverage_file_sha256,
        "separation_policy": {
            "evaluation_only": True,
            "retrieval_corpus": False,
            "training_data": False,
            "raw_content_stored": False,
            "provider_transmission_allowed": False,
            "activation_allowed": False,
        },
        "review_instructions": {
            "source_ids_are_candidates_only": True,
            "candidate_approval_does_not_create_eligible_evidence": True,
            "approved_sections_require_governed_capture_and_new_source_ids": True,
            "contract_must_be_regenerated_with_approved_labels_after_review": True,
            "every_correction_requires_a_new_contract_checksum": True,
        },
        "reviewers": {
            "clinical": _reviewer_template("clinical"),
            "native_simplified_chinese": _reviewer_template("native_simplified_chinese"),
            "product": _reviewer_template("product"),
            "rights": _reviewer_template("rights"),
        },
        "subject_reviews": subject_reviews,
        "source_reviews": source_reviews,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--generated-on",
        default=datetime.now(UTC).date().isoformat(),
    )
    args = parser.parse_args()

    queue = _load(args.queue)
    artifact_name = queue["coverage_snapshot"]["coverage_artifact"]
    if Path(artifact_name).name != artifact_name:
        raise SystemExit("coverage artifact must be a plain filename")
    coverage_path = args.artifact_root / artifact_name
    packet = build_packet(
        _load(args.contract),
        queue,
        _load(coverage_path),
        contract_file_sha256=_file_hash(args.contract),
        queue_file_sha256=_file_hash(args.queue),
        coverage_file_sha256=_file_hash(coverage_path),
        generated_on=args.generated_on,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "subject_review_count": len(packet["subject_reviews"]),
                "source_review_count": len(packet["source_reviews"]),
                "status": packet["status"],
                "provider_calls": 0,
                "paid_usage_usd": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
