# Dr. AI

Dr. AI v1.0 is an invited, non-clinical beta built with Flutter, FastAPI, and
PostgreSQL. The repository accepts clearly synthetic demonstration data only.
Do not enter real patient data.

Current milestone: Week 1 authentication, authorization, PostgreSQL data
foundation, and seeded responsive dashboards.

## Repository map

- `apps/dr_ai_app/` - doctor web and patient mobile Flutter application.
- `services/api/` - FastAPI, SQLAlchemy, Alembic, authentication, and seed flow.
- `docs/` - frozen product/design/API decisions and closure evidence.
- `deploy/tencent/staging/` - deployment manifests for existing Tencent Cloud
  resources; no resources are created by the repository.

## Local start

Create PostgreSQL databases named `dr_ai` and `dr_ai_test`, then:

```bash
cd services/api
cp .env.example .env
uv sync --locked --dev
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

Populate seed passwords and local invite codes only in the untracked `.env`.
For normal local development, use Flutter web, widget tests, and CI rather than
loading iOS or Android simulators. From the repository root, verify Flutter
with:

```bash
./scripts/verify_flutter.sh
```

Mobile simulators/emulators are reserved for milestone checks that need native
runtime behavior, such as secure storage, permissions, notifications, platform
builds, and beta packaging. Physical devices can replace local simulators when
disk space is tight.

Android development storage is intentionally externalized: the SDK is configured
at `/Volumes/AndroidAVD/sdk`, with the legacy Homebrew SDK path kept as a
symlink, and AVD images live under `/Volumes/AndroidAVD/avd`. This APFS volume
is backed by the `PHILIPS` SSD. Keep `PHILIPS` and `/Volumes/AndroidAVD`
mounted before Android builds or emulator checks.

See the service/app READMEs for the complete verification commands.
