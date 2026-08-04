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
The product owner authorized wholly synthetic controlled-staging refreshes.
The latest verified refresh deployed the Phase 5 worktree based on commit
`7b8d004` through migration `20260728_0052`. The immutable API digest is
`sha256:58244c2e385b3dcaa050820ed99d16d71b4ef25c35a5f685c471872afacb739b`;
the web archive SHA-256 is
`0e8f7ffbe049f5734feb9276cafd2033d8cd48b1a4fd82dee020b4ba30bf5741`.
The backup, artifact, migration/seed, smoke, lifecycle, and redaction evidence
is recorded in the Phase 5 closure record. That staging evidence
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

## Phase 7 verified staging identity

The completed controlled-synthetic Phase 7 rehearsal uses:

- API:
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:844e16893bf6b1b7e396cbd253cc50a861d651a69b91c4381203d5c0ce416803`;
- retrieval:
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-retrieval@sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89`;
- source identity: `7b8d004+api-portable-20ae98ff`;
- schema: `20260730_0054`;
- Flutter web content-manifest SHA-256:
  `5468b6aca9697f3c0916d19e7b09cf49e2c1bad7689c0cd4c6370e019c0b82f0`;
  and
- Flutter web archive SHA-256:
  `1afefc00851466cec14f7167609f4b7740b44fa5da871a06c2ab78698d1c06b1`.

Final readiness keeps Slice D, Slice F, chatbot generation, notification
workers, APNs, EMAS, and Web Push disabled; imaging reports
`blocked_provider_text_only`. The pre-activation and post-activation backups,
three-role smoke, governed release transitions, exact predecessor rollback,
backup restoration, and count-only redaction evidence are recorded in
[`docs/periodic_dev_docs/Phase_7_Closure_Record_2026-07-30.md`](../../../docs/periodic_dev_docs/Phase_7_Closure_Record_2026-07-30.md).

## 2026-08-04 verified controlled-staging refresh

The latest verified refresh deploys source
`1cc0c87e90167244984d88de613695f8bc09a8f6` with:

- API digest
  `sha256:b51c0ecb6204c86214ab75d5ea12f52d3181d6e195c9be7befea0208738d231e`;
- unchanged retrieval digest
  `sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89`;
- schema `20260802_0058` with no Alembic drift;
- Flutter web content-manifest SHA-256
  `982035b38aa5ce8ad776cb5d979f5a3bbd9d4a5ba3d9482f5c8e1fea29890c96`;
  and
- owner-only checksum-verified backup
  `/home/ubuntu/dr-ai/staging/backups/20260804T022356Z-main-c168bdd`.

Both seed passes created zero records. Public health, root, privacy, and
unauthenticated boundaries passed, as did the authenticated doctor, patient,
unrelated-patient, and payer smoke. API, Caddy, and retrieval reported zero
restarts, deployed web hashes matched locally, and the count-only recent-log
scan found zero sensitive-or-critical matches.

The image contains the checksum-bound Clinical Event Intelligence evaluation
package and the database contains its `0055`-`0058` persistence schema. This
refresh does not activate the three CEI purposes: each remains disabled and
kill-switched, every active release pointer is null, and no CEI provider call
was made. The immutable release installer correctly rejected registering an
enabled-runtime artifact under the disabled runtime contract. Activation
requires a separate explicit authorization and rollback-aware exercise.

This remains wholly synthetic controlled staging. It is not evidence or
authorization for real-patient transmission, live payer integration, public
production, commercial use, clinical efficacy, privacy/security approval, or
legal/regulatory clearance.

## Phase 6 notification delivery gate

The staging example keeps `DR_AI_NOTIFICATION_EXTERNAL_DELIVERY_ENABLED=false`,
leaves every provider credential empty, and keeps EMAS OEM approvals false.
The persisted in-product inbox remains available independently. Missing
credentials, entitlement, permission, endpoint, provider approval, or target
readiness must produce an unavailable or failed bounded result; it must not
create a provider receipt or a delivered state.

Alibaba Cloud EMAS Mobile Push is the selected new Android adapter because its
current official integration supports the major China OEM channels. Tencent
TPNS is not the new-application default because Tencent ended new application
access and sales on 2024-03-31. APNs and Web Push remain separate adapters.
Exact prerequisites, primary sources, evidence semantics, and external blockers
are recorded in
[`docs/runbooks/Phase_6_Notification_Delivery_Readiness.md`](../../../docs/runbooks/Phase_6_Notification_Delivery_Readiness.md).

## Release sequence

1. Create and validate host-only backups of `.env`, Compose/Caddy configuration,
   the current web bundle, knowledge release artifacts, and a PostgreSQL
   custom-format dump. Do not mutate the live release until these checks pass.
2. From the repository root, build `services/api/Dockerfile` with the repository
   root as its context and push an immutable digest to the existing Tencent
   Container Registry repository. The root context includes the checksum-bound
   Clinical Event Intelligence evaluation package required at runtime:

   ```bash
   docker build --platform linux/amd64 -f services/api/Dockerfile .
   ```
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

11. Verify `https://$DR_AI_STAGING_HOST/health`, root web, `/privacy`,
   database status, the unauthenticated `/api/v1/me` `401` envelope, login,
   refresh rotation, logout, and neutral cross-patient access.
12. From the repository root, run `python3 scripts/run_staging_smoke.py` with
   credentials supplied only through its documented environment variables.
   Require its final
   `STAGING SMOKE PASSED` marker, then inspect recent API and Caddy logs for
   sensitive or critical patterns without printing credentials or
   content-bearing records.
13. For a separately authorized Phase 6 provider exercise, first apply the
    notification-readiness runbook. Back up and checksum the pre-change host
    state, verify only credential presence (never values), keep unavailable
    adapters disabled, and record provider acceptance separately from
    user-visible delivery evidence.

For a Phase 5 refresh, additionally require the completed Phase 5 local gates,
preserve the existing retrieval image unless independently released, and keep
patient-chat generation plus both expected-care generation purposes disabled
and kill-switched. Do not mutate or replace historical release/evaluation
artifacts to make the deployment pass.

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
