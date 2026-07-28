# Phase 4 Slices B/C Care-Reference Foundation Record

Status: complete locally

Date: 2026-07-25

Scope: provider-neutral governed reference persistence and model-free
deterministic evaluation

## Outcome

Slices B and C from `docs/Dr_AI_v1.0_AI_Platform_Architecture.md` are
implemented and verified locally. This is an internal backend foundation, not
a public API or product surface.

The implementation adds:

- a common versioned release contract for scenario definitions, care plans,
  pricing references, and utilization rules;
- provenance, source/payload SHA-256 checksums, effective intervals, freshness,
  independent rights flags, named checksum-bound review, activation,
  supersession, rollback, and active pointers;
- database immutability after activation and append-only review, activation,
  and evaluation history;
- scenario applicability and compatible-release validation;
- exact code-system/code, unit, quantity, currency, date, facility, and
  reference validation;
- integer-minor-unit item and aggregate range arithmetic;
- transparent within/above/below range, unsupported, missing-information,
  invalid-reference/observation, comparison-not-ready, justified-exception,
  and suppression states;
- duplicate observed-line and declared-total reconciliation checks; and
- append-only re-evaluation with exact structured input facts,
  release IDs/versions/checksums, input/result checksums, and predecessor
  lineage;
- exact database-backed resolution of the active scenario, care-plan, pricing,
  and utilization releases for a caller-supplied structured scope; and
- an internal orchestration service that checks the doctor-patient
  relationship, Clinical Event ownership, submitting-doctor payer-request
  scope, and exact immutable payer-line IDs/amounts before evaluating and
  persisting a metadata-only audit event.

No model or provider adapter is imported or called by the engine.

## Persistence Boundary

Migration `20260725_0040_care_reference_foundation.py` adds:

- `governed_care_releases`
- `governed_care_release_reviews`
- `governed_care_release_activations`
- `governed_active_care_releases`
- `care_scenario_definitions`
- `care_plans`
- `care_plan_items`
- `pricing_reference_sets`
- `pricing_reference_items`
- `utilization_rule_sets`
- `utilization_rules`
- `care_reference_evaluations`

The new tables are additive. Existing `clinical_events`,
`clinical_services`, `care_cost_items`, `payer_requests`,
`payer_request_lines`, and `payer_reviews` are unchanged. An evaluation may
reference a Clinical Event or immutable payer request, but it cannot mutate
clinical truth, delivered-service state, active financial companions, or
submitted snapshots.

The resolver follows `governed_active_care_releases`; it does not infer a
latest version or silently mix releases. Supersession and rollback therefore
change the exact four-release bundle selected for future evaluations while
past evaluation rows retain their original foreign keys and checksums.
Authorization failures use the neutral internal `not_found` error boundary.

## Fixture And Data Boundary

The blocked candidate
`cn-sh-outpatient-single-region-ct-plain-v1` is the first executable fixture.
It contains only the candidate identifier and unavailable/blocked control
state. It contains no official service code, amount, attachment content,
runtime reference row, seed, prompt, or active release.

Two unrelated, wholly synthetic reference families exercise the same engine:

- an outpatient rehabilitation course with session quantities and a synthetic
  range; and
- a synthetic laboratory panel with an attributable justified exception.

This proves that scenario support comes from compatible releases and structured
configuration, not a CT/disease branch.

The integration fixture persists and activates only the wholly synthetic
outpatient-rehabilitation family under the synthetic scope
`CN|Synthetic Province|public|primary|CNY`. Its four releases carry approved
synthetic-only reviews and prohibit provider transmission and redistribution.
The idempotent local bootstrap resolves the active bundle after installation;
it does not ingest or activate the blocked Shanghai source.

## Verification

Verified locally:

- Alembic upgrade to `20260725_0040`;
- Alembic schema drift check: no new upgrade operations;
- one-step downgrade to `20260724_0039`;
- re-upgrade to `20260725_0040`;
- final Alembic schema drift check: no new upgrade operations;
- Ruff formatting on all changed Python files;
- full API Ruff static check;
- focused integration, care-reference engine, and preserved care-cost tests:
  `21 passed`;
- all API tests in clean final partitions: HPA ingestion `4 passed` plus the
  remaining suite `315 passed` (`319` total);
- the synthetic bootstrap installed and resolved the same active `v1` bundle
  twice, proving idempotent local setup;
- integration coverage proves exact active resolution, supersession and
  rollback, persisted stale-release suppression, neutral cross-patient denial,
  submitting-doctor payer-request isolation, immutable snapshot amount
  enforcement, and end-to-end persisted evaluation without AI; and
- repository whitespace validation is recorded in the final task handoff.

The only migration-check warning is the pre-existing SQLAlchemy table-sort
warning for the mutually dependent `kb_rights_records` and `kb_sources`
foreign keys. It is unrelated to this slice and did not produce schema drift.
The known slow HPA partition passed `4/4` in 181.88 seconds, and every
remaining test passed `315/315` in the second partition.

## Explicitly Not Done

- no Shanghai-source ingestion or activation;
- no live, real, or confidential reference/patient/claim data;
- no DeepSeek call, candidate schema, prompt, or Slice D work;
- no public HTTP route, Flutter UI, deployment, commit, push, or pull request;
- no coverage, eligibility, reimbursement, payment, fraud, abuse, clinical
  necessity, or punitive decision; and
- no change to the blocked first-scenario release gates.

The next authorized work is not implied by this record. Slice D, a public
comparison workflow, doctor review/presentation, and any reference admission
remain separate decisions.
