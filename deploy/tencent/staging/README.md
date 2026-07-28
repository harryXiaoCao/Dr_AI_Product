# Tencent Cloud staging deployment

This directory is the reproducible staging handoff for the approved Dr. AI
architecture: an immutable FastAPI container on an existing Tencent Cloud
compute host, Flutter web static files served by Caddy from the same origin,
Caddy-managed HTTPS, an immutable internal retrieval-model service, and an
existing TencentDB for PostgreSQL instance. It does not create billable
resources or change account-wide settings.

The Slice F/G handoff is configuration-ready but deliberately inactive:
`.env.example` keeps the expected-care explanation purpose disabled and its
kill switch on. The pending checksum-bound release, frozen synthetic result,
and runbook live under `evaluation/expected_care/` and
`docs/runbooks/Expected_Care_Explanation_Controlled_Staging_Runbook.md`.
The product owner authorized the 2026-07-26 wholly synthetic controlled-staging
refresh recorded in the Phase 4 F/G closure record. That one staging action
does not authorize real-patient transmission, real-provider use, live payer
integration, public production, commercial use, or release activation.

## Required existing resources

- Tencent Cloud compute host with Docker Compose and inbound TCP 80/443.
- Tencent Container Registry namespace/repository.
- TencentDB for PostgreSQL database and least-privilege application user.
- Approved DNS name resolving to the compute host.
- Network rules allowing the compute host to reach TencentDB over its private
  endpoint.

Keep registry, database, DNS, and account credentials outside the repository.
Populate `.env` from `.env.example` on the host with mode `0600`.

## Release sequence

1. Create and validate host-only backups of `.env`, Compose/Caddy configuration,
   the current web bundle, knowledge release artifacts, and a PostgreSQL
   custom-format dump. Do not mutate the live release until these checks pass.
2. Build `services/api/Dockerfile` and push an immutable digest to the existing
   Tencent Container Registry repository.
3. Set `DR_AI_IMAGE` to that digest and configure the approved staging
   hostname/database values in the host-only `.env`.
4. Keep `DR_AI_RETRIEVAL_IMAGE` pinned to a validated immutable digest; replace
   it only when the retrieval validation artifact and image are released
   together.
5. Run migrations as a one-off task:

   ```bash
   docker compose run --rm api uv run --no-sync alembic upgrade head
   ```

6. Seed the clearly synthetic demonstration accounts:

   ```bash
   docker compose run --rm api uv run --no-sync python -m app.seed
   ```

7. Run the seed command a second time and confirm every `*_created` count is
   zero.
8. Build the Flutter web app for the approved staging origin:

   ```bash
   cd ../../apps/dr_ai_app
   flutter build web \
     --release \
     --no-web-resources-cdn \
     --dart-define=DR_AI_API_BASE_URL=https://$DR_AI_STAGING_HOST
   ```

   `--no-web-resources-cdn` keeps the Flutter renderer assets on the same
   Tencent origin. This avoids a blank or heavily delayed first render when
   Google-hosted CanvasKit resources are slow or unavailable in China.

9. Copy the generated `apps/dr_ai_app/build/web` contents to the host-side
   `web/` directory beside `compose.yaml`. Back up any existing `web/`
   directory first.

10. Start or refresh the service:

   ```bash
   docker compose up -d
   ```

11. Verify `https://$DR_AI_STAGING_HOST/health`, root web,
   `/beta-support`, database status, login, refresh rotation, logout, and
   neutral cross-patient access.

The API container disables access logs so authorization headers, request
bodies, refresh tokens, passwords, and synthetic patient-owned content cannot
enter application logs.

## Caddy routing

Caddy serves the Flutter web build from `/srv/dr-ai-web` and keeps API traffic
same-origin:

- `/api/*` reverse-proxies to `api:8000`;
- `/health` reverse-proxies to `api:8000`;
- all other routes serve static Flutter files;
- Flutter deep links fall back to `/index.html`.
