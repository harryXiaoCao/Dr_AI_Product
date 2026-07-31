# Phase 7 Controlled-Staging Rehearsal

Date: 2026-07-30

Status: the controlled-staging deployment, governed AI exercises, authenticated
three-role smoke, rendered doctor inspection, backup restoration, and exact
API/schema/web rollback are complete. External notification transports and
DeepSeek imaging activation remain truthfully blocked.

## Scope and non-authority

This runbook deploys and rehearses the synthetic Phase 1-6 framework in
controlled staging. It does not authorize real-patient data, live payer
integration, public production, commercial rollout, or clinical, privacy,
legal, regulatory, or provider-delivery claims.

Use synthetic accounts, resources, images, endpoints, and tasks only. Do not
put patient/resource identity, free text, prompts, responses, images, message
bodies, raw device endpoints, provider payloads, credentials, secrets, or
authentication tokens in logs or evidence.

## Stop conditions

Stop before mutation when any of the following is true:

- the exact host, deployment directory, live staging database, source revision,
  migration head, active image digests, or predecessor web checksum is unknown;
- the pre-change backup is missing, unreadable, not checksum-verified, or not
  owner-only;
- the restore target is the live database or is not a fresh isolated database;
- a release checksum, purpose/schema/prompt/model version, predecessor, machine
  gate, or allowed stage waiver is inconsistent;
- a provider is not independently ready for the selected purpose;
- presence-only secret checks fail or any suspected sensitive-pattern count is
  non-zero; or
- rollback targets are not exact and schema-compatible.

## 1. Resolve and record the exact pre-change target

Record content-free values only:

- source revision and branch;
- explicit controlled-staging host and narrow deployment directory;
- live staging database name;
- API and retrieval image digests;
- Flutter web bundle SHA-256;
- Alembic current revision and expected head;
- notification, chatbot, Slice D, Slice F, and imaging enabled/kill-switch
  states; and
- current governed release identities for each purpose.

`scripts/staging/phase7_inventory.py` produces a read-only local inventory.
`scripts/staging/phase7_operation_preview.py` validates explicit target inputs
and prints backup, isolated-restore, or rollback plans; it does not execute
them. Treat a preview as a guard, not completion evidence.

The recorded Phase 7 pre-change state is:

- API:
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:58244c2e385b3dcaa050820ed99d16d71b4ef25c35a5f685c471872afacb739b`;
- retrieval:
  `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-retrieval@sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89`;
- schema: `20260728_0052`; and
- predecessor web archive:
  `0e8f7ffbe049f5734feb9276cafd2033d8cd48b1a4fd82dee020b4ba30bf5741`.

## 2. Create an owner-only backup

1. Create a new, timestamped backup directory under the exact staging
   deployment's `backups/` directory.
2. Set the directory to `0700` before writing into it.
3. Back up the host `.env`, Compose/Caddy configuration, current web bundle,
   governed release artifacts, and a PostgreSQL custom-format dump.
4. Set every backup file to `0600`.
5. Produce a manifest containing artifact names, sizes, and SHA-256 values; do
   not include secret contents or database rows.
6. Recompute every checksum and require an exact match.
7. Use `pg_restore --list` against the custom dump and record only the bounded
   catalog result.

Archived `.env` files are recovery references, not durable secret stores. If a
credential is rotated after backup, restore the non-secret configuration and
inject the current secret through the owner-readable host environment; never
reactivate an obsolete archived credential.

The completed pre-change backup is
`/home/ubuntu/dr-ai/staging/backups/20260730T140240Z-phase7-preactivation`:
directory mode `0700`, six files mode `0600`, six checksum verifications passed,
and the restore catalog contained `849` lines.

## 3. Restore to a disposable isolated database

1. Create a fresh database whose name begins `dr_ai_phase7_restore_`; never
   target the live staging database.
2. Restore the verified custom dump.
3. Compare the restored Alembic revision with the pre-change revision.
4. Compare a sorted public-table catalog hash and table count.
5. Record bounded row-count sanity checks only for approved categories.
6. Run a bounded health/authentication smoke against the isolated target.
7. Drop the disposable database only after evidence is recorded and only when
   the exact target has been re-resolved.

Completed pre-change evidence:

- restore database `dr_ai_phase7_restore_20260730_140240`;
- restored revision `20260728_0052`;
- `users=16`, `clinical_events=5`, `notifications=1`;
- live and restored public-table counts `108`; and
- public-table catalog hashes matched.

## 4. Verify release artifacts before activation

For every AI purpose, independently verify:

- purpose code and contract, schema, prompt, model configuration, provider, and
  model;
- frozen-suite, sanitized-result, source, and output-schema checksums;
- append-only evaluation lineage;
- current-stage machine gates and truthful review/waiver state;
- exact predecessor and rollback target;
- release effective dates and compatibility with the deployed schema; and
- initial kill-switch state.

Never activate a release with SQL or direct table changes when a governed
management command exists. Never reuse one purpose's evaluation or release
state as evidence for another.

## 5. Slice D sequence

1. Register the separately evaluated Slice D release through its governed
   command.
2. Activate it under the controlled-synthetic-stage waiver only.
3. Generate a candidate from the authenticated doctor path.
4. Admit only through the deterministic governed admission workflow.
5. Compare admitted facts with delivered facts using integer minor-unit
   arithmetic.
6. Read back through authorized patient, doctor, and payer paths.
7. Inject unsupported values, prompt injection, stale/inactive/superseded
   release, checksum drift, malformed output, timeout, provider outage, quota,
   and kill-switch cases.
8. Confirm that fallback facts remain available and no AI process changes
   clinical, financial, payer, or notification records.
9. Disable the purpose and roll back to the exact compatible predecessor.
10. Record only content-free release identity, transition, latency, usage,
    bounded error/fallback codes, and invariant counts.

Completed staging sequence:
`v2-2026-07-30 -> v3-2026-07-30-rehearsal -> exact v2 rollback`.
The authenticated doctor route generated a release-bound candidate, replayed
it safely, required a human acknowledgement, published a deterministic
comparison, and then returned to the disabled state through the kill switch.

## 6. Slice F sequence

1. Verify the corrected predecessor-linked artifact and sanitized evaluation.
2. Register and activate through the governed command.
3. Exercise one authorized patient, doctor, and payer comparison explanation.
4. Confirm every generated claim cites the supplied deterministic facts and
   cannot introduce or modify a number, date, code, comparison, clinical fact,
   financial allocation, payer state, or notification.
5. Inject timeout, quota, malformed output, provider outage, stale release,
   incompatible checksum/schema, unsupported claim, bilingual contradiction,
   and kill-switch cases.
6. Activate a compatible successor, then roll back to the exact predecessor.
7. Engage the predecessor kill switch and verify that effective active
   resolution is empty and deterministic fallback remains available.

The completed local and controlled-staging rehearsal was
`v4-2026-07-30 -> v5-2026-07-30-rehearsal -> exact v4 rollback -> v4 kill`,
with no effective active release. The staging doctor path generated and
replayed a validated explanation without changing the persisted deterministic
comparison.

## 7. Imaging capability and release sequence

First check current primary provider documentation. DeepSeek's official V4
integration documentation identifies the selected V4 endpoint as text-only.
The completed bounded probe sent a genuine 1x1 synthetic PNG and received a 4xx
response; image input and structured output were not observed.

Therefore:

- evaluate the purpose as `unavailable_text_only`;
- do not send a text-only request and call it a multimodal probe;
- do not register or activate an imaging release;
- do not substitute another provider merely to create a pass; and
- retain the existing doctor-owned upload/review path and bounded unavailable
  state.

Only if the selected provider later documents image input may a bounded
synthetic-image capability probe run. Registration then additionally requires
purpose-specific localization, omission, unsupported-observation, bilingual,
structured-output, privacy/metadata, hallucinated-diagnosis, timeout/cost, and
snapshot-stability gates.

## 8. Chatbot product-path sequence

Use the authenticated Flutter patient path, not a provider script alone.
Exercise literal-question retrieval, bounded expansion, meaning-drift rejection,
admitted evidence, visibly labeled `general_model_knowledge` where allowed,
emergency routing, cross-resource denial, diagnosis/individualized dosing and
record-write boundaries, prompt injection, timeout, quota, malformed output,
stale/inactive release, kill switch, original-query fallback, EN/zh-Hans, and
append-only generation history.

Record only content-free readiness, latency, usage, bounded error/fallback
codes, release identity, and analytics counts. The completed staging sequence
registered and activated chatbot v1, exercised an authenticated patient
literal educational question through the product route, verified append-only
history, killed the release, and confirmed the active pointer was empty.

## 9. External notification sequence

Follow `docs/runbooks/Phase_6_Notification_Delivery_Readiness.md`. Enable only
one independently ready channel at a time. Preserve distinct states for
scheduled, attempted, provider accepted, sent, delivered-if-supported,
displayed-if-observed, failed, expired, and unknown.

For each ready channel, test synthetic denied, revoked, unsupported, stale,
rotated, signed-out, multiple-device, quiet-hours, retry, expiry, cancellation,
supersession, source-completion race, and secure deep-link behavior on launch,
background, resume, and authentication restoration. A provider success is
never user-visible display evidence.

Current result: APNs, EMAS, and Web Push remain disabled because their exact
credentials, signing/provider prerequisites, secure raw endpoint
infrastructure, and supported target evidence are unavailable. Do not run or
claim an external send until those blockers close.

## 10. Deploy and run smoke

After the backup/restore and all preflight gates pass:

1. build and push immutable API and retrieval images;
2. build the exact Flutter web bundle and record its SHA-256;
3. deploy exact digests, never mutable tags;
4. migrate to the expected revision;
5. run idempotent seeds twice;
6. verify public health/readiness and deployment/schema identities;
7. run authenticated patient, doctor, and payer smoke;
8. inspect EN/zh-Hans mobile, tablet, and desktop layouts, enlarged text,
   keyboard focus/restoration, screen-reader semantics, loading, empty,
   offline, stale, unavailable, retry, fallback, conflict, expired,
   superseded, denied, history, and long localized content; and
9. run presence-only configuration and count-only selected-log scans.

Recorded result:

- final source identity: `7b8d004+api-portable-20ae98ff`;
- final API digest:
  `sha256:844e16893bf6b1b7e396cbd253cc50a861d651a69b91c4381203d5c0ce416803`;
- final retrieval digest:
  `sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89`;
- final web content-manifest SHA-256:
  `5468b6aca9697f3c0916d19e7b09cf49e2c1bad7689c0cd4c6370e019c0b82f0`;
- final web archive SHA-256:
  `1afefc00851466cec14f7167609f4b7740b44fa5da871a06c2ab78698d1c06b1`;
- final schema: `20260730_0054`; Alembic drift check passed;
- public health and authenticated patient/doctor/payer smoke passed before and
  after recovery;
- deployed doctor UI rendered without clipping at mobile, tablet, and desktop
  widths; notification unavailable/empty and localized account states were
  inspected; and
- broader three-role bilingual, enlarged-text, keyboard/focus, semantics, and
  long-content states passed the Flutter executable suite and stable goldens.

## 11. Bounded failure campaign

`scripts/staging/phase7_fault_campaign.py` prints the required cases in a
content-free plan. Execute each case with deterministic test controls, advance
it only through `planned -> injected -> contained -> recovered -> verified`,
and use only allow-listed result codes.

Before and after each case, compare content-free row and duplicate counts for:
clinical events, expected-care facts, financial allocations, payer submissions,
payer decisions, support requests, notifications, notification delivery
attempts, and analytics identities. Require zero unexpected duplicates and only
explicitly allowed row deltas.

The ordered campaign contract and deterministic fault controls are verified.
Provider/release/output, concurrency, advisory-lock, idempotency, notification,
cancellation, and fallback cases were executed locally. Backup restore and
exact API/schema/web rollback/recovery were additionally executed against the
controlled-staging target. Uncontrolled cloud failures were not induced.

## 12. Exact rollback and recovery

API rollback requires the recorded predecessor digest and a schema
compatibility check. Flutter rollback requires the exact predecessor bundle
checksum. AI rollback uses the governed exact-predecessor transition and then
re-engages the kill switch when the expected state is disabled.

After each rollback:

- verify health/readiness, deployment and schema identity;
- run public and authenticated smoke;
- confirm the expected governed-release identity or disabled state;
- compare no-duplicate invariants;
- run a count-only redaction scan; and
- append content-free rollback completion evidence.

Completed result:

- API rollback restored predecessor digest
  `sha256:58244c2e385b3dcaa050820ed99d16d71b4ef25c35a5f685c471872afacb739b`;
- schema rollback reached `20260728_0052`;
- predecessor web archive was restored and served;
- predecessor health returned database `ok` with AI disabled;
- the verified post-activation dump was restored to the live staging target;
- Alembic returned `20260730_0054 (head)` with no drift;
- the final API/web release was reinstated; and
- authenticated three-role smoke passed after recovery with zero suspected
  sensitive-pattern matches in the sampled API/Caddy logs.

## 13. Completion rule

Phase 7 closes only when every non-external row in
`docs/periodic_dev_docs/Phase_7_Live_Gap_Matrix_2026-07-30.md` has observed
evidence and every external blocker remains truthfully disabled. Never replace
a missing receipt, physical-target observation, authenticated staging journey,
rendered inspection, or rollback result with local unit-test evidence.
