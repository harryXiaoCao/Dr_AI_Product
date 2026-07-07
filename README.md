# Dr. AI

Dr. AI v1.0 is an invited, non-clinical beta built with Flutter, FastAPI, and
PostgreSQL. The repository accepts clearly synthetic demonstration data only.
Do not enter real patient data.

Current milestone: Week 4 Days 18-20 release prep is complete in the working
tree, Tencent staging now serves the Flutter web app plus the refreshed API
from the same HTTPS origin with credentialed smoke passing after the Caddy
change, and the non-Apple closure pass has added Android upload-key release
signing configuration plus public screenshot evidence. The app now includes
the Week 1 authentication/authorization
foundation, Week 2 doctor-led care loop through demo upload and simulated
assessment, Week 3 recovery/chat/consultation workflow, and Week 4 hardening.
Days 18-20 add a public pre-login Beta support surface for privacy notice,
consent readiness, account deletion request preparation, feedback draft
preparation, and known limitations, plus local release notes and release-gate
checklists. Real COS upload completion, real model inference, TestFlight/
Android closed-testing upload, production web/final-domain deployment, release
tagging, tester invites, monitoring/account changes, and clinical workflows
remain deferred until the required credentials/account access and a committed
release point are available.

## Repository map

- `apps/dr_ai_app/` - doctor web and patient mobile Flutter application.
- `services/api/` - FastAPI, SQLAlchemy, Alembic, authentication, and seed flow.
- `docs/` - frozen product/design/API decisions and closure evidence.
- `deploy/tencent/staging/` - deployment manifests for existing Tencent Cloud
  resources; no resources are created by the repository.

Release-prep records:

- `docs/v1.0.0-beta.1_Release_Notes.md`
- `docs/Week_4_Days_18_20_Release_Gate_Checklist.md`
- `docs/Week_4_Days_18_20_Release_Closure_Record.md`
- `docs/v1.0.0-beta.1_Non_Apple_Closure_Record.md`

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

## Personal beta access

Current personal-device access should use the lowest-friction channel for each
surface:

- Computer: install/open the HTTPS staging Flutter web app as a browser web app
  or PWA from Chrome, Edge, or Safari at
  `https://dr-ai.43.132.169.195.sslip.io`. Native desktop packaging remains
  unnecessary for this beta unless PWA behavior proves insufficient.
- Android phone: use the local debug APK built for the staging API origin:
  `apps/dr_ai_app/build/app/outputs/flutter-apk/app-debug.apk`.
  Play Console release builds now require a local ignored upload keystore via
  `apps/dr_ai_app/android/key.properties`.
- iPhone: direct Xcode install to a connected device is the fastest path once
  an Apple development team is selected for bundle id
  `com.harrycao.drai.drAiApp`. TestFlight still requires explicit approval and
  App Store Connect setup before any upload.
