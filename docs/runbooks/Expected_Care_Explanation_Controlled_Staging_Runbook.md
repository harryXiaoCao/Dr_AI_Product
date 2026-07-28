# Expected-care explanation controlled-staging runbook

## Boundary

The product owner authorized controlled Tencent staging for wholly synthetic
development on 2026-07-26. This does not authorize real-patient transmission,
real-provider use, live payer integration, public production, commercial use,
or any external review claim.

## Preflight

1. Back up PostgreSQL and verify a restore into an isolated database.
2. Record current image digest, Alembic revision, environment checksum, and
   rollback target.
3. Verify migration head `20260726_0047`, including monotonic explanation
   release-event sequencing and append-only governed care releases.
4. Verify the frozen suite/result/release file checksums against the pending
   release artifact.
5. Keep `DR_AI_EXPECTED_CARE_EXPLANATION_KILL_SWITCH=true` and
   `DR_AI_EXPECTED_CARE_EXPLANATION_ENABLED=false`.
6. Confirm the dataset is wholly synthetic and contains no real patient,
   credential, payer, confidential-rate, or reviewer-only operational data.

## Synthetic walkthrough

Use the existing synthetic doctor, patient, and payer accounts. Verify:

- baseline visibility without clinician response;
- delivered and submitted comparisons as separate immutable layers;
- concurrence, disagreement, and exception as separate evidence;
- doctor technical lineage; patient-filtered facts; exact payer organization
  scope;
- validated English and Simplified-Chinese explanation;
- provider timeout, invalid output, kill-switch, and no-release fallback;
- pending-cost/manual-documentation/payer-clarification continuity;
- keyboard traversal, semantics, narrow mobile layout, desktop layout, and no
  overflow.

Keep the purpose disabled and kill-switched for the initial shared staging
deployment. A later synthetic-only activation may use the recorded
`product_owner_waived_for_current_stage` states only after checksum verification
and an explicit rollback target. Those waivers never satisfy future real-world
gates.

## Rollback and restore

1. Turn on the purpose kill switch. This immediately preserves structured
   baseline/comparison fallback.
2. Record an append-only release event; never edit the prior release.
3. Move an active pointer only to the declared checksum-compatible release
   target, or engage the explicit fixed-structured-fallback target recorded for
   a first activation. Never infer a rollback target from “latest”.
4. Restore the database only for disaster recovery, not to erase immutable
   audit history. Reconcile comparison/explanation/release counts and checksums
   after restore.
5. Re-run authorization, fallback, health, migration, and UI checks.

Health/readiness output must remain content-free: database state, purpose
enabled/disabled, kill-switch state, compatible active release yes/no, and
provider reachability category only. Never emit keys, prompts, facts, raw
provider content, patient/request identifiers, or reviewer notes.
