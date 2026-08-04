# Clinical Event Intelligence evaluation

This directory is the frozen, wholly synthetic evaluation boundary for the
Clinical Event Intelligence Engine. It is separate from retrieval corpora,
governed releases, operational records, and any future training data.

## Contents

- `frozen_suite.v1.json` defines the scenario families, required behaviors,
  adversarial cases, and mandatory machine thresholds.
- `verification_matrix.v1.json` maps service-level adversarial requirements to
  the exact tests that passed in the full API suite. The evaluator reports
  locally executed validator checks separately from this external evidence.
- `results/*.sanitized.json` records content-free execution evidence. Raw model
  responses, when a bounded live assurance run is explicitly enabled, remain
  under the gitignored `results/raw/` directory.

## Execution

From `services/api`:

```bash
uv run python scripts/evaluate_clinical_event_intelligence.py
uv run python scripts/evaluate_clinical_event_intelligence.py --live
```

The default run is deterministic and provider-free. `--live` performs a
bounded call using the server-side credential and the purpose-specific model
configuration. It never reads real patient data. A live result is assurance
evidence only: it does not activate a governed release or create a training
label.

## Release boundary

Passing this suite is necessary but insufficient for release. Primary
assessment, critic, and role explanation have separate governed purpose
releases, kill switches, budgets, rollback targets, and evaluation evidence.
The current stage status is
`product_owner_waived_for_current_stage`; real-patient, clinical, payer,
privacy, and regulatory authorization gates remain separate.
