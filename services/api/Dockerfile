FROM ghcr.io/astral-sh/uv:0.11.26 AS uv

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY services/api/alembic.ini ./
COPY services/api/migrations ./migrations
COPY services/api/app ./app
COPY services/api/scripts ./scripts
COPY services/api/knowledge_base ./knowledge_base
COPY evaluation/clinical_event_intelligence ./evaluation/clinical_event_intelligence

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
