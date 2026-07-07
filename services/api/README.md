# Dr. AI API

FastAPI and PostgreSQL service for the invited Dr. AI beta. Week 1 exposes
authentication, current-user identity, assigned-patient summaries, and
role-specific synthetic dashboard reads. Week 2 exposes read-only synthetic
patient-care fixtures, demo upload presign metadata, deterministic simulated
assessment results, and audit metadata events. Week 3 Days 11-12 exposes
synthetic recovery plans, Today tasks, and task completion tracking. Week 3
Days 13-14 exposes educational chat and asynchronous specialist-consultation
tracking. Week 4 Days 16-17 hardening trims string request fields before
validation, rejects unsafe consultation specialty and summary text, and expands
log-hygiene checks across auth, refresh, upload, chat, and consultation flows.
Week 4 Days 18-20 release prep adds Flutter/doc surfaces only; it does not
change the API contract. Real COS upload completion, real AI/model inference,
and real clinical workflows remain unavailable.

Use synthetic content only. Do not submit real patient data.

## Local database and environment

PostgreSQL 17 is the development and CI database. Create `dr_ai` and
`dr_ai_test`, copy `.env.example` to the ignored `.env`, and generate unique
local values for the JWT secret, invite codes, and three synthetic seed
passwords.

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
- `GET /api/v1/patients/{patient_id}/doctor-notes`
- `GET /api/v1/patients/{patient_id}/care`
- `GET /api/v1/patient/me/care`
- `GET /api/v1/medications`
- `POST /api/v1/patients/{patient_id}/assets/presign`
- `GET /api/v1/patients/{patient_id}/assessments`
- `POST /api/v1/patients/{patient_id}/assessments`
- `GET /api/v1/patients/{patient_id}/recovery-plans`
- `POST /api/v1/patients/{patient_id}/recovery-plans`
- `PUT /api/v1/patients/{patient_id}/recovery-plans/{plan_id}`
- `POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate`
- `GET /api/v1/patient/me/today`
- `POST /api/v1/patient/me/tasks/{task_id}/completion`
- `POST /api/v1/chat/threads/{thread_id}/messages`
- `GET /api/v1/consultations`
- `POST /api/v1/consultations`

Doctors can read only active-care assigned patients. Patients can read only
their own records, medications, and assessment history; doctor notes are
doctor-facing only. Doctors can run simulated assessments for assigned
patients. Patients cannot run assessments. Cross-patient and wrong-role probes
remain neutral `404 not_found`.

Doctors can create, edit, and activate synthetic recovery plans only for
assigned patients. Patients can read only their own active Today tasks and can
complete only their own active tasks. Recovery-plan and completion audit events
record metadata such as status, task count, category, and plan/task IDs; they
do not copy patient-owned plan instructions or task details into audit
metadata.

Educational chat accepts patient question-preparation prompts only. Red-flag
phrases bypass DeepSeek and return the fixed emergency guidance. Unsafe prompts
and DeepSeek timeout/malformed/quota failures return bounded fallback
messages. Local/test environments and unset DeepSeek keys use the safe fallback
path. Chat audit and storage record metadata only, such as prompt hash, length,
fallback category, and model label; raw prompts and raw model output are not
stored.

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
controls prepare local drafts only.

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
