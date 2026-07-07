# Week 2, Days 8-9 Closure Record

Recorded: 2026-07-05

Status: complete for repository implementation and local verification.

Tencent staging status: not touched in this phase.

## Closure outcome

Week 2 Days 8-9 implemented the approved demo upload and simulated assessment
slice without starting DeepSeek chat, recovery plans, reminders, consultation,
real COS upload completion, real AI/model inference, or real clinical
workflows. All content remains synthetic demonstration content only.

Branch: `codex/week1-days3-5`

Draft stacked PR #2 remains:
<https://github.com/harryXiaoCao/Dr_AI_Product/pull/2>

PR #1 and PR #2 were not merged.

## Schema and migration

New migration revision: `20260705_0003`

Migration file:
`services/api/migrations/versions/20260705_0003_week2_upload_assessment_audit.py`

The migration creates:

- `demo_medical_assets`
- `simulated_assessments`
- `audit_events`

Every new patient-owned object carries `patient_id`. Simulated assessments also
carry `actor_user_id` and an idempotency key. Audit events store metadata only;
they do not store upload URLs, tokens, passwords, or patient-owned content.

## Implemented API paths

Week 2 Days 8-9 added:

- `POST /api/v1/patients/{patient_id}/assets/presign`
- `GET /api/v1/patients/{patient_id}/assessments`
- `POST /api/v1/patients/{patient_id}/assessments`

Authorization rules:

- Doctors can presign demo uploads only for active-care assigned patients.
- Patients can presign demo uploads and list assessment results only for their
  own patient profile.
- Doctors can run deterministic simulated assessments for assigned patients.
- Patients cannot run assessments.
- Wrong-role and cross-patient probes remain neutral `404 not_found`.

## Simulated assessment behavior

The assessment service is fixture-based and deterministic. It currently accepts
only server-owned synthetic fixtures such as `synthetic_lung_case_001` and
returns the frozen response shape with:

- `mode: simulated`
- `status: completed`
- risk band and unitless demo score
- input completeness
- `fixture-simulator-1.0.0`
- persistent `Research simulation - not for diagnosis.`
- limitations and safe next steps

The demo score is not a probability, diagnostic confidence, validated model
output, or clinical recommendation.

## Flutter behavior

Doctor-facing Week 2 Days 8-9 UI was added under Patient Management after the
Days 6-7 profile, history, medication, and doctor-note sections:

- demo image upload metadata form;
- upload prepared state with synthetic-only object key and expiry;
- simulated assessment fixture selector;
- simulated assessment loading, validation, network/error, empty-history, and
  result states;
- persistent simulation and synthetic-data labels;
- result panel with risk band, demo score, completeness, fixture/model version,
  limitations, and safe next steps.

Patient-side display remains limited to assessment read access through the API
contract. No Week 3 recovery, reminder, chat, or consultation UI was added.

## Local verification evidence

Recorded after the Days 8-9 completion audit on 2026-07-05.

| Check | Result |
|---|---|
| Backend targeted tests | Passed: `12 passed` for `tests/test_week2_upload_assessment.py`, `tests/test_patient_care_loop.py`, and `tests/test_migrations_and_seed.py` |
| Backend Ruff | Passed: `All checks passed!` |
| Alembic upgrade | Passed: upgraded local database to `20260705_0003` |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| Flutter verification | Passed: `./scripts/verify_flutter.sh`; analysis clean and `15` widget/golden tests passed |
| Whitespace check | Passed: `git diff --check` |

## Remaining Week 2 work

Approved next scope is the Day 10 gate only:

- verify doctor patient -> record -> upload -> assessment -> result;
- verify no client can access an unrelated patient by changing an ID;
- verify upload and assessment failure states recover without losing form data.

Do not implement DeepSeek chat, recovery-plan workflows, reminders,
consultations, real AI assessment, real patient data, or clinical behavior in
the Day 10 gate.
