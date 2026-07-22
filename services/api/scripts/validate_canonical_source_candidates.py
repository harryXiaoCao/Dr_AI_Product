"""Validate the rights-blocked canonical source-intake queue.

This is a structural, no-network, no-provider check. It fails closed until
every currently observed no-evidence canonical and variant has an explicit
research lead. It does not turn a link into eligible evidence or approve any
source.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

DEFAULT_CONTRACT = Path("knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json")
DEFAULT_QUEUE = Path("knowledge_base/evaluation/canonical_rural_symptom_source_candidates.v1.json")
DEFAULT_ARTIFACT_ROOT = Path("knowledge_base/release_artifacts/evaluation")
FORBIDDEN_CONTENT_FIELDS = {"raw_content", "passage_text", "excerpt"}
PENDING_REVIEW_FIELDS = (
    "clinical_review",
    "native_simplified_chinese_review",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return payload


def validate_queue(
    contract: dict[str, Any],
    queue: dict[str, Any],
    artifact: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    cases = contract.get("cases", [])
    case_ids = {case.get("case_id") for case in cases}
    variant_ids = {
        variant.get("variant_id") for case in cases for variant in case.get("variants", [])
    }
    snapshot = queue.get("coverage_snapshot", {})
    sources = queue.get("sources", [])
    domains = set(queue.get("allowed_authority_domains", []))

    if queue.get("schema_version") != "1.1.0":
        failures.append("unsupported_queue_schema")
    if not str(queue.get("status", "")).endswith("review_pending"):
        failures.append("queue_not_review_pending")
    if snapshot.get("contract_sha256") != contract.get("content_sha256"):
        failures.append("queue_contract_checksum_mismatch")
    if artifact.get("contract_sha256") != contract.get("content_sha256"):
        failures.append("artifact_contract_checksum_mismatch")
    if not domains:
        failures.append("authority_domain_allowlist_missing")

    separation = queue.get("separation_policy", {})
    if separation != {
        "evaluation_only": True,
        "retrieval_corpus": False,
        "training_data": False,
        "raw_content_stored": False,
        "provider_transmission_allowed": False,
        "activation_allowed": False,
    }:
        failures.append("unsafe_separation_policy")

    candidate_ids: set[str] = set()
    locators: set[str] = set()
    mapped_cases: set[str] = set()
    mapped_variants: set[str] = set()
    for source in sources:
        candidate_id = source.get("candidate_id")
        locator = source.get("canonical_locator")
        if not isinstance(candidate_id, str) or not candidate_id.startswith("KBSC-"):
            failures.append("invalid_candidate_id")
        elif candidate_id in candidate_ids:
            failures.append(f"duplicate_candidate_id:{candidate_id}")
        else:
            candidate_ids.add(candidate_id)
        if not isinstance(locator, str):
            failures.append(f"missing_locator:{candidate_id}")
        else:
            parsed = urlsplit(locator)
            if (
                parsed.scheme != "https"
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port not in {None, 443}
                or parsed.fragment
                or (parsed.hostname or "").casefold() not in domains
            ):
                failures.append(f"locator_not_allowlisted:{candidate_id}")
            if locator in locators:
                failures.append(f"duplicate_locator:{candidate_id}")
            locators.add(locator)
        source_cases = set(source.get("intended_case_ids", []))
        source_variants = set(source.get("intended_variant_ids", []))
        if not source_cases or not source_cases <= case_ids:
            failures.append(f"invalid_case_mapping:{candidate_id}")
        if not source_variants <= variant_ids:
            failures.append(f"invalid_variant_mapping:{candidate_id}")
        mapped_cases.update(source_cases)
        mapped_variants.update(source_variants)
        if source.get("rights_decision") != "link_only_pending":
            failures.append(f"rights_not_pending:{candidate_id}")
        for field in PENDING_REVIEW_FIELDS:
            if source.get(field) != "pending":
                failures.append(f"{field}_not_pending:{candidate_id}")
        if source.get("patient_readability_review") not in {
            "pending",
            "not_applicable_until_transformed",
        }:
            failures.append(f"invalid_readability_status:{candidate_id}")
        if not source.get("candidate_coverage") or not source.get("known_limitations"):
            failures.append(f"review_notes_missing:{candidate_id}")
        if FORBIDDEN_CONTENT_FIELDS & source.keys():
            failures.append(f"raw_content_leak:{candidate_id}")

    no_evidence_cases = {
        item.get("case_id")
        for item in artifact.get("observations", [])
        if item.get("decision") == "no_eligible_evidence"
    }
    no_evidence_variants = {
        item.get("variant_id")
        for item in artifact.get("variant_observations", [])
        if item.get("decision") == "no_eligible_evidence"
    }
    declared_cases = set(snapshot.get("canonical_no_evidence_case_ids", []))
    declared_case_mapped = set(snapshot.get("canonical_candidate_mapped_case_ids", []))
    declared_case_unmapped = set(snapshot.get("canonical_candidate_unmapped_case_ids", []))
    declared_variants = set(snapshot.get("variant_no_evidence_ids", []))
    declared_variant_mapped = set(snapshot.get("variant_candidate_mapped_ids", []))
    declared_variant_unmapped = set(snapshot.get("variant_candidate_unmapped_ids", []))

    if declared_cases != no_evidence_cases:
        failures.append("canonical_gap_snapshot_drift")
    if declared_variants != no_evidence_variants:
        failures.append("variant_gap_snapshot_drift")
    if declared_case_mapped != no_evidence_cases & mapped_cases:
        failures.append("canonical_mapping_snapshot_drift")
    if declared_variant_mapped != no_evidence_variants & mapped_variants:
        failures.append("variant_mapping_snapshot_drift")
    if declared_case_unmapped != no_evidence_cases - mapped_cases:
        failures.append("canonical_unmapped_snapshot_drift")
    if declared_variant_unmapped != no_evidence_variants - mapped_variants:
        failures.append("variant_unmapped_snapshot_drift")
    if no_evidence_cases - mapped_cases:
        failures.append("canonical_research_leads_incomplete")
    if no_evidence_variants - mapped_variants:
        failures.append("variant_research_leads_incomplete")

    return {
        "validator_version": "canonical-source-intake-validator-v2",
        "contract_sha256": contract.get("content_sha256"),
        "coverage_artifact": snapshot.get("coverage_artifact"),
        "candidate_source_count": len(sources),
        "canonical_no_evidence_count": len(no_evidence_cases),
        "canonical_mapped_research_lead_count": len(no_evidence_cases & mapped_cases),
        "canonical_unmapped_ids": sorted(no_evidence_cases - mapped_cases),
        "variant_no_evidence_count": len(no_evidence_variants),
        "variant_mapped_research_lead_count": len(no_evidence_variants & mapped_variants),
        "variant_unmapped_ids": sorted(no_evidence_variants - mapped_variants),
        "provider_calls": 0,
        "paid_usage_usd": 0,
        "eligible_evidence_claimed": False,
        "clinical_approval_claimed": False,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = _load(args.contract)
    queue = _load(args.queue)
    artifact_name = queue.get("coverage_snapshot", {}).get("coverage_artifact")
    if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
        raise SystemExit("coverage_snapshot.coverage_artifact must be a plain filename")
    artifact = _load(args.artifact_root / artifact_name)
    result = validate_queue(contract, queue, artifact)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
