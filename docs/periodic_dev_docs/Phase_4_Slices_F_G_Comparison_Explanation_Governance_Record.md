# Phase 4 Slices F/G — comparison, explanation, and governance record

Date: 2026-07-26

Status: complete for wholly synthetic development and controlled staging.
Real-patient, real-provider, live-payer, public-production, and commercial use
remain separately gated.

## Corrected explanation boundary

Slice F keeps the immutable baseline, deterministic comparison, clinician
response, submitted facts, generated explanation, and human payer state as
separate layers. Comparison does not require clinician concurrence.

The original free-prose explanation contract was unsuitable because identical
citations could accompany contradictory English and Chinese protected values.
The corrected contract is:

- purpose contract `expected-care-role-explanation-purpose.v2`;
- claim-graph schema `expected-care-role-explanation-claim-graph.v2`; and
- prompt `expected-care-role-explanation-prompt.v3`.

DeepSeek can select only admitted fact IDs, one controlled claim type per
section, and allow-listed connective language. The server owns currencies,
integer minor-unit amounts, quantities, units, dates, percentages, codes,
comparison labels, reference/effective dates, names, and identifiers. English
and Simplified Chinese are rendered from the same canonical claims. Exact
reconstruction validation rejects independent prose, protected-value mutation,
unsupported entities, bilingual disagreement, sensitive fields, prompt
injection, and prohibited clinical or payer conclusions. Failure produces the
structured server-owned fallback without hiding the baseline or comparison.

Adversarial tests cover USD-for-CNY substitution; altered amount, quantity,
unit, date, percentage, code, and comparison label; bilingual contradiction;
unsupported person/organization/hospital/payer/clinician names; UUID, email,
reviewer-note, confidential-identifier, and internal-code leakage; prompt
injection; and prohibited clinical/payer conclusions.

## Executable Slice G gates

`evaluation/expected_care/frozen_suite.v1.json` is executed by
`services/api/scripts/evaluate_expected_care_explanations.py`. Gate metrics are
derived only from recorded observations. The runner executes arithmetic and
comparison labels; mixed currency; incomplete allocation; missing cost and
`pending_cost`; stale, inactive, superseded, and checksum-drifted releases;
malformed/schema-invalid output; unsupported facts and protected-value
mutations; timeout/quota/error fallback; role visibility and cross-scope
attacks; exact doctor/patient/payer fact-object differences; structured
fallback; bilingual contradiction; and concurrency/idempotency conflicts.

Historical v1 and v2 release rows and all earlier passing and failing
evaluation files remain unchanged. An append-only
`release_marked_unsuitable` event records that v2 cannot be activated because
its free-prose validator and hard-coded gate counts overstated deterministic
exactness.

The corrected paid run
`evaluation/expected_care/results/20260726T141758Z.sanitized.json` passed every
mandatory executable gate:

- schema, fact, exactness, bilingual, comparison, authorization, visibility,
  and fallback rates: `1.0`;
- unsupported-claim and leakage rates: `0.0`;
- provider failures: `0`;
- provider-reported usage: `8,246` input and `2,939` output tokens;
- configured cost: `1,978` microunits; and
- p50/p95 latency: `4,040 / 4,628 ms`.

The deterministic no-provider run is also retained. These are synthetic
engineering measurements, not external or professional approvals.

## Governed release operations

Migrations `20260726_0045`, `0046`, and `0047` add the immutable comparison and
explanation domains, monotonic release-event sequencing, exact early-stage
status widths, and database-level append-only release protection.

`expected_care_release_operations.py` provides advisory-locked,
expected-version and content-bound-idempotency operations for stage waivers,
activation, supersession, kill switch, exact rollback, and unsuitable-release
correction. Every transition appends evidence; release and event rows are not
updated. Activation verifies source/schema/prompt/model/evaluation lineage,
purpose compatibility, every mandatory machine gate, stage state, and an
explicit rollback target. Conflicting active releases fail closed. Readiness
is content-free.

Pending v3 is predecessor-linked to immutable v2:

`evaluation/expected_care/releases/expected-care-role-explanation.v3.pending.json`

Release ID: `efbd6b9b-131f-4ab7-90e4-e0c1c1c6aad6`.

Its current-stage requirements are truthfully recorded as
`product_owner_waived_for_current_stage` or
`not_required_for_early_synthetic_development`. No review is represented as
externally completed. The distinct future real-world gates remain in the
artifact. v3 remains pending and kill-switched; machine-gate success alone did
not activate it.

## Separate Slice D evidence

`expected_care_candidate` keeps its own purpose contract, provider input,
schema, validator, fallback, suite, metrics, and release decision. Its paid
evaluation covers rehabilitation, laboratory, imaging, consultation/treatment
sessions, alternative pathways, missing/conflicting information, protected
codes/currencies/units/amounts/totals, stale and checksum-drifted releases,
malformed output, timeout/error, cross-scope attacks, and deterministic
fallback.

The first live run is retained as failed after one malformed response and
three five-second timeouts. The systemic fix increased only this purpose's
bounded timeout/output allowance. The corrected paid run
`evaluation/expected_care_candidate/results/20260726T142027Z.sanitized.json`
passed every executable machine gate with `10,796` input and `3,779` output
tokens, configured cost `2,570` microunits, and no failed observations.

The separate pending synthetic-stage Slice D release is:

`evaluation/expected_care_candidate/releases/expected-care-candidate.v1.pending.json`

Release ID: `6006d53b-470b-4fdc-ac80-d94795548855`.

## Synthetic Slice A reference families

Governed, versioned, effective-dated, checksum-bound fixtures now cover
rehabilitation, laboratory, imaging, and consultation/treatment-session
pathways. Every source and invented range is labeled
`synthetic_product_fixture`, uses explicit currency/units/codes/applicability,
and is not an official price, guideline, negotiated rate, coverage rule, or
real patient fact. The blocked real-world Shanghai imaging candidate remains
blocked.

## Complete role workflow

- Doctor: creates or refreshes an immutable comparison, optionally admits
  submitted facts, sees idempotent replay and predecessor-linked history, and
  requests/retries the doctor-scoped explanation.
- Patient: always sees the immutable baseline and authorized latest
  comparison, explicitly requests/retries a patient-safe explanation, and
  always retains structured fallback.
- Payer: remains bound to the exact request and active organization, sees
  submitted facts/comparison/clinician response/human payer state/explanation
  separately, and can request only payer-scoped explanation. No clinical,
  reimbursement, denial, or adverse decision is automatic.

Flutter uses content-bound idempotency keys and never constructs provider
facts. English/Simplified-Chinese responsive states include loading, empty,
unavailable, conflict, fallback, retry, replay, and history behavior with
semantic controls and deterministic keyboard traversal.

## Verification

- complete PostgreSQL API suite: `360` tests passed after one direct-release
  immutability regression was found and fixed in migration `0047`;
- Flutter analysis and full functional/accessibility suite: passed
  (`72` tests plus `15` intentionally skipped general pixel cases);
- expected-care rendered goldens: doctor desktop, patient Simplified-Chinese
  mobile, and payer desktop all passed and were visually inspected;
- corrected paid Slice F and independent Slice D evaluations: all mandatory
  executable gates passed; failed and deterministic runs retained;
- Alembic local database upgraded through `0047`; and
- `git diff --check`: passed.

All data used here is wholly synthetic. No real patient, provider, payer,
hospital, claim, confidential rate, reviewer, or identifier data was used.

## 2026-07-27 DeepSeek Vision capability check

The separately planned DeepSeek Vision purpose remains unimplemented and
disabled. Current official DeepSeek documentation describes DeepSeek V4 as
text-only and does not provide image input through the public API. The
documented integration workaround proxies images through another provider,
which would violate Dr. AI's DeepSeek-only rule for every enabled generative or
multimodal purpose.

Per the authorized Phase 1-4 task boundary, no proxy-provider implementation,
fake draft, prompt, schema, release, or activation evidence was created. Manual
imaging upload/review and doctor-owned findings remain the product path until an
official DeepSeek image-input capability exists.

## Controlled Tencent staging evidence

The existing synthetic-only Tencent staging environment was refreshed after a
checksum-verified 74 MB host-only backup:

`/home/ubuntu/dr-ai/staging/backups/20260726T143619Z-ag-hardening-retry2`

The first two backup attempts are retained as failed operational evidence: one
encountered root-owned release artifacts and one found no host `pg_dump`.
The successful attempt used an ephemeral official PostgreSQL client container,
verified the custom-format dump and every copied file, and changed no host
package.

Deployed API digest:

`hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:3e88886efc85d009c3761b72dfff3f628c5901267b5cd6ada6afc41f7be53a52`

Staging verification:

- Alembic `20260726_0047 (head)` and `alembic check` reported no new
  operations; the known knowledge-rights/source cycle warning remains;
- two synthetic seed passes created zero records;
- all four synthetic reference families installed and resolved;
- staging registered immutable v1/v2 history, the v2 unsuitable event, pending
  v3, its early-stage waiver event, and the separate pending Slice D release;
- staging v3 ID `c8d96972-b3e8-4272-8fcb-9a94e579b61c`, with no active pointer;
- deployed explanation/comparison source hashes exactly match the immutable v3
  release artifact;
- `expected_care_candidate_enabled=false`,
  `expected_care_explanation_enabled=false`, and explanation kill switch
  `true`;
- the complete redaction-safe authenticated smoke passed health, doctor and
  patient login, database write/conflict, resource search, token rotation and
  logout, cross-patient denial, upload metadata, simulated assessment,
  recovery/Today, patient chat, consultation, private messaging, and privacy
  deep link;
- local/remote hashes matched for `index.html`, `main.dart.js`, and
  `flutter_service_worker.js`;
- public health reported staging/database `ok` and explanation `disabled`;
  public `/privacy` returned `200`; and
- recent API/Caddy logs contained zero sensitive-or-critical pattern matches.

The immutable retrieval-model image was not changed. No release was activated,
no real data was transmitted, and no production/public/commercial environment
was changed.

## 2026-07-27 current-source compatibility note

The paid passing candidate and explanation artifacts, unsuitable v2 evidence,
and pending release manifests above remain immutable historical evidence. The
Phase 1-4 closure subsequently changed the candidate, explanation, and
comparison sources to add the exact server-built fact object, payer-scope
hardening, and owning-patient comparison authorization:

- candidate current `40a6376f38fa969d32ad9f9e845878e34e713f70e316ec83b44b90a0ef5afdfa`;
  pending v1 expects
  `b322595da5ba8792b4345f1a68af0947ef9d3cd5dc84c87124f26585abfe0eb6`;
- explanation current
  `9bc95f2f6fc158d5e6c2b1025b76f25dbf82735b7035b07416948635426091e0`;
  pending v3 expects
  `bb0c939d5eb69b650c553f45721b4c24e1268587965afe75bfe14c2a5bd76192`;
- comparison current
  `7a59a276a7ef4056642d2434ee58d3d80836c0b21a3b01eff0cac187488ff5a2`;
  pending v3 expects
  `ffc94ec9e24dde184f065794351269712d34a316fd9269b746717002f449af55`.

The governed release path therefore rejects those pending manifests for the
current source, as intended. No prior evidence was rewritten and no
checksum-incompatible activation was attempted. A new paid evaluation and
successor release are required after a DeepSeek credential and controlled
staging authority are available. The directly executable deterministic reruns
`evaluation/expected_care_candidate/results/20260726T164756Z.sanitized.json`
and
`evaluation/expected_care/results/20260726T164757Z.sanitized.json`
retain the current no-provider/fallback state; provider-dependent machine gates
remain false rather than being fabricated.
