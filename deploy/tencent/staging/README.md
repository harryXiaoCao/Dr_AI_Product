# Tencent Cloud staging deployment

This directory is the reproducible staging handoff for the approved Dr. AI
architecture: an immutable FastAPI container on an existing Tencent Cloud
compute host, Flutter web static files served by Caddy from the same origin,
Caddy-managed HTTPS, and an existing TencentDB for PostgreSQL instance. It does
not create billable resources or change account-wide settings.

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

1. Build `services/api/Dockerfile` and push an immutable digest to the existing
   Tencent Container Registry repository.
2. Set `DR_AI_IMAGE` to that digest and configure the approved staging
   hostname/database values in the host-only `.env`.
3. Run migrations as a one-off task:

   ```bash
   docker compose run --rm api uv run --no-sync alembic upgrade head
   ```

4. Seed the clearly synthetic demonstration accounts:

   ```bash
   docker compose run --rm api uv run --no-sync python -m app.seed
   ```

5. Run the seed command a second time and confirm every `*_created` count is
   zero.
6. Build the Flutter web app for the approved staging origin:

   ```bash
   cd ../../apps/dr_ai_app
   flutter build web \
     --release \
     --dart-define=DR_AI_API_BASE_URL=https://$DR_AI_STAGING_HOST
   ```

7. Copy the generated `apps/dr_ai_app/build/web` contents to the host-side
   `web/` directory beside `compose.yaml`. Back up any existing `web/`
   directory first.

8. Start or refresh the service:

   ```bash
   docker compose up -d
   ```

9. Verify `https://$DR_AI_STAGING_HOST/health`, root web,
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
