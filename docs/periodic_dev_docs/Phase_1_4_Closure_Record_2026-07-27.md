# Phase 1-4 Closure Record

Date: 2026-07-27

Status: local synthetic product foundation complete; external conditions
truthfully retained

## Outcome

Phases 1-4 now form one coherent synthetic product foundation. Existing Slice
A-G work and immutable passing and failing evidence were preserved. The
implementation closes the current patient, doctor, payer, clinical-event,
support, chatbot, imaging-byte, expected-care, comparison, explanation, and
governance work without beginning the dedicated Phase 5 refinement backlog or
Phase 6 notification delivery.

The live gap matrix is
`docs/periodic_dev_docs/Phase_1_4_Live_Gap_Matrix_2026-07-27.md`.

## Completed implementation

- Phase 1 fails closed for unsupported roles and ambiguous payer memberships.
  Sensitive reads and mutations enforce patient, care-relationship, exact payer
  request, and active-organization scope. New payer/release transitions use
  expected versions, content-bound idempotency, locks, attribution, append-only
  history, and content-minimized audit data.
- Migrations `0048`-`0051` add chat lifecycle, payer transition safety,
  chatbot release governance, and imaging-byte provenance without rewriting
  earlier migrations or evidence.
- Phase 2 has a real-route three-party episode from symptoms/history through
  records, imaging, prescriptions/medications, recovery, services/costs,
  immutable baseline, comparison, doctor justification, exact payer request,
  clarification, and manual reviewer outcome.
- Patient Records, Imaging, Medications, Recovery, Care & Cost, Contacts, and
  Account are persisted destinations. Imaging supports real local byte
  transfer, finalization, checksum/MIME/size/expiry validation, retry,
  immutable provenance, and authorized download. Tencent COS configuration
  fails closed instead of returning a fake upload URL.
- Phase 3 persists thread creation, history, reopen, archive, retention-safe
  deletion, sources, limitations, bounded record-category disclosure, and
  failure/retry states. DeepSeek is the only generated-answer provider and is
  independently release/checksum/kill-switch/rollback governed; deterministic
  emergency, privacy, authorization, retrieval, validation, and medication
  boundaries remain product-owned.
- Phase 4 builds the exact event-scoped cost-estimation fact object on the
  server. Imaging drafts and doctor-confirmed findings remain separate; doctors
  retain ownership of findings and diagnoses. Authorized roles see used,
  not-used, and missing facts, provenance, synthetic references/effective
  dates, assumptions, uncertainty/range, submitted amount, comparison,
  explanation/fallback, response, and history.
- `phase4-combined-product-path-v2` exercises rehabilitation, laboratory,
  imaging, consultation, medication, prescription, recovery, and treatment
  combinations, including missing/conflicting facts and alternatives. Cost
  differences produce review and justification opportunities only; every payer
  outcome remains a manual attributed action.

All identities, organizations, medical information, images, references, prices,
services, requests, and reviewer actions used in development and evidence are
synthetic.

## Verification evidence

- Complete backend suite: passed.
- Focused authorization, comparison, payer, imaging, and combined-journey
  suite: 37 tests passed.
- Migration base-to-head, `0051 -> 0050 -> 0051`, `alembic current`,
  `alembic heads`, and `alembic check`: passed. The pre-existing
  `kb_rights_records`/`kb_sources` cycle warning remains and no new schema
  operation was proposed.
- Chatbot frozen product-path evaluation: all 11 bilingual, privacy, injection,
  malformed-output, timeout, quota, outage, context-drift, cross-patient,
  kill-switch, and rollback gates passed. The latest retained result is
  `evaluation/chatbot/results/20260726T164729Z.sanitized.json`.
- Candidate and explanation deterministic runners execute directly and retain
  new no-provider/fallback observations. Earlier paid passing and failing
  artifacts remain immutable.
- Flutter format and analysis passed; 79 runnable functional/accessibility
  tests passed, with 15 intentionally skipped general pixel cases in the
  repository verifier.
- Seven expected-care tests passed, including English doctor desktop,
  Simplified-Chinese patient mobile, and English payer desktop exact goldens.
  Keyboard traversal, semantic controls, enlarged-text narrow layout, loading,
  empty, unavailable, conflict, retry, fallback, replay, and history behavior
  passed.
- Flutter web release build passed. Actual built-web inspection at 1280x832 and
  412x917 confirmed responsive Simplified-Chinese rendering, expected fonts,
  and no console warning/error. English role rendering was additionally
  inspected through the passing exact goldens.
- The public Tencent staging health endpoint and root/security headers remain
  healthy on the existing `0047` deployment.

One historical doctor-resources golden, outside the modified Phase 1-4
surfaces, differs by 1.39% on desktop and 1.86% on Simplified-Chinese mobile
under the current host renderer. Its functional/accessibility tests pass. The
historical pixels were not rewritten merely to mask a renderer variance; the
generated failure images were moved to
`/tmp/dr_ai_doctor_resources_golden_failures_20260727`.

## External conditions

### DeepSeek image input

The separately governed Vision purpose remains absent and disabled. Current
official DeepSeek documentation describes DeepSeek V4 as text-only and does
not expose public image input. Its documented integration workaround sends
images through another provider, which would violate the product's
DeepSeek-only generative/multimodal rule. Per the task instruction, no proxy,
fake Vision draft, or fabricated release evidence was created. Manual imaging
upload and doctor-owned findings remain fully usable.

### DeepSeek release assurance

Paid calls were authorized, but neither `DEEPSEEK_API_KEY` nor
`DR_AI_DEEPSEEK_API_KEY` was present. The current source also intentionally
differs from the earlier immutable pending releases after authorization and
fact-object integration:

- candidate current `40a6376f...`; pending v1 `b322595d...`;
- explanation current `9bc95f2f...`; pending v3 `bb0c939d...`;
- comparison current `7a59a276...`; pending v3 `ffc94ec...`.

Those earlier releases remain valid historical evidence but cannot activate
the current source. A new paid, checksum-compatible successor evaluation and
release is required before activation; deterministic validation and fallback
remain available meanwhile.

### Controlled Tencent staging

The current process had no staging account passwords, host/deployment
credentials, or registry authority. Therefore the final source could not be
backed up, deployed, migrated from `0047` to `0051`, or exercised through an
authenticated controlled-stage three-role smoke. The existing public staging
state was checked read-only and was not represented as final-source evidence.

### Android build

The web build passed, but the Android debug build could not start because the
configured SDK points to `/Volumes/AndroidAVD/sdk` and that external volume was
not mounted. JDK 21 is present. No duplicate multi-gigabyte SDK was downloaded
to the internal disk.

These are concrete external conditions, not deferred local implementation
items. Phase 5 and Phase 6 remain unopened.
