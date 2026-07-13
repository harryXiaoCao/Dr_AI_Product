# Dr. AI Product Requirements Document v1.0

Status: formal production PRD
Owner: Harry Cao
Last updated: 2026-07-13
Primary platforms: Flutter mobile, Flutter web, FastAPI, PostgreSQL, Tencent Cloud
Product stage: production/commercial v1.0 in progress; Phase 2 and the Phase 2.5 product-quality gate are complete, chatbot evaluation is reported complete, and Phase 3 chatbot development planning is active

## 1. Executive Summary

Dr. AI is an AI clinical-copilot application for doctors and patients. The product is designed to help clinicians manage patient care more safely and continuously, while helping patients understand and follow their care journey outside the clinic.

The product should not be treated as a generic telemedicine app. Its core value is assisting the doctor-patient workflow across identity, medical history, clinical events, prescriptions, imaging, recovery plans, educational chat, specialist consultation, and eventually AI-assisted diagnosis and care-plan drafting.

The original Word PRD defines a broad healthcare operating-system vision for rural and underserved communities. This Markdown PRD updates that direction against the current repository and implementation plan. In the current product reality, Dr. AI already has a functioning doctor/patient foundation, but production v1.0 is not complete until the visible product feels credible, safe, and commercially usable without relying on seed/demo context.

## 2. Product Vision

Dr. AI should give patients a continuous, understandable care companion and give doctors a structured clinical workspace that reduces fragmented work across profile review, medical history, diagnosis context, prescriptions, imaging, recovery tracking, and patient follow-up.

The long-term vision is to make advanced diagnostic and care-management capability more accessible to smaller clinics and underserved communities. The product should eventually connect local doctors, patients, specialists, AI diagnostic services, and clinic operations in one governed system.

## 3. Positioning

Dr. AI is an AI clinical copilot, not a direct-to-consumer diagnosis bot and not a replacement for licensed clinicians.

The product must communicate three boundaries clearly:

- Doctors remain responsible for clinical judgment, diagnosis, and treatment decisions.
- Patients receive guidance, education, reminders, recovery-plan support, and escalation prompts, not autonomous medical diagnosis.
- AI output remains assistive and non-clinical until model validation, regulatory, privacy, and deployment gates are explicitly closed.

## 4. Source Of Truth And Current Product Reality

This PRD is grounded in:

- The original Word PRD at `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx`.
- The current implementation source of truth in `docs/Dr_AI_v1.0_Implementation_Plan.md`.
- The product-quality gate in `docs/Dr_AI_v1.0_Product_Quality_Gate.md`.
- The Phase 2 patient/doctor progress record in `docs/Phase_2_Patient_Doctor_Core_Progress_Record.md`.
- The API contract in `docs/Dr_AI_v1.0_API_Contract.md`.
- The current Flutter and FastAPI code.

Current verified product state:

- Doctor and patient roles are implemented.
- Specialist and admin roles are reserved in the backend but not yet product-ready.
- Invited registration, login, refresh-token rotation, logout, and role routing exist.
- Patient profile fields, doctor profile fields, avatar URL fields, patient codes, and doctor-patient care relationships exist.
- Doctor-side patient connection by patient-shared code exists.
- Clinical Event / Care Episode is the central Phase 2 workflow object.
- Patient demographics, medical history, allergies, chronic diseases, visit history, diagnoses, doctor notes, medication records, prescriptions, reminders, imaging metadata, recovery plans, patient Today progress, patient event updates, consultation requests, and educational chat have implemented foundations.
- External push, SMS, email, native local notifications, real model inference, real clinical claims, billing operations, analytics dashboards, clinic operations, specialist workflows, and admin workflows are not production-ready.
- The implementation plan records the Phase 2.5 product-quality gate as complete. Phase 3 chatbot development is open, while each AI workflow still requires its own retrieval, medical-review, safety, privacy, legal, provider, and regulatory release gates.

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

Specialists are future v1.0 commercial users. They need to:

- Receive consultation requests from doctors.
- Review structured patient context and attachments/annotations where authorized.
- Accept, reject, or respond to consultation requests.
- Provide structured specialist feedback without bypassing doctor ownership.

Specialist UI is not currently implemented and must remain unavailable until Phase 5.

### 5.4 Administrators

Administrators are future v1.0 commercial users. They need to:

- Manage users, hospitals, clinics, role assignments, and configuration.
- Review audit events and system status.
- Manage support, feedback, and deletion queues.
- Oversee clinic resources, billing, analytics, and operational modules where enabled.

Admin UI is not currently implemented and must remain unavailable until Phase 5.

## 6. Product Goals

1. Make the patient-doctor care workflow understandable from first use.
2. Provide a calm, credible healthcare UX that can be shown to early testers, advisors, and competition judges without explaining away prototype roughness.
3. Make Clinical Events / Care Episodes the organizing concept for doctor work and patient care continuity.
4. Let patients own identity and medical-history setup while doctors review, verify, and amend with audit trails.
5. Keep role-based access, cross-patient isolation, and audit metadata strict.
6. Support AI-assisted diagnosis, recovery planning, medication safety, and education through clearly gated workflows.
7. Preserve a future path to specialist, admin, clinic operations, billing, analytics, and China-market localization without exposing half-built modules as production features.

## 7. Non-Goals And Safety Boundaries

The following are not allowed in production-facing v1.0 until separately approved:

- Real patient data.
- Clinical claims that the product diagnoses, treats, or replaces clinicians.
- Autonomous diagnosis or medication-change instructions.
- Real model inference presented as clinically validated.
- Public release, store upload, tester invite, deployment, account change, or data deletion without explicit approval.
- Specialist/admin access to unfinished workflows.
- Normal-flow UI that presents seeded/demo/test content as the main product experience.

The product may keep a concise staging or beta warning that no real patient data should be entered. That warning should be environment-level and professional, not repeated as distracting "demo" language across every normal workflow.

## 8. Release Scope

### 8.1 v1.0 Production Core

Production v1.0 must include a credible doctor/patient experience:

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

### 8.2 v1.0 Commercial Readiness Scope

These modules remain inside the commercial v1.0 product boundary, but they may be hidden or disabled until implemented:

- Specialist consultation workflow beyond basic doctor request/status.
- Admin dashboard and queue management.
- Clinic resource management.
- Appointment and scheduling workflows.
- Billing subset: invoices, payment status, revenue summaries, and insurance fields if needed.
- Analytics subset: disease statistics, recovery progress, referrals, AI usage, and operational activity.
- Monitoring, backup/restore rehearsal, release signing, and deployment runbook.
- Simplified Chinese and English localization foundation.

### 8.3 Explicit Stretch Or Gate Items

These items require separate readiness decisions:

- Real GCAVE-GAN / multimodal lung-cancer model inference.
- Real clinical deployment and clinical claims.
- Voice/video consultation.
- DICOM viewing and segmentation.
- Barcode scanning.
- Full payment processing.
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
```

The Clinical Event / Care Episode should represent one medical problem or follow-up condition managed over time. One appointment can contain multiple Clinical Events, and one Clinical Event can span multiple encounters.

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

### 11.8 AI Diagnosis Assistant

Requirements:

- AI diagnosis workflow should support intake, clinical variables, image/CT reference selection, optional genomic fields, run status, result history, limitation display, and doctor review.
- The future multimodal lung-cancer prediction model must be behind an adapter boundary.
- If no validated runnable model exists, the system may use a clearly labeled non-clinical simulated adapter while preserving production workflow quality.
- No clinical claim may be made until model readiness, validation, privacy, legal, and regulatory gates are cleared.

Acceptance criteria:

- Phase 3 cannot start until the product-quality gate is closed.
- Every AI result is reviewed by a doctor before affecting patient-facing care.
- The UI distinguishes simulated, educational, and clinically validated outputs.

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

- Future v1.0 commercial modules include medicine inventory, equipment, beds, ambulance/referral resources, equipment booking, appointments, scheduling, hospital information, doctor information, and doctor team management.
- Modules must remain hidden or disabled in production UI until backed by real state, permissions, validation, and tests.

Acceptance criteria:

- No visible production card leads to a placeholder-only workflow.
- Resource and appointment conflicts are handled before launch.

### 11.12 Billing And Analytics

Requirements:

- Billing v1.0 subset should define invoices, payment status, clinic revenue summaries, and insurance fields if needed.
- Full payment processing remains gated until account, legal, and provider readiness are approved.
- Analytics should cover disease statistics, referrals, recovery progress, revenue where billing exists, AI usage, and operational activity.

Acceptance criteria:

- Billing and analytics surfaces are hidden until meaningful data and role access exist.
- Financial workflows do not imply real payment processing before the gate is closed.

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
- Replace normal-flow "synthetic", "demo", "fixture", and "seed" wording with professional user-facing copy.
- Keep only concise environment-level warnings for staging/no-real-data use.
- Every major empty state must explain what is missing, why it matters, what the next action is, and who owns it.
- Verify important flows through screenshots and first-use walkthroughs, not only automated tests.

Definition of done:

- A new patient can sign up, complete profile basics, find profile settings, share a patient code, and understand next steps.
- A new doctor can sign up, connect a patient, and start a Clinical Event without seed data.
- Screenshots look credible enough to show externally.
- Patient and doctor experiences feel like one coherent product.

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

AES-256 encryption and OAuth from the original PRD remain product/security considerations, but implementation should be driven by actual platform needs, threat model, and compliance requirements rather than checkbox claims.

### 14.3 Reliability And Observability

Requirements:

- Health endpoint for service availability.
- Monitoring for API 5xx, auth failures, chat/model failures, upload issues, and assessment/AI workflow errors.
- Crash/error tracking for app surfaces.
- Clear staging and production separation.
- Runbooks for deployment, rollback, backup, restore, and environment recreation.

### 14.4 Performance

Initial production targets:

- Authenticated API reads should feel interactive on ordinary clinic networks.
- Doctor patient workspace should load section data progressively and avoid whole-screen blocking when possible.
- Patient mobile dashboard should remain responsive under text scaling and phone-width layouts.
- AI calls must provide loading, timeout, retry, and fallback states.

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

Data principles:

- Patient-owned identity and history must be separated from doctor-authored clinical judgments.
- Doctor amendments must preserve original patient-entered content.
- Event-linked resources must validate event ownership.
- Seeded data may exist for smoke/regression but must not define the normal user journey.

## 16. AI Requirements

AI agents planned:

- Medical Chat Agent for bounded patient education.
- Radiology / lung-cancer prediction agent based on the user's research model, gated until runnable and validated.
- Medication Safety Agent for interaction warnings, gated until data source and safety rules exist.
- Recovery Planning Agent for draft care-plan generation, gated until doctor review workflow and product-quality gate are complete.

AI safety principles:

- AI is assistive, not autonomous.
- Emergency escalation comes before model calls.
- Doctor review is mandatory for diagnosis and treatment-impacting outputs.
- Model provenance, limitations, and simulated/validated status must be visible.
- AI workflows must be audited without storing raw sensitive content in logs.

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

- Make Dr. AI feel like a real commercial healthcare app before adding more AI.
- Close onboarding, profile/avatar, typography, empty-state, copy, and screenshot readiness gaps.

### Phase 3: AI Systems

Status: development planning active; chatbot evaluation reported complete.

Purpose:

- Add the doctor Resources workspace and governed Chinese/WHO knowledge base; implement bounded retrieval-grounded patient chat using `deepseek-v4-flash` through a provider-neutral adapter; then add separately gated AI diagnostic workflow, AI recovery-plan drafting, Medication Safety Agent framework, and AI audit/safety coverage.

### Phase 4: Clinic Operations

Status: not started.

Purpose:

- Add resource, equipment, appointment, scheduling, hospital, doctor information, and doctor-team workflows.

### Phase 5: Specialist, Admin, Billing, Analytics

Status: not started.

Purpose:

- Add specialist consultation workflows, admin dashboard, support queues, audit read/search, billing subset, analytics subset, and commercial management surfaces.

### Phase 6: Production Hardening And Release

Status: partially started for doctor workspace refactor; broader hardening remains open.

Purpose:

- Complete localization foundation, monitoring, backup/restore, signing, release channels, staging/production separation, tester onboarding, and deployment runbooks.

## 19. Open Questions

1. What exact market should v1.0 target first: rural clinics, school/competition demonstration, small private clinics, or general patient-doctor beta?
2. Should patient registration require phone number only, email optional, or both?
3. Which identity verification path is acceptable for v1.0: invite code, SMS code, manual approval, or a combination?
4. Which Chinese hospital/clinic metadata source should power doctor hospital selection?
5. What is the minimum acceptable specialist workflow for v1.0: text-only response, structured annotation, or attachment-based review?
6. Which billing subset is required for commercial credibility if real payments remain deferred?
7. What evidence is required before the lung-cancer prediction model can appear as more than a simulated/non-clinical adapter?
8. Which flows must be mobile-native before release, and which can remain web/PWA first?
9. What privacy/legal wording is required before any external tester uses the product?
10. When should seeded demo data be wiped or separated from staging manual tests?

## 20. Acceptance Criteria For Production v1.0

Dr. AI v1.0 is product-complete only when:

- Patient and doctor first-use flows work from zero accounts without relying on seeded data.
- Patient identity, profile, avatar, medical history, and doctor connection are clear.
- Doctor patient workspace is organized around Clinical Events and does not feel like unrelated CRUD panels.
- Every visible production module is implemented, intentionally disabled, or removed.
- Specialist/admin/clinic/billing/analytics surfaces do not appear as fake production features.
- AI workflows are gated, reviewed, and labeled according to model readiness.
- Security, RBAC, audit, and log-hygiene checks pass.
- No real patient data or clinical claims are used before the required gates close.
- Visual quality, typography, empty states, and onboarding pass human screenshot review.
- Documentation, API contract, and implementation plan agree on current scope.

## 21. Appendix: Original PRD Items Reconciled

The original Word PRD included authentication, patient profiles, medical records, AI diagnosis, specialist consultation, AI medical chat, recovery plans, medication management, clinic resource management, appointment system, billing, analytics, AI agents, security, Flutter, FastAPI, PostgreSQL, DeepSeek, a custom diagnosis model, and Tencent Cloud.

This Markdown PRD preserves that vision but updates the release interpretation:

- Authentication, patient profiles, medical records, recovery plans, medication management, educational chat, and doctor/patient workflow are v1.0 core.
- AI diagnosis remains a v1.0 product direction. It has passed the Phase 2.5 product-quality prerequisite but remains gated by separate model-readiness, clinical-safety, privacy, legal, and regulatory review.
- Specialist, clinic operations, billing, analytics, and admin workflows remain in v1.0 commercial-readiness scope but must stay hidden or disabled until implemented.
- Offline mode, wearables, national EHR integration, and disease surveillance are deferred beyond v1.0 unless the implementation plan is amended.
- The product's immediate priority is not adding more modules; it is making the existing doctor/patient product feel real, safe, and trustworthy.
