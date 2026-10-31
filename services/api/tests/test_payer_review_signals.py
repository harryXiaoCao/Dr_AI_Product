from types import SimpleNamespace

from app.care_cost import _payer_review_signals


def test_payer_review_signals_flag_evidence_exceptions_without_coverage_decision():
    artifact = SimpleNamespace(
        artifact_version=3,
        lifecycle_state="validated",
        disagreement_state="partial_disagreement",
    )
    item = SimpleNamespace(
        confidence=45,
        missing_information_json=[{"fact_id": "missing-1"}],
        contradicting_facts_json=[{"fact_id": "conflict-1"}],
        exploratory=False,
        wide_uncertainty=False,
        estimated_cost_high_minor=1000,
        requested_amount_minor=1200,
    )

    signals = _payer_review_signals(artifact, [item])

    assert signals.model_dump() == {
        "artifact_version": 3,
        "assessment_unavailable": False,
        "low_confidence": True,
        "missing_information": True,
        "conflicting_evidence": True,
        "cost_exception": True,
    }
    assert "approve" not in signals.model_dump_json()


def test_payer_review_signals_missing_assessment_is_explicit():
    artifact = SimpleNamespace(
        artifact_version=1,
        lifecycle_state="provider_unavailable",
        disagreement_state="unavailable",
    )
    signals = _payer_review_signals(artifact, [])
    assert signals.assessment_unavailable
    assert not signals.low_confidence
    assert not signals.conflicting_evidence
