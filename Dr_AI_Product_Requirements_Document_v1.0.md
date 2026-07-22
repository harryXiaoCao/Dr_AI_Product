# Dr. AI Product Requirements Document v1.0

Status: formal production-readiness PRD
Owner: Harry Cao
Last updated: 2026-07-23
Primary platforms: Flutter mobile, Flutter web, FastAPI, PostgreSQL, Tencent Cloud
Product stage: production-quality development in progress; the patient/doctor
and governed-AI foundation is preserved while Dr. AI adds a China-first,
multi-scenario care-and-cost transparency platform for patients, doctors, and
authorized payer reviewers. Synthetic/de-identified showcases are the first
validation and partnership path, not the final product boundary.

## 1. Executive Summary

Dr. AI is an explainable care-and-cost review platform for patients, doctors,
and payer reviewers such as government medical-insurance or authorized
insurance organizations. It preserves the existing clinical-copilot foundation
while adding a transparent view of planned care, services actually delivered,
charges, coverage, and material cost or utilization differences that may need
human review.

The product is not a generic telemedicine app, an autonomous diagnosis system,
or an automated claim-denial engine. Its core value is to connect the existing
doctor-patient workflow with an evidence-linked **expected-care envelope**: a
versioned range of plausible services and costs, generated from reviewed rules,
fee references, and bounded AI assistance. The envelope is compared with
planned, delivered, billed, allowed, paid, and patient-responsibility amounts.
Differences create explainable review alerts, not accusations of abuse.

The original Word PRD defines a broad healthcare operating-system vision for
rural and underserved communities. This Markdown PRD changes the primary value
proposition but retains the goal of a production-ready product. Dr. AI should
be engineered for reliable multi-scenario use, real persistence, strict
authorization, versioned policy data, operational controls, and future
institutional integration. Until the required licenses, partners, governed
data, validation, privacy, security, and regulatory gates are closed, external
showcases and testing must use synthetic or appropriately de-identified data
and must not claim measured real-world impact, clinical validation, fraud
detection, coverage authority, or authorization for live use.

## 2. Product Vision

Dr. AI should make the care-and-payment journey understandable to all three
parties without placing AI above human judgment. Patients should understand
what care is planned, what occurred, what was charged, what is covered, and
what they may owe. Doctors should retain a structured clinical workspace and
receive review support before a claim or cost package is finalized. Authorized
payer reviewers should receive itemized, evidence-linked comparisons and the
doctor's explanation for legitimate exceptions.

The long-term vision is a governed, interoperable platform that improves
medical-resource transparency and supports appropriate utilization, especially
for smaller clinics and underserved communities. China is the first
jurisdictional design target. A future U.S. adapter may support U.S. coding,
contracted-rate, claim, and patient-responsibility concepts, but must not reuse
Chinese reimbursement logic as if the systems were interchangeable.

## 3. Positioning

Dr. AI is an **AI-empowered medical expenditure transparency and utilization
review platform**, not a direct-to-consumer diagnosis bot, fraud adjudicator,
or replacement for clinicians or payer reviewers.

The product must communicate three boundaries clearly:

- Doctors remain responsible for clinical judgment, diagnosis, treatment, and
  the clinical justification for exceptional care.
- Patients receive guidance, education, reminders, recovery-plan support, and escalation prompts, not autonomous medical diagnosis.
- Payer reviewers remain responsible for reimbursement, escalation, appeal,
  and suspected-fraud decisions. No model output may automatically deny,
  reduce, or delay care or coverage.
- AI output remains assistive, uncertain, sourced, versioned, and
  non-authoritative until the relevant model, data, policy, clinical,
  regulatory, privacy, and deployment gates are explicitly closed.
- A variance is a prompt for review, not proof of waste, abuse, fraud, poor
  care, or an incorrect bill.

## 4. Source Of Truth And Current Product Reality

This PRD is grounded in:

- The original Word PRD at `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx`.
- The current implementation source of truth in `docs/Dr_AI_v1.0_Implementation_Plan.md`.
- The product-quality gate in `docs/Dr_AI_v1.0_Product_Quality_Gate.md`.
- The Phase 2 patient/doctor progress record in `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`.
- The API contract in `docs/Dr_AI_v1.0_API_Contract.md`.
- The implemented-plus-planned data boundary in `docs/Dr_AI_v1.0_ERD.md`.
- The current Flutter and FastAPI code.

Current verified product state:

- Doctor, patient, and payer primary roles are implemented. Payer access also
  requires an active organization membership; the role alone grants no case
  access.
- Specialist and admin roles are reserved in the backend but not yet product-ready.
- Invited registration, login, refresh-token rotation, logout, and role routing exist.
- Patient profile fields, doctor profile fields, avatar URL fields, patient codes, and doctor-patient care relationships exist.
- Doctor-side patient connection by patient-shared code exists.
- Clinical Event / Care Episode is the central Phase 2 workflow object.
- Patient demographics, medical history, allergies, chronic diseases, visit history, diagnoses, doctor notes, medication records, prescriptions, reminders, imaging metadata, recovery plans, patient Today progress, patient event updates, consultation requests, and educational chat have implemented foundations.
- Event-level care-and-cost items, patient/doctor ledger readback, immutable
  payer-request line snapshots, and a scoped human payer-review queue are
  implemented as the first local three-party vertical slice. Amounts use CNY
  integer minor units.
- External push, SMS, email, native local notifications, real model inference,
  production claims/adjudication, reference-pricing and coverage engines,
  analytics dashboards, clinic operations, specialist workflows, and admin
  workflows are not production-ready.
- The implementation plan records the Phase 2.5 product-quality gate as complete. Phase 3 chatbot development is open, while each AI workflow still requires its own retrieval, medical-review, safety, privacy, legal, provider, and regulatory release gates.
- Payer organizations and memberships now exist for synthetic-only review.
  Coverage enrollment, formal claim/claim-line semantics, reference pricing,
  expected-care envelopes, deterministic variance alerts, appeals, and live
  organizational onboarding remain planned and must not be represented as
  current functionality.

## 5. Target Users

### 5.1 Patients

Patients use Dr. AI mainly on mobile. They need to:

- Create or access an account.
- Complete identity and contact profile basics.
- Enter and maintain medical history.
- Share a patient code with a doctor.
- Understand current Clinical Events / Care Episodes.
- View prescriptions, medications, reminders, imaging status, recovery plans, and Today tasks.
- Send limited self-reported updates to active Clinical Events.
- Ask educational health questions with clear emergency escalation.
- Understand what to do next without seeing developer/test vocabulary.

### 5.2 Doctors

Doctors use Dr. AI mainly on tablet or web. They need to:

- Sign in or create an approved doctor account.
- Complete doctor identity and institution profile basics.
- Connect patients by patient-shared code.
- Review patient profile and medical history.
- Create and manage Clinical Events / Care Episodes.
- Manage diagnoses, prescriptions, medication schedules, recovery plans, imaging review, private notes, consultation requests, and activity timeline in event context.
- Search a dedicated doctor-only medical Resources workspace backed exclusively by admitted authoritative Chinese medical organizations or WHO sources, with visible provenance, jurisdiction, dates, language, review, and version status.
- Use AI assistance only after the non-AI workflow is credible and the relevant safety gates are closed.

### 5.3 Specialists

Specialists are preserved future product users outside the critical path of the
v1.0 three-party core. They need to:

- Receive consultation requests from doctors.
- Review structured patient context and attachments/annotations where authorized.
- Accept, reject, or respond to consultation requests.
- Provide structured specialist feedback without bypassing doctor ownership.

Specialist UI is not currently implemented and must remain unavailable until Phase 5.

### 5.4 Administrators

Administrators are preserved future product users. A minimal synthetic payer
configuration may initially be fixture- or migration-owned; a general admin
surface is not required for the v1.0 three-party core. Administrators eventually
need to:

- Manage users, hospitals, clinics, role assignments, and configuration.
- Review audit events and system status.
- Manage support, feedback, and deletion queues.
- Oversee clinic resources, billing, analytics, and operational modules where enabled.

Admin UI is not currently implemented and must remain unavailable until Phase 5.

### 5.5 Payer Reviewers

Payer reviewers represent an authorized government medical-insurance agency,
public program, or insurance organization. They need to:

- Review only cases within their organization's explicit authorization scope.
- Compare itemized planned, delivered, billed, allowed, paid, and
  patient-responsibility amounts.
- Inspect the expected-care envelope, its range, jurisdiction, source lineage,
  version, confidence, and missing-information notes.
- See explainable variance reason codes without treating an alert as a fraud
  determination.
- Request clarification, accept a clinician explanation, escalate for human
  review, or close the review with a recorded reason.
- Keep reimbursement and suspected-abuse decisions human-owned and auditable.

Payer organizations, policies, coverage, claim records, and reviewer accounts
remain synthetic until the corresponding institutional, data, privacy,
security, and regulatory gates close. The production domain and authorization
model must nevertheless be designed for real organizations rather than a
single fixture. A government regulator and an insurance payer are not assumed
to be the same legal organization merely because both may review expenditure
information.

## 6. Product Goals

1. Make the patient-doctor care workflow understandable from first use.
2. Provide a calm, credible healthcare UX that can be shown to early testers, advisors, and competition judges without explaining away prototype roughness.
3. Make Clinical Events / Care Episodes the organizing concept for doctor work and patient care continuity.
4. Let patients own identity and medical-history setup while doctors review, verify, and amend with audit trails.
5. Keep role-based access, cross-patient isolation, and audit metadata strict.
6. Support bounded, evidence-linked explanation, recovery-plan support,
   medication safety, and education through clearly gated workflows; do not
   commercialize Dr. AI as a diagnostic tool.
7. Add a three-party, itemized care-and-cost review loop that is transparent to
   patients, clinicians, and authorized payer reviewers.
8. Demonstrate how explainable variance review could reduce unnecessary or
   unusually costly care without encouraging under-treatment or automatic
   denial.
9. Preserve a future path to specialist, admin, clinic operations, billing,
   analytics, and jurisdiction-specific deployment without exposing half-built
   modules as finished features.

## 7. Non-Goals And Safety Boundaries

The following are not allowed in v1.0 or any public-facing claim unless
separately approved and validated:

- Real patient data.
- Clinical claims that the product diagnoses, treats, or replaces clinicians.
- Autonomous diagnosis or medication-change instructions.
- A single AI-estimated amount presented as the correct or medically necessary
  cost.
- Automatic claim denial, payment reduction, care restriction, fraud labeling,
  clinician ranking, or punitive action.
- Language stating that a variance proves waste, abuse, fraud, over-treatment,
  or an incorrect bill.
- An opaque score without sources, reason codes, uncertainty, and an available
  human review path.
- Real model inference presented as clinically validated.
- Public release, store upload, tester invite, deployment, account change, or data deletion without explicit approval.
- Specialist/admin access to unfinished workflows.
- Normal-flow UI that presents seeded/demo/test content as the main product experience.

The product may keep a concise staging or beta warning that no real patient data should be entered. That warning should be environment-level and professional, not repeated as distracting "demo" language across every normal workflow.

## 8. Release Scope

### 8.1 v1.0 Production-Ready Core

v1.0 must include a production-quality patient/doctor/payer platform:

- Account lifecycle and role-based routing.
- Patient onboarding, profile, avatar, medical-history setup, and doctor connection.
- Doctor onboarding, doctor profile, patient connection, and patient workspace.
- Clinical Event / Care Episode management.
- Patient profile and medical-history read/update/review workflow.
- Medication, prescription, reminder, recovery-plan, imaging, consultation, and activity workflows linked to Clinical Events.
- Patient Today view and recovery-plan progress.
- Patient educational chat with safety escalation.
- Support, feedback, and account deletion request submission/status foundation.
- Strict RBAC, neutral denials, metadata-only audit events, and no real patient data.
- Production-quality UX, typography, empty states, and onboarding.
- Synthetic payer organization, plan/coverage, and reviewer access.
- A configurable China-first end-to-end workflow from doctor-authored clinical
  plan to itemized charge review and patient-facing cost explanation across a
  clinician-reviewed set of representative scenario families. The system must
  not hardcode one disease, encounter, hospital, or payer fixture.
- Versioned expected-care envelope with plausible care categories, an
  estimated cost range, sources, jurisdiction, effective date, confidence,
  and missing-information notes.
- Itemized planned, delivered, billed, allowed, paid, and patient-responsibility
  amounts using an explicit currency and integer minor units.
- Explainable review alerts, clinician rationale, human resolution, and an
  immutable state-transition history.
- A prominent environment boundary while live-use gates remain open:
  synthetic/de-identified data, no clinical or reimbursement use, and no
  proven real-world impact claim. This boundary limits deployment, not the
  production quality or breadth of the product architecture.

### 8.2 Preserved Future Product Scope

These modules are preserved for later development but are not required for the
production-ready three-party care-and-cost core:

- Specialist consultation workflow beyond basic doctor request/status.
- Admin dashboard and queue management.
- Clinic resource management.
- Appointment and scheduling workflows.
- Legacy billing subset: invoices, payment status, and revenue summaries. These
  do not replace the new encounter/claim/line-item review domain.
- Analytics subset: disease statistics, recovery progress, referrals, AI usage, and operational activity.
- Monitoring, backup/restore rehearsal, release signing, and deployment runbook.
- Simplified Chinese and English localization foundation.

### 8.3 Explicit Live-Deployment And Expansion Gates

These items require separate readiness decisions:

- Real GCAVE-GAN / multimodal lung-cancer model inference.
- Real clinical deployment and clinical claims.
- Voice/video consultation.
- DICOM viewing and segmentation.
- Barcode scanning.
- Full payment processing.
- Live payer integration, real claim submission, eligibility verification,
  prior authorization, reimbursement adjudication, or appeal processing.
- Real hospital fee schedules, negotiated rates, DRG/DIP settlement data, or
  U.S. coding/contract adapters unless rights, currency, effective dates, and
  jurisdiction are verified.
- External SMS/email/push/native notification delivery.
- National EHR integration.
- Wearables.
- Offline mode.
- Disease surveillance and broad public-health analytics.

## 9. Core Product Model

Dr. AI should be organized around a coherent care model:

```text
Patient Account
  -> Patient Profile
  -> Medical History
  -> Doctor-Patient Care Relationship
  -> Clinical Event / Care Episode
      -> Diagnosis context
      -> Prescriptions
      -> Medication schedule and reminders
      -> Recovery plan
      -> Imaging assets and doctor findings
      -> Patient updates
      -> Doctor notes
      -> Specialist consultation
      -> Activity timeline
      -> Care-and-cost review case
          -> Doctor-authored planned care
          -> Expected-care envelope and cost range
          -> Delivered-service and claim line items
          -> Variance alerts and reason codes
          -> Clinician rationale
          -> Human payer review and resolution
          -> Patient-facing cost explanation
```

The Clinical Event / Care Episode should represent one medical problem or follow-up condition managed over time. One appointment can contain multiple Clinical Events, and one Clinical Event can span multiple encounters.

The care-and-cost review case is linked to, but does not own or rewrite, the
Clinical Event. Clinical truth, AI suggestions, delivered services, submitted
charges, payer decisions, and patient-visible explanations must remain
separate records with independent provenance and timestamps.

## 10. Primary User Journeys

### 10.1 New Patient First Use

1. Patient creates an account using phone number and optional email.
2. Patient confirms password, accepts privacy and terms, and completes verification or invite flow.
3. Patient sets display name, avatar, birth date or age, sex/gender, contact number, emergency contact, preferred language, and contact preference.
4. Patient enters medical-history basics or sees a clear setup entry point.
5. Patient receives a patient code and understands how to share it with a doctor.
6. Patient sees a dashboard with a clear next action, even before any doctor connection exists.

### 10.2 Doctor First Use

1. Doctor creates or signs in to an approved account.
2. Doctor completes identity, specialty, title, hospital association, department, phone, email, country, province, city, and preferred language. Hospital records become administrator-managed after registration.
3. Doctor previews the patient name and masked ID, confirms the match, and then connects the patient by patient-shared code.
4. Doctor reviews patient profile and medical history.
5. Doctor creates or selects a Clinical Event.
6. Doctor manages prescriptions, medication schedules, recovery plan, imaging review, notes, and consultation inside the selected event.

### 10.3 Active Patient Care

1. Patient sees active Clinical Events and Today tasks.
2. Patient completes medication, exercise, diet, and follow-up tasks.
3. Patient reads active recovery-plan progress.
4. Patient submits updates to the relevant Clinical Event without editing doctor-owned diagnosis fields.
5. Patient asks educational questions with red-flag emergency escalation before any model call.

### 10.4 Doctor Event Management

1. Doctor opens Patient Management.
2. Doctor selects an assigned patient.
3. Doctor reviews identity-safe summary and verified history.
4. Doctor selects the active Clinical Event.
5. Doctor updates diagnosis context, prescriptions, medication schedule, imaging review, recovery plan, notes, consultation, and timeline.
6. Doctor resolves or closes the event when clinically appropriate.

### 10.5 Three-Party Care-And-Cost Review

1. The doctor selects a Clinical Event and records a preliminary assessment
   plus a proposed care plan. Synthetic/de-identified fixtures exercise this
   same production contract until live-data gates close.
2. Dr. AI generates a draft expected-care envelope from versioned, admitted
   clinical/utilization rules and jurisdiction-specific price references.
3. The doctor reviews the envelope before submission, corrects factual errors,
   and records why an exceptional pathway is clinically justified.
4. Synthetic delivered-service and claim line items are recorded separately
   from the plan and AI output.
5. The review engine compares itemized amounts and utilization, then emits
   explainable `review_recommended` alerts for material differences.
6. The payer reviewer inspects sources and clinician rationale, requests
   clarification or records a human resolution, and never delegates the final
   reimbursement or abuse decision to the model.
7. The patient sees plain-language planned-versus-actual-versus-covered amounts
   and review status without internal fraud scores, reviewer-only notes, or
   another patient's data.

## 11. Functional Requirements

### 11.1 Authentication And Account Management

Requirements:

- Support patient and doctor registration through approved invite or verification policy.
- Support phone number as a required account field and email as optional or secondary where product policy allows.
- Accept Unicode text, including Simplified Chinese, in names and other free-text profile fields; a one-character Chinese family name must pass validation.
- Require password confirmation, privacy consent, and terms consent during signup.
- Support login, logout, session restoration, refresh-token rotation, and server-side session revocation.
- Allow authenticated doctors and patients to change their password after confirming the current password; revoke all refresh sessions after a successful change.
- Allow password recovery by the verified phone number on the account. The challenge, expiry, attempt limit, reset, and audit flow must be production-backed even while the external SMS sender remains deferred to Phase 6.
- Fail closed for unsupported roles.
- Provide profile editing for patients and doctors.
- Allow doctors and patients to add, update, or remove the optional account email from Account.
- Display doctor phone and available email in the doctor Account contact summary.
- Treat a doctor as recently active only when their latest authenticated activity is within the preceding 14 days.
- Keep hospital information read-only for doctors after registration; hospital and clinic records are owned by administrator workflows.
- Provide account deletion, support, and feedback request submission/status.
- Support biometric login on mobile when platform configuration is ready.
- Support SMS verification or explicitly document it as deferred.

Acceptance criteria:

- A new patient and doctor can create accounts without seed data.
- A wrong-role user cannot access another role's workspace.
- Refresh-token reuse revokes the session family.
- Support/deletion/feedback requests persist and are scoped to the requester.
- Password changes and resets revoke existing refresh sessions and create metadata-only audit events.

### 11.2 Patient Profile And Medical History

Requirements:

- Patient profile includes avatar, display name, birth date or age, sex/gender, phone, emergency contact, preferred language, contact preference, country/province/city, and address where needed.
- Patients can update their own profile.
- Doctors can review patient profile but should not directly own patient identity fields.
- Medical history includes allergies, chronic diseases, surgeries, family history, lifestyle/relevant history, long-term medications, and previous major diagnoses.
- Doctors can verify, request correction, or add clinician amendments without overwriting patient-entered history.
- Sensitive reads and writes create metadata-only audit events.

Acceptance criteria:

- Patient profile setup is a guided first-use journey.
- Patient medical-history setup is visible during or immediately after onboarding.
- Doctor amendments are visually distinguishable and audited.
- Patient-owned content is not silently replaced by doctor actions.

### 11.3 Doctor Patient Workspace

Requirements:

- Patient Management should be a focused patient workspace, not a long mixed dashboard.
- Desktop/tablet layout should include assigned-patient list/search and a selected-patient detail area.
- Phone-width layout should avoid overflow and use compact patient selection.
- Patient-ID connection must show a minimal patient match preview and require explicit doctor confirmation before creating the care relationship.
- Detail sections should include Overview, Profile, Medical History, Clinical Events, Medications & Prescriptions, Recovery Plans, Imaging, and Consultation & Activity.
- Each section should have one primary job and section-level loading, empty, validation, failure, unauthorized, and success states.

Acceptance criteria:

- A new doctor with no patients sees a clear patient-code connection empty state.
- A doctor with a connected patient can create a Clinical Event before adding event-linked care records.
- Recovery plan, imaging, prescriptions, medication schedule, and consultation do not visually compete as unrelated panels.

#### Doctor Resources

Requirements:

- Add a top-level doctor Resources page at `/doctor/resources`.
- Move medical-resource search from the doctor header into a dedicated search bar on that page and remove the unscoped global header search.
- Keep assigned-patient and Clinical Event search inside Patient Management; do not mix patient records with external medical-evidence search.
- Search only the doctor-approved view of the governed medical knowledge base described in `docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`.
- Show publisher, official locator, jurisdiction, original language, publication/review date, version/supersession state, rights/display limits, medical-review state, and patient-use eligibility.
- Support bilingual topic, document-type, organization, jurisdiction, language, audience, date, and current/superseded filters.
- Provide Search, Saved, Recent updates, and Source registry states without copying patient data into the knowledge base.

Acceptance criteria:

- A doctor can verify every result against its original official source and see when newer guidance supersedes it.
- Rights-pending, quarantined, expired, withdrawn, or patient-only-ineligible content cannot leak into the active doctor search index.
- Search telemetry remains metadata-only and does not log raw query text that may contain patient information.

### 11.4 Clinical Events / Care Episodes

Requirements:

- Doctors can create and update Clinical Events for assigned patients.
- Patients can read their own Clinical Events.
- Patients can submit event updates without changing doctor diagnosis fields.
- Event data includes title, chief complaint, symptom summary, diagnosis or provisional diagnosis, onset date, status, timeline, and linked resources.
- Event-linked resources include prescriptions, medication schedules, reminders, recovery plans, imaging, notes, consultations, and activity timeline rows.

Acceptance criteria:

- Event-linked writes validate that the event belongs to the authorized patient.
- Cross-patient and wrong-role probes return neutral denial.
- A doctor can understand a patient's current care around the selected event without scanning unrelated modules.

### 11.5 Medications, Prescriptions, And Reminders

Requirements:

- Doctors can create and update prescriptions inside Clinical Events.
- Prescriptions contain medication name, dose, route, frequency, duration, issue date, instructions, prescribing doctor, and linked Clinical Event.
- Medication schedules represent what the patient should do now.
- Reminders should be generated from medication schedule, refill timing, recovery plan, and follow-up milestones rather than being a disconnected doctor workspace.
- Patients see due/overdue medication tasks and a compact active medication summary.
- Interaction-warning framework should exist before product claims medication safety.
- Barcode scanning remains gated until device/package readiness is approved.

Acceptance criteria:

- Patient-facing medication UI prioritizes current action, not dense metadata.
- Doctor-authored prescriptions link to the active Clinical Event.
- External notification delivery is not implied until SMS/push/email gates are implemented.

### 11.6 Recovery Plans And Today Tasks

Requirements:

- Doctors can create, edit, submit, approve, activate, and complete recovery plans.
- Each active Clinical Event should have at most one active recovery plan.
- Plans include medication, exercise, diet, follow-up, and recovery tasks.
- Patients can complete and uncomplete Today tasks.
- Patient Today view shows progress, remaining tasks, and what happens next.
- Phase 3 may add AI recovery-plan drafts, but the doctor-owned workflow must remain clear.

Acceptance criteria:

- Recovery plans cannot be edited in invalid review states.
- Closing a plan requires required tasks to be complete or explicitly handled.
- The patient dashboard reads as a guided care companion, not a task dump.

### 11.7 Medical Records And Imaging

Requirements:

- Medical records include visit history, diagnoses, prescriptions, imaging metadata/files, doctor notes, and related care context.
- Imaging upload workflow supports Tencent-COS-compatible preparation, completion, status, list/detail readback, and doctor review.
- Imaging must be linked to Clinical Events where possible.
- Doctors can enter manual imaging findings/results.
- The product must not infer clinical findings or make automated imaging claims without validated model gates.
- DICOM viewing and segmentation are optional later scope unless separately approved.

Acceptance criteria:

- Upload status and failure states are clear and recoverable.
- Imaging review metadata is visible to doctor and patient according to role.
- Manual findings are clearly doctor-entered, not AI-generated.

### 11.8 Research-Gated Clinical Evidence Support

Requirements:

- Preserve the existing assessment adapter only as an isolated research and
  evaluation boundary outside the commercial value proposition. Research may
  retain clinical variables, image/CT reference selection, optional genomic
  fields, run status, result history, limitation display, and clinician review.
- Any future multimodal model must remain behind an adapter boundary and may
  not be presented as a Dr. AI diagnosis feature in the commercial product.
- Commercial workflows may use governed evidence support to summarize known
  records, surface missing information, draft questions, and explain reviewed
  care-and-cost facts. It may not establish a diagnosis, medical necessity,
  reimbursement amount, abuse finding, or automatic decision.
- No clinical or utilization claim may be made until the relevant model,
  evidence, validation, privacy, legal, regulatory, and release gates close.

Acceptance criteria:

- Research assessment outputs never enter the commercial care-and-cost
  workflow by default.
- Every assistive output is labeled by origin and review state; unevaluated AI
  fields remain empty rather than showing invented scores.
- Human doctors and payer reviewers retain their respective decisions.

### 11.9 Patient AI Medical Chat

Requirements:

- Patient chat supports educational question preparation, symptom explanation at a safe general level, medication education, and care-plan clarification.
- Emergency red-flag escalation must run before model calls.
- The chat must not provide diagnosis, emergency triage replacement, or medication-change instructions.
- The server must proxy LLM calls and handle timeouts, quota errors, malformed responses, unsafe prompts, and rate limits.
- Conversation history may be stored only with appropriate safety and privacy rules.

Acceptance criteria:

- Red-flag prompts return fixed emergency guidance.
- Unsafe prompts and provider failures return bounded fallback copy.
- Raw prompts, secrets, and raw model output are not written to logs.

### 11.10 Specialist Consultation

Requirements:

- Doctors can request specialist consultation for assigned patients.
- Consultation requests should link to Clinical Events.
- Specialist workflow should include request triage, accept/reject, response, and attachments or structured annotations where feasible.
- Voice/video consultation is a stretch gate.
- Patient visibility should be role-appropriate and avoid bypassing doctor ownership.

Acceptance criteria:

- Current doctor request/status flow remains bounded until specialist UI exists.
- Specialist role remains unavailable until access, UI, and tests are implemented.

### 11.11 Clinic Operations

Requirements:

- Preserved future modules include medicine inventory, equipment, beds,
  ambulance/referral resources, equipment booking, appointments, scheduling,
  hospital information, doctor information, and doctor team management.
- Modules must remain hidden or disabled in production UI until backed by real state, permissions, validation, and tests.

Acceptance criteria:

- No visible production card leads to a placeholder-only workflow.
- Resource and appointment conflicts are handled before launch.

### 11.12 Care-And-Cost Transparency And Payer Review

Requirements:

- Model payer organizations and scoped payer-reviewer memberships separately
  from hospitals, clinics, and government regulators.
- Model synthetic coverage/enrollment with jurisdiction, effective dates,
  member reference, and coverage status; do not place benefit rules or
  identifiers in unstructured metadata when they require validation.
- Create a review case for one patient, Clinical Event, encounter, provider,
  payer, and jurisdiction. A case may contain multiple immutable claim
  submissions or revisions.
- Store itemized service/claim lines with service code system, code, label,
  quantity, unit, service date, currency, billed amount, allowed amount,
  payer-paid amount, patient-responsibility amount, and provenance.
- Store planned care separately from delivered services and claim lines.
- Generate versioned expected-care envelopes containing a range rather than a
  single correct cost, plus source/rule lineage, jurisdiction, effective date,
  confidence, assumptions, and missing information.
- Link envelope items to relevant care categories, expected quantity/range,
  and estimated low/high amounts. Do not require exact one-to-one agreement
  where multiple clinically reasonable pathways exist.
- Emit review alerts with transparent reason codes such as duplicate service,
  unusual quantity or duration, price outside the admitted reference range,
  service-mix difference, or missing documentation. An alert's semantic status
  is `review_recommended`, not `abuse_detected`.
- Let doctors submit versioned explanations and supporting references without
  changing the original claim or AI output.
- Let authorized payer reviewers request information, accept an explanation,
  escalate to another human, or close a review with a reason and audit event.
- Give patients a separate plain-language cost view. Do not expose confidential
  reviewer notes, hidden models, negotiated rates without permission, or
  suspected-fraud labels.
- Preserve legacy invoices/payment status only as optional downstream billing
  summaries; they are not the source of truth for claim review.
- Keep live claim submission, eligibility, payment, denial, prior
  authorization, and appeal integrations disabled until their institutional,
  legal, security, and regulatory gates close. The internal states and adapter
  boundaries must still be production-designed and testable with fixtures.

Acceptance criteria:

- A frozen, clinician-reviewed China-first scenario suite can complete the full
  seven-step journey in Section 10.5 without hidden manual database edits. The
  suite must exercise materially different care pathways, justified
  exceptions, price/utilization alert types, and patient-responsibility states.
- Every displayed number identifies currency, amount type, provenance, and
  effective date; totals reconcile exactly to their line items.
- Payer access is organization- and case-scoped; doctors and patients cannot
  see reviewer-only content.
- Every alert shows its input comparison, rule/reference version, uncertainty,
  and available human action.
- No automated action changes clinical care, claim state, coverage, payment,
  or a clinician's standing.
- Analytics distinguish potential savings or flagged amount from confirmed
  savings. Synthetic demonstration results are never reported as real-world
  impact.

### 11.13 Admin And Support

Requirements:

- Admin dashboard should support user management, hospital/clinic management, audit-event search, system status, and support/deletion/feedback queue handling.
- Public unauthenticated privacy/support route and authenticated in-role support submissions should coexist.
- Support actions must be audited and status-tracked.

Acceptance criteria:

- Admin routes fail closed until implemented.
- A patient or doctor can submit and read their own request status.
- Admin queue operations cannot leak private user data across roles.

## 12. UX And Product Quality Requirements

The Phase 2.5 product-quality gate was mandatory before Phase 3 AI work and is
recorded complete in the implementation plan. Its standards remain regression
requirements throughout Phase 3.

Requirements:

- Replace prototype-like typography, spacing, hierarchy, and generic visual treatment with a calm, premium healthcare interface.
- Define a production font strategy for English and Simplified Chinese.
- Make avatar/profile setup obvious and familiar.
- Make patient onboarding human, guided, and mobile-first.
- Make doctor patient management dense enough for clinical work but calm enough to scan.
- Make payer review data-dense but explainable: show the compared line, range,
  reason code, source date, clinician response, and human next action together.
- Replace normal-flow "synthetic", "demo", "fixture", and "seed" wording with professional user-facing copy.
- While live-use gates remain open, keep one persistent, professional
  environment-level disclosure that the active environment uses
  synthetic/de-identified data and is not for clinical or reimbursement use;
  do not scatter developer/test vocabulary through normal workflow copy.
- Every major empty state must explain what is missing, why it matters, what the next action is, and who owns it.
- Verify important flows through screenshots and first-use walkthroughs, not only automated tests.

Definition of done:

- A new patient can sign up, complete profile basics, find profile settings, share a patient code, and understand next steps.
- A new doctor can sign up, connect a patient, and start a Clinical Event without seed data.
- Screenshots look credible enough to show externally.
- Patient and doctor experiences feel like one coherent product.
- Patient, doctor, and payer views clearly distinguish AI-generated,
  doctor-reviewed, delivered, submitted, and human-reviewed states.

## 13. Localization Requirements

Dr. AI should target Chinese customers while keeping English support.

Requirements:

- Support Simplified Chinese (`zh_Hans`) and English (`en`).
- Treat Simplified Chinese as the primary production copy path.
- Use Flutter localization with ARB files and generated accessors.
- Keep backend responses machine-readable through stable codes/enums.
- Translate UI labels, actions, status text, validation, empty states, and user-facing errors in Flutter.
- Do not automatically translate user-entered clinical content.
- Use locale-aware date, time, phone, reminder, and status formatting.

## 14. Technical Requirements

### 14.1 Architecture

- Flutter shared app for patient mobile and doctor web/tablet surfaces.
- FastAPI backend with REST APIs.
- PostgreSQL database with Alembic migrations.
- Tencent Cloud for staging and later production infrastructure.
- LLM/AI calls routed through the backend, never directly from the client.
- Same-origin hosting preferred for web/API staging.
- Jurisdiction adapters must isolate Chinese coding/payment references from any
  future U.S. coding, contracted-rate, and claim rules.
- Deterministic arithmetic, authorization, rule evaluation, totals, and state
  transitions remain server-owned. An LLM may draft an explanation or
  structured candidate envelope but may not calculate authoritative totals or
  execute clinical, claim, coverage, or payment actions.

### 14.2 Security And Privacy

Requirements:

- HTTPS outside local development.
- JWT access tokens with short expiry.
- Rotating opaque refresh tokens stored server-side as hashes.
- Role-based access control.
- Neutral cross-patient denials.
- Metadata-only audit logs.
- No secrets, tokens, real patient data, raw prompts, raw model output, filenames, object keys, upload URLs, or clinical content in logs.
- Secure backup and restore rehearsal before production.
- No real patient data until privacy, consent, security, and legal gates are closed.
- Payer access requires organization-scoped authorization, purpose limitation,
  least-privilege fields, and case-level audit events.
- Reviewer-only notes, confidential rate data, and internal alert features must
  not leak to patient or doctor views.

AES-256 encryption and OAuth from the original PRD remain product/security considerations, but implementation should be driven by actual platform needs, threat model, and compliance requirements rather than checkbox claims.

### 14.3 Reliability And Observability

Requirements:

- Health endpoint for service availability.
- Monitoring for API 5xx, auth failures, chat/model failures, upload issues, and assessment/AI workflow errors.
- Crash/error tracking for app surfaces.
- Clear staging and production separation.
- Runbooks for deployment, rollback, backup, restore, and environment recreation.
- Model/rule/reference releases used by an envelope or alert must be immutable
  and reproducible after activation or rollback.

### 14.4 Performance

Initial production targets:

- Authenticated API reads should feel interactive on ordinary clinic networks.
- Doctor patient workspace should load section data progressively and avoid whole-screen blocking when possible.
- Patient mobile dashboard should remain responsive under text scaling and phone-width layouts.
- AI calls must provide loading, timeout, retry, and fallback states.
- Itemized monetary totals and patient responsibility must render without
  floating-point rounding and remain usable even when AI providers are offline.

## 15. Data Requirements

Primary entities:

- User
- PatientProfile
- DoctorProfile
- CareRelationship
- ClinicalEvent
- ClinicalEventUpdate
- MedicalRecord
- MedicalHistoryReview
- Allergy
- ChronicDisease
- VisitHistory
- Diagnosis
- DoctorNote
- Medication
- Prescription
- PrescriptionMedication
- MedicationReminder
- Notification
- MedicalImagingAsset
- SimulatedAssessment / future AssessmentRun
- RecoveryPlan
- RecoveryTask
- ChatThread
- ChatMessage
- ConsultationRequest
- SupportRequest
- DeletionRequest
- FeedbackRequest
- Hospital
- Clinic
- RoleAssignment
- DoctorTeam
- ClinicResource
- Equipment
- Appointment
- Booking
- Invoice
- PaymentStatus
- RevenueSummary
- AnalyticsEvent
- AuditEvent
- PayerOrganization
- PayerMembership
- CoverageEnrollment
- CareEncounter
- CarePlanItem
- CareScenarioDefinition
- Claim
- ClaimLine
- PricingReferenceSet
- PricingReferenceItem
- UtilizationRuleSet
- UtilizationRule
- ExpectedCareEnvelope
- ExpectedCareEnvelopeItem
- VarianceAlert
- ClinicianRationale
- PayerReview
- ReviewStateTransition

Data principles:

- Patient-owned identity and history must be separated from doctor-authored clinical judgments.
- Doctor amendments must preserve original patient-entered content.
- Event-linked resources must validate event ownership.
- Seeded data may exist for smoke/regression but must not define the normal user journey.
- Monetary values use integer minor units with explicit ISO currency; ranges
  store low and high values under one currency.
- Clinical records, planned care, delivered services, claims, AI suggestions,
  alerts, explanations, and human decisions are independently versioned and
  must never overwrite one another.
- Claim and envelope totals are derived and validated against immutable line
  items; revisions append a new version rather than mutating submitted history.
- Every rule, price reference, envelope, alert, rationale, and review carries
  jurisdiction, provenance, version/effective time, and actor or system origin.

## 16. AI Requirements

AI agents planned:

- Medical Chat Agent for bounded patient education.
- Radiology / lung-cancer prediction agent based on the user's research model, gated until runnable and validated.
- Medication Safety Agent for interaction warnings, gated until data source and safety rules exist.
- Recovery Planning Agent for draft care-plan generation, gated until doctor review workflow and product-quality gate are complete.
- Expected-Care Drafting Agent for producing a bounded, structured candidate
  envelope from admitted rules and references; a deterministic service
  validates every code, range, source, and arithmetic field.
- Variance Explanation Agent for translating deterministic comparisons into
  patient-, doctor-, or reviewer-appropriate explanations. It does not decide
  whether care was necessary or abusive.

AI safety principles:

- AI is assistive, not autonomous.
- Emergency escalation comes before model calls.
- Doctor review is mandatory for diagnosis and treatment-impacting outputs.
- Model provenance, limitations, and simulated/validated status must be visible.
- AI workflows must be audited without storing raw sensitive content in logs.
- AI must output ranges, assumptions, missing information, and source IDs when
  estimating care or costs; unsupported codes or amounts fail closed.
- Deterministic duplicate, quantity, price-range, documentation, and total
  checks precede any generative explanation.
- AI cannot automatically deny, pay, reduce, escalate, or close a claim; alter
  care; label abuse/fraud; or rank clinicians.

## 17. Success Metrics

Product readiness metrics:

- New patient can complete first-use profile and doctor-connection flow without help.
- New doctor can connect a patient and create a Clinical Event without seed data.
- Major empty states lead to clear next actions.
- User-facing normal flows avoid prototype/test vocabulary.
- Screenshots pass human review for credibility, hierarchy, and trust.

Workflow metrics:

- Time from doctor login to connected patient workspace.
- Time from connected patient to first Clinical Event.
- Percentage of patients with completed profile basics.
- Percentage of patients with medical-history setup complete.
- Recovery-plan task completion rate.
- Patient update submission rate for active Clinical Events.
- Doctor review completion rate for submitted recovery plans and imaging.

Safety and reliability metrics:

- Cross-role and cross-patient denial test pass rate.
- Audit event coverage for sensitive reads/writes.
- API error rate.
- Chat safety fallback success rate.
- Upload/recovery failure rate.
- No-secrets/no-clinical-content log hygiene checks.

Commercial-readiness metrics:

- Number of hidden/disabled placeholder surfaces remaining.
- Specialist/admin workflow readiness by acceptance criteria.
- Localization coverage by screen and message type.
- Monitoring and backup/restore rehearsal completion.

Demonstration and review-quality metrics:

- Itemized arithmetic reconciliation pass rate: 100%.
- Percentage of alerts with a visible reason code, source/rule version,
  comparison value, uncertainty, and human next action: 100%.
- Cross-payer, cross-patient, and reviewer-note isolation test pass rate: 100%.
- Doctor and payer-reviewer task completion time for the synthetic case.
- Reviewer agreement on whether each frozen case should be surfaced for human
  review, reported separately from final reimbursement or abuse judgments.
- Alert precision/recall on a frozen, expert-labeled synthetic/de-identified
  evaluation set, with false-positive rate reported prominently.
- Patient/doctor/NGO comprehension of planned, actual, covered, and
  out-of-pocket amounts in moderated review.
- Clinician override and explanation rates, treated as calibration evidence
  rather than clinician noncompliance.

No synthetic metric may be presented as realized savings, reduced abuse, or
clinical effectiveness.

## 18. Milestones

### Phase 0: Scope Reconciliation

Status: complete.

Purpose:

- Reconcile original PRD with current product reality.
- Decide what remains v1.0 core, what is gated, and what is deferred.

### Phase 1: Production Data Foundation

Status: complete.

Purpose:

- Add schema foundations for hospitals, clinics, teams, resources, appointments, prescriptions, notifications, billing, analytics, support queues, roles, RBAC, and audit foundations.

### Phase 2: Patient And Doctor Core Workflows

Status: complete locally and recorded.

Purpose:

- Implement patient/doctor medical-history, medication, prescription, reminder, imaging, recovery-plan, Today, Clinical Event, patient-code connection, and manual onboarding foundations.

### Phase 2.5: Product Quality And First-Use Readiness

Status: complete in the implementation plan; remains a regression gate.

Purpose:

- Preserve the completed real-product UX quality standard as the product moves
  toward production-ready three-party workflows.
- Close onboarding, profile/avatar, typography, empty-state, copy, and screenshot readiness gaps.

### Phase 3: AI Systems

Status: substantial local work preserved; prior commercialization gate
superseded by the 2026-07-22 direction decision.

Purpose:

- Preserve and finish the bounded capabilities needed by the new platform:
  governed evidence, provenance, structured output,
  deterministic safety, question-bounded context, doctor Resources, and safe
  patient explanation. Do not treat completion of the former chatbot
  commercialization backlog or the 2026-08-12 target as a prerequisite for the
  re-scoped v1.0 product.

### Phase 4: Payer And Multi-Scenario Data Foundation

Status: in progress locally; the first care-and-cost vertical slice is
implemented, while the expanded multi-scenario foundation remains open.

Purpose:

- Freeze the three-party intended-use boundary, China-first terminology, and a
  versioned scenario-coverage matrix.
- Preserve the implemented payer role, payer organization/membership,
  event-level care-cost items, submitted request snapshots, human reviews,
  RBAC, audit events, and focused tests as the thin workflow foundation.
- Add payer organization/membership, synthetic coverage, encounter, planned
  care, claim/line, pricing-reference, rule-release, expected-care-envelope,
  alert, rationale, review, and transition models with RBAC and audit tests.
- Define configurable scenario definitions and applicability rules so new
  diseases, encounter types, hospital levels, regions, and payer policies enter
  through reviewed data/releases rather than code forks.
- Preserve clinic-operations tables but defer their full UI unless required by
  the three-party core.

### Phase 5: Three-Party Multi-Scenario Product Workflow

Status: in progress locally; patient cost transparency, doctor cost-item CRUD
and request submission, payer registration, dashboard, queue, detail, and human
review are implemented for the first slice.

Purpose:

- Implement the seven-step journey in Section 10.5 across doctor, payer, and
  patient interfaces.
- Expand the current generic request workflow into governed coverage,
  reference, expected-envelope, variance, clarification, and appeal workflows
  without weakening the existing human-decision boundary.
- Add deterministic totals and variance checks, structured AI drafting and
  explanations, clinician rationale, payer human resolution, and
  patient-readable transparency.
- Validate with a frozen, representative synthetic/de-identified scenario
  suite and keep specialist/admin/legacy billing work outside the critical
  path.

### Phase 6: Production Hardening And Stakeholder Validation

Status: existing UX/localization foundations partially complete; new
three-party validation remains open.

Purpose:

- Complete bilingual copy, security/privacy review, synthetic-data controls,
  reproducible deployment, backup/restore, alert calibration, accessibility,
  and stakeholder walkthrough evidence.
- Run moderated reviews with doctors, NGO members, and prospective payer
  stakeholders across the representative scenario suite. Record findings as
  feasibility and usability evidence, not clinical validation or real-world
  savings.
- Keep public app-store release, real patient/claim use, and live payer
  integration behind a later regulatory and partnership decision.

## 19. Open Questions

1. Which China-first scenario should be the first vertical slice, which
   additional scenario families are required in the v1.0 coverage matrix, and
   which named clinicians will review their pathways and justified exceptions?
2. Should patient registration require phone number only, email optional, or both?
3. Which identity verification path is acceptable for v1.0: invite code, SMS code, manual approval, or a combination?
4. Which Chinese hospital/clinic metadata source should power doctor hospital selection?
5. What is the minimum acceptable specialist workflow for v1.0: text-only response, structured annotation, or attachment-based review?
6. Which public or permissioned Chinese code, fee, DRG/DIP, formulary, and
   utilization-rule references may be used in development, showcases, and
   eventual live deployment, and at what geographic/hospital level?
7. What evidence is required before the lung-cancer prediction model can appear as more than a simulated/non-clinical adapter?
8. Which flows must be mobile-native before release, and which can remain web/PWA first?
9. What privacy/legal wording is required before any external tester uses the product?
10. When should seeded demo data be wiped or separated from staging manual tests?
11. Which party is the first payer persona: government medical-insurance
    reviewer, commercial insurer reviewer, or an NGO/public-interest observer?
12. Which variance categories will be frozen for v1.0, and what clinician-
    reviewed exceptions must prevent false alerts or under-treatment pressure?
13. Which amounts may the patient see, and which negotiated rates or internal
    review notes must remain restricted?
14. What representative frozen synthetic/de-identified evaluation suite,
    coverage matrix, and human-review rubric are sufficient for production
    readiness while keeping clinical effectiveness and live-impact claims
    separately gated?
15. What data-sharing, regulatory, and institutional partnership evidence would
    be required before any live hospital or payer pilot?

## 20. Acceptance Criteria For Production-Ready v1.0

Dr. AI v1.0 is product/engineering production-ready only when:

- Patient and doctor first-use flows work from zero accounts without relying on seeded data.
- Patient identity, profile, avatar, medical history, and doctor connection are clear.
- Doctor patient workspace is organized around Clinical Events and does not feel like unrelated CRUD panels.
- Every visible production module is implemented, intentionally disabled, or removed.
- The payer role and full care-and-cost review journey work across the frozen
  representative scenario suite with no hidden database edits.
- The workflow and schema are scenario-configurable rather than hardcoded to
  one condition, hospital, payer, or synthetic identity.
- Specialist/admin/clinic/legacy-billing surfaces outside the three-party core do
  not appear as fake finished features.
- AI workflows are gated, reviewed, and labeled according to model readiness.
- Expected-care output is a sourced range with assumptions and uncertainty,
  never a single authoritative cost.
- All monetary totals reconcile to immutable line items and identify currency,
  amount type, provenance, and effective date.
- Variance alerts are explainable `review_recommended` signals with clinician
  response and human payer resolution; no automated denial or abuse label is
  possible.
- Patient, doctor, and payer views enforce field-level and case-level access
  boundaries.
- Security, RBAC, audit, and log-hygiene checks pass.
- No real patient data or clinical claims are used before the required gates close.
- Visual quality, typography, empty states, and onboarding pass human screenshot review.
- This PRD, the implementation plan, and the ERD agree on current scope. The
  API contract describes the implemented first payer workflow and must be
  reconciled again in the same slice that adds coverage, claims, references,
  expected-care envelopes, alerts, appeals, or AI review contracts.
- Product/engineering readiness is reported separately from live-use
  authorization. Until external gates close, every showcase states
  synthetic/de-identified data, research/education purpose, and absence of
  clinical, reimbursement, regulatory, or real-world-impact validation.

## 21. Appendix: Original PRD Items Reconciled

The original Word PRD included authentication, patient profiles, medical records, AI diagnosis, specialist consultation, AI medical chat, recovery plans, medication management, clinic resource management, appointment system, billing, analytics, AI agents, security, Flutter, FastAPI, PostgreSQL, DeepSeek, a custom diagnosis model, and Tencent Cloud.

This Markdown PRD preserves those foundations but updates the product
interpretation:

- Authentication, patient profiles, medical records, recovery plans, medication management, educational chat, and doctor/patient workflow are v1.0 core.
- The legacy AI diagnosis concept is not part of the commercial Dr. AI product.
  Its adapter may remain isolated for separately governed research/evaluation;
  it cannot establish diagnosis, treatment, medical necessity, or expected
  cost in the three-party workflow.
- The immediate v1.0 direction is the production-ready, three-party,
  China-first care-and-cost transparency platform defined in this PRD;
  stakeholder showcases are the first validation and partnership channel.
- Specialist, clinic operations, legacy billing, analytics, and admin
  workflows are preserved but must stay hidden or disabled until implemented.
- Offline mode, wearables, national EHR integration, and disease surveillance are deferred beyond v1.0 unless the implementation plan is amended.
- The product's immediate priority is a coherent, explainable, human-reviewed,
  multi-scenario platform that joins the existing doctor/patient foundation to
  payer review without overstating what AI, synthetic evidence, or a cost
  variance can prove.
