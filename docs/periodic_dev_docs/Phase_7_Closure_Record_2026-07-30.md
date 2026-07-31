# Phase 7 Closure Record — 2026-07-30

## Closure status

Phase 7 is **complete for the authorized controlled-synthetic staging scope**.
The final immutable API/web release was deployed at schema `20260730_0054`;
Slice D, Slice F, and chatbot purposes were activated independently through
their governed commands, exercised through authenticated product APIs, and
returned to disabled states. A pre-change backup, isolated restore, separate
post-activation backup, exact predecessor API/schema/web rollback, live backup
restoration, three-role smoke, rendered responsive inspection, and count-only
redaction scans all passed.

APNs, Alibaba Cloud EMAS Mobile Push, and Web Push remain externally blocked
because no exact credentials, signing/provider approvals, secure endpoint
resolver, service worker/VAPID subscription infrastructure, or supported
physical target was available. DeepSeek's selected endpoint rejected genuine
image input, so no imaging release was registered or activated. These are
truthful disabled gates, not missing evidence disguised as success.

This record is controlled-staging evidence only. It is not real-patient,
live-payer, public-production, commercial, clinical, legal, privacy, regulatory,
provider-delivery, or target-visible evidence.

## Evidence classification

- **Controlled staging:** observed on the named staging host or its isolated
  restore database.
- **Local live-provider evaluation:** a real DeepSeek request executed from the
  development environment against synthetic frozen cases; it is not staging
  product-path activation.
- **Local deterministic rehearsal:** an in-repository or local-database
  governance/failure-control exercise; it is not external-provider or deployed
  staging evidence.
- **Pending:** no completion claim is permitted until the placeholder is
  replaced by recorded evidence.
- **Externally blocked:** production-quality disabled behavior exists, but an
  exact credential, signing identity, provider approval, secure endpoint
  resolver, browser capability, or physical target is unavailable.

## Controlled-staging pre-change inventory

The exact deployed state captured before Phase 7 activation work was:

| Item | Pre-change identity |
|---|---|
| API image | `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:58244c2e385b3dcaa050820ed99d16d71b4ef25c35a5f685c471872afacb739b` |
| Retrieval image | `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-retrieval@sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89` |
| Database revision | `20260728_0052` |
| Flutter web archive SHA-256 | `0e8f7ffbe049f5734feb9276cafd2033d8cd48b1a4fd82dee020b4ba30bf5741` |

The predecessor API, retrieval, and web identities above were used in the live
rollback rehearsal rather than inferred after deployment.

## Backup and isolated restoration

- Backup path:
  `/home/ubuntu/dr-ai/staging/backups/20260730T140240Z-phase7-preactivation`.
- The backup directory was mode `0700`; its six files were mode `0600`.
- All `6` recorded SHA-256 checks passed.
- `pg_restore` successfully listed a catalog containing `849` lines.
- Restoration used a fresh isolated database,
  `dr_ai_phase7_restore_20260730_140240`; the live staging database was not the
  restore target.
- The restored Alembic revision was `20260728_0052`, matching the pre-change
  source.
- Content-free sanity counts were `users=16`, `clinical_events=5`, and
  `notifications=1`.
- The live source and isolated restore each contained `108` public tables, and
  the full public-table catalog hash matched.

The post-activation backup
`/home/ubuntu/dr-ai/staging/backups/20260730T151000Z-phase7-postactivation`
was separately created with owner-only permissions. Seven recorded artifacts
passed SHA-256 verification and its `pg_restore` catalog contained `890` lines.
That dump was later restored to the exact live controlled-staging database
after the predecessor rollback; Alembic returned `20260730_0054 (head)` and
`alembic check` reported no new upgrade operations.

## Governed Slice D evaluation

The append-only sanitized result
`evaluation/expected_care_candidate/results/20260730T140946Z.sanitized.json`
records a local **live DeepSeek** evaluation against synthetic frozen inputs:

- all Slice D machine gates passed;
- schema-valid response rate: `1.0`;
- executable failure-case rate: `1.0`;
- provider usage: `10,796` input and `3,779` output tokens;
- configured cost: `2,570` microunits;
- four provider observations were validated; and
- deterministic failure cases covered unsupported values, cross-scope region,
  stale release, checksum drift, malformed schema, timeout, provider error,
  quota, and fallback.

On controlled staging, v2 was activated, v3 superseded it, and v3 was rolled
back to the exact predecessor v2. The authenticated doctor product path then
generated a release-bound candidate, replayed the same idempotency key safely,
required an attributable human acknowledgement, and published the
deterministic comparison. The candidate kill switch was re-engaged and final
readiness returned `disabled`. DeepSeek was never pricing authority and the AI
candidate did not mutate the immutable baseline.

## Governed Slice F evaluation and lifecycle rehearsal

The append-only sanitized result
`evaluation/expected_care/results/20260730T141037Z.sanitized.json` records a
local **live DeepSeek** evaluation against synthetic frozen inputs:

- every positive machine rate was `1.0`;
- unsupported-claim and prohibited-leakage rates were `0.0`;
- provider failures were `0`;
- latency was `4,080 ms` p50 and `5,003 ms` p95;
- provider usage was `8,246` input and `2,937` output tokens; and
- configured cost was `1,977` microunits.

The local governed lifecycle then registered
`v4-2026-07-30` and `v5-2026-07-30-rehearsal`, activated v4, superseded it with
v5, rolled back to the exact compatible predecessor v4, and engaged v4's kill
switch. The effective active release after the rehearsal was **none**.

The same governed sequence was repeated on controlled staging: v4 waiver and
activation, idempotent activation replay, v5 waiver and supersession, exact
rollback to v4, authenticated doctor explanation generation against the
persisted deterministic comparison, replay-safe readback, and final v4 kill
switch. Final readiness returned `disabled`. No direct release-table mutation
was used.

Deterministic persisted facts and comparisons remain authoritative. Generated
explanations are bounded rephrasings and have no authority to mutate clinical
events, expected-care facts, financial allocations, payer requests or
decisions, notification records, or human-authored justification.

## Governed imaging capability result

DeepSeek's current official integration documentation states that V4 is
text-only. A bounded capability probe nevertheless sent a genuine 1x1
synthetic PNG through the selected endpoint. It returned a 4xx response in
`1,310 ms`; `image_input_accepted=false`,
`structured_output_observed=false`, and
`release_registration_allowed=false`. No request or response body was retained
as closure evidence.

The fail-closed capability contract and frozen suite distinguish documented
text-only behavior, a future image-declared provider requiring a bounded probe,
probe failure, and genuine image-plus-structured-output capability. No
alternate provider was substituted, no text request was described as
multimodal evidence, and no imaging release or UI activation is claimed.

## Chatbot product-path exercise

Chatbot v1 was registered and activated through the governed command. An
authenticated synthetic patient asked an allowed literal educational question
through the same API route used by the Flutter UI. The bounded answer was
persisted with append-only user/assistant history. The frozen product-path
suite covers bilingual behavior, privacy/cross-scope denial, prompt injection,
malformed output, timeout, quota, outage, meaning drift, original-query
fallback, emergency behavior, kill switch, and rollback. The chatbot kill
command cleared the active pointer atomically and final readiness returned
`disabled`.

## Notification, concurrency, and failure-containment evidence

The canonical Phase 6 notification lifecycle was strengthened and locally
verified for:

- exact endpoint rotation while preserving other devices;
- stable provider idempotency keys across retries;
- bounded retryable evidence when an adapter raises;
- concurrent workers not delivering the same claimed outbox row twice;
- concurrent creation deduplicating one occurrence under advisory locking;
- cancellation during provider I/O containing local state and recording late
  provider acceptance without turning it into user-visible delivery;
- schedule-relative expiry;
- replay conflict, supersession, stale-source suppression, quiet hours, and
  redacted endpoint responses; and
- fail-closed adapter attempts without fabricated receipts.

The deterministic Phase 7 operational helpers additionally validate exact
staging targets, narrow backup/restore/rollback previews, isolated restore
database naming, content-free invariant counts, presence-only secret state,
sensitive-pattern counts, and an ordered 25-case fault-campaign state machine.
Provider/output/release, concurrency, conflict, notification, and containment
cases were exercised through deterministic tests; backup restoration and
API/schema/web rollback were additionally exercised on controlled staging.

## Final deployment and product evidence

| Required evidence | Final result |
|---|---|
| Source revision deployed | `7b8d004+api-portable-20ae98ff` |
| Final API image digest | `sha256:844e16893bf6b1b7e396cbd253cc50a861d651a69b91c4381203d5c0ce416803` |
| Final retrieval image digest | `sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89` |
| Final Flutter web content-manifest SHA-256 | `5468b6aca9697f3c0916d19e7b09cf49e2c1bad7689c0cd4c6370e019c0b82f0` |
| Final Flutter web archive SHA-256 | `1afefc00851466cec14f7167609f4b7740b44fa5da871a06c2ab78698d1c06b1` |
| Final staging Alembic revision/schema check | `20260730_0054`; no drift |
| Phase 7 post-deploy backup | 7 artifacts verified; restore catalog 890 lines |
| Public health/readiness smoke | passed; final AI/worker/transports disabled |
| Authenticated patient/doctor/payer staging smoke | passed before and after recovery |
| Slice D staging activation/disablement/rollback | v2 -> v3 -> exact v2; product path passed; killed |
| Slice F staging activation/disablement/rollback | v4 -> v5 -> exact v4; product path passed; killed |
| Chatbot authenticated generation/kill-switch | passed; active pointer cleared |
| Rendered inspection | deployed doctor UI inspected at 390, 820, and desktop widths; no final console warnings |
| Broader role/localization/accessibility inspection | 98 Flutter tests passed with 17 intentional skips; stable Phase 5/6 goldens and role tests retained |
| Presence-only artifact scan | 5 files; 0 suspected matches |
| Content-free staging log scan | 0 suspected matches |
| API/schema/web exact-predecessor rollback | predecessor digest + schema 0052 + archived web started healthy |
| Backup restoration and final recovery | post-activation dump restored; schema 0054/no drift; three-role smoke passed |
| Duplicate containment | concurrency/idempotency suites passed; no unexpected smoke replay duplicates |

## Credential-handling remediation

During exact cleanup of the disposable restore database, one failed operator
command emitted the staging database connection DSN to transient terminal
output. It was not written to repository artifacts, application logs, closure
evidence, metrics, screenshots, or provider metadata. The database user's
password was immediately rotated through PostgreSQL, the owner-readable host
environment was updated, the temporary rotation file was securely removed, and
schema `0054` plus public health were revalidated.

The `.env` copies inside the immutable pre/post rehearsal backups now contain an
intentionally obsolete database credential. Future recovery must restore data
and non-secret configuration, then securely re-inject the current database
credential rather than copying the archived credential into service.

## External blockers retained

- **APNs:** exact push entitlement, provisioning/signing, APNs key, secure raw
  token resolution, registration/permission path, and signed physical-target
  evidence are unavailable.
- **Alibaba Cloud EMAS Mobile Push:** exact Alibaba project/application, signed
  Android package identity, OEM credentials and approvals, privacy-consent
  initialization, secure endpoint resolution, and China-compatible physical
  target evidence are unavailable.
- **Web Push:** VAPID configuration, push service worker, subscription
  lifecycle/rotation/revocation, and supported HTTPS browser/network evidence
  are unavailable.
- **On-device scheduling:** explicit ownership and cancellation semantics are
  not implemented and therefore are not activated.
- **DeepSeek imaging:** the selected official API contract is text-only for this
  purpose; no image-capable release can be registered without genuine
  documented capability and a bounded image-input probe.

No provider acceptance, delivery, operating-system display, user observation,
real-world AI authorization, or commercial readiness is inferred from these
disabled readiness states.
