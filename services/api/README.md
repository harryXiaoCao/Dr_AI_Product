# Dr. AI API

FastAPI foundation for the invited Dr. AI beta. This service currently exposes
only `GET /health`; authentication and clinical features are intentionally
deferred.

Use synthetic content only. Do not submit real patient data.

## Local verification

```bash
uv sync --locked --dev
uv run ruff check .
uv run pytest -W error
uv run uvicorn app.main:app --reload
```
