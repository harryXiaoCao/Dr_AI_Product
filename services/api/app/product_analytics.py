import hashlib
import json
import re
from typing import Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import AppSettings, CurrentUser, DbSession
from app.errors import ApiError
from app.models import AnalyticsEvent, UserRole
from app.rbac import require_enabled_role

router = APIRouter(prefix="/api/v1", tags=["product analytics"])

AnalyticsEventName = Literal[
    "journey_started",
    "journey_completed",
    "task_completed",
    "workflow_failed",
    "workflow_retried",
    "workflow_conflict",
    "workflow_fallback",
    "workflow_replayed",
    "navigation_abandoned",
    "notification_inbox_opened",
    "notification_deep_link_opened",
    "notification_scheduled",
    "notification_suppressed",
    "notification_permission_result",
    "notification_delivery_attempted",
    "notification_provider_accepted",
    "notification_delivery_failed",
    "notification_delivery_retried",
    "notification_expired",
    "notification_dismissed",
    "notification_deep_link_completed",
    "notification_abandoned",
]
JourneyCode = Literal[
    "account_support",
    "account_feedback",
    "account_deletion",
    "account_security",
    "clinical_event_review",
    "patient_records",
    "patient_imaging",
    "patient_medications",
    "patient_recovery",
    "care_cost_review",
    "expected_care_explanation",
    "doctor_justification",
    "payer_manual_review",
    "patient_chat",
    "contacts",
    "notification_inbox",
]
OutcomeCode = Literal[
    "started",
    "completed",
    "failed",
    "abandoned",
    "retried",
    "conflict",
    "fallback",
    "replayed",
    "opened",
    "scheduled",
    "suppressed",
    "attempted",
    "accepted",
    "expired",
    "dismissed",
]
FailureCategory = Literal[
    "validation",
    "authorization",
    "not_found",
    "conflict",
    "network",
    "timeout",
    "provider_unavailable",
    "release_unavailable",
    "storage_unavailable",
    "unknown",
]
LatencyBucket = Literal[
    "lt_250ms",
    "250_999ms",
    "1_2_99s",
    "3_9_99s",
    "10_29_99s",
    "30s_plus",
    "not_measured",
]

KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,119}$")
ROLE_JOURNEY_DENY = {
    UserRole.patient: {"doctor_justification", "payer_manual_review"},
    UserRole.doctor: {"payer_manual_review"},
    UserRole.payer: {
        "patient_records",
        "patient_imaging",
        "patient_medications",
        "patient_recovery",
        "doctor_justification",
        "patient_chat",
    },
}
EVENT_OUTCOME = {
    "journey_started": "started",
    "journey_completed": "completed",
    "task_completed": "completed",
    "workflow_failed": "failed",
    "workflow_retried": "retried",
    "workflow_conflict": "conflict",
    "workflow_fallback": "fallback",
    "workflow_replayed": "replayed",
    "navigation_abandoned": "abandoned",
    "notification_inbox_opened": "opened",
    "notification_deep_link_opened": "opened",
    "notification_scheduled": "scheduled",
    "notification_suppressed": "suppressed",
    "notification_permission_result": "completed",
    "notification_delivery_attempted": "attempted",
    "notification_provider_accepted": "accepted",
    "notification_delivery_failed": "failed",
    "notification_delivery_retried": "retried",
    "notification_expired": "expired",
    "notification_dismissed": "dismissed",
    "notification_deep_link_completed": "completed",
    "notification_abandoned": "abandoned",
}
JOURNEY_SURFACE = {
    "account_support": "account",
    "account_feedback": "account",
    "account_deletion": "account",
    "account_security": "account",
    "clinical_event_review": "clinical_event",
    "patient_records": "records",
    "patient_imaging": "imaging",
    "patient_medications": "medications",
    "patient_recovery": "recovery",
    "care_cost_review": "care_cost",
    "expected_care_explanation": "expected_care",
    "doctor_justification": "payer_request",
    "payer_manual_review": "payer_request",
    "patient_chat": "chat",
    "contacts": "contacts",
    "notification_inbox": "notifications",
}


class ProductAnalyticsDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    journey_code: JourneyCode
    surface_code: Literal[
        "account",
        "clinical_event",
        "records",
        "imaging",
        "medications",
        "recovery",
        "care_cost",
        "expected_care",
        "payer_request",
        "chat",
        "contacts",
        "notifications",
    ]
    outcome: OutcomeCode
    failure_category: FailureCategory | None = None
    latency_bucket: LatencyBucket = "not_measured"
    locale: Literal["en", "zh-Hans"]
    platform: Literal["web", "ios", "android", "macos", "windows", "linux", "unknown"]
    layout: Literal["mobile", "tablet", "desktop", "unknown"]

    @model_validator(mode="after")
    def failure_category_matches_outcome(self) -> "ProductAnalyticsDimensions":
        if self.outcome == "failed" and self.failure_category is None:
            raise ValueError("failure_category is required when outcome is failed")
        if self.outcome != "failed" and self.failure_category is not None:
            raise ValueError("failure_category is allowed only when outcome is failed")
        return self


class ProductAnalyticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_name: AnalyticsEventName
    deduplication_key: str = Field(min_length=12, max_length=120)
    dimensions: ProductAnalyticsDimensions

    @model_validator(mode="after")
    def event_dimensions_are_consistent(self) -> "ProductAnalyticsRequest":
        expected_outcome = EVENT_OUTCOME[self.event_name]
        if self.dimensions.outcome != expected_outcome:
            raise ValueError(f"{self.event_name} requires outcome {expected_outcome}")
        expected_surface = JOURNEY_SURFACE[self.dimensions.journey_code]
        if self.dimensions.surface_code != expected_surface:
            raise ValueError(f"{self.dimensions.journey_code} requires surface {expected_surface}")
        if self.event_name.startswith("notification_") and (
            self.dimensions.journey_code != "notification_inbox"
        ):
            raise ValueError("notification events require the notification_inbox journey")
        return self


class ProductAnalyticsResponse(BaseModel):
    accepted: Literal[True] = True
    persisted: bool
    replayed: bool


def _checksum(body: ProductAnalyticsRequest, *, role: str, environment: str) -> str:
    payload = {
        "event_name": body.event_name,
        "dimensions": body.dimensions.model_dump(mode="json"),
        "role": role,
        "environment": environment,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.post(
    "/product-events",
    response_model=ProductAnalyticsResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_product_event(
    body: ProductAnalyticsRequest,
    user: CurrentUser,
    db: DbSession,
    settings: AppSettings,
) -> ProductAnalyticsResponse:
    require_enabled_role(user, {UserRole.patient, UserRole.doctor, UserRole.payer})
    key = body.deduplication_key.strip()
    if not KEY_PATTERN.fullmatch(key):
        raise ApiError(
            422,
            "validation_failed",
            "The product event could not be validated.",
            [
                {
                    "field": "deduplication_key",
                    "code": "invalid_idempotency_key",
                    "message": (
                        "Use 12 to 120 letters, numbers, dots, underscores, colons, or hyphens."
                    ),
                }
            ],
        )
    if body.dimensions.journey_code in ROLE_JOURNEY_DENY.get(user.role, set()):
        raise ApiError(
            422,
            "validation_failed",
            "The product event could not be validated.",
            [
                {
                    "field": "dimensions.journey_code",
                    "code": "role_journey_mismatch",
                    "message": "This journey is not available for the current role.",
                }
            ],
        )

    deduplication_digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    event_checksum = _checksum(
        body,
        role=user.role.value,
        environment=settings.environment,
    )
    try:
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": (f"product-event:{settings.environment}:{deduplication_digest}")},
        )
        existing = db.scalar(
            select(AnalyticsEvent).where(
                AnalyticsEvent.environment == settings.environment,
                AnalyticsEvent.deduplication_key == deduplication_digest,
            )
        )
        if existing is not None:
            if existing.event_checksum != event_checksum:
                raise ApiError(
                    409,
                    "conflict",
                    "The deduplication key was already used with different event content.",
                )
            db.rollback()
            return ProductAnalyticsResponse(persisted=True, replayed=True)

        dimensions = body.dimensions.model_dump(mode="json")
        db.add(
            AnalyticsEvent(
                actor_user_id=None,
                patient_id=None,
                clinic_id=None,
                event_type=body.event_name,
                resource_type=body.dimensions.journey_code,
                resource_id=None,
                role=user.role.value,
                environment=settings.environment,
                schema_version="content_free_product_v1",
                deduplication_key=deduplication_digest,
                event_checksum=event_checksum,
                outcome=body.dimensions.outcome,
                failure_category=body.dimensions.failure_category,
                latency_ms=None,
                metadata_json=dimensions,
            )
        )
        db.commit()
    except ApiError:
        raise
    except SQLAlchemyError:
        db.rollback()
        return ProductAnalyticsResponse(persisted=False, replayed=False)
    return ProductAnalyticsResponse(persisted=True, replayed=False)
