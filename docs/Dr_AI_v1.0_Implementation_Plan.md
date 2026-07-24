---
title: "Dr. AI v1.0 Implementation Plan"
status: "2026-07-23 first three-party care-and-cost workflow deployed to Tencent staging; expanded governed review platform remains in progress"
created: "2026-07-02"
last_updated: "2026-07-23"
owner: "Harry Cao"
delivery_window: "Production v1.0 phase after completed beta foundation; implementation schedule to be estimated after Phase 1 planning starts"
release_target: "Production-ready China-first multi-scenario platform; stakeholder showcases use synthetic/de-identified data until live-use gates close"
---

# Dr. AI v1.0 Implementation Plan

This file is the durable source of truth for implementing Dr. AI v1.0. Future chats should read this file before proposing or making implementation changes.

## Source Links

- Current product requirements:
  `Dr_AI_Product_Requirements_Document_v1.0.md`
- Historical source requirements:
  `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx`
- Implemented and planned data boundary: `docs/Dr_AI_v1.0_ERD.md`
- Research paper: `/Users/Harry-Cao/Desktop/留学规划/科研/Prediction_of_Lung_Cancer_Metastasis_Risk_Based_on_GCAVE-GAN_Data_Augmentation_and_Multimodal_Feature_Fusion.pdf`
- Figma prototype: https://www.figma.com/proto/8EJikM9M97nVy3R5JLeC0O/Figma-basics?node-id=618-1051&t=gWNIJAQQiMLGLeS6-1

## Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-07-02 | Use Flutter rather than native SwiftUI. | One shared codebase is required for the patient mobile experience and doctor web experience. |
| 2026-07-02 | Make the doctor-led care loop the golden workflow. | It demonstrates the product's clinical-copilot positioning while connecting the doctor and patient experiences. |
| 2026-07-02 | Target an invited public beta. | The release should be distributable and testable but will not make clinical-use claims. |
| 2026-07-02 | Plan for one solo developer using Codex. | The schedule and scope must remain achievable within one month. |
| 2026-07-02 | Use a simulated lung-risk assessment in v1.0. | Only the research paper is currently available; there is no runnable model checkpoint or inference code. |
| 2026-07-02 | Use synthetic or de-identified demonstration data only. | The one-month beta does not include the governance and validation required for real patient data. |
| 2026-07-07 | Re-scope v1.0 from invited beta/demo MVP to production/commercial v1.0. | The beta foundation proves the core loop, but PRD-listed systems and visible dashboard modules must become functional production workflows or be removed/disabled before v1.0 is complete. |
| 2026-07-07 | Close Phase 0 with production-scope decisions; do not start Phase 1 in the closure pass. | The surface audit and closure record settle kept, gated, removed/disabled, and deferred modules; production data-foundation implementation remains the next explicit phase. |
| 2026-07-08 | Treat doctor Patient Management as a patient workspace, not a long mixed dashboard. | Phase 2 made the doctor/patient loop functional, but the doctor detail page now needs stable information architecture: assigned-patient navigation, selected-patient summary, and focused subsections for medical history, medications, prescriptions, reminders, recovery plans, imaging, notes, and activity. |
| 2026-07-08 | Add a production localization foundation before broad UI expansion. | The commercial product targets Chinese customers and must support at least Simplified Chinese and English with real Flutter localization, Chinese-first copy review, locale-aware formatting, and no automatic translation of user-entered clinical content. |
| 2026-07-08 | Center Phase 2 patient/doctor workflows on clinical events rather than isolated widgets. | Patient profile and medical history, doctor diagnoses, prescriptions, recovery plans, imaging findings, notes, and specialist consultation become understandable only when they link to a coherent medical problem/care episode. |
| 2026-07-09 | Add a production product-quality gate before Phase 3. | The Phase 2 data/workflow foundation is useful, but the current visible app still feels like a prototype. Commercial readiness now requires a real-app UX pass before AI work resumes. |
| 2026-07-09 | Treat aesthetic quality as a functional healthcare requirement. | Typography, spacing, profile/avatar setup, empty states, and removal of demo/test language affect trust and must be designed deliberately, not patched after feature work. |
| 2026-07-11 | Complete connected doctor-patient messaging before Phase 3. | Both roles need one mutual contact model and a reliable human communication path before AI chat expands; system chat stays read-only and group chat stays explicitly empty. |
| 2026-07-12 | Keep Phase 3 model evaluation isolated from the production chatbot. | The frozen synthetic/public suite may be collected through a thin research runner before production chatbot integration; it must not import application code, expose sealed rubrics/answers, use real patient data, or become a production inference path. |
| 2026-07-13 | Use one governed medical knowledge platform for bounded patient RAG and doctor evidence search. | The patient chatbot needs a stricter patient-approved retrieval view, while doctors need a dedicated Resources workspace over the broader doctor-approved corpus; both require shared provenance, rights, versioning, review, and rollback controls. |
| 2026-07-13 | Treat the Phase 3 chatbot as a bounded server-controlled workflow, not an autonomous medical agent. | DeepSeek-v4-flash is the initial backbone, but deterministic safety, context selection, retrieval, evidence sufficiency, semantic claim validation, product actions, and provider-neutral fallbacks remain server-controlled. |
| 2026-07-16 | Admit the manually reviewed 55-entry Chinese corpus to a local patient retrieval release. | The product owner confirmed every entry and document is patient-use approved. The system preserves unspecified reviewer attribution, independently versions the reviewed translations, retains U.S. jurisdiction metadata, and still requires all production and live-provider gates. |
| 2026-07-16 | Replace the optional Slice 6 retrieval-adapter experiment with governed online-source expansion and freshness. | Expanding reviewed China-relevant evidence is more valuable than custom reranker training at the current baseline. Online content must enter through allowlisted scheduled ingestion, quarantine, rights and medical review, evaluation, and immutable activation; patient answers must never search the unrestricted public web directly. |
| 2026-07-17 | Make personalized context data-origin neutral and question-bounded. | Synthetic fixtures should exercise the same patient tables and model-input contract that future patient-entered records use. The server selects only relevant fields with provenance and dates; it never sends the whole record or interprets one measurement as a diagnosis. |
| 2026-07-18 | Use adaptive multi-call RAG rather than calling DeepSeek repeatedly for every input. | Ordinary questions retain retrieval then generation. Only ambiguous, colloquial, short-reference, or weak-retrieval cases may use one schema-constrained query-planner call, followed by server validation and fused original-plus-rewrite retrieval; high-risk claim verification may use an optional bounded pass but never replaces deterministic safety or independent review. |
| 2026-07-18 | Insert refinement Slices 9A-9E before the final Slice 10 commercialization gate. | Retrieval rights/ranking, adaptive rescue, semantic claim support, real-context privacy/chat lifecycle, and operational evidence are implementation work, while Slice 10 remains final verification and the production/commercialization decision rather than a catch-all build phase. |
| 2026-07-18 | Accept Hong Kong for the current embedding/reranking stage and defer the final production-region decision. | The API and PostgreSQL already operate in Tencent Hong Kong. Moving only embedding/reranking to Mainland China would add cross-border traffic, latency, failure modes, privacy review, and a second operational environment. Current development/staging may stay coherent in Hong Kong; patient-facing production still requires explicit region, residency, network-performance, provider-rights, privacy/legal, and no-training/no-retention evidence. Mainland hosting becomes mandatory only if the approved China-market/data-governance decision requires it. Slice 9B development may begin while the external Slice 9A production-evidence gate remains open. |
| 2026-07-21 | Reopen Slice 9A around the 100-question symptom-first rural-China contract and pause new Slice 9B optimization. | The old eight-case 9A suite expected the only symptom-orientation case to have no evidence and the artifact named 9B `v2-final` failed improvement and latency. The new boundary uses a controlled clinical presentation, combination/negation-aware pre-retrieval emergency routing, candidate 120 scene-safety copy, separate variants, and release-bound case-by-case coverage evidence. The candidate contract and copy require named review; retrieval hits are not clinical support. |
| 2026-07-22 | Pivot v1.0 to a production-ready, China-first, three-party care-and-cost transparency platform, using synthetic/de-identified stakeholder showcases as the first validation and partnership path. | Public clinical deployment and app-store distribution require licenses, institutional partners, validated models, governed data, and regulatory readiness that are not currently available, but those deployment constraints do not require a demo-only architecture. The existing patient/doctor, Clinical Event, governed-knowledge, safety, and audit foundation remains useful. The new v1.0 adds organization-scoped payer review, itemized care/claim transparency, versioned expected-care ranges, explainable variance review, clinician rationale, and human resolution across configurable clinical scenarios. |
| 2026-07-22 | Keep diagnosis, care, reimbursement, and suspected-abuse decisions human-owned. | An AI estimate is not the correct treatment or price, and a difference is not proof of waste, abuse, fraud, or poor care. Dr. AI may draft a sourced expected-care envelope and explain deterministic comparisons, but it may not automatically diagnose, deny or reduce payment, delay care, label abuse, rank clinicians, or take punitive action. |
| 2026-07-22 | Make China the first jurisdiction adapter and defer U.S. support. | China and the United States use materially different coding, pricing, coverage, settlement, and review workflows. v1.0 will support a clinician-reviewed matrix of China-first scenario families through configurable releases; the first scenario is an implementation slice, not the product boundary. Any future U.S. adapter must have separate code systems, contracted-rate concepts, rules, rights, and validation. |

## 2026-07-22 Product-Direction Amendment

This section supersedes the earlier diagnosis/chatbot-centered definition of
**production/commercial v1.0** and its 2026-08-12 patient-chatbot
commercialization deadline. It does **not** replace production readiness with a
single demo. The current target is a production-quality, multi-scenario
care-and-cost transparency platform; real clinical/payer operation and public
distribution remain gated until the necessary external approvals and evidence
exist. Historical entries remain below as implementation evidence and are not
permission to discard completed work.

### Current v1.0 outcome

Deliver one coherent, bilingual, production-ready China-first platform that:

1. preserves the existing patient and doctor care foundation;
2. adds organization-scoped payer organizations and authorized payer-reviewer
   memberships, exercised first with synthetic/de-identified data;
3. links any supported Clinical Event and encounter to planned care, delivered
   services, and itemized claim/cost data through configurable scenario and
   jurisdiction releases rather than disease-specific code;
4. produces a versioned **expected-care envelope** with plausible care
   categories, low/high cost estimates, jurisdiction, effective date,
   references, assumptions, confidence, and missing information;
5. compares planned, delivered, billed, allowed, paid, and
   patient-responsibility amounts through deterministic rules and arithmetic;
6. creates explainable `review_recommended` alerts rather than abuse or fraud
   determinations;
7. lets the clinician correct facts and record a versioned clinical rationale;
8. lets an authorized human payer reviewer request clarification, accept or
   reject a request with a recorded reason, escalate, or close the review; and
9. gives the patient a plain-language view of planned, actual, covered, and
   out-of-pocket amounts without exposing reviewer-only notes or confidential
   rate information.

### Build, validation, and live-deployment boundary

- Use synthetic or appropriately de-identified data until real-data,
  institutional, privacy, security, clinical, legal, and regulatory gates close.
- Do not submit a real claim, verify real eligibility, adjudicate coverage,
  transfer funds, or connect to a live hospital/payer system.
- Do not present a simulated assessment as a diagnosis or use it to establish
  medical necessity.
- Do not present one number as the correct cost. Every estimate is a range with
  source, version, date, jurisdiction, assumptions, and uncertainty.
- Do not claim that an alert proves waste, abuse, fraud, over-treatment,
  incorrect billing, or clinician wrongdoing.
- Do not claim real savings, reduced abuse, clinical effectiveness, regulatory
  approval, or authorization for live use from synthetic cases or stakeholder
  showcases. Product/engineering production readiness must be reported
  separately from clinical, reimbursement, and regulatory authorization.
- Preserve deterministic safety, authorization, evidence, arithmetic, and
  workflow-state control. Generative AI may draft structured candidates and
  explanations only inside those controls.

### Reuse and change boundary

Preserve authentication, RBAC, patient/doctor profiles, care relationships,
Clinical Events, prescriptions, medications, imaging, recovery plans,
consultations, chat, governed knowledge, provenance, model-provider adapters,
structured output validation, metadata-only telemetry, and audit events.

Preserve the implemented payer organizations/memberships, event-level
care-cost items, submitted request snapshots, and human payer reviews. Add
coverage, encounters, planned-care items, formal claims and claim lines,
configurable scenario definitions,
pricing-reference and utilization-rule releases, expected-care envelopes and
items, variance alerts, clinician rationales, payer reviews, and immutable
review-state transitions. Use synthetic/de-identified rows until live-data
gates close, but do not design synthetic-only contracts.
Legacy invoices/payment statuses may remain but are not the claim-review source
of truth.

## Preserved 2026-07-07 Re-scope: Production v1.0

The section below records the production re-scope adopted on 2026-07-07. It is
preserved because its completed foundations and quality requirements remain
valuable, but its public production/commercial release target is superseded by
the 2026-07-22 Product-Direction Amendment above.

The completed beta/demo MVP foundation includes authentication/session
handling, seeded dashboards, the doctor-led patient care loop, simulated
assessment, recovery plan, patient Today tasks, educational chat, consultation
request/status, Tencent staging web/API deployment, Android debug access, beta
support surfaces, and mark-only logo assets.

The old diagnosis/chatbot-centered production/commercial checklist remains
historical backlog. Current v1.0 completion follows the re-scoped production-
readiness definition of done later in this document. Any old item outside the
three-party core is preserved but does not block that core.

Current planning rule: every visible doctor, patient, specialist, and admin dashboard card, button, route, and module must either be implemented to the agreed v1.0 level or intentionally removed/disabled in production-facing UI. Placeholder cards must not remain in a production release.

Product-quality rule: `Dr_AI_v1.0_Product_Quality_Gate.md` was required before
Phase 3 and is now recorded complete. Its visual quality, typography,
profile/onboarding, empty-state, and production-copy standards remain
regression requirements throughout Phase 3 rather than a closed-and-forgotten
milestone.

### Production v1.0 Product Boundary

#### A. Production MVP core

- Make every visible doctor/patient dashboard item functional, routable, and backed by real state.
- Remove or disable placeholder modules that are not implemented for production.
- Add loading, empty, validation, failure, unauthorized, and success states for every module.
- Keep role-based access and doctor-patient boundaries strict across patient, doctor, specialist, and admin roles.
- Ensure production modules have backend persistence, validation, tests, and audit events where appropriate.

#### B. Authentication and account management

- Keep login, logout, refresh-token rotation, and session restoration.
- Add full registration or controlled invite onboarding.
- Add SMS verification or document why it is deferred.
- Add biometric login support for mobile where feasible.
- Add profile management.
- Add an account deletion/support request workflow that actually submits requests to the backend queue instead of only preparing local drafts.
- Add OAuth only if there is a real product need; otherwise document OAuth as not required for v1.0.

#### C. Patient profile and medical history management

- Patient demographics, allergies, chronic diseases, medications, medical history, visit history, diagnoses, prescriptions, imaging metadata/files, and doctor notes.
- Patient-facing read/update surfaces where appropriate.
- Doctor-side create, edit, review, and history workflows.
- Audit logs for sensitive reads and writes.

#### D. Medical records and imaging

- Real medical-record CRUD.
- Upload workflow with real Tencent COS completion, not only presign metadata.
- Safe file validation, size/type enforcement, resumable or recoverable failure handling, and clear upload status.
- Imaging list, detail, and review workflow.
- DICOM viewing and segmentation remain optional later scope unless explicitly needed for the initial commercial release.

#### E. Preserved AI assessment workflow

- Preserve the workflow for AI assessment intake, execution, review, and
  history as a simulated/research adapter.
- If the real lung-cancer model is not runnable and validated, use a clearly labeled non-clinical simulated adapter while keeping the workflow production-quality.
- Preserve the response contract for a future validated model adapter.
- Include input collection, CT/image reference, clinical variables, optional genomic fields, run status, result history, limitations, audit trail, and doctor review.
- Do not make clinical claims until model readiness and regulatory gates are cleared.
- Treat real GCAVE-GAN/AMCM inference as a model-readiness/regulatory gate, not as permission to omit the UI and product workflow.
- Do not use an assessment result as an authoritative diagnosis, medical-
  necessity determination, expected price, or reimbursement decision.

#### F. AI recovery plan workflow

- AI-assisted recovery-plan generation or drafting.
- Doctor review, edit, and approve flow.
- Patient Today tasks for medication, exercise, diet, and follow-up.
- Completion tracking, notifications/reminders, regeneration/revision history, safety limitations, and audit events.

#### G. Patient AI chat

- Patient educational chat must be fully functional and robust.
- Keep the DeepSeek/LLM proxy server-side.
- Run red-flag emergency escalation before any model call.
- Keep medication guidance safe and bounded; do not provide diagnosis or medication-change instructions.
- Handle rate limits, timeout fallback, malformed response fallback, quota fallback, and unsafe prompt behavior.
- Store conversation history where appropriate.
- Show clear source/provenance and limitations.

#### H. Specialist consultation

- Text consultation workflow with request, accept/reject, status, specialist response, and attachments/annotations where feasible.
- Voice/video consultation is a v1.0 production requirement if real-time infrastructure is available; otherwise it is a v1.0 stretch gate with an explicit blocker and acceptance note.
- Shared annotations should be implemented at least as image/record comments or structured notes if full live annotation is too large.

#### I. Medication management

- Medication list CRUD.
- Medication reminders and refill reminders.
- Interaction warning framework.
- Barcode scanning if feasible; otherwise mark as a v1.0 stretch gate with explicit package/device reason.
- Medication Safety Agent placeholder/adapter if a real drug-interaction database is unavailable.

#### J. Clinic operations

- Resource management for medicine inventory, equipment, beds, ambulance, and referral resources.
- Equipment booking.
- Appointment booking, scheduling, and reminders.
- Hospital information editing.
- Doctor information editing.
- Doctor team management.
- Roles and flows for doctor, specialist, and admin.
- Availability, booking status, resource state, and conflict handling.

#### K. Care-and-cost transparency, payer review, and analytics

- Make the new three-party review domain the v1.0 product's primary workflow
  rather than treating insurance as optional invoice metadata.
- Implement synthetic payer organization/membership and coverage scope.
- Implement encounters, planned-care items, claims, immutable claim lines,
  pricing/rule releases, expected-care envelopes, explainable variance alerts,
  clinician rationale, human review, and patient-facing cost explanations.
- Keep invoice, payment-status, and revenue-summary tables as preserved legacy
  foundations; do not treat them as the claim-review source of truth.
- Keep real claim submission, eligibility, authorization, adjudication,
  payment, denial, appeal, and negotiated-rate integrations gated.
- Analytics must separate flagged amount, reviewed amount, accepted
  explanation, confirmed correction, and hypothetical savings. Never report a
  synthetic flagged amount as real savings or prevented abuse.

#### L. Administration

- Admin dashboard.
- User management.
- Hospital/clinic management.
- Audit event read/search.
- System status.
- Support, deletion, and feedback request queue.
- Configuration for registration policy, roles, and clinic metadata.

#### M. Production and showcase readiness

- Monitoring and alerting.
- Crash/error tracking.
- API 5xx, auth, chat, assessment, and upload monitoring.
- Backup and restore rehearsal.
- Production/staging separation.
- Reproducible local, controlled-staging, and future production deployment
  paths, with production activation remaining externally gated.
- Doctor, NGO, and prospective payer-reviewer walkthrough scripts.
- Support, feedback, and deletion workflows.
- Privacy/security documentation.
- Deployment/recreation runbook.
- No real patient data until privacy, consent, security, and legal requirements are satisfied.
- No public store upload, real hospital/payer connection, or production claim
  until a later product, partnership, legal, security, clinical, and regulatory
  decision explicitly reopens those gates.

### Phase 0 Production Scope Decisions

The Phase 0 audit and closure record settle the production v1.0 scope boundary
without starting Phase 1 implementation:

- Keep as production v1.0 core: authentication/account lifecycle, patient
  profiles/history/records/imaging metadata, AI diagnosis workflow with a
  simulated adapter until model/regulatory gates clear, recovery plans, Today
  tasks, medication reminders, patient educational chat, specialist
  consultation text workflow, medication management, administration, support,
  deletion, feedback, and commercial readiness gates.
- Keep as production/commercial-readiness scope but hide or disable until
  implemented: clinic resources, equipment, beds, ambulance/referrals,
  appointments/scheduling, hospital and doctor information editing, doctor
  team management, bounded billing, and bounded analytics.
- Gate explicitly: real clinical claims, real patient data, validated model
  use, production clinical deployment, voice/video consultation, barcode
  scanning, full payment processing, DICOM viewing/segmentation, and external
  store/account/release actions.
- Exclude from v1.0 unless this plan is amended: national EHR integration,
  wearables, offline mode, disease surveillance, and broad public-health
  analytics.
- Support/deletion/feedback must use a combined production shape: a public
  unauthenticated privacy/support route, authenticated in-role submission, and
  an admin-managed backend queue with status, audit metadata, authorization,
  and policy controls. The current `/beta-support` local-only deletion and
  feedback drafts are not production workflows.
- Specialist/admin first implementation may proceed from written product
  acceptance criteria and route/state specs if approved; new Figma/design
  evidence is required before Phase 5 only when visual parity, complex
  multi-panel workflows, or shared design-system changes are introduced.

Closure evidence:

- `docs/Phase_0_Production_v1_Surface_Audit.md`
- `docs/Phase_0_Production_v1_Closure_Record.md`

Localization target:

- Use Flutter's official localization flow with generated accessors and ARB
  files, starting with Simplified Chinese (`zh_Hans`) and English (`en`).
- Treat Simplified Chinese as the primary production copy path for Chinese
  customers, with English as the secondary supported locale.
- Localize UI labels, actions, validation messages, empty states, status labels,
  and user-facing errors through generated localization accessors instead of
  hardcoded widget strings.
- Keep backend responses machine-readable through stable codes/enums such as
  `not_found`, `draft`, `pending_review`, `approved`, and `completed`;
  translate those codes in Flutter rather than mixing server strings across
  languages.
- Do not automatically translate user-entered clinical content such as doctor
  notes, medication names, plan instructions, imaging labels, patient messages,
  or uploaded-record descriptions. Preserve those values exactly as entered
  unless a later explicit clinical-translation feature is designed, reviewed,
  and gated.
- Apply locale-aware formatting for dates, times, phone numbers, reminder
  schedules, and status text.
- Keep SMS notification copy clinically neutral when the Phase 6
  China-market SMS delivery gate is later closed.

Localization implementation decisions (2026-07-10):

- `app_en.arb` is the source language catalog and `app_zh.arb` is the
  Simplified Chinese catalog. Flutter-generated accessors are the only new
  path for localized production copy; do not add a second parallel app or
  duplicate screen tree.
- On first use, Flutter follows the device language when it is Chinese or
  English. All other device languages resolve to English. A user selection is
  stored locally in secure storage and takes effect immediately without an API
  round trip.
- The persisted doctor/patient `preferred_language` profile field remains the
  cross-device account preference. Account editing aligns that field with the
  immediate interface locale; the local interface setting remains available
  when the API is offline.
- Localize product-owned copy and stable status/error codes. Never translate
  patient-entered or clinician-entered clinical content automatically.
- Language names retain stable English storage values (`English` and
  `Simplified Chinese`) so the existing API contract does not change; only
  their displayed labels are localized.
- All current production UI surfaces now use the shared English/Simplified
  Chinese catalogs: authentication and registration, patient and doctor
  dashboards and Account pages, Patient Management, care details, Contacts,
  Recovery Plans, legal/support content, dialogs, validation, empty states,
  notifications, semantics, and stable status/error labels. Structured
  geographic reference data keeps stable English storage values while its
  Chinese display labels are resolved centrally.
- Production forms do not prefill synthetic clinical values. Test fixtures
  remain confined to automated test code and no validation run writes to a
  production-facing data store.

### Doctor Patient Management sections:

- Overview: read-only patient profile summary, important verified history,
  active Clinical Events, active recovery plan, and current medications.
- Profile: read-only patient basic information with correction-request or
  confirmation-needed affordance, not direct doctor editing.
- Medical History: patient-entered history plus doctor verification/amendment
  workflow.
- Clinical Events: main doctor workspace for symptoms, diagnosis, status,
  event updates, and links to all event-owned resources.
- Medications & Prescriptions: prescription authoring plus generated medication
  schedules; this replaces separate competing medication/prescription/reminder
  workflows.
- Recovery Plans: event-linked recovery timeline creation, editing, revision,
  and completion.
- Imaging: event-linked upload/review plus manual imaging findings/results.
- Consultation & Activity: doctor notes, specialist review, and activity
  timeline.

### Current v1.0 Production-Readiness Milestone Tracker

- [x] Direction 0: freeze the high-level product boundary
  - [x] Preserve all completed patient/doctor and Phase 3 work.
  - [x] Add payer reviewer as the third primary party.
  - [x] Choose China-first product scope and defer a separate U.S.
    jurisdiction adapter.
  - [x] Define expected-care output as a sourced range, not a correct price.
  - [x] Keep clinical, reimbursement, and suspected-abuse decisions human-owned.
  - [x] Prohibit automatic denial, care restriction, fraud labeling, clinician
    ranking, and synthetic-impact claims.
- [ ] Direction 1: freeze scenario coverage and reference boundaries
  - [ ] Select the first China-first vertical slice, then define the additional
    scenario families required for the v1.0 coverage matrix. The first slice
    must not become a hardcoded product boundary.
  - [ ] Obtain named clinical review of each supported scenario family's
    plausible pathways, exceptions, and unsafe under-treatment failure modes.
  - [ ] Define the patient, clinician, payer reviewer, and NGO observer views.
  - [ ] Record the allowed code systems, fee/reference sources, geographic and
    hospital-level scope, currency, effective dates, and rights.
  - [ ] Freeze a representative synthetic/de-identified multi-scenario suite,
    expected reviewer labels, and known justified-variance cases before tuning
    alerts.
- [ ] Direction 2: payer and cost-review data foundation
  - [x] Add `payer_organizations` and organization-scoped
    `payer_memberships`; do not collapse government regulator, public payer,
    and commercial insurer into one unqualified role. The current registration
    flow creates synthetic-only organizations and active memberships; live
    organization verification remains open.
  - [x] Add the first workflow slice: generic Clinical Event-linked
    `care_cost_items`, submitted `payer_requests`, immutable
    `payer_request_lines`, and membership-attributed `payer_reviews`.
  - [ ] Add production-designed `coverage_enrollments` with jurisdiction and
    effective dates; populate only synthetic/de-identified fixtures until
    live-data gates close.
  - [ ] Add versioned `care_scenario_definitions` and a coverage matrix that
    bind scenario family, encounter type, population/applicability constraints,
    jurisdiction, evidence/rule releases, review status, and activation state.
  - [ ] Add `care_encounters` and `care_plan_items` linked to the existing
    patient, doctor, clinic, and Clinical Event records.
  - [ ] Add versioned `claims` and immutable `claim_lines` with explicit code
    system, quantity/unit, currency, and billed/allowed/paid/patient amounts.
  - [ ] Add immutable `pricing_reference_sets/items` and
    `utilization_rule_sets/rules` with provenance, jurisdiction, version,
    effective dates, review status, and activation/rollback.
  - [ ] Add `expected_care_envelopes/items`, `variance_alerts`,
    `clinician_rationales`, `payer_reviews`, and
    `review_state_transitions`.
  - [x] Add the first-slice Alembic migration, schemas, synthetic fixtures,
    fail-closed patient/doctor/payer RBAC, neutral cross-patient denials, and
    metadata-only audit tests. Broader multi-organization isolation evidence
    remains part of Direction 6.
  - [x] Reconcile the API contract for the implemented first slice; keep
    speculative coverage, claim, pricing, rule, envelope, and appeal endpoints
    out of the contract until their authorization and state models are fixed.
- [ ] Direction 3: deterministic review engine
  - [x] Implement integer-minor-unit arithmetic and request line-to-total
    reconciliation without floating-point money for the first workflow slice.
    The future reference/rule comparison engine remains open.
  - [ ] Implement deterministic duplicate, unusual quantity/duration,
    price-range, service-mix, and missing-documentation comparisons.
  - [ ] Bind every result to the exact claim, reference/rule release, input
    checksum, jurisdiction, and effective date.
  - [ ] Emit `review_recommended` plus reason codes and compared values; never
    emit `abuse_detected` or a punitive action.
  - [ ] Support clinically justified exceptions, missing-information status,
    alert suppression with reason, and immutable re-evaluation history.
  - [ ] Fail closed on mixed currencies, unavailable references, invalid
    ranges, unsupported codes, stale releases, or unreconciled totals.
- [ ] Direction 4: bounded AI envelope and explanation support
  - [ ] Define a provider-neutral structured expected-care candidate schema.
  - [ ] Retrieve only admitted clinical/utilization and pricing references for
    the active jurisdiction and effective date.
  - [ ] Require low/high range, assumptions, missing information, confidence,
    and cited source/rule IDs; reject unsupported codes and amounts.
  - [ ] Keep deterministic validators and arithmetic authoritative before any
    AI output is stored or displayed.
  - [ ] Require doctor review before a candidate envelope can be compared with
    delivered services or shown as reviewed.
  - [ ] Generate role-specific explanations from validated facts only; patient
    copy must not expose reviewer-only notes, confidential rates, or suspicion
    labels.
  - [ ] Add fixed fallbacks for missing evidence, provider failure, schema
    failure, and disagreement; no provider failure may block human care.
- [ ] Direction 5: multi-scenario three-party user experience
  - [x] Doctor first slice: Clinical Event-linked care-item CRUD with service
    date, type, status, quantity, actual/requested/patient amounts, notes, and
    payer-request submission. Sourced ranges and clinician exception rationale
    remain open.
  - [x] Payer reviewer first slice: organization-scoped dashboard, queue,
    immutable itemized request detail, clarification, acceptance, rejection,
    escalation, closure, and human resolution. Sources, deterministic alerts,
    and formal appeals remain open.
  - [x] Patient first slice: Clinical Event-grouped care-and-cost ledger with
    actual, requested, and patient-responsibility totals and request readback.
    Coverage determinations, expected ranges, and question prompts remain open.
  - [ ] Show `AI-generated`, `doctor-reviewed`, `delivered`, `submitted`, and
    `human-reviewed` as distinct states.
  - [x] Add bilingual copy plus loading, empty, error, unauthorized, and
    responsive small-screen states for the first slice. Stale-reference states
    and evidence/range visualizations remain open.
- [ ] Direction 6: production-readiness evaluation and stakeholder validation
  - [ ] Pass 100% arithmetic reconciliation and authorization/isolation tests.
  - [ ] Measure per-scenario and aggregate alert precision, recall, and
    false-positive rate on the frozen expert-labeled synthetic/de-identified
    suite; prevent a strong scenario from hiding failure in another.
  - [ ] Prove the same APIs, schema, authorization, state machine, arithmetic,
    and observability work across supported scenarios without condition-specific
    application-code forks.
  - [ ] Record clinician override/explanation rates and analyze them as
    calibration evidence, not clinician misconduct.
  - [ ] Run moderated task/comprehension reviews with doctors, NGO members, and
    prospective payer stakeholders.
  - [ ] Rehearse outage, rollback, stale-reference, conflicting-pathway,
    exception, and under-treatment-risk cases.
  - [ ] Produce reproducible stakeholder showcases plus a production-readiness
    and limitations report. Clearly separate engineering/product readiness from
    unavailable real-world savings, abuse-reduction, clinical, reimbursement,
    and regulatory evidence.

### Preserved Historical Production v1.0 Milestone Tracker

The checklist below records completed foundation work and the former product
backlog. Its unchecked items do not block the current three-party core unless they
are explicitly referenced by the current tracker above.

- [x] Phase 0: Plan reconciliation and placeholder audit
  - [x] Read the PRD, current implementation plan, API contract, and design-freeze docs.
  - [x] Inventory doctor dashboard cards, buttons, routes, and menu items.
  - [x] Inventory patient dashboard cards, buttons, routes, and menu items.
  - [x] Inventory specialist-facing surfaces.
  - [x] Inventory admin/support-facing surfaces.
  - [x] Mark each surface as functional, partial, placeholder, or remove/disable.
  - [x] Map every kept surface to a PRD module or explicit product decision.
  - [x] Identify stale beta-only assumptions in docs and UI copy.
  - [x] Draft the production API/data-model gap list.
  - [x] Update acceptance criteria for every kept module.
  - [x] Record Phase 0 audit findings in a closure note.
    - First slice recorded in `docs/Phase_0_Production_v1_Surface_Audit.md`
      for doctor and patient visible surfaces.
    - Second slice recorded specialist, admin, support/deletion/feedback, hidden
      route/model/API/test/design reconciliation, and production support queue
      gaps in `docs/Phase_0_Production_v1_Surface_Audit.md`.
    - Final closure recorded in
      `docs/Phase_0_Production_v1_Closure_Record.md`; Phase 1 has not started.
- [x] Phase 1: Production data foundation
  - [x] Add hospital and clinic models/migrations.
  - [x] Add doctor team and role-assignment models/migrations.
  - [x] Add clinic resource and equipment models/migrations.
  - [x] Add appointment and booking models/migrations.
  - [x] Add prescription and medication-reminder models/migrations.
  - [x] Add notification models/migrations.
  - [x] Add invoice, payment-status, and revenue-summary models/migrations.
  - [x] Add analytics event models/migrations.
  - [x] Add support, deletion, and feedback request models/migrations.
  - [x] Expand RBAC for patient, doctor, specialist, and admin.
    - [x] Reserve backend `specialist` and `admin` role values.
    - [x] Make unsupported/future API and Flutter roles fail closed before
      specialist/admin workflows are usable.
    - [x] Add Phase 1 route-level role helpers so enabled doctor/patient
      foundation workflows are allowlisted and specialist/admin workflow
      access stays denied until Phase 5.
  - [x] Add cross-role and cross-patient authorization tests.
    - [x] Add focused unsupported-role and existing beta-route denial tests for
      the initial Phase 1 slice.
    - [x] Add focused support/deletion/feedback status-isolation tests for
      wrong requester, unsupported/future roles, and no-side-effect denials.
  - [x] Expand audit coverage for sensitive reads, writes, uploads, AI runs, support actions, and admin actions.
    - [x] Add support queue audit-metadata and support-request audit-event
      persistence coverage for the schema foundation.
    - [x] Add endpoint-level support queue audit assertions for request
      creation, own-status listing, and own-status reads.
    - [x] Keep future admin action endpoints unavailable in Phase 1 and verify
      unsupported specialist/admin probes create no queue rows or audit
      records.
  - [x] Separate seeded/demo data paths from production data paths.
    - [x] Verify synthetic seed flow leaves the new production foundation
      tables empty.
  - [x] Update API contract and seed fixtures.
    - [x] Update the API contract for Phase 1 schema foundation and
      fail-closed future-role behavior.
    - [x] Add no production seed fixtures in Phase 1; the current seed remains
      synthetic demo-only and the new production foundation tables remain empty
      until later production workflows populate them.
- [x] Phase 2: Patient and doctor core workflows
  - [x] Implement patient demographic create/edit/review flow.
    - [x] First slice: add persisted demographics fields, doctor assigned-patient
      review/edit, patient own-profile edit, and care-bundle readback.
    - [x] Phase 2 closure decision: patient creation beyond account/profile
      registration is not owned by Phase 2; controlled invite onboarding and
      account registration remain in the authentication/account lifecycle
      scope.
  - [x] Implement allergy and chronic-disease management.
    - [x] First slice: add persisted allergy and chronic-disease CRUD for
      assigned doctors and own-patient allowed updates, with neutral denials and
      metadata-only audit events.
  - [x] Implement visit-history CRUD.
    - [x] First slice: add doctor-owned visit-history CRUD with patient/doctor
      readback, neutral denials, and metadata-only audit events.
  - [x] Implement diagnosis and doctor-note CRUD.
    - [x] First slice: add doctor-owned diagnosis CRUD and doctor-note
      create/edit/delete, with patient-visible diagnoses, hidden patient
      doctor notes, neutral denials, and metadata-only audit events.
  - [x] Implement prescription CRUD.
    - [x] Medication slice: add doctor-owned prescription create/edit/delete
      with medication lines, patient/doctor readback, neutral denials, and
      metadata-only audit events.
  - [x] Implement patient-facing profile/history read surfaces.
    - [x] First slice: extend patient care bundle and Flutter patient profile
      card with demographics, allergies, chronic diseases, visit history, and
      diagnoses; doctor notes stay hidden from patients.
  - [x] Implement patient-facing allowed update surfaces.
    - [x] First slice: allow own-patient demographics, allergies, and chronic
      diseases to be updated through authenticated API paths.
  - [x] Implement doctor-side medical-history review/edit workflow.
    - [x] First slice: extend doctor Patient Management read surface and API
      write paths for demographics, allergies, chronic diseases, visits,
      diagnoses, and notes.
  - [x] Complete Tencent COS upload finalization.
    - [x] Imaging slice: add production-separated Tencent-COS-compatible
      imaging upload metadata, metadata-only upload completion confirmation,
      upload/review statuses, neutral denials, and safe audit metadata.
  - [x] Add imaging list/detail/review workflow.
    - [x] Imaging slice: add doctor/patient imaging list/detail readback,
      doctor-only reviewed/rejected status workflow, expanded care-bundle
      readback, and doctor/patient Flutter imaging surfaces.
  - [x] Implement medication list CRUD.
    - [x] Medication slice: add doctor-owned medication create/edit/delete,
      patient/doctor readback, and Flutter doctor/patient medication surfaces.
  - [x] Implement medication reminders.
    - [x] Medication slice: add doctor-owned in-app medication reminders with
      patient readback and metadata-only queued notification rows.
  - [x] Implement refill reminders.
    - [x] Medication slice: add refill reminders linked to prescription
      medication lines with the same neutral boundary and metadata-only queue.
  - [x] Implement recovery-plan draft workflow.
    - [x] Recovery-plan closure slice: add production review metadata,
      metadata-only audit events, explicit submit-for-review, request-changes,
      approve, activate-compatible, and complete transitions, plus progress
      summaries.
  - [x] Implement doctor review/edit/approve workflow.
    - [x] Recovery-plan closure slice: doctor-only transition endpoints and
      Flutter controls now expose draft/review/approval/completion state.
  - [x] Implement patient Today task tracking.
    - [x] Recovery-plan closure slice: patient Today now returns active plan
      progress, completed/remaining task counts, completion percent, and
      completion timestamps through the active task readback.
  - [x] Implement notification/reminder delivery path.
    - [x] Medication slice: add backend-only in-app queued notification records
      for active medication/refill reminders; external delivery remains
      deferred.
    - [x] Phase 2 closure decision: external push, SMS, email, or native local
      notification delivery is not implemented in Phase 2 because it requires
      credentials, platform configuration, or account/service changes; the safe
      local Phase 2 path remains metadata-only in-app queue/readback.
  - [x] Add core workflow tests and audit assertions.
    - [x] First slice: add backend Phase 2 tests for migration presence,
      seed/demo separation, patient allowed updates, doctor-only history writes,
      cross-patient/wrong-role neutral denials, patient-hidden doctor notes, and
      metadata-only audit assertions.
    - [x] Medication slice: add backend tests for medication, prescription,
      medication reminder, refill reminder, own notification readback,
      cross-patient/wrong-role neutral denials, and metadata-only audit/
      notification assertions.
    - [x] Imaging slice: add backend tests for imaging upload preparation,
      completion, list/detail/readback, doctor review, patient/cross-patient
      neutral denials, seed separation, and metadata-only audit assertions.
    - [x] Recovery-plan closure slice: add backend tests for review
      transitions, wrong-role/cross-patient neutral denials, Today progress,
      complete-only-after-all-tasks semantics, and metadata-only audit
      assertions.
- [x] Pre-phase 2.5.
  - [x] Reframe doctor Patient Management navigation around Overview, Profile,
    Medical History, Clinical Events, Medications & Prescriptions, Recovery
    Plans, Imaging, and Consultation & Activity.
  - [x] Add an event-context card that groups existing visit history,
    diagnosis, prescriptions, medication schedules, generated reminders,
    imaging, and notes around the active Clinical Event concept.
  - [x] Remove the standalone doctor Reminders workspace section; reminder
    rows now appear as generated medication-schedule outputs under
    Medications & Prescriptions and Consultation & Activity.
  - [x] Keep this slice frontend-only because the current Phase 2 API can
    support the workflow clarification through existing care-bundle fields.
  - [x] Add a persisted Clinical Event/Care Episode model and explicit foreign
    keys from prescriptions, medication schedules, recovery plans, imaging,
    notes, consultation, and activity as a deeper additive backend migration.
    - [x] Add `clinical_events` plus nullable `clinical_event_id` links on
      visit history, diagnoses, medications, prescriptions, medication/refill
      reminders, metadata-only notifications, recovery plans, imaging assets,
      doctor notes, and consultation requests.
    - [x] Add doctor-only event create/update endpoints, doctor/patient event
      reads, patient-owned event aliases, and care-bundle event readback with
      linked-resource counts.
    - [x] Keep existing endpoints backward-compatible by making
      `clinical_event_id` optional.
    - [x] Add focused RBAC/audit tests for doctor create/update, patient read,
      patient mutation denial, cross-patient denial, event-linked resource
      readback, generated notification linkage, and metadata-only audit.
    - [x] Extend Flutter care-bundle domain models to parse event-linked
      resources.
  - [x] Add active Clinical Event workflow wiring in doctor Patient Management.
    - [x] Add an always-visible active Clinical Event selector above doctor
      workspace sections.
    - [x] Add doctor-side Clinical Event create/update controls in the
      Clinical Events section, with doctor-owned diagnosis copy and patient
      read-only behavior documented in the UI.
    - [x] Scope encounter updates, diagnosis readback, prescriptions,
      medication schedules, generated reminders, recovery plans, imaging,
      doctor notes, consultation requests, and activity timeline rows to the
      selected Clinical Event where the resource carries `clinical_event_id`.
    - [x] Pass selected `clinical_event_id` through Flutter client calls for
      medication schedule saves, prescription issue, medical imaging presign,
      recovery-plan create/update, and specialist consultation requests while
      keeping backend fields nullable for backward compatibility.
    - [x] Keep standalone doctor reminders removed; reminders remain generated
      medication-schedule outputs.
    - [x] Add focused Flutter widget/fake coverage for event create/update,
      event selection, and event-linked doctor writes.
  - [x] Remaining Phase 2 workflow clarification polish.
    - [x] Add doctor verification/amendment affordances for patient-entered
      Medical History with visible audit trail.
    - [x] Add event-update/timeline entries beyond the current linked-resource
      readback.
    - [x] Enforce or clearly surface one active Recovery Plan per active
      Clinical Event in the doctor UI/API.
    - [x] Add manual doctor-entered imaging findings/results fields without
      automated clinical claims.
    - [x] Add patient-submitted Clinical Event updates while preserving
      doctor-owned diagnosis controls.
  - [x] Phase 2 manual-testing onboarding cleanup.
    - [x] Expose invited sign-up in Flutter so patient and doctor test
      accounts can be created from zero instead of relying on seed accounts.
    - [x] Add doctor-side patient-code connection so a newly registered
      patient can share their code and the doctor can create the active care
      relationship before starting Clinical Events.
    - [x] Show a fresh patient onboarding view with the patient code and empty
      profile/history state when no seeded dashboard exists.
    - [x] Keep seeded demo data optional for staging smoke/regression only;
      manual workflow testing should start from registered accounts and
      user-created records.
- [x] Phase 2.5: Product quality and first-use readiness gate
  - [x] Audit staging as a real patient and doctor with screenshots.
  - [x] Define a production typography and visual-system direction for English
    and Simplified Chinese.
    - [x] Obtain user approval before applying the final English/Chinese font
      family pairing.
    - [x] Bundle Inter for Latin text and Noto Sans SC for Simplified Chinese
      locally in Flutter, with variable-weight support and bundled OFL license
      text so typography remains consistent without a runtime font CDN.
  - [x] Replace default-looking/generic typography, weak spacing, and crowded
    hierarchy in the patient and doctor surfaces.
  - [x] Make patient profile setup a guided first-use flow: avatar, display
    name, birth date or age, sex/gender, contact number, emergency contact,
    preferred language, and contact preference.
  - [x] Add a patient medical-history setup entry point during or immediately
    after onboarding.
  - [x] Rework fresh patient dashboard empty states so the next action is
    obvious without relying on seed/demo context.
  - [x] Rework doctor no-patient and selected-patient empty states around
    patient-code connection and Clinical Event creation.
  - [x] Keep seeded data available only for regression/smoke checks, not as the
    manual testing default.
  - [x] Verify the app by screenshots and first-use walkthroughs, not only by
    endpoint coverage and widget tests.
  - [x] Update docs with product-quality evidence before opening Phase 3.
  - [x] Add production account-security foundations for both roles.
    - [x] Enable authenticated password changes with current-password
      verification, refresh-session revocation, and metadata-only audit events.
    - [x] Add phone-number password recovery with expiring, hashed,
      attempt-limited verification challenges; external SMS delivery remains a
      Phase 6 integration.
    - [x] Replace the fixed registration code with the same expiring,
      hashed phone-challenge foundation; only local/test responses may expose a
      development code before the Phase 6 SMS provider is connected.
    - [x] Allow doctors and patients to add, update, or remove optional account
      email from Account.
    - [x] Accept one-character Chinese family names and Unicode free text
      without ASCII-only input filtering.
    - [x] Show doctor phone and available email in Account, and derive the
      active label from authenticated activity within the previous 14 days.
    - [x] Replace default page navigation motion with one restrained,
      reduced-motion-aware fade/slide/depth transition system.
  - [x] Enable doctor local-file avatar upload through the shared validated
    avatar pipeline.
  - [x] Add patient-match preview and explicit confirmation before a doctor
    creates a care relationship from a patient ID.
  - [x] Clarify the patient intake survey with visible sections, required and
    optional labels, examples, and conditional follow-up guidance.
  - [x] Remove duplicate doctor-dashboard profile/hospital edit actions; keep
    doctor profile editing in Account and hospital data administrator-owned.
  - [x] Hide unfinished navigation destinations and the historical demo upload
    and assessment UI from production-facing patient/doctor workflows until
    their real workflows and gates are implemented.
- [ ] Phase 3: AI systems
  - [x] Phase 2.5 is complete and the product-quality gate is explicitly
    closed; preserve it as a regression gate throughout Phase 3.
  - [x] Build the thin, isolated model-only benchmark runner as research
    infrastructure rather than extending the production chatbot.
    - [x] Keep the runner under `evaluation/chatbot/` with no Flutter,
      FastAPI, database, production-chat, or patient-record dependency.
    - [x] Pin the six approved model identifiers and shared non-secret settings.
    - [x] Send only permitted conversation inputs; never send answer keys,
      rubrics, required facts, provenance, or reviewer metadata to candidates.
    - [x] Run one model per command with deterministic shuffle, bounded retry,
      append-only results, and resume by successful `case_id`.
    - [x] Bind result filenames and rows to a settings hash that includes the
      frozen suite checksum so incompatible runs cannot mix silently.
    - [x] Record provider/model identity, response, provider token usage,
      latency, attempts, finish metadata, timestamp, and redaction-safe errors.
    - [x] Keep sealed outputs in the gitignored evaluation results directory.
    - [x] Add no-cost preflight, explicit review gating, environment templates,
      and focused offline tests.
    - [ ] Run one-case smoke checks after keys/endpoints are configured.
    - [ ] Run the full six-model model-only benchmark and blind scoring.
    - [ ] Add production-simulated mode only after an approved retrieval corpus
      and per-case retrieval inputs exist; never substitute rubric sources.
  - [x] Freeze the production RAG, constrained-agent, doctor Resources, and
    medical knowledge-base planning baseline in
    `Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`.
    - [x] Store the normative Mermaid implementation workflow in Section 4.1.1
      and require explicit product/safety review before changing its control
      boundaries or ordering.
  - [ ] Freeze the knowledge-source admission, commercial-rights, translation,
    medical-review, audience, supersession, and index-release policies.
  - [ ] Define stable doctor-resource search, patient retrieval-evidence,
    structured model-output, tool, fallback, and safe-telemetry contracts.
  - [ ] Add a top-level doctor Resources destination at `/doctor/resources`.
    - [ ] Move the doctor medical-resource search bar onto that page.
    - [ ] Remove the current unscoped doctor header search bars.
    - [ ] Keep assigned-patient and Clinical Event search inside Patient
      Management rather than mixing it with external evidence search.
    - [ ] Add Search, Saved, Recent updates, and Source registry states with
      bilingual filters, provenance, dates, version status, and source detail.
  - [ ] Implement the governed medical knowledge foundation.
    - [ ] Add publisher, authority, rights, source, version, passage,
      terminology, review, index-release, and retrieval-event entities.
    - [ ] Add immutable raw capture, checksums, parsing lineage, quarantine,
      supersession, expiry, and deterministic index rollback.
    - [ ] Build separate `doctor_resources_approved` and
      `patient_chat_approved` retrieval views.
    - [ ] Start with a small rights-cleared Chinese/WHO pilot corpus and pass
      source-by-source legal plus medical review before scaling.
  - [ ] Implement and evaluate hybrid Chinese/English retrieval.
    - [ ] Combine lexical and dense search, mandatory metadata filters,
      medically evaluated reranking, deduplication, and source diversity.
    - [ ] Add evidence sufficiency, conflict, jurisdiction, audience,
      freshness, and stale/superseded gates before generation.
    - [ ] Validate retrieval independently before connecting the model.
  - [x] Implement the bounded patient-chat orchestrator.
    - [x] Enforce deterministic emergency/prohibited-request routing before
      retrieval or generation.
    - [x] Keep knowledge retrieval, selected-care context, question preparation,
      navigation, and fixed escalation server-controlled. DeepSeek returns only
      schema-constrained answer or rewrite candidates and cannot select or
      execute product operations. Selected-care context is question-bounded
      and provenance-preserving; deployment settings still control which
      categories may be transmitted.
    - [x] Integrate `deepseek-v4-flash` through the provider-neutral adapter
      with schema-constrained internal output.
    - [x] Keep three explicit patient response modes: citation- and
      claim-validated `approved_evidence`; separately configured,
      citation-free `general_model_knowledge` when adequate approved evidence
      is unavailable; and server-owned `fixed_safety_response` for emergency,
      authorization, provider, and other fixed paths. The general mode receives
      no patient-record context, exposes no source cards, and can be disabled
      without changing the retrieval release.
    - [x] Version the answer-depth policy to request 2-4 supported sections
      (300-600 Chinese characters or 180-350 English words) without changing
      the normative safety, retrieval, evidence, or validation boundaries.
    - [x] Keep operational telemetry metadata-only while storing authenticated,
      patient-owned readable AI threads under the explicitly amended Slice 8
      history boundary, with bounded model context and at least 60-day
      retention from the latest exchange.
    - [x] Activate local patient-approved immutable release
      `KBIR-8293AC8D815B9715D1B44F42` with 55 reviewed versions and 426
      Simplified-Chinese passages.
    - [x] Verify the existing ignored server-side DeepSeek credential and run
      one live grounded-answer smoke test without exposing or committing it.
  - [x] Implement governed online-source expansion and freshness outside the
    patient answer path.
    - [x] Pilot allowlisted National Health Commission and China CDC source
      families with source-specific authority, content-class, rights, parser,
      schedule, and kill-switch policies.
    - [x] Add scheduled fetch, checksum/version change detection, redirect and
      format controls, sanitization, prompt-injection scanning, quarantine, and
      parser-drift monitoring.
    - [x] Require medical, native-language, patient-readability,
      jurisdiction/applicability, rights, security, retrieval-evaluation, and
      explicit activation approvals before a candidate reaches the active
      patient release.
    - [x] Preserve immutable release history and keep the last approved release
      active whenever discovery, fetching, parsing, review, or evaluation
      fails.
    - [x] Keep general public-web search, arbitrary URLs, and direct live-page
      transmission to DeepSeek unavailable in patient chat.
    - [x] Keep National Medical Products Administration, selected WHO
      resources, and doctor-only literature discovery excluded until separate
      governed source-family decisions are approved.
    - [x] Defer custom retrieval/reranking training unless later evaluation
      demonstrates a specific unresolved retrieval failure.
  - [x] Implement the synthetic personalized-context foundation.
    - [x] Select question-relevant profile, measurement, condition,
      medication, Clinical Event, and recovery-plan fields server-side instead
      of transmitting the full patient record.
    - [x] Preserve stable context IDs, field provenance, source record, and
      recorded dates through provider input and structured-output validation.
    - [x] Treat one elevated blood-pressure measurement as a dated observation,
      not an inferred diagnosis.
    - [x] Show bilingual category, provenance, and date cards when an answer
      actually uses patient context.
    - [x] Exercise the path with a synthetic account while keeping the broker
      compatible with future patient-entered records in the same tables.
  - [ ] Complete the symptom-first 100-question Slice 9A reset.
    - [x] Create candidate contract
      `dr-ai-rural-symptom-first-canonical-v1` with all 100 canonical questions,
      85 separate variants: 25 symptom-only, 31 disease-name-removed, eight
      colloquial, ten abbreviated, and 11 multi-turn. Every variant has its own
      urgency route, controlled presentation fields, source-policy profile,
      relevant/forbidden source fields, required answer behavior, and
      retrieval/model permissions. Structural minimums require every variant
      kind plus multi-turn coverage of all ten domains and all five routes.
    - [x] Keep the contract evaluation-only and explicitly excluded from the
      retrieval corpus, model evidence, and training data.
    - [x] Add a controlled deterministic presentation covering symptoms,
      anatomy, onset, duration, trajectory, severity, associated signs,
      measurements, population, pregnancy, exposures, trauma, danger signals,
      negated concepts, and hypothetical/not-present concept mentions.
    - [x] Replace the small emergency-only keyword entry point with
      combination-, severity-, context-, and negation-aware rules that execute
      before retrieval or model calls and return candidate 120 plus brief
      scene-safety copy. The controlled `SafetyAssessment` is now the sole
      emergency authority: the former overdose/self-harm regex override was
      removed and those presentations use controlled concepts, negation,
      hypothetical handling, danger-signal selection, and the same fixed
      zero-call emergency response path.
    - [x] Pass the no-cost local candidate safety gate: 37/37 proposed critical
      canonicals and 45/45 critical variants route to emergency before calls;
      0/63 other canonicals false-route to emergency. A contract-driven
      integration test also executes all 82 critical canonical/variant inputs
      through the real patient-chat entry point. Multi-turn inputs are sent as
      real sequential requests, with fail-fast retrieval on the turn where the
      emergency presentation is complete. This is not clinical approval.
      The unified-authority v6 local artifact also asserts production-shared
      assessment parity over all 100 canonicals and 85 variants, including
      affirmed and negated/hypothetical Chinese and English overdose/self-harm
      inputs; candidate recall remains 37/37 and 45/45 with zero non-emergency
      false positives.
    - [x] Add a separate declarative non-emergency care-timing policy over the
      controlled presentation. The no-cost candidate v5 gate matches all 100
      canonical route labels and all 85 variant route labels across emergency,
      medication boundary, same-day, clinician-contact, and routine routes.
      Multi-turn variants run sequentially through one production-shared,
      bounded user-turn continuity resolver: emergency follow-ups remain
      pre-retrieval/model, only the latest needed patient-authored turn can
      carry, action-only new topics do not inherit old medical context, and the
      current literal retrieval query stays unchanged. The v5 safety artifact
      uses the same resolver as the endpoint.
      The server exposes the route, constrains the model's allowed next action,
      rejects same-day downgrades and model-selected emergency actions, and
      preserves `seek_local_care` in evidence/provider fallbacks. The rule table
      and fixed timing copy remain pending named review and are not approved.
    - [x] Audit the active local release
      `KBIR-D3DFA94CC95660019B6EF94E` case by case with zero provider calls:
      36 candidate-hit cases, 17 `no_eligible_evidence` cases, and 47
      pre-safety/no-call cases. Candidate source IDs remain unlabelled pending
      case-specific clinical review and cannot be counted as support.
      The production-shared sequential-continuity slice includes real endpoint
      coverage for all five critical multi-turn variants plus urgent,
      clinician-contact, routine, and medication-boundary sequences. Current
      verification for the expanded matrix passed all 250 collected API tests
      in the repository's established 3 + 4 + 243 database-safe partitions,
      full Ruff, Alembic drift (`No new upgrade operations detected`), and
      `git diff --check`. Alembic retained the pre-existing cyclic
      `kb_rights_records`/`kb_sources` foreign-key warning.
    - [ ] Obtain named clinical, native-Simplified-Chinese, and product review
      of every urgency label, presentation annotation, variant, relevant/
      forbidden source label, required behavior, and scene-safety instruction;
      then freeze a new checksum rather than editing an approved suite in place.
      A generated review packet now binds the exact contract, v8 coverage
      artifact, and 31-source intake queue. It exposes all 100 canonical and 85
      variant annotations, active retrieval candidate IDs, and link-only leads
      while remaining evaluation-only and content-free. Its fail-closed
      validator is structurally green but records 949 pending readiness items;
      named decisions have not been supplied or inferred.
    - [ ] Fill case-specific clinically relevant and forbidden source IDs,
      ingest rights-cleared authoritative patient-facing evidence through the
      governed workflow where gaps remain, and rerun a release-matched retrieval
      gate with strong symptom-only performance and zero forbidden leakage.
      A v8 zero-provider local audit now covers all 100 canonicals and all 85
      variants separately: 20/33/47 canonical candidate/no-evidence/pre-safety
      decisions and 14/25/46 variant decisions. Presentation centrality now
      applies to literal as well as generated views, so broad incidental matches
      previously admitted through generic literal overlap fail closed; multiple
      pregnancy/exposure/trauma contexts must all be central. Relevance remains
      unapproved. The versioned Mainland source-candidate queue now maps an
      explicit official research lead to all 33 canonical and all 25 variant
      no-evidence presentations. A no-cost validator binds these mappings to
      the contract and v8 coverage checksums; rejects raw content, unsafe
      domains, approval drift, or evaluation/retrieval/training-data mixing;
      and fails closed if a future observed gap lacks a research lead. The v5
      artifact passes this structural discovery gate with 31 sources, zero
      provider calls, and no evidence or approval claim.
      Research-lead mapping is not corpus coverage: all 31 candidate sources
      remain link-only and activation-blocked because official publication and
      public access do not establish commercial storage, transformation,
      embedding, excerpt-display, or provider-transmission rights.
    - [x] Add a separate canonical retrieval-only policy and scorer rather than
      treating coverage counts as retrieval quality. The checksum- and active-
      release-bound v1 policy requires reviewed labels for all 92 retrieval-
      eligible subjects and explicitly gates recall@6, MRR, relevant-decision
      correctness, symptom-only recall, paired-variant non-degradation,
      forbidden leakage, retrieval errors, pre-safety calls, latency, provider
      calls, and cost. The v9 audit records per-turn production retrieval
      latency and call counts without making planner/answer-model calls. Its
      first artifact is structurally valid but fails closed with 101 readiness
      and seven metric failures because all relevant/forbidden source labels
      remain pending: candidate sufficiency is 34/92 overall and 3/8 for
      retrieval-eligible symptom-only variants, not a clinical-support score.
      The operational diagnostics show 93/93 zero-call pre-safety subjects,
      zero retrieval errors, 918 ms p95, 1,687 ms maximum, and zero provider
      calls/cost. Labelled recall and non-degradation remain unscored.
    - [x] Implement the local multi-view
      literal/canonical/population-exposure-action retrieval foundation with
      batched embeddings, unchanged per-view rights/release filters,
      presentation-central admission for literal and generated patient hits,
      literal-order preservation among admitted evidence,
      one literal-query reranker call, and content-free view telemetry. Focused
      tests prove symptom-only colloquial and heat-exposure recovery from zero
      literal hits and preserve unrelated-source safeguards. Contextual
      pregnancy/exposure/trauma queries additionally require that context to be
      central in source metadata and a reported symptom to appear in the
      passage. The v8 audit makes each synthetic user turn a separate request,
      preserves the literal query, runs deterministic safety before every
      retrieval, and stores a content-free per-turn trace. It made zero provider
      calls. This is not the reviewed
      non-degradation/relevance gate: that remains blocked on the case-specific
      labels and corpus coverage above.
    - [ ] Evaluate complete answers separately for claim-to-citation support,
      uncertainty, practical next action, prohibited medication changes, and
      no autonomous diagnosis before resuming paid Slice 9B work.
      The versioned contract now includes a separate complete-answer policy and
      a no-cost preflight/scorer. It requires 100% machine pass, emergency
      recall and zero-call behavior, medication-gate behavior, claim support,
      relevant-source use, uncertainty, route/action behavior, provider usage
      reporting, variant non-degradation, and zero forbidden leakage, plus
      explicit latency/cost ceilings. Independent human review remains a
      separate mandatory gate that an AI judge cannot close. The first
      five-case preflight spans all five route classes, fixes concurrency at
      one, calculates a worst-case `$0.013496` estimate under a `$0.10` cap,
      makes zero provider calls, and correctly refuses execution because the
      candidate contract/critical set are not frozen or approved and all 53
      model-eligible canonicals plus 39 model-eligible variants still lack
      approved case-specific source IDs and coverage. The v4 preflight records
      zero structural and 190 readiness failures. A separate executable
      rollback-only production-path lane now covers all 93 pre-model subjects:
      82 emergency canonical/variants and 11 medication-change refusals. Its v2
      artifact passes 93/93 with exact route/action behavior, exact controlled
      emergency guidance, zero retrieval/planner/answer calls, zero tokens/cost,
      11 ms p95 and 29 ms maximum latency, and zero persisted evaluation threads
      or events. A complementary rollback-only lane now covers all 92
      post-safety subjects through real active-release retrieval with external
      planner/answer requests forcibly disabled. Its v2 artifact passes 92/92
      safe-fallback and route/action behavior with 34 candidate-sufficient and
      58 no-evidence decisions, 92 retrievals, zero provider requests/tokens/
      cost, 900 ms p95 and 975 ms maximum latency, and no persisted evaluation
      data. This is not the retrieval-quality, generated-answer, or human-review
      gate.
  - [ ] Complete chatbot refinement Slice 9A: retrieval correctness,
    transmission rights, and production ranking.
    - [x] Enforce `model_provider_transmission_allowed`, rights expiry/revocation,
      audience, review, and active-release admission both during patient-index
      construction and immediately before external-model transmission.
    - [x] Add one declared self-hosted production multilingual embedding
      service and reranker profile, require their exact release lineage in
      production, and retain the local deterministic path only for development,
      tests, and recorded degradation fallback. Hong Kong is acceptable for
      the current stage; final region approval remains evidence-based.
    - [ ] Replace the active production deployment's local baseline with the
      declared services after infrastructure deployment and medical evaluation.
      - [x] Build and locally validate an isolated HTTP inference service for
        the 4-vCPU/8-GB GTE candidate pair with immutable model/code revisions,
        a 30-passage rerank cap, 512-token CPU cap, measured peak memory,
        Chinese ranking smoke, and the main API's real embedding contract.
      - [ ] Deploy the candidate on the upgraded Linux CVM, measure its actual
        peak memory/latency there, rebuild the full immutable index, and accept
        GTE only if every frozen Slice 9A retrieval gate passes.
    - [x] Freeze retrieval-only candidate cases and implement Recall@k,
      nDCG/MRR, no-evidence precision, forbidden-source leakage, diversity,
      latency, and jurisdiction/language gates without using sealed answer
      cases for tuning. The runner fails closed while clinician review is
      pending.
    - [ ] Record clinician approval/corrections and pass every frozen retrieval
      threshold against the approved production services.
    - [ ] Reconcile the current Mainland-specific code/config identifiers with
      the approved Hong Kong-or-Mainland production-region decision before
      production activation; documentation approval alone does not change the
      runtime validator.
  - [ ] Complete chatbot refinement Slice 9B: adaptive multi-call RAG and
    retrieval rescue.
    - [x] Keep ordinary questions on original-query retrieval followed by one
      grounded-generation call; trigger an extra DeepSeek planner call only for
      server-detected ambiguity, colloquial wording, short references, or weak
      initial retrieval.
    - [x] Require a strict bounded query-understanding schema, validate meaning
      preservation, search both original and candidate queries, fuse and
      deduplicate results, and retain the same rights/evidence gates. The
      symptom-first validator now requires controlled-presentation containment
      and preservation: aliases may normalize reported facts, but added or
      omitted symptoms, anatomy, timing/duration, severity/trajectory,
      associated signs, measurements, population/pregnancy/exposure/trauma
      context, requested actions, danger signals, negation/hypothetical state,
      or condition labels are rejected before retry retrieval. The planner sees
      only the prior user turn admitted by deterministic continuity; its output
      replaces only the trusted presentation's literal query, so retry views
      and presentation centrality cannot become model-authored.
    - [x] Make context-resolved retrieval authoritative for referential and
      ambiguous rescue: exclude original-only candidates, use an original rank
      only to corroborate an identical checksum, fail closed when resolved-topic
      evidence is insufficient, and forbid generic utility gains from claiming
      `improved`.
    - [x] Permit at most one rewrite call and one retrieval retry; record only
      content-free trigger, attempt, token/cache, latency, cost, retrieval-
      delta, and fallback metadata.
    - [ ] Prove measured improvement on frozen hard queries without degrading
      ordinary-query quality or exceeding approved latency/cost budgets. The
      candidate suite and runner are frozen. Product-owner approval by Harry
      Cao and clinical/native Simplified Chinese approval by Hou Jin, Doctor at
      Beijing Hospital, are recorded for 2026-07-18 with no corrections; the
      first live run failed and is preserved as evidence. Corrected v2 trigger,
      feasibility, planner-use, latency, and cost gates pass no-cost preflight;
      the v2 live artifact also failed on the local fallback ranking stack.
      Further paid runs are paused until a new semantic release passes Slice 9A.
  - [ ] Complete chatbot refinement Slice 9C: semantic claim support, answer
    verification, and follow-up quality.
    - [x] Add the first deterministic sentence-level support gate so a valid
      passage ID is not sufficient by itself. Each displayed sentence is
      checked only against its cited passages and cited authorized context for
      numeric expressions, controlled disease/presentation concepts, and
      topic-bearing semantic overlap; unrelated valid citations fail closed.
      Cited patient context also requires the server-issued attribution phrase,
      and controlled provenance language cannot contradict the cited record
      origin. Unsupported diagnostic subtypes are metadata-only.
    - [x] Prevent model-generated uncertainty text from introducing unsupported
      numbers, disease concepts, or clinical-presentation features, while
      allowing it to restate the patient's reported presentation.
    - [ ] Extend and clinician-calibrate the gate for thresholds, intervals,
      causal assertions, monitoring schedules, medication/treatment claims,
      and subtle contradiction; run the frozen complete-answer evaluation
      before claiming semantic validation.
    - [x] Add a separate complete-answer machine scorer and fail-closed
      preflight with frozen-contract/checksum binding, active-release source
      label checks, one-provider-at-a-time/concurrency-one execution,
      deterministic token-cap spend estimation, a five-case initial batch,
      repeated-provider-failure stop policy, provider-reported usage/cost
      requirements, variant non-degradation, and an independent human-review
      gate that remains pending even when every machine metric passes. Evaluator
      v3 requires exact `initial_batch` or `full_contract` input sets, prevents
      a partial batch from claiming the full machine gate, applies each
      variant's own route/permission/source labels, and rejects duplicate IDs,
      truthy-string booleans, negative call/token/cost values, or duplicate
      citations.
    - [ ] Keep deterministic validators mandatory. Treat any optional second
      DeepSeek verification call as a bounded flagging aid that cannot override
      deterministic failure or substitute for independent clinical review.
    - [ ] Add a structured follow-up question, clarification purpose, and
      missing-information category to the answer contract; reject questions
      that are unsafe, redundant, repetitive, or already answered.
  - [ ] Complete chatbot refinement Slice 9D: real-context privacy,
    adversarial isolation, and chat lifecycle.
    - [ ] Enforce trusted synthetic/real data origin and keep real context off
      until consent, field allowlisting, no-training/no-retention, Mainland-
      China location, privacy, legal, provider, and product approvals are all
      file-backed and active.
    - [ ] Test prompt injection in user messages, patient-entered fields,
      doctor-authored records, conversation history, and retrieved passages;
      untrusted content must not change safety, authorization, or policy.
    - [ ] Define minimum and maximum history retention, implement expiry and
      patient deletion behavior, and verify export/delete/backup/restore and
      cross-patient/cross-role isolation without retaining deleted content in
      telemetry.
  - [ ] Complete chatbot refinement Slice 9E: operational controls and the
    pre-release evidence package.
    - [ ] Implement independent model/prompt, retrieval-release,
      embedding/reranker, corpus, and source-family kill switches and rollback.
    - [ ] Add provider concurrency budgets, timeouts, retries, circuit breakers,
      rate limits, pseudonymous cache/tenant isolation, token/cache/latency/
      provider-cost accounting, and redaction-safe dashboards.
    - [ ] Run retrieval-rescue, claim-support, personalization, multi-turn,
      rural/low-bandwidth, safety, adversarial, load, outage, and recovery
      evaluations; keep AI judging distinct from named medical/native-Chinese
      human review and keep evaluation data out of retrieval tuning.
    - [ ] Rehearse rollback, assign monitoring/incident owners, and produce the
      versioned limitations, evaluation, observability, and rollback package.
  - [ ] Complete final chatbot Slice 10 production, clinical, and
    commercialization verification only after Slices 9A-9E are complete.
    - [ ] Re-run the frozen model, retrieval, semantic-support, privacy,
      security, usability, load, failure, recovery, and live-workflow gates on
      the exact release candidate.
    - [ ] Obtain named medical, native-Chinese, privacy, security, legal,
      provider-contract, data-location, product, operations, and regulatory
      signoffs with known limitations and rollback ownership.
    - [ ] Use a small monitored cohort and verify generation, retrieval,
      reranker/index, and source-family kill switches before the 2026-08-12
      production/commercialization decision.
  - [ ] Define stable AI assessment request/response contract.
  - [ ] Implement diagnostic input collection.
  - [ ] Add CT/image reference selection.
  - [ ] Add clinical-variable input.
  - [ ] Add optional genomic-field input.
  - [ ] Add assessment run status and result history.
  - [ ] Add simulated/model adapter boundary.
  - [ ] Add doctor review and limitation display.
  - [ ] Add diagnostic audit events.
  - [ ] Implement AI recovery-plan draft generation.
  - [ ] Add recovery-plan regeneration/revision history.
  - [ ] Harden patient chat red-flag path.
  - [ ] Harden patient chat unsafe-prompt path.
  - [ ] Harden timeout, quota, malformed-response, and rate-limit fallbacks.
  - [ ] Add conversation history where appropriate.
  - [ ] Implement Medication Safety Agent adapter/framework.
  - [ ] Add AI workflow tests and safety fixtures.
- [ ] Phase 4: Clinic operations
  - [ ] Implement medicine inventory list/detail/edit flow.
  - [ ] Implement equipment list/detail/edit flow.
  - [ ] Implement bed and ambulance resource state flow.
  - [ ] Implement referral-resource list/detail/edit flow.
  - [ ] Implement equipment booking flow.
  - [ ] Add booking conflict detection.
  - [ ] Implement appointment booking flow.
  - [ ] Implement appointment scheduling and rescheduling.
  - [ ] Implement appointment reminders.
  - [ ] Implement doctor team invite/add/remove flow.
  - [ ] Add clinic-operations tests and audit assertions.
- [ ] Phase 5: Specialist, admin, and commercial modules
  - [ ] Implement specialist role access.
  - [ ] Implement consultation request triage.
  - [ ] Implement consultation accept/reject flow.
  - [ ] Implement specialist response flow.
  - [ ] Implement consultation attachments or structured annotations.
  - [ ] Define voice/video stretch-gate acceptance.
  - [ ] Implement admin dashboard shell.
  - [ ] Implement user management.
  - [ ] Implement administrator-owned hospital/clinic management.
  - [ ] Implement audit-event read/search.
  - [ ] Implement system-status view.
  - [ ] Implement invoice and payment-status surfaces.
  - [ ] Implement clinic revenue summaries.
  - [ ] Implement analytics disease statistics.
  - [ ] Implement analytics referrals and recovery progress.
  - [ ] Implement analytics AI usage and operational activity.
  - [ ] Implement support/deletion/feedback queues.
  - [ ] Add specialist/admin/commercial tests.
- [ ] Phase 6: Production hardening and release
  - [x] Refactor doctor Patient Management into a focused patient workspace.
    - [x] Add assigned-patient list/search navigation as a narrow, scannable
      column on desktop/tablet.
    - [x] Add selected-patient summary header with identity-safe essentials and
      workflow status only.
    - [x] Add subsection navigation for Overview, Profile, Medical History,
      Clinical Events, Medications & Prescriptions, Recovery Plans, Imaging,
      and Consultation & Activity.
    - [x] Keep one primary task per subsection, with section-level loading,
      empty, validation, failure, unauthorized, and success states.
    - [x] Add responsive behavior for phone-width doctor layouts without text
      overflow or overlapping controls.
    - [x] Verify with focused Flutter widget/golden coverage and
      `./scripts/verify_flutter.sh`.
      - Focused widget coverage was added for desktop workspace navigation and
        phone-width compact patient selection; dashboard golden baselines were
        not updated because this slice did not intentionally change the frozen
        dashboard golden surfaces.
  - [x] Add production multilingual foundation.
    - [x] Add Flutter localization generation with ARB files for English and
      Simplified Chinese.
    - [x] Add system-locale resolution for Chinese/English with English
      fallback, plus a securely persisted in-app override.
    - [x] Add patient and doctor Account controls that apply language changes
      immediately in the same application.
    - [x] Treat Simplified Chinese as the primary production copy path and
      English as the secondary supported locale.
    - [x] Localize UI copy, actions, validation, empty states, status labels,
      and user-facing errors through generated localization accessors.
    - [x] Keep API responses machine-readable and translate stable codes/enums
      in Flutter.
    - [x] Do not automatically translate user-entered clinical content.
    - [ ] Add locale-aware date, time, phone-number, and reminder formatting.
  - [ ] Add API 5xx monitoring.
  - [ ] Add auth/chat/assessment/upload monitoring.
  - [ ] Close external notification delivery gate with China-market SMS as the
    primary channel.
    - [ ] Choose the allowed Phase 6 notification channels; default to
      phone-number SMS for Chinese customers, with native push, native local
      notifications, or email added only if there is a clear product/release
      need.
    - [ ] Configure approved SMS provider credentials and account access for
      local, staging, and production environments without committing secrets.
    - [ ] Add environment-separated notification configuration, sender
      templates, rate limits, retry limits, and provider failover rules where
      appropriate.
    - [ ] Implement delivery workers/adapters with idempotency, retry,
      delivery status, failure status, suppression/opt-out, and rate limiting.
    - [ ] Add patient consent and phone-number verification/preference
      controls before any real SMS delivery.
    - [ ] Keep notification copy clinically neutral and avoid medication names,
      recovery-plan instructions, task details, imaging details, URLs, tokens,
      secrets, or clinical interpretations in outbound SMS content.
    - [ ] Store delivery metadata only: channel, status, timestamps, safe
      template identifier, retry count, and provider message-id hash if needed.
    - [ ] Add tests for successful delivery, retry, provider failure, disabled
      preferences, unverified phone numbers, wrong-role/cross-patient
      boundaries, audit metadata, and log redaction.
    - [ ] Verify the SMS path in staging with synthetic users and test phone
      numbers only before any production or real-user delivery.
  - [ ] Add crash/error tracking.
  - [ ] Configure alert routing.
  - [ ] Run backup rehearsal.
  - [ ] Run restore rehearsal.
  - [ ] Run security and privacy review.
  - [ ] Verify staging/production separation.
  - [ ] Prepare Android release signing.
  - [ ] Prepare iOS release signing.
  - [ ] Prepare TestFlight path when account access exists.
  - [ ] Prepare Play closed-testing path when account access exists.
  - [ ] Run production deployment rehearsal.
  - [ ] Update deployment/recreation runbook.
  - [ ] Prepare tester onboarding.
  - [ ] Verify support, feedback, and deletion workflows.
  - [ ] Confirm no production-facing placeholders remain.
  - [ ] Run final acceptance checklist.
  - [ ] Record production v1.0 closure evidence.

### Production v1.0 Deferrals and Gates

This historical heading is retained for link stability. The following gates
control live clinical/payer operation and public distribution; they do not
reduce the required engineering and product quality of v1.0.

#### Safety/regulatory gated

- Real clinical claims.
- Real diagnostic model use for patient care.
- Real patient data ingestion before privacy, consent, legal, and security readiness.
- Production clinical deployment.
- Live payer/hospital integration, real eligibility or claim processing,
  automated coverage/payment decisions, and any suspected-fraud determination.
- Any public claim that Dr. AI prevents abuse, saves money, validates treatment,
  or improves clinical outcomes.

#### Technical stretch gates

- Live voice/video consultation if real-time infrastructure is not ready.
- Barcode scanning if package/device scope is too large for the production v1.0 release window.
- Full insurance/payment processing, prior authorization, denial, appeal, or
  adjudication integration.
- DICOM viewing/segmentation if not required for the initial commercial release.

#### Not v1.0

- National EHR integration.
- Wearables.
- Offline mode if still too large.
- Disease surveillance or broad predictive public-health analytics unless explicitly added to the v1.0 commercial scope.

### Current v1.0 Production-Readiness Definition of Done

The current v1.0 product is engineering/product production-ready only when:

- Every visible v1.0 item is functional or intentionally
  removed/disabled.
- Patient, doctor, and payer-reviewer roles complete the frozen representative
  China-first scenario suite from proposed care through human cost review.
- Scenario, rule, price-reference, and evidence releases are configurable and
  versioned; adding an admitted scenario does not require a disease-specific
  application fork.
- Existing patient/doctor clinical foundations remain intact; specialist,
  clinic-operations, admin, legacy billing, and public-release work outside the
  three-party core may remain hidden and deferred.
- All data is persisted through migrations and survives restart/deployment.
- Every major workflow has loading, empty, validation, failure, unauthorized, and success states.
- Cross-role, cross-patient, cross-payer, and reviewer-note access is blocked
  and tested.
- Audit logs exist for sensitive operations.
- Claim/envelope totals reconcile to immutable line items using integer minor
  units and explicit currency.
- Every envelope and alert shows provenance, jurisdiction, version/effective
  date, uncertainty, and a human next action.
- A variance cannot automatically change clinical care, claim/payment state,
  coverage, clinician standing, or an abuse/fraud label.
- Clinicians can explain exceptional care and authorized payer reviewers can
  record a human resolution with immutable history.
- Patient-facing cost explanations distinguish planned, delivered, billed,
  allowed, paid, and patient-responsibility amounts.
- The frozen evaluation reports per-scenario and aggregate alert
  precision/recall and false-positive rate, plus arithmetic, isolation,
  fallback, exception, and under-treatment-risk evidence.
- Local, controlled-staging, and future production deployment configurations
  can be recreated from docs; backup/restore, monitoring, incident response,
  kill switches, and rollback are verified in proportion to risk.
- Product/engineering readiness is reported separately from live-use
  authorization. Until external gates close, every external walkthrough states
  that the active data are synthetic/de-identified and the product is not yet
  authorized or validated for clinical diagnosis, reimbursement, fraud
  detection, real savings, or public production use.

### Worktree and Branch Maintenance

Current repository baseline after this cleanup: `main` should contain the completed beta/demo MVP foundation, release-preparation evidence, production v1.0 re-scope, and this worktree-maintenance policy. The previous stacked beta branches remain historical references, but future production v1.0 work should branch from `main` unless there is a specific reason to inspect old stack history.

Future development should keep the worktree organized as follows:

- Start each production phase or clearly bounded feature from a fresh `codex/phase-N-short-name` or `codex/<module>-<goal>` branch based on current `main`.
- Keep one active branch per execution lane; avoid continuing new production work on legacy beta branch names.
- Before editing, run `git status --short --branch` and confirm whether existing dirty files belong to the current task.
- Commit completed, verified slices before starting a new phase, external deployment pass, or unrelated module.
- Do not leave generated release evidence, closure records, migrations, or screenshots untracked when they are part of the milestone proof.
- Do not commit local secrets, real keystores, populated `.env` files, credentials, or private patient data.
- Keep generated build directories, local caches, and disposable simulator output ignored or outside the repo unless a screenshot/archive is intentionally saved as evidence.
- Merge completed phase branches back to `main` after the phase is verified and documented.
- Update this implementation plan and the relevant closure record whenever branch strategy, release state, deployment status, or production scope changes.
- Push, tag, create pull requests, deploy, or invite testers only when explicitly authorized.

## Historical Beta Milestone Tracker

- [x] Week 1: Foundation and design freeze
  - [x] Days 1-2: foundation, implementation-facing design freeze, and API contract
  - [x] Days 3-5: data/auth shells, seeded dashboards, and Week 1 gate
- [x] Week 2: Complete the golden care loop
  - [x] Days 6-7: patient search/list, profile, medical history, medications, doctor notes, and core states
  - [x] Days 8-9: presigned demo-image upload, simulated assessment, result screen, and audit events
  - [x] Day 10: polish gate for care-loop completion, neutral unrelated-patient denial, and failure recovery
- [x] Week 3: Recovery, reminders, chat, and consultation
  - [x] Days 11-12: recovery-plan editor, patient Today tasks, completion tracking, and local notification shell
  - [x] Days 13-14: DeepSeek chat and specialist consultation
  - [x] Day 15: full doctor-led gate, chat safety fixtures, duplicate consultation reuse, and small-screen Ask Dr. AI polish
- [ ] Week 4: Hardening and beta release
  - [x] Days 16-17: accessibility, security, validation, log hygiene, dependency, audit, and backup/restore planning hardening
  - [x] Days 18-19: local device/browser release-gate checklist, beta packaging/deployment preparation, and privacy/consent/deletion/feedback/limitations surfaces
  - [x] Day 20: local clean-account demo plan, backup demo evidence plan, release notes, tag plan, tester invite checklist, monitoring checklist, and approved Tencent staging same-origin web/API deployment
- [ ] Final acceptance criteria verified
- [ ] `v1.0.0-beta.1` tagged and released

---

## Progress and Change Log

Add one row whenever implementation status, scope, architecture, or a major decision changes.

| Date | Status | Change | Evidence / Files | Next Step |
|---|---|---|---|---|
| 2026-07-24 | Complete locally - explicit patient-chat grounding modes and useful no-evidence path | Replaced the current automatic no-evidence refusal boundary with three additive, separately governed response modes: claim/citation-validated `approved_evidence`, citation-free and patient-record-free `general_model_knowledge` when adequate approved evidence is unavailable, and server-owned `fixed_safety_response` for emergency, authorization, provider, malformed-output, and other fixed paths. Preserved authentication, bounded continuity, controlled clinical presentation, deterministic emergency/prohibited-action routing, server urgency/action authority, provider-transmission rights, and historical response compatibility. Refined the planner schema, kept literal-query-first retrieval, searched up to two accepted planned queries independently, and added context-authoritative versus self-contained reciprocal-rank fusion with checksum deduplication and source caps. Added independent grounded/general kill switches and schema versions, content-free grounding/retrieval/fallback/repair telemetry plus migration `0039`, intent-adaptive grounded length, safe mixed-medication partial handling, and provider-detail redaction from patient responses. Flutter now displays distinct grounding banners, actionable reviewed source cards, no Sources block for general knowledge, and preserved uncertainty/context/emergency states. Ruff and all 63 focused backend chatbot tests pass; migration upgrade and Alembic drift pass with only the known knowledge-rights/source cycle warning; Flutter analysis passes through an exact ASCII-path copy and both focused patient-chat widget tests pass. Historical Slice 9A/9B metrics and clinical/production gates remain unchanged. No frozen/paid evaluation suite, deployment, activation, commit, push, or real-patient action was performed. An initial focused test revealed that shared test settings inherited a configured provider credential and issued one unintended single request; the fixture now forcibly removes provider credentials unless a stubbed contract test explicitly opts in. | `services/api/app/patient_chat.py`, `services/api/app/ai_chat.py`, `services/api/app/retrieval_rescue.py`, `services/api/app/chatbot_contracts.py`, `services/api/app/config.py`, `services/api/app/models.py`, `services/api/migrations/versions/20260724_0039_chatbot_grounding_modes.py`, `services/api/tests/`, `apps/dr_ai_app/lib/features/chat/presentation/chat_screens.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/`, `Dr_AI_Product_Requirements_Document_v1.0.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_Product_Quality_Gate.md`, `docs/periodic_dev_docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/periodic_dev_docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/chatbot-evaluation/Phase_3_Chatbot_Evaluation_and_Model_Strategy.md` | Keep general-model knowledge enabled only in explicitly approved early-stage environments; independently disable it to restore fixed no-evidence behavior. Clinical/native-Chinese review, passing retrieval/answer gates, privacy/legal/provider evidence, staged rollout, and production activation remain separate. |
| 2026-07-24 | Complete locally - doctor Payment Request outcome visibility and explicit payer rejection | Expanded the human payer-review contract with an explicit `reject` action and persisted `rejected` request status while retaining required reason codes, membership-scoped authorization, metadata-safe audit, and reviewer-only note isolation. Rejection is counted as a completed human review but is not described as payment denial, coverage adjudication, reimbursement, or a final patient obligation. The doctor Payment Requests history now defaults to all requests and provides counted All, Awaiting outcome, Accepted, Rejected, and Closed filters; accepted and rejected cards remain in the same immutable request history and show the current human outcome, review date, and non-private reason code, while reviewer-only notes remain redacted. The payer review dialog now exposes localized Accept and Reject actions. Focused backend coverage proves the reject transition, doctor readback, completed-review accounting, and note redaction; focused Flutter tests prove payer rejection and doctor accepted/rejected filtering; full Ruff/API tests, Flutter analysis, all active widget/golden tests, and whitespace checks pass. No migration, existing-data reset, commit, push, deployment, real payer decision, coverage determination, or payment action was performed. | `services/api/app/care_cost.py`, `services/api/tests/test_care_cost_workflow.py`, `apps/dr_ai_app/lib/features/care_cost/presentation/care_cost_screens.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/doctor_payer_requests_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `Dr_AI_Product_Requirements_Document_v1.0.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Keep formal appeals, coverage/adjudication integration, payment processing, and live payer authorization as separately governed future work. |
| 2026-07-24 | Complete locally - Clinical Service foundation and imaging-procedure vertical slice | Added the smallest canonical persisted `ClinicalService` foundation for ordered, scheduled, and delivered care, with patient and Clinical Event ownership, recognizable category/name/code fields, ordering doctor, optional performing provider/clinic and appointment, governed lifecycle states and dates, metadata-safe audit events, and explicit imaging-evidence relationships. Migration `20260724_0038` safely creates the service model, converts every existing event-linked specialist consultation into a one-to-one consultation service, moves its active financial companion without changing the companion identifier or any immutable payer-request snapshot, links `MedicalImagingAsset` evidence to the service, and replaces consultation-specific cost linkage with the database-enforced rule that one active `CareCostItem` belongs to exactly one medication/product or clinical service. Doctor Patient Management now displays `No cost recorded`, `Cost pending`, estimate/final amounts, and already-submitted state directly on medication, consultation, and imaging-service records with prominent localized Add/Complete/Edit cost actions. The Imaging subsection now creates and edits real imaging procedures, keeps clinical, scheduling/service, and financial details separated, permits urgent clinical saves with pending cost, and attaches multiple image/report assets as non-billable evidence without creating extra charges. Patient ledger and doctor Payment Requests consume the same companion and expose category, lifecycle status/date, pricing state, amounts, eligibility, and explicit blocked reasons; server-side submission revalidates authorization, source identity/status, patient/event ownership, currency, positive/exact allocations, completeness, and duplicate submission, while prior request lines remain immutable after later source edits. Appointments remain optional scheduling containers rather than automatic charges; bookings, uploads/reports, prescription documents, diagnoses, notes, observations, and ungoverned equipment reservations are not priced. Ruff and the complete API test suite passed; the focused end-to-end imaging test covers pending cost, two evidence files with one charge, payer submission, source mutation, immutable snapshots, read-only patient access, and preserved order time; Alembic upgrade, check, one-step downgrade, re-upgrade, and final drift check passed; and `./scripts/verify_flutter.sh` passed analysis plus all active widget and golden tests. No existing local data was reset, and no commit, push, deployment, coverage determination, payer decision, or real patient-data action was performed. | `services/api/migrations/versions/20260724_0038_clinical_services_imaging.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/app/care_cost.py`, `services/api/tests/test_care_cost_workflow.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/doctor_payer_requests_screen.dart`, `apps/dr_ai_app/lib/features/care_cost/`, `apps/dr_ai_app/lib/features/patient/`, `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `Dr_AI_Product_Requirements_Document_v1.0.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_ERD.md`, `docs/Dr_AI_v1.0_Product_Quality_Gate.md` | Extend the same source model only in this order and with a real lifecycle, authorization path, UI, and tests: completed consultation/visit plus broader appointment relationship; laboratory tests; treatment/therapy sessions; then governed equipment rental/use or explicit policy-backed fees. Deployment remains a separately approved action. |
| 2026-07-24 | Complete locally - source-linked clinical financial workflow | Removed the standalone doctor `Care & costs` Patient Management subsection and its generic CRUD editor, then moved compact financial capture into the natural medication/product and specialist-consultation forms. Each supported billable source can be saved with an explicit pending-cost, estimate, or final state; pending cost never blocks the clinical save but remains visibly ineligible for payer submission. Migration `20260724_0037` adds nullable source foreign keys, source-specific partial unique indexes, a single-source constraint, and `pricing_state` so the active `care_cost_item` is a structurally linked financial companion shared by the patient ledger and Payment Requests. Medication and companion writes are transactional; source edits synchronize the current ledger row; source deletion removes only the active companion; and existing immutable `payer_request_lines` remain unchanged historical evidence. Server-side submission validation requires an authorized treating doctor, matching patient and Clinical Event, a linked non-cancelled source, CNY, a positive estimated/final total, exact payer-requested plus expected-patient allocation, and no prior submission. Prescription documents do not create a second medication charge; the current imaging artifact/report, diagnoses, history, notes, recovery artifacts, reminders, and patient updates remain non-billable because none is a distinct delivered price-bearing service. Patient-facing terminology now separates totals/estimates, requested payer amounts, expected patient responsibility, and payer-review status. Ruff, the full API suite, Alembic drift, Flutter analysis, and all active widget tests pass; the focused care-cost golden suite was refreshed only after inspecting the intentional patient-ledger change; and the live synthetic workflow was inspected without console errors at 1280x832 and 412x917, including a durable pending medication save and its blocked reason in Payment Requests. No commit, push, deployment, live payer decision, coverage determination, or real patient-data action was performed. | `services/api/migrations/versions/20260724_0037_link_care_cost_clinical_sources.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/app/care_cost.py`, `services/api/tests/test_care_cost_workflow.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/doctor_payer_requests_screen.dart`, `apps/dr_ai_app/lib/features/care_cost/`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/care_cost_golden_test.dart`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_ERD.md` | Add distinct persisted imaging-procedure, laboratory-test, and treatment-session sources before pricing those workflows; preserve clinical-safety-first pending-cost saves and immutable request snapshots. Deployment remains a separate approved action. |
| 2026-07-24 | Complete locally - production-quality payer Account workspace | Upgraded `/payer/account` from a read-only list into a responsive bilingual account-management workspace. An authenticated payer reviewer can now update only the persisted reviewer-owned display name and professional title through the allow-listed `PATCH /api/v1/payer/me/profile` contract and can update or remove the optional account email through the existing shared account-email flow. The page prevents no-op and repeated saves, preserves entered values across recoverable failures, refreshes payer profile/dashboard state after a confirmed save, and maps validation, email-conflict, expired-session, unavailable-membership, loading, success, and connection states into localized UI. Organization name/type, jurisdiction, membership status, access scope, and organization verification are visually separated as read-only administrator-controlled governance data; the endpoint rejects attempts to write those fields and retains neutral `404` behavior without allowing self-verification or scope expansion. The Account page reuses the established password-change/session-revocation component and confirmed sign-out control. No payer phone, language, or avatar fields and no schema migration were added because the current payer data model has no authoritative persisted source for them. Ruff and the full API pytest suite passed; Flutter formatting, analysis, and all active widget tests passed; and a fresh local preview using the sample payer account was inspected without console errors at desktop and 412x917 mobile widths in Simplified Chinese. | `apps/dr_ai_app/lib/features/care_cost/presentation/payer_account_screen.dart`, `apps/dr_ai_app/lib/features/care_cost/application/care_cost_providers.dart`, `apps/dr_ai_app/lib/features/auth/application/auth_controller.dart`, `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `services/api/app/care_cost.py`, `services/api/tests/test_care_cost_workflow.py`, `docs/Dr_AI_v1.0_API_Contract.md` | Administrator-managed payer invitations, membership assignment/revocation, live organization verification, and any future persisted payer contact/language/avatar model remain separate planned work; deployment remains an explicit later action. |
| 2026-07-24 | Complete locally - dedicated doctor Payment Requests workspace | Upgraded `/doctor/payer-requests` from history-only readback into a dedicated, navigation-visible doctor workspace that combines request preparation and tracking. The responsive progressive flow now limits patient selection to the authenticated doctor's assigned-patient endpoint; groups selection by Clinical Event with status, dates, and totals; requires explicit eligible item selection; marks cancelled and previously submitted source rows unavailable; shows payer name/type; requires a doctor-owned clinical/request summary; provides an itemized review with explicit confirmation; prevents double submission; preserves form state after recoverable errors; displays a durable server-confirmed success state; and keeps immutable request history with localized human-review statuses while excluding payer-only notes. The Patient Management shortcut now deep-links with patient and event preselected instead of opening the former modal. The API now requires a non-empty item selection and rejects source rows already snapshotted by an earlier request with `409 conflict`; no schema or authoritative financial-arithmetic change was required. AI remains labelled `Not evaluated`, and no diagnosis, medical-necessity, eligibility, coverage, adjudication, contracted-rate, or payment behavior was added. Full API pytest and Ruff passed; `./scripts/verify_flutter.sh` passed analysis and all active widget tests; the care-cost golden suite passed; and the new 1280x832 desktop plus 412x917 mobile workspace renders were inspected, including a mobile navigation-height correction. | `apps/dr_ai_app/lib/features/doctor/presentation/doctor_payer_requests_screen.dart`, `apps/dr_ai_app/lib/shared/widgets/responsive_app_shell.dart`, `apps/dr_ai_app/lib/app/routing/router.dart`, `apps/dr_ai_app/lib/features/care_cost/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `apps/dr_ai_app/test/care_cost_golden_test.dart`, `apps/dr_ai_app/test/goldens/doctor_payment_requests_1280x832.png`, `apps/dr_ai_app/test/goldens/doctor_payment_requests_412x917.png`, `services/api/app/care_cost.py`, `services/api/tests/test_care_cost_workflow.py`, `docs/Dr_AI_v1.0_API_Contract.md` | Deployment remains a separate approved action; staging still reflects the earlier handoff commit. |
| 2026-07-23 | Deployed - first three-party care-and-cost vertical slice on Tencent staging | Committed the complete governed patient-chat and care-cost worktree to `main` at `e537289`, built and pushed backend image digest `sha256:baec9d8f175cdd30ca72e95bd61f45ca27afc679472b5342e5d9bb89914078fe`, rebuilt Flutter web for the Tencent same-origin HTTPS endpoint, and deployed the API/web gateway while retaining the already validated immutable retrieval image. Before mutation, captured and validated the Compose/Caddy configuration, Flutter web bundle, release artifacts, and PostgreSQL custom-format dump under host-only backup `backups/20260722T171712Z-e537289`. Alembic upgraded staging through `0036` and reported no drift; the synthetic seed remained idempotent on two runs; all containers were healthy; the public health/root endpoints returned `200`; the new care-cost and payer routes were present in the deployed schema; and the redaction-safe authenticated staging suite passed doctor/patient login, database writes, neutral cross-patient denial, recovery, chat, consultation, messaging, and Flutter deep links. This is still synthetic/de-identified staging: no live payer verification, adjudication, payment, AI medical-necessity decision, or commercialization gate was opened. | `deploy/tencent/staging/`, `scripts/run_staging_smoke.py`, `services/api/migrations/versions/20260723_0035_care_cost_payer_workflow.py`, `services/api/migrations/versions/20260723_0036_care_cost_schema_parity.py`, commit `e537289`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Define the governed China-first coverage/reference and expected-envelope slice before implementing any AI review score. |
| 2026-07-23 | Complete locally - first three-party care-and-cost vertical slice | Reframed the commercial product away from diagnosis and implemented the first transparent workflow across all three parties: payer registration with synthetic-only organization membership; Clinical Event-linked care-cost item CRUD; patient and doctor ledger readback; immutable payer-request snapshots; doctor request tracking; payer dashboard, scoped queue, detail, and human clarification/accept/escalate/close actions; responsive bilingual Flutter surfaces; and metadata-only audit coverage. AI review fields remain explicitly `not_evaluated` and cannot make a diagnosis, payment, abuse, or denial decision. The full backend suite and Ruff pass; Alembic upgrade/drift passes at `0036`; Flutter analysis and all active tests pass; and patient-mobile plus payer-desktop rendered golden inspection passes after correcting the detected material-surface and row-overflow defects. No live organization verification, coverage/claim adjudication, pricing/rule release, expected-care envelope, AI utilization assessment, deployment, push, commit, real patient data, or external account action was performed. | `services/api/app/care_cost.py`, `services/api/app/models.py`, `services/api/app/auth.py`, `services/api/migrations/versions/20260723_0035_care_cost_payer_workflow.py`, `services/api/migrations/versions/20260723_0036_care_cost_schema_parity.py`, `services/api/tests/test_care_cost_workflow.py`, `apps/dr_ai_app/lib/features/care_cost/`, `apps/dr_ai_app/lib/features/auth/`, `apps/dr_ai_app/lib/app/routing/`, `apps/dr_ai_app/test/care_cost_golden_test.dart`, `Dr_AI_Product_Requirements_Document_v1.0.md`, `docs/Dr_AI_v1.0_ERD.md`, `docs/Dr_AI_v1.0_API_Contract.md` | Define the governed China-first coverage/reference and expected-envelope slice before implementing any AI review score. |
| 2026-07-02 | Approved - Not Started | Approved implementation plan recorded as the project source of truth. | `docs/Dr_AI_v1.0_Implementation_Plan.md` | Begin Week 1 foundation and design-freeze tasks. |
| 2026-07-02 | In Progress - Week 1 | Implemented Week 1 Days 1-2 foundations: Flutter web/iOS/Android scaffold with role-aware routes and design tokens; FastAPI settings and health endpoint; environment templates; CI; design-freeze inventory and current prototype captures. Figma node metadata remains blocked by the Starter-plan MCP limit, so Week 1 is not complete. | `apps/dr_ai_app/`, `services/api/`, `.github/workflows/ci.yml`, `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/beta/Week_1_Days_1_2_Foundation_Record.md`, `docs/design-evidence/` | Reconcile exact Figma metadata when the quota resets, then begin Week 1 Days 3-4 authentication and data foundations. |
| 2026-07-03 | In Progress - Week 1 | Replaced device-mockup screenshots with direct 1x exports of the doctor and patient Figma frames. Confirmed the patient bottom navigation labels and preserved the Figma file by removing temporary export presets. | `docs/design-evidence/doctor-dashboard-618-1051.png`, `docs/design-evidence/patient-dashboard-663-398.png`, `docs/Dr_AI_v1.0_Design_Freeze.md` | Reconcile exact Figma hierarchy and token metadata after the monthly MCP quota resets. |
| 2026-07-04 | Complete - Week 1 Days 1-2 | Reconciled the design freeze from the authoritative manual Figma inspection; froze the planned v1 API contract; completed Android and iOS toolchains; added a reproducible Unicode-path verification workflow; removed the supported Starlette test-client warning; and verified Flutter web/Android/iOS plus both remote CI jobs. Week 1 remains open for Days 3-5. | `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/beta/Week_1_Days_1_2_Foundation_Record.md`, `scripts/verify_flutter.sh`, [draft PR #1](https://github.com/harryXiaoCao/Dr_AI_Product/pull/1), [green CI run](https://github.com/harryXiaoCao/Dr_AI_Product/actions/runs/28676795816) | Begin Week 1 Days 3-4 database, authentication, authorization, and responsive-shell work without expanding the approved scope. |
| 2026-07-05 | Complete - Week 1 | Closed the Tencent staging gate after implementing the PostgreSQL/Alembic data foundation, synthetic idempotent seed flow, Argon2 email/password auth, short-lived access tokens, rotating server-revocable refresh sessions, logout revocation, role and care-relationship authorization, neutral cross-patient failures, Flutter Riverpod/Dio/session restoration/logout, responsive doctor/patient dashboards, golden dashboard tests, and Tencent staging manifests. Local backend, Flutter, web, Android, iOS, API smoke, Android patient integration, GitHub Actions checks, Tencent HTTPS `/health`, TencentDB migration, idempotent seed, staging login, refresh rotation, logout revocation, and cross-patient authorization checks passed. | `services/api/`, `apps/dr_ai_app/`, `.github/workflows/ci.yml`, `deploy/tencent/staging/`, `docs/beta/Week_1_Days_3_5_Closure_Record.md`, [draft PR #2](https://github.com/harryXiaoCao/Dr_AI_Product/pull/2), staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Completed by Week 2 Days 6-7; see `docs/beta/Week_2_Days_6_7_Closure_Record.md`. |
| 2026-07-05 | Complete - Week 2 Days 6-7 | Implemented the read-only patient-care slice: PostgreSQL/Alembic models for medical records, medications, and doctor notes; synthetic idempotent seed fixtures; doctor patient search/list and patient profile/care bundle reads; patient own-care and medication reads; neutral cross-patient and wrong-role denials; Flutter doctor Patient Management surface; patient-side profile/history/medication display; and loading, empty, validation, unauthorized, and network-error states. Verified backend lint, targeted backend tests, Alembic drift check, Flutter analyze/widget/golden tests, and whitespace. | `services/api/app/dashboard.py`, `services/api/app/models.py`, `services/api/migrations/versions/20260705_0002_week2_patient_care_loop.py`, `services/api/tests/test_patient_care_loop.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/`, `docs/beta/Week_2_Days_6_7_Closure_Record.md` | Begin Week 2 Days 8-9 only: presigned demo-image upload, assessment form, deterministic simulated assessment service, risk-result screen, simulation label/limitations, and audit events. |
| 2026-07-05 | Complete - Week 2 Days 8-9 | Implemented demo-only upload presign metadata, patient-owned demo asset records, deterministic fixture-based simulated assessments, assessment history reads, audit metadata events, and the doctor Patient Management upload/assessment/result workflow with persistent simulation and synthetic-data labels. Kept the work synthetic, non-clinical, and doctor-led; no DeepSeek, recovery plans, reminders, consultations, real COS upload completion, real model, or real patient data were added. Verified backend lint, targeted backend tests, Alembic upgrade/drift check, Flutter analyze/widget/golden tests, and whitespace. | `services/api/app/dashboard.py`, `services/api/app/models.py`, `services/api/migrations/versions/20260705_0003_week2_upload_assessment_audit.py`, `services/api/tests/test_week2_upload_assessment.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/`, `docs/beta/Week_2_Days_8_9_Closure_Record.md` | Run the Day 10 gate only: complete patient -> record -> upload -> assessment -> result review, verify cross-patient denial, and confirm failure recovery without expanding into Week 3. |
| 2026-07-05 | Complete - Week 2 Day 10 polish gate | Sharpened demo upload presign validation with `415 unsupported_media_type`, `413 payload_too_large`, filename/content-type mismatch checks, and neutral cross-patient denial coverage. Added Flutter widget tests proving upload and assessment failures preserve form state and recover on retry. Updated the API README, API contract, implementation plan, and closure records without starting Week 3 scope. Verified backend focused tests, backend Ruff, full backend tests, Alembic drift check, Flutter analyze/widget/golden tests, and whitespace. | `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/tests/test_week2_upload_assessment.py`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `services/api/README.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/beta/Week_2_Day_10_Polish_Closure_Record.md` | Begin Week 3 only when explicitly requested: recovery, reminders, chat, and consultation remain deferred. |
| 2026-07-05 | Complete - Week 3 Days 11-12 | Implemented the recovery-plan slice: PostgreSQL/Alembic recovery plan, task, and completion models; synthetic seed plan with medication, exercise, diet, and follow-up tasks; doctor create/edit/activate endpoints and Patient Management editor; patient Today tasks with completion tracking; demo-only local medication notification shell; audit metadata for plan mutations and task completions; and focused wrong-role/cross-patient tests. Kept DeepSeek chat, streaming UI, red-flag escalation, rate limiting, specialist consultation, real notifications, real COS upload completion, real model inference, and clinical workflows deferred. Verified backend Ruff, full backend tests, Alembic upgrade/check, Flutter analyze/widget/golden tests through `./scripts/verify_flutter.sh`, and whitespace. | `services/api/app/models.py`, `services/api/app/dashboard.py`, `services/api/migrations/versions/20260705_0004_week3_recovery_plans.py`, `services/api/tests/test_week3_recovery_plans.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/`, `docs/beta/Week_3_Days_11_12_Closure_Record.md` | Begin Days 13-14 only when explicitly requested: DeepSeek chat and specialist consultation remain deferred. |
| 2026-07-05 | Complete - Week 3 Days 13-14 | Implemented the chat and consultation slice: PostgreSQL/Alembic chat thread/message/rate-limit and consultation request models; server-side DeepSeek proxy using `deepseek-v4-flash` with local/test safe fallback; red-flag escalation before any LLM call; unsafe prompt, timeout, malformed, quota, and rate-limit fallback behavior; metadata-only chat escalation and consultation audit events; patient educational chat with streaming-style chunk reveal; and doctor/patient consultation request/status display. Kept all content synthetic and educational; no DeepSeek key reaches Flutter, no raw prompt/model output is stored, and no real clinical assessment, real COS upload completion, billing, appointments, video/voice consultation, analytics, staging deployment, or Week 4 hardening/release work was added. Verified backend Ruff, full backend tests, Alembic upgrade/check, Flutter analyze/widget/golden tests through `./scripts/verify_flutter.sh`, and whitespace. | `services/api/app/ai_chat.py`, `services/api/app/dashboard.py`, `services/api/app/models.py`, `services/api/migrations/versions/20260705_0005_week3_chat_consultation.py`, `services/api/tests/test_week3_chat_consultation.py`, `apps/dr_ai_app/lib/features/patient/`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `docs/beta/Week_3_Days_13_14_Closure_Record.md` | Run Day 15 gate only: verify the full doctor-led loop across doctor and patient accounts, chat isolation/safety, and read-only Figma resource cards without expanding into Week 4. |
| 2026-07-05 | Complete - Week 3 Day 15 gate | Moved the dirty Week 2/Week 3 working tree off `codex/week1-days3-5` onto the stacked branch `codex/week2-week3-care-loop` before Day 15 edits, preserving PR #1 and PR #2 unmerged and avoiding history rewrites. Closed the Week 3 gate with an API-level doctor-led loop test, expanded chat safety eval fixtures for red flags, prompt injection, medication-change requests, diagnosis requests, contact-info leakage, and normal educational questions, duplicate requested-consultation reuse, and small-screen Ask Dr. AI auto-scroll/dense-input polish. Kept JSON-first streaming-style chat; no true SSE, fine-tuning, staging deployment, real clinical workflow, or Week 4 hardening/release work was added. Verified backend Ruff, focused Week 3 tests, full backend tests, Alembic upgrade/check, Flutter analyze/widget/golden tests through `./scripts/verify_flutter.sh`, and whitespace. | `services/api/app/dashboard.py`, `services/api/tests/test_week3_chat_consultation.py`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `docs/beta/Week_3_Day_15_Gate_Closure_Record.md` | Begin Week 4 hardening and beta-release work only when explicitly requested. |
| 2026-07-06 | Complete - Week 4 Days 16-17 hardening | Completed the local hardening pass only: added deterministic Flutter focus traversal, contrast/text-scaling responsive QA coverage, trimmed request-string validation, unsafe consultation specialty/summary rejection, expanded log-hygiene tests across auth, refresh, upload, chat, and consultation attempts, and recorded local dependency/audit/backup-restore review evidence. Kept Tencent staging, production release, real COS upload completion, real clinical workflows, privacy/consent/deletion/feedback, analytics, packaging, and true SSE deferred. | `apps/dr_ai_app/lib/app/app.dart`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/tests/test_errors_and_logs.py`, `services/api/tests/test_week3_chat_consultation.py`, `docs/beta/Week_4_Days_16_17_Hardening_Closure_Record.md` | Begin Days 18-19 only when requested: physical-device/browser checks, beta packaging/deployment, privacy/consent/deletion/feedback/limitations, and release preparation remain deferred. |
| 2026-07-06 | Complete - Week 4 Days 18-20 local release prep | Prepared the local release gate without external action: added the Flutter Beta support privacy/consent/deletion/feedback/limitations surface from the login screen and `/beta-support`, release notes, device/browser and packaging checklist, clean-account demo plan, backup demo evidence plan, backup/restore rehearsal plan, tag plan, tester invite checklist, and monitoring checklist. Kept Tencent staging, TestFlight, Android closed testing, web deployment, tag creation, tester invites, monitoring/account changes, recording, real COS upload completion, real clinical workflows, analytics expansion, and true SSE approval-gated and untouched. | `apps/dr_ai_app/lib/features/beta/presentation/beta_support_screen.dart`, `apps/dr_ai_app/lib/features/auth/presentation/login_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `docs/beta/v1.0.0-beta.1_Release_Notes.md`, `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md`, `docs/beta/Week_4_Days_18_20_Release_Closure_Record.md` | Final acceptance remains approval-gated: verify or refresh staging, run approved physical-device/release builds, create/push `v1.0.0-beta.1`, invite testers, and monitor only after explicit authorization. |
| 2026-07-06 | Prepared - v1.0 beta deployment/publishing operations | Re-audited the release gate docs, API contract, READMEs, Tencent staging manifests, and API settings before external actions. Re-ran local readiness: backend Ruff passed; full backend tests passed with `48 passed`; Alembic upgrade/check passed with no model drift; `uv pip check` and `uv lock --check` passed; `./scripts/verify_flutter.sh` passed with analysis clean and `26` widget/golden tests; Flutter web release build passed using `/Users/Harry-Cao/development/flutter/bin/flutter build web --release` and produced `apps/dr_ai_app/build/web`; `git diff --check` passed. No Tencent staging, TestFlight, Android closed testing, production web deployment, tag, tester/account/monitoring, commit, push, PR, deletion, or screen-recording action was performed. | `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`, `deploy/tencent/staging/compose.yaml`, `deploy/tencent/staging/.env.example`, `deploy/tencent/staging/Caddyfile`, `services/api/app/config.py`, `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md` | Next approval-gated action: explicitly approve Tencent staging refresh/verification before any live staging command, deployment, smoke check, account action, or hosting change. |
| 2026-07-06 | Partially verified - Tencent staging public health | After explicit approval for Tencent staging refresh/verification, verified the documented temporary staging URL public health endpoint: `https://dr-ai.43.132.169.195.sslip.io/health` returned HTTP 200 with `status=ok`, `environment=staging`, and `database=ok`. Safe unauthenticated probes confirmed protected API routes return standardized `401 unauthenticated`. `/beta-support` returned API `404 not_found`, confirming the live staging origin remains API-only and does not yet serve the Flutter Beta support web route. No populated staging `.env`, smoke credentials, Docker CLI, Tencent CLI, SSH host details, or repo deployment automation were available locally, so migration/seed refresh, doctor/patient login, token rotation, logout, neutral cross-patient denial, golden care loop, patient Today/Ask Dr. AI/consultation status, and live Beta support web checks remain pending. | `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`, `deploy/tencent/staging/README.md`, `deploy/tencent/staging/Caddyfile` | Provide approved staging host access and smoke credentials, or perform the documented host-side Docker Compose migration/seed/service refresh manually, before credentialed staging smoke can be completed. |
| 2026-07-06 | Prepared - staging smoke runner | Added `scripts/run_staging_smoke.py`, a redaction-safe HTTPS smoke runner for the credentialed staging checklist. Verified safe missing-credential failure and Python syntax. SSH authentication to the documented likely target `ubuntu@43.132.169.195` failed with `Permission denied (publickey)` using the current SSH agent, so host-side migration/seed refresh and credentialed smoke still require manual SSH key/alias setup and smoke passwords. | `scripts/run_staging_smoke.py`, `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md`, `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md` | Manually add approved SSH access and load `DR_AI_STAGING_*` smoke credentials, then run the smoke runner and host-side Docker Compose refresh. |
| 2026-07-06 | Complete - Tencent staging API refresh and smoke | Used the approved `ccx2009.pem` key to access the Tencent CVM at `ubuntu@43.132.169.195`. The image digest in `Dr_AI_Credentials.xlsx` was rejected by Docker because it had no matching `linux/amd64/v3` manifest, so a sanitized API Docker context was built on the CVM and pushed to TCR as `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:99b401b86310b335d3045484a57a9f5c2415bb8170053cf80c5d084101a2d863`. Staging `.env` was backed up before image changes. Alembic upgraded from Week 1 through Week 3 migrations, seed ran twice with the second run idempotent, `docker compose up -d` recreated the API container on the new digest, `/health` returned staging/database ok, and the credentialed smoke runner passed health, doctor/patient login, refresh rotation, logout revocation, doctor assigned-patient search, neutral cross-patient denial, demo upload presign, simulated assessment, recovery-plan activation, patient Today/task completion, Ask Dr. AI, doctor consultation request, and patient consultation status readback. Redaction-safe API log keyword count for obvious token/password patterns was `0`. `/beta-support` still returned `404`, confirming staging remains API-only until a web hosting pass is approved. | `scripts/run_staging_smoke.py`, `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`, `docs/beta/v1.0.0-beta.1_Release_Notes.md`, `README.md` | Next approval-gated release actions: deploy doctor web/Beta support hosting, then proceed to TestFlight, Android closed testing, clean-account demo, release tag, tester invites, and monitoring setup only with explicit approval. |
| 2026-07-06 | Complete - Tencent staging same-origin web/API deployment | After explicit approval, built the Flutter web app for `https://dr-ai.43.132.169.195.sslip.io`, deployed it to `/home/ubuntu/dr-ai/staging/web`, backed up the previous remote web/Caddy/Compose files, mounted the web directory into Caddy, and updated Caddy so `/api/*` and `/health` reverse-proxy to `api:8000` while root and Flutter deep links serve static web files with `/index.html` fallback. Caddy config validation passed, Caddy restarted while the API container stayed running, `/health` still returned staging/database ok, root and `/beta-support` returned Flutter web instead of API `404`, unauthenticated `/api/v1/me` still returned the standardized `401` envelope, and the credentialed staging smoke passed health, login, refresh/logout, cross-patient denial, demo upload, simulated assessment, recovery-plan activation, patient Today/task completion, Ask Dr. AI, consultation readback, and Beta support web checks. In-app browser rendered the login page and Beta support page with clean console logs; authenticated browser canvas login was blocked by Browser runtime timeout, so authenticated behavior is covered by the smoke runner. | `deploy/tencent/staging/compose.yaml`, `deploy/tencent/staging/Caddyfile`, `apps/dr_ai_app/lib/main.dart`, `apps/dr_ai_app/lib/app/routing/router.dart`, `scripts/run_staging_smoke.py`, `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`, `docs/beta/v1.0.0-beta.1_Release_Notes.md`, `README.md` | Remaining approval-gated release actions: TestFlight, Android closed testing, production web/final domain, release tag, tester invites, monitoring/account settings, and screen recording. |
| 2026-07-07 | Complete - personal installable access prep | Prepared personal access paths without store/account actions: computer access should use the Tencent HTTPS Flutter web app as a browser-installed PWA/web app; PWA metadata was productized and served with `manifest.json` plus `flutter_service_worker.js`; the public `/beta-support` route is preserved through auth restoration; a staging Android debug APK was built at `apps/dr_ai_app/build/app/outputs/flutter-apk/app-debug.apk` and later rebuilt after the mark-only logo refresh with SHA-256 `c331b485fa3d04e2fb9030a5ba2ee5769919f6343dfbf10d5fcef4fe217c55aa`; and iOS signing inspection found bundle id `com.harrycao.drai.drAiApp`, automatic signing, and no checked-in `DEVELOPMENT_TEAM`. Final staging smoke passed from the CVM after the PWA refresh. | `apps/dr_ai_app/web/manifest.json`, `apps/dr_ai_app/web/index.html`, `apps/dr_ai_app/lib/app/app.dart`, `apps/dr_ai_app/lib/app/routing/router.dart`, `apps/dr_ai_app/android/app/src/main/AndroidManifest.xml`, `apps/dr_ai_app/ios/Runner/Info.plist`, `scripts/run_staging_smoke.py`, `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`, `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md`, `docs/beta/v1.0.0-beta.1_Release_Notes.md` | Approval-gated next actions remain TestFlight upload, Android closed-testing upload, production web/final domain, release tag, tester invites, monitoring/account settings, screen recording, and store/account changes. |
| 2026-07-07 | Complete - mark-only logo replacement | Replaced the placeholder medical icon and platform icon artwork with the selected mark-only Dr. AI logo extracted from `/Users/Harry-Cao/Downloads/Generated image 1.png`, excluding the `Dr. AI` wordmark from icon artwork. Updated Flutter in-app brand marks, web favicon/PWA icons, Android launcher icons, iOS app icons, dashboard golden baselines, the local web build, and the local Android debug APK. | `apps/dr_ai_app/assets/brand/dr_ai_mark.png`, `apps/dr_ai_app/lib/shared/widgets/brand_mark.dart`, `apps/dr_ai_app/lib/features/auth/presentation/login_screen.dart`, `apps/dr_ai_app/lib/shared/widgets/responsive_app_shell.dart`, `apps/dr_ai_app/web/favicon.png`, `apps/dr_ai_app/web/icons/`, `apps/dr_ai_app/android/app/src/main/res/mipmap-*/ic_launcher.png`, `apps/dr_ai_app/ios/Runner/Assets.xcassets/AppIcon.appiconset/`, `apps/dr_ai_app/test/goldens/` | Live Tencent staging web was not redeployed in this pass; deploy the rebuilt `apps/dr_ai_app/build/web` only after explicit approval. |
| 2026-07-07 | Advanced - non-Apple release closure | Removed the unsafe Android debug-signing fallback for release builds, added an ignored upload-key `key.properties` template, verified release app-bundle builds now fail clearly until a real local upload keystore is supplied, re-ran the redaction-safe Tencent staging smoke successfully, and captured non-secret public screenshots for the staging login and Beta support routes. Google Play upload, tester invites, monitoring account changes, and the `v1.0.0-beta.1` tag were not performed because the workspace lacks Play/monitoring/tester credentials and the current dirty working tree must be committed before a meaningful tag can include the beta state. | `apps/dr_ai_app/android/app/build.gradle.kts`, `apps/dr_ai_app/android/key.properties.example`, `docs/release-evidence/v1.0.0-beta.1/staging-login.png`, `docs/release-evidence/v1.0.0-beta.1/staging-beta-support.png`, `docs/beta/v1.0.0-beta.1_Non_Apple_Closure_Record.md`, `docs/beta/Week_4_Days_18_20_Release_Gate_Checklist.md`, `docs/beta/v1.0.0-beta.1_Release_Notes.md`, `README.md`, `apps/dr_ai_app/README.md` | To finish non-Apple store/release publication, provide or create a local Android upload keystore, provide Google Play Console/tester/monitoring access, commit the release state, then create and push `v1.0.0-beta.1`. |
| 2026-07-07 | Re-scoped - Production v1.0 planning | Re-scoped the project from v1.0 beta completion toward v1.0 production/commercial completion. The user clarified that PRD-listed systems and visible dashboard modules should remain in v1.0 development scope; the current beta foundation is not sufficient for production v1.0 because many dashboard items are still placeholders or partial workflows. The implementation plan now tracks production modules, role coverage, commercial readiness, safety/regulatory gates, and external account/store gates. | `docs/Dr_AI_v1.0_Implementation_Plan.md`, `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx` | Begin Phase 0: reconcile the PRD, current UI, API contract, and data model; inventory every visible dashboard card/button/route; and mark each as functional, partial, placeholder, or remove/disable. |
| 2026-07-07 | Complete - worktree cleanup and mainline organization | Documented the future worktree/branch-maintenance policy, preserved the completed beta foundation and release evidence, committed the dirty beta state, and moved `main` forward so production v1.0 work can branch from a clean mainline baseline. No new code behavior was edited during this cleanup pass. | `docs/Dr_AI_v1.0_Implementation_Plan.md`, `git status --short --branch`, `git diff --check` | Start Phase 0 production work from a fresh branch based on `main`; keep each future phase committed and documented before starting the next lane. |
| 2026-07-07 | In Progress - Phase 0 first surface audit slice | Completed the first production v1.0 Phase 0 documentation slice: read the PRD, implementation plan, API contract, design freeze, and beta closure records; inventoried current doctor and patient Flutter routes, nav labels, dashboard cards, buttons, and API-backed workflows; classified visible doctor/patient surfaces as functional, partial, placeholder, or remove/disable; mapped kept surfaces to PRD modules; identified stale beta-only assumptions; drafted the initial production API/data-model gap list; and updated kept-module acceptance criteria. No app code behavior, deployment, push, tag, PR, external account, or live infrastructure action was performed. | `docs/Phase_0_Production_v1_Surface_Audit.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, `apps/dr_ai_app/lib/app/routing/router.dart`, `apps/dr_ai_app/lib/shared/widgets/responsive_app_shell.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/doctor_dashboard_screen.dart`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `services/api/app/dashboard.py`, `services/api/app/models.py` | Superseded by the Phase 0 closure row below; Phase 1 remained unstarted. |
| 2026-07-07 | Complete - Phase 0 production scope closure | Closed Phase 0 documentation only: reconciled the API contract so beta guarantees remain preserved while production gaps are explicit; finalized kept, gated, removed/disabled, and not-v1.0 product-scope decisions; documented the combined public support route, authenticated in-role support route, and admin-managed backend queue shape; decided that specialist/admin Phase 5 can begin from written acceptance criteria unless new visual parity or complex workflow evidence is needed; and created the Phase 0 closure record. No code behavior, Phase 1 implementation, deployment, push, tag, PR, commit, staging, or external account action was performed. | `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Phase_0_Production_v1_Surface_Audit.md`, `docs/Phase_0_Production_v1_Closure_Record.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Phase 1 may begin only when explicitly requested: start with production data foundation, fail-closed role expansion, support/deletion/feedback models, admin/specialist RBAC, and authorization/audit tests. |
| 2026-07-07 | Complete - docs organization after Phase 0 closure | Organized historical beta markdown records under `docs/beta/`, added `docs/README.md` as the documentation index, updated root/app/API README stage summaries to production v1.0 Phase 0 complete and Phase 1 not started, refreshed the design-freeze status so it is clearly doctor/patient-only visual evidence, and updated references to the moved beta records. No app/API behavior, Phase 1 implementation, deployment, push, tag, PR, commit, staging, or external account action was performed. | `docs/README.md`, `docs/beta/`, `README.md`, `apps/dr_ai_app/README.md`, `services/api/README.md`, `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Phase 1 remains the next explicit production implementation phase; start only when requested. |
| 2026-07-07 | In Progress - Phase 1 first data-foundation slice | Started Phase 1 implementation with additive production foundation models and migration for hospitals, clinics, role assignments, doctor teams, clinic resources/equipment, appointments/bookings, prescriptions/medication reminders, notifications, invoices/payment statuses/revenue summaries, analytics events, and support/deletion/feedback queue requests. Reserved `specialist` and `admin` backend role values while keeping their registration and beta dashboard access fail-closed; fixed Flutter unknown/future role parsing so unsupported roles route to `/unauthorized` instead of doctor UI; and verified the synthetic seed flow leaves new production tables empty. No Phase 2 workflows, specialist/admin UI, deployment, push, tag, PR, commit, or external account action was performed. | `services/api/app/models.py`, `services/api/migrations/versions/20260707_0006_phase1_production_foundation.py`, `services/api/tests/test_phase1_production_foundation.py`, `apps/dr_ai_app/lib/app/routing/app_role.dart`, `apps/dr_ai_app/lib/app/routing/router.dart`, `docs/Phase_1_Production_Data_Foundation_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md` | Continue Phase 1 only: expand route-level RBAC/audit coverage, decide minimal support/deletion/feedback submission semantics, and keep production fixtures separate from demo seed data before any Phase 2 workflow starts. |
| 2026-07-07 | Complete - Phase 1 production data foundation | Finished the remaining Phase 1 foundation slice without starting Phase 2/4/5 workflows: added route-level RBAC helpers, registered authenticated `/api/v1/support-requests` submission and requester-scoped status endpoints, kept specialist/admin support access fail-closed, persisted support/deletion/feedback queue rows with redacted body storage and audit metadata, added support request create/list/status audit events, and expanded tests for future-role denial, wrong-requester isolation, unsafe-content rejection, seed/demo separation, and no-side-effect admin/specialist probes. No patient/doctor CRUD workflow, clinic-operation workflow, specialist/admin UI, admin queue handling, deployment, push, tag, PR, commit, or external account action was performed. | `services/api/app/support.py`, `services/api/app/rbac.py`, `services/api/app/main.py`, `services/api/app/schemas.py`, `services/api/tests/test_phase1_production_foundation.py`, `docs/Phase_1_Production_Data_Foundation_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Phase 2 patient/doctor core workflows remain next and must be explicitly requested. Phase 5 still owns specialist/admin UI, audit search, system status, and admin-managed support queue handling. |
| 2026-07-07 | Complete - Tencent staging redeploy for Phase 1 foundation | After explicit approval, redeployed Tencent same-origin staging so live web/API matches the completed Phase 1 foundation. Built and pushed a sanitized API image on the CVM, deployed immutable digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:d10187ae5178b089581a05b603f77c32ece079341bef7b3a93d8f79c3035af93`, applied Alembic migration `20260707_0006`, confirmed two idempotent synthetic seed runs, rebuilt and installed the Flutter web bundle for `https://dr-ai.43.132.169.195.sslip.io`, validated/recreated Caddy, and verified public health/web routes plus credentialed staging smoke. The new Phase 1 support endpoints passed create/list/status, cross-requester `404`, and unsafe-content `422` staging probes. No production deployment, tester/account/monitoring change, native store upload, tag, push, PR, real patient data, or clinical workflow was performed. | `docs/Phase_1_Production_Data_Foundation_Record.md`, `deploy/tencent/staging/README.md`, `scripts/run_staging_smoke.py`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Staging is current for Phase 1. Begin Phase 2 only when explicitly requested; keep Phase 5 admin support queue handling and specialist/admin UI deferred. |
| 2026-07-07 | Complete - Phase 2 medication core slice | Implemented the next Phase 2 patient/doctor core slice locally: doctor-owned medication CRUD, prescription CRUD with medication lines, medication reminders, refill reminders, metadata-only in-app queued notification records for active reminders, expanded care-bundle readback, patient own reminder/notification reads, doctor Patient Management medication workflow controls, patient prescription/reminder readback, neutral wrong-role/cross-patient denials, and metadata-only audit/notification assertions. No migration was required because Phase 1 already added prescription, prescription medication, medication reminder, and notification tables. No Phase 3 AI workflow, Phase 4 clinic operations, Phase 5 specialist/admin UI, deployment, push, tag, PR, external notification service, real patient data, or clinical claim was added. | `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/app/models.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/`, `apps/dr_ai_app/test/app_test.dart`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md` | Continue Phase 2 only: Tencent COS upload finalization, imaging list/detail/review workflow, production recovery-plan draft/review/approve depth, patient Today production tracking depth, and remaining core workflow tests remain. |
| 2026-07-08 | Complete - Phase 2 patient/doctor core closure | Closed Phase 2 locally after the existing medical-history, medication, and imaging slices by adding production recovery-plan review metadata, migration `20260708_0009`, doctor-only submit-review/request-changes/approve/activate-compatible/complete transitions, patient Today progress summaries, Flutter doctor review controls, Flutter patient Today progress readback, updated patient dashboard golden evidence, expanded API/docs, and focused RBAC/audit tests. External push/SMS/email/native notification delivery remains gated beyond Phase 2 because it requires credentials, account/service changes, and platform configuration; the Phase 2 safe path remains metadata-only in-app notification records. No Phase 3 AI inference, Phase 4 clinic operations, Phase 5 specialist/admin UI, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `services/api/migrations/versions/20260708_0009_phase2_recovery_plan_review.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/goldens/patient_dashboard_412x917.png`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/README.md`, `README.md` | Superseded by the 2026-07-09 product-quality reset: Phase 2.5 Product Quality and First-Use Readiness must close before Phase 3 AI starts. |
| 2026-07-08 | Complete - Phase 2 Tencent staging redeploy prep | Cleaned up the Phase 2 worktree with local commit `8e9d344`, redeployed Tencent same-origin staging to the completed Phase 2 API/web state, applied staging migrations through `20260708_0009`, confirmed idempotent synthetic seed runs, deployed immutable API digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:a1d55dd905acdd2113ed2dac163aaa7f0d1fc1a37ec4a0d2855b7e65e4250381`, refreshed the mounted web directory in place, recreated API/Caddy, validated Caddy, and passed credentialed staging smoke plus public route checks. Android debug APK rebuild is still blocked until `/Volumes/AndroidAVD/sdk` is mounted; the existing July 7 APK is stale for Phase 2. iPhone native install still requires Apple development-team signing setup. | `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `deploy/tencent/staging/README.md`, `scripts/run_staging_smoke.py`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | User inspection can start from the staging web/PWA. Rebuild the Android debug APK after the Android SDK mount is restored; use direct Xcode install or TestFlight only after Apple signing/account prerequisites are ready. |
| 2026-07-08 | Planned - post-Phase-2 UX and multilingual hardening | Documented the future doctor Patient Management workspace reorganization and production multilingual foundation. The doctor workspace should move from a crowded single page to assigned-patient navigation, selected-patient summary, and focused subsections for overview, history, visits/diagnoses, medications, prescriptions, reminders, recovery plans, imaging, doctor notes, and activity. The localization foundation should support Simplified Chinese and English through Flutter localization, keep backend responses machine-readable, preserve user-entered clinical content without automatic translation, and use locale-aware formatting. No code behavior, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `docs/Dr_AI_v1.0_Implementation_Plan.md`, `docs/README.md` | The next doctor-workspace cleanup should be a focused frontend architecture slice that follows the documented Phase 6 UX hardening plan and avoids starting Phase 3 AI, Phase 4 clinic operations, Phase 5 specialist/admin UI, or multilingual implementation unless explicitly requested. |
| 2026-07-08 | Complete - post-Phase-2 doctor workspace layout cleanup | Refactored the Flutter doctor Patient Management surface into a focused patient workspace: assigned-patient search/list remains a narrow left column on desktop/tablet, phone-width layouts use a compact patient-picker sheet, the detail pane has an identity-safe selected-patient summary header, and doctor work is split into Overview, Medical history, Visits and diagnoses, Medications, Prescriptions, Reminders, Recovery plan, Imaging, Doctor notes, and Notifications/activity subsections. Medication, prescription, reminder, recovery-plan, imaging, doctor-note, and activity controls now live in their focused subsections instead of competing in one long mixed page. Backend/API/RBAC/audit behavior, schemas, migrations, real patient data boundaries, clinical-claim boundaries, deployment, push, tag, PR, and external account state were unchanged. The multilingual/localization foundation remains future Phase 6 work and was not implemented in this slice. `./scripts/verify_flutter.sh` passed with analysis clean and all Flutter widget/golden tests passing; `git diff --check` passed. | `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Keep production multilingual/localization foundation as a separate approved Phase 6 slice. |
| 2026-07-08 | Complete - Tencent staging web redeploy for doctor workspace cleanup | After explicit approval, rebuilt Flutter web for `https://dr-ai.43.132.169.195.sslip.io`, backed up the existing Tencent host `web/` directory as `web.backup.20260708T134138`, synced the new `apps/dr_ai_app/build/web` bundle into the mounted staging `web/` directory in place, force-recreated Caddy so the bind mount sees the fresh files, and validated the Caddy config. Public checks passed for `/health` with staging/database ok, root web, `/beta-support`, unauthenticated `/api/v1/me` returning `401`, and deployed asset hashes matching the local web build. The API image/container, database, migrations, seed data, RBAC, audit behavior, production environment, tester/account settings, native store uploads, commits, pushes, tags, and pull requests were unchanged. Credentialed staging smoke was not run because `DR_AI_STAGING_*` smoke credentials were not loaded in this shell. | `apps/dr_ai_app/build/web`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | User can inspect the updated doctor Patient Management workspace on staging; hard refresh or clear PWA/browser site data if an installed app keeps an older service-worker cache. |
| 2026-07-08 | Planned - Phase 2 clinical-event workflow clarification | Documented the next Phase 2 product-logic clarification under the Phase 2 milestone: Patient Profile is patient-edited and doctor-reviewed only; Medical History is patient-entered with doctor verification/amendment; "Visits and diagnoses" should become Clinical Events/Care Episodes; prescriptions generate medication schedules and patient Today tasks; standalone doctor Reminders should be removed; Recovery Plans and Imaging should link to Clinical Events; and Doctor Notes plus activity should become Consultation & Activity. This was documentation only. No code behavior, backend schema, API contract, migration, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `docs/Dr_AI_v1.0_Implementation_Plan.md` | Next approved implementation should be a carefully scoped Phase 2 workflow-clarification slice centered on Clinical Events/Care Episodes. Aesthetic and practical quality are more important than completing every listed task quickly. |
| 2026-07-08 | Complete - Phase 2 Clinical Event UI clarification slice | Implemented the first Phase 2 workflow-clarification slice locally in the Flutter doctor Patient Management workspace. The doctor navigation now uses Overview, Profile, Medical History, Clinical Events, Medications & Prescriptions, Recovery Plans, Imaging, and Consultation & Activity; the Clinical Events view groups existing visit-history and diagnosis records around the active care-episode concept; medication, prescription, generated reminder, recovery, imaging, note, specialist consultation, and activity surfaces are visually linked back to the selected Clinical Event. The standalone doctor Reminders workspace section and manual reminder editor were removed from the doctor UI. Backend/API/schema/RBAC/audit behavior, migrations, deployment, push, tag, PR, external account state, real patient data, and clinical-claim boundaries were unchanged. | `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, `docs/README.md` | Continue Phase 2 workflow clarification only when approved: add a persisted Clinical Event/Care Episode model and explicit event links for prescriptions, medication schedules, recovery plans, imaging, notes, consultation, and activity as an additive backend/API migration with focused RBAC/audit tests. |
| 2026-07-08 | Complete - Phase 2 Clinical Event backend/API slice | Implemented the deeper additive Phase 2 workflow-clarification backend/API slice locally: added migration `20260708_0010` with persisted `clinical_events`; added nullable `clinical_event_id` links for visit history, diagnoses, medications, prescriptions, medication/refill reminders, metadata-only notifications, recovery plans, imaging assets, doctor notes, and consultation requests; added doctor-only Clinical Event create/update endpoints plus doctor/patient reads and patient-owned aliases; expanded care-bundle readback with `clinical_events`, linked-resource counts, `recovery_plans`, and nullable event IDs; and extended Flutter care-bundle domain models to parse event-linked resources without changing the current UI layout. Focused tests cover doctor create/update, patient read/no-mutate, cross-patient/wrong-role neutral denial, event-linked resource readback, generated notification linkage, and metadata-only audit redaction. No Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, Phase 6 localization, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `services/api/migrations/versions/20260708_0010_phase2_clinical_events.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/README.md` | Continue Phase 2 workflow clarification only when approved: decide the next doctor/patient UI step for actively creating/selecting Clinical Events, event-filtered editing, and patient-submitted updates. Keep Phase 3 AI, Phase 4 clinic operations, Phase 5 specialist/admin UI, and Phase 6 localization separate. |
| 2026-07-08 | Complete - Phase 2 Clinical Event workflow polish slice | Continued the Phase 2 workflow clarification locally by adding derived Clinical Event timeline entries to event/care-bundle readback, adding doctor-entered manual imaging finding/result fields through the existing doctor-only imaging review flow, adding migration `20260708_0011`, and tightening recovery-plan activation so approving a replacement completes active plans only inside the same Clinical Event while the doctor UI clearly surfaces the active-plan-per-event state. Flutter doctor Patient Management now displays event timeline rows and manual imaging findings inside the selected Clinical Event context. Focused backend coverage validates timeline readback, manual finding/result audit redaction, and event-scoped recovery-plan replacement. No Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, Phase 6 localization, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `services/api/migrations/versions/20260708_0011_phase2_imaging_manual_findings.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`, `apps/dr_ai_app/lib/features/patient/application/patient_care_providers.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/test/fakes.dart`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/README.md` | Remaining Phase 2 workflow clarification: audited doctor verification/amendment for patient-entered Medical History and patient-submitted Clinical Event updates that preserve doctor-owned diagnosis controls. |
| 2026-07-08 | Complete - Phase 2 workflow clarification closure | Finished the remaining Phase 2 workflow-clarification items locally by adding migration `20260708_0012` with `medical_history_reviews` and `clinical_event_updates`; adding doctor-only audited medical-history verification, correction-request, and amendment overlays that preserve the patient-entered source history; adding patient-owned Clinical Event update submission/readback that appears in event responses and the derived timeline without mutating doctor-owned diagnosis summaries; and wiring Flutter doctor Patient Management and the patient dashboard to those workflows. Focused backend and Flutter tests cover doctor-only history review, patient-only own event updates, cross-patient/wrong-role neutral denial, care-bundle readback, timeline readback, diagnosis preservation, and metadata-only audit redaction. No Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, Phase 6 localization, deployment, push, tag, PR, external account action, real patient data, or clinical claim was added. | `services/api/migrations/versions/20260708_0012_phase2_history_reviews_event_updates.py`, `services/api/app/models.py`, `services/api/app/schemas.py`, `services/api/app/dashboard.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`, `apps/dr_ai_app/lib/features/patient/application/patient_care_providers.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/README.md` | Phase 2 workflow clarification is complete locally against the eight-functionality list. Next production work should remain gated by the implementation plan: Phase 3 AI systems only with explicit approval, while Phase 4 clinic operations, Phase 5 specialist/admin UI, and Phase 6 localization remain separate. |
| 2026-07-08 | Complete - Phase 2 workflow clarification GitHub/staging handoff | Committed the Phase 2 workflow-clarification closure as `33d70e5` and pushed branch `codex/phase-2-patient-doctor-core` to GitHub, then redeployed Tencent same-origin staging for user inspection. The staging API now runs immutable digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:25532802291eae937b06266288047436646a72524d119965714879b2e44e42d7`; Alembic applied `20260708_0010`, `20260708_0011`, and `20260708_0012`; synthetic seed remained idempotent; Flutter web was rebuilt for `https://dr-ai.43.132.169.195.sslip.io`; Caddy was validated/recreated; public health/web checks passed; the credentialed staging smoke passed; and a focused live smoke passed for doctor medical-history review overlays, doctor Clinical Event creation, patient Clinical Event updates, and diagnosis-preserving event timeline readback. No production deployment, tester/account/monitoring change, native store upload, tag, PR, real patient data, Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, or Phase 6 localization was performed. | `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | User inspection can continue on staging before deciding whether any Phase 2 polish is needed. Phase 3 AI systems remains approval-gated and should not start until Phase 2 inspection is accepted. |
| 2026-07-08 | Complete - Phase 2 manual-testing onboarding cleanup | Completed the pre-Phase-3 cleanup requested after staging inspection: exposed invited sign-up in Flutter, added a doctor patient-code connection flow, added a fresh-patient onboarding state that shows the patient code when no seeded dashboard exists, and added from-zero API/widget tests so manual testing no longer depends on the seeded Riley/Avery demo relationship. Seed data remains available only as optional staging smoke/regression scaffolding; the intended manual path is now register patient, register doctor, connect by patient code, then create care records from zero. Focused backend tests, ruff, Flutter verification, and whitespace checks pass locally. No Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, Phase 6 localization, deployment, push, tag, PR, external account action, real patient data, clinical claim, or destructive staging data reset was performed in this local slice. | `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/tests/helpers.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/auth/`, `apps/dr_ai_app/lib/features/patient/`, `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/fakes.dart`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, `docs/README.md` | Decide whether to commit/push/deploy this cleanup. Any wipe/archive of existing synthetic staging records should be a separately confirmed staging-only operation. |
| 2026-07-08 | Complete - Phase 2 onboarding cleanup GitHub/staging handoff | Committed the manual-testing onboarding cleanup as `b14f10d` and pushed branch `codex/phase-2-patient-doctor-core` to GitHub, then redeployed Tencent same-origin staging for user inspection. The staging API now runs immutable digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:719bbef7331e4e1616e881a20f8b60367d468a02778c64922999da03e12464d9`; Alembic `upgrade head` completed with no new migration; Flutter web was rebuilt for `https://dr-ai.43.132.169.195.sslip.io`; Caddy was validated/recreated; public health/web checks passed; and a focused live onboarding smoke passed for invited patient/doctor registration, fresh patient-code readback, doctor patient-code connection, and Clinical Event creation after connection. Synthetic seed was not rerun, staging data was not wiped, and `main` was not changed. No production deployment, tester/account/monitoring change, native store upload, tag, PR, real patient data, Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, or Phase 6 localization was performed. | `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | User inspection can use invited sign-up and patient-code connection on staging. Any destructive cleanup of old synthetic staging records remains a separate confirmation gate. |
| 2026-07-09 | Complete - Product quality gate documentation reset | Documented the post-inspection product-quality reset: Phase 2 remains a useful technical workflow foundation, but the visible app is not yet a commercial-quality healthcare product. Added `Dr_AI_v1.0_Product_Quality_Gate.md`, made Phase 2.5 Product Quality and First-Use Readiness the next milestone before Phase 3, updated the docs indexes, downgraded the old design freeze to historical beta evidence, and recorded the need for real-app typography, patient avatar/profile setup, guided onboarding, meaningful empty states, and removal of normal-flow synthetic/demo language. No code behavior, deployment, push, tag, PR, external account action, real patient data, Phase 3 AI generation, Phase 4 clinic operations, Phase 5 specialist/admin UI, or Phase 6 localization was added. | `docs/Dr_AI_v1.0_Product_Quality_Gate.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, `docs/README.md`, `README.md`, `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md` | Next implementation should close Phase 2.5 through screenshot-backed product UX work before any AI feature development starts. |
| 2026-07-10 | Complete - Phase 2.5 patient contact and authentication refinement slice | Added a read-only patient contact API backed by active care relationships so multiple connected doctors appear automatically; added a mobile-first Contacts destination with System, deferred Dr. AI, individual doctors, and deferred group-chat states; rebuilt the medical-fee placeholder into a spacious, accessible, non-clickable summary; separated sign-in and registration into `/login` and `/register`; limited authentication feedback to about two seconds and cleared it when changing auth pages; and changed Terms/Privacy return navigation to registration. Messaging, group creation, payment processing, and Phase 3 AI remain deferred. Focused multi-doctor API coverage, backend Ruff, the complete Flutter verification gate, mobile/enlarged-text layout checks, and local browser QA at `412x917` and `1280x832` passed. No deployment, push, tag, PR, production data, external account action, Phase 3/4/5/6 work, or real clinical behavior was performed. | `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/tests/test_phase2_patient_doctor_core.py`, `apps/dr_ai_app/lib/features/patient/presentation/patient_contacts_screen.dart`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `apps/dr_ai_app/lib/features/auth/`, `apps/dr_ai_app/lib/app/routing/router.dart`, `apps/dr_ai_app/lib/shared/widgets/responsive_app_shell.dart`, `apps/dr_ai_app/test/app_test.dart` | Continue the remaining Phase 2.5 screenshot-backed product-quality gate only; keep real messaging, payment processing, and Phase 3 AI approval-gated. |
| 2026-07-10 | Complete - Simplified Chinese full-surface UI localization | Completed the shared English/Simplified Chinese UI path across authentication, patient and doctor dashboards and Account pages, Patient Management, care details, Contacts, Recovery Plans, public support/legal content, dialogs, validation, empty states, notifications, semantics, and stable status/error display. Chinese/English device-locale selection uses English fallback, both roles can switch language immediately, and the preference is securely persisted. Stable API/profile values and user-entered clinical content remain unchanged; structured geographic labels are localized only for display. Production clinical forms no longer prefill synthetic workflow values, and validation used isolated widget-test fixtures without writing production-facing records. Flutter localization generation and static UI-string review were completed; `./scripts/verify_flutter.sh` and `git diff --check` are the completion gates. No deployment, push, tag, PR, external account action, API/schema change, or real patient data change was performed. | `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/l10n.yaml`, `apps/dr_ai_app/lib/app/app.dart`, `apps/dr_ai_app/lib/features/auth/presentation/login_screen.dart`, `apps/dr_ai_app/lib/features/patient/presentation/`, `apps/dr_ai_app/lib/features/doctor/presentation/`, `apps/dr_ai_app/lib/shared/widgets/`, `apps/dr_ai_app/test/app_test.dart` | User performs the planned Chinese copy review and reports wording preferences; future UI copy must be added to both ARB catalogs in the same change. |
| 2026-07-10 | Complete - production refinement mainline and Tencent staging redeploy | Committed the production localization, account, contact, security, profile, last-activity, typography, transition, and UI refinements on `main` as `6019b77` and pushed `main` to GitHub. The release gate passed backend Ruff, the full backend test suite, Alembic upgrade/check, dependency/lock checks, Flutter analysis and 44 active widget tests, a staging-configured Flutter web release build, a no-codesign iOS device build, and whitespace checks. Backed up the host-only staging environment and mounted web directory as timestamp `20260710T142535Z`; built and pushed immutable API digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:99c853635a43b9063392c648a0e37efaa9eaf0ff69b092c4343ddbd0f7b97779`; applied migrations `20260710_0015` through `20260710_0018`; and confirmed both seed passes created zero records. Rebuilt Flutter web for the same-origin Tencent URL, deployed matching Inter and Noto Sans SC assets, validated and recreated Caddy, and verified matching local/remote/public hashes. Public health, root, privacy deep link, and unauthenticated API checks passed; the credentialed smoke suite passed authentication, token rotation/logout, care-relationship isolation, assessment, recovery plan, Today tasks, educational chat, and consultation flows; the live database is at Alembic head `20260710_0018`; and recent API/Caddy logs contained no matching error indicators. No production environment, app-store upload, tester/account setting, tag, destructive data reset, or real patient data action was performed. | `services/api/`, `apps/dr_ai_app/`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, `deploy/tencent/staging/`, `scripts/run_staging_smoke.py`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Staging is current for this refinement round. Native iPhone installation remains a user-controlled Xcode signing action using the verified Flutter iOS project. |
| 2026-07-11 | Complete locally - pre-Phase 3 contacts and private messaging | Added mutual active-relationship contact lists for doctors and patients, text-only private conversation persistence and role-aware authorization, clickable System and Dr. AI destinations for both roles, a shared AI placeholder interface, read-only System chat, and explicit empty group-chat states. Migration `20260711_0019` adds private-thread participant/type fields and private-message content. Focused API coverage proves bidirectional delivery and neutral denial for unconnected patients; Flutter widget regression coverage remains green. No group creation, system-message sending, Phase 3 model expansion, deployment, push, or external action was performed. | `services/api/app/models.py`, `services/api/app/dashboard.py`, `services/api/app/schemas.py`, `services/api/migrations/versions/20260711_0019_private_messaging.py`, `services/api/tests/test_private_messaging.py`, `apps/dr_ai_app/lib/features/chat/`, `apps/dr_ai_app/lib/features/doctor/presentation/doctor_contacts_screen.dart`, `apps/dr_ai_app/lib/features/patient/presentation/patient_contacts_screen.dart` | Finish the remaining product-quality gate review before officially starting Phase 3. |
| 2026-07-13 | Complete - Phase 3 RAG, bounded-agent, doctor Resources, and knowledge-base planning baseline | Reconciled the user-confirmed move into chatbot development with the PRD and documentation index; froze a dedicated `/doctor/resources` product specification that moves medical evidence search out of the global header; designed a server-controlled finite-state agent flow around `deepseek-v4-flash`; defined hybrid Chinese/English retrieval, evidence/citation/safety gates, fixed fallbacks, metadata-only observability, source/rights/version/review/index schemas, separate doctor/patient retrieval views, and a small independent retrieval/reranking adapter recommendation. This was planning and source-of-truth documentation only: no Flutter route, backend API/schema, corpus ingestion, model call, deployment, external action, real patient data, or clinical claim was added. | `Dr_AI_Product_Requirements_Document_v1.0.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, `docs/README.md` | Implement Slice 1 governance/contracts first, then the fixture-backed doctor Resources shell; do not scale ingestion or connect patient RAG until source-specific rights and medical review pass. |
| 2026-07-13 | Complete - private messaging, Phase 3 architecture mainline, and Tencent staging redeploy | Committed the accumulated safe product, private-messaging, branding, and Phase 3 architecture/documentation changes on `main` as `7eb9b41` and pushed `main` to GitHub. The release gate passed backend Ruff, all `77` backend tests, lock/dependency checks, Alembic upgrade/drift checks, Flutter analysis and all active tests, a staging-configured web release build, a no-codesign iOS device build, PDF source/render inspection, and whitespace checks. The unsafe local `chatbot-evaluation.zip` archive was deliberately excluded because it contains sealed evaluation materials and remains untracked. Backed up Tencent staging `.env` and web assets as `20260713T082341Z`; built and published immutable backend digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:40741589b537c5873dfe58482a821ca535df3fad84f28b692f355eb6f1819ee8`; applied migration `20260711_0019`; confirmed two seed passes created zero records; deployed matching Flutter web artifacts; validated/recreated Caddy; and verified local/remote hashes. Public health, root, privacy, and unauthenticated API checks passed. The corrected credentialed smoke suite passed authentication/session rotation, care isolation, assessment, recovery, Today, educational chat, consultation, connected private messaging, unconnected-patient denial, and the privacy deep link. The database is at Alembic head `20260711_0019`, both services are running, timestamped backups exist, and recent API/Caddy logs contained no matching critical error indicators. This refreshed the existing Tencent staging environment only; no production environment, app-store release, tester/account change, tag, destructive data reset, or real patient data action was performed. | `services/api/`, `apps/dr_ai_app/`, `scripts/run_staging_smoke.py`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.pdf`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Tencent staging is current at commit `7eb9b41`; begin Phase 3 Slice 1 governance/contracts without bypassing source-rights or clinical-review gates. |
| 2026-07-15 | Complete - Phase 3 Slice 4 retrieval baseline mainline and Tencent staging redeploy | Cleaned `services/api/` by deleting only the proven redundant 55-row generation checkpoint JSONL files and ignored caches while preserving the manually reviewed translation/summary JSON artifacts required by import and regression tests. Completed the governed 353-source knowledge catalog, 55 open-content documents, approved Simplified Chinese translations, approved bilingual summaries, summary-aware doctor Resources search, doctor Resources UI/reader, and Alembic metadata reconciliation through `20260715_0026`. The release gate passed backend Ruff, all `106` backend tests, Alembic upgrade/check with no new operations, lock/dependency checks, Flutter analysis and `55` active widget tests, the staging-configured web release build, and whitespace checks. Committed the release as `0574b1b` on `main` and pushed it to GitHub. Backed up Tencent staging database, host-only environment, and web bundle at `backups/20260715T145939Z`; built and published immutable `linux/amd64` API digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:f48cc3c6b7a31d156d4afa83cc25c9159c9eaefc4947da7355909203df19ee9b`; migrated staging from `0019` through `0026`; confirmed two zero-change seed passes; imported 353 sources, 55 approved translations, and 55 approved bilingual summaries; and deployed the matching Flutter web bundle. Staging Alembic check reports no new upgrade operations, exact database counts are `353` sources, `55` approved translations, and `55` approved summaries, public root/health/privacy-support checks return `200`, unauthenticated `/api/v1/me` returns `401`, both containers are running, and recent API/Caddy logs contain no error indicators. The credentialed smoke suite passed all existing role/auth/care/chat/workflow checks plus a summary-only doctor Resources search for the high-blood-pressure source. This refreshed the existing Tencent staging environment only; no production environment, app-store release, account change, destructive data reset, or real patient data action was performed. | `services/api/`, `apps/dr_ai_app/`, `scripts/run_staging_smoke.py`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Slice 4 staging is current. Continue the next explicitly approved Phase 3 slice without bypassing rights, review, retrieval, citation, or safety gates. |
| 2026-07-15 | Complete - Tencent blank-first-render correction | Reproduced the reported blank/incomplete Flutter web render in the user's Chrome tab after a cache-bypassing reload. The page eventually rendered and emitted no console errors, while local, Tencent-hosted, and public release assets matched; the cold-start bootstrap was still resolving CanvasKit from Google's CDN and could leave users in China without a visible surface during renderer startup. Rebuilt the same staging release with `--no-web-resources-cdn`, verified `useLocalCanvasKit=true`, added a static accessible Dr. AI loading surface that remains until Flutter's first frame, backed up the pre-fix web bundle at `backups/20260715T152421Z`, synchronized the corrected bundle in place, and force-recreated Caddy without restarting the API. Chrome cache-bypass and fresh-tab checks now render the doctor dashboard without console warnings/errors, public `/health` remains staging/database ok, and both Tencent containers remain running. | `apps/dr_ai_app/web/index.html`, `deploy/tencent/staging/README.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Keep Tencent web builds self-contained with `--no-web-resources-cdn`; the loading surface prevents future cold engine starts from appearing blank. |
| 2026-07-15 | Complete - TencentDB patient-profile save diagnosis and correction | Reproduced the patient-profile save failure in the user's Chrome session and correlated it with the deployed API logs. TencentDB was healthy and correctly enforcing the unique account-email constraint; the API defect was a lazy relationship access that triggered SQLAlchemy autoflush before the existing duplicate-email `IntegrityError` handler, turning the intended conflict into an unhandled server error. Captured the patient audit identifier before mutation, added a preflight duplicate lookup plus race-safe `409 email_already_in_use` handling, and replaced the misleading network message with specific English and Simplified Chinese guidance. Added backend and Flutter regressions plus live staging smoke coverage for a no-op profile database write and non-mutating duplicate-email conflict. All `107` backend tests, Alembic check, Flutter analysis, and `56` active widget tests passed. Backed up Tencent database/environment/web as `backups/20260715T154253Z`, deployed immutable API digest `hkccr.ccs.tencentyun.com/dr-ai/dr-ai-backend@sha256:521706f20f22bbfc0ba94cd36abf2062c6b350f746eb872b4ad91acc08fd9607` and the matching bilingual web build, and passed the complete credentialed staging smoke. Final TencentDB checks confirm a connected read-write primary at migration `0026`, no pending Alembic operations, zero recent matching API/Caddy errors, and both containers running. | `services/api/app/auth.py`, `services/api/tests/test_auth.py`, `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `scripts/run_staging_smoke.py`, staging URL: <https://dr-ai.43.132.169.195.sslip.io> | Patient profile edits now save when the optional email is empty or unique; an email already bound to another account remains rejected safely with actionable bilingual guidance. |
| 2026-07-16 | Complete locally - Phase 3 Slice 5 patient RAG workflow, retrieval release, and live smoke | Implemented the normative patient-chat control flow as a server-owned finite-state workflow: deterministic emergency/prohibited/PII routing, patient-only retrieval and evidence gate, provider-neutral DeepSeek v4 Flash JSON adapter with thinking disabled, strict schema and citation validation, fixed fail-closed fallbacks, metadata-only `chatbot_events`, and session-only Flutter conversation state with bilingual safety copy and source cards. The legacy educational-chat endpoint wraps the same orchestrator. After product-owner confirmation that all 55 entries/documents were manually reviewed and patient-use approved, materialized 55 checksum-linked Chinese patient versions, 426 approved passages, and 165 medical/native-language/readability review rows without inventing reviewer names or changing the 353-source registry. Built and activated immutable local release `KBIR-8293AC8D815B9715D1B44F42`; a real local query returned six passages from six sources with sufficient evidence while retaining U.S. jurisdiction metadata. Focused provider-boundary coverage confirms a missing key returns `provider_unavailable` after sufficient retrieval and never uses model memory. The ignored local server environment already contained a DeepSeek credential, so no new key was requested or exposed. A bounded live orchestrator smoke passed with sufficient evidence, six retrieved sources/passages, valid structured output, one supported displayed citation, no fallback, and provider-reported usage of 4,250 input plus 160 output tokens; telemetry stored content-free metadata only. The first HTTP-auth attempt stopped before the model because local seed passwords were absent, so the successful call used the same server orchestrator directly with the existing synthetic patient row. | `services/api/app/patient_chat.py`, `services/api/app/patient_knowledge_release.py`, `services/api/app/knowledge_retrieval.py`, `services/api/scripts/activate_open_patient_education_release.py`, `services/api/knowledge_base/release_artifacts/`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/tests/test_phase3_patient_knowledge_release.py`, `apps/dr_ai_app/lib/features/chat/presentation/chat_screens.dart`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` | Slice 5 is complete locally. Production release still requires retrieval/answer/safety evaluation, clinical approval, privacy/legal/provider gates, observability/load checks, rollback rehearsal, production embedding/reranking approval, and deployment authorization. |
| 2026-07-17 | Complete locally - Phase 3 Slice 7 synthetic personalized-context foundation | Added a data-origin-neutral server context broker that selects only question-relevant profile basics, dated measurements, conditions, current prescriptions/medication schedules, active Clinical Events, and active recovery-plan fields. Every fragment carries a stable context ID, record provenance, source resource, and recorded date; provider output must cite used IDs, and server validation rejects unsupported personalization. One blood-pressure reading is explicitly represented as an observation rather than a diagnosis. The patient API returns server-derived context category/provenance/date cards, and the bilingual Flutter chat shows them only when context was actually used. Migration `20260717_0029` adds the profile-context provenance timestamp, and the synthetic patient seed supplies one dated observation while using the same tables and model-input contract as future patient-entered records. Full backend Ruff/tests, Alembic upgrade/drift check, Flutter analysis, all `58` active widget tests, and whitespace checks pass locally. No persistent conversation history, Slice 8 continuity, live provider smoke, deployment, push, PR, external account action, or real patient record was added. | `services/api/app/patient_context.py`, `services/api/app/patient_chat.py`, `services/api/app/ai_chat.py`, `services/api/app/chatbot_contracts.py`, `services/api/migrations/versions/20260717_0029_phase3_patient_context.py`, `services/api/tests/test_phase3_patient_chat.py`, `apps/dr_ai_app/lib/features/chat/presentation/chat_screens.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` | Slice 7 is complete locally. Slice 8 should add bounded session continuity and follow-up handling without creating persistent readable chat history. |
| 2026-07-17 | Complete locally - Phase 3 Slice 8 conversational continuity and interaction | Revised the earlier metadata-only history assumption per explicit product direction and implemented patient-owned readable AI threads with neutral cross-patient denial, a 60-day minimum retention timestamp renewed after each exchange, bounded eight-message model context, follow-up-aware retrieval, targeted non-repeating clarification prompts, and practical action chips. The chatbot now opens on a clean unsaved page, creates a thread on first send, restores full validated answer/source/context metadata, and provides a responsive collapsible history rail that defaults closed on small screens. `chatbot_events` remains content-free telemetry. Migration `20260717_0030` adds thread retention metadata and permits assistant messages without falsely assigning a patient actor. Backend Ruff, all backend tests, Alembic upgrade/drift check, Flutter analysis, the focused chat widget test, and all 59 non-golden Flutter tests pass. The two pre-existing dashboard golden comparisons still mismatch current unrelated dashboard rendering and were not regenerated during this slice. No deployment, push, PR, external account action, provider smoke, or real patient record was used. | `services/api/app/patient_chat.py`, `services/api/app/ai_chat.py`, `services/api/app/chatbot_contracts.py`, `services/api/app/models.py`, `services/api/migrations/versions/20260717_0030_phase3_chat_continuity.py`, `services/api/tests/test_phase3_patient_chat.py`, `apps/dr_ai_app/lib/features/chat/presentation/chat_screens.dart`, `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/l10n/`, `docs/Dr_AI_v1.0_ERD.md`, `docs/Dr_AI_v1.0_API_Contract.md` | Continue to Slice 9 answer depth and practical usefulness without expanding the chatbot's diagnostic or medication-change boundary; reconcile the unrelated dashboard goldens only in their own visual-baseline task. |
| 2026-07-17 | Complete locally - Phase 3 Slice 9 answer depth and practical usefulness | Expanded non-emergency diagnosis-seeking prompts from blanket refusal into evidence-grounded symptom orientation while preserving doctor ownership of confirmed diagnosis and treatment. The model contract now requires 3-5 supported sections, material uncertainty and a next action for symptom guidance, and rejects confident diagnostic assertions; medication-change and emergency gates remain unchanged. The patient chat now carries a concise AI-fallibility/verification notice, renders answer sections as readable paragraphs, shows material uncertainty in a distinct caution panel, offers broader symptom starter copy, and provides an “organize my symptoms” action. Updated the intended-use boundary, architecture, API contract, bilingual copy, response parsing, focused backend/widget coverage, and a mobile golden regression. No deployment, push, PR, external account action, provider smoke, real patient record, or autonomous diagnosis/treatment behavior was added. | `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `services/api/app/patient_chat.py`, `services/api/app/ai_chat.py`, `services/api/app/chatbot_contracts.py`, `services/api/tests/test_phase3_patient_chat.py`, `apps/dr_ai_app/lib/features/chat/presentation/chat_screens.dart`, `apps/dr_ai_app/lib/features/patient/domain/patient_care_data.dart`, `apps/dr_ai_app/lib/l10n/`, `apps/dr_ai_app/test/app_test.dart`, `apps/dr_ai_app/test/patient_chat_golden_test.dart`, `apps/dr_ai_app/test/goldens/patient_chat_practical_guidance_412x917.png` | Slice 9 is complete locally. Continue to planned refinement Slice 9A; final Slice 10 remains blocked until Slices 9A-9E have file-backed completion evidence. |
| 2026-07-18 | Planned - Phase 3 chatbot refinement Slices 9A-9E before final Slice 10 | Integrated the missing and underdeveloped chatbot components plus the approved adaptive multi-call RAG direction into five bounded slices: retrieval rights/production ranking; optional DeepSeek query planning and fused retrieval rescue; semantic claim support and follow-up quality; real-context privacy, adversarial isolation, and chat lifecycle; and operational controls with a pre-release evidence package. Preserved deterministic pre-model safety, server ownership of all operations, original-query retrieval, one rewrite/retry budget, fail-closed validation, and separation of AI-assisted judging from human signoff. Slice 10 remains final verification and the production/commercialization decision rather than an implementation backlog. This was documentation-only; no code, provider call, deployment, external account, or real patient data was changed. | `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Implement Slice 9A first and do not begin Slice 9B until its runtime rights, production retrieval, and retrieval-only evaluation gates pass. |
| 2026-07-18 | Slice 9A implementation complete locally; production gate open | Added independent live provider-transmission-right checks during patient release construction and immediately before evidence reaches an external reranker or DeepSeek; revoked, expired, not-yet-effective, and source-mismatched rights fail closed. Added exact passage embedding-model lineage, release/config matching, self-hosted BGE-M3 and BGE cross-encoder profiles, deterministic degradation fallback metadata, and production rejection of unapproved model profiles. Frozen a retrieval-only candidate suite spanning colloquial Chinese, bilingual terminology, short follow-up, symptom orientation, medication education, stale/conflict, and no-evidence behavior. Hong Kong is accepted for current development/staging because the API and PostgreSQL already operate there; the final production region remains evidence-based. The gate calculates Recall@6, nDCG@6, MRR, no-evidence precision, forbidden leakage, diversity, jurisdiction/language, and p95 latency without answer-evaluation material. Ruff, all `144` backend tests with warnings as errors, migration upgrade/drift check, and whitespace checks pass. The gate runner correctly refuses to create production evidence while clinician review is pending; no reviewer identity, approval, production service deployment, or passing production metric artifact was invented. The runtime validator still carries the original Mainland-specific identifiers and must be reconciled before production activation. | `services/api/app/knowledge_rights.py`, `services/api/app/knowledge_retrieval.py`, `services/api/app/knowledge_retrieval_evaluation.py`, `services/api/migrations/versions/20260718_0032_slice9a_retrieval_release_config.py`, `services/api/knowledge_base/evaluation/retrieval_cases.slice9a.v1.json`, `services/api/scripts/evaluate_slice9a_retrieval.py`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` | Begin Slice 9B implementation without weakening the open Slice 9A production gate. Before patient-facing production, obtain clinician approval/corrections, pass every retrieval threshold in the selected region, and reconcile the region-specific runtime configuration. |
| 2026-07-18 | Slice 9B implementation complete locally; production evidence gate open | Preserved literal original-query retrieval and the ordinary one-retrieval/one-answer path. Added deterministic short-reference, colloquial/ambiguous, and measured-weak-result triggers; one strict DeepSeek query-planner schema; a hard one-call/one-retry budget with bounded recent user context, provider timeout, conservative pre-call cost reservation, and no repair loop; meaning-drift and prohibited-instruction rejection; reciprocal-rank fusion with checksum collapse, per-source limits, conflict/sufficiency re-evaluation, and acceptance only on positive retrieval utility delta. Planner failure, malformed output, drift, retry failure, budget excess, and no improvement retain the original safe result or fixed fallback. Migration `20260718_0033` adds content-free rescue trigger/outcome, model, token/cache, latency, configured-price cost, delta, and retry-ID telemetry without storing queries, rewrites, concepts, prompts, conversation, or passages. Frozen six candidate hard/ordinary cases plus a validation/live gate runner. Harry Cao's product-owner approval and Hou Jin's clinical/native Simplified Chinese approval as Doctor at Beijing Hospital are file-backed for 2026-07-18 with no corrections required. Ruff, all `149` backend tests with warnings as errors, Alembic upgrade/drift check, dependency compatibility, suite validation, and whitespace checks pass. No provider call, deployment, production metric claim, real patient data, or Slice 9A gate bypass occurred. | `services/api/app/retrieval_rescue.py`, `services/api/app/ai_chat.py`, `services/api/app/patient_chat.py`, `services/api/app/knowledge_retrieval.py`, `services/api/app/chatbot_contracts.py`, `services/api/migrations/versions/20260718_0033_slice9b_retrieval_rescue.py`, `services/api/knowledge_base/evaluation/retrieval_rescue_cases.slice9b.v1.json`, `services/api/scripts/evaluate_slice9b_retrieval_rescue.py`, `services/api/tests/test_phase3_patient_chat.py`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` | Run the live approved-provider gate and require hard-query improvement, zero ordinary-query degradation, and passing latency/cost budgets. Slice 9C development may proceed without claiming either the Slice 9A or 9B production gate closed. |
| 2026-07-19 | Slice 9B failed-run correction implemented; v2 live gate pending | Preserved the first approved live artifact showing `0.0` hard-query improvement, `1.0` ordinary non-degradation, `2,586 ms` p95 rescue latency, `88` microunits average cost, and overall failure. Corrected longer Chinese reference detection, moved resolvable short references to deterministic bounded-thread query composition without a planner call, required context anchoring for ambiguous model rewrites with a safe contextual fallback, shortened the planner output budget, and separated `latency_exceeded` from `cost_exceeded`. Created reviewed suite v2 without changing any query or clinical source label; only the already-saturated colloquial case moved from impossible improvement to non-degradation control. Added expected-trigger, hard-case feasibility, minimum planner-use, suite-checksum, release-ID, total-latency, cost, and evidence-overwrite protections plus a no-cost preflight. The v2 preflight passes all six cases with three genuinely improvable hard cases and exact trigger matches. Ruff, all `153` backend tests with warnings as errors, suite validation, preflight, dependency compatibility, and whitespace checks pass. No second paid provider run, deployment, real patient data, or production-gate closure was claimed. | `services/api/app/retrieval_rescue.py`, `services/api/app/ai_chat.py`, `services/api/app/chatbot_contracts.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/scripts/evaluate_slice9b_retrieval_rescue.py`, `services/api/knowledge_base/evaluation/retrieval_rescue_cases.slice9b.v2.json`, `services/api/knowledge_base/release_artifacts/evaluation/slice9b-rescue.json`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` | Run v2 once with the approved provider and a new output path; close Slice 9B only if hard improvement, ordinary non-degradation, trigger, planner-use, total-latency, and cost gates all pass. |
| 2026-07-21 | Complete locally - first deterministic Slice 9C claim-support gate | Added sentence-level validation after schema and passage-ID membership: each answer sentence must remain anchored to its specifically cited admitted passages and authorized context, unsupported numbers/disease concepts/clinical-presentation features fail closed, and a valid but unrelated passage ID is rejected. Model uncertainty cannot introduce unsupported clinical entities. Patient-context use requires a server-issued attribution phrase and controlled provenance wording cannot contradict the cited record origin. Failures return fixed `unsupported_citation` copy and store only a content-free diagnostic subtype. Focused symptom-first structural tests passed `96/96`; all `215` backend tests, full Ruff, Alembic drift check, and whitespace checks passed. The existing cyclic `kb_rights_records`/`kb_sources` Alembic sort warning remains. No paid provider call, clinical approval, source-right activation, immutable release activation, deployment, real patient data, complete-answer evaluation, or production gate closure occurred. | `services/api/app/claim_support.py`, `services/api/app/patient_chat.py`, `services/api/tests/test_claim_support.py`, `services/api/tests/test_phase3_patient_chat.py`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Continue the 100-question Slice 9A corpus and named-review gates before paid 9B work; separately extend and clinician-calibrate Slice 9C for causal, interval, schedule, medication/treatment, and subtle-contradiction claims before running complete-answer evaluation. |
| 2026-07-21 | Complete locally - canonical complete-answer evaluation foundation and fail-closed preflight | Advanced the candidate canonical contract to schema `1.1.0` with a separate `canonical-complete-answer-v1` policy. Added machine scoring for route/action behavior, 100% emergency recall and zero pre-emergency calls, medication refusal, claim support, relevant/forbidden sources, uncertainty, provider usage, paired-variant non-degradation, latency, failures, and cost. A machine pass cannot close the independent clinician/native-Chinese human-review gate. Added a checksum- and active-release-bound preflight with one provider at a time, concurrency one, a five-case route-balanced initial batch, explicit answer/planner token caps, a computed worst-case `$0.013496` estimate under a `$0.10` cap, and repeated-provider-failure stop policy. The preflight made zero provider calls and correctly refused paid execution with 112 explicit blockers: six contract/review freeze blockers plus missing approved coverage and relevant-source labels for all 53 model-eligible canonicals. Regenerated matching safety-v2 and coverage-v4 artifacts; safety remains 37/37 canonical and 39/39 variant candidate critical recall with zero non-emergency false positives, while coverage remains 42/11/47 canonical and 19/5/39 variant candidate/no-evidence/pre-safety. The combined structural suite passed `101/101`; a first full run encountered a transient database wait in an existing HPA retrieval test, that exact test then passed independently, and a clean full rerun passed all `220` tests. Full Ruff, Alembic drift, and whitespace checks passed; the known cyclic knowledge-rights/source FK warning remains. No provider call, paid usage, approval, activation, deployment, or real-patient action occurred. | `services/api/app/answer_evaluation.py`, `services/api/scripts/evaluate_canonical_answers.py`, `services/api/scripts/build_canonical_symptom_contract.py`, `services/api/scripts/evaluate_canonical_symptom_contract.py`, `services/api/tests/test_answer_evaluation.py`, `services/api/knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-complete-answer-preflight-v1-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-safety-v2-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-coverage-KBIR-D3DFA94CC95660019B6EF94E-v4-answer-policy-local-20260721.json`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain and record named review plus case-specific approved source labels; only then run the five-case paid batch. Do not resume paid 9B or expand the answer batch until that batch passes machine gates and independent human review. |
| 2026-07-21 | Complete locally - symptom-first urgency routing and bounded multi-turn safety slice | Replaced the non-emergency all-routine behavior with a controlled clinical-presentation rule engine covering symptoms, anatomy, timing, trajectory, severity, associated signs, measurements, population/pregnancy, exposures, trauma, danger signals, negation, and hypothetical mentions. Deterministic routing now owns `emergency_120`, `urgent_same_day`, `clinician_contact`, and `routine_education`; it runs before retrieval or model calls, constrains the allowed next action, and rejects model attempts to weaken or upgrade the server route. Added bounded user-only multi-turn continuity while keeping the current literal retrieval query authoritative. Regenerated the checksum-bound 100-case/63-variant contract and local safety/coverage artifacts. Candidate routing matches all 100 canonicals and 63 variants; emergency recall remains 37/37 canonicals and 39/39 critical variants with zero non-emergency false positives and no claimed clinical approval. The latest retrieval audit reports 36 sufficient, 17 no-eligible-evidence, and 47 pre-safety canonicals plus 17/7/39 variants; link-only source candidates cover 12 of the 17 canonical gaps, while `RCQ-018`, `RCQ-028`, `RCQ-035`, `RCQ-074`, and `RCQ-083` still have no mapped candidate. The complete-answer v2 preflight remains fail-closed with 112 readiness failures, a five-case `$0.013496` maximum estimate under the `$0.10` cap, concurrency one, and zero provider calls. Bounded release membership was materialized before retrieval eligibility joins to eliminate a repeatable PostgreSQL full-suite slowdown. Focused structural tests passed `115/115`, retrieval/HPA tests passed `27/27`, and the clean full API run passed all `235` collected tests; full Ruff, Alembic drift, and whitespace checks passed, with the pre-existing cyclic knowledge-rights/source FK warning retained. No paid call, clinical approval, source activation, immutable-release activation, deployment, or real-patient action occurred. | `services/api/app/clinical_presentation.py`, `services/api/app/patient_chat.py`, `services/api/app/ai_chat.py`, `services/api/app/chatbot_contracts.py`, `services/api/app/answer_evaluation.py`, `services/api/app/knowledge_retrieval.py`, `services/api/scripts/build_canonical_symptom_contract.py`, `services/api/scripts/evaluate_canonical_symptom_contract.py`, `services/api/scripts/evaluate_canonical_answers.py`, `services/api/knowledge_base/evaluation/canonical_rural_symptom_questions.v1.json`, `services/api/knowledge_base/evaluation/canonical_rural_symptom_source_candidates.v1.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-safety-urgency-v3-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-coverage-KBIR-D3DFA94CC95660019B6EF94E-v5-urgency-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-complete-answer-preflight-v2-urgency-local-20260721.json`, `services/api/tests/test_clinical_presentation.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/tests/test_answer_evaluation.py`, `services/api/tests/test_canonical_source_candidates.py`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_API_Contract.md` | Obtain named clinical/native-Chinese/product review of routes, danger-signal combinations, scene-safety copy, and all case annotations; ingest and review authoritative patient-facing sources for the 17 canonical and seven variant evidence gaps; assign relevant/forbidden source IDs; then rerun retrieval and complete-answer gates before any paid 9B optimization. |
| 2026-07-21 | Complete locally - checksum-bound canonical source-intake mapping | Upgraded the separated source-candidate queue to schema `1.1.0` and added six verified official Mainland links for the previously unmapped biliary-pattern pain, spreading insect-bite changes, dog-bite rabies exposure, colloquial palpitation/chest-tightness, post-vaccination fever, and acute back-pain/leg-numbness presentations. Canonical and variant mappings are now explicit for all sources. Added a standalone no-network/no-provider validator that binds the queue to the canonical-contract and v5-coverage checksums, restricts locators to declared authority domains, verifies unique identifiers and exact mapping of all 17 canonical and seven variant no-evidence observations, enforces evaluation/retrieval/training separation, rejects embedded content or approval drift, and emits a local evidence artifact. The gate passes with 18 candidate sources, 17/17 canonical research leads, 7/7 variant research leads, zero unmapped IDs, zero provider calls, and explicit `eligible_evidence_claimed=false` and `clinical_approval_claimed=false`. This closes only research-lead discovery: every source remains link-only, rights-pending, review-pending, non-retrievable, and activation-blocked. The focused tests pass `3/3`; the clean full API run reaches 100% for all `236` collected tests; full Ruff, Alembic drift, and whitespace checks pass, with the pre-existing cyclic knowledge-rights/source FK warning retained. No content capture, clinical approval, rights approval, model call, paid usage, source/release activation, deployment, or real-patient action occurred. | `services/api/knowledge_base/evaluation/canonical_rural_symptom_source_candidates.v1.json`, `services/api/scripts/validate_canonical_source_candidates.py`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-source-intake-v1-local-20260721.json`, `services/api/tests/test_canonical_source_candidates.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain source- and content-class-specific reuse rights and named section-level clinical/native-Chinese/product review before governed capture. Then ingest approved sections, build a new immutable candidate release, populate case-specific relevant/forbidden source IDs, and rerun retrieval and complete-answer gates before any paid Slice 9B work. |
| 2026-07-21 | Complete locally - current v8 symptom-gap research-lead discovery | Expanded the separated, evaluation-only queue with 13 additional official Mainland source links and extended three existing mappings, covering every currently observed v8 presentation-centrality gap without storing article text or admitting evidence. The checksum-bound v2 validator passes with 31 link-only candidates, 33/33 canonical mappings, 25/25 variant mappings, zero provider calls, zero paid usage, and explicit `eligible_evidence_claimed=false` and `clinical_approval_claimed=false`. All candidates remain source-rights-, section-level clinical-, native-Simplified-Chinese-, readability-, and product-review pending; completion of link discovery does not change the v8 `no_eligible_evidence` decisions or populate relevant/forbidden source labels. Focused source-intake/coverage tests passed `5/5`; the full API suite passed all 250 tests in the established `3 + 4 + 243` database-safe partitions; full Ruff and Alembic drift passed; Alembic retained the known cyclic `kb_rights_records`/`kb_sources` warning. An overlapping local pytest rerun briefly deadlocked while two sessions attempted migrations against the same database; after confirming no stale pytest process remained, the isolated partition passed with exit code zero. No content capture, rights or clinical approval, source/release activation, answer generation, paid model call, deployment, or real-patient action occurred. | `services/api/knowledge_base/evaluation/canonical_rural_symptom_source_candidates.v1.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-source-intake-v5-complete-research-leads-local-20260721.json`, `services/api/tests/test_canonical_source_candidates.py`, `services/api/scripts/validate_canonical_source_candidates.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain source- and content-class-specific reuse rights and named section-level clinical/native-Chinese/readability/product review. Only approved sections may be governed into a new immutable candidate release; then populate case-specific relevant/forbidden source IDs and rerun retrieval, safety, rescue, and complete-answer gates before paid optimization. |
| 2026-07-21 | Complete locally - checksum-bound canonical review-provenance gate | Added a deterministic, evaluation-only review packet bound to the exact canonical contract file/content checksum, v8 active-release coverage artifact, and 31-source research-lead queue. The packet exposes all 100 canonical cases and 85 variants with their controlled annotations, active retrieval candidate IDs, and separate link-only lead IDs; it stores no article bodies or passages. Added a fail-closed validator for exact sets/checksums, no-content separation, named reviewer provenance, per-subject route/presentation/behavior/source/scene-safety decisions, source-specific rights capabilities and evidence, section selection, corrections requiring regeneration, and bidirectional source-to-case scope. The current packet is structurally valid but intentionally fails readiness with 949 pending items: 822 subject decisions, 34 active-source selections, 58 research-lead selections, four reviewer roles, and 31 source dispositions. It reports `eligible_evidence_claimed=false`, zero provider calls, and zero paid usage. Adversarial tests prove annotation/source drift, embedded source content, checkbox-only approval, missing rights/sections, and one-sided source scope fail closed. Focused review/source/coverage tests passed `10/10`; the full API suite passed all 255 tests in sequential `3 + 4 + 248` database-safe partitions; full Ruff and Alembic drift passed, retaining the known cyclic `kb_rights_records`/`kb_sources` warning. No review decision, rights approval, content capture, contract freeze, source/release activation, model call, deployment, or real-patient action was invented. | `services/api/scripts/build_canonical_review_packet.py`, `services/api/scripts/validate_canonical_review_packet.py`, `services/api/knowledge_base/evaluation/canonical_rural_symptom_review_packet.v1.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-review-readiness-v1-pending-local-20260721.json`, `services/api/tests/test_canonical_review_packet.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain and record the named reviews in a packet copy. Apply any corrections by regenerating the canonical contract and packet with new checksums; only then pursue rights-cleared governed section capture, source-ID label population, an immutable candidate release, and separate retrieval/rescue/safety/complete-answer gates. |
| 2026-07-21 | Complete locally - unified controlled emergency-routing authority | Removed the remaining patient-entry-point overdose/self-harm regex bypass so the production-shared controlled `SafetyAssessment` is the sole authority for every emergency decision. Added controlled Chinese/English overdose and self-harm presentation concepts, danger signals, priority/guidance mapping, and negation/hypothetical handling. Affirmed crisis inputs return immediate 120 plus bounded scene-safety guidance before retrieval/model calls; negated and educational/hypothetical forms do not emergency-route. A contract-wide invariant test proves endpoint routing agrees with the controlled assessment for all 100 canonicals and 85 variants. The checksum-bound v6 local safety artifact keeps exact route parity at 100/100 canonicals and 85/85 variants, emergency recall at 37/37 canonicals and 45/45 critical variants, zero non-emergency false positives, and zero structural/metric failures. Focused tests passed `100/100`; the full API suite passed all `269` tests in sequential `3 + 4 + 262` database-safe partitions. Full Ruff, Alembic upgrade/drift, and whitespace checks passed; Alembic retained the known cyclic `kb_rights_records`/`kb_sources` warning. No clinical approval, corpus support, model/provider call, paid usage, source/release activation, deployment, or real-patient action was claimed. | `services/api/app/clinical_presentation.py`, `services/api/app/patient_chat.py`, `services/api/tests/test_clinical_presentation.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/scripts/evaluate_canonical_symptom_contract.py`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-safety-urgency-v6-unified-authority-local-20260721.json`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain named clinical/native-Chinese/product review of every route, danger-signal combination, and scene-safety instruction; then complete rights-cleared governed evidence capture, source-ID labels, and the separate retrieval/rescue/complete-answer gates before any paid optimization or production claim. |
| 2026-07-21 | Complete locally - fail-closed canonical retrieval-only quality gate | Added a separate schema `1.0.0`, checksum- and active-release-bound retrieval policy and offline scorer so candidate coverage can no longer stand in for retrieval quality. The gate requires reviewed support labels for all 92 retrieval-eligible subjects and independently enforces relevant-source recall@6, MRR, relevant-decision correctness, symptom-only recall, all 39 paired-variant non-degradation comparisons, reviewed no-evidence precision, zero forbidden leakage/errors/pre-safety calls, 2,500 ms p95 and 8,000 ms maximum latency, and zero provider calls/cost. Extended the production `RetrievalResult` and canonical audit with content-free per-turn call/latency measurements; v9 preserves the v8 20/33/47 canonical and 14/25/46 variant candidate/no-evidence/pre-safety sets, so the existing 31-source v8 research queue remains a valid historical mapping. The first gate is structurally valid but honestly fails with 101 readiness and seven metric failures: support-label readiness is 0/92, clinically labelled recall/symptom-only recall/non-degradation are unscored, and candidate sufficiency is only 34/92 overall and 3/8 for retrieval-eligible symptom-only variants. Operational diagnostics pass locally at 93/93 pre-safety zero-call, zero retrieval errors, 918 ms p95, 1,687 ms maximum, zero provider calls, and `$0` usage; the observed zero forbidden hits cannot close that gate while labels are pending. Adversarial tests cover label/checksum/release drift, symptom-only degradation, forbidden leakage, latency, and missing observations. An initial HPA partition was interrupted after an uncommitted bulk-release query selected an unstable PostgreSQL plan; the integration test now commits activation before the patient read, matching production visibility, and the isolated partition passes. Focused tests passed `89/89`; all `274` API tests passed in sequential `3 + 4 + 267` partitions. Full Ruff and Alembic upgrade/drift passed, retaining the known cyclic `kb_rights_records`/`kb_sources` warning. No clinical/source-right approval, evidence admission, planner/answer-model call, paid usage, release activation, deployment, or real-patient action was claimed. | `services/api/app/canonical_retrieval_evaluation.py`, `services/api/app/knowledge_retrieval.py`, `services/api/scripts/audit_canonical_symptom_coverage.py`, `services/api/scripts/evaluate_canonical_retrieval.py`, `services/api/knowledge_base/evaluation/canonical_rural_symptom_retrieval_gate.v1.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-coverage-KBIR-D3DFA94CC95660019B6EF94E-v9-gate-metrics-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-retrieval-gate-v1-pending-local-20260721.json`, `services/api/tests/test_canonical_coverage_audit.py`, `services/api/tests/test_canonical_retrieval_evaluation.py`, `services/api/tests/test_hpa_health_myths_ingestion.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Complete named review and rights-cleared governed capture, populate case-specific relevant/forbidden labels, build a new immutable candidate release, and rerun this gate. Only after labelled symptom-only and paired metrics pass should complete-answer evaluation and any paid Slice 9B optimization resume. |
| 2026-07-21 | Complete locally - canonical complete-answer matrix-integrity gate | Corrected two false-positive paths in the complete-answer evaluator. Variants now retain their own expected route, retrieval/model permissions, relevant source IDs, forbidden source IDs, and coverage state instead of inheriting the parent canonical labels. Scoring now requires an explicit exact scope: the five route-balanced canonical IDs for `initial_batch`, or all 100 canonical plus 85 variant IDs for `full_contract`; duplicate, missing, extra, or unplanned observations fail before scoring. A passing initial batch can set only `ready_for_full_contract_run`, while `machine_gate_passed` remains false until the exact 185-input matrix passes. The scorer also rejects non-object observations, truthy-string booleans, negative call/latency/token/cost values, and invalid or duplicate citation source IDs. Contract/preflight readiness now includes all 39 model-eligible variants as well as 53 canonicals and requires named review provenance. The no-cost v4 preflight is structurally valid but records 190 readiness failures: 106 canonical source/coverage failures, 78 variant source/coverage failures, and six contract/review/freeze failures. It plans one case per route, retains the visible DeepSeek `deepseek-v4-flash` configuration, concurrency one, `$0.013496` worst-case estimate under `$0.10`, zero provider calls, and `$0` paid usage. Adversarial tests prove partial batches cannot pass, variant-specific urgent/source labels are honored, and malformed booleans/negative usage are rejected. Focused answer/retrieval/safety tests passed `114/114`; all `277` API tests passed in sequential `3 + 4 + 270` partitions. Full Ruff and Alembic upgrade/drift passed, retaining the known cyclic `kb_rights_records`/`kb_sources` warning. No paid call, clinical/source-right approval, evidence admission, full answer result, human-review pass, release activation, deployment, or real-patient action was claimed. | `services/api/app/answer_evaluation.py`, `services/api/scripts/evaluate_canonical_answers.py`, `services/api/tests/test_answer_evaluation.py`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-complete-answer-preflight-v4-matrix-integrity-local-20260721.json`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Complete named review, governed evidence capture, source labels, and a passing release-matched retrieval gate. Then run only the exact five-case paid initial batch; proceed to the 185-input run only if that batch passes, and keep independent clinician/native-Chinese human review mandatory. |
| 2026-07-21 | Complete locally - safety-authoritative retrieval-rescue planner boundary | Closed a cross-layer authority gap in Slice 9B. The patient endpoint now gives rescue only the prior user turn admitted by deterministic continuity, rather than the last three user messages. Rewrite validation is bound to the exact non-emergency `SafetyAssessment.presentation` and preserves symptoms, anatomy, onset, duration, trajectory, severity, associated signs, measurements, population, pregnancy, exposures, trauma, requested actions, danger signals, negation/hypothetical state, and condition mentions. A validated model rewrite can replace only `literal_query`; retry multi-view construction and presentation-central evidence admission still use the trusted controlled representation. The frozen v2 evaluator now follows the same continuity/safety path before retrieval. Runner v3 writes immutable structural-preflight evidence and explicitly records zero calls, tokens, and cost. The v3 preflight passed all six frozen cases with three improvable hard cases and exact trigger matches, but it is not a paid improvement/latency result and does not close Slice 9B. Added adversarial tests for omitted duration, reintroduced unadmitted pregnancy history, trusted retry presentation, and one-turn measurement-method continuity. Focused presentation/patient-chat tests passed `103/103`; all `280` API tests passed in sequential `3 + 4 + 273` partitions. The first HPA partition was interrupted after transient database waiting on its fourth test; Alembic remained at head, the exact case passed independently in 14 seconds, and the complete four-test partition then passed in 18 seconds. No provider/model call, paid usage, corpus or clinical approval, release activation, deployment, or real-patient action occurred. | `services/api/app/clinical_presentation.py`, `services/api/app/retrieval_rescue.py`, `services/api/app/patient_chat.py`, `services/api/scripts/evaluate_slice9b_retrieval_rescue.py`, `services/api/tests/test_clinical_presentation.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/knowledge_base/release_artifacts/evaluation/slice9b-rescue-v3-trusted-presentation-preflight-local-20260721.json`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Complete named clinical/source-right review, governed section capture, case-specific source labels, and a passing release-matched Slice 9A retrieval gate. Only then run the smallest paid Slice 9B batch and require hard-query improvement, non-degradation, latency, and cost gates before any larger run. |
| 2026-07-21 | Complete locally - rollback-only production-path pre-model answer gate | Added an executable, content-free complete-answer lane for every contract subject that must terminate before retrieval or a model: 47 canonicals and 46 variants, comprising 82 emergency routes and 11 prohibited medication-change refusals. Runner v2 executes the real `send_patient_chat_message` path under the recognized synthetic demo identity, inserts only the contract-authorized prior user turn for multi-turn cases, replaces retrieval/planner/answer adapters with fail-fast probes, requires emergency output to equal the controlled guidance selected by `SafetyAssessment`, and contains endpoint commits in an outer rollback-only transaction. The immutable local artifact passed 93/93 with 100% emergency recall, zero pre-emergency calls, 100% medication-gate and route/action behavior, 11 ms p95 and 29 ms maximum latency, zero provider-reported tokens, and `$0` paid usage; direct database checks found zero persisted evaluation threads or events. The planner adapter's own input bound is now also one prior user message. Separately, replaced the active-release materialized CTE/JSON join that intermittently stalled PostgreSQL with a deterministic two-stage immutable-membership lookup; release-scoped embedding precedence, legacy fallback, rights/review eligibility, and model-version fail-closed behavior are preserved and regression-tested. Affected HPA/retrieval/release tests passed `35/35`, and the complete API suite passed all `282` collected tests. Repository-wide Ruff lint and touched-file Ruff formatting checks pass; Alembic upgrade/drift passes with the known cyclic `kb_rights_records`/`kb_sources` warning; the repository-wide format check still identifies 21 pre-existing Phase 3 files outside this slice and those intentional changes were not mass-reformatted. No provider/model call, clinical or language approval, corpus admission, generated-answer/full-contract pass, release activation, deployment, or real-patient action was claimed. | `services/api/scripts/evaluate_canonical_answers.py`, `services/api/app/ai_chat.py`, `services/api/app/knowledge_retrieval.py`, `services/api/tests/test_answer_evaluation.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/tests/test_phase3_knowledge_retrieval.py`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-premodel-answer-v2-rollback-production-path-local-20260721.json`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain named clinical/native-Chinese/product review, rights-cleared governed evidence, case-specific source labels, and a passing release-matched Slice 9A retrieval gate. Then run the exact five-case generated-answer batch before the 185-input gate and independent human review; only after those pass may the smallest paid Slice 9B improvement/latency batch run. |
| 2026-07-21 | Complete locally - presentation-aware rescue and all-remaining-subject safe-degradation gate | Audited the five retrieval-eligible symptom-only failures and confirmed that they are governed-corpus gaps rather than missed approved evidence: orthostatic presyncope, positional vertigo, pesticide-related dermatitis, palpitation/chest-tightness, and reduced fetal movement all map to official Mainland research leads, but every lead remains link-only and rights/review pending. Live page checks found explicit NHC copyright notices and no recorded reusable licence for the Beijing/Yantai pages, so no body text was copied or admitted. Added a second rollback-only production-path lane for the exact 92 post-safety subjects (53 canonicals and 39 variants), complementing the 93 pre-model subjects without overlap. It runs real active-release retrieval while local probes force planner/answer service unavailability and prohibit external requests; the v2 content-free artifact passes 92/92 route/action, call-boundary, fixed-fallback, zero-usage, and rollback checks, with 34 candidate-sufficient and 58 no-evidence decisions, 92 retrievals, 59 planner-adapter invocations, 34 answer-adapter invocations, zero provider requests/tokens/cost, 900 ms p95, 975 ms maximum latency, and zero persisted threads/events. The first diagnostic run exposed a systemic regex-first defect: the suffix `要紧吗` classified a self-contained blood-streaked-sputum query as context-dependent ambiguity and erased sufficient evidence when the planner was unavailable. Rescue triggering now consults the controlled presentation and may use ambiguity evidence-withholding only when no standalone symptom, pregnancy, exposure, trauma, or explicit-condition topic exists. The corrected full artifact restores exact 34/58 parity with the retrieval audit; the Slice 9B v4 no-cost preflight retains exact trigger matches across all six frozen cases. Focused answer/patient-chat tests passed `71/71`; all `284` API tests passed. Repository-wide Ruff lint and touched-file formatting pass; Alembic upgrade/drift passes with the known cyclic knowledge-rights/source warning. No content licence, clinical/language approval, evidence admission, retrieval-quality/complete-answer pass, provider request, paid usage, release activation, deployment, or real-patient action was claimed. | `services/api/app/retrieval_rescue.py`, `services/api/scripts/evaluate_canonical_answers.py`, `services/api/scripts/evaluate_slice9b_retrieval_rescue.py`, `services/api/tests/test_answer_evaluation.py`, `services/api/tests/test_phase3_patient_chat.py`, `services/api/knowledge_base/release_artifacts/evaluation/canonical-safe-fallback-v2-presentation-aware-rollback-local-20260721.json`, `services/api/knowledge_base/release_artifacts/evaluation/slice9b-rescue-v4-presentation-aware-ambiguity-preflight-local-20260721.json`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain reuse permission or select rights-cleared alternatives, then complete named section-level clinical/native-Chinese/readability/product review and governed capture for the five symptom-only gaps and all other unsupported cases. Populate relevant/forbidden labels, build a new immutable candidate release, and pass the retrieval-only gate before the exact five-case generated-answer batch or any paid Slice 9B rerun. |
| 2026-07-21 | Complete locally - rights-cleared supplementary symptom-source intake and fail-closed review gate | Generalized the governed open-content and DeepSeek translation pipeline to accept explicit checksum-bound supplementary corpus sizes and artifact paths while preserving the frozen 55-source schema and provenance. Captured five publisher-authored MedlinePlus summaries under the existing public-domain content-class evidence: low blood pressure, dizziness/vertigo, arrhythmia, pesticides, and skin conditions. Generated five unofficial Simplified-Chinese candidates sequentially with `deepseek-v4-flash` after a one-document probe; provider-reported usage was 2,591 input, 1,706 output, and 4,297 total tokens, with approximately `$0.0008` configured-price cost under a `$0.05` ceiling and no provider failures. Added a separate checksum-bound corpus-review manifest and validator requiring named medical, native-Chinese, readability, Mainland-applicability, and product review without copying evaluation prompts into retrieval material. Structural validation passes, while admission correctly fails with 45 pending review decisions and four open translation/centrality blockers. Import verification produced five pending sources and five `generated_pending_review` translations with zero patient/doctor, lexical, or vector eligibility. Focused source/translation/review tests passed `15/15`; all `292` API tests passed. Repository-wide Ruff lint, touched-file formatting, JSON parsing, Alembic upgrade/drift, and whitespace checks pass; Alembic retains the known cyclic `kb_rights_records`/`kb_sources` warning. No clinical/language/readability/Mainland/product approval, evidence support label, immutable release, retrieval or answer gate improvement, deployment, or real-patient action is claimed. | `services/api/app/open_content_ingestion.py`, `services/api/app/knowledge_translation.py`, `services/api/app/knowledge_review.py`, `services/api/scripts/build_open_patient_education_corpus.py`, `services/api/scripts/build_open_symptom_gap_corpus.py`, `services/api/scripts/import_open_patient_education.py`, `services/api/scripts/import_open_patient_education_translations.py`, `services/api/scripts/translate_open_patient_education.py`, `services/api/scripts/validate_open_symptom_review.py`, `services/api/knowledge_base/catalog/open_symptom_presentations.v1.json`, `services/api/knowledge_base/translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.json`, `services/api/knowledge_base/translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.jsonl`, `services/api/knowledge_base/reviews/open_symptom_presentations.v1.json`, `services/api/tests/test_phase3_open_patient_education.py`, `services/api/tests/test_phase3_knowledge_translation.py`, `services/api/tests/test_open_symptom_review.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain named reviews and resolve all four blockers; replace or strictly limit the two weak-centrality sources, capture a rights-reviewed reduced-fetal-movement source, and only then admit reviewed passages, populate source labels, build a non-active immutable candidate, and rerun the Slice 9A retrieval-only gate before any further paid Slice 9B work. |
| 2026-07-21 | Complete locally - licensed reduced-fetal-movement source intake | Extended the six-source symptom-presentation intake without changing the active release. Generalized the governed catalog to represent explicit publisher jurisdiction, authority basis, content class, licence-stable ID, permission scope, capability flags, supporting evidence locators, population, and review-due metadata while keeping schema `1.0` frozen to the original 55-source counts. Captured the NHS `Your baby's movements` patient page as six publisher-authored text sections after mechanically verifying the NHS OGL v3 commercial/adaptation terms, content-exclusion page, non-excluded URL path, required clinical phrases, and removal of images/video/logos and linked third-party material. The checksum-bound rights record permits the public-source translation call but named rights review remains mandatory before candidate admission; translated or non-refreshed wording cannot inherit NHS clinical approval, claim NHS authorship/endorsement, or retain England-specific care navigation without Mainland review. One sequential `deepseek-v4-flash` call generated the six-section Chinese candidate with 611 input, 511 output, and 1,122 total provider-reported tokens; cumulative six-source usage is 3,202 input, 2,217 output, and 5,419 total tokens, with approximately `$0.0011` configured-price cost under `$0.05` and zero provider failures. The review manifest now binds six sources/translations, requires 60 named rights/medical/language/readability/Mainland/product decisions, and intentionally fails admission with six open blockers. Local import verification records six sources, six versions, eleven original passages, and six `generated_pending_review` translations with zero patient/doctor, lexical, or vector eligibility. Focused tests passed `15/15`; all `292` API tests passed. No rights/clinical/language/readability/Mainland/product approval, relevant/forbidden source label, evidence admission, immutable release, retrieval/answer metric change, deployment, or real-patient action is claimed. | `services/api/app/open_content_ingestion.py`, `services/api/app/knowledge_review.py`, `services/api/scripts/build_open_symptom_gap_corpus.py`, `services/api/knowledge_base/catalog/open_symptom_presentations.v1.json`, `services/api/knowledge_base/translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.json`, `services/api/knowledge_base/translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.jsonl`, `services/api/knowledge_base/reviews/open_symptom_presentations.v1.json`, `services/api/tests/test_phase3_open_patient_education.py`, `services/api/tests/test_phase3_knowledge_translation.py`, `services/api/tests/test_open_symptom_review.py`, `services/api/knowledge_base/README.md`, `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`, `docs/Dr_AI_v1.0_Implementation_Plan.md` | Obtain and record all named reviews, resolve the six blockers, apply corrections by regenerating checksum-bound artifacts, then populate case-specific source labels and build a non-active immutable candidate for the Slice 9A retrieval-only gate. |
