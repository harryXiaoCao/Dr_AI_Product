# Phase 5 Closure Record

Date: 2026-07-28

Status: complete for the controlled synthetic product framework

Base checkpoint: clean `main` commit `7b8d004`

This record closes Phase 5 of
`docs/Dr_AI_v1.0_Implementation_Plan.md`. It records the exact implemented
product-coherence, lifecycle, analytics, accessibility, rendered-product, and
controlled-staging evidence. It does not revise immutable Phase 1-4, Slice A-G,
evaluation, failed-result, passing-result, rollback, release, or historical
golden evidence.

## Implemented Slice

### Persisted three-role account-request lifecycle

- Migration `20260728_0052` adds an opaque public receipt, request checksum,
  version, retention/effect codes, withdrawal metadata, and append-only
  `support_request_events`.
- Patient, doctor, and payer users share one bilingual account-request center
  backed by requester-scoped create/list/detail/withdraw routes.
- Submission validates content, returns a visible receipt, survives navigation,
  and provides status, current/superseded history, retention boundaries, and
  next actions.
- Retry is content-bound and idempotent. Identical retries replay the original
  mutation; changed-content reuse returns a conflict and the client rotates the
  key only after an explicit conflict. Ambiguous network failure preserves the
  original key.
- Deletion requests are requests for governed review. The interface explicitly
  states that regulated and audit-retained records are not deleted
  immediately.
- Withdrawal is limited to contractually reversible states. Terminal records
  remain visible and immutable.
- Cross-role and cross-requester reads fail neutrally.
- Administrative transitions use a non-public local/test/staging command with
  an active synthetic operations actor. No admin or specialist product surface
  was added.

### Product language and histories

- Shared presentation vocabulary distinguishes submitted facts, immutable
  deterministic baselines, included/not-used/missing facts, synthetic
  references and effective dates, AI drafts, deterministic warnings and
  fallbacks, doctor responses, payer evidence, manual reviewer transitions,
  final human outcomes, and superseded history.
- Expected-care and payer views no longer expose payer-request UUIDs, raw
  purpose/status codes, or schema-oriented labels.
- Doctor and payer histories identify the actor, time, currentness, recorded
  reason, and next permitted action without exposing confidential reviewer
  notes.
- The medication notification shell is deliberately read-only and states the
  Phase 6 delivery boundary; it does not simulate device notification
  scheduling.
- Payer organization, membership, jurisdiction, verification, and
  authorization remain read-only. Only the existing allow-listed reviewer
  identity fields remain editable.

### Content-free analytics

- `POST /api/v1/product-events` accepts bounded event names and allow-listed
  dimensions for completion, failure, retry, conflict, fallback, replay,
  latency bucket, reliably observable abandonment, and existing in-product
  notification interactions.
- The server derives role and environment, hashes the client deduplication key,
  binds the event content to a checksum, enforces role/journey and
  event/outcome matrices, and returns replay/conflict deterministically.
- Content-free rows store no actor, patient, clinic, or resource identity. The
  database check constraint enforces that invariant.
- Unexpected storage failure returns a non-blocking accepted response with
  `persisted=false`; the user workflow is not blocked.
- Free text, direct contact, patient identity, message/imaging contents,
  confidential payer notes, secrets, and arbitrary dimensions are rejected by
  construction and executable tests.
- Phase 6 APNs, Android push, device tokens, delivery outbox, receipts,
  scheduled adherence notifications, and operating-system delivery were not
  implemented.

## Executable Local Evidence

Backend:

- full FastAPI suite: `379 passed`;
- focused Phase 5 lifecycle/analytics suite: `23 passed`;
- Ruff checks passed;
- migration upgrade/downgrade/upgrade round trip passed;
- Alembic `current`, `heads`, and `check` reported
  `20260728_0052 (head)` with no new upgrade operations;
- synthetic seed was idempotent;
- support-operations actor bootstrap returned `created` and then `reused`.

Flutter:

- `./scripts/verify_flutter.sh` completed with analyzer `No issues found`;
- `89` tests passed and `17` intentional platform/golden skip markers were
  reported by the repository verification harness;
- account-request coverage includes all three roles, provider loading/failure,
  history failure/retry, idempotency conflict/replay, keyboard focus,
  semantics, enlarged text, and bilingual mobile/desktop goldens;
- two new stable targets were visually inspected:
  `account_requests_patient_zh_412x917_large_text.png` and
  `account_requests_payer_en_1280x1100.png`;
- the historical doctor-resources golden files were not regenerated. Their
  known small host-renderer variance remains historical evidence rather than a
  rewritten target;
- the release web build completed. The non-fatal Cupertino icon-font warning
  remains because no visible Phase 5 control depends on that absent font.

Android:

- `/Volumes/AndroidAVD/sdk` was mounted and used; no Android SDK was downloaded
  to internal storage;
- debug APK:
  `apps/dr_ai_app/build/app/outputs/flutter-apk/app-debug.apk`;
- APK SHA-256:
  `58ee4fadec8d6ca6201ad3af84177c37622c356c46ecd7f6c034f2bdf526b143`.

Repository:

- `git diff --check` passed before packaging;
- unrelated historical evidence and existing work were preserved;
- no commit, push, history rewrite, or historical target regeneration was
  performed.

## Actual Built-Application Inspection

The release-built Flutter web app ran against an isolated PostgreSQL database
and the real FastAPI service. Browser inspection enabled the Flutter semantics
tree and exercised persisted journeys rather than fixture-only widget state.

Patient:

- navigated the persisted Records, Imaging, Medications, Recovery, Care &
  Cost, Contacts, and Account framework;
- submitted a synthetic account request, observed its receipt and timeline,
  retried safely without duplication, inspected the deletion retention
  boundary, confirmed withdrawal, and observed the terminal persisted history.

Doctor:

- opened the assigned synthetic patient and reviewed the current Clinical
  Event, history, imaging, medication, recovery, services, cost, immutable
  baseline, deterministic comparison/fallback material, and payer state;
- after a human payer clarification request, submitted an attributable
  clarification through the actual UI;
- observed the persisted doctor response and the request transition back to
  human review.

Payer:

- remained bound to `Synthetic Phase 5 Health Fund` and its exact request
  scope;
- inspected submitted facts, evidence, immutable baseline, comparison,
  clinician position, doctor response, and manual transition history;
- recorded an attributable `request_clarification` decision with a human
  reason and observed the persisted result and current timeline;
- verified that governed organization/membership/access fields remained
  read-only.

English and Simplified Chinese, desktop and narrow/enlarged-text states,
keyboard traversal, focus order, screen-reader semantics, loading, empty,
unavailable, permission-denied, conflict, retry, replay, fallback, success,
completion, and history states were covered by the combined rendered and
executable evidence.

## Controlled Tencent Synthetic Staging

Release identity:

- release:
  `20260728T100014Z-phase5-worktree-7b8d004-51c41a36`;
- source identity: uncommitted Phase 5 worktree based on `7b8d004`;
- API archive SHA-256:
  `51c41a365f0d7f4c46953a6c0a43e7341f36dfceddbf0661605410eb9c884381`;
- immutable API digest:
  `sha256:58244c2e385b3dcaa050820ed99d16d71b4ef25c35a5f685c471872afacb739b`;
- web archive SHA-256:
  `0e8f7ffbe049f5734feb9276cafd2033d8cd48b1a4fd82dee020b4ba30bf5741`;
- deployed `main.dart.js` SHA-256:
  `62aef133cdc707b7fcb802d0c09d9e900482b5269eec2aee02bba2ebc739b98b`.

Backup:

- directory:
  `/home/ubuntu/dr-ai/staging/backups/20260728T100014Z-phase5-worktree-7b8d004-51c41a36`;
- contains host `.env`, Compose/Caddy configuration, web bundle, release
  artifacts, PostgreSQL custom-format dump, and `SHA256SUMS`;
- all checksums verified before mutation;
- database dump SHA-256:
  `0d17c04e3918291abd802a32d3e359c87ed4880834b6fd7c9be6e9615f89484d`.

Deployment proof:

- migration upgraded `20260727_0051 -> 20260728_0052`;
- `current` and `heads` both reported `20260728_0052 (head)`;
- Alembic schema check reported no new upgrade operations;
- both post-migration seed runs reported every `*_created=0`;
- the existing retrieval image remained unchanged at
  `sha256:bc91102572ab164ef58b3b07a1594e9457cd53b0904a3ca83f2cbbc077346b89`;
- `/health` returned API/database `ok`, environment `staging`, patient-chat
  generation `disabled`, and expected-care explanation `disabled`;
- environment verification retained:
  `DR_AI_CHATBOT_PURPOSE_ENABLED=false`,
  `DR_AI_CHATBOT_KILL_SWITCH=true`,
  `DR_AI_EXPECTED_CARE_CANDIDATE_ENABLED=false`,
  `DR_AI_EXPECTED_CARE_EXPLANATION_ENABLED=false`, and
  `DR_AI_EXPECTED_CARE_EXPLANATION_KILL_SWITCH=true`.

Authenticated smoke:

- final marker: `STAGING SMOKE PASSED`;
- passed health, doctor/patient login, Phase 5 support
  conflict/isolation/history, analytics replay/redaction, profile write and
  duplicate conflict, refresh rotation/logout revocation, assigned-patient
  search, neutral cross-patient denial, imaging metadata, assessment,
  recovery, Today readback/completion, patient education, consultation,
  connected messaging, unconnected denial, and privacy deep link;
- the optional payer-credential branch was skipped because no payer credential
  was supplied in the staging secret set. Payer authorization and lifecycle
  passed the local actual-built-app journey and executable backend/Flutter
  suites; no credential was invented or exposed to turn the optional marker
  green.

Operational and redaction proof:

- a staging support request transitioned `queued -> reviewing`; an identical
  command replay returned `replayed` without a duplicate event; the request
  then transitioned `reviewing -> resolved`;
- requester readback returned `resolved`, version `3`, no further action, and
  one requester plus two support-team timeline events;
- the staging aggregate found one Phase 5 content-free event and confirmed its
  64-character stored deduplication digest plus null actor, patient, clinic,
  and resource identity fields;
- the presence-only recent API/Caddy log scan found no authorization, bearer,
  password, access-token, or refresh-token pattern. The scan did not print log
  lines or request content.

## Preserved Boundaries

- Patient-chat generation and both expected-care generation purposes remain
  disabled; applicable kill switches remain engaged.
- DeepSeek Vision remains absent because the supported DeepSeek API does not
  accept image input. No other provider was used as a proxy.
- Phase 6 system notification delivery remains open.
- The product remains synthetic-only. Real-patient transmission,
  real-provider evidence, live payer integration/adjudication, clinical,
  privacy, legal, regulatory, commercial, public-production, and app-store
  authorization remain separate gates.
- Immutable Slice A-G release/evaluation/failure/pass/rollback/closure records
  and historical goldens remain unchanged.

## Closure Decision

Every Phase 5 implementation item and exit criterion is complete within the
authorized controlled synthetic-development scope. The remaining items above
are explicit external or later-phase boundaries and do not require fabricated
approval, a substitute provider, hidden product behavior, or rewriting
historical evidence.
