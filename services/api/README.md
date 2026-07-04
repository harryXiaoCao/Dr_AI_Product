# Dr. AI API

FastAPI and PostgreSQL service for the invited Dr. AI beta. Week 1 exposes
authentication, current-user identity, assigned-patient summaries, and
role-specific synthetic dashboard reads only. Clinical workflows remain
unavailable.

Use synthetic content only. Do not submit real patient data.

## Local database and environment

PostgreSQL 17 is the development and CI database. Create `dr_ai` and
`dr_ai_test`, copy `.env.example` to the ignored `.env`, and generate unique
local values for the JWT secret, invite codes, and three synthetic seed
passwords.

```bash
uv sync --locked --dev
uv run alembic upgrade head
uv run alembic check
uv run python -m app.seed
uv run python -m app.seed
```

The second seed run must report zero newly created users, relationships, and
dashboards. Seed account emails are:

- `doctor.demo@example.com`
- `patient.demo@example.com`
- `unrelated.patient@example.com`

Passwords are never stored in the repository and must come from environment
configuration.

## API and verification

```bash
uv run ruff check .
uv run pytest -W error
uv run uvicorn app.main:app --reload --no-access-log
```

The access token lifetime defaults to 10 minutes. Refresh tokens are opaque,
rotated on every use, stored only as SHA-256 hashes, and grouped into a
server-revocable session family. Replay revokes the family. Logout revokes the
active refresh session and its access token is rejected by subsequent
authenticated reads.

All non-2xx application responses use the frozen error envelope with a request
ID. Cross-patient and wrong-role resource probes return neutral
`404 not_found`.

## Container

`Dockerfile` builds the locked API image and disables HTTP access logs. Run
migration and synthetic seeding as explicit one-off release tasks before
starting the service. Tencent staging instructions live in
`../../deploy/tencent/staging/`.
