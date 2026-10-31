import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.care_cost import router as care_cost_router
from app.chatbot_release_governance import (
    chatbot_generation_readiness,
    differential_planning_readiness,
    semantic_routing_readiness,
)
from app.clinical_event_intelligence_governance import intelligence_readiness
from app.clinical_event_intelligence_routes import (
    router as clinical_event_intelligence_router,
)
from app.config import get_settings
from app.dashboard import router as dashboard_router
from app.database import SessionLocal, engine
from app.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    safe_internal_error,
    validation_error_handler,
)
from app.expected_care_candidate_governance import (
    CandidateReleaseTransitionError,
    active_candidate_release,
)
from app.expected_care_comparison import router as expected_care_comparison_router
from app.expected_care_explanations import (
    explanation_release_ready,
)
from app.expected_care_explanations import (
    router as expected_care_explanations_router,
)
from app.expected_care_review import router as expected_care_review_router
from app.hospital_admin import doctor_router as doctor_hospital_resource_router
from app.hospital_admin import router as hospital_admin_router
from app.knowledge_catalog import router as knowledge_catalog_router
from app.knowledge_retrieval import router as knowledge_retrieval_router
from app.notification_delivery import readiness as notification_delivery_readiness
from app.notifications import router as notifications_router
from app.patient_chat import router as patient_chat_router
from app.product_analytics import router as product_analytics_router
from app.support import router as support_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Role-based care, cost-transparency, and educational-support API for Dr. AI. "
            "Synthetic or de-identified validation data only. Not intended for clinical use "
            "or reimbursement decisions."
        ),
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = f"req_{uuid.uuid4().hex}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Idempotency-Key",
            ],
            expose_headers=["X-Request-ID"],
        )

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, safe_internal_error)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, object]:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                schema_revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
            with SessionLocal() as db:
                compatible_release = explanation_release_ready(db, settings)
                chatbot_readiness = chatbot_generation_readiness(db, settings)
                semantic_routing = semantic_routing_readiness(settings)
                differential_planning = differential_planning_readiness(settings)
                clinical_intelligence_readiness = intelligence_readiness(db, settings)
                try:
                    candidate_release = active_candidate_release(db, settings)
                except CandidateReleaseTransitionError as exc:
                    candidate_release = None
                    candidate_release_code = str(exc)
                else:
                    candidate_release_code = "ready"
        except SQLAlchemyError as exc:
            raise ApiError(
                503, "service_unavailable", "The service is temporarily unavailable."
            ) from exc
        explanation_readiness = "disabled"
        if settings.expected_care_explanation_enabled:
            if settings.expected_care_explanation_kill_switch:
                explanation_readiness = "kill_switched"
            elif compatible_release:
                explanation_readiness = "ready"
            else:
                explanation_readiness = "blocked_no_compatible_release"
        candidate_readiness = "disabled"
        if settings.expected_care_candidate_enabled:
            candidate_readiness = candidate_release_code
        notification_readiness = {
            channel: notification_delivery_readiness(settings, channel).code
            for channel in ("apns", "android_emas", "web_push")
        }
        return {
            "status": "ok",
            "service": "dr-ai-api",
            "environment": settings.environment,
            "database": "ok",
            "schema_revision": schema_revision,
            "deployment": {
                "source_revision": settings.deployment_source_revision,
                "image_digest": settings.deployment_image_digest,
                "web_sha256": settings.deployment_web_sha256,
            },
            "patient_chat_generation": chatbot_readiness.code,
            "patient_chat_semantic_routing": semantic_routing.code,
            "patient_chat_differential_planning": differential_planning.code,
            "expected_care_candidate": candidate_readiness,
            "expected_care_candidate_release_version": (
                candidate_release.version if candidate_release else None
            ),
            "expected_care_explanation": explanation_readiness,
            "clinical_event_intelligence": clinical_intelligence_readiness,
            "imaging_observation_draft": "blocked_provider_text_only",
            "notification_worker": (
                "enabled" if settings.notification_worker_enabled else "disabled"
            ),
            "notification_delivery": notification_readiness,
        }

    app.include_router(auth_router)
    app.include_router(hospital_admin_router)
    app.include_router(doctor_hospital_resource_router)
    app.include_router(care_cost_router)
    app.include_router(clinical_event_intelligence_router)
    app.include_router(dashboard_router)
    app.include_router(expected_care_review_router)
    app.include_router(expected_care_comparison_router)
    app.include_router(expected_care_explanations_router)
    app.include_router(knowledge_catalog_router)
    app.include_router(knowledge_retrieval_router)
    app.include_router(notifications_router)
    app.include_router(patient_chat_router)
    app.include_router(product_analytics_router)
    app.include_router(support_router)
    return app


app = create_app()
