# Dr. AI API

## Expected-care comparison and explanation

Migration head `20260726_0047` adds append-only deterministic comparisons,
role-specific explanation requests/attempts/artifacts, monotonic governed
release events, and database-level immutable governed care releases.
`DR_AI_EXPECTED_CARE_EXPLANATION_ENABLED=false` and
`DR_AI_EXPECTED_CARE_EXPLANATION_KILL_SWITCH=true` are the safe defaults.
DeepSeek is the only accepted explanation provider. The corrected claim-graph
contract lets the provider select admitted claims while the server renders all
protected values in both languages. Public generation requires a
checksum-compatible active release and current-stage/future-stage review
requirements appropriate to the deployment. Pending v3 remains kill-switched
and therefore fails closed to structured facts.

Run the frozen suite from this directory:

```bash
uv run python -m scripts.evaluate_expected_care_explanations
uv run python -m scripts.evaluate_expected_care_explanations --live
uv run python -m scripts.evaluate_expected_care_candidates --live
```

The live command is wholly synthetic and requires `DR_AI_DEEPSEEK_API_KEY`.
Raw responses remain under ignored
`evaluation/expected_care/results/raw/`; sanitized metrics are retained beside
the frozen suite. Register the checksum-bound pending artifact only after
running migrations:

```bash
uv run alembic upgrade head
uv run python -m scripts.register_early_stage_ai_releases
```

FastAPI and PostgreSQL service for the Dr. AI beta foundation and production
v1.0 planning baseline. The historical beta API exposes authentication,
current-user identity, assigned-patient summaries, role-specific synthetic
dashboard reads, read-only synthetic patient-care fixtures, demo upload
presign metadata, deterministic simulated assessment results, recovery plans,
Today tasks, educational chat, asynchronous consultation request/status
readback, and audit metadata events.

Production v1.0 Phase 0, Phase 1, and Phase 2 patient/doctor core workflows
are complete locally. Phase 1 adds schema foundations, fail-closed
specialist/admin role boundaries, route-level RBAC helpers, and authenticated
support/deletion/feedback submission plus requester-scoped status endpoints.
Phase 2 adds persisted demographics, allergies, chronic diseases, visit
history, diagnoses, doctor-note CRUD, expanded care-bundle readback,
doctor-owned medication CRUD, prescription CRUD, medication/refill reminders,
metadata-only in-app queued notification records, production-separated
Tencent-COS-compatible imaging metadata/finalization/review, recovery-plan
review/approval/completion semantics, patient Today progress, neutral denials,
and metadata-only audit events. Specialist/admin workflows, admin
support/deletion/feedback queue handling, external push/SMS/email/native
notification delivery, raw COS file-transfer verification, billing workflows,
analytics dashboards, clinic operations workflows, real AI/model inference,
and real clinical workflows remain unavailable until later production phases
implement and test them.

Use synthetic content only. Do not submit real patient data.

Slice 9A retains BGE-M3 and BGE Reranker v2 M3 as the production-approved
profile. A resource-bounded GTE staging candidate is implemented separately in
`../retrieval_inference`: the pinned multilingual base pair passed local 8-GB
feasibility and the real API embedding contract, but it is not production-
approved and cannot be used by an existing immutable release. The current
production code identifiers retain the initial
Mainland-specific deployment assumption, but Hong Kong is accepted for current
development/staging. Before production activation, runtime configuration must
be reconciled with the explicitly approved Hong Kong-or-Mainland region and its
documented residency, network, privacy/legal, and provider controls. Local
hashing and policy scoring remain deterministic test/degradation fallbacks.
Patient release construction and the final pre-provider handoff independently
re-read effective, unexpired, source-matched
`model_provider_transmission_allowed` rights.

The frozen retrieval suite is
`knowledge_base/evaluation/retrieval_cases.slice9a.v1.json`. The runner refuses
to execute it until its clinician review record is approved:

```bash
uv run python -m scripts.evaluate_slice9a_retrieval \
  --output knowledge_base/release_artifacts/evaluation/slice9a-retrieval.json
```

For a semantic-model migration, first build a non-active candidate from the
active patient corpus. Embeddings are batched and stored on release-passage
snapshots, so the old active release remains a valid rollback point:

```bash
uv run python -m scripts.build_patient_retrieval_candidate \
  --artifact-root knowledge_base/release_artifacts \
  --approver-id <approved-operator>

uv run python -m scripts.evaluate_slice9a_retrieval \
  --candidate-release-id <candidate-uuid> \
  --output knowledge_base/release_artifacts/evaluation/slice9a-<candidate-id>.json

uv run python -m scripts.activate_patient_retrieval_candidate \
  --release-id <candidate-uuid> \
  --evaluation knowledge_base/release_artifacts/evaluation/slice9a-<candidate-id>.json \
  --activated-by <approved-operator>
```

Evaluation switches to the candidate only inside a rolled-back transaction.
Activation refuses a mismatched, unapproved, overwritten, or failing artifact.

Slice 9B keeps clear questions on that original-query path. A resolvable short
reference uses bounded recent user context without another model call;
ambiguous, colloquial, or measured weak retrieval may spend one small schema-
constrained query-planner call. Every rescue remains limited to one retrieval
retry. The server rejects meaning drift and makes the resolved-query result
authoritative for referential/ambiguous rescue. Original rankings may
corroborate only the same passage checksum and cannot introduce final evidence.
Resolved-topic sufficiency, duplicate and source-diversity controls, and
conflict checks are re-evaluated before rescue can report improvement.
Resolution or sufficiency failure returns no eligible evidence for a contextual
query instead of exposing an unrelated original-only result.
The candidate rescue suite has file-backed product-owner, clinical, and native
Simplified Chinese approval dated 2026-07-18. Validation is no-cost; the live
run still requires the approved provider configuration and active release:

```bash
uv run python -m scripts.evaluate_slice9b_retrieval_rescue validate
uv run python -m scripts.evaluate_slice9b_retrieval_rescue preflight
uv run python -m scripts.evaluate_slice9b_retrieval_rescue run \
  --output knowledge_base/release_artifacts/evaluation/slice9b-rescue-v2.json
```

The failed v1 and v2 evidence artifacts remain preserved; the runner refuses to
overwrite an existing artifact. Do not repeat a paid run on the local fallback
ranking stack. First build and pass Slice 9A with a new immutable semantic
release, then use a new Slice 9B output path.

## Local database and environment

PostgreSQL 17 is the development and CI database. Create `dr_ai` and
`dr_ai_test`, copy `.env.example` to the ignored `.env`, and generate unique
local values for the JWT secret and three synthetic seed passwords.

```bash
uv sync --locked --dev
uv run alembic upgrade head
uv run alembic check
uv run python -m app.seed
uv run python -m app.seed
```

The second seed run must report zero newly created users, relationships,
dashboards, records, medications, notes, recovery plans, and recovery tasks.
Demo assets, assessments, task completions, chat threads/messages, rate-limit
rows, consultation requests, and audit events are created by workflow tests or
endpoint calls, not by seeding.

After the three synthetic role accounts exist, install the complete local
Slice E demonstration with:

```bash
uv run python -m scripts.bootstrap_synthetic_expected_care_demo
```

The command is idempotent and restricted to local/test environments. It creates
one wholly synthetic event, delivered service/cost/request scope, one
immutable payer-linked baseline with clinician concurrence, and one separate
published baseline without a clinician response. Doctors cannot edit, reject,
or hide either baseline. The candidate fixture is deterministic and in-process;
it does not call DeepSeek or any external provider.
Seed account emails are:

- `doctor.demo@example.com`
- `patient.demo@example.com`
- `unrelated.patient@example.com`

Passwords are never stored in the repository and must come from environment
configuration.

## API and verification

```bash
uv run ruff check .
uv run pytest -W error
uv run uvicorn app.main:app --reload --no-access-log
```

The access token lifetime defaults to 10 minutes. Refresh tokens are opaque,
rotated on every use, stored only as SHA-256 hashes, and grouped into a
server-revocable session family. Replay revokes the family. Logout revokes the
active refresh session and its access token is rejected by subsequent
authenticated reads.

All non-2xx application responses use the frozen error envelope with a request
ID. Cross-patient and wrong-role resource probes return neutral
`404 not_found`.

Implemented Week 2 and Week 3 endpoints include:

- `GET /api/v1/patients?q=...`
- `GET /api/v1/patients/{patient_id}`
- `GET /api/v1/patients/{patient_id}/records`
- `GET /api/v1/patients/{patient_id}/medications`
- `POST /api/v1/patients/{patient_id}/medications`
- `PUT /api/v1/patients/{patient_id}/medications/{medication_id}`
- `DELETE /api/v1/patients/{patient_id}/medications/{medication_id}`
- `GET /api/v1/patients/{patient_id}/doctor-notes`
- `GET /api/v1/patients/{patient_id}/care`
- `GET /api/v1/patient/me/care`
- `GET /api/v1/medications`
- `GET /api/v1/reminders`
- `GET /api/v1/patient/me/notifications`
- `GET /api/v1/patients/{patient_id}/prescriptions`
- `POST /api/v1/patients/{patient_id}/prescriptions`
- `PUT /api/v1/patients/{patient_id}/prescriptions/{prescription_id}`
- `DELETE /api/v1/patients/{patient_id}/prescriptions/{prescription_id}`
- `GET /api/v1/patients/{patient_id}/medication-reminders`
- `POST /api/v1/patients/{patient_id}/medication-reminders`
- `PUT /api/v1/patients/{patient_id}/medication-reminders/{reminder_id}`
- `DELETE /api/v1/patients/{patient_id}/medication-reminders/{reminder_id}`
- `POST /api/v1/patients/{patient_id}/assets/presign`
- `POST /api/v1/patients/{patient_id}/imaging/presign`
- `POST /api/v1/patients/{patient_id}/imaging/{asset_id}/complete`
- `GET /api/v1/patients/{patient_id}/imaging`
- `GET /api/v1/patients/{patient_id}/imaging/{asset_id}`
- `POST /api/v1/patients/{patient_id}/imaging/{asset_id}/review`
- `GET /api/v1/patient/me/imaging`
- `GET /api/v1/patient/me/imaging/{asset_id}`
- `GET /api/v1/patients/{patient_id}/assessments`
- `POST /api/v1/patients/{patient_id}/assessments`
- `GET /api/v1/patients/{patient_id}/recovery-plans`
- `POST /api/v1/patients/{patient_id}/recovery-plans`
- `PUT /api/v1/patients/{patient_id}/recovery-plans/{plan_id}`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/submit-review`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/request-changes`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/approve`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/complete`
- `GET /api/v1/patient/me/today`
- `POST /api/v1/patient/me/tasks/{task_id}/completion`
- `POST /api/v1/chat/threads/{thread_id}/messages`
- `POST /api/v1/patient/chat/messages`
- `GET /api/v1/consultations`
- `POST /api/v1/consultations`

Doctors can read only active-care assigned patients. Patients can read only
their own records, medications, prescriptions, reminders, metadata-only
notifications, and assessment history; doctor notes are doctor-facing only.
Doctors can run simulated assessments for assigned patients. Patients cannot
run assessments. Cross-patient and wrong-role probes remain neutral
`404 not_found`.

The patient-chat endpoint keeps conversation content in the client session and
follows the Phase 3 bounded RAG workflow. It routes emergencies and prohibited
requests before retrieval or generation, retrieves only from the active
patient-approved immutable release, calls DeepSeek only after sufficient
evidence, validates structured output and passage citations, and records only
content-free `chatbot_events`. Colloquial Chinese and English symptom
paraphrases are normalized into bounded clinical concepts for routing and
retrieval. Patient evidence requires the same primary symptom concept to be
central to the source metadata, rather than an incidental passage mention, plus
meaningful topic coverage; authority, dense similarity, and result count alone
cannot make off-topic evidence sufficient. Malformed structured output receives
one bounded repair attempt containing the complete JSON Schema and content-free
field-level validation issues. Only the diagnostic subtype and attempt count are
added to telemetry. For relevant questions, a server-side context
broker selects bounded profile, measurement, condition, medication, Clinical
Event, or recovery-plan fields and validates every model-used context ID. The
response exposes only server-derived context category, provenance, and date
cards alongside the answer. Without an active patient release it returns the
fixed retrieval fallback; without `DR_AI_DEEPSEEK_API_KEY` it returns the fixed
provider fallback.

Retrieval-rescue telemetry is content-free: trigger category, attempted flag,
outcome, planner model, provider-reported token/cache counts when present,
latency, configured-price cost, retrieval delta, and retry request ID. It never
stores the original question, candidate rewrite, concepts, synonyms, recent
conversation, prompt, response, or passage text.

The locally reviewed 55-document Chinese corpus can be promoted and its
content-addressed patient release activated idempotently with:

```bash
uv run python -m scripts.activate_open_patient_education_release \
  --reviewer-id product-owner-confirmed-unspecified \
  --confirm-all-55-patient-approved
```

The active local manifest contains 55 source versions and 426 passages. Keep
`DR_AI_DEEPSEEK_API_KEY` only in the ignored server `.env`; it must never enter
Flutter, source control, command output, or chatbot telemetry.

After the complete 697-entry HPA corpus has been imported and human review is
confirmed, promote it and activate a combined immutable patient release with:

```bash
uv run python -m scripts.activate_hpa_health_myths_release \
  --confirm-all-697-human-reviewed
```

Slice 6 adds an offline governed-source worker for NHC and China CDC freshness
monitoring. Synchronize the checked-in allowlist and inspect status with:

```bash
uv run python -m scripts.manage_online_sources sync
uv run python -m scripts.manage_online_sources status
```

`poll` performs bounded allowlisted network reads outside the patient request
path and records changes only in quarantine. Both pilot families remain
metadata-only and rights-pending, so polling cannot store article text or
change the active patient release. Source-family kill switches are enforced by
retrieval even when a source is already present in an immutable release.

Doctors can create, edit, and delete medication entries, prescriptions with
medication lines, and medication/refill reminders only for assigned patients.
Active medication/refill reminders create metadata-only in-app queued
notification rows for the patient account. The backend does not call external
SMS, email, push, or native local-notification services in this slice.
Medication, prescription, reminder, notification, and audit metadata stores
resource IDs, statuses, counts, reminder type, and channel only; it does not
copy medication names, dosages, schedules, notes, prescription notes, or
reminder labels into audit or notification metadata.

Doctors and patients can prepare and complete imaging uploads only inside
their assigned/own patient boundary. The Phase 2 imaging workflow stores
Tencent-COS-compatible metadata, upload status, review status, and byte counts;
it does not fetch files from COS, inspect image contents, run model inference,
or create clinical interpretation. Doctors can mark completed imaging metadata
as reviewed or rejected. Imaging audit metadata stores actor role, content
type, byte counts, storage provider, upload status, review status, and boolean
checksum/ETag presence only; it does not copy filenames, object keys, upload
URLs, ETags, checksums, image contents, or review notes.

Doctors can create, edit, submit for review, request changes, approve,
activate-compatible, and complete synthetic recovery plans only for assigned
patients. Patients can read only their own active Today tasks and can complete
only their own active tasks. Recovery-plan and completion audit events record
metadata such as status, review status, task counts, completed counts,
category, source transition, and plan/task IDs; they do not copy plan titles,
patient-owned plan instructions, task titles, or task details into audit
metadata.

Educational chat accepts patient question-preparation prompts only. Red-flag
phrases bypass DeepSeek and return the fixed emergency guidance. Unsafe prompts
and DeepSeek timeout/malformed/quota failures return bounded fallback messages;
malformed structured output receives one schema-guided repair attempt first.
Local/test
environments and unset DeepSeek keys use the safe fallback path. Chat audit and
storage record metadata only, such as prompt hash, length, fallback category,
model label, diagnostic subtype, and attempt count; raw prompts and raw model
output are not stored.

Doctors can create asynchronous synthetic specialist-consultation requests
only for assigned patients. Doctors and patients can list only consultations
they are authorized to see. Repeating the same requested consultation for the
same doctor and patient returns the existing request instead of creating a
duplicate. Consultation audit metadata records specialty, priority, status, and
IDs without copying the request summary.

Demo upload presign is metadata-only in Week 2. It accepts `image/png`,
`image/jpeg`, and `application/dicom` metadata up to `10485760` bytes, checks
filename extension consistency, returns `415 unsupported_media_type` for
unsupported media types, and returns `413 payload_too_large` for oversized
metadata.

Week 4 Days 16-17 hardening status: local validation and log-hygiene coverage
now verifies that credentials, refresh tokens, authorization headers, upload
filenames, raw chat prompts, unsafe consultation summaries, and DeepSeek keys
do not appear in captured application logs. `uv pip check` is the repo-scoped
dependency compatibility check for this service; `uv run pip check` can inspect
unrelated ambient packages on this machine because the API venv intentionally
does not install `pip`.

Day 10 gate status: the local repository verifies the doctor
patient -> record -> upload -> assessment -> result path, neutral unrelated
patient denial, and upload/assessment failure recovery without losing form
data. Staging deployment is not updated by the Day 10 polish pass unless a
separate staging task is requested.

Week 3 Day 15 status: the local repository verifies the full doctor-led loop
across doctor and patient accounts, chat safety fixtures, duplicate
consultation reuse, consultation request/status readback, and
wrong-role/cross-patient denial. Real notifications and staging deployment are
not updated by this phase unless separately requested.

Week 4 Days 16-17 did not touch Tencent staging, production deployment,
administrator audit reads, real COS upload completion, or real clinical
workflows.

Week 4 Days 18-20 local release prep does not add API endpoints and does not
touch Tencent staging, production deployment, TestFlight, Android closed
testing, web deployment, tags, tester invites, monitoring/account settings, or
real data deletion. The Flutter Beta support account-deletion and feedback
controls still prepare local drafts only until the Flutter surface is wired to
the Phase 1 backend support endpoints.

Phase 1 status: migration `20260707_0006` adds production
foundation tables for hospitals, clinics, role assignments, doctor teams,
clinic resources/equipment, appointments/bookings, prescriptions/medication
reminders, notifications, invoices/payment statuses/revenue summaries,
analytics events, and support/deletion/feedback queue requests. The existing
synthetic seed flow does not populate those production foundation tables.
Backend `specialist` and `admin` enum values exist for RBAC preparation, but
registration for those roles fails closed and unsupported roles cannot use the
beta dashboard or support-request routes. Authenticated doctors and patients
can submit support, deletion, and feedback queue requests and read only their
own request statuses. Admin-managed support queue handling remains Phase 5.

Current production planning and Phase 0 closure evidence live in
`../../docs/Dr_AI_v1.0_Implementation_Plan.md` and
`../../docs/Phase_0_Production_v1_Closure_Record.md`; the Phase 1 foundation
is recorded in `../../docs/Phase_1_Production_Data_Foundation_Record.md`.
Historical beta records live under `../../docs/beta/`.

## Web hosting and CORS

The first beta should prefer same-origin hosting: serve the Flutter web build
and reverse-proxy `/api/*` to FastAPI from the same HTTPS origin. In that mode,
leave `DR_AI_CORS_ALLOWED_ORIGINS=[]`.

If the web app must be hosted on a separate HTTPS origin, set
`DR_AI_CORS_ALLOWED_ORIGINS` to the exact allowed origin JSON array, for example
`["https://dr-ai-web.example.test"]`. Wildcard CORS is rejected for staging and
production. Do not enable credentials-based browser cookies; the Week 1 client
uses bearer access tokens and a locally stored refresh token.

## Container

`Dockerfile` builds the locked API image and disables HTTP access logs. Run
migration and synthetic seeding as explicit one-off release tasks before
starting the service. Tencent staging instructions live in
`../../deploy/tencent/staging/`.
