"""Provider-neutral JSON transport primitives for bounded server-side AI purposes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class ProviderTransportError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class JsonProviderResponse:
    payload: dict[str, object]


class OpenAICompatibleJsonTransport:
    """Send one OpenAI-compatible JSON request without purpose-specific semantics."""

    def request(
        self,
        *,
        endpoint: str,
        api_key: str,
        request_body: dict[str, object],
        timeout_seconds: float,
    ) -> JsonProviderResponse:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - configured HTTPS provider endpoint.
                request,
                timeout=timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise ProviderTransportError("timeout") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in {402, 429}:
                raise ProviderTransportError("quota") from exc
            raise ProviderTransportError("provider_unavailable") from exc
        except json.JSONDecodeError as exc:
            raise ProviderTransportError("malformed_envelope") from exc
        except OSError as exc:
            raise ProviderTransportError("provider_unavailable") from exc
        if not isinstance(payload, dict):
            raise ProviderTransportError("malformed_envelope")
        return JsonProviderResponse(payload=payload)
