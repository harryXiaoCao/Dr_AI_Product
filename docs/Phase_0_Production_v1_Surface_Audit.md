# Phase 0 Production v1 Surface Audit

Recorded: 2026-07-07T13:32:02+08:00; closed:
2026-07-07T16:25:30+08:00

Status: complete for Phase 0. Doctor, patient, specialist, admin, and
support/deletion/feedback visible surfaces have been inventoried, classified,
mapped to PRD modules or production decisions, and closed with final
production-scope decisions in
`docs/Phase_0_Production_v1_Closure_Record.md`.

Branch/worktree evidence: `git status --short --branch` showed
`## main...origin/main` before this note was created. HEAD was `2c4b5c0`.
No code behavior was changed in this pass. The final closure pass updated
documentation only.

## Scope

This audit reconciles the current Flutter surfaces and API/data model against
the production v1.0 rule in `docs/Dr_AI_v1.0_Implementation_Plan.md`: every
visible dashboard card, button, route, and module must either become functional
to the agreed production v1.0 level or be intentionally removed/disabled in
production-facing UI.

Evidence used across the Phase 0 audit slices so far:

- PRD: `/Users/Harry-Cao/Downloads/Dr_AI_Product_Requirements_Document_v1.0.docx`
- Plan: `docs/Dr_AI_v1.0_Implementation_Plan.md`
- API contract: `docs/Dr_AI_v1.0_API_Contract.md`
- Design freeze: `docs/Dr_AI_v1.0_Design_Freeze.md`
- Beta closure records:
  `docs/beta/Week_4_Days_18_20_Release_Closure_Record.md`,
  `docs/beta/v1.0.0-beta.1_Release_Notes.md`, and
  `docs/beta/v1.0.0-beta.1_Deployment_Publishing_Preparation_Record.md`
- Flutter routes and widgets:
  `apps/dr_ai_app/lib/app/routing/router.dart`,
  `apps/dr_ai_app/lib/app/routing/app_role.dart`,
  `apps/dr_ai_app/lib/shared/widgets/responsive_app_shell.dart`,
  `apps/dr_ai_app/lib/features/beta/presentation/beta_support_screen.dart`,
  `apps/dr_ai_app/lib/features/doctor/presentation/doctor_dashboard_screen.dart`,
  `apps/dr_ai_app/lib/features/doctor/presentation/patient_management_screen.dart`,
  `apps/dr_ai_app/lib/features/patient/presentation/patient_dashboard_screen.dart`,
  `apps/dr_ai_app/lib/features/patient/application/patient_care_providers.dart`,
  and `apps/dr_ai_app/lib/features/auth/data/dr_ai_repository.dart`
- Backend endpoints/models:
  `services/api/app/dashboard.py`, `services/api/app/main.py`,
  `services/api/app/auth.py`, and `services/api/app/models.py`
- Tests:
  `apps/dr_ai_app/test/app_test.dart`,
  `services/api/tests/test_week3_chat_consultation.py`, and focused `rg`
  searches across `apps/dr_ai_app/lib`, `services/api/app`, and
  `services/api/tests`.

No live browser screenshots were captured in these Phase 0 documentation
slices because route/widget/API/test inventory was sufficient to classify the
visible and absent role surfaces. Screenshots or golden comparison should be
added if later Phase 0 findings depend on visual details that are not obvious
from code.

## Status Terms

| Status | Meaning |
|---|---|
| Functional | Backed by a route/API/state path and acceptable for production after normal hardening and copy/data cleanup. |
| Partial | Real route/API/state exists, but production v1.0 still needs missing data model, workflow depth, copy changes, role coverage, or hardening. |
| Placeholder | Visible product promise is present but not a functional workflow. |
| Remove/disable | Do not leave visible in production until intentionally implemented or explicitly gated. |

## PRD Module Map

The PRD names Version 1.0 MVP as authentication, medical records, AI medical
chat, AI diagnosis, specialist consultation, recovery plans, and medication
reminders. It separately lists patient profiles, medical records, medication
management, clinic resources, appointments, billing, analytics, specialist
roles, and administrators as platform modules. The updated implementation plan
currently keeps many of those broader modules in production v1.0 unless this
plan later marks them as safety/regulatory gated, technical stretch-gated, or
not v1.0.

## Route Inventory

| Route | Role | Current status | Evidence | PRD mapping | Production v1.0 action needed | Acceptance criteria |
|---|---|---|---|---|---|---|
| `/login` | Public | Partial | `router.dart:35`; `dr_ai_repository.dart:88-142`; `auth.py:95-222` | Authentication | Keep. Add production registration/invite policy, profile/account management, optional SMS/biometric decision, production copy, and account deletion/support submission path. | Login/logout/refresh/session restore work across platforms; registration or invite onboarding is documented and tested; account support/deletion requests persist server-side; wrong credentials stay neutral. |
| `/doctor` | Doctor | Partial | `router.dart:36-44`; `doctor_dashboard_screen.dart:10-82`; `dashboard.py:615-620` | Doctor dashboard, clinic operations, analytics, resource management | Keep only if each visible card below becomes functional or is removed/disabled. Current dashboard payload is a seeded `DashboardSnapshot`, not production state. | Doctor dashboard aggregates real persisted module state, has loading/empty/error/unauthorized states, and contains no inert visible controls. |
| `/doctor/patients` | Doctor | Partial | `router.dart:40-43`; `patient_management_screen.dart:11-205`; `dashboard.py:623-745` | Patient profiles, medical records, medication management | Keep. Promote from synthetic readback and beta care loop to production patient-management workflow. | Doctor can search assigned patients, open profile, view/update allowed profile/medical-history/record/medication/note data, and all access is care-relationship enforced and audited. |
| `/patient` | Patient | Partial | `router.dart:46-49`; `patient_dashboard_screen.dart:13-203`; `dashboard.py:1056-1150` | Patient dashboard, recovery, records, medications, consultation, AI chat | Keep only after placeholder cards and nav labels are resolved. Current route combines real Today/chat/care readback with multiple inert Figma surfaces. | Patient dashboard exposes only functional modules or disabled/gated modules; patient can complete tasks, view allowed records/medications, see consultation status, and understand safety limits. |
| `/beta-support` | Public | Partial | `router.dart:50-53`; beta closure records; release notes | Commercial readiness, privacy/support/deletion/feedback | Convert from beta-support surface to production support/privacy/deletion/feedback workflow or keep as beta-only route outside production navigation. | Support, feedback, deletion, and consent actions submit to a backend queue with status tracking; beta-only wording is removed from production release. |
| `/unauthorized` | Cross-role guard | Functional foundation | `router.dart:54-57`; backend neutral denials in `dashboard.py` | Security/RBAC | Keep. Treat Flutter guard as navigation only; production authority remains server-side. | Wrong-role and cross-patient probes are neutral and tested in Flutter and API paths; no sensitive object existence leaks. |

## Doctor Surface Inventory

| Surface / route | Current status | Evidence | PRD module mapping | Production v1.0 action needed | Acceptance criteria | Notes / safety gate |
|---|---|---|---|---|---|---|
| Doctor top nav: Dashboard | Partial | `responsive_app_shell.dart:21-39`, `245-252`; route `/doctor` | Doctor dashboard | Keep. Ensure dashboard is a real operational overview, not seeded demo payload. | Selecting Dashboard shows production dashboard state and active module summaries. | Currently routes to `/doctor`. |
| Doctor top nav: AI Diagnostic | Placeholder | `responsive_app_shell.dart:23-26`, `245-252` | AI Diagnosis Assistant | Keep only if it routes to diagnostic intake/history/review, or disable until implemented. | Selecting it opens diagnostic workflow with input collection, run status, history, simulation/validated-model labeling, and audit trail. | Currently falls back to `/doctor`. |
| Doctor top nav: AI Recovery Plan | Placeholder | `responsive_app_shell.dart:27-30`, `245-252` | Recovery Plans | Keep only if it routes to recovery-plan review/editor or disable until implemented. | Selecting it opens a real plan queue/editor/history with doctor review/edit/approve. | Current recovery editor exists inside Patient Management only. |
| Doctor top nav: Medical Resources | Placeholder | `responsive_app_shell.dart:31-34`, `245-252` | Clinic Resource Management | Keep only if resources are production v1.0; otherwise remove/disable. | Selecting it opens inventory/equipment/bed/ambulance/referral resource state with CRUD and conflict/status handling. | Currently falls back to `/doctor`; dashboard has read-only summaries. |
| Doctor top nav: Patient Management | Partial | `responsive_app_shell.dart:35-38`, `245-249`; `/doctor/patients` | Patient Profiles, Medical Records, Medication Management | Keep and expand. | Route is functional, backed by API, and supports production patient CRUD/history workflows with audit events. | Best current doctor module. |
| Doctor global search | Placeholder | `responsive_app_shell.dart:205-212`; no search handler | Patient search, resources, cases | Either implement global search across allowed patients/cases/resources or disable. | Search returns scoped results, preserves privacy boundaries, has empty/error states, and never leaks unrelated patients. | Current search bar is visual only. |
| Logout action | Functional foundation | `responsive_app_shell.dart:232-237`; `dr_ai_repository.dart:121-142`; `auth.py:210-219` | Authentication | Keep. | Logout revokes refresh session server-side when possible and always clears local token. | Already verified in beta smoke records. |
| Hospital identity card | Placeholder | `doctor_dashboard_screen.dart:92-164` | Hospital/clinic management | Keep only if hospital profile editing is production v1.0. | Hospital info is persisted, editable by authorized roles, audited, and visible in dashboard summary. | `Edit Hospital Info` is disabled with Week 1 copy. |
| Doctor identity card | Placeholder | `doctor_dashboard_screen.dart:166-220` | Doctor information editing, team management | Keep only if profile editing is production v1.0. | Doctor profile fields are persisted, editable by authorized users, and audited. | `Edit Doctor Info` is disabled with Week 1 copy. |
| Quick Access: CT/X-ray/MRI/upload/records/recovery/imaging/equipment tiles | Placeholder | `doctor_dashboard_screen.dart:231-296` | AI Diagnosis, Medical Records, Imaging, Recovery Plans, Resources | Replace with route-backed actions or remove. | Each tile opens the matching workflow or is not visible. | Current tiles are containers, not buttons. |
| Team Management cards and add tile | Placeholder | `doctor_dashboard_screen.dart:299-350` | Doctor team management | Keep only with doctor-team invite/add/remove workflow. | Team members are loaded from persisted clinic/team data; add/remove/edit actions are role-gated and audited. | Add tile is an icon-only inert container. |
| Recent Activities time picker / Cancel / OK | Placeholder | `doctor_dashboard_screen.dart:372-416` | Appointments, scheduling | Remove/disable unless appointment scheduling is implemented. | Activity list and scheduling controls reflect real appointments/tasks, and Cancel/OK perform safe state changes. | Current Cancel/OK are text only. |
| Resource Overview: equipment, medication stocks, staffing, beds | Placeholder | `doctor_dashboard_screen.dart:418-490` | Clinic Resource Management, Medication inventory | Keep only with real resource/inventory state. | Resource cards show persisted inventory/resource status and link to edit/booking/detail workflows. | Current copy says `Read-only synthetic summaries`. |
| Patient search/list | Partial | `patient_management_screen.dart:79-168`; `dashboard.py:623-659` | Patient Profiles | Keep and expand. | Search supports production patient identifiers, pagination, empty/error states, and care-relationship authorization. | Currently synthetic patient search only. |
| Patient profile bundle | Partial | `patient_management_screen.dart:171-285`; `dashboard.py:716-745` | Patient Profiles, Medical Records, Medication Management | Keep and expand. | Doctor can view and update permitted demographics, allergies, chronic diseases, records, diagnoses, prescriptions, medications, notes, and visit history. | Current view is mostly read-only and synthetic. |
| Demo image upload preparation | Partial | `patient_management_screen.dart:288-421`; `dashboard.py:748-799` | Medical Records and Imaging | Replace demo presign with real upload completion or disable in production. | Upload validates file type/size, completes Tencent COS transfer, records asset status, supports retry/failure states, and audits metadata. | Current URL is `demo-upload.invalid`; no real upload completion. |
| Simulated assessment form/history | Partial | `patient_management_screen.dart:423-504`; `dashboard.py:802-911` | AI Diagnosis Assistant | Keep as production-quality simulated adapter until validated model is gated in. | Diagnostic workflow collects required references/variables, records run status/history, labels simulation persistently, and preserves future adapter contract. | Clinical claims remain safety/regulatory gated. |
| Recovery Plan Editor | Partial | `patient_management_screen.dart:551-881`; `dashboard.py:914-1053` | Recovery Plans | Keep and productionize. | Doctor can draft/edit/activate/revise plans; tasks support medication/exercise/diet/follow-up, patient delivery, completion tracking, revision history, reminders, and audit events. | Current default text is beta/synthetic. |
| Specialist Consultation request panel | Partial | `patient_management_screen.dart:884-1069`; `dashboard.py:1225-1305` | Specialist Consultation | Keep as request workflow, but specialist-side response flow is missing. | Doctor can create request; specialist can accept/reject/respond; patient/doctor see status; attachments/annotations are supported or explicitly gated. | Voice/video is a technical stretch gate unless infra exists. |

## Patient Surface Inventory

| Surface / route | Current status | Evidence | PRD module mapping | Production v1.0 action needed | Acceptance criteria | Notes / safety gate |
|---|---|---|---|---|---|---|
| Patient nav: Dashboard | Partial | `responsive_app_shell.dart:41-52`, `253-255`; `/patient` | Patient dashboard | Keep after dashboard cleanup. | Selecting Dashboard shows production patient summary with no inert cards. | All patient nav labels currently route to `/patient`. |
| Patient nav: Contact | Placeholder | `responsive_app_shell.dart:43`, `253-255` | Specialist/doctor consultation | Implement route/section focus or disable. | Selecting Contact opens contact/consultation status and allowed messaging or appointment options. | Currently no separate route. |
| Patient nav: Medical Service | Placeholder | `responsive_app_shell.dart:44-47`, `253-255` | Medical records, imaging, services, appointments | Implement route/section focus or disable. | Selecting Medical Service opens allowed records, imaging, appointments/services, and support states. | Currently no separate route. |
| Patient nav: Recovery Plan | Placeholder | `responsive_app_shell.dart:48-51`, `253-255` | Recovery Plans | Implement route/section focus or disable. | Selecting Recovery Plan opens full active plan/history, task completion, and reminders. | Current plan summary and Today tasks are on `/patient`. |
| Patient Today tasks | Partial | `patient_dashboard_screen.dart:77-89`, `206-305`; `dashboard.py:1056-1129` | Recovery Plans, medication reminders | Keep and productionize. | Patient sees active plan tasks, completes allowed tasks, sync failures are recoverable, and reminders are real or explicitly local-only. | Current notification shell is local demo. |
| Patient Recovery Plan day columns / See More | Placeholder | `patient_dashboard_screen.dart:92-114`, `660-745` | Recovery Plans | Replace seeded summary with real plan/history route or disable See More. | Each day/task reflects active plan data; See More opens full task details/history. | See More is disabled and labeled unavailable. |
| Contact Doctor card | Partial | `patient_dashboard_screen.dart:116-129`, `748-839`; `dashboard.py:1225-1245` | Specialist Consultation, doctor contact | Keep and expand. | Patient sees assigned doctor and consultation status, can access approved contact/support path, and receives status changes. | Status readback exists; patient cannot initiate request. |
| Medical Fee / Pay Now | Placeholder | `patient_dashboard_screen.dart:131-135`, `841-910` | Billing | Remove/disable unless billing subset is accepted for production v1.0. | If kept, invoices/payment status/insurance fields/revenue linkage exist; Pay Now either works through approved payment flow or is hidden. | Current copy says `Visual placeholder only`; Pay Now disabled. |
| Ask Dr. AI chat | Partial | `patient_dashboard_screen.dart:141-147`, `308-485`; `dashboard.py:1153-1222` | AI Medical Chat | Keep and harden. | Chat stores appropriate history, handles red flags before model calls, rate limits/fallbacks safely, shows provenance/limits, and never uses raw records/images. | Current chat is educational and server-proxied. |
| Check Medical Record card | Placeholder | `patient_dashboard_screen.dart:149-173`, `913-981`; own care readback at `556-614` | Medical Records | Replace with full record list/detail route or disable card. | Patient can view allowed records/history with loading/empty/error states and no doctor-only notes. | Card itself is an empty/summary card, not clickable. |
| Check Imaging Results card | Placeholder | `patient_dashboard_screen.dart:149-173`, `913-981` | Medical Records and Imaging | Replace with imaging list/detail route or disable. | Patient can view allowed imaging metadata/results or clear empty state; real image access is controlled and audited. | No imaging endpoint/list/detail is present beyond demo asset metadata. |
| Patient search bar | Placeholder | `patient_dashboard_screen.dart:176-180`; no handler | Patient services/records search | Implement scoped search or remove. | Search returns only allowed patient-owned content and supports empty/error states. | Current SearchBar has no callback. |
| Profile and Medications card | Partial | `patient_dashboard_screen.dart:191-197`, `556-614`; `dashboard.py:1132-1150`, `1308-1317` | Patient Profiles, Medication Management | Keep and expand. | Patient can view/update allowed profile fields, medications, refill/reminder info, and interaction warnings where available. | Current view is read-only synthetic data. |

## Specialist Surface Inventory

| Surface / route | Current status | Evidence | PRD module mapping | Production v1.0 action needed | Acceptance criteria | Notes / safety gate |
|---|---|---|---|---|---|---|
| Specialist Flutter route/workbench | Placeholder / absent | `router.dart:34-58`; `rg --files apps/dr_ai_app/lib/features` shows no specialist feature directory | Specialist Consultation; Hospital Specialists role | Add a specialist workbench in Phase 5 or explicitly gate specialist-facing UI from production. | A specialist can sign in with a specialist role, see assigned consultation requests only, accept/reject/respond, and access only assigned case context. | There is no hidden specialist route in the current Flutter app. |
| Specialist app role parsing | Placeholder / unsafe for future roles | `app_role.dart:1-12`; unknown wire role defaults to doctor | Role-based access | Fix before adding specialist/admin roles. | Unknown or unsupported roles must not default to doctor UI; they should fail closed or route to an explicit unsupported-role state. | This is not an active production leak while the backend only emits doctor/patient, but it becomes a blocker before role expansion. |
| Doctor-created specialist consultation request | Partial | `patient_management_screen.dart:914-1069`; `dashboard.py:1248-1305`; `test_week3_chat_consultation.py` consultation tests | Specialist Consultation | Keep and expand. | Doctor can create safe, synthetic request; specialist can triage/respond; doctor and patient receive status changes; audit events record metadata only. | Current workflow stops at `requested`; no specialist assignment/response path exists. |
| Patient specialist status readback | Partial | `patient_dashboard_screen.dart:799-824`; `dashboard.py:1225-1245` | Specialist Consultation | Keep only with production status lifecycle, or simplify until specialist workflow exists. | Patient sees status for their own request, including accepted/responded/completed states, without seeing unrelated case data. | Current readback is useful but depends on doctor-created request status only. |
| Backend specialist role and assignment model | Placeholder / absent | `models.py:25-28`, `433-458`; `dashboard.py:1225-1305`; API contract says specialist behavior is not otherwise implemented | Specialist Consultation | Add `specialist` role, specialist profile/assignment fields, consultation lifecycle endpoints, and tests. | Specialist access is server-authorized, assigned-only, audited, and neutral for wrong-role/cross-case probes. | Voice/video remains technical stretch-gated unless real-time infrastructure is approved. |
| Specialist design/Figma reference | Placeholder / absent | `Dr_AI_v1.0_Design_Freeze.md` lists only doctor and patient target frames | Specialist Consultation | Create or approve a specialist production surface before implementation, or explicitly gate it. | Specialist workflow has an accepted information architecture, states, and accessibility expectations before Phase 5 implementation starts. | No current Figma frame establishes specialist UI. |

## Admin Surface Inventory

| Surface / route | Current status | Evidence | PRD module mapping | Production v1.0 action needed | Acceptance criteria | Notes / safety gate |
|---|---|---|---|---|---|---|
| Admin Flutter route/dashboard | Placeholder / absent | `router.dart:34-58`; `rg --files apps/dr_ai_app/lib/features` shows no admin feature directory | Administration | Add admin dashboard shell or explicitly gate admin UI from production v1.0 claims. | Admin can access a role-gated dashboard with user management, clinic/hospital management, audit search, system status, and support queues. | No visible admin route or navigation item exists today. |
| Admin app/backend role | Placeholder / absent | `app_role.dart:1-12`; `models.py:25-28`; `auth.py:45-50`, `88-132` | Administration; Authentication | Add `admin` role, invite/onboarding policy, profile/display handling, route guards, and API authorization. | Admin role is created only through controlled onboarding; unsupported roles fail closed; wrong-role probes are tested. | Current auth/register creates only doctor/patient profiles. |
| Audit-event read/search endpoint | Placeholder / reserved | API contract reserves `GET /api/v1/audit-events`; `main.py:72-73` includes only auth/dashboard routers; no `@router.get("/audit-events")` implementation found | Audit logs; Administration | Implement admin-only audit-event read/search or remove the endpoint claim from production readiness. | Admin can search audit metadata without patient-content leakage; pagination, filters, retention, and access logs are tested. | `AuditEvent` model exists, but read UI/API is absent. |
| User management | Placeholder / absent | No admin route, model, endpoint, or tests found for user management beyond auth/session endpoints | Administration | Add user list/detail/disable/invite/role-management workflow or gate it. | Admin can manage users without exposing passwords/tokens and with audit events for every sensitive action. | Deleting users is high-risk and needs explicit policy before implementation. |
| Hospital/clinic management | Placeholder / absent | Doctor dashboard has disabled hospital edit copy; no hospital/clinic production model found beyond `DoctorProfile.hospital_name` | Administration; Clinic operations | Add hospital/clinic models and admin editing workflow or gate it. | Admin can create/edit clinic metadata, with validation and audit trail. | Current hospital identity card is a doctor-dashboard placeholder. |
| System status/admin monitoring | Placeholder / absent | `/health` exists; no admin system-status UI or monitoring surface found | Administration; Commercial readiness | Add read-only system status and monitoring links/summary if kept in v1.0. | Admin can see API/database/status checks and last smoke/backup evidence without secrets. | Production monitoring remains Phase 6 work. |

## Support, Deletion, And Feedback Surface Inventory

| Surface / route | Current status | Evidence | PRD module mapping | Production v1.0 action needed | Acceptance criteria | Notes / safety gate |
|---|---|---|---|---|---|---|
| Public `/beta-support` route | Partial / beta-only | `router.dart:20-22`, `50-53`; `app_test.dart:306-320` | Commercial readiness; Support/deletion/feedback | Convert to production support/privacy/deletion/feedback route, or keep outside production navigation as beta-only. | Public support route has production wording, clear privacy limits, backend submission/status where applicable, and no stale beta promises. | Route is intentionally pre-auth and direct-path reachable. |
| Login `Beta privacy and support` link | Partial / beta-only | `login_screen.dart:154-157`; `router.dart:51-52` | Commercial readiness | Rename or remove for production. | Entry point label matches the production support/privacy experience and does not imply beta status after v1.0 launch. | Current label is correct for beta history, stale for production v1.0. |
| Beta privacy notice | Partial / beta-only | `beta_support_screen.dart:45-67` | Privacy/security documentation | Replace with production privacy/support notice while preserving non-clinical and no-real-data limits until approved. | Notice states data policy, support channels, limitations, and emergency boundaries for the actual production release. | Current copy says invited beta and synthetic-only. |
| Consent checklist | Partial / local-only | `beta_support_screen.dart:69-106`; `app_test.dart:246-250` | Tester onboarding; privacy/consent | Decide whether production needs persistent consent acknowledgement or remove local readiness checklist. | If kept, consent is persisted server-side with user, timestamp, version, and audit event; otherwise production support route does not show fake completion state. | Current state is local widget state only. |
| Account deletion request | Placeholder / local-only | `beta_support_screen.dart:109-143`, `238-249`; release notes say local drafts only | Account lifecycle; support/deletion queue | Replace with backend request queue and status tracking, or hide from production UI until policy is approved. | Deletion request creates a server-side case, verifies identity, records audit metadata, exposes status, and never deletes data immediately without policy. | Current button only sets `_deletionPrepared = true` and shows a local snackbar. |
| Feedback form | Placeholder / local-only | `beta_support_screen.dart:146-185`, `252-260`; release notes say no external message is sent | Support/feedback queue | Replace with backend feedback submission and admin/support queue, or hide from production UI. | Feedback is submitted server-side, rate-limited, sanitized for secrets/patient data, statused, and visible to authorized admin/support staff. | Current button only sets `_feedbackPrepared = true`. |
| Known limitations disclosure | Partial / beta-only | `beta_support_screen.dart:187-209`; release notes known limitations | Commercial readiness; safety gates | Keep a production limitations page but remove stale release-action wording. | Limitations reflect actual production gates: model/regulatory, real data, voice/video, billing, appointments, analytics, release/account gates. | Current limitations include beta publishing actions and no longer map cleanly to production v1.0. |
| Authenticated support shell | Partial | `beta_support_screen.dart:216-230` | Support/deletion/feedback | Decide whether signed-in users access support through their role shell or a neutral support layout. | Signed-in support path preserves role navigation while making support actions clear and backend-backed. | The route can render inside `ResponsiveAppShell`, but no role nav points to it. |
| Backend support/deletion/feedback queue | Placeholder / absent | `rg` found no support/deletion/feedback endpoints or models; `main.py:72-73` includes only auth/dashboard routers | Administration; support/deletion/feedback queue | Add models, migrations, API endpoints, admin/support UI, and tests in Phase 1/5, or explicitly gate. | Requests persist through restart, have statuses, are role-gated, audited, and covered by wrong-role and data-leak tests. | This is the central blocker for treating support/deletion/feedback as production functional. |

## Hidden Route, Model, API, Test, And Design Reconciliation

| Area checked | Verified current state | Evidence | Production implication |
|---|---|---|---|
| Flutter route tree | Only `/login`, `/doctor`, `/doctor/patients`, `/patient`, `/beta-support`, and `/unauthorized` are registered. | `router.dart:34-58`; `rg -n "GoRoute\|path: '/"` | No hidden specialist or admin surface exists. |
| Flutter feature folders | Feature folders are `auth`, `beta`, `dashboard`, `doctor`, `foundation`, and `patient`; no `specialist` or `admin` folder exists. | `find apps/dr_ai_app/lib/features -maxdepth 3 -type d` | Specialist/admin UI must be designed and implemented later, or explicitly gated. |
| Flutter role model | Client enum supports doctor/patient only and defaults unknown role values to doctor. | `app_role.dart:1-12` | Role expansion must fail closed before specialist/admin accounts are introduced. |
| Backend route registration | FastAPI includes only auth and dashboard routers. | `main.py:72-73`; `rg -n "APIRouter\|include_router\|@router"` | No hidden admin/support router exists. |
| Backend roles | SQLAlchemy `UserRole` includes only `doctor` and `patient`. | `models.py:25-28` | Specialist/admin RBAC is a Phase 1/5 blocker. |
| Consultation lifecycle | Consultation rows contain patient, requesting doctor, specialty, summary, priority, status, and safety label; no specialist assignee/response fields. | `models.py:433-458`; `dashboard.py:1225-1305` | Current consultation is request/status readback only. |
| Audit events | `AuditEvent` model exists, but no administrator read/search endpoint is implemented. | `models.py:461-477`; API route search | Admin audit workflows are absent despite API-contract reservation. |
| Tests | Tests cover beta support route/local-only behavior and doctor/patient consultation request/status, not specialist/admin/support queue workflows. | `app_test.dart:223-320`, `677-694`; `test_week3_chat_consultation.py` | Current tests support the partial classifications only. |
| Design/Figma references | Design freeze documents doctor and patient frames only. | `Dr_AI_v1.0_Design_Freeze.md` | Specialist/admin/support production UI needs explicit design approval or documented low-fidelity product acceptance before Phase 5. |

## Stale Beta-Only Assumptions Found

| Location | Stale assumption | Production handling |
|---|---|---|
| `docs/Dr_AI_v1.0_API_Contract.md` | Describes Dr. AI v1.0 as an invited, non-clinical beta. | Keep safety language, but split beta contract status from production v1.0 contract gap list. |
| `docs/Dr_AI_v1.0_Design_Freeze.md` | Calls Medical Fee a non-functional v1.0 placeholder and says only role homes/unauthorized existed in Days 1-2. | Preserve historical design-freeze facts, but do not use them as production permission for visible placeholders. |
| `doctor_dashboard_screen.dart` | Disabled edit actions still say unavailable in Week 1. | Replace with production copy, route-backed actions, or remove. |
| `patient_dashboard_screen.dart` | Pay Now says unavailable in Week 1; Medical Fee says visual placeholder only. | Remove/disable unless production billing subset is implemented. |
| `patient_management_screen.dart` | Recovery plan default text says invited beta workflow validation and synthetic-only instructions. | Replace with production safety copy and real-state workflow while retaining non-clinical model limits. |
| `responsive_app_shell.dart` | Doctor/patient nav labels appear production-like but mostly route to the dashboard. | Add routes/workflows or disable labels until implemented. |
| Release notes and closure records | Correctly identify beta-only deployment, TestFlight/Play/tag/tester gates, and absent modules. | Keep as historical records; production docs should not imply beta completion equals v1.0 completion. |

## Production API And Data-Model Gap List

1. Roles: backend `UserRole` and Flutter `AppRole` currently support only `doctor` and `patient`; Flutter also defaults unknown wire roles to doctor. Production needs explicit `specialist` and `admin` roles, fail-closed unsupported-role handling, route guards, API authorization, and tests.
2. Account lifecycle: registration/invite exists in the contract, but production needs profile management, support/deletion request persistence, SMS/biometric decisions, and possibly OAuth decision documentation.
3. Patient profile depth: current `PatientProfile` has display name and synthetic identifier only; production needs demographics, allergies, chronic diseases, medications, medical history, visit history, diagnoses, prescriptions, and patient-editable fields where allowed.
4. Medical records: current records/medications/notes are mostly read-only fixtures; production needs CRUD, diagnoses, prescriptions, visit history, doctor-note create/edit, audit logs, and patient-facing detail views.
5. Imaging and assets: current demo asset presign stores metadata and returns `demo-upload.invalid`; production needs real Tencent COS upload completion, validation, status, retry/failure handling, list/detail, and secure access.
6. AI diagnosis: current endpoint runs deterministic synthetic fixtures; production needs intake fields, CT/image reference selection, clinical variables, optional genomic references, run status/history, review state, audit trail, and a preserved future validated-model adapter boundary.
7. Recovery plans: current plan/task workflow is partial; production needs revision history, richer task scheduling, doctor approval semantics, patient history, real reminder/notification delivery or explicit local-only gate, and safety copy cleanup.
8. Patient chat: current educational chat has safety and provider fallback foundations; production needs conversation-history UX, source/provenance details, operational monitoring, and continued red-flag/rate-limit/fallback hardening.
9. Specialist consultation: current model is request-only; production needs specialist assignment, accept/reject/respond, attachments or structured annotations, patient/doctor status events, and voice/video stretch-gate documentation if not shipped.
10. Medication management: current medications are read-only; production needs CRUD, reminders/refill reminders, interaction-warning framework, barcode stretch-gate decision, and Medication Safety Agent adapter/framework.
11. Clinic operations: no production models for hospital/clinic, teams, medicine inventory, equipment, beds, ambulance, referrals, equipment booking, appointments, scheduling, reminders, or conflict handling.
12. Billing and analytics: visible Medical Fee exists, but there are no invoice/payment/insurance/revenue models or disease/referral/recovery/revenue/AI-usage analytics models.
13. Administration/support: no admin dashboard, user management, hospital/clinic management, audit-event search UI/API, system-status UI, support/deletion/feedback backend queue, or production support route exists.
14. Monitoring/commercial readiness: beta records prepared checklists, but production needs implemented monitoring, backup/restore rehearsal evidence, staging/production separation, release signing, store gates, tester onboarding, and privacy/security documentation.

## Acceptance Criteria Updates For Kept Modules

| Module kept for production v1.0 | Updated acceptance criteria |
|---|---|
| Authentication and account lifecycle | Login/logout/refresh/session restore remain functional; production registration or invite onboarding is implemented; account support/deletion requests persist to backend; SMS/biometric/OAuth are either implemented or explicitly gated. |
| Doctor dashboard | Every visible doctor card/control is route-backed and state-backed, or removed/disabled; dashboard summaries come from production data models and include loading, empty, error, unauthorized, and success states. |
| Patient dashboard | Every visible patient card/control/nav label is route-backed and state-backed, or removed/disabled; no patient-facing beta/demo-only promise remains in production UI. |
| Patient management | Doctor can search assigned patients and view/update allowed profile, history, record, medication, diagnosis, prescription, imaging, and note data with audit events and neutral cross-patient denials. |
| Medical records and imaging | Real record CRUD and secure upload/list/detail workflows exist; Tencent COS upload completion is verified; patient and doctor access boundaries are tested. |
| AI diagnosis workflow | Simulated adapter remains clearly labeled until model/regulatory gate clears; intake, run status, result history, limitations, doctor review, and audit trail are complete. |
| Recovery plans and reminders | Doctor can draft/edit/activate/revise plans; patient can complete tasks and view plan history; reminders/notifications are real or explicitly gated; safety limitations and audit events are present. |
| Patient AI chat | Server-side LLM proxy, red-flag precheck, unsafe-prompt fallback, timeout/quota/malformed fallback, rate limits, conversation history, and limitations/provenance are verified. |
| Specialist consultation | Doctor request, specialist accept/reject/respond, patient/doctor status, attachments or structured annotations, and audit events are implemented; voice/video is implemented or explicitly stretch-gated. |
| Medication management | Medication CRUD, reminders, refill reminders, interaction-warning framework, and medication safety adapter/gate are documented and tested. |
| Clinic operations | Resource, equipment, bed, ambulance, referral, appointment, schedule, hospital info, doctor info, and team management workflows are implemented or removed from visible production UI. |
| Billing and analytics | If visible, billing has invoices/payment status/insurance/revenue summaries; analytics has disease/referral/recovery/revenue/AI usage/operational activity views. Otherwise visible billing/analytics cards are removed/disabled. |
| Admin and support | Admin role/dashboard, user/hospital management, audit search, system status, support/deletion/feedback queues, production support/privacy route, and role configuration are implemented before production v1.0 claims completion. Beta-local support wording and local-only draft controls are removed from production-facing UI. |

## Product Judgment

The current beta/demo MVP is valuable as a care-loop proof, but it should not
be treated as a production v1.0 product. The highest-risk production issue is
not a hidden bug; it is visible over-promising. Doctor and patient dashboards
display multiple modules that look product-ready but route nowhere, have no
handler, or are explicitly synthetic/read-only. Support/deletion/feedback looks
like a user-facing route, but it only prepares local beta drafts. Specialist
and admin roles are PRD-visible but do not have actual product surfaces yet.
The production path should therefore prioritize surface truthfulness before
breadth: either make a visible module real to its acceptance criteria or
hide/disable it with clear gating.

## Final Phase 0 Decisions

### Production module scope

| PRD / product area | Production v1.0 decision | Production UI rule |
|---|---|---|
| Authentication, role routing, session lifecycle | Keep. Production v1.0 needs invite or registration policy, profile/account management, and account support/deletion submission beyond the beta foundation. | Visible login/account surfaces may remain only when backed by server state and neutral failures. |
| Patient profiles, medical history, medical records, imaging metadata, prescriptions, doctor notes | Keep as production core. | Doctor/patient record surfaces stay visible only after CRUD/read workflows, authorization, audit events, and loading/empty/error states exist. |
| AI diagnosis assistant | Keep as production workflow with a simulated adapter until model/regulatory readiness clears. | Visible diagnostic actions must route to intake, run status, result history, limitations, and doctor review; validated-model claims stay gated. |
| Recovery plans, Today tasks, medication reminders | Keep as production core. | Plan/task/reminder UI must be state-backed; demo/local-only notification wording must be removed or explicitly gated. |
| Patient AI chat | Keep as patient education workflow. | Must remain server-proxied, red-flag-first, bounded, monitored, and non-diagnostic. |
| Specialist consultation | Keep for production v1.0, but gate voice/video as a technical stretch item unless real-time infrastructure is approved. | Doctor request UI may remain only when specialist triage/response/status workflows are added or clearly disabled until Phase 5. |
| Medication management and safety | Keep. Barcode scanning is a technical stretch gate; Medication Safety Agent may ship as a framework/adapter if no real drug database is ready. | Medication UI must support CRUD/reminders/refills/interaction-warning state or be hidden. |
| Clinic operations: resources, equipment, beds, ambulance, referrals, appointments, scheduling, hospital/doctor/team management | Keep as production/commercial-readiness scope even though the original PRD roadmap listed much of it after MVP. | Existing dashboard cards/nav labels must be removed/disabled until implemented; no inert resource/team/appointment controls in production UI. |
| Billing and analytics | Keep only as a bounded commercial-readiness subset for v1.0: invoices, payment status, insurance fields if needed, revenue summaries, disease/referral/recovery/AI-usage/operational activity analytics. Full payment processing is account/compliance gated. | Patient `Medical Fee` and analytics/revenue surfaces must be hidden/disabled until backend models and UI exist. `Pay Now` must not be visible as a working claim without an approved payment path. |
| Administration | Keep as required production management scope, but no current admin surface exists. | Admin UI/claims stay absent until role, dashboard, user/clinic management, audit search, system status, and support queues are implemented. |
| Commercial readiness: monitoring, backup/restore, release signing, tester onboarding, privacy/security docs | Keep for production hardening. | These are release gates, not dashboard promises. Do not expose them as user-facing modules unless implemented. |
| Not v1.0 | National EHR integration, wearables, offline mode unless re-approved, disease surveillance, broad public-health analytics. | Keep absent from production UI and docs unless the plan is explicitly amended. |

### Support, deletion, and feedback shape

Production v1.0 should use a combined shape:

- Public unauthenticated route: keep a production renamed successor to
  `/beta-support` for privacy, limitations, emergency boundaries, and a low-risk
  contact path. It must not expose patient-specific status before
  authentication.
- Authenticated in-role route: keep an in-role support entry for signed-in
  doctors and patients, using the existing role shell pattern only after it is
  renamed away from beta copy and backed by API submission.
- Admin-managed backend queue: required before support, deletion, or feedback
  is production-functional. Requests need models, migrations, status,
  ownership/role checks, rate limiting or abuse controls, audit metadata, and
  admin/support handling.
- Account deletion must be request-based, identity-checked, audited, and
  policy-governed. Production UI must not imply immediate deletion.
- Feedback must be sanitized and stored server-side; the UI must warn against
  secrets and real patient data until real-data governance is approved.

### Specialist and admin design evidence

Specialist and admin production surfaces do not need new Figma evidence before
Phase 5 if written product acceptance criteria and low-fidelity route/state
specifications are approved in the implementation plan. New Figma or visual
design evidence is still required before Phase 5 if the implementation aims
for visual parity with a designed admin/specialist experience, adds complex
multi-panel workflows, or changes the shared navigation/design system beyond
existing doctor/patient patterns.

### Phase 0 closure

The Phase 0 closure record exists at
`docs/Phase_0_Production_v1_Closure_Record.md`. Phase 1 may begin only after a
fresh branch/status check and must start with production data foundation work;
no Phase 1 implementation has started in this documentation closure pass.
