import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.config import get_settings
from app.dashboard import router as dashboard_router
from app.database import engine
from app.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    safe_internal_error,
    validation_error_handler,
)
from app.support import router as support_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Authentication and synthetic dashboard API for the Dr. AI invited beta. "
            "Not intended for clinical use or real patient data."
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
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept"],
            expose_headers=["X-Request-ID"],
        )

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, safe_internal_error)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise ApiError(
                503, "service_unavailable", "The service is temporarily unavailable."
            ) from exc
        return {
            "status": "ok",
            "service": "dr-ai-api",
            "environment": settings.environment,
            "database": "ok",
        }

    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(support_router)
    return app


app = create_app()
