import copy
import hashlib
import json
from pathlib import Path

from scripts.build_canonical_review_packet import build_packet
from scripts.validate_canonical_review_packet import validate_review_packet

API_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = API_ROOT / "knowledge_base/evaluation"
ARTIFACT_DIR = API_ROOT / "knowledge_base/release_artifacts/evaluation"
CONTRACT_PATH = EVALUATION_DIR / "canonical_rural_symptom_questions.v1.json"
QUEUE_PATH = EVALUATION_DIR / "canonical_rural_symptom_source_candidates.v1.json"
PACKET_PATH = EVALUATION_DIR / "canonical_rural_symptom_review_packet.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs() -> tuple[dict, dict, dict, dict, Path]:
    contract = _load(CONTRACT_PATH)
    queue = _load(QUEUE_PATH)
    coverage_path = ARTIFACT_DIR / queue["coverage_snapshot"]["coverage_artifact"]
    return contract, queue, _load(coverage_path), _load(PACKET_PATH), coverage_path


def _validate(packet: dict) -> dict:
    contract, queue, coverage, _, coverage_path = _inputs()
    return validate_review_packet(
        contract,
        queue,
        coverage,
        packet,
        contract_file_sha256=_sha256(CONTRACT_PATH),
        queue_file_sha256=_sha256(QUEUE_PATH),
        coverage_file_sha256=_sha256(coverage_path),
    )


def test_review_packet_is_deterministic_complete_and_separated() -> None:
    contract, queue, coverage, packet, coverage_path = _inputs()
    rebuilt = build_packet(
        contract,
        queue,
        coverage,
        contract_file_sha256=_sha256(CONTRACT_PATH),
        queue_file_sha256=_sha256(QUEUE_PATH),
        coverage_file_sha256=_sha256(coverage_path),
        generated_on=packet["generated_on"],
    )

    assert packet == rebuilt
    assert packet["separation_policy"] == {
        "evaluation_only": True,
        "retrieval_corpus": False,
        "training_data": False,
        "raw_content_stored": False,
        "provider_transmission_allowed": False,
        "activation_allowed": False,
    }
    assert len(packet["subject_reviews"]) == 185
    assert (
        sum(item["subject_type"] == "canonical_case" for item in packet["subject_reviews"]) == 100
    )
    assert sum(item["subject_type"] == "variant" for item in packet["subject_reviews"]) == 85
    assert len(packet["source_reviews"]) == 31
    serialized = json.dumps(packet, ensure_ascii=False)
    assert '"raw_content"' not in serialized
    assert '"passage_text"' not in serialized
    assert '"excerpt"' not in serialized
    assert all(
        source["rights"]["decision"] == "pending"
        and not any(source["rights"]["capabilities"].values())
        for source in packet["source_reviews"]
    )


def test_pending_review_packet_is_structural_but_not_approval_ready() -> None:
    _, _, _, packet, _ = _inputs()

    result = _validate(packet)

    failure_groups: dict[str, int] = {}
    for failure in result["readiness_failures"]:
        code = failure.split(":", maxsplit=1)[0]
        failure_groups[code] = failure_groups.get(code, 0) + 1
    assert result["structurally_valid"]
    assert result["structural_failures"] == []
    assert failure_groups == {
        "relevant_source_not_selected": 34,
        "research_lead_not_selected": 58,
        "reviewer_not_approved": 4,
        "source_disposition_incomplete": 31,
        "subject_not_approved": 822,
    }
    assert len(result["readiness_failures"]) == 949
    assert not result["ready_for_contract_regeneration"]
    assert not result["eligible_evidence_claimed"]
    assert result["provider_calls"] == 0
    assert result["paid_usage_usd"] == 0
    assert not result["passed"]
    assert not any(
        failure.startswith("no_reviewable_evidence_candidate:")
        for failure in result["readiness_failures"]
    )


def test_review_validator_detects_contract_source_and_content_drift() -> None:
    _, _, _, packet, _ = _inputs()
    unsafe = copy.deepcopy(packet)
    unsafe["subject_reviews"][0]["annotation"]["expected_urgency_route"] = "emergency_120"
    unsafe["source_reviews"][0]["candidate_snapshot"]["title"] = "changed"
    unsafe["source_reviews"][0]["raw_content"] = "must never enter this packet"

    result = _validate(unsafe)

    assert not result["structurally_valid"]
    assert "subject_binding_mismatch:RCQ-001:annotation" in result["structural_failures"]
    assert any(failure.endswith(":candidate_snapshot") for failure in result["structural_failures"])
    assert "embedded_source_content_forbidden" in result["structural_failures"]
    assert not result["passed"]


def test_checkbox_approval_cannot_bypass_rights_sections_or_provenance() -> None:
    _, _, _, packet, _ = _inputs()
    unsafe = copy.deepcopy(packet)
    unsafe["status"] = "review_complete"
    for reviewer in unsafe["reviewers"].values():
        reviewer["decision"] = "approved"
    for subject in unsafe["subject_reviews"]:
        for decision_name, decision in subject["review_decisions"].items():
            if decision != "not_applicable":
                subject["review_decisions"][decision_name] = "approved"
        if subject["retrieval_candidate_source_ids"]:
            subject["approved_relevant_source_ids"] = [subject["retrieval_candidate_source_ids"][0]]
    for source in unsafe["source_reviews"]:
        source["disposition"] = "approved"
        for decision_name in source["review_decisions"]:
            source["review_decisions"][decision_name] = "approved"
        source["rights"]["decision"] = "approved"

    result = _validate(unsafe)

    assert result["structurally_valid"] is False
    assert "status_claims_incomplete_review" in result["structural_failures"]
    assert "reviewer_provenance_missing:clinical:reviewer_id" in result["readiness_failures"]
    first_source = unsafe["source_reviews"][0]["candidate_id"]
    assert f"source_sections_not_selected:{first_source}" in result["readiness_failures"]
    assert (
        f"source_right_missing:{first_source}:model_provider_transmission_allowed"
        in result["readiness_failures"]
    )
    assert not result["passed"]


def test_approved_research_lead_requires_bidirectional_approved_scope() -> None:
    _, _, _, packet, _ = _inputs()
    inconsistent = copy.deepcopy(packet)
    subject = next(
        item for item in inconsistent["subject_reviews"] if item["subject_id"] == "RCQ-011"
    )
    candidate_id = subject["research_lead_candidate_ids"][0]
    subject["approved_research_lead_candidate_ids"] = [candidate_id]

    result = _validate(inconsistent)

    assert (
        f"approved_lead_source_not_approved:RCQ-011:{candidate_id}" in result["readiness_failures"]
    )
    assert not result["passed"]
