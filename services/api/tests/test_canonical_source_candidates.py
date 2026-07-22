import json
from pathlib import Path

from scripts.validate_canonical_source_candidates import validate_queue

EVALUATION_DIR = Path(__file__).resolve().parents[1] / "knowledge_base/evaluation"
CONTRACT_PATH = EVALUATION_DIR / "canonical_rural_symptom_questions.v1.json"
CANDIDATES_PATH = EVALUATION_DIR / "canonical_rural_symptom_source_candidates.v1.json"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "knowledge_base/release_artifacts/evaluation"


def test_source_candidate_queue_is_rights_blocked_and_separate() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    queue = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    case_ids = {case["case_id"] for case in contract["cases"]}
    variant_ids = {
        variant["variant_id"] for case in contract["cases"] for variant in case["variants"]
    }
    sources = queue["sources"]

    assert queue["schema_version"] == "1.1.0"
    assert queue["status"].endswith("review_pending")
    assert queue["separation_policy"] == {
        "evaluation_only": True,
        "retrieval_corpus": False,
        "training_data": False,
        "raw_content_stored": False,
        "provider_transmission_allowed": False,
        "activation_allowed": False,
    }
    assert len({source["candidate_id"] for source in sources}) == len(sources)
    assert len({source["canonical_locator"] for source in sources}) == len(sources)

    for source in sources:
        assert source["rights_decision"] == "link_only_pending"
        assert source["clinical_review"] == "pending"
        assert source["native_simplified_chinese_review"] == "pending"
        assert source["intended_case_ids"]
        assert set(source["intended_case_ids"]) <= case_ids
        assert set(source["intended_variant_ids"]) <= variant_ids
        assert source["canonical_locator"].startswith("https://")
        assert source["candidate_coverage"]
        assert source["known_limitations"]
        assert not {"raw_content", "passage_text", "excerpt"} & source.keys()

    assert set(queue["review_policy"]) == {
        "authority",
        "rights",
        "clinical",
        "language_and_readability",
        "retrieval",
    }


def test_source_candidate_queue_maps_every_current_coverage_gap_to_a_research_lead() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    queue = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    snapshot = queue["coverage_snapshot"]
    artifact = json.loads(
        (ARTIFACT_DIR / snapshot["coverage_artifact"]).read_text(encoding="utf-8")
    )
    no_evidence = {
        item["case_id"]
        for item in artifact["observations"]
        if item["decision"] == "no_eligible_evidence"
    }
    variant_no_evidence = {
        item["variant_id"]
        for item in artifact["variant_observations"]
        if item["decision"] == "no_eligible_evidence"
    }
    mapped = set(snapshot["canonical_candidate_mapped_case_ids"])
    unmapped = set(snapshot["canonical_candidate_unmapped_case_ids"])
    variant_mapped = set(snapshot["variant_candidate_mapped_ids"])
    variant_unmapped = set(snapshot["variant_candidate_unmapped_ids"])
    queue_case_ids = {
        case_id for source in queue["sources"] for case_id in source["intended_case_ids"]
    }
    queue_variant_ids = {
        variant_id for source in queue["sources"] for variant_id in source["intended_variant_ids"]
    }

    assert snapshot["contract_sha256"] == contract["content_sha256"]
    assert snapshot["contract_sha256"] == artifact["contract_sha256"]
    assert set(snapshot["canonical_no_evidence_case_ids"]) == no_evidence
    assert mapped | unmapped == no_evidence
    assert not mapped & unmapped
    assert mapped == no_evidence & queue_case_ids
    assert set(snapshot["variant_no_evidence_ids"]) == variant_no_evidence
    assert variant_mapped | variant_unmapped == variant_no_evidence
    assert not variant_mapped & variant_unmapped
    assert variant_mapped == variant_no_evidence & queue_variant_ids
    assert unmapped == set()
    assert variant_unmapped == set()


def test_source_candidate_validator_is_fail_closed_and_claims_no_approval() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    queue = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    artifact = json.loads(
        (ARTIFACT_DIR / queue["coverage_snapshot"]["coverage_artifact"]).read_text(encoding="utf-8")
    )

    result = validate_queue(contract, queue, artifact)

    assert result["passed"]
    assert result["failures"] == []
    assert result["candidate_source_count"] == 31
    assert result["canonical_mapped_research_lead_count"] == 33
    assert result["variant_mapped_research_lead_count"] == 25
    assert result["canonical_unmapped_ids"] == []
    assert result["variant_unmapped_ids"] == []
    assert result["provider_calls"] == 0
    assert result["paid_usage_usd"] == 0
    assert not result["eligible_evidence_claimed"]
    assert not result["clinical_approval_claimed"]

    unsafe = json.loads(json.dumps(queue))
    unsafe["sources"][0]["rights_decision"] = "approved"
    unsafe_result = validate_queue(contract, unsafe, artifact)
    assert not unsafe_result["passed"]
    assert unsafe_result["failures"] == [
        f"rights_not_pending:{unsafe['sources'][0]['candidate_id']}"
    ]
