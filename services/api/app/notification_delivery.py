"""Provider-neutral delivery readiness and bounded results.

No endpoint token or provider payload is accepted by this module. A future
credentialed transport must resolve an endpoint through a secrets boundary and
return only a bounded result code or a hash of a provider receipt.
"""

from dataclasses import dataclass
from typing import Literal

from app.config import Settings

DeliveryState = Literal["accepted", "delivered", "failed", "unknown"]
OperationalOutcome = Literal[
    "scheduled",
    "attempted",
    "provider_accepted",
    "sent",
    "delivered_if_supported",
    "displayed_if_observed",
    "failed",
    "expired",
    "unknown",
]


@dataclass(frozen=True)
class DeliveryReadiness:
    channel: str
    provider: str
    ready: bool
    code: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class DeliveryResult:
    state: DeliveryState
    code: str
    retryable: bool
    provider_receipt_hash: str | None = None


@dataclass(frozen=True)
class DeliveryRequest:
    """Content-free transport request.

    The idempotency key is stable for one notification/channel and may be
    forwarded to providers that support collapse or idempotency identifiers.
    It contains no user, patient, resource, endpoint, or message content.
    """

    channel: str
    idempotency_key: str
    attempt_number: int


@dataclass(frozen=True)
class DeliveryObservation:
    """Content-free event suitable for metrics or bounded operational logs."""

    channel: str
    idempotency_key: str
    attempt_number: int
    outcomes: tuple[OperationalOutcome, ...]
    result_code: str
    retryable: bool


def operational_outcomes(result: DeliveryResult) -> tuple[OperationalOutcome, ...]:
    """Map a bounded adapter result to truthful operational observations."""

    prefix: tuple[OperationalOutcome, ...] = ("attempted",)
    if result.state == "accepted":
        return (*prefix, "provider_accepted")
    if result.state == "delivered":
        return (*prefix, "sent", "delivered_if_supported")
    if result.state == "failed":
        return (*prefix, "failed")
    return (*prefix, "unknown")


def readiness(settings: Settings, channel: str) -> DeliveryReadiness:
    blockers: list[str] = []
    provider = channel
    if not settings.notification_external_delivery_enabled:
        blockers.append("external_delivery_disabled")
    if channel == "apns":
        provider = "apple_apns"
        if not settings.notification_apns_team_id:
            blockers.append("missing_team_id")
        if not settings.notification_apns_key_id:
            blockers.append("missing_key_id")
        if not settings.notification_apns_bundle_id:
            blockers.append("missing_bundle_id")
        if settings.notification_apns_private_key is None:
            blockers.append("missing_private_key")
    elif channel == "android_emas":
        provider = "alibaba_cloud_emas_mobile_push"
        if not settings.notification_emas_app_key:
            blockers.append("missing_app_key")
        if settings.notification_emas_app_secret is None:
            blockers.append("missing_app_secret")
        if not settings.notification_emas_android_package:
            blockers.append("missing_android_package")
        if not settings.notification_emas_oem_approvals_verified:
            blockers.append("oem_channel_approvals_unverified")
    elif channel == "web_push":
        provider = "web_push_vapid"
        if not settings.notification_web_push_vapid_public_key:
            blockers.append("missing_vapid_public_key")
        if settings.notification_web_push_vapid_private_key is None:
            blockers.append("missing_vapid_private_key")
        if not settings.notification_web_push_subject:
            blockers.append("missing_vapid_subject")
    else:
        blockers.append("unsupported_channel")
    if blockers:
        return DeliveryReadiness(
            channel=channel,
            provider=provider,
            ready=False,
            code=blockers[0],
            blockers=tuple(blockers),
        )
    # Credentials alone do not prove a target, signing entitlement, OEM channel
    # approval, or an installed transport client.
    return DeliveryReadiness(
        channel=channel,
        provider=provider,
        ready=False,
        code="transport_runtime_not_activated",
        blockers=("transport_runtime_not_activated",),
    )


class NotificationAdapter:
    channel: str

    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        raise NotImplementedError


class FailClosedAdapter(NotificationAdapter):
    def __init__(self, channel: str, result_code: str) -> None:
        self.channel = channel
        self._result_code = result_code

    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        return DeliveryResult(
            state="failed",
            code=self._result_code,
            retryable=False,
        )


def adapter_for(settings: Settings, channel: str) -> NotificationAdapter:
    state = readiness(settings, channel)
    return FailClosedAdapter(channel, state.code)
