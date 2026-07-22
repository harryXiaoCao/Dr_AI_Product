from types import SimpleNamespace

from scripts.audit_canonical_symptom_coverage import _retrieve_sequential_variant


def _retrieval_result() -> SimpleNamespace:
    return SimpleNamespace(
        decision=SimpleNamespace(value="eligible_evidence"),
        view_kinds=("literal", "clinical_presentation"),
        literal_candidate_count=1,
        latency_ms=123,
    )


def test_sequential_audit_preserves_each_literal_query_and_carries_pregnancy(
    monkeypatch,
) -> None:
    calls = []

    def fake_retrieve(db, request, *, audience, presentation):
        del db
        calls.append((request.query, audience, presentation))
        return _retrieval_result()

    monkeypatch.setattr(
        "scripts.audit_canonical_symptom_coverage.retrieve",
        fake_retrieve,
    )
    turns = ["我怀孕八个月。", "今天孩子几乎不动了，怎么办？"]

    result, error_code, trace = _retrieve_sequential_variant(SimpleNamespace(), turns)

    assert result is not None
    assert error_code is None
    assert [query for query, _, _ in calls] == turns
    assert all(audience == "patient" for _, audience, _ in calls)
    final_presentation = calls[-1][2]
    assert final_presentation.literal_query == turns[-1]
    assert "pregnant" in final_presentation.pregnancy
    assert "decreased_fetal_movement" in final_presentation.symptoms
    assert trace[-1]["continuity_reason"] == "pregnancy_dependency"
    assert trace[-1]["literal_query_preserved"] is True
    assert trace[-1]["retrieval_latency_ms"] == 123


def test_sequential_audit_bypasses_retrieval_when_follow_up_becomes_emergency(
    monkeypatch,
) -> None:
    calls = []

    def fake_retrieve(db, request, *, audience, presentation):
        del db, audience, presentation
        calls.append(request.query)
        return _retrieval_result()

    monkeypatch.setattr(
        "scripts.audit_canonical_symptom_coverage.retrieve",
        fake_retrieve,
    )
    turns = ["我刚喷完农药。", "现在头晕、恶心，还直流口水。"]

    result, error_code, trace = _retrieve_sequential_variant(SimpleNamespace(), turns)

    assert result is None
    assert error_code is None
    assert calls == [turns[0]]
    assert trace[-1]["safety_route"] == "emergency_120"
    assert trace[-1]["retrieval_attempted"] is False
    assert trace[-1]["retrieval_outcome"] == "bypassed_pre_safety"
