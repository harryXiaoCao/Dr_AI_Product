# Phase 2 Patient And Doctor Core Progress Record

Recorded: 2026-07-08T00:54:29+08:00

Status: Phase 2 patient/doctor core workflows are complete locally. External
push, SMS, email, native local-notification delivery, real patient data,
clinical claims, real model inference, specialist/admin workflows, clinic
operations, billing, analytics, deployment, pushes, tags, pull requests, and
external account actions remain outside this Phase 2 closure.

## Scope Completed

- Added persisted patient demographics fields for display name, birth year,
  sex, preferred language, and contact preference.
- Added persisted allergy, chronic-disease, visit-history, and diagnosis
  tables.
- Added doctor-note update timestamp support.
- Added doctor assigned-patient profile update and patient own-profile update.
- Added allergy and chronic-disease create, edit, delete, and list endpoints
  for assigned doctors and the owning patient.
- Added visit-history and diagnosis create, edit, delete, and list endpoints;
  writes are doctor-only and reads are available to the owning patient.
- Added doctor-note create, edit, delete, and audited list endpoints;
  doctor notes remain hidden from patient-owned care bundles.
- Expanded doctor and patient care-bundle responses with demographics,
  allergies, chronic diseases, visit history, and diagnoses.
- Extended Flutter doctor Patient Management and patient profile/history read
  surfaces to show the new medical-history fields.
- Added focused backend and Flutter widget coverage for the first-slice
  readback surfaces and backend boundaries.
- Added doctor-owned medication create, edit, delete, and list endpoints;
  patients can read only their own medications.
- Added doctor-owned prescription create, edit, delete, and list endpoints with
  prescription medication lines; patients can read their own prescriptions.
- Added doctor-owned medication reminders and refill reminders, with patient
  own-reminder readback.
- Added a bounded backend delivery path that creates metadata-only in-app
  queued notification rows for active medication/refill reminders. No external
  push, SMS, email, or native local-notification service is called.
- Expanded doctor and patient care-bundle responses with prescriptions and
  medication reminders.
- Extended Flutter doctor Patient Management with medication, prescription,
  medication-reminder, and refill-reminder review/save controls.
- Extended Flutter patient profile/medication readback with prescription and
  medication-reminder status display.
- Added focused backend and Flutter widget coverage for the medication core
  slice.
- Added a production-separated medical imaging asset table for
  Tencent-COS-compatible upload metadata, upload completion confirmation,
  upload/review statuses, and doctor review metadata.
- Added imaging upload preparation, metadata-only completion, list, detail, and
  doctor-only review endpoints.
- Expanded doctor and patient care-bundle responses with imaging assets.
- Extended Flutter doctor Patient Management with imaging status readback and
  a small prepare/finalize/review workflow panel.
- Extended Flutter patient profile readback with imaging upload/review status.
- Added focused backend and Flutter widget coverage for the imaging slice.
- Added production recovery-plan review metadata for draft, in-review,
  changes-requested, approved/active, and completed semantics.
- Added doctor-only recovery-plan transition endpoints for submit-for-review,
  request-changes, approve, legacy activate compatibility, and complete.
- Added patient Today production tracking depth with active-plan progress
  summary, completed/remaining task counts, completion percent, and task
  completion timestamps.
- Added a persisted Clinical Event/Care Episode table as the central Phase 2
  workflow-clarification object.
- Added doctor-only Clinical Event create/update endpoints and doctor/patient
  read endpoints, including patient-owned `/patient/me/clinical-events`
  aliases.
- Added nullable `clinical_event_id` links on visit history, diagnoses,
  medications, prescriptions, medication/refill reminders, metadata-only
  notifications, recovery plans, imaging assets, doctor notes, and consultation
  requests.
- Expanded care-bundle responses with `clinical_events`, linked-resource
  counts, `recovery_plans`, and nullable event IDs on linked resources.
- Extended Flutter care-bundle domain models to parse Clinical Events and
  event-linked resource IDs.
- Extended Flutter doctor Patient Management so Clinical Events are the active
  organizing object above the workspace sections.
- Added doctor-side Clinical Event create/update/select controls inside the
  Clinical Events section.
- Scoped doctor Patient Management readback for encounter updates, diagnosis,
  medications, prescriptions, generated reminders, recovery plans, imaging,
  doctor notes, consultation requests, and activity timeline rows to the
  selected Clinical Event where linked event IDs exist.
- Wired the selected `clinical_event_id` into Flutter medication schedule save,
  prescription issue, medical imaging presign, recovery-plan create/update,
  and specialist consultation request calls. Existing backend request fields
  remain nullable for backward compatibility.
- Extended Flutter doctor Patient Management with recovery-plan review status,
  submit/review/approve/complete controls, and progress readback.
- Extended Flutter patient Today with a compact active-plan progress line.
- Updated patient dashboard golden evidence after the intentional Today visual
  change.
- Added focused backend and Flutter widget coverage for recovery-plan review
  semantics and patient Today progress.
- Added derived Clinical Event timeline readback so event responses show
  ordered episode activity beyond linked-resource counts.
- Added doctor-entered manual imaging finding/result fields to the doctor-only
  imaging review flow, backed by migration `20260708_0011`.
- Tightened recovery-plan activation so approving a replacement completes
  active plans only within the same Clinical Event; the doctor UI also
  surfaces the active-plan-per-event state.
- Extended Flutter doctor Patient Management to display event timeline rows
  and manual imaging findings/results inside the selected Clinical Event
  context.
- Added audited medical-history review overlays backed by migration
  `20260708_0012`, allowing assigned doctors to mark patient-entered history
  as verified, request correction, or add a clinician amendment without
  overwriting the original patient-entered allergy, chronic-disease, or record
  row.
- Added patient-submitted Clinical Event update rows backed by migration
  `20260708_0012`, with patient-owned submission/readback and inclusion in
  Clinical Event responses, care bundles, linked-resource counts, and the
  derived event timeline.
- Extended Flutter doctor Patient Management with a Medical History review
  panel and visible doctor review/amendment audit overlay.
- Extended the Flutter patient dashboard with a compact Clinical Event update
  submission panel that lets patients report an update without touching
  doctor-owned diagnosis fields.
- Added Phase 2 manual-testing onboarding cleanup so testers can create
  invited doctor/patient accounts from zero in Flutter, see the patient's
  generated patient code, connect that patient from doctor Patient Management,
  and then create Clinical Events and care records without relying on the
  seeded demo relationship.

## RBAC And Data Boundary

- Doctors can access Phase 2 medical-history resources only through an active
  care relationship.
- Patients can access only their own profile/history resources.
- Patients can update only demographics, allergies, and chronic diseases in
  this slice.
- Visit-history, diagnosis, doctor-note, medication, prescription, and reminder
  mutations are doctor-only.
- Patient probes to doctor-note endpoints return neutral `404 not_found`.
- Cross-patient probes return neutral `404 not_found`.
- Existing beta/demo seed data stays synthetic. The new production
  medical-history tables remain empty after seeding until tests or workflows
  create rows.
- The Phase 1 prescription, prescription-medication, medication-reminder, and
  notification tables are now used by Phase 2 workflows; no real patient data
  or production seed fixtures are introduced.
- Medical imaging uses a new production `medical_imaging_assets` table and
  keeps the historical `demo_medical_assets` beta path intact.
- Imaging upload completion confirms metadata only. The backend does not call
  Tencent COS, fetch files, inspect image contents, run model inference, or
  make clinical interpretations in this slice.
- Doctors and patients can list/read imaging metadata only through an active
  care relationship or own-patient boundary. Review status changes are
  doctor-only. Manual imaging findings/results are doctor-entered fields; the
  backend does not generate or infer those findings.
- Recovery-plan create/edit/review/approve/complete mutations are doctor-only
  and scoped to an active care relationship.
- Patients can read only their own active Today tasks and complete only their
  own active tasks.
- Clinical Event create/update remains doctor-only and scoped to an active
  care relationship. Patients can read their own events but cannot mutate
  event diagnosis summaries or doctor diagnosis records.
- Medical-history verification, correction requests, and clinician amendments
  are doctor-only overlays scoped to an active care relationship. They do not
  overwrite patient-entered history rows.
- Patients can submit updates only to their own Clinical Events. Patient
  updates are separate timeline entries and do not mutate doctor diagnosis
  summaries or diagnosis records.
- Doctors can connect a patient by patient-shared code. This creates or
  reactivates only that doctor-patient care relationship; wrong-role and
  invalid-code probes keep returning neutral `404 not_found`.
- Event-linked resource writes validate that `clinical_event_id` belongs to the
  same authorized patient; wrong-role and cross-patient probes keep returning
  neutral `404 not_found`.
- Recovery-plan edits are blocked while a plan is in review and after approval
  or completion. Approval makes the plan active and completes any previous
  active plan for the same Clinical Event, while preserving active plans for
  unrelated Clinical Events.
- Closing a recovery plan requires all active plan tasks to be completed.

## Audit Behavior

- Profile, allergy, chronic-disease, visit-history, diagnosis, doctor-note,
  medication, prescription, reminder, notification read, and care-bundle
  read/write paths create metadata-only audit events.
- Audit metadata records actor role, field names, statuses, counts, and
  resource identifiers only.
- Audit metadata does not copy allergy labels, condition names, visit
  summaries, diagnosis labels, doctor-note titles, note bodies, or other
  medical content.
- Audit and notification metadata does not copy medication names, dosages,
  schedules, medication notes, prescription notes, reminder labels, or other
  clinical content.
- Imaging audit metadata stores actor role, content type, byte counts,
  storage provider, upload status, review status, boolean checksum/ETag
  presence, and booleans for whether manual findings/result fields were
  supplied only.
- Imaging audit metadata does not copy filenames, object keys, upload URLs,
  ETags, checksums, image contents, manual finding/result text, review notes,
  or clinical interpretations.
- Recovery-plan audit metadata stores status, review status, task counts,
  completed task counts, categories, source transition, and resource IDs only.
- Recovery-plan audit metadata does not copy plan titles, instructions, task
  titles, task details, notification labels, or clinical content.
- Clinical Event and event-link audit metadata stores actor role, statuses,
  field names, resource IDs, counts, and event IDs only.
- Clinical Event and event-link audit metadata does not copy event titles,
  chief complaints, symptom summaries, diagnosis summaries, visit summaries,
  diagnosis labels, medication names, prescription notes, reminder labels,
  filenames, object keys, consultation questions, doctor notes, or clinical
  content.
- Medical-history review audit metadata stores actor role, target type,
  target ID, action, and booleans for supplied amendment/correction text only.
  It does not copy patient-entered history labels or amendment/correction
  content.
- Patient Clinical Event update audit metadata stores actor role, event ID,
  update type, and a summary-presence boolean only. It does not copy the
  patient's update text or alter doctor-owned diagnosis content.
- Patient-code connection audit metadata stores actor role, created/reactivated
  booleans, and a code-supplied boolean only. It does not copy the patient code
  into audit metadata.

## Remaining Phase 2 Workflow Clarification Work

- No known remaining items from the eight-functionality Phase 2 workflow
  clarification list remain open locally. Future hardening, external delivery,
  real-data readiness, AI assistance, clinic operations, specialist/admin UI,
  and localization remain separate gated phases.

## Deferred Beyond Phase 2

- External push, SMS, email, and native local-notification delivery remain
  gated because implementing them safely requires credentials, account/service
  changes, platform configuration, and later release hardening. Phase 2 keeps
  the backend delivery path metadata-only through in-app queued notification
  records. Phase 6 should close this as a China-market SMS-first delivery
  gate using phone-number-based messaging, with native push, native local
  notifications, or email added only if a later product/release decision needs
  them.
- Seeded demo accounts and relationships remain optional staging smoke and
  regression scaffolding. Manual product testing should use invited sign-up,
  patient-code connection, and user-created records from zero. A future
  staging-only database reset can remove accumulated synthetic inspection data,
  but it should be confirmed separately because it is destructive.
- Real patient data, clinical claims, real model inference, specialist/admin
  workflows, clinic operations, billing, analytics, deployment, pushes, tags,
  pull requests, and external account actions remain out of Phase 2.

## Verification

Recorded during this local implementation pass:

- `uv run ruff check .`: passed after backend formatting fixes.
- `uv run pytest tests/test_phase2_patient_doctor_core.py -q`: `8 passed`
  after the Clinical Event backend/API slice.
- `uv run pytest tests/test_phase2_patient_doctor_core.py -q`: `10 passed`
  after the audited Medical History review and patient Clinical Event update
  closure slice.
- `uv run alembic upgrade head`: passed through migration `20260708_0012`.
- `uv run alembic check`: passed with no new upgrade operations detected.
- `./scripts/verify_flutter.sh`: passed with analysis clean and widget/golden
  tests passing after the audited history review and patient event-update UI
  updates.

Full backend, Alembic, dependency, Flutter, and diff checks should be recorded
in the final task status for this implementation pass.

## Post-Closure Tencent Staging Redeploy

Recorded: 2026-07-08T01:17:44+08:00

After Phase 2 was committed locally as `8e9d344`, Tencent same-origin staging
was redeployed so the live web/API environment matches the completed Phase 2
patient/doctor core closure. This redeploy did not change production, tester
accounts, monitoring/account settings, native store uploads, tags, pushes,
pull requests, real patient data, or clinical workflows.

Deployment evidence:

- Pre-deploy local verification passed: backend Ruff, full backend tests
  (`64 passed`), Alembic upgrade/check, `uv pip check`,
  `./scripts/verify_flutter.sh`, Flutter web release build for
  `https://dr-ai.43.132.169.195.sslip.io`, and `git diff --check`.
- Built and pushed a sanitized API image on the Tencent CVM and deployed
  immutable digest
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:a1d55dd905acdd2113ed2dac163aaa7f0d1fc1a37ec4a0d2855b7e65e4250381`.
- Applied Alembic migrations `20260707_0007`, `20260708_0008`, and
  `20260708_0009` on staging.
- Ran the synthetic seed twice on staging; both runs were idempotent with all
  created counts at `0`.
- Rebuilt Flutter web for the Tencent staging origin, updated the mounted
  host-side `web/` directory in place, recreated API and Caddy containers, and
  validated the Caddy config.
- Credentialed staging smoke passed for health, doctor/patient login,
  refresh/logout, assigned-patient search, neutral cross-patient denial, demo
  upload presign, simulated assessment, recovery-plan save/activation,
  patient Today/task completion, Ask Dr. AI, consultation readback, and Beta
  support web surface.
- Public checks passed for `/health`, `/`, `/beta-support`, and unauthenticated
  `/api/v1/me` returning `401`.

Install-prep status after redeploy:

- Computer and phone browser/PWA inspection should use
  `https://dr-ai.43.132.169.195.sslip.io`.
- The Android debug APK was not rebuilt in this pass because Flutter is
  configured for `/Volumes/AndroidAVD/sdk`, but that SDK mount was unavailable
  locally. The existing `app-debug.apk` from 2026-07-07 is stale for Phase 2
  and should not be used as Phase 2 evidence.
- iPhone native install still requires selecting an Apple development team for
  bundle id `com.harrycao.drai.drAiApp`; TestFlight/App Store Connect remains
  separate from this staging redeploy.

## Workflow-Clarification Tencent Staging Redeploy

Recorded: 2026-07-08T22:57:20+08:00

After the Phase 2 Clinical Event workflow-clarification closure was committed
locally as `33d70e5` and pushed to GitHub branch
`codex/phase-2-patient-doctor-core`, Tencent same-origin staging was redeployed
so the live web/API environment matches the completed eight-functionality
workflow-clarification slice. This redeploy did not change production, tester
accounts, monitoring/account settings, native store uploads, tags, pull
requests, real patient data, or clinical workflows.

Deployment evidence:

- Built and pushed a sanitized API image on the Tencent CVM and deployed
  immutable digest
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:25532802291eae937b06266288047436646a72524d119965714879b2e44e42d7`.
- Applied Alembic migrations `20260708_0010`, `20260708_0011`, and
  `20260708_0012` on staging.
- Ran the synthetic seed twice on staging; both runs were idempotent with all
  created counts at `0`.
- Rebuilt Flutter web for
  `https://dr-ai.43.132.169.195.sslip.io`, confirmed the build was `41M` with
  `30` files, and found no database/JWT/DeepSeek/SSH/password env marker
  matches in the web build.
- Backed up the previous host-side web directory as
  `web.backup.20260708T145110Z`, synced the new web build in place, validated
  Caddy, and recreated the Caddy container. The remote `web/` directory now
  contains `30` files and is `42M`.
- Public HTTPS checks passed for `/health`, `/`, `/beta-support`, and
  unauthenticated `/api/v1/me` returning `401`.
- Credentialed staging smoke passed for health, doctor/patient login,
  refresh/logout, assigned-patient search, neutral cross-patient denial, demo
  upload presign, simulated assessment, recovery-plan save/activation,
  patient Today/task completion, Ask Dr. AI, consultation readback, and Beta
  support web surface.
- Focused Phase 2 live smoke passed for the new workflow-clarification
  endpoints: doctor medical-history review overlay creation, doctor Clinical
  Event creation, patient Clinical Event update creation, and event readback
  preserving doctor diagnosis while including the patient update in the
  timeline.

Inspection URL:

- `https://dr-ai.43.132.169.195.sslip.io`

## Post-Inspection Product Quality Reset

Recorded: 2026-07-09

After staging inspection, Phase 2 should be treated as a technical workflow
foundation, not as a commercially acceptable product surface. The user-facing
app still feels like a prototype: weak typography, missing first-class
patient avatar/profile setup, insufficient patient onboarding, too much
synthetic/demo language in the product experience, and doctor/patient screens
that do not yet communicate the calm trust expected from a real healthcare
application.

This does not invalidate the Phase 2 backend/API/RBAC/audit work, but it does
change the next step. Phase 3 AI systems should remain blocked until the
product-quality gate in `Dr_AI_v1.0_Product_Quality_Gate.md` is closed.

Immediate next work:

- audit live staging screenshots as patient and doctor;
- define a real production visual system and typography direction;
- implement patient avatar/profile setup and profile editing from the profile
  entry point;
- guide first-time patients through profile, medical history, and doctor
  connection;
- make doctor empty states and patient connection feel like a product flow;
- remove normal-flow "synthetic", "demo", "fixture", and "seed" copy from the
  user experience while preserving concise no-real-data staging warnings.

## Manual-Testing Onboarding Tencent Staging Redeploy

Recorded: 2026-07-08T23:42:47+08:00

After the Phase 2 manual-testing onboarding cleanup was committed locally as
`b14f10d` and pushed to GitHub branch
`codex/phase-2-patient-doctor-core`, Tencent same-origin staging was redeployed
so the live web/API environment supports from-zero invited patient/doctor
manual testing. This redeploy did not merge into `main`, change production,
alter tester/account settings, upload native store builds, create tags or pull
requests, use real patient data, start Phase 3 AI generation, or perform a
destructive staging database reset.

Deployment evidence:

- Built and pushed a sanitized API image on the Tencent CVM and deployed
  immutable digest
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:719bbef7331e4e1616e881a20f8b60367d468a02778c64922999da03e12464d9`.
- Ran Alembic `upgrade head` on staging. No new migration was needed for this
  cleanup slice.
- Did not rerun the synthetic seed. Existing seed records remain only as
  optional staging smoke/regression scaffolding; the intended inspection path
  is invited registration, patient-code connection, and user-created records.
- Rebuilt Flutter web for
  `https://dr-ai.43.132.169.195.sslip.io`, confirmed the local build was `41M`,
  found no database/JWT/DeepSeek/SSH/password env marker matches in the web
  build, synced the host-side `web/` directory in place, validated Caddy, and
  recreated the Caddy container. The remote `web/` directory now contains `90`
  files and is `42M`.
- Public HTTPS checks passed for `/health`, `/`, `/beta-support`, and
  unauthenticated `/api/v1/me` returning `401`.
- Focused live onboarding smoke passed without printing invite codes, patient
  codes, passwords, access tokens, or refresh tokens: invited patient and
  doctor registration, fresh patient care-bundle readback with a generated
  patient code, doctor patient-code connection after neutral pre-connection
  denial, and Clinical Event creation after connection.

Inspection URL:

- `https://dr-ai.43.132.169.195.sslip.io`
