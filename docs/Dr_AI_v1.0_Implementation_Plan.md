---
title: "Dr. AI v1.0 Implementation Plan"
status: "Phases 1-4 locally complete; external provider, Android volume, and final controlled-staging evidence recorded"
created: "2026-07-02"
last_updated: "2026-07-27"
owner: "Harry Cao"
release_target: "Production-quality, China-first medical-information and care-cost transparency platform; synthetic controlled staging until later real-world gates close"
---

# Dr. AI v1.0 Implementation Plan

This file is the durable implementation source of truth for Dr. AI v1.0.
Future work must read this plan before changing product scope, architecture, or
release status.

The current product is **not an autonomous medical-diagnosis agent**. Dr. AI is
a three-party medical-information and care-cost transparency platform intended
to reduce information inequality and make potential misuse or inefficient use
of medical resources easier for people to examine. It helps patients, doctors,
and authorized payer reviewers see the same care episode from appropriate,
role-safe perspectives.

Dr. AI may estimate, compare, explain, and warn. It must not independently:

- create the authoritative medical diagnosis;
- prescribe or change treatment;
- determine medical necessity;
- approve, deny, reduce, or delay a payer request;
- label a patient, doctor, hospital, or request as abusive, fraudulent, or
  wasteful; or
- impose any punitive or reimbursement action.

Doctors remain responsible for recorded diagnoses, prescriptions, clinical
plans, and justifications. Authorized payer reviewers make payer decisions
manually.

## Source-of-Truth Documents

- Product requirements: `Dr_AI_Product_Requirements_Document_v1.0.md`
- Data boundary: `docs/Dr_AI_v1.0_ERD.md`
- API contract: `docs/Dr_AI_v1.0_API_Contract.md`
- Product quality gate: `docs/Dr_AI_v1.0_Product_Quality_Gate.md`
- AI platform architecture:
  `docs/Dr_AI_v1.0_AI_Platform_Architecture.md`
- First-scenario reference boundary:
  `docs/Dr_AI_v1.0_First_Scenario_Reference_Boundary.md`
- Current A-G closure evidence:
  `docs/periodic_dev_docs/Phase_4_Slices_F_G_Comparison_Explanation_Governance_Record.md`

When an older requirement conflicts with this plan, this plan's 2026-07-26
product boundary controls. Completed historical work remains evidence, but
unfinished diagnosis-agent or clinic-operations backlog does not silently
become current v1.0 scope.

## Current Product Boundary

### Primary users

1. **Patient**
   - owns and reviews their profile and medical history;
   - sees Clinical Events, records, imaging, prescriptions, medications,
     recovery plans, reminders, cost baselines, submitted costs, payer status,
     and patient-safe explanations;
   - uses the Dr. AI chatbot for bounded medical-information support;
   - never sees confidential payer notes, internal service codes, or another
     patient's information.

2. **Doctor**
   - records symptoms, diagnoses, prescriptions, medications, imaging,
     consultations, checks, treatments, recovery plans, and delivered services;
   - reviews the source facts used by AI;
   - sees the immutable expected-cost range and deterministic comparison;
   - submits a payer request and appends additional information or justification
     when warned about missing information or an unusual cost variance;
   - never receives an automatic payer approval or denial from AI.

3. **Authorized payer reviewer**
   - is bound to an active payer-organization membership and the exact submitted
     request;
   - sees submitted facts, the role-safe expected-cost range, deterministic
     comparison, clinician response, and human payer state as separate objects;
   - requests clarification and manually accepts, rejects, escalates, or closes
     the request with an attributable reason;
   - cannot access other payer organizations or unrelated patients.

### Supporting product surfaces

- Authentication, registration/invite, session restoration, account/profile,
  language, support, feedback, and deletion requests.
- Doctor-patient relationships, contacts, messaging, and activity history.
- Clinical Event / Care Episode records and event-linked medical information.
- Imaging upload and review, including a clearly labeled DeepSeek Vision
  demonstration result.
- Persisted notification inbox and operating-system notification delivery.
- Audit, observability, backups, deployment, release governance, kill switches,
  and rollback.

### Removed from the current v1.0 implementation backlog

The following unfinished ideas came from the former diagnosis-agent or broad
clinic-management vision and do not block the current v1.0:

- autonomous diagnosis or lung-cancer-risk product claims;
- GCAVE-GAN/AMCM production inference;
- AI-authored treatment or recovery plans;
- medication-change or prescribing agents;
- medicine inventory, equipment, beds, ambulance, and referral-resource
  management;
- general hospital administration, doctor-team management, and revenue
  dashboards;
- voice/video consultation, DICOM segmentation, barcode scanning, wearables,
  national EHR integration, disease surveillance, and public-health analytics;
- automated claim adjudication, eligibility determination, payment transfer,
  denial, appeal resolution, fraud detection, or clinician ranking.

These capabilities require a future explicit plan amendment before product
implementation. Existing completed foundations may remain in the repository
when they are harmless and reusable, but their visible unfinished UI must be
removed, disabled with a truthful explanation, or converted into a supported
workflow.

## AI Product Contract

### DeepSeek backbone

DeepSeek is the required v1.0 backbone for every generative or multimodal AI
purpose. No other generative provider may silently serve a v1.0 product request.
The server may retain provider-neutral transport interfaces for tests,
deterministic stubs, outage fallback, and future migration, but the configured
runtime provider for each enabled v1.0 AI purpose must be DeepSeek.

Every AI purpose must still have its own:

- purpose code and allowed users;
- server-built input allow-list;
- DeepSeek model and endpoint configuration;
- prompt, schema, and model version;
- deterministic validation;
- timeout, retry, quota, and concurrency policy;
- content-free telemetry and audit evidence;
- evaluation suite and governed release;
- kill switch, structured fallback, and rollback target.

One purpose must never reuse another purpose's prompt, schema, validator,
metrics, or release decision merely because both use DeepSeek.

### Purpose 1: expected clinical-event cost

DeepSeek drafts a structured expected-care candidate. Deterministic server logic
publishes the immutable baseline only after validating it against admitted,
versioned synthetic or future governed references.

The cost boundary covers every billable clinical service associated with the
Clinical Event, including:

- prescribed medications and delivered medication products;
- imaging procedures;
- laboratory and other checks/tests;
- doctor and specialist consultation sessions;
- rehabilitation and recovery-treatment sessions;
- other delivered treatment or service records explicitly marked billable.

Prescription documents, appointment placeholders, diagnoses, notes, imaging
files/reports, recovery-plan documents, reminders, and evidence attachments are
medical-information records, not separately priced line items. Their linked
delivered services or products may be priced.

The server assembles the minimum relevant fact object from:

- symptoms and clinical context entered by the doctor;
- medical history, allergies, conditions, and current medications from the
  patient's account;
- doctor-uploaded imaging and the separately labeled DeepSeek Vision draft;
- doctor-confirmed imaging findings or diagnoses;
- prescriptions, medications already taken, adherence events, and recovery
  plan progress;
- completed and planned consultations, laboratory work, imaging, treatments,
  rehabilitation, quantities, units, and dates;
- documented missing or conflicting information; and
- admitted reference releases applicable to the scenario, currency,
  jurisdiction, facility scope, and effective date.

Every displayed estimate must expose, through role-safe views:

- the low and high amount in integer minor units and currency;
- included service categories and quantities;
- source facts used and facts not used;
- source/reference version, effective date, and synthetic status where
  applicable;
- assumptions, missing information, conflicts, and confidence category;
- model, prompt, schema, validator, and release versions in audit/readiness
  metadata without exposing secrets or internal identifiers;
- deterministic comparison with the submitted cost; and
- immutable history and predecessor differences.

AI output is not an official price, negotiated rate, coverage rule, clinical
guideline, or payer conclusion. Provider failure must preserve manual clinical
documentation, `pending_cost`, payer clarification, and structured fallback.

### Purpose 2: cost and comparison explanation

DeepSeek selects only admitted fact IDs, claim types, and allowed connective
language. The server renders protected amounts, currencies, quantities, units,
dates, percentages, codes, labels, names, and identifiers from one canonical
claim graph into English and Simplified Chinese.

Generated prose may not independently narrate or modify protected values.
Doctor, patient, and payer explanations use different server-owned fact objects
and visibility rules. Unsupported claims, bilingual contradictions, protected
value mutations, confidential leakage, or prohibited clinical/payer conclusions
must fail validation and use structured fallback.

### Purpose 3: imaging interpretation demonstration

A doctor uploads an imaging asset through the governed file workflow. The
server invokes the configured DeepSeek multimodal/vision endpoint and stores an
immutable, versioned **AI imaging observation draft** with provenance,
limitations, confidence, and failure state.

The product must label this output as AI-generated and unconfirmed. It may
identify candidate observations for doctor review, but it must not silently
write the patient's diagnosis, medical necessity, treatment, or payer outcome.
The doctor may record a separate human finding or diagnosis and may reference,
correct, or disagree with the AI draft without editing the draft itself.

Patients and authorized payers may see only the role-authorized, product-approved
view. Raw model reasoning, hidden prompts, unrelated image metadata, reviewer
notes, and internal identifiers must not be exposed.

### Purpose 4: Dr. AI chatbot

The Dr. AI chatbot uses DeepSeek for generated answers. Server-controlled
emergency routing, privacy and authorization checks, bounded context selection,
governed retrieval, source admission, semantic claim validation, and fixed
fallback remain authoritative.

The chatbot may provide bounded medical information and help a user understand
their own role-authorized records. It must not become an autonomous diagnosis,
individualized prescribing, medication-change, payer-decision, or record-write
agent. It must disclose source and limitation state and remain usable when the
provider times out, returns malformed output, reaches quota, or is disabled.

## Notification and Reminder Contract

Notifications are a product system, not transient widget state. Each
notification must be persisted, authorized, localized, auditable, and delivered
through an operating-system notification adapter where the user has granted
permission. The app also retains an in-product inbox so denied device permission
or delivery failure does not erase the event.

Required patient notifications:

- medication dose and refill reminders;
- prescription availability or change recorded by a doctor;
- recovery-plan task and follow-up reminders;
- consultation/check/imaging schedule reminders;
- payer clarification or human decision status when patient-visible.

Required doctor notifications:

- a medication or recovery-plan task has no completion recorded after the
  configured grace period, or reliable adherence evidence records that it was
  not followed;
- a payer reviewer manually accepted, rejected, escalated, closed, or requested
  clarification for a submitted request;
- the submitted/requested cost is below or above the published expected range;
- expected-cost generation or comparison needs additional information;
- an imaging observation draft is ready or failed validation.

Cost-variance notifications are warnings only. For example, when the governed
expected range is synthetic CNY 5,000-10,000 and the doctor submits synthetic
CNY 2,000 or 20,000, the system asks for additional information or a
justification. It does not reject, rewrite, block, approve, or deny the request.
The original estimate, submitted cost, warning, doctor response, and payer
decision remain separate immutable evidence.

The deterministic comparison service, not DeepSeek prose, creates
missing-information and outside-range warning events. When the only fact is a
missing patient check-in, notification copy must say that no completion was
recorded; it must not claim proven non-adherence.

Notification requirements:

- persisted `notification_event`, user preference, device endpoint, delivery
  attempt, and receipt state rather than a UI-only alert;
- a server-owned event/outbox worker and platform adapter boundary for APNs,
  the selected production-region-compatible Android push transport, and Web
  Push; scheduled on-device reminders may supplement but not replace the
  authoritative server event;
- content-bound idempotency and duplicate suppression;
- per-user locale, time zone, quiet hours, and channel preference;
- explicit patient/doctor event subscriptions;
- no sensitive clinical detail on a locked screen by default;
- permission requested in context, with a usable denied-permission state;
- delivery attempt, success/failure, retry, read, and dismissal state;
- deep links only to an authorized current-session destination;
- deterministic reminder scheduling and cancellation after completion;
- stale reminder suppression and replay-safe background processing;
- accessible in-app inbox, keyboard navigation, and English/Simplified-Chinese
  copy;
- system-notification adapters for supported Flutter targets, with early
  controlled staging allowed to use synthetic recipients and device tokens
  only.

SMS, email, and consumer messaging integrations are not required for this
slice. They need a later explicit channel, consent, privacy, and operational
decision.

## Data and Transparency Rules

- A Clinical Event / Care Episode is the organizing unit for symptoms,
  diagnoses, records, imaging, prescriptions, medications, recovery plans,
  delivered services, costs, comparisons, payer requests, and notifications.
- The patient account is the source for patient-owned medical history.
  Doctors verify or append professional records; they do not silently overwrite
  patient-entered history.
- Price delivered medication, consultation, imaging, laboratory, rehabilitation,
  and treatment-service records. Do not price records merely because they
  contain clinical information.
- Clinical work may be saved as `pending_cost`. Payer submission requires a
  complete, positive, single-currency allocation that reconciles exactly.
- Money uses integer minor units. Quantities, units, service dates, currency,
  source/effective dates, and codes are explicit.
- Baselines, comparisons, doctor responses, payer requests, payer decisions,
  AI explanations, and notifications are append-only or immutable where
  required by their contract.
- All early-stage patients, clinicians, payer organizations, claims, prices,
  references, images, reviewers, and utilization facts are synthetic.
- Every invented value is explicitly synthetic and never represented as an
  official price, clinical guideline, negotiated rate, coverage rule,
  regulatory conclusion, or real patient fact.
- Role views may differ only by explicit authorization and confidentiality
  rules. They must not disagree about a shared admitted fact.

## Stage and Review Boundary

The current stage is early synthetic development and controlled staging.
External human approval is not required for synthetic development, tests,
internal demonstrations, or controlled Tencent staging.

Current-stage review fields must use truthful values such as:

- `not_required_for_early_synthetic_development`; or
- `product_owner_waived_for_current_stage`.

They must never claim that clinical, pricing, native-Simplified-Chinese,
privacy, security, legal, payer-workflow, or regulatory review was externally
or professionally completed when it was not.

Separate future gates remain mandatory before:

- real-patient data;
- real-provider clinical use;
- live payer organizations, eligibility, claims, or decisions;
- hospital or payer-system integration;
- public production or app-store distribution;
- commercial operation; or
- claims of savings, reduced abuse, clinical benefit, official pricing,
  reimbursement accuracy, or regulatory readiness.

Production-quality architecture, persistence, authorization, accessibility,
concurrency, observability, rollback, and failure behavior are not waived.

## Execution Phases

The former proposed “Phase H” is not a separate phase. Product completion,
real-AI workflow readiness, notifications, and activation rehearsal are
integrated into Phases 2-7 below.

### Phase 0 - Product boundary and source-of-truth cleanup

Status: **complete for the current plan**

- [x] Reframe v1.0 around medical-information equality and care-cost
  transparency.
- [x] Keep diagnosis, treatment, and payer decisions human-owned.
- [x] Make patient, doctor, and payer reviewer the three primary roles.
- [x] Remove unfinished autonomous diagnosis-agent and broad clinic-operations
  backlog from current v1.0.
- [x] Preserve completed work and historical evidence without making it current
  scope.
- [x] Record the early synthetic-development boundary and future live-use
  gates separately.

### Phase 1 - Identity, persistence, authorization, and audit foundation

Status: **complete and regression-covered through migration 0051**

- [x] Authentication, sessions, registration/invite foundation, role-aware
  routing, and fail-closed unsupported roles.
- [x] Patient/doctor identity and care-relationship foundation.
- [x] Payer organizations and active organization-scoped memberships.
- [x] Clinical Event-linked medical and cost persistence foundations.
- [x] Support, feedback, deletion-request, audit-event, and notification data
  foundations.
- [x] English/Simplified-Chinese localization foundation.
- [x] Keep all sensitive reads/writes, cross-role boundaries, idempotency, and
  concurrency behavior covered as later workflows are completed.
- [x] Remove or explicitly gate any obsolete specialist/admin routes that are
  not required by this plan.

Exit criteria:

- no unsupported role inherits another role's access;
- all current workflow objects have explicit ownership and authorization;
- migrations are upgradeable and schema drift checks pass;
- audit data excludes secrets and unnecessary clinical content.

### Phase 2 - Complete Clinical Event and three-party product workflows

Status: **locally complete through the coherent three-party synthetic journey**

Doctor:

- [x] Patient workspace, Clinical Events, baseline medical information, care
  documentation, medications/prescriptions, recovery plans, imaging metadata,
  care-cost items, payer requests, and human messaging foundations.
- [x] Complete the single coherent flow:
  Clinical Event -> symptoms/history -> records/imaging -> prescription,
  medication, consultation/check/treatment/recovery plan -> delivered service
  and cost -> expected baseline -> comparison -> payer request.
- [x] Make include/exclude-from-current-cost-context choices explicit where
  clinically and contractually appropriate.
- [x] Complete real file-upload finalization, safe validation, retry/recovery,
  authorized download, and immutable file provenance.
- [x] Complete history for medical records, imaging drafts/findings, baselines,
  comparisons, explanations, justifications, requests, and payer decisions.

Patient:

- [x] Dashboard, Today tasks, medical/recovery foundations, care-and-cost
  ledger, expected-care baseline/comparison/explanation read paths, contacts,
  and messaging.
- [x] Make Records, Imaging, Medications, Recovery, Care & Cost, Contacts, and
  Account real destinations backed by persisted state.
- [x] Always retain the immutable baseline and a structured fallback even when
  DeepSeek is unavailable.
- [x] Provide explicit explanation request/retry and complete history states.

Payer:

- [x] Organization-scoped queue, exact request read, itemized facts,
  clarification, accept/reject/escalate/close, and role-scoped expected-care
  views.
- [x] Complete evidence, doctor-justification, comparison, explanation, and
  transition history as visibly distinct sections.
- [x] Preserve exact request binding across refresh, retry, and concurrent
  reviewer actions.
- [x] Keep every final payer outcome a manual reviewer action.

Shared UI quality:

- [x] Audit every visible card, tab, icon, button, menu item, and deep link.
  Each must be a real authorized action, a useful navigation destination, a
  clearly read-only information surface, or removed/disabled with truthful
  copy.
- [x] Add responsive mobile/desktop layout, accessible semantics, deterministic
  keyboard navigation, focus restoration, and contrast.
- [x] Add loading, empty, unavailable, permission-denied, conflict, stale,
  fallback, retry, replay, success, and history states.
- [x] Keep content-bound idempotency keys server-verifiable. Flutter must never
  construct provider facts or protected AI values.
- [x] Inspect real rendered English and Simplified-Chinese states, not only
  fake-data widget assertions.

Exit criteria:

- no production-facing dead end or placeholder remains;
- each mutation persists, authorizes, audits, replays safely, and has a visible
  outcome;
- exact patient, doctor, and payer views pass cross-scope tests;
- the end-to-end synthetic episode can be completed from each role.

### Phase 3 - DeepSeek chatbot and medical-information workflow

Status: **local implementation and executable product-path evaluation
complete; controlled synthetic staging activation and live DeepSeek assurance
remain open**

- [x] Server-side DeepSeek chat adapter and bounded purpose contract.
- [x] Deterministic emergency and prohibited-medication-change routing.
- [x] Governed retrieval, provenance, rights/review metadata, context
  minimization, planner bounds, claim support, and fixed fallback foundations.
- [x] Immutable evaluation artifacts retain both passing and failing runs.
- [x] Set DeepSeek as the only enabled v1 generated-answer provider while
  retaining deterministic test stubs and fixed non-provider fallbacks.
- [x] Complete patient chat thread create/list/open/archive/delete behavior and
  visible source/limitation states.
- [x] Complete role-authorized patient-record context with a visible “used in
  this answer” summary and no whole-record transmission.
- [x] Run executable bilingual, privacy, injection, malformed-output, timeout,
  quota, context-drift, and cross-patient gates from the real product path.
- [x] Rehearse kill switch, provider outage, and rollback without losing access
  to deterministic emergency guidance or the rest of the product.

Local evidence: migration `0050` adds immutable checksum-bound releases and
events plus an exact mutable active pointer; incompatible, missing, disabled,
or kill-switched releases fail closed. The frozen suite at
`evaluation/chatbot/frozen_suite.v1.json` passed all 11 product-path gates with
zero live provider calls. The pending v1 release remains deliberately
kill-switched until controlled Tencent synthetic staging and a live DeepSeek
assurance run are recorded. Paid calls were authorized for this work, but no
DeepSeek credential was present in the repository or process environment.

Exit criteria:

- a user can complete the real chatbot workflow in controlled synthetic staging
  (**open external verification**);
- every generated answer is DeepSeek-backed, governed, validated, and
  traceable to admitted inputs;
- unsafe or failed generation degrades to deterministic product-owned behavior.

### Phase 4 - DeepSeek care-cost intelligence and imaging input

Status: **cost/fact transparency complete locally; historical A-G evidence
preserved; DeepSeek Vision externally blocked and activation remains Phase 7**

Completed A-G foundation:

- [x] Governed synthetic rehabilitation, laboratory, imaging, and
  consultation/treatment reference families with versions, effective dates,
  checksums, currency, units, applicability, provenance, and expected outcomes.
- [x] Separate DeepSeek `expected_care_candidate` contract and executable
  evaluation.
- [x] Immutable deterministic expected-care baseline and comparison history.
- [x] Canonical bilingual claim-graph explanations with protected server-rendered
  values.
- [x] Executable machine gates for arithmetic, visibility, fallback, release
  drift, provider failure, adversarial mutations, cross-scope attacks,
  concurrency, and idempotency.
- [x] Immutable v1/v2 history, append-only v2 unsuitable evidence,
  predecessor-linked pending v3, and a separate pending Slice D release.
- [x] Advisory-locked release operations, exact expected-version/checksum
  checks, purpose kill switch, activation, supersession, explicit rollback, and
  append-only transition evidence.
- [x] Doctor/patient/payer baseline, comparison, explanation, retry, and history
  actions in Flutter.
- [x] Controlled Tencent staging deployment through migration `0047`, with AI
  purposes disabled and v3 pending after the A-G closure.

Open completion work:

- [ ] Implement the DeepSeek Vision purpose as a separate prompt/schema/
  validator/evaluation/release domain.
  **External provider-capability block confirmed 2026-07-27:** the current
  official DeepSeek V4 API is text-only and does not accept image inputs.
  DeepSeek's documented integration workaround sends images through a different
  provider, which is prohibited by this plan's DeepSeek-only rule. Per the
  authorized task boundary, this purpose remains absent and disabled rather
  than using a proxy model. Manual imaging upload and doctor-owned findings
  remain available. Re-open only after DeepSeek publishes an official
  image-input API suitable for this separately governed purpose.
- [x] Bind imaging drafts and doctor-confirmed findings into the exact,
  role-visible cost-estimation fact object without letting either overwrite the
  other.
- [x] Expand synthetic episode fixtures across rehabilitation, laboratory,
  imaging, consultation, medication, prescription, and treatment combinations,
  including missing/conflicting facts and alternative pathways.
- [x] Complete transparent “facts used / facts not used / missing facts”
  presentation for doctor, patient, and payer.
- [x] Add patient-safe and payer-safe imaging/cost explanations from canonical
  facts; never expose confidential reviewer notes or internal identifiers.
- [ ] Activate Slice D and Slice F separately during the Phase 7 controlled
  rehearsal only after checksum-compatible executable gates pass.

Authoritative closure evidence:

- `docs/periodic_dev_docs/Phase_4_Slices_B_C_Care_Reference_Foundation_Record.md`
- `docs/periodic_dev_docs/Phase_4_Slice_D_Expected_Care_Candidate_Record.md`
- `docs/periodic_dev_docs/Phase_4_Slice_E_Doctor_Review_and_Presentation_Record.md`
- `docs/periodic_dev_docs/Phase_4_Slices_F_G_Comparison_Explanation_Governance_Record.md`

Exit criteria:

- one synthetic event exercises symptoms, history, imaging, medications,
  recovery progress, services, quantities, and costs through the real product
  path;
- DeepSeek purposes are independently governed and deterministic validation
  remains authoritative;
- role views are transparent, fact-consistent, and confidentiality-safe;
- provider failure never blocks documentation, comparison, justification, or
  manual payer review.

### Phase 5 - Product refinement and feature-complete framework

Status: **open**

This phase completes the framework; it is not a cosmetic-only polish pass.

- [ ] Run a fresh route/control audit against the live Flutter application and
  current API, replacing the old diagnosis-agent audit as the working list.
- [ ] Resolve every incomplete visible destination under the Phase 2 role
  workflows.
- [ ] Consolidate duplicate widgets that represent the same persisted object or
  action.
- [ ] Use one visual language for facts, AI drafts, deterministic results,
  human responses, warnings, and final human decisions.
- [ ] Make histories and state transitions understandable without requiring
  internal IDs or developer knowledge.
- [ ] Complete support, feedback, deletion-request, and account lifecycle
  submission/readback states needed by the three primary roles.
- [ ] Add content-free product analytics for task completion, failure category,
  retry, fallback, notification delivery, and latency.
- [ ] Add screenshot/golden coverage for representative real data-backed
  mobile, tablet, and desktop states in both languages.
- [ ] Inspect rendered flows with keyboard-only navigation and system text
  scaling.

Exit criteria:

- every visible control meets the Phase 2 shared UI rule;
- every user journey has a beginning, persisted middle state, recoverable
  failure path, and visible completion;
- no “demo” interaction is visually indistinguishable from a real persisted
  action;
- feature completion and visual refinement are verified on real rendered
  synthetic staging states.

### Phase 6 - System notifications, adherence, and warning workflow

Status: **open**

- [ ] Finalize notification event types, severity, audience, deduplication key,
  scheduling rule, expiry, and deep-link contract.
- [ ] Complete persisted notification event/outbox, user preference, device
  endpoint, delivery attempt, receipt, and retry contracts.
- [ ] Implement APNs, the selected production-region-compatible Android push
  adapter, Web Push, and supported on-device scheduling behind one server-owned
  delivery boundary.
- [ ] Implement patient medication, refill, recovery-task, follow-up, and
  consultation/check/imaging reminders.
- [ ] Implement doctor adherence warnings, payer-transition notifications,
  missing-information warnings, cost-variance warnings, and imaging-draft
  status notifications.
- [ ] Add doctor justification as an append-only response to a warning; never
  mutate the estimate, comparison, request, or payer decision.
- [ ] Deliver through supported operating-system notification adapters and the
  persisted in-app inbox.
- [ ] Add opt-in/permission, quiet hours, locale/time-zone, privacy-safe preview,
  retry, delivery receipt, read/dismiss, expiry, and cancellation.
- [ ] Test missed schedules, duplicate jobs, offline devices, token rotation,
  revoked permission, clock/time-zone change, stale reminders, and concurrent
  completion.
- [ ] Test that warning generation never becomes automatic payer adjudication or
  blocks a doctor's submission.

Exit criteria:

- synthetic reminders reach the supported device/system notification surface
  and remain visible in the authorized inbox;
- duplicate or stale notifications are suppressed deterministically;
- doctor warning -> additional information/justification -> manual payer
  decision works end to end;
- locked-screen content and deep links do not leak sensitive information.

### Phase 7 - Controlled staging activation and operational rehearsal

Status: **open**

- [ ] Back up the controlled staging database and record exact deployed image,
  web, schema, configuration, and release checksums.
- [ ] Run migrations and schema-drift checks against the staged source state.
- [ ] Register stage-specific waivers truthfully; do not fabricate external
  approval.
- [ ] Activate the corrected pending Slice F v3 through the governed command,
  verify readiness, use it from the real doctor/patient/payer UI, then
  re-engage the kill switch.
- [ ] Activate the separate Slice D release, exercise
  candidate -> baseline -> comparison -> explanation, then re-engage its kill
  switch.
- [ ] Register, activate, test, disable, and roll back the separate DeepSeek
  Vision release after its machine gates pass.
- [ ] Exercise DeepSeek chatbot generation from the product UI and its
  timeout/quota/malformed/kill-switch fallbacks.
- [ ] Exercise operating-system notifications on supported real targets using
  synthetic accounts and device tokens.
- [ ] Rehearse provider outage, stale/checksum-drifted release, malformed
  output, concurrent requests, idempotency conflict, database contention,
  notification failure, rollback, and exact-predecessor recovery.
- [ ] Verify content-free readiness/latency/error/usage metrics, redaction-safe
  logs, backups, and rollback evidence.
- [ ] Produce a synthetic stakeholder walkthrough and limitations report for
  doctor, patient, and payer journeys.

Exit criteria:

- all mandatory results are calculated from executed observations;
- real product UI paths invoke enabled DeepSeek purposes only while their
  compatible governed release is active;
- kill switch and rollback restore the expected content-free readiness state;
- no synthetic exercise creates real-patient, real-provider, live-payer,
  public-production, or commercial evidence.

## Cross-Phase Verification Matrix

Every open phase must add or preserve executable coverage for:

| Area | Mandatory evidence |
|---|---|
| Authorization | Patient, doctor, payer membership, organization, exact request, and cross-scope attacks |
| Persistence | Immutable history, append-only events, migrations, constraints, and exact readback |
| Money | Integer minor units, allocation reconciliation, mixed currency, pending cost, missing cost, and range boundaries |
| AI contracts | Schema, admitted facts, protected values, bilingual equivalence, unsupported claims, prompt injection, timeout, quota, error, and fallback |
| Release governance | Checksums, effective dates, stale/inactive/superseded releases, drift, expected version, idempotency, advisory locks, activation, kill switch, rollback, and conflicting active release prevention |
| Transparency | Facts used/not used, synthetic labels, source/effective dates, uncertainty, role-safe baseline, comparison, explanation, human response, and payer decision |
| Notifications | Schedule, permission, privacy preview, duplicate suppression, delivery/retry, expiry, read/dismiss, deep-link authorization, and time-zone behavior |
| UI | English/Simplified Chinese, mobile/desktop, keyboard, semantics, loading, empty, conflict, unavailable, retry, fallback, replay, and history |
| Operations | Health/readiness, redaction-safe logs, backups, restore/rollback, observability, and controlled staging smoke |

A listed case is not a passing case. Machine-gate metrics must be computed only
from executed observations. Failed and passing runs are retained; history is
never overwritten to improve a release result.

## v1.0 Engineering Definition of Done

Dr. AI v1.0 is engineering-complete for the early synthetic stage only when:

1. Every production-facing control is functional, deliberately read-only, or
   removed/disabled with truthful copy.
2. Patient, doctor, and payer can complete their role-specific end-to-end
   synthetic workflows without a developer tool.
3. Every mutation is persisted, authorized, validated, audited, idempotent, and
   recoverable from conflict or provider failure.
4. Every enabled generative or multimodal product purpose uses DeepSeek through
   its own governed contract and active compatible release.
5. Cost estimation transparently uses the admitted subset of symptoms, patient
   history, imaging drafts/findings, medications, adherence/recovery progress,
   consultations, checks, treatments, quantities, and costs.
6. AI imaging output remains a reviewable draft and never silently becomes the
   recorded diagnosis.
7. Cost variance produces a warning and a doctor-justification opportunity,
   never an automatic block, approval, denial, or accusation.
8. Payer decisions remain manual and attributable.
9. Patient reminders and doctor workflow warnings reach the supported system
   notification surface and persisted inbox without sensitive lock-screen
   leakage.
10. English and Simplified-Chinese rendered workflows meet the accessibility,
    responsive-layout, fallback, and history requirements.
11. Backend, Flutter, migration, evaluation, staging smoke, concurrency,
    rollback, and rendered-state checks pass.
12. Synthetic-stage waivers and future real-world gates are represented
    truthfully and separately.

This definition proves a production-quality framework and controlled synthetic
readiness. It does not prove clinical efficacy, official pricing, reimbursement
accuracy, reduced misuse, regulatory authorization, or readiness for real
patients, real providers, live payers, public production, or commercial use.

## Historical Evidence Policy

The former multi-page diagnosis/chatbot milestone tracker and per-change log
were removed from this active plan because they obscured current scope and left
obsolete unchecked work looking mandatory.

Historical evidence remains in Git history and in the repository's dated
closure records, evaluation artifacts, release manifests, migration history,
deployment runbooks, and `docs/periodic_dev_docs/`. Do not edit immutable
release/evaluation history to match this cleaned plan. When a completed
foundation is reused, cite its existing evidence rather than copying a large
historical log back into this file.

## Worktree and Change Rules

- Preserve unrelated dirty changes and all completed Slice A-G work.
- Inspect current code and source-of-truth documents before implementation.
- Prefer one coherent vertical slice across persistence, API, Flutter,
  evaluation, governance, documentation, and controlled staging.
- Do not commit, push, deploy, activate a release, contact an external party,
  or use real data unless the relevant request explicitly authorizes it.
- Documentation status must distinguish implemented, locally verified,
  controlled-staging verified, and future-gated work.
- A future scope change must update this plan before implementation begins.
