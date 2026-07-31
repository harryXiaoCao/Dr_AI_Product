# Phase 5 Live Gap Matrix

Date: 2026-07-28

Status: closed for the controlled synthetic Phase 5 scope

This is the closed Phase 5 matrix for the product-coherence and lifecycle
slice. It begins from clean `main` commit `7b8d004`, which records the final
Phase 1-4 controlled Tencent staging deployment. It does not replace or revise
the immutable Phase 1-4, Slice A-G, release, evaluation, failure, rollback, or
golden evidence.

A row is complete only after its implementation and executable or rendered
evidence pass. An audited gap is not a completed implementation.

## Preserved Baseline

| Area | Audited starting state | Phase 5 rule | Status |
|---|---|---|---|
| Phase 1-4 product path | Patient, doctor, and exact-organization payer workflows are persisted through migration `0051`; the July 28 final-source staging deployment and authenticated redaction-safe smoke passed. | Extend in place and preserve role, event, request, lineage, and confidentiality boundaries. | Preserved complete |
| AI release state | Patient-chat generation and both expected-care generation purposes are disabled and kill-switched. Current source checksums differ from the immutable pending releases. | Do not activate or rewrite historical releases/evaluations. A future activation requires a checksum-compatible successor evaluation and release. | Preserved disabled |
| Imaging AI | Manual imaging upload/download and doctor-owned findings are available; official DeepSeek image input remains unavailable. | Do not proxy Vision through another provider or fabricate an AI draft. | Externally blocked purpose; manual path preserved |
| Historical goldens | The doctor-resources functional/accessibility checks pass, while the historical target has a small current-host renderer variance. | Diagnose without regenerating the historical target merely to make it green. | Preserved evidence |

## Route And Control Completion

| Area | Audited gap or requirement | Required evidence | Status |
|---|---|---|---|
| Full role inventory | Re-audit every patient, doctor, and payer page, card, tab, icon, button, menu item, filter, search field, form, dialog, history entry, retry, download, deep link, and unavailable state against the live route and API. | Checked inventory tied to real routes, persisted actions, deliberate read-only copy, or specific disable/removal reasons. | Complete; actual built-app journeys and 89 Flutter tests cover representative destinations and controls |
| Support/privacy surface | The prior deletion and feedback controls prepared widget-local state even though authenticated support-request persistence existed. | Bilingual persisted submission, receipt, readback, history, retry/conflict, cancellation where valid, truthful retention semantics, and role isolation. | Complete through the shared persisted request center and migration `0052` |
| Account integration | Legal copy says support/deletion/feedback can be tracked from account surfaces. | Patient, doctor, and payer account journeys show their own persisted requests and next action without exposing another requester. | Complete; shared account destination remains available through profile/care-provider loading and failure states |
| Histories | Existing domains retain substantial immutable history; Phase 5 applies one understandable actor/time/currentness/next-action language across clinical, financial, chat, support, and account records. | Representative data-backed history tests and rendered inspection for current, superseded, pending, failed, fallback, and final states. | Complete for implemented three-role domains; confidential/internal identifiers remain hidden |
| Duplicate representations | Providers, repositories, mappings, presentation models, and widgets were checked for independently representing the same persisted object or action. | Targeted consolidation with role-specific authorization/disclosure preserved; no broad speculative rewrite. | Complete through one account-request center, repository mapping, and small shared history/status primitives |

## Lifecycle And Analytics

| Area | Audited gap or requirement | Required evidence | Status |
|---|---|---|---|
| Support/feedback/deletion lifecycle | Migration `0052` adds public receipts, request checksums, versions, retention/effect codes, withdrawal, and append-only events over requester-scoped create/list/detail. | Authorization, cross-role isolation, content-bound idempotency, safe replay, conflict, recoverable failure, attributable transition, cancellation/withdrawal policy, deletion retention copy, and audit tests. | Complete; backend full suite 379 passed and focused Phase 5 suite 23 passed |
| Operational transitions | Phase 5 does not add a specialist or general administrator product surface merely to process synthetic requests. | Tightly scoped authorized backend/test-fixture transition path with no cross-role leakage or fabricated professional review. | Complete; non-public local/test/staging command, unloggable synthetic actor bootstrap, applied/replayed/resolved staging proof |
| Payer identity | Organization, membership, jurisdiction, verification, and authorization remain administrator-owned and read-only; only allow-listed reviewer identity fields are editable. | Payer lifecycle UI and tests retain the existing allow-list and neutral membership boundary. | Preserved and regression-covered |
| Content-free analytics | `/product-events` persists a bounded event/dimension contract with hashed deduplication, environment/role rules, content checksum, non-blocking storage failure, and identity-null database constraint. | Executable allow-list and redaction tests; no identity, direct contact, free clinical text, messages, imaging, reviewer notes, secrets, or content-bearing identifiers. | Complete; executable injection/matrix/replay/conflict/redaction tests and staging at-rest invariant passed |
| Notification analytics boundary | Existing in-product notification interactions may be instrumented. APNs, Android push, device tokens, notification outbox delivery, and scheduled adherence notifications belong to Phase 6. | Tests prove Phase 5 analytics does not implement or imply Phase 6 delivery. | Complete; interaction-only event names, no delivery infrastructure added |

## Rendered Product And Accessibility

| Area | Required evidence | Status |
|---|---|---|
| Role, locale, and viewport coverage | Representative patient, doctor, and payer data-backed states in English and Simplified Chinese on mobile, tablet, and desktop. | Complete in widget, golden, and actual built-app coverage |
| State coverage | Loading, empty, unavailable, permission-denied, stale, conflict, retry, replay, fallback, success, completion, and history. | Complete for implemented surfaces through data-backed tests and persisted journeys |
| Accessibility | Normal/enlarged text, keyboard-only navigation, deterministic focus order/restoration, screen-reader semantics, contrast, and long localized strings. | Complete; analyzer and accessibility/focus/semantics/enlarged-text tests passed |
| Goldens | Add only stable, meaningful Phase 5 states; inspect every changed or new target visually and preserve the unrelated historical doctor-resources target. | Complete; two new account-request targets visually inspected, historical doctor-resources files unchanged |
| Built application | Exercise representative three-role journeys through the actual built product, not widget assertions alone. | Complete locally through the release-built web app and isolated PostgreSQL-backed API |

## Documentation And Deployment

| Area | Audited starting state | Required completion evidence | Status |
|---|---|---|---|
| Source-of-truth reconciliation | The implementation plan, PRD, documentation index, AI architecture, deployment README, API contract, and ERD are reconciled to migration `0052` without rewriting dated historical evidence. | Update current documents without changing immutable dated evidence. API contract and ERD must follow the actual migration and route contracts. | Complete |
| Local gates | Phase 1-4 baseline passed backend, migration, Flutter, accessibility, golden, web-build, and rendered checks before Phase 5 began. | Re-run proportionate backend, migration, Flutter, rendered, Android, and whitespace gates after Phase 5 implementation. | Complete; exact commands/results are in the closure record |
| Android | SDK was mounted at `/Volumes/AndroidAVD/sdk`; no internal SDK was downloaded. | Build with the configured external SDK or record an external block. | Complete; debug APK built, SHA-256 recorded |
| Controlled staging | The Phase 5 worktree based on `7b8d004` is deployed through migration `0052` with a verified backup, immutable API digest, matching web hashes, two no-op seeds, passing smoke, lifecycle replay proof, at-rest analytics assertion, and clean presence-only log scan. | Preserve AI/retrieval state and exact evidence. | Complete; optional payer credential smoke skipped truthfully because no staging payer secret was supplied, while payer behavior passed the local built-app journey and authorization suite |

## Exit Criteria

- Every visible control is functional, deliberately read-only, or
  removed/disabled with truthful specific copy.
- Every three-role journey has a beginning, persisted middle, recoverable
  failure path, and visible completion.
- No demo interaction is visually indistinguishable from a persisted action.
- Support, feedback, deletion-request, and account lifecycles are persisted,
  isolated, auditable, replay-safe, recoverable, and truthful about retention.
- Product analytics is content-free, allow-listed, deduplicated where
  appropriate, environment/role bounded, non-blocking, and redaction-tested.
- English and Simplified-Chinese mobile, tablet, desktop, enlarged-text,
  keyboard, focus, semantics, contrast, state, golden, and built-application
  evidence pass.
- Controlled Tencent synthetic staging is refreshed only after local gates
  pass, while all pending AI purposes remain disabled and kill-switched.

All Phase 5 exit criteria are satisfied within the authorized synthetic scope.
The DeepSeek image-input limitation, real-patient/provider/payer authorization,
public production, Phase 6 delivery infrastructure, and the known historical
host-renderer variance remain explicit external or later-phase boundaries, not
unfinished Phase 5 implementation.
