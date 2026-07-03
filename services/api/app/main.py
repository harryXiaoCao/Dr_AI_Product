from fastapi import FastAPI

from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Foundation API for synthetic Dr. AI beta experiences. "
            "Not intended for clinical use or real patient data."
        ),
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "dr-ai-api",
            "environment": settings.environment,
        }

    return app


app = create_app()
