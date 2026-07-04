# Week 1, Days 3-5 Closure Record

Recorded: 2026-07-04

Status: complete for repository implementation, local verification, and native
runtime checks; Tencent HTTPS staging deployment is externally blocked and is
not claimed as passed.

Week 2 status: not started.

## Closure outcome

Week 1 Days 3-5 implemented the approved data, authentication, authorization,
session, responsive-shell, and seeded-dashboard scope without enabling deferred
clinical workflows. The code remains synthetic-data only and non-clinical.

Branch: `codex/week1-days3-5`

Stacking base: `codex/week1-days1-2-closure`

Draft pull request: pending creation after this record is committed and pushed.

GitHub Actions run: pending after draft pull request creation.

## Schema and migration

Initial migration revision: `20260704_0001`

Migration file:
`services/api/migrations/versions/20260704_0001_auth_data_foundation.py`

The migration creates:

- `users`
- `doctor_profiles`
- `patient_profiles`
- `care_relationships`
- `refresh_sessions`
- `dashboard_snapshots`

It also creates the PostgreSQL `user_role` enum with `doctor` and `patient`.

Clinical Week 2-3 entities and behavior remain unavailable. The database is
ready for future migration expansion, but records, uploads, assessments,
recovery-plan workflows, medication behavior, reminders, chat, DeepSeek, and
consultations were not implemented in this gate.

## Synthetic accounts and seed procedure

Seed command:

```bash
cd services/api
uv run alembic upgrade head
uv run python -m app.seed
uv run python -m app.seed
```

Seed account emails:

- `doctor.demo@example.com`
- `patient.demo@example.com`
- `unrelated.patient@example.com`

Seed passwords are never committed. They must come from:

- `DR_AI_SEED_DOCTOR_PASSWORD`
- `DR_AI_SEED_PATIENT_PASSWORD`
- `DR_AI_SEED_UNRELATED_PATIENT_PASSWORD`

The seed flow is idempotent. Local PostgreSQL evidence:

```text
Synthetic seed complete: users_created=3, relationships_created=2, dashboards_created=3
Synthetic seed complete: users_created=0, relationships_created=0, dashboards_created=0
```

## Authentication and session design

- Passwords are hashed with Argon2id.
- Access tokens are short-lived HS256 JWTs with issuer, audience, subject,
  role, refresh-session id, JWT id, issued-at, and expiry claims.
- Refresh tokens are opaque random values.
- Only SHA-256 refresh-token hashes are stored server-side.
- Refresh succeeds once, rotates to a replacement session, marks the presented
  token used and revoked, and returns a new access/refresh pair.
- Replaying a used, revoked, expired, or otherwise invalid refresh token returns
  `401 unauthenticated`. Reuse of a used token revokes the entire refresh
  family.
- Logout requires the current bearer access token plus refresh token body,
  revokes the active refresh session, and causes subsequent authenticated reads
  through that session to fail.
- API access logs are disabled in the container handoff to avoid logging
  authorization headers, request bodies, passwords, refresh tokens, or
  patient-owned content.

## Role and ownership rules

- The server, not Flutter navigation, is the authorization boundary.
- Doctors can read only patients linked by an active `CareRelationship`.
- Patients can read only their own patient dashboard/resource.
- Revoked or inactive relationships are treated as absent.
- Wrong-role and cross-patient probes return neutral `404 not_found` when
  confirming existence would leak another patient's resource.
- All application errors use the frozen envelope with request IDs.

## Implemented API paths

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me`
- `GET /api/v1/me/dashboard`
- `GET /api/v1/patients`
- `GET /api/v1/patients/{patient_id}`
- `GET /api/v1/patient/me/today`

Pagination is frozen at `limit <= 50` for Week 1 list endpoints.

## Flutter behavior

- Riverpod owns authentication/session state and dependency injection.
- Dio handles networking, bearer tokens, standardized API errors, and one
  refresh-and-retry path after `401`.
- The refresh token is stored with `flutter_secure_storage`; the access token
  is memory-only.
- Startup restores a secure stored refresh session by rotating it.
- Logout revokes the server session and clears local token state.
- Role-aware routing rejects wrong-role navigation.
- Responsive shells:
  - `<600px`: patient bottom navigation.
  - `600-1023px`: compact/tablet rail.
  - `>=1024px`: doctor-oriented navigation and multi-column dashboard.
- Dashboard content is seeded synthetic demonstration data only.
- The exact non-clinical and synthetic-data labels remain visible.

## Local verification evidence

| Check | Result |
|---|---|
| Empty PostgreSQL migration | Passed on throwaway `dr_ai_smoke`; revision `20260704_0001` applied |
| Synthetic seed command twice | Passed; second run created zero new records |
| Backend Ruff | Passed: `All checks passed!` |
| Backend tests with warnings as errors | Passed: `16 passed` |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| API smoke | Passed: health, login, `/me`, active patient read, neutral cross-patient `404`, refresh replay rejection, logout revocation |
| Flutter formatting | Passed for changed Dart test files |
| `./scripts/verify_flutter.sh` | Passed: analysis clean; 11 widget/golden tests passed |
| Flutter web build | Passed: `✓ Built build/web`; non-blocking `CupertinoIcons` font warning observed with no project references |
| Android debug build | Passed: `✓ Built build/app/outputs/flutter-apk/app-debug.apk` |
| Android smoke launch | Passed: installed APK and launched `com.harrycao.drai.dr_ai_app/.MainActivity` cold |
| Android seeded patient login | Passed: Flutter integration test on `emulator-5554` against local FastAPI/PostgreSQL |
| Unsigned iOS Simulator build | Passed: `✓ Built build/ios/iphonesimulator/Runner.app` |
| iOS Simulator smoke launch | Passed after restart: `simctl launch` returned process id for `com.harrycao.drai.drAiApp` |
| Dashboard visual verification | Passed: golden screenshots at `1280x832` and `412x917` inspected and committed as synthetic visual baselines |
| Environment-template review | No committed secrets; seed passwords/invite/JWT secrets are placeholders only |

Golden files:

- `apps/dr_ai_app/test/goldens/doctor_dashboard_1280x832.png`
- `apps/dr_ai_app/test/goldens/patient_dashboard_412x917.png`

## Staging deployment status

Deployment manifests were added under `deploy/tencent/staging/` for the
approved architecture:

- existing Tencent Cloud compute host;
- existing Tencent Container Registry image;
- existing TencentDB for PostgreSQL;
- Caddy-managed HTTPS;
- one-off migration and synthetic seeding tasks before API startup.

Local checks found GitHub CLI access, but no local Tencent CLI or Docker command
was available from the current shell, and the earlier in-app browser attempt to
open the Tencent Cloud console was blocked by browser policy. Because deploying
or exposing a public HTTPS service is consequential, no workaround was used and
no staging endpoint is claimed.

Staging gate blocker:

- Tencent Cloud console/tooling access is unavailable in this session.
- Docker/Tencent deployment execution is unavailable locally.
- Therefore staging `/health`, HTTPS database connectivity, and staging auth
  smoke tests remain unverified.

Staging URL: not provisioned in this run.

Non-secret deployment identifiers: not available.

## Security and data review

- No real patient data was added.
- All seed names, emails, identifiers, and dashboard content are synthetic.
- No passwords, raw refresh tokens, JWTs, or cloud credentials are committed.
- Refresh tokens are stored server-side only as hashes.
- Application/container docs instruct running without HTTP access logs.
- Standard error responses carry request IDs.
- The research model is not implemented and no clinical-validation claim is
  made.

## Draft PR and CI

Draft PR: pending creation.

CI run: pending after push.

This record must be updated with PR and CI links after the branch is pushed and
GitHub Actions completes.

## Remaining Week 2 work

Week 2 remains not started. Approved next scope:

- patient search/list and richer profile;
- medical history, medications, and doctor notes;
- loading, empty, validation, unauthorized, and network-error states for the
  expanded care loop;
- presigned demo-image upload;
- deterministic simulated assessment fixture service;
- assessment result screen with simulation label and limitations;
- audit events for sensitive operations.

Do not implement DeepSeek, recovery-plan workflows, reminders, chat,
consultations, or clinical behavior before their approved Week 3 scope.
