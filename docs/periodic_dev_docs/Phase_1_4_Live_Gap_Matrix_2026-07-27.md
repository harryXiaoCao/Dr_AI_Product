# Phase 1-4 Live Gap Matrix

Date: 2026-07-27

Status: closed local implementation record; external conditions listed below

This matrix was rebuilt from the current repository, source-of-truth documents,
tests, migrations, Flutter routes and controls, and the rendered-product
evidence. It does not replace immutable Slice A-G records. A row is closed only
after its implementation and executable evidence pass.

## Phase 1

| Area | Live evidence | Gap or decision | Status |
|---|---|---|---|
| Unsupported roles | Registration, API authorization, Flutter role mapping, and routing fail closed for `specialist` and `admin`; obsolete team/admin controls were removed. | None in the Phase 1-4 product boundary. | Complete |
| Ownership and role isolation | Doctor-patient, exact payer request/organization, chat thread, fact snapshot, imaging byte, and download scope checks fail closed with regression coverage. | None locally. | Complete |
| Idempotency and concurrency | Comparison, explanation, release, payer review, and doctor response mutations use content-bound idempotency, expected versions, row/advisory locks, and conflict responses. | None locally. | Complete |
| Audit and redaction | New clinical, imaging, payer, support, and governance transitions retain attributable, content-minimized audit/history metadata; tests reject secrets and unnecessary clinical copy. | None locally. | Complete |
| Migrations and schema drift | Linear migrations through `20260727_0051`; base-to-head, `0051 -> 0050 -> 0051`, `alembic current`, and `alembic check` pass. The pre-existing knowledge-rights/source cycle warning remains documented. | None introduced by this work. | Complete |

## Phase 2

| Area | Live evidence | Gap or decision | Status |
|---|---|---|---|
| Clinical Event workflow | The `phase4-combined-product-path-v2` fixture executes symptoms/history, imaging and doctor findings, prescriptions/medications, recovery, consultation/laboratory/imaging/rehabilitation/treatment services and costs, baseline, comparison, justification, exact payer request, clarification, and manual acceptance through real routes. | None locally. | Complete |
| Patient destinations | Records, Imaging, Medications, Recovery, Care & Cost, Contacts, and Account are persisted destinations with authorized read/download and state handling. | None locally. | Complete |
| Imaging upload/download | Migration `0051` and the storage boundary provide byte upload/finalization, MIME/size/checksum validation, expiry/replay/conflict handling, retry, immutable provenance, authorized download, and fail-closed Tencent COS configuration. | A real COS transfer awaits the next credentialed staging deployment; local byte-path behavior is executable. | Complete locally |
| Doctor justification | Append-only, versioned, reviewer-attributable doctor responses bind the exact payer request and comparison/baseline lineage. | None locally. | Complete |
| Payer transitions | Valid manual transition state machine, expected version, content-bound idempotency, row locks, reviewer attribution, and visibly distinct transition history are implemented. | None locally. | Complete |
| Visible controls | Route/control audit removed obsolete team/demo controls; legal/support/AI unavailable states use truthful copy. EN/zh expected-care goldens, actual web rendering, mobile/desktop layouts, keyboard/accessibility and state tests pass. | One unrelated historical doctor-resource golden differs by 1.39-1.86% across the current host renderer; functional and accessibility checks pass and immutable historical pixels were not rewritten. | Complete with documented renderer variance |

## Phase 3

| Area | Live evidence | Gap or decision | Status |
|---|---|---|---|
| DeepSeek answer path | DeepSeek is the only v1 generated provider; migration `0050` adds checksum-bound release/readiness, default-off enablement, default-on kill switch, immutable events, and exact rollback. Deterministic boundaries remain product-owned. | Live activation requires a credentialed, checksum-compatible controlled-stage run. | Complete locally; staging blocked |
| Thread lifecycle | Create/list/open/history/archive/reopen/retention-preserving delete, sources, limitations, failure/retry, and neutral cross-patient behavior are persisted and tested. | None locally. | Complete |
| Bounded patient context | Selection is role-authorized, question-bounded and capped; UI discloses only used categories/provenance/date, and frozen real-route tests prove privacy and cross-patient isolation. | None locally. | Complete |
| Evaluation and rollback | `evaluation/chatbot/` retains an 11-gate real-product-path suite covering bilingual, privacy, injection, malformed output, timeout, quota, outage, drift, cross-patient access, kill switch, and exact rollback. | No DeepSeek credential or final deployment access was present for a paid controlled-stage run. | Complete locally; external evidence blocked |

## Phase 4

| Area | Live evidence | Gap or decision | Status |
|---|---|---|---|
| Slices A-G | Candidate and explanation purposes, immutable baselines/comparisons, deterministic validation, append-only release history, kill switches, rollback, paid passing/failing evaluations, Flutter role views, and controlled Tencent evidence are real and preserved. | Do not rewrite or conflate their evidence. | Preserved complete |
| DeepSeek Vision | No Vision purpose is enabled or implemented. Current official DeepSeek V4 API documentation describes the model as text-only and its integration vision behavior as a proxy through another provider. | Per the task instruction, leave Vision unimplemented rather than violating the DeepSeek-only product contract. Re-evaluate only when an official DeepSeek image-input API is available. | Externally blocked |
| Exact cost fact object | The server builds the immutable, event-scoped fact object from symptoms, history, imaging drafts, doctor findings, prescriptions, medication taken, recovery, consultations, laboratory/imaging/rehabilitation/treatment services, quantities, units, dates, and costs; it classifies used/not-used/missing facts with provenance and role-safe views. | None locally. | Complete |
| Synthetic combined event | The combined real-route fixture covers all required clinical/cost categories, missing/conflicting data and alternative pathways, through baseline, comparison, fallback, justification, and manual payer decision. | None locally. | Complete |
| Role transparency | Doctor, patient, and payer see authorized facts used/not used/missing, synthetic references/effective dates, assumptions, uncertainty/range, submitted amount, comparison, explanation/fallback, response, and history. | None locally. | Complete |

## Verification Baseline

- Full backend suite: passed after upgrade through `0051`.
- Migrations: base-to-head, downgrade/re-upgrade, current/head, and schema-drift
  checks passed.
- Flutter: formatting, analysis, 79 functional/accessibility tests, seven
  expected-care goldens, web release build, and actual EN/zh mobile/desktop
  rendered inspection passed.
- Real-route synthetic doctor/patient/payer journey and all 11 chatbot product
  gates passed.
- Public Tencent health/security-header checks passed against the prior `0047`
  deployment. Final-source deploy/authenticated smoke is externally blocked by
  absent staging credentials.
- Android debug build is externally blocked because the configured SDK resides
  on the unmounted `/Volumes/AndroidAVD` volume.
