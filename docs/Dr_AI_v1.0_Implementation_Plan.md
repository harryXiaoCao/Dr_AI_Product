---
title: "Dr. AI v1.0 Implementation Plan"
status: "In Progress - Week 1 (Days 1-2 complete)"
created: "2026-07-02"
last_updated: "2026-07-04T12:11:19+08:00"
owner: "Harry Cao"
delivery_window: "One month / 20 focused working days"
release_target: "Invited public beta"
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

## Weekly Milestone Tracker

- [ ] Week 1: Foundation and design freeze
  - [x] Days 1-2: foundation, implementation-facing design freeze, and API contract
  - [ ] Days 3-5: data/auth shells, seeded dashboards, and Week 1 gate
- [ ] Week 2: Complete the golden care loop
- [ ] Week 3: Recovery, reminders, chat, and consultation
- [ ] Week 4: Hardening and beta release
- [ ] Final acceptance criteria verified
- [ ] `v1.0.0-beta.1` tagged and released

---

# Approved Plan

The plan below is preserved unchanged from its approval on 2026-07-02.

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

## v1.0 Product Boundary

### Included

- Email/password authentication, secure session refresh, logout, and doctor/patient roles.
- Doctor dashboard matching the existing Figma layout.
- Patient mobile dashboard matching the existing patient frame.
- Patient list, profile, medical history, notes, medications, and uploaded demo images.
- Presigned image upload to Tencent COS.
- Simulated multimodal lung-risk assessment with reproducible fixture results.
- Recovery-plan creation and patient daily task view.
- Medication schedules and local mobile notifications.
- DeepSeek-powered educational chat with emergency escalation rules.
- Asynchronous specialist-consultation request with status tracking.
- Audit log for sensitive reads, writes, uploads, assessments, and chat escalation.
- Synthetic demonstration patients and onboarding walkthrough.

### Explicitly deferred

- Real GCAVE-GAN/AMCM inference, clinical claims, or real-patient deployment.
- DICOM viewing, segmentation, genomic-file processing, and generated CT images.
- SMS verification, biometric login, video/voice consultations, live annotations.
- Medication-interaction engine, barcode scanning, billing, appointments, inventory editing, analytics, and offline mode.
- App Store production launch; v1.0 uses invited beta distribution.
- Chinese localization; code is localization-ready, but the initial UI follows the English Figma design.

Resource and analytics cards already present in Figma remain read-only demo summaries.

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

## Four-Week Build Schedule

### Week 1 — Foundation and design freeze

**Days 1–2**

- Create Flutter and FastAPI projects, environment configuration, linting, tests, and CI.
- Inspect both Figma frames in detail when the connector limit resets.
- Produce the screen inventory, interaction map, design tokens, and reusable component list.
- Freeze the golden workflow and API contract.

**Days 3–4**

- Implement database schema, migrations, synthetic seed data, and authentication.
- Add role authorization and doctor–patient relationship enforcement.
- Build responsive application shells and login states.

**Day 5 gate**

- Doctor can sign in on web and patient can sign in on mobile.
- Both dashboards render seeded data at the two Figma reference sizes.
- CI builds Flutter web, runs Flutter tests, and runs backend tests.
- Staging API and database are reachable over HTTPS.

### Week 2 — Complete the golden care loop

**Days 6–7**

- Patient search/list, profile, medical history, medications, and doctor notes.
- Loading, empty, validation, unauthorized, and network-error states.

**Days 8–9**

- Presigned demo-image upload.
- Assessment form and deterministic simulated assessment service.
- Risk-result screen with simulation label, limitations, and audit events.

**Day 10 gate**

- Doctor can complete patient → record → upload → assessment → result.
- No client can access an unrelated patient by changing an ID.
- Upload and assessment failure states recover without losing form data.

### Week 3 — Recovery, reminders, chat, and consultation

**Days 11–12**

- Doctor recovery-plan editor.
- Patient “Today” view with medication, exercise, diet, and follow-up tasks.
- Completion tracking and local medication notifications.

**Days 13–14**

- DeepSeek chat proxy, streaming response UI, red-flag escalation, rate limiting, and safe fallbacks.
- Asynchronous specialist-consultation request and status display.

**Day 15 gate**

- Full doctor-led loop works across two accounts.
- Patient immediately sees the activated plan.
- Chat never exposes system prompts, secrets, or another patient’s data.
- Existing Figma resource cards remain visually present but clearly read-only.

### Week 4 — Hardening and beta release

**Days 16–17**

- Accessibility labels, keyboard navigation, contrast, text scaling, and responsive QA.
- Security review, dependency scan, upload validation, audit coverage, and backup restore rehearsal.
- Remove debug logs and verify that logs contain no patient content.

**Days 18–19**

- End-to-end tests on physical iOS and Android devices plus desktop browsers.
- TestFlight build, Android closed-testing bundle, and production Flutter web deployment.
- Beta privacy notice, consent, account deletion, feedback form, and known-limitations page.

**Day 20 release gate**

- Run a complete demo using a clean account and a second device.
- Record a backup demo video.
- Tag `v1.0.0-beta.1`, preserve migrations, seed script, API contract, and release notes.
- Invite a small tester group and monitor crashes, API errors, chat failures, and assessment failures.

Flutter’s official release process supports TestFlight and Android release bundles; signing should be tested before the final week. [iOS release guide](https://docs.flutter.dev/deployment/ios), [Android release guide](https://docs.flutter.dev/deployment/android)

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

### Definition of done

v1.0 is complete when:

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
| 2026-07-02 | In Progress - Week 1 | Implemented Week 1 Days 1-2 foundations: Flutter web/iOS/Android scaffold with role-aware routes and design tokens; FastAPI settings and health endpoint; environment templates; CI; design-freeze inventory and current prototype captures. Figma node metadata remains blocked by the Starter-plan MCP limit, so Week 1 is not complete. | `apps/dr_ai_app/`, `services/api/`, `.github/workflows/ci.yml`, `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/Week_1_Days_1_2_Foundation_Record.md`, `docs/design-evidence/` | Reconcile exact Figma metadata when the quota resets, then begin Week 1 Days 3-4 authentication and data foundations. |
| 2026-07-03 | In Progress - Week 1 | Replaced device-mockup screenshots with direct 1x exports of the doctor and patient Figma frames. Confirmed the patient bottom navigation labels and preserved the Figma file by removing temporary export presets. | `docs/design-evidence/doctor-dashboard-618-1051.png`, `docs/design-evidence/patient-dashboard-663-398.png`, `docs/Dr_AI_v1.0_Design_Freeze.md` | Reconcile exact Figma hierarchy and token metadata after the monthly MCP quota resets. |
| 2026-07-04 | Complete - Week 1 Days 1-2 | Reconciled the design freeze from the authoritative manual Figma inspection; froze the planned v1 API contract; completed Android and iOS toolchains; added a reproducible Unicode-path verification workflow; removed the supported Starlette test-client warning; and verified Flutter web/Android/iOS plus both remote CI jobs. Week 1 remains open for Days 3-5. | `docs/Dr_AI_v1.0_Design_Freeze.md`, `docs/Dr_AI_v1.0_API_Contract.md`, `docs/Week_1_Days_1_2_Foundation_Record.md`, `scripts/verify_flutter.sh`, [draft PR #1](https://github.com/harryXiaoCao/Dr_AI_Product/pull/1), [green CI run](https://github.com/harryXiaoCao/Dr_AI_Product/actions/runs/28676795816) | Begin Week 1 Days 3-4 database, authentication, authorization, and responsive-shell work without expanding the approved scope. |
