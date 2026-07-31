from app.imaging_ai_capability import (
    CapabilityProbeError,
    CapabilityProbeResponse,
    evaluate_imaging_capability,
)


class _Probe:
    def __init__(self, response: CapabilityProbeResponse | None = None) -> None:
        self.response = response
        self.calls = 0

    def probe(self) -> CapabilityProbeResponse:
        self.calls += 1
        if self.response is None:
            raise CapabilityProbeError("synthetic_probe_failure")
        return self.response


def test_text_only_capability_fails_closed_without_provider_call() -> None:
    probe = _Probe()
    result = evaluate_imaging_capability(
        provider="deepseek",
        model="deepseek-v4-flash",
        declared_input_modalities=("text",),
        probe=probe,
    )
    assert result.status == "unavailable_text_only"
    assert result.provider_call_attempted is False
    assert result.release_registration_allowed is False
    assert probe.calls == 0


def test_image_declaration_requires_a_bounded_probe() -> None:
    result = evaluate_imaging_capability(
        provider="deepseek",
        model="deepseek-v4-flash",
        declared_input_modalities=("text", "image"),
    )
    assert result.status == "unavailable_probe_not_run"
    assert result.release_registration_allowed is False


def test_failed_probe_cannot_register_release() -> None:
    result = evaluate_imaging_capability(
        provider="deepseek",
        model="deepseek-v4-flash",
        declared_input_modalities=("text", "image"),
        probe=_Probe(),
    )
    assert result.status == "probe_failed"
    assert result.provider_call_attempted is True
    assert result.release_registration_allowed is False


def test_only_image_and_structured_output_can_pass_capability_gate() -> None:
    result = evaluate_imaging_capability(
        provider="deepseek",
        model="deepseek-v4-flash",
        declared_input_modalities=("text", "image"),
        probe=_Probe(
            CapabilityProbeResponse(
                image_input_accepted=True,
                structured_output_received=True,
                diagnostic_code="synthetic_capability_verified",
                latency_ms=12,
            )
        ),
    )
    assert result.status == "capability_verified"
    assert result.release_registration_allowed is True
