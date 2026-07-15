---
title: "Dr. AI v1.0 Implementation Plan"
status: "Phase 2 and the Phase 2.5 product-quality gate are complete; Phase 3 Slice 4 retrieval baseline is active"
created: "2026-07-02"
last_updated: "2026-07-15T23:48:00+08:00"
owner: "Harry Cao"
delivery_window: "Production v1.0 phase after completed beta foundation; implementation schedule to be estimated after Phase 1 planning starts"
release_target: "Production/commercial v1.0 after beta foundation; invited beta remains historical milestone"
---

# Dr. AI v1.0 Implementation Plan

This file is the durable source of truth for implementing Dr. AI v1.0. Future chats should read this file before proposing or making implementation changes.

## Source Links

- Product requirements: `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx`
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
| 2026-07-13 | Treat the Phase 3 chatbot as a constrained agentic workflow, not an autonomous medical agent. | DeepSeek-v4-flash is the initial backbone, but deterministic safety, allowlisted tools, evidence sufficiency, citation validation, output policy, and provider-neutral fallbacks remain server-controlled. |

## Current Re-scope: Production v1.0

The 2026-07-02 approved one-month plan is now a preserved historical beta plan, not the full definition of Dr. AI v1.0 completion. The completed beta/demo MVP foundation includes authentication/session handling, seeded dashboards, the doctor-led patient care loop, simulated assessment, recovery plan, patient Today tasks, educational chat, consultation request/status, Tencent staging web/API deployment, Android debug access, beta support surfaces, and mark-only logo assets.

Production/commercial v1.0 is still in progress. v1.0 is complete only when the visible product surfaces are functional production workflows backed by real state, not static cards, demo-only summaries, or partial flows. Existing PRD functionality belongs inside v1.0 production development unless this document explicitly marks it as safety/regulatory gated, technical stretch-gated, or not v1.0.

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

#### E. AI diagnostic workflow

- Complete product workflow for AI diagnostic intake, execution, review, and history.
- If the real lung-cancer model is not runnable and validated, use a clearly labeled non-clinical simulated adapter while keeping the workflow production-quality.
- Preserve the response contract for a future validated model adapter.
- Include input collection, CT/image reference, clinical variables, optional genomic fields, run status, result history, limitations, audit trail, and doctor review.
- Do not make clinical claims until model readiness and regulatory gates are cleared.
- Treat real GCAVE-GAN/AMCM inference as a model-readiness/regulatory gate, not as permission to omit the UI and product workflow.

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

#### K. Billing and analytics

- Billing remains in v1.0 commercial-readiness scope even if full payments/insurance cannot launch immediately.
- The v1.0 billing subset must explicitly include invoices, clinic revenue summaries, payment status, and insurance fields if needed.
- If payments are not launched in v1.0, document exactly which billing subset is included and which payment-account gate remains.
- Analytics must include disease statistics, referrals, recovery progress, revenue if billing is implemented, AI usage, and operational activity.

#### L. Administration

- Admin dashboard.
- User management.
- Hospital/clinic management.
- Audit event read/search.
- System status.
- Support, deletion, and feedback request queue.
- Configuration for registration policy, roles, and clinic metadata.

#### M. Commercial readiness

- Monitoring and alerting.
- Crash/error tracking.
- API 5xx, auth, chat, assessment, and upload monitoring.
- Backup and restore rehearsal.
- Production/staging separation.
- Release signing for Android and iOS.
- TestFlight and Play closed testing when account access exists.
- Tester onboarding.
- Support, feedback, and deletion workflows.
- Privacy/security documentation.
- Deployment/recreation runbook.
- No real patient data until privacy, consent, security, and legal requirements are satisfied.

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

### Production v1.0 Milestone Tracker

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
  - [ ] Implement the bounded patient-chat orchestrator.
    - [ ] Enforce deterministic emergency/prohibited-request routing before
      retrieval or generation.
    - [ ] Allow only server-validated read-only knowledge, selected-care-
      context, question-preparation, navigation, and fixed-escalation tools.
    - [ ] Integrate `deepseek-v4-flash` through the provider-neutral adapter
      with schema-constrained internal output.
    - [ ] Require claim-to-passage support, citation rendering, policy
      validation, and fixed no-evidence/provider/safety fallbacks.
    - [ ] Keep conversation content session-only and telemetry metadata-only
      until the frozen storage/privacy boundary is explicitly amended.
  - [ ] Evaluate a small, replaceable multilingual medical query/reranking
    adapter only after the non-tuned retrieval baseline is frozen.
    - [ ] Use rights-cleared, clinician-reviewed Chinese/English query-passage
      pairs and keep all sealed evaluation cases out of training.
    - [ ] Do not assume hosted DeepSeek-v4-flash accepts a LoRA adapter; keep
      the adapter as an independent service unless weight access and provider
      terms explicitly permit backbone fine-tuning.
  - [ ] Close retrieval, answer-quality, safety/security, usability,
    privacy/legal/provider, load, observability, incident-response, rollback,
    native-Chinese, and medical-review release gates.
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

#### Safety/regulatory gated

- Real clinical claims.
- Real diagnostic model use for patient care.
- Real patient data ingestion before privacy, consent, legal, and security readiness.
- Production clinical deployment.

#### Technical stretch gates

- Live voice/video consultation if real-time infrastructure is not ready.
- Barcode scanning if package/device scope is too large for the production v1.0 release window.
- Full insurance/payment processing if payment accounts and compliance setup are not ready.
- DICOM viewing/segmentation if not required for the initial commercial release.

#### Not v1.0

- National EHR integration.
- Wearables.
- Offline mode if still too large.
- Disease surveillance or broad predictive public-health analytics unless explicitly added to the v1.0 commercial scope.

### Production v1.0 Definition of Done

Production v1.0 is complete only when:

- Every visible dashboard item is functional or intentionally removed/disabled.
- Patient, doctor, specialist, and admin roles each have working production workflows.
- Patient medical history, medical records, medication management, recovery plans, consultation, AI chat, AI diagnostic workflow, resource management, booking, hospital/doctor/team management, analytics, and support/admin workflows are implemented to the agreed v1.0 level.
- All data is persisted through migrations and survives restart/deployment.
- Every major workflow has loading, empty, validation, failure, unauthorized, and success states.
- Cross-role and cross-patient access is blocked and tested.
- Audit logs exist for sensitive operations.
- Monitoring and backup/restore are verified.
- Android and iOS release paths are ready, except where blocked by external account access.
- Tencent staging or production deployment can be recreated from docs.
- No clinical claims are made unless the model/regulatory gate has been cleared.
- No placeholder cards remain in production-facing UI.

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

# Historical Approved Beta Plan

The plan below is preserved as the approved beta/demo MVP plan from 2026-07-02. It documents the completed beta foundation and related closure records, but it is no longer the full definition of production/commercial v1.0 completion.

# Dr. AI v1.0 — One-Month Public Beta Plan

## Summary

Build one responsive Flutter product with:

- Doctor experience optimized for the 1280×832 laptop dashboard.
- Patient experience optimized for the 412×917 mobile dashboard.
- FastAPI backend, PostgreSQL, Tencent COS, and DeepSeek chat.
- One polished “doctor-led care loop”:
  1. Doctor opens a patient record.
  2. Reviews clinical information and demo CT image.
  3. Runs a clearly labeled simulated lung-metastasis assessment.
  4. Reviews the result and creates a recovery plan.
  5. Patient receives the plan, medication reminders, and AI-guided education.
  6. Doctor can submit an asynchronous specialist-consultation request.

The release will be an invited public beta through TestFlight, Android closed testing, and a deployed doctor web application—not a clinically approved product.

Grounding sources: [PRD](/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx), [research paper](/Users/Harry-Cao/Desktop/留学规划/科研/Prediction_of_Lung_Cancer_Metastasis_Risk_Based_on_GCAVE-GAN_Data_Augmentation_and_Multimodal_Feature_Fusion.pdf), and [Figma prototype](https://www.figma.com/proto/8EJikM9M97nVy3R5JLeC0O/Figma-basics?node-id=618-1051).

### Historical beta deferrals

- Real GCAVE-GAN/AMCM inference, clinical claims, or real-patient deployment.
- DICOM viewing, segmentation, genomic-file processing, and generated CT images.
- SMS verification, biometric login, video/voice consultations, live annotations.
- Medication-interaction engine, barcode scanning, billing, appointments, inventory editing, analytics, and offline mode.
- App Store production launch; v1.0 uses invited beta distribution.
- Chinese localization; code is localization-ready, but the initial UI follows the English Figma design.

Historical beta note: resource and analytics cards already present in Figma remained read-only demo summaries for the invited beta only; the current production v1.0 scope above supersedes this.

## Technical Design

### Flutter client

Use a single feature-oriented Flutter codebase targeting web, iOS, and Android.

- Navigation: `go_router` with role-protected routes.
- State and dependency injection: Riverpod.
- Networking: Dio with authenticated refresh and standardized API errors.
- Secure tokens: `flutter_secure_storage`.
- Notifications: `flutter_local_notifications`.
- Models: generated JSON serialization with immutable request/response types.
- Responsive shell:
  - `<600px`: patient bottom navigation.
  - `600–1023px`: compact rail/tablet layout.
  - `≥1024px`: doctor navigation and multi-column dashboard.
- Convert Figma colors, typography, spacing, radii, and reusable cards into central design tokens. Flutter recommends branching layouts by available width instead of device identity. [Flutter adaptive-layout guidance](https://docs.flutter.dev/ui/adaptive-responsive/general)

### Backend and infrastructure

Build a modular FastAPI monolith rather than separate microservices.

- FastAPI container on Tencent Cloud behind HTTPS.
- TencentDB for PostgreSQL with managed backups.
- Tencent COS for demo medical images using short-lived signed URLs.
- Database migrations with Alembic.
- Argon2 password hashing.
- Short-lived access JWT plus rotating refresh token.
- Server-side RBAC and doctor–patient care-relationship checks.
- Structured audit and application logs without medical content or tokens.
- Staging and production environments with separate databases and buckets.
- Redis omitted initially; add it only if distributed rate limiting becomes necessary.

TencentDB handles PostgreSQL installation, replication, storage, and backups, reducing solo-operator work. [TencentDB documentation](https://intl.cloud.tencent.com/document/product/409/4989)

### Core data model

Create these principal entities:

- `User`, `DoctorProfile`, `PatientProfile`, `CareRelationship`
- `MedicalRecord`, `MedicalAsset`, `Medication`
- `AIAssessment`, `RecoveryPlan`, `RecoveryTask`, `Reminder`
- `ChatThread`, `ChatMessage`
- `ConsultationRequest`
- `AuditEvent`

Every patient-owned object carries `patient_id`; every clinical mutation records actor, timestamp, action, and affected object.

### API contract

Provide versioned `/api/v1` endpoints for:

- `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`
- `/me`
- `/patients` and `/patients/{id}`
- `/patients/{id}/records`
- `/patients/{id}/assets/presign`
- `/patients/{id}/assessments`
- `/patients/{id}/recovery-plans`
- `/patient/me/today`
- `/medications` and `/reminders`
- `/chat/threads/{id}/messages`
- `/consultations`
- `/audit-events` for authorized administrators only

Important public types:

```text
UserRole = doctor | patient
AssessmentMode = simulated | validated_model
AssessmentStatus = queued | completed | failed
RiskBand = low | moderate | high
ConsultationStatus = requested | accepted | completed | cancelled
RecoveryPlanStatus = draft | active | completed
```

`AIAssessmentResponse` includes:

```text
assessment_id
mode
risk_band
demo_score
input_completeness
model_version
limitations[]
recommended_next_steps[]
created_at
```

The UI always renders `mode: simulated` as “Research simulation — not for diagnosis.” The score is deterministic from seeded fixture IDs and must never be presented as genuine model output.

### AI safety

The paper reports strong cross-validation results on 143 patients, but there is no runnable checkpoint or external clinical validation. Therefore, v1.0 must not convert its reported 96.88% accuracy into a clinical product claim.

The future model interface will accept:

- CT asset reference.
- Pre-treatment clinical variables.
- Versioned genomic-feature reference.
- Model/version metadata.

Recurrence and survival outcomes will not be used as v1 prediction inputs because they may introduce outcome leakage.

DeepSeek is called only by FastAPI; API keys never enter Flutter. Use `deepseek-v4-flash` from the outset because legacy model names are scheduled for retirement during the development month. [DeepSeek API documentation](https://api-docs.deepseek.com/)

Chat safeguards:

- Do not send names, contact information, raw records, or images to DeepSeek.
- Red-flag symptom detection runs before the LLM and returns a fixed emergency message.
- The model provides education and question preparation, not diagnosis or medication changes.
- Every answer includes provenance and limitations.
- Rate limits, output-length limits, timeout handling, and a safe fallback response are mandatory.

Local simulator policy: keep the daily loop on Flutter web, widget tests, and
CI. Do not load the Android emulator or iOS Simulator for ordinary tasks.
Reserve local simulators for native runtime checks, platform configuration
changes, and beta packaging. If disk space is limited, use physical iOS/Android
devices or CI platform builds as the replacement.

Development storage policy: Android tooling should remain on the PHILIPS-backed
APFS volume. Flutter is configured to use `/Volumes/AndroidAVD/sdk`; the
Android AVD home is `/Volumes/AndroidAVD/avd`; and
`/opt/homebrew/share/android-commandlinetools` is only a compatibility symlink.
Future phases must not reinstall Android SDK, system images, or AVD data onto
the internal disk unless this policy is intentionally revised. iOS should stay
minimal: keep only the simulator/runtime needed for milestone verification and
prefer physical devices or CI when available.

## Verification and Acceptance Tests

### Automated tests

- Backend unit tests for authorization, recovery-plan state, assessment fixtures, and chat escalation.
- API integration tests for every golden-flow endpoint.
- Flutter widget tests for doctor and patient primary states.
- Golden-image tests at 1280×832 and 412×917.
- End-to-end test covering doctor assessment → plan activation → patient task completion.
- Contract test ensuring the simulator and future real model return the same response shape.
- Migration test from an empty database and from the previous staging revision.

### Security and failure scenarios

- Expired/rotated token, wrong role, and cross-patient access attempts.
- Oversized, invalid, or malicious upload.
- DeepSeek timeout, malformed response, quota exhaustion, and unsafe prompt.
- Duplicate plan activation and duplicate notification scheduling.
- Interrupted upload and poor mobile connection.
- Deleted account, revoked care relationship, and stale browser session.
- Audit events generated for all sensitive operations.

### Historical beta definition of done

The invited beta/demo MVP was considered complete when:

- A first-time tester can complete the golden workflow without developer assistance.
- The workflow takes under five minutes with seeded data.
- Doctor and patient layouts match their Figma frames at reference dimensions.
- No P0/P1 defects remain.
- Every AI surface is visibly labeled as educational or simulated.
- No real patient data is required or accepted during beta.
- TestFlight, Android closed testing, and doctor web deployment are independently usable.
- A fresh deployment can be recreated from repository documentation and environment templates.

## Assumptions

- One solo developer has approximately 20 focused working days and uses Codex for implementation and QA.
- The public beta is invitation-based and uses synthetic/de-identified demonstration content only.
- The same Flutter repository serves doctor web and patient mobile experiences.
- Existing Figma styling remains authoritative; no visual redesign is planned.
- English is the v1 interface language, with localization infrastructure added from day one.
- The research model remains a simulated adapter until source code, weights, preprocessing logic, and independent validation become available.
- If the schedule slips, specialist consultation is reduced to a single request form before any golden-flow functionality is cut.

---

## Progress and Change Log

Add one row whenever implementation status, scope, architecture, or a major decision changes.

| Date | Status | Change | Evidence / Files | Next Step |
|---|---|---|---|---|
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
