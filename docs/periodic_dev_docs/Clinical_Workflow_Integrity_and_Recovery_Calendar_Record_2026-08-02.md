# Clinical Workflow Integrity and Recovery Calendar Record

Date: 2026-08-02
Scope: local wholly synthetic development

## Delivered

- Added migration `20260802_0058` for structured consultation/service metadata,
  prescription version integrity, and recovery phases/tasks.
- Kept the Consultation section as the specialist-referral request workflow.
  Added ordinary treating-doctor consultation, encounter-update, and diagnosis
  append actions plus consultation/list readback under the selected Clinical
  Event, fixing the previously empty doctor-record lists.
- Kept clinical records separate from unique `care_cost_items` companions.
  `pending_cost` saves remain valid and payer submission remains fail-closed.
- Added atomic multi-medication prescriptions, finalization immutability,
  explicit replacement lineage, content checksums, and actor-scoped idempotency.
- Added ordered recovery calendar phases, typed scheduled tasks, clinician
  checkpoints, progress separation, published immutability, and revisions.
- Normalized patient-account dropdowns to canonical values independently from
  English/Simplified Chinese labels, including the exact saved value `female`.
- Retained deterministic chat safety first, preferred approved retrieval, and
  added visibly labeled bounded `general_model_knowledge` plus useful fixed
  provider-failure guidance for an acute joint injury question.

## Verification evidence

- Focused backend clinical, cost, recovery, consultation, chat, governance,
  authorization, immutability, idempotency, and concurrency tests passed.
- The broader FastAPI suite and Ruff checks passed after the specialist-referral
  versus treating-doctor consultation correction.
- Migration downgrade to `0057`, re-upgrade to `0058`, current-head check, and
  Alembic drift check passed. The existing KB cyclic-FK sorting warning remains.
- The exact narrow-width `female` widget regression, doctor recovery-calendar,
  consultation, and clinical-service widget regressions passed.
- Flutter analysis passed through an ASCII temporary path; direct analysis from
  the repository's Chinese path hits a Flutter LSP JSON framing bug.
- The final Flutter verifier passed 115 tests with 23 repository-defined skips.
  Rendered Chinese desktop and 412x917 mobile views showed the three Clinical
  Event append modes without overflow; a fresh corrected browser tab had no
  error/warning logs. `git diff --check` passed.
- The running local API reported schema `20260802_0058` and patient-chat
  generation `ready` for governed purpose `patient_chat_generated_answer`,
  release `v1-synthetic-2026-07-27`, model `deepseek-v4-flash`.

## Explicit limits

No real patient data or live payer system was used. This record does not claim
clinical validation, official pricing, payer acceptance, privacy/security
certification, legal/regulatory approval, real-patient authorization, or
public-production readiness.
