# Dr. AI

Dr. AI is moving from a completed invited, non-clinical beta foundation toward
production/commercial v1.0. Phase 2 patient/doctor workflow foundations are
implemented, but the visible app is not yet commercial-quality. Before Phase 3
AI work starts, the project must close the product-quality gate in
`docs/Dr_AI_v1.0_Product_Quality_Gate.md`: real-app onboarding, patient
avatar/profile setup, credible typography, calmer patient/doctor workflows,
useful empty states, and removal of normal-flow synthetic/demo language.

The repository accepts clearly synthetic demonstration data only. Do not enter
real patient data.

The historical beta foundation includes authentication/authorization, seeded
doctor and patient dashboards, the doctor-led care loop through demo upload and
simulated assessment, recovery plans and Today tasks, educational chat,
consultation request/status readback, same-origin Tencent staging web/API
deployment, Android debug access, beta support surfaces, and release evidence.
That beta foundation is not the full production v1.0 definition:
specialist/admin roles, support/deletion/feedback admin queue handling,
external notification delivery beyond metadata-only in-app records, billing
workflows, analytics dashboards, clinic operations workflows, real model
inference, store uploads, final-domain production deployment, tester invites,
monitoring/account changes, and clinical workflows remain gated or unstarted.

## Repository map

- `apps/dr_ai_app/` - doctor web and patient mobile Flutter application.
- `services/api/` - FastAPI, SQLAlchemy, Alembic, authentication, and seed flow.
- `docs/` - current production v1.0 plan, Phase 0 closure, design/API
  decisions, and historical beta records under `docs/beta/`.
- `deploy/tencent/staging/` - deployment manifests for existing Tencent Cloud
  resources; no resources are created by the repository.

Current production docs:

- `docs/Dr_AI_v1.0_Implementation_Plan.md`
- `docs/Dr_AI_v1.0_Product_Quality_Gate.md`
- `docs/Phase_0_Production_v1_Surface_Audit.md`
- `docs/Phase_0_Production_v1_Closure_Record.md`
- `docs/Phase_1_Production_Data_Foundation_Record.md`
- `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`
- `docs/Dr_AI_v1.0_API_Contract.md`
- `docs/Dr_AI_v1.0_Design_Freeze.md`

Historical beta records:

- `docs/beta/v1.0.0-beta.1_Release_Notes.md`
- `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md`
- `docs/beta/Week_4_Days_18_20_Release_Closure_Record.md`
- `docs/beta/v1.0.0-beta.1_Non_Apple_Closure_Record.md`

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

Populate seed passwords and local secrets only in the untracked `.env`.
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
