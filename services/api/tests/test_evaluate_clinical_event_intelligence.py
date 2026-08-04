import importlib.util
import json
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts/evaluate_clinical_event_intelligence.py"
    spec = importlib.util.spec_from_file_location("evaluate_clinical_event_intelligence", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_free_frozen_suite_is_deterministic_and_writes_no_raw_content(tmp_path) -> None:
    module = _module()
    suite = json.loads(module.DEFAULT_SUITE.read_text(encoding="utf-8"))

    evidence = json.loads(module.DEFAULT_VERIFICATION_EVIDENCE.read_text(encoding="utf-8"))
    first = module.evaluate(
        suite, live=False, case_id=None, raw_dir=tmp_path / "raw", verification_evidence=evidence
    )
    second = module.evaluate(
        suite, live=False, case_id=None, raw_dir=tmp_path / "raw", verification_evidence=evidence
    )

    assert first["passed"] is True
    assert first["summary"] == {"passed": 5, "total": 5}
    assert first["combined_verification_passed"] is True
    assert first["unverified_adversarial_cases"] == []
    assert not (tmp_path / "raw").exists()
    assert all(row["provider_usage"] == [] for row in first["results"])
    assert all(row["explanation"]["attempted"] is False for row in first["results"])
    assert [row["snapshot_checksum_sha256"] for row in first["results"]] == [
        row["snapshot_checksum_sha256"] for row in second["results"]
    ]
    assert all(
        observation["passed"] is True
        for row in first["results"]
        for observation in row["adversarial"]
        if observation["executed"]
    )


def test_case_filter_and_unknown_case_are_explicit(tmp_path) -> None:
    module = _module()
    suite = json.loads(module.DEFAULT_SUITE.read_text(encoding="utf-8"))

    result = module.evaluate(
        suite,
        live=False,
        case_id="consultation_tier5_exploratory",
        raw_dir=tmp_path / "raw",
        verification_evidence=json.loads(
            module.DEFAULT_VERIFICATION_EVIDENCE.read_text(encoding="utf-8")
        ),
    )
    assert result["summary"] == {"passed": 1, "total": 1}
    tier5 = next(
        observation
        for observation in result["results"][0]["adversarial"]
        if observation["case_id"] == "tier5_nonzero_cost_alignment_weight"
    )
    assert tier5["passed"] is True

    try:
        module.evaluate(
            suite,
            live=False,
            case_id="missing",
            raw_dir=tmp_path / "raw",
            verification_evidence=None,
        )
    except ValueError as exc:
        assert str(exc) == "unknown_case_id"
    else:
        raise AssertionError("unknown case unexpectedly evaluated")
