"""Fail-closed capability contract for the separately governed imaging purpose."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Protocol

PURPOSE_CODE = "imaging_observation_draft"
PURPOSE_CONTRACT_VERSION = "imaging-observation-draft-purpose.v1"
CAPABILITY_CONTRACT_VERSION = "image-input-capability.v1"


@dataclass(frozen=True)
class CapabilityProbeResponse:
    image_input_accepted: bool
    structured_output_received: bool
    diagnostic_code: str
    latency_ms: int


class CapabilityProbe(Protocol):
    def probe(self) -> CapabilityProbeResponse: ...


class CapabilityProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImagingCapabilityEvaluation:
    purpose_code: str
    purpose_contract_version: str
    capability_contract_version: str
    provider: str
    model: str
    declared_input_modalities: tuple[str, ...]
    status: Literal[
        "unavailable_text_only",
        "unavailable_probe_not_run",
        "probe_failed",
        "capability_verified",
    ]
    provider_call_attempted: bool
    image_input_accepted: bool
    structured_output_received: bool
    release_registration_allowed: bool
    diagnostic_code: str
    latency_ms: int | None
    evaluation_checksum_sha256: str


def _checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate_imaging_capability(
    *,
    provider: str,
    model: str,
    declared_input_modalities: tuple[str, ...],
    probe: CapabilityProbe | None = None,
) -> ImagingCapabilityEvaluation:
    common: dict[str, object] = {
        "purpose_code": PURPOSE_CODE,
        "purpose_contract_version": PURPOSE_CONTRACT_VERSION,
        "capability_contract_version": CAPABILITY_CONTRACT_VERSION,
        "provider": provider,
        "model": model,
        "declared_input_modalities": list(declared_input_modalities),
    }
    if "image" not in declared_input_modalities:
        result = {
            **common,
            "status": "unavailable_text_only",
            "provider_call_attempted": False,
            "image_input_accepted": False,
            "structured_output_received": False,
            "release_registration_allowed": False,
            "diagnostic_code": "documented_text_only",
            "latency_ms": None,
        }
    elif probe is None:
        result = {
            **common,
            "status": "unavailable_probe_not_run",
            "provider_call_attempted": False,
            "image_input_accepted": False,
            "structured_output_received": False,
            "release_registration_allowed": False,
            "diagnostic_code": "bounded_capability_probe_required",
            "latency_ms": None,
        }
    else:
        try:
            response = probe.probe()
        except CapabilityProbeError:
            result = {
                **common,
                "status": "probe_failed",
                "provider_call_attempted": True,
                "image_input_accepted": False,
                "structured_output_received": False,
                "release_registration_allowed": False,
                "diagnostic_code": "capability_probe_failed",
                "latency_ms": None,
            }
        else:
            verified = response.image_input_accepted and response.structured_output_received
            result = {
                **common,
                "status": "capability_verified" if verified else "probe_failed",
                "provider_call_attempted": True,
                "image_input_accepted": response.image_input_accepted,
                "structured_output_received": response.structured_output_received,
                "release_registration_allowed": verified,
                "diagnostic_code": response.diagnostic_code,
                "latency_ms": max(0, response.latency_ms),
            }
    return ImagingCapabilityEvaluation(
        **result,
        evaluation_checksum_sha256=_checksum(result),
    )
