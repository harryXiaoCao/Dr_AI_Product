# Week 4 Days 18-20 Release Gate Checklist

Prepared: 2026-07-06

Status: local checklist prepared. Tencent staging same-origin web/API
deployment has been performed after explicit approval. A non-Apple closure pass
configured Android release signing to require a real upload key, re-ran the
staging smoke, and captured public web screenshots. No production release, tag,
tester invite, account-level monitoring change, native store upload, or
screen-recording action has been performed.

## Local evidence to keep before release approval

- Backend:
  - `cd services/api && uv run ruff check .`
  - `cd services/api && uv run pytest -W error`
  - `cd services/api && uv run alembic upgrade head`
  - `cd services/api && uv run alembic check`
  - `cd services/api && uv pip check`
  - `cd services/api && uv lock --check`
- Flutter:
  - `./scripts/verify_flutter.sh`
  - `cd apps/dr_ai_app && flutter build web`
- Whitespace:
  - `git diff --check`

## Tencent staging smoke runner

After staging host migration/seed refresh is approved and smoke credentials are
loaded into the local shell, run the redaction-safe HTTP smoke runner from the
repository root:

```bash
DR_AI_STAGING_BASE_URL=https://dr-ai.43.132.169.195.sslip.io \
DR_AI_STAGING_DOCTOR_PASSWORD="$DR_AI_STAGING_DOCTOR_PASSWORD" \
DR_AI_STAGING_PATIENT_PASSWORD="$DR_AI_STAGING_PATIENT_PASSWORD" \
DR_AI_STAGING_UNRELATED_PATIENT_PASSWORD="$DR_AI_STAGING_UNRELATED_PATIENT_PASSWORD" \
python3 scripts/run_staging_smoke.py
```

The doctor, patient, and unrelated-patient emails default to the seeded demo
accounts. Override them only if staging uses different approved smoke accounts:

- `DR_AI_STAGING_DOCTOR_EMAIL`
- `DR_AI_STAGING_PATIENT_EMAIL`
- `DR_AI_STAGING_UNRELATED_PATIENT_EMAIL`

If the unrelated-patient password is not available, set
`DR_AI_STAGING_UNRELATED_PATIENT_ID` to an approved unrelated synthetic patient
ID. The script intentionally fails instead of pretending a random unknown UUID
is a true cross-patient denial check.

## Device and browser checks

Run these only with available local devices or browser tooling. Do not load
simulators/emulators unless a native release-gate issue requires them.

| Surface | Prepared check | Status |
|---|---|---|
| Doctor desktop web | Open Tencent staging web, sign in as doctor, complete the golden care loop through consultation request. | API-backed credentialed staging smoke passed again on 2026-07-07. Public staging login screenshot captured at `docs/release-evidence/v1.0.0-beta.1/staging-login.png`. |
| Patient desktop browser | Sign in as patient, verify Today tasks, Ask Dr. AI educational response, consultation status, and Beta support surface. | API-backed credentialed staging smoke passed again on 2026-07-07. PWA manifest and service worker are served over HTTPS. Public Beta support screenshot captured at `docs/release-evidence/v1.0.0-beta.1/staging-beta-support.png`. |
| Physical iOS device | Build/run on a physical device, sign in as patient, verify secure session, Today tasks, Ask Dr. AI, logout, and Beta support. | Requires connected iPhone and signing approval. Project has bundle id `com.harrycao.drai.drAiApp`, automatic signing, and no checked-in `DEVELOPMENT_TEAM`. |
| Physical Android device | Build/run on a physical device, sign in as patient, verify secure session, Today tasks, Ask Dr. AI, logout, and Beta support. | Debug APK rebuilt for staging after the mark-only logo refresh: `apps/dr_ai_app/build/app/outputs/flutter-apk/app-debug.apk`; SHA-256 `c331b485fa3d04e2fb9030a5ba2ee5769919f6343dfbf10d5fcef4fe217c55aa`. User reported the app works on their phone; no agent-controlled Android device was available in this pass. |

## Packaging preparation

### TestFlight

Prepared command shape, not executed:

```bash
cd apps/dr_ai_app
flutter build ipa \
  --release \
  --build-name=1.0.0 \
  --build-number=1 \
  --dart-define=DR_AI_API_BASE_URL=https://<approved-beta-origin>
```

Approval required before configuring signing, uploading to App Store Connect,
submitting for TestFlight review, or inviting testers.

### Android closed testing

Prepared command shape, not executed:

```bash
cd apps/dr_ai_app
flutter build appbundle \
  --release \
  --build-name=1.0.0 \
  --build-number=1 \
  --dart-define=DR_AI_API_BASE_URL=https://<approved-beta-origin>
```

Approval required before adding production signing credentials, uploading to
Google Play Console, submitting closed testing, or inviting testers.

Current repository state: release builds require
`apps/dr_ai_app/android/key.properties`, copied from
`apps/dr_ai_app/android/key.properties.example`, plus a local ignored upload
keystore. Without those local credentials, the app-bundle command fails
intentionally with `Android release signing requires android/key.properties`
instead of creating a debug-signed release artifact.

For first personal-device Android testing, use the local debug APK instead of
release signing:

```bash
cd apps/dr_ai_app
flutter build apk \
  --debug \
  --dart-define=DR_AI_API_BASE_URL=https://dr-ai.43.132.169.195.sslip.io
```

Current output:
`apps/dr_ai_app/build/app/outputs/flutter-apk/app-debug.apk`.

### Doctor web

Prepared command shape, not executed:

```bash
cd apps/dr_ai_app
flutter build web \
  --release \
  --dart-define=DR_AI_API_BASE_URL=https://<approved-beta-origin>
```

Tencent staging same-origin web deployment was performed after explicit
approval on 2026-07-06. On 2026-07-07, the staging web bundle was refreshed
with PWA metadata, productized app names, and public `/beta-support` route
preservation. Computer access should use the HTTPS staging web app as a
browser-installed web app/PWA; native desktop packaging is not needed for the
current beta. Approval is still required before production web deployment,
final-domain cutover, or changing hosting/account settings beyond the approved
staging Caddy/web update.

## Clean-account demo

Prepared flow:

1. Create or verify an approved clean invited-beta doctor account.
2. Create or verify an approved clean invited-beta patient account.
3. Doctor signs in on desktop web.
4. Doctor opens Patient Management and selects the assigned synthetic patient.
5. Doctor reviews profile, records, medications, notes, and existing
   simulated-assessment history.
6. Doctor prepares demo upload metadata and runs a simulated assessment.
7. Doctor creates/updates and activates a recovery plan.
8. Patient signs in on a second device when feasible.
9. Patient verifies Today tasks, completes one synthetic task, sends a general
   Ask Dr. AI education question, and views consultation status.
10. Both roles open Beta support and verify privacy, consent, feedback,
    deletion-request, and known-limitation surfaces.
11. Both roles sign out.

## Backup demo evidence plan

Screen recording is approval-gated. If approved, record the clean-account demo
with no secrets, environment files, tokens, terminal scrollback, or real
patient data visible. Store the output path in the closure record and verify
the video opens before treating it as evidence.

Current evidence: non-secret public-route screenshots were captured at:

- `docs/release-evidence/v1.0.0-beta.1/staging-login.png`
- `docs/release-evidence/v1.0.0-beta.1/staging-beta-support.png`

## Backup/restore rehearsal

Staging or production data must not be touched without approval. The approved
rehearsal target should be a disposable database or staging snapshot:

1. Create a timestamped `pg_dump`.
2. Restore into a fresh disposable database.
3. Run `uv run alembic upgrade head`.
4. Run `uv run alembic check`.
5. Run `uv run python -m app.seed` twice and verify the second run is
   idempotent.
6. Run backend smoke tests against the restored target.
7. Record backup path, source revision, restore target, and row-count sanity
   checks.

## Tagging plan

Prepared command shape, not executed:

```bash
git tag -a v1.0.0-beta.1 -m "Dr. AI v1.0.0-beta.1"
git push origin v1.0.0-beta.1
```

Create and push the tag only after explicit approval and after the release
branch status, verification evidence, release notes, migrations, seed script,
and API contract are reviewed. Do not tag the current `HEAD` while the working
tree still contains uncommitted implementation and release-documentation
changes, because the tag would not include the actual beta state.

## Tester invite and monitoring checklist

Approval required before inviting testers or changing monitoring/account
settings.

- Invite only the approved small beta group.
- Include the synthetic-only boundary, no-real-data rule, emergency disclaimer,
  feedback path, deletion request path, and known limitations.
- Monitor crash reports, API 5xx responses, authentication failures,
  chat fallback/rate-limit events, assessment failures, upload metadata errors,
  and cross-patient/wrong-role probes.
- Triage P0/P1 defects before expanding the tester group.

Current state: no account-level monitoring resources were created or changed in
the non-Apple closure pass because no monitoring provider/account access was
available in the workspace.
