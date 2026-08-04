# Clinical Event Intelligence Engine implementation record

Date: 2026-08-01
Stage: controlled synthetic development
Data boundary: wholly synthetic evaluation and existing authorized local test
fixtures only

## Outcome

This record covers the first coherent implementation of the provider-neutral
Clinical Event Intelligence Engine across PostgreSQL, FastAPI, DeepSeek purpose
adapters, role-authorized API views, Flutter, evaluation, and release controls.
It does not represent clinical validation, payer acceptance, real-patient
authorization, public production release, or regulatory approval.

## Implemented boundary

- An additive Alembic migration freezes versioned Clinical Event snapshots,
  normalized requested-line assessments, pathways, retrieval lineage,
  provider-attempt telemetry, immutable artifacts, role explanations, and
  human/outcome lineage.
- Server snapshot construction keeps requested billable lines immutable and
  resolves location only from structured Clinical Event, facility, and
  provider-organization records. Missing or conflicting location remains
  explicit; neither free text nor IP inference is used.
- Retrieval is server-directed and governed-release-bound. It filters by
  authorization scope, effective dates, payer/facility applicability,
  provider-transmission permission, and confidential-price status before any
  provider call.
- Primary assessment and critic use separate `deepseek-v4-pro` purpose
  configuration. Role explanation uses separate `deepseek-v4-flash`
  configuration and selects frozen fact IDs rather than rewriting shared
  scores or ranges.
- Strict schemas and deterministic validation enforce exact requested-line
  coverage, independent six-dimensional scores, versioned aggregation,
  predicted/requested separation, price provenance, wide tier-5 uncertainty,
  no admitted source for tier 5, and no automatic clinical or payer action.
- Patient, doctor, and payer API views share one artifact identity and filter
  role-specific detail. Flutter provides responsive English and Simplified
  Chinese loading, empty, missing-information, fallback, disagreement,
  provider-unavailable, assessment, pathway, counterfactual, and lineage
  surfaces.

## DeepSeek documentation and live assurance

The implementation was checked against DeepSeek's official 2026-08-01 model,
pricing, and JSON Output documentation. The credentialed `/models` endpoint
returned both configured identifiers: `deepseek-v4-pro` and
`deepseek-v4-flash`. The OpenAI-compatible chat-completions JSON Output path is
used because the official documentation currently limits the Responses API to
flash while both models support JSON Output through chat completions.

The first two bounded wholly synthetic pro assurance attempts correctly
returned structured tier-5 provenance but produced insufficiently wide cost
ranges. The deterministic validator rejected both with
`tier5_uncertainty_not_wide`; no critic call ran. These were retained as failed
assurance evidence, not hidden as passes. The final validated run used the
same strict provider output contract plus a deterministic safe normalization
that may widen only the upper tier-5 bound and records that transformation in
validation lineage.

The final bounded run passed primary assessment, one critic pass, and the
patient explanation path. It deliberately surfaced
`material_disagreement` for human review. Provider-reported usage and
configured-price accounting were:

- primary `deepseek-v4-pro`: 3,058 input tokens, 1,479 output tokens, 2,617
  micro-USD;
- critic `deepseek-v4-pro`: 2,902 input tokens, 409 output tokens, 1,618
  micro-USD; and
- explanation `deepseek-v4-flash`: 767 input tokens, 126 output tokens, 143
  micro-USD.

Total configured-price cost was 4,378 micro-USD (USD 0.004378). The sanitized
result stores no raw provider content; raw wholly synthetic response bodies
remain under the gitignored evaluation directory.

## Verification evidence

Completed verification:

- focused CEI backend, integration, persistence, evaluation, and migration
  suite: 24 passed;
- full FastAPI suite: passed;
- isolated Alembic cycle on `dr_ai_test`: `0055 -> 0054 -> 0055`, followed by
  `alembic check` with no pending operations;
- local development schema reconciled from a stale `0054` marker to the exact
  verified `0055` shape after a 6.4 MB custom-format backup. Backup SHA-256:
  `2a71305e1d7f009d57822bbf7bf5bdbf3e398cce556d7d6af325648c5099130a`;
- backend Ruff formatting/static checks: passed;
- provider-free frozen suite: all 5 scenarios and all 27 validator/service
  adversarial requirements covered, with no unverified cases;
- final bounded live DeepSeek assurance: passed primary, critic,
  reconciliation, tier-5 labeling/weighting, and explanation;
- Flutter analysis: no issues; full Flutter suite: 105 passed with 23
  intentionally skipped platform/golden tests; and
- explicit CEI golden suite: all 6 English/Simplified Chinese patient, doctor,
  and payer mobile/desktop renderings passed and were visually inspected.

The Alembic drift check retains a pre-existing SQLAlchemy warning about the
mutually dependent `kb_rights_records` and `kb_sources` foreign keys; it still
reports `No new upgrade operations detected`.

Key evidence files:

- `evaluation/clinical_event_intelligence/frozen_suite.v1.json`
- `evaluation/clinical_event_intelligence/verification_matrix.v1.json`
- `evaluation/clinical_event_intelligence/results/clinical-event-intelligence-provider-free-20260801T153400Z.json`
- `evaluation/clinical_event_intelligence/results/clinical-event-intelligence-live-20260801T153444Z.json`

## Preserved gates

- AI output is evidence, never ground truth or an automatic decision.
- Purpose releases remain independently disabled and kill-switched by default.
- A passing synthetic suite does not activate a release.
- Real-patient transmission, real payer policy/rates, clinical validation,
  privacy/security review, legal/regulatory authorization, and production
  rollback rehearsal remain separate gates.
- A future specialized cost model must first run through the same
  provider-neutral artifact contract in shadow mode. It cannot rewrite prior
  artifacts or inherit DeepSeek output as a training label.

## 2026-08-02 governed local-synthetic activation supplement

This supplement records the later, explicitly authorized activation. It does
not rewrite the 2026-08-01 implementation evidence above. The database is at
Alembic `20260802_0057`; local API configuration enables all three CEI purposes
and clears all three purpose kill switches without exposing the server-side
credential to Flutter.

### Final active immutable releases

All releases use scope `controlled_synthetic_staging`, exact predecessor and
rollback version `v4-controlled-synthetic-20260802`, the corrected verification
matrix SHA-256
`8892b0ed73531f6f38e8905f30a7b1218bd766ac87c35a83291762369b52ca2a`,
and provider-free result SHA-256
`8068807b57e46430bfadf31ea3f7abfbb45a7534eec6ae3d35aacb4777ff237c`.

| Purpose | Provider/model | v5 release ID | Payload checksum SHA-256 |
|---|---|---|---|
| primary | DeepSeek / `deepseek-v4-pro` | `5a9de552-cdfc-409c-b00d-4dbc15b4373e` | `02bb96bcd5f85004f8784f47cb47d03612c89d84624908d921ade084bfb3a9f1` |
| critic | DeepSeek / `deepseek-v4-pro` | `fae75bd8-e8fb-49dc-ac3b-27661a43ba23` | `c2e26503777c7f0751c52db77bb68f006f3678ed2b7fbb28b4bba597ca33cc3d` |
| role explanation | DeepSeek / `deepseek-v4-flash` | `635756a5-613d-4e94-b130-b040ff8830e4` | `5b16237755158a7cdf0f89e129901700ba5c9b8569109ef113a9ed00e9bbf456` |

The v5-to-v4 rollback events were
`d1951330-7766-41a7-8111-eb9bc2d3f646`,
`20af98bc-3f85-46bb-83ff-724c031edde1`, and
`15ebbce0-646a-4d9a-8603-4446ba4e10e9`. Restoration to v5 used append-only
events `a08f0010-e698-4ea5-954f-97e4f12d0f24`,
`4fcc4506-4562-4018-a375-62f6d3938f95`, and
`c36ecaa7-cfc7-4c0d-8962-b7e2815d5a7f`. Repeated installation and operation
calls are content-idempotent; expected version/checksum mismatches and stale or
drifted releases fail closed.

The operational rollback form is, for example, the exact primary v5-to-v4
target:

```bash
cd services/api
uv run python scripts/manage_clinical_event_intelligence_releases.py rollback \
  --release-id 5a9de552-cdfc-409c-b00d-4dbc15b4373e \
  --target-release-id c58c4466-4551-459c-8b41-557e1ec65690 \
  --expected-version v5-controlled-synthetic-20260802 \
  --expected-checksum 02bb96bcd5f85004f8784f47cb47d03612c89d84624908d921ade084bfb3a9f1 \
  --idempotency-key operator-primary-v5-to-v4-rollback-20260802
```

The critic and explanation operations use their corresponding v5 IDs and
checksums above and exact v4 targets
`869c91d0-a29f-4191-8065-136b5a347f91` and
`095768aa-6738-4b05-8547-ac1e45455c0f`.

### Live wholly synthetic workflow evidence

Before provider egress, an independent database assertion verified fixture
`clinical-event-intelligence-local-synthetic-v1`, payer request
`8a788b62-6bc7-4e1f-b036-bb5cda7244f1`, patient external ID
`SYN-CEI-LOCAL-001`, synthetic organization/membership scope, and exactly two
synthetic line codes. The successful immutable artifact is
`8146e307-f488-4e5b-80a9-be642669379a`, run
`c7c56f5e-739c-4d0f-aed3-36bb69316f21`, version 2.

Both requested lines appear once with all six non-empty 0-100 dimensions,
independent documentation completeness, requested/predicted separation,
quantity and cost ranges, and tiers 1 and 5. Tier 5 has no admitted price
reference, is visibly exploratory/model-only, uses a 12000-24000 minor-unit
wide range, and has zero cost-alignment weight. Primary/critic reconciliation
persisted `material_disagreement`; human review is required and no score can
approve, deny, reduce, delay, remove, or prescribe care.

The successful DeepSeek attempts used `deepseek-v4-pro`: primary 3,926 input /
2,064 output tokens and critic 4,889 input / 458 output tokens. Persisted
role-explanation calls used `deepseek-v4-flash`: doctor English 2,219/124,
patient Simplified Chinese 1,144/101, and payer English 1,188/121. Only
validated fact selection and safe prose are persisted; raw responses, hidden
prompts, credentials, source IDs, confidential rates, reviewer-private notes,
and chain-of-thought are excluded.

A prior provider-invalid attempt produced a `provider_unavailable` artifact
without automatic action. Documentation, clarification, pending-cost, and
human-review workflows remained usable. Sequential retry replayed the artifact;
same-key concurrent requests returned one artifact identity with no duplicate.

### Verification and visible state

- Focused CEI/health/backend/API/governance checks: 44 passed, plus the final
  governance activation suite 7 passed.
- Full FastAPI suite: passed.
- Alembic `0056 -> 0057 -> 0056 -> 0057` regression cycle and final drift check:
  passed; the pre-existing mutually dependent knowledge-base FK warning remains.
- Focused CEI Ruff format/static checks and `git diff --check`: passed.
- Flutter analysis: no issues; full Flutter suite: 111 passed with 23 intentional
  skips; six CEI goldens passed.
- The running browser was inspected for patient, doctor, and payer; English and
  Simplified Chinese; 412x917 mobile and 1280x720 desktop; normal, missing,
  tier-5, disagreement, fallback, and provider-unavailable states. Console logs
  contained no application exception; the debug web server emitted one DWDS
  injected-client JSON type error while the application remained loaded and
  usable. The locale-aware GET fix now returns the persisted role explanation
  rather than incorrectly labeling every successful explanation as structured
  fallback.
- Final `/health`: schema `20260802_0057`; primary `ready`; critic `ready`;
  explanation `ready`.

Sanitized machine-readable evidence is
`evaluation/clinical_event_intelligence/results/clinical-event-intelligence-activation-20260802.json`
(SHA-256
`aac95cb3bce42173882626dc2158d58f3a697a4d598696685452f00a4e555c9e`).

### Remaining authorization boundary

This result proves governed local use with wholly synthetic data only. It does
not establish real-patient transmission permission, clinical efficacy or
validation, official prices, payer acceptance, reimbursement accuracy,
privacy/security certification, legal or regulatory authorization, public
production readiness, or commercial impact.
