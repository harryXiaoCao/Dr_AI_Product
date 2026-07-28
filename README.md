# Dr. AI

Slices A-G are hardened for wholly synthetic development and controlled
staging: governed synthetic rehabilitation, laboratory, imaging, and
consultation reference families; immutable deterministic comparison;
canonical-claim role explanations; separately evaluated Slice D and Slice F
DeepSeek purposes; executable machine gates; append-only release operations;
and complete doctor/patient/payer actions. Baseline display and comparison do
not require clinician approval; clinician responses remain separate evidence.
Pending v3 and the separate Slice D release use truthful current-stage waivers
and remain kill-switched. Real-patient, real-provider, live-payer,
public-production, and commercial gates remain separate. See
`docs/periodic_dev_docs/Phase_4_Slices_F_G_Comparison_Explanation_Governance_Record.md`
and `docs/runbooks/Expected_Care_Explanation_Controlled_Staging_Runbook.md`.

Dr. AI is a production-quality product in development for China-first,
multi-scenario care-and-cost transparency. The implemented foundation includes
patient, doctor, and organization-scoped payer-reviewer workflows, Clinical
Events and Clinical Services, source-linked care-cost records, immutable payer
request snapshots, human payer-review outcomes, governed medical knowledge,
and a bounded patient chatbot. An internal, default-off expected-care candidate
purpose now produces schema-constrained, source-linked synthetic candidates
over versioned clinical/utilization and pricing references, then revalidates
every field deterministically. Slice E publishes the validated result as an
immutable baseline and records clinician positions separately; no doctor can
edit, reject, or hide the baseline.

The repository accepts clearly synthetic demonstration data only. Do not enter
real patient data.

The historical invited-beta foundation is preserved, but it is not the current
product boundary. Production claims/adjudication, live coverage and payment,
live reference-pricing releases, production immutable expected-care baselines,
public AI cost assistance,
external notification delivery, specialist/admin/clinic operations, public
store distribution, final-domain production deployment, real-patient use, and
live institutional integration remain independently gated until their
implementation, evaluation, authorization, and external requirements close.

## Repository map

- `apps/dr_ai_app/` - doctor web and patient mobile Flutter application.
- `services/api/` - FastAPI, SQLAlchemy, Alembic, authentication, and seed flow.
- `docs/` - current production v1.0 plan, Phase 0 closure, design/API
  decisions, and historical beta records under `docs/beta/`.
- `deploy/tencent/staging/` - deployment manifests for existing Tencent Cloud
  resources; no resources are created by the repository.

Current production docs:

- `Dr_AI_Product_Requirements_Document_v1.0.md`
- `docs/Dr_AI_v1.0_Implementation_Plan.md`
- `docs/Dr_AI_v1.0_AI_Platform_Architecture.md`
- `docs/Dr_AI_v1.0_ERD.md`
- `docs/Dr_AI_v1.0_API_Contract.md`
- `docs/Dr_AI_v1.0_Product_Quality_Gate.md`
- `docs/periodic_dev_docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`
- `docs/periodic_dev_docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`

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
uv run python -m scripts.bootstrap_synthetic_expected_care_demo
uv run uvicorn app.main:app --reload
```

Populate seed passwords and local secrets only in the untracked `.env`.
The Slice E bootstrap is idempotent, wholly synthetic, restricted to
local/test environments, and performs no external provider call.
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
