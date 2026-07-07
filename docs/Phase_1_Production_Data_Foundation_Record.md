# Phase 1 Production Data Foundation Record

Recorded: 2026-07-07T17:33:59+08:00

Status: Phase 1 production data foundation complete. Phase 2 workflows have
not started.

## Scope

This record closes production/commercial v1.0 Phase 1 only. It adds the
production schema foundation, route-level RBAC helpers, fail-closed role
boundaries, endpoint-level authorization tests, and authenticated
support/deletion/feedback submission/status foundation needed before later
specialist/admin and commercial workflows can become visible product surfaces.

No specialist/admin Flutter UI, Phase 2 patient/doctor CRUD workflows, Phase 4
clinic-operation workflows, Phase 5 admin handling UI, admin support queue
resolution, real COS upload completion, real notification delivery,
billing/payment processing, analytics dashboards, clinical model use, external
account action, tag, push, or pull request was performed.

## Implemented

- Added the Phase 1 Alembic migration
  `services/api/migrations/versions/20260707_0006_phase1_production_foundation.py`.
- Expanded backend `UserRole` enum to include `specialist` and `admin`.
- Kept future `specialist` and `admin` registration fail-closed until invite,
  profile, and workflow semantics are explicitly implemented.
- Made unsupported API roles unable to use the beta `/api/v1/me/dashboard`
  workflow.
- Made Flutter role parsing fail closed: unknown/future wire roles now map to
  `AppRole.unsupported` and route to `/unauthorized`, not `/doctor`.
- Added production foundation models for:
  - hospitals and clinics;
  - role assignments, doctor teams, and doctor-team memberships;
  - clinic resources and equipment;
  - appointments and equipment bookings;
  - prescriptions, prescription medications, and medication reminders;
  - notifications;
  - invoices, payment statuses, and revenue summaries;
  - analytics events;
  - support/deletion/feedback queue requests.
- Preserved existing beta/demo paths and synthetic seed data without moving
  seeded rows into production tables.
- Added route-level RBAC helpers for Phase 1 foundation routes.
- Added authenticated `/api/v1/support-requests` submission and requester-owned
  status read endpoints for doctor and patient users only.
- Kept specialist/admin support-request access fail-closed until Phase 5
  workflows are explicitly implemented.
- Persisted support, deletion, and feedback queue rows with `queued` status,
  requester authorization, redacted body storage, and audit metadata.
- Added metadata-only support audit events for queue creation, own-status
  listing, and own-status reads.
- Added focused tests for migration presence, seed/demo separation,
  specialist/admin fail-closed registration, unsupported-role dashboard denial,
  cross-role patient-route denial, support queue/audit metadata persistence,
  wrong-requester status denial, unsupported/future role denial without side
  effects, and unsafe support-content rejection.

## Data Boundary

The existing seed flow still creates only synthetic beta/demo users, care
relationships, dashboards, records, medications, notes, recovery plans, and
recovery tasks. The new production foundation tables remain empty after
`app.seed` runs. This keeps beta/demo data paths separate from the new
production data foundation until Phase 2+ workflows intentionally populate the
production tables.

## Remaining After Phase 1

- Phase 2 patient/doctor CRUD workflows have not started.
- Phase 4 clinic operations have not started.
- Phase 5 specialist/admin UI, audit search, system status, and admin-managed
  support/deletion/feedback queue handling have not started.
- Real upload completion, real notification delivery, billing/payment
  processing, analytics dashboards, production monitoring, external release
  actions, clinical model use, and real patient data remain gated.
- Production seed fixtures were not added in Phase 1 because no production
  workflow requires seeded production rows yet; the current seed remains
  synthetic demo-only.

## Post-Closure Tencent Staging Redeploy

Recorded: 2026-07-07T17:52:12+08:00

After Phase 1 was committed, Tencent staging was explicitly redeployed so the
live same-origin web/API environment matches the completed Phase 1 foundation.
This redeploy did not change production, tester accounts, monitoring/account
settings, native store uploads, tags, pushes, pull requests, or real patient
data.

Deployment evidence:

- Pre-deploy `/health` returned staging/database `ok`.
- Built a sanitized API image on the Tencent CVM and pushed/deployed immutable
  digest
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:d10187ae5178b089581a05b603f77c32ece079341bef7b3a93d8f79c3035af93`.
- Ran Alembic on staging; migration `20260707_0006` applied successfully.
- Ran the synthetic seed twice; both runs were idempotent with all created
  counts at `0`.
- Rebuilt Flutter web for
  `https://dr-ai.43.132.169.195.sslip.io`, installed it to the host `web/`
  directory after backing up the previous bundle, validated Caddy config, and
  recreated Caddy.
- Public checks passed for `/health`, `/`, `/beta-support`, and unauthenticated
  `/api/v1/me` returning `401`.
- Credentialed staging smoke passed for login, refresh/logout, assigned-patient
  search, neutral cross-patient denial, demo upload presign, simulated
  assessment, recovery-plan activation, patient Today/task completion, Ask Dr.
  AI, consultation status, and Beta support web surface.
- Phase 1 support queue probe passed for support request create/list/status,
  cross-requester `404`, and unsafe-content `422`.
- Recent API log keyword scan found `0` matches for obvious password, token,
  bearer, DeepSeek-key, JWT, or database URL strings.

## Verification

- `uv run ruff check .`: passed.
- `uv run pytest tests/test_phase1_production_foundation.py -q`: `5 passed`.
- `uv run pytest tests/test_phase1_production_foundation.py -q`: `9 passed`
  after authenticated support/deletion/feedback submission/status endpoints
  and route-level RBAC tests were added.
- `uv run pytest tests/test_auth.py tests/test_week2_upload_assessment.py
  tests/test_week3_chat_consultation.py
  tests/test_phase1_production_foundation.py -q`: `33 passed`.
- `uv run alembic upgrade head`: passed through revision `20260707_0006`.
- `uv run alembic check`: passed with no new upgrade operations detected.

Additional full-suite and Flutter verification should be recorded in the final
task status for the implementation pass that created this record.
