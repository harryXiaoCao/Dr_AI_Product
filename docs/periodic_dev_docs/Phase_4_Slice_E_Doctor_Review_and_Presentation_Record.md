# Phase 4 Slice E Immutable Baseline And Presentation Record

Date: 2026-07-26
State: revised locally for synthetic/stub-controlled use

## Outcome

Slice E publishes a deterministically validated expected-care candidate as a
separate immutable system baseline. A doctor cannot approve, edit, reject,
unpublish, or hide it. The doctor may append an attributable position:
`acknowledge`, `concur`, `disagree`, or `exception`. Payer reimbursement
adjudication remains a separate human workflow. Slice E calls no model or
external provider.

## Persistence And Authority

Migration `20260726_0042` remains the append-only audit foundation. Migration
`20260726_0043`:

- preserves prior approve/edit/reject artifacts as legacy immutable history;
- permits a system-published baseline with no doctor-decision foreign key;
- retains immutable baseline items, clinician responses, rationales, and
  lifecycle evidence; and
- keeps the transaction-locked head only for optimistic response concurrency.

Migration `20260726_0044` performs an idempotent, model-free backfill for
pre-existing candidates that already passed deterministic validation and whose
persisted item sums still match their integer-minor-unit totals. Read routes
never publish or mutate data.

The published baseline preserves the original candidate checksum,
purpose/schema/prompt/configuration versions, exact release
IDs/versions/checksums, assumptions, limitations, missing information, and
deterministically calculated integer-minor-unit item and total ranges.
`candidate_modified=false` is persisted and returned. Database triggers reject
application-level update/delete of candidates, baselines, items, responses,
rationales, and lifecycle events.

Immediately before accepting a clinician response, the server re-authorizes the
doctor-patient relationship and exact Clinical Event, verifies any immutable
payer-request binding, resolves the current active releases, compares exact
lineage/checksums, reruns deterministic validation, and reconciles the baseline
items and totals. Response input accepts no replacement item, quantity, code,
unit, currency, amount, total, or reference selection.

## Routes And Visibility

Doctors can list/read published baselines, append clinician responses, and read
immutable candidate/baseline/response history. Patients can read a patient-safe
validated baseline even when no clinician response exists. Authorized payer
reviewers can read a payer-linked baseline only through the exact immutable
request and active organization membership.

Patient and payer responses exclude provider prompts/raw output,
reviewer-only notes, content-free diagnostics, credentials, confidential rate
identifiers, and suspicion labels. Patient-safe clinician comments are shown
separately from the baseline. Payer presentation separates candidate,
deterministic validation, baseline, clinician response, submitted facts, and
human payer state. It provides no clinical approval or automated reimbursement
control.

## Flutter Presentation

The doctor workspace labels the range as an immutable system baseline, exposes
its admitted references/effective dates and deterministic evidence, and offers
only acknowledge, concur, disagreement, and exception actions. The patient
surface explains that the baseline cannot be hidden by a clinician and is not
a prescription, quote, bill, coverage decision, reimbursement amount, or final
patient responsibility. The payer surface shows the same baseline and
clinician position beside submitted facts and the separate payer workflow.

English and Simplified Chinese surfaces remain responsive and accessible.
Golden images cover doctor desktop `1280x832`, Chinese patient mobile
`412x917`, and payer desktop `1280x832`.

## Interactive Local Demonstration

The local/test-only idempotent bootstrap makes no network or model call and
creates:

- one wholly synthetic Clinical Event;
- one delivered synthetic Clinical Service and cost companion;
- one immutable payer request and submitted line snapshot;
- one payer-linked published baseline with clinician concurrence; and
- one published baseline with no clinician response.

The same doctor, patient, and payer navigation entry points remain available.
The fixture demonstrates that patient visibility does not depend on doctor
approval and that disagreement or exception records do not alter baseline
items or totals.

## Verification

- focused candidate/baseline API suite: `29/29` passed;
- full API suite: passed at `100%` with warnings treated as errors;
- Flutter Slice E goldens plus main widget suite: `63/63` passed;
- repository Flutter verifier: analysis clean, `72` functional tests passed,
  `15` unrelated CI-mode goldens skipped;
- all three revised role-specific golden images were inspected;
- Python compile and focused Ruff checks passed;
- migrations `0043` and `0044` upgraded successfully; Alembic reports no
  schema drift (apart from the pre-existing knowledge-base cycle warning);
- the Flutter analyzer still crashes before diagnostics on the checkout's
  Chinese path; compilation and widget tests provide the current source check.

Live inspection of the synthetic doctor account confirmed the revised
desktop controls and the responsive `412x917` layout. The inspection exposed
and then verified the repair of a seven-pixel candidate-rail overflow; the
final rendered state has no overflow indicator.

## Slice F/G Reconciliation

Slices F/G now implement deterministic comparison against delivered/submitted
facts and a separately governed validated-explanation purpose. Neither
baseline display nor deterministic comparison requires clinician approval or
concurrence; clinician responses remain separate attributable evidence.

The remaining blocks are usable reviewed China reference releases, the named
clinical/pricing/native-Chinese/privacy/security/legal/payer/regulatory
reviews, real-data authorization, external deployment, and production
activation. The locally registered explanation release remains pending and
kill-switched.
