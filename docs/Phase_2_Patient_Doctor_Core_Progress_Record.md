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
- Extended Flutter doctor Patient Management with recovery-plan review status,
  submit/review/approve/complete controls, and progress readback.
- Extended Flutter patient Today with a compact active-plan progress line.
- Updated patient dashboard golden evidence after the intentional Today visual
  change.
- Added focused backend and Flutter widget coverage for recovery-plan review
  semantics and patient Today progress.

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
  doctor-only.
- Recovery-plan create/edit/review/approve/complete mutations are doctor-only
  and scoped to an active care relationship.
- Patients can read only their own active Today tasks and complete only their
  own active tasks.
- Recovery-plan edits are blocked while a plan is in review and after approval
  or completion. Approval makes the plan active and completes any previous
  active plan for the same patient.
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
  storage provider, upload status, review status, and boolean checksum/ETag
  presence only.
- Imaging audit metadata does not copy filenames, object keys, upload URLs,
  ETags, checksums, image contents, review notes, or clinical interpretations.
- Recovery-plan audit metadata stores status, review status, task counts,
  completed task counts, categories, source transition, and resource IDs only.
- Recovery-plan audit metadata does not copy plan titles, instructions, task
  titles, task details, notification labels, or clinical content.

## Deferred Beyond Phase 2

- External push, SMS, email, and native local-notification delivery remain
  gated because implementing them safely requires credentials, account/service
  changes, platform configuration, and later release hardening. Phase 2 keeps
  the backend delivery path metadata-only through in-app queued notification
  records. Phase 6 should close this as a China-market SMS-first delivery
  gate using phone-number-based messaging, with native push, native local
  notifications, or email added only if a later product/release decision needs
  them.
- Controlled invite onboarding and account registration remain in the
  authentication/account lifecycle scope; Phase 2 does not create a separate
  doctor-side patient-account creation workflow.
- Real patient data, clinical claims, real model inference, specialist/admin
  workflows, clinic operations, billing, analytics, deployment, pushes, tags,
  pull requests, and external account actions remain out of Phase 2.

## Verification

Recorded during this local implementation pass:

- `uv run ruff check .`: passed after backend formatting fixes.
- `uv run pytest tests/test_phase2_patient_doctor_core.py -q`: `7 passed`.
- `./scripts/verify_flutter.sh`: passed with analysis clean and widget/golden
  tests passing after recovery-plan/Today golden updates.

Full backend, Alembic, dependency, Flutter, and diff checks should be recorded
in the final task status for this implementation pass.
