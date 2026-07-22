import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.knowledge_review import (
    SOURCE_REVIEW_ROLES,
    TRANSLATION_REVIEW_ROLES,
    SupplementaryReviewManifest,
    load_supplementary_review_manifest,
    validate_supplementary_review_manifest,
)
from app.knowledge_translation import load_translation_corpus
from app.open_content_ingestion import load_open_content_catalog

REVIEW_PATH = Path("knowledge_base/reviews/open_symptom_presentations.v1.json")


def _validate() -> tuple[SupplementaryReviewManifest, dict[str, object]]:
    manifest = load_supplementary_review_manifest(REVIEW_PATH)
    catalog_path = Path(manifest.source_catalog.locator)
    translation_path = Path(manifest.translation_artifact.locator)
    result = validate_supplementary_review_manifest(
        manifest,
        catalog=load_open_content_catalog(catalog_path),
        catalog_path=catalog_path,
        translation=load_translation_corpus(translation_path),
        translation_path=translation_path,
    )
    return manifest, result


def test_supplementary_review_manifest_is_bound_separate_and_pending() -> None:
    manifest, result = _validate()

    assert manifest.expected_source_count == 6
    assert manifest.status == "review_pending"
    assert "RCQ-" not in REVIEW_PATH.read_text(encoding="utf-8")
    assert manifest.separation_policy.model_dump() == {
        "retrieval_corpus": True,
        "evaluation_contract": False,
        "training_data": False,
        "raw_patient_queries_included": False,
        "activation_allowed_while_pending": False,
        "model_generation_may_close_review": False,
    }
    assert all(
        set(source.source_reviews) == set(SOURCE_REVIEW_ROLES) for source in manifest.sources
    )
    assert all(
        set(source.translation_reviews) == set(TRANSLATION_REVIEW_ROLES)
        for source in manifest.sources
    )
    assert all(
        decision.status == "pending"
        for source in manifest.sources
        for decision in (*source.source_reviews.values(), *source.translation_reviews.values())
    )
    assert result["structurally_valid"] is True
    assert result["human_reviews_complete"] is False
    assert result["blocking_findings_resolved"] is False
    assert result["admission_ready"] is False
    assert result["candidate_build_allowed"] is False
    assert result["activation_allowed"] is False
    assert result["clinical_approval_claimed"] is False
    assert result["structural_failures"] == []
    assert len(result["readiness_failures"]) == 66


def test_review_manifest_records_known_translation_and_centrality_blockers() -> None:
    manifest, _ = _validate()
    findings = {
        finding.finding_id
        for source in manifest.sources
        for finding in source.blocking_findings
        if finding.status == "open"
    }

    assert findings == {
        "KBF-DIZZINESS-SCOPE-LIMIT",
        "KBF-LOW-BP-DIAGNOSTIC-WORDING",
        "KBF-NHS-ADAPTATION-ATTRIBUTION",
        "KBF-NHS-MATERNITY-PATHWAY-LOCALIZATION",
        "KBF-PESTICIDE-TERM-NARROWING",
        "KBF-SKIN-SOURCE-CENTRALITY",
    }


def test_review_manifest_detects_lineage_drift() -> None:
    manifest, _ = _validate()
    manifest.translation_artifact.sha256 = "0" * 64
    catalog_path = Path(manifest.source_catalog.locator)
    translation_path = Path(manifest.translation_artifact.locator)

    result = validate_supplementary_review_manifest(
        manifest,
        catalog=load_open_content_catalog(catalog_path),
        catalog_path=catalog_path,
        translation=load_translation_corpus(translation_path),
        translation_path=translation_path,
    )

    assert result["structurally_valid"] is False
    assert "translation_artifact_checksum_mismatch" in result["structural_failures"]


def test_review_decision_cannot_claim_anonymous_approval() -> None:
    payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    payload["sources"][0]["source_reviews"]["medical"]["status"] = "approved"

    with pytest.raises(ValidationError, match="require a reviewer and review time"):
        SupplementaryReviewManifest.model_validate(payload)


def test_manifest_status_cannot_bypass_pending_reviews() -> None:
    manifest, _ = _validate()
    manifest.status = "approved_for_admission"
    catalog_path = Path(manifest.source_catalog.locator)
    translation_path = Path(manifest.translation_artifact.locator)

    result = validate_supplementary_review_manifest(
        manifest,
        catalog=load_open_content_catalog(catalog_path),
        catalog_path=catalog_path,
        translation=load_translation_corpus(translation_path),
        translation_path=translation_path,
    )

    assert result["structurally_valid"] is False
    assert result["candidate_build_allowed"] is False
    assert result["activation_allowed"] is False
    assert "manifest_claims_unearned_admission" in result["structural_failures"]
