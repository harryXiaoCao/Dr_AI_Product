# Phase 4 Slice D Expected-Care Candidate Record

Status: complete for wholly synthetic development and controlled staging

Date: 2026-07-25

Scope: provider-neutral, schema-constrained expected-care candidate generation
over admitted synthetic releases

## Outcome

Slice D from `docs/Dr_AI_v1.0_AI_Platform_Architecture.md` is implemented as an
internal backend purpose. It is not a public API, doctor-review workflow,
patient/payer surface, or live provider release.

The implementation adds:

- purpose code `expected_care_candidate` with independent purpose-contract,
  output-schema, prompt, and model-configuration versions;
- a provider protocol plus reusable JSON transport, with provider and model
  selected from configuration;
- a strict output schema for exact release lineage, applicability, structured
  items/ranges, assumptions, missing information, attributable exceptions,
  bounded confidence, and limitations;
- minimum-necessary input selection from the exact authorized Clinical Event
  scope and exact active scenario, care-plan, pricing, and utilization
  releases;
- deterministic revalidation through the B/C engine, exact source/rule IDs,
  release IDs/checksums, and integer-minor-unit reconciliation;
- fixed safe fallbacks, default-off kill switch, local/test synthetic-only
  gate, timeout, one bounded retry, conservative pre-call cost reservation,
  content-free telemetry, and transaction-scoped idempotency locking; and
- immutable regeneration lineage without overwriting an earlier candidate.

The provider input excludes patient/event identifiers, Clinical Event free
text, unrelated history, payer notes, attachments, contact/credential data,
raw source content, confidential price rows, and any release without explicit
provider-transmission permission.

## Persistence Boundary

Migration `20260725_0041_expected_care_candidates.py` adds:

- `expected_care_candidate_requests`
- `expected_care_candidate_attempts`
- `expected_care_candidate_results`

Database triggers make all three tables append-only. Requests retain the exact
actor/case scope, idempotency fingerprint, optional payer request and
predecessor, purpose/configuration versions, provider/model, exact four release
foreign keys plus checksum lineage, minimum-input checksum, validation
outcome, output checksum, and usage. Attempt telemetry is content-free. A
result is either a deterministically validated governed candidate or a fixed
safe fallback.

Candidate lifecycle states are `generated_pending_review`, `invalid`,
`suppressed`, and `provider_unavailable`. A candidate never becomes a
doctor-reviewed expected-care envelope and cannot approve, activate, compare,
authorize, pay, deny, change care, change financial state, or drive a workflow
transition.

## Fixture And Provider Boundary

The first persisted Slice D fixture is the wholly synthetic outpatient
rehabilitation bundle. Its new `v3-slice-d` release explicitly permits
provider transmission only for local/test synthetic candidate verification;
it grants no real-data, live-use, or production authority. An unrelated wholly
synthetic outpatient laboratory bundle passes through the same persistence,
resolution, schema, validation, and provider-stub path.

The Shanghai CT candidate remains blocked and has no active/runtime release.
No official Shanghai code, amount, attachment content, or source text was
copied into a release, prompt, candidate, seed, or test.

Deterministic in-process provider tests remain the fast regression layer. Slice
D now also has its own frozen, wholly synthetic DeepSeek evaluation at
`evaluation/expected_care_candidate/`. It does not reuse Slice F's prompt,
schema, validator, metrics, fallback, or release decision.

The first paid run is retained as failed: one malformed response and three
provider timeouts exposed that the original five-second bound was too short
for the separate candidate schema. After increasing only Slice D's bounded
timeout and output allowance, paid run `20260726T142027Z` passed every
executable machine gate with no failed observations, `10,796` input and
`3,779` output tokens, and configured cost `2,570` microunits.

A separate governed pending synthetic-stage release was then registered:
`evaluation/expected_care_candidate/releases/expected-care-candidate.v1.pending.json`.
Its release ID is `6006d53b-470b-4fdc-ac80-d94795548855`. Current-stage review
requirements are recorded as product-owner waivers, never as external or
professional approvals. Real-patient, real-provider, live-payer,
public-production, and commercial gates remain separate.

## Verification

Verified locally:

- Alembic upgrade to `20260725_0041`;
- one-step downgrade to `20260725_0040` and re-upgrade to
  `20260725_0041 (head)`;
- Alembic schema drift check with no new upgrade operations;
- focused Slice D/B/C/care-cost tests: `43/43`;
- complete API suite including the later A-G hardening pass: `360` tests
  executed, followed by the passing focused immutability regression suite;
- repository-wide Ruff static checks, touched-file formatting, and
  `git diff --check`; and
- local synthetic bootstrap and active-release state inspection.

The migration check retains the pre-existing SQLAlchemy table-sort warning for
the mutually dependent `kb_rights_records` and `kb_sources` foreign keys. It is
unrelated to Slice D and produces no schema drift.

## Explicitly Not Done

- no Slice E doctor approve/edit/reject workflow or reviewed envelope;
- no public route, Flutter UI, patient/payer presentation, or explanation call;
- no real-data or public-provider workflow; paid requests were limited to the
  wholly synthetic frozen evaluation;
- no real patient, claim, payer, confidential price, or source content;
- no Shanghai-source admission or activation;
- no deployment, commit, push, or pull request; and
- no clinical, coverage, reimbursement, payment, fraud, punitive, or workflow
  authority.
