# Dr. AI v1.0 API Contract

Status: historical beta/demo API boundary is implemented for authentication,
Week 1 dashboard reads, Week 2 patient-care, demo-upload,
simulated-assessment, Day 10 polish, Week 3 recovery-plan, Today-task,
completion, educational-chat, and consultation request/readback endpoints;
Week 4 Days 18-20 release-prep surfaces add no API changes. Production v1.0
Phase 1 is complete for production data foundation, route-level RBAC helpers,
fail-closed future-role boundaries, and authenticated support/deletion/
feedback submission plus requester-scoped status reads. Phase 2 patient/doctor
medical-history APIs are implemented for demographics, allergies, chronic
diseases, visit history, diagnoses, doctor notes, medication CRUD,
prescription CRUD, medication/refill reminders, expanded care-bundle readback,
neutral denials, metadata-only audit events, and metadata-only in-app queued
notification records. Phase 2 imaging APIs are implemented for
Tencent-COS-compatible upload metadata, metadata-only upload completion,
imaging list/detail readback, doctor-only review status, neutral denials, and
metadata-only audit events. Phase 2 recovery-plan APIs are implemented for
draft, submit-for-review, request-changes, approve/active, complete, patient
Today progress, neutral denials, and metadata-only audit events. Phase 2
workflow clarification now adds persisted Clinical Event/Care Episode records,
doctor-owned create/update, patient-own read aliases, nullable event links on
core Phase 2 resources, event-linked care-bundle readback, neutral denials, and
metadata-only audit events. Production v1.0 still needs the reserved
specialist, administrator, admin support-queue handling, external notification
delivery, and audit-read workflows before those surfaces can be treated as
available. Phase 3 Slice 1 freezes chatbot governance and shared contracts.
Slice 3 adds a doctor-only authoritative-link catalog route. Slice 4 adds
release-specific doctor and patient retrieval endpoints while keeping the real
WHO/NHC passage corpus inactive until rights and clinician-review approval.
The 2026-07-23 care-and-cost slice adds payer registration and membership,
event-level cost-item CRUD/readback, immutable payer-request snapshots, and an
organization-scoped human review queue. It does not add claims adjudication,
coverage decisions, or AI utilization decisions. The 2026-07-25 Slices B/C
add internal provider-neutral reference persistence and a model-free
deterministic evaluation service, but intentionally add no public HTTP route.
Slice D adds a separate internal schema-constrained expected-care candidate
service and immutable persistence, also without a public HTTP route.

Contract version: `1.1.0`

Recorded: 2026-07-04; authentication models frozen: 2026-07-04; Week 2 Days
6-7 reads added: 2026-07-05; Week 2 Days 8-9 demo upload and simulated
assessment endpoints added: 2026-07-05; Day 10 upload validation and recovery
coverage added: 2026-07-05; Week 3 Days 11-12 recovery-plan and task
completion endpoints added: 2026-07-05; Week 3 Days 13-14 educational-chat
and consultation endpoints added: 2026-07-05; Week 3 Day 15 duplicate
consultation reuse and safety fixture coverage added: 2026-07-05; Week 4
Days 16-17 validation/log-hygiene hardening added: 2026-07-06; Week 4 Days
18-20 release-prep surfaces added no API changes: 2026-07-06; Phase 1
production data-foundation schema, future-role fail-closed boundary, and
authenticated support/deletion/feedback submission/status endpoints added:
2026-07-07; Phase 2 first-slice demographics, allergy/chronic disease,
visit-history, diagnosis, doctor-note, expanded care-bundle, and patient
allowed-update endpoints added: 2026-07-07; Phase 2 medication,
prescription, medication/refill reminder, own-reminder read, and own
metadata-notification endpoints added: 2026-07-07; Phase 2 imaging upload
metadata, completion, list/detail, review, and care-bundle readback endpoints
added: 2026-07-08; Phase 2 recovery-plan review, approval, completion, and
Today progress endpoints added: 2026-07-08; Phase 2 Clinical Event/Care
Episode backend model, endpoints, resource links, and care-bundle readback
added: 2026-07-08; payer identity and the first three-party care-and-cost
workflow added: 2026-07-23; canonical Clinical Service and imaging-procedure
financial workflow added: 2026-07-24; internal governed care-reference
persistence and deterministic engine added without HTTP routes: 2026-07-25

This contract preserves the public HTTP boundary implemented for the historical
Dr. AI v1.0.0-beta.1 demo and records the intended shape of production v1.0
extensions. The current backend exposes the authentication, identity,
assigned-patient, synthetic dashboard, Week 2 patient-care/upload/assessment
routes, Day 10 validation polish, Week 3 Days 11-12 recovery-plan/task routes,
and Week 3 Days 13-14 educational-chat and consultation request/readback
routes identified below. Later real notification delivery, specialist response
workflows, admin-managed support queues, administrator audit reads, and other
administrator workflows remain reserved production gaps and must not be
inferred to be available.

The implemented beta/demo API slice is an invited, non-clinical beta. It uses
synthetic demonstration content only, accepts no real patient data, and
provides no diagnosis or medical advice. Production/commercial v1.0 must keep
those safety limits until model, data, privacy, legal, and regulatory gates
are cleared, but the production release is not complete merely because this
beta contract is implemented.

## Contract interpretation after production re-scope

- Beta guarantees in this file remain preserved for compatibility and
  historical release evidence.
- Reserved paths, enum values, roles, and workflows are production targets or
  compatibility placeholders until implemented, tested, and documented.
- Specialist and administrator behavior is contract direction, not current
  product functionality. Backend enum values now reserve `specialist` and
  `admin`, but registration for those roles fails closed, beta dashboard and
  support-request access are forbidden, and Flutter routes unknown/future roles
  to the unauthorized state instead of doctor UI.
- `GET /api/v1/audit-events` is reserved for an administrator-only production
  audit-search workflow; no current route or admin UI implements it.
- Account deletion, feedback, and support submissions now persist to a backend
  queue for authenticated doctor/patient users with requester-scoped status,
  authorization, and audit metadata. Admin/support handling, queue assignment,
  resolution, and UI remain reserved production gaps.
- Raw Tencent COS file-transfer verification, real notification delivery,
  billing, appointments, clinic operations, analytics, and production
  monitoring remain outside the implemented API boundary unless explicitly
  added in later production phases.

## Transport and representation

- HTTPS is required outside local development.
- JSON is the default request and response representation.
- Timestamps use RFC 3339 UTC strings, for example
  `2026-07-04T08:30:00Z`.
- Resource identifiers are opaque strings. Clients must not infer meaning from
  them.
- Demo upload presign accepts only `image/jpeg`, `image/png`, and
  `application/dicom` metadata up to `10_485_760` bytes. Rate limits and
  cursor pagination limits will be set before their broader production use.
- Secrets, raw tokens, medical content, and real patient data must not appear
  in URLs, logs, fixtures, or error messages.

## Implemented authentication models

Registration accepts patient, doctor, and payer roles after server-side
verification. The role is persisted by the server; Flutter cannot elevate it.
Payer registration additionally creates or joins a synthetic-only organization
record and an active membership for the current local workflow. This is not
verified institutional onboarding.

### `POST /api/v1/auth/register`

Request:

```json
{
  "email": "new.patient@example.com",
  "phone_number": "+8613800000000",
  "password": "user-supplied 8-20 characters",
  "role": "patient",
  "verification_code": "server-issued one-time code",
  "terms_accepted": true,
  "patient_profile": {
    "display_name": "Lin Patient"
  }
}
```

The password must be 8-20 characters. Payer registration supplies
`payer_profile` with `display_name`, `organization_name`, `title`, and one of
`public_payer`, `commercial_payer`, or `observer` as `organization_type`.
Invalid verification returns `403 forbidden`; an existing normalized email or
phone returns `409 conflict`.

### `POST /api/v1/auth/login`

Request:

```json
{
  "email": "patient.demo@example.com",
  "password": "user-supplied password"
}
```

Unknown emails, inactive accounts, and incorrect passwords share the same
neutral `401 unauthenticated` response.

### Login, registration, and refresh response

```json
{
  "access_token": "opaque-access-token",
  "refresh_token": "opaque-refresh-token",
  "token_type": "bearer",
  "expires_in": 600,
  "user": {
    "id": "opaque-uuid",
    "email": "patient.demo@example.com",
    "role": "patient",
    "display_name": "Riley Demo Patient"
  }
}
```

The access token is an HS256 JWT with issuer, audience, subject, role, session,
issued-at, expiry, and unique token ID claims. It defaults to 10 minutes. The
refresh token is a cryptographically random opaque value; only its SHA-256 hash
is stored. Refresh sessions default to 14 days and are server-revocable.

### `POST /api/v1/auth/refresh`

Request:

```json
{
  "refresh_token": "opaque-refresh-token"
}
```

Every successful refresh replaces and revokes the presented token. Reusing a
rotated token revokes its entire session family and returns neutral
`401 unauthenticated`.

### `POST /api/v1/auth/logout`

Request:

```json
{
  "refresh_token": "opaque-refresh-token"
}
```

The request also carries the current bearer access token. Success returns
`204 No Content`. The active refresh session is revoked, and subsequent use of
the access token is rejected by the server-side session check.

### `GET /api/v1/me`

Response:

```json
{
  "id": "opaque-uuid",
  "email": "patient.demo@example.com",
  "role": "patient",
  "display_name": "Riley Demo Patient",
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data."
}
```

## Paths frozen for v1

| Method | Path | Doctor | Patient | Purpose |
|---|---|---:|---:|---|
| `GET` | `/health` | Public | Public | Unversioned service health only |
| `POST` | `/api/v1/auth/register` | Own account | Own account | Create an invited beta account |
| `POST` | `/api/v1/auth/login` | Own account | Own account | Start a session |
| `POST` | `/api/v1/auth/refresh` | Own session | Own session | Rotate a refresh session |
| `POST` | `/api/v1/auth/logout` | Own session | Own session | Revoke the current session |
| `GET` | `/api/v1/me` | Own profile | Own profile | Read current identity and role |
| `GET` | `/api/v1/me/dashboard` | Own dashboard | Own dashboard | Read the current role's synthetic seeded dashboard |
| `GET` | `/api/v1/patients` | Assigned patients | No | List patients in an active care relationship |
| `POST` | `/api/v1/patients/connect` | Patient code supplied by patient | No | Connect an assigned patient by patient code |
| `GET` | `/api/v1/patients/{patient_id}` | Assigned patient | Own record only | Read a patient summary |
| `GET` | `/api/v1/patients/{patient_id}/records` | Assigned patient | Own records only | List medical-record fixtures |
| `GET` | `/api/v1/patients/{patient_id}/medications` | Assigned patient | Own medications only | List medications for one patient |
| `POST` | `/api/v1/patients/{patient_id}/medications` | Assigned patient | No | Create a medication entry |
| `PUT` | `/api/v1/patients/{patient_id}/medications/{medication_id}` | Assigned patient | No | Edit a medication entry |
| `DELETE` | `/api/v1/patients/{patient_id}/medications/{medication_id}` | Assigned patient | No | Delete a medication entry |
| `GET` | `/api/v1/patients/{patient_id}/doctor-notes` | Assigned patient | No | List doctor-facing note fixtures |
| `POST` | `/api/v1/patients/{patient_id}/doctor-notes` | Assigned patient | No | Create a doctor-facing note |
| `PUT` | `/api/v1/patients/{patient_id}/doctor-notes/{note_id}` | Assigned patient | No | Edit a doctor-facing note |
| `DELETE` | `/api/v1/patients/{patient_id}/doctor-notes/{note_id}` | Assigned patient | No | Delete a doctor-facing note |
| `PATCH` | `/api/v1/patients/{patient_id}/profile` | Assigned patient | Own profile | Update allowed demographics |
| `PATCH` | `/api/v1/patient/me/profile` | No | Own profile | Update own allowed demographics |
| `GET` | `/api/v1/patients/{patient_id}/clinical-events` | Assigned patient | Own data | List Clinical Events/Care Episodes |
| `POST` | `/api/v1/patients/{patient_id}/clinical-events` | Assigned patient | No | Create a Clinical Event/Care Episode |
| `GET` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}` | Assigned patient | Own data | Read one Clinical Event/Care Episode |
| `PUT` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}` | Assigned patient | No | Edit a Clinical Event/Care Episode |
| `GET` | `/api/v1/patients/{patient_id}/medical-history-reviews` | Assigned patient | Own data | List audited clinician review overlays for patient-entered history |
| `POST` | `/api/v1/patients/{patient_id}/medical-history-reviews` | Assigned patient | No | Create a verification, correction request, or clinician amendment overlay |
| `GET` | `/api/v1/patients/{patient_id}/allergies` | Assigned patient | Own data | List allergies |
| `POST` | `/api/v1/patients/{patient_id}/allergies` | Assigned patient | Own data | Create an allergy entry |
| `PUT` | `/api/v1/patients/{patient_id}/allergies/{allergy_id}` | Assigned patient | Own data | Edit an allergy entry |
| `DELETE` | `/api/v1/patients/{patient_id}/allergies/{allergy_id}` | Assigned patient | Own data | Delete an allergy entry |
| `GET` | `/api/v1/patients/{patient_id}/chronic-diseases` | Assigned patient | Own data | List chronic diseases |
| `POST` | `/api/v1/patients/{patient_id}/chronic-diseases` | Assigned patient | Own data | Create a chronic-disease entry |
| `PUT` | `/api/v1/patients/{patient_id}/chronic-diseases/{condition_id}` | Assigned patient | Own data | Edit a chronic-disease entry |
| `DELETE` | `/api/v1/patients/{patient_id}/chronic-diseases/{condition_id}` | Assigned patient | Own data | Delete a chronic-disease entry |
| `GET` | `/api/v1/patients/{patient_id}/visit-history` | Assigned patient | Own data | List visit-history entries |
| `POST` | `/api/v1/patients/{patient_id}/visit-history` | Assigned patient | No | Create a visit-history entry |
| `PUT` | `/api/v1/patients/{patient_id}/visit-history/{visit_id}` | Assigned patient | No | Edit a visit-history entry |
| `DELETE` | `/api/v1/patients/{patient_id}/visit-history/{visit_id}` | Assigned patient | No | Delete a visit-history entry |
| `GET` | `/api/v1/patients/{patient_id}/diagnoses` | Assigned patient | Own data | List diagnoses |
| `POST` | `/api/v1/patients/{patient_id}/diagnoses` | Assigned patient | No | Create a diagnosis entry |
| `PUT` | `/api/v1/patients/{patient_id}/diagnoses/{diagnosis_id}` | Assigned patient | No | Edit a diagnosis entry |
| `DELETE` | `/api/v1/patients/{patient_id}/diagnoses/{diagnosis_id}` | Assigned patient | No | Delete a diagnosis entry |
| `GET` | `/api/v1/patients/{patient_id}/prescriptions` | Assigned patient | Own data | List prescriptions |
| `POST` | `/api/v1/patients/{patient_id}/prescriptions` | Assigned patient | No | Create a prescription with medication lines |
| `PUT` | `/api/v1/patients/{patient_id}/prescriptions/{prescription_id}` | Assigned patient | No | Edit a prescription and replace medication lines |
| `DELETE` | `/api/v1/patients/{patient_id}/prescriptions/{prescription_id}` | Assigned patient | No | Delete a prescription |
| `GET` | `/api/v1/patients/{patient_id}/medication-reminders` | Assigned patient | Own data | List medication and refill reminders |
| `POST` | `/api/v1/patients/{patient_id}/medication-reminders` | Assigned patient | No | Create an in-app medication or refill reminder |
| `PUT` | `/api/v1/patients/{patient_id}/medication-reminders/{reminder_id}` | Assigned patient | No | Edit an in-app reminder |
| `DELETE` | `/api/v1/patients/{patient_id}/medication-reminders/{reminder_id}` | Assigned patient | No | Delete an in-app reminder |
| `GET` | `/api/v1/patients/{patient_id}/care` | Assigned patient | Own history only | Read profile, records, medications, prescriptions, reminders, history, and doctor-visible notes |
| `POST` | `/api/v1/patients/{patient_id}/assets/presign` | Assigned patient | Own assets only | Request a short-lived demo upload URL |
| `POST` | `/api/v1/patients/{patient_id}/imaging/presign` | Assigned patient | Own assets only | Prepare Tencent-COS-compatible imaging upload metadata |
| `POST` | `/api/v1/patients/{patient_id}/imaging/{asset_id}/complete` | Assigned patient | Own asset only | Confirm metadata-only upload completion |
| `GET` | `/api/v1/patients/{patient_id}/imaging` | Assigned patient | Own assets only | List imaging upload/review metadata |
| `GET` | `/api/v1/patients/{patient_id}/imaging/{asset_id}` | Assigned patient | Own asset only | Read one imaging metadata record |
| `POST` | `/api/v1/patients/{patient_id}/imaging/{asset_id}/review` | Assigned patient | No | Mark imaging metadata as reviewed or rejected |
| `GET` | `/api/v1/patients/{patient_id}/assessments` | Assigned patient | Own results only | List assessment summaries |
| `POST` | `/api/v1/patients/{patient_id}/assessments` | Assigned patient | No | Run a deterministic simulation |
| `GET` | `/api/v1/patients/{patient_id}/recovery-plans` | Assigned patient | Own plans only | List recovery plans |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans` | Assigned patient | No | Create a draft recovery plan |
| `PUT` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}` | Assigned patient | No | Edit a recovery plan |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/submit-review` | Assigned patient | No | Submit a draft recovery plan for doctor review |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/request-changes` | Assigned patient | No | Return a submitted recovery plan to draft editing |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/approve` | Assigned patient | No | Approve and activate a submitted recovery plan |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate` | Assigned patient | No | Activate a recovery plan |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans/{plan_id}/complete` | Assigned patient | No | Complete an active recovery plan after all tasks are complete |
| `GET` | `/api/v1/patient/me/today` | No | Own data | Read the patient's current active tasks |
| `POST` | `/api/v1/patient/me/tasks/{task_id}/completion` | No | Own active task only | Complete a Today task |
| `DELETE` | `/api/v1/patient/me/tasks/{task_id}/completion` | No | Own active task only | Uncomplete a Today task after an accidental check |
| `GET` | `/api/v1/patient/me/care` | No | Own records, medications, prescriptions, and reminders only | Read own profile, history, medications, prescriptions, and reminders |
| `GET` | `/api/v1/patient/me/clinical-events` | No | Own events only | List own Clinical Events/Care Episodes |
| `GET` | `/api/v1/patient/me/clinical-events/{event_id}` | No | Own event only | Read one own Clinical Event/Care Episode |
| `GET` | `/api/v1/patient/me/clinical-events/{event_id}/updates` | No | Own event only | List patient-submitted updates for one own Clinical Event |
| `POST` | `/api/v1/patient/me/clinical-events/{event_id}/updates` | No | Own event only | Submit a patient update without editing doctor diagnosis |
| `GET` | `/api/v1/patient/me/imaging` | No | Own assets only | List own imaging upload/review metadata |
| `GET` | `/api/v1/patient/me/imaging/{asset_id}` | No | Own asset only | Read one own imaging metadata record |
| `GET` | `/api/v1/medications` | Assigned patient scope | Own data | List own medications |
| `GET` | `/api/v1/reminders` | Assigned patient scope | Own data | List own medication/refill reminders |
| `GET` | `/api/v1/patient/me/notifications` | No | Own data | List own metadata-only in-app notification records |
| `POST` | `/api/v1/chat/threads/{thread_id}/messages` | Authorized thread | Own thread | Send an educational-chat message |
| `POST` | `/api/v1/patient/chat/messages` | Patient | Own question-relevant records only | Run safety-gated patient RAG, including evidence-grounded symptom orientation; return the server-owned urgency route, route-consistent next action, answer sections, material uncertainties, reviewed source cards, and validated context category/provenance/date cards |
| `GET` | `/api/v1/patient/chat/threads` | Patient | Own AI threads only | List patient-owned AI conversations newest first with the minimum retention date |
| `GET` | `/api/v1/patient/chat/threads/{thread_id}` | Patient | Own AI thread only | Restore readable user/assistant history and validated answer metadata; foreign thread IDs return neutral not-found |
| `GET` | `/api/v1/doctor/me/contacts` | Doctor | Own active relationships | List connected patients for doctor Contacts |
| `GET` | `/api/v1/private-chats/{contact_id}/messages` | Doctor or patient | Active mutual care relationship | Read a private conversation |
| `POST` | `/api/v1/private-chats/{contact_id}/messages` | Doctor or patient | Active mutual care relationship | Send a text-only private message |
| `GET` | `/api/v1/consultations` | Authorized cases | Own requests | List consultation requests |
| `POST` | `/api/v1/consultations` | Assigned patient | No | Request asynchronous specialist review |
| `POST` | `/api/v1/support-requests` | Own account | Own account | Submit authenticated support, deletion, or feedback request |
| `GET` | `/api/v1/support-requests` | Own requests | Own requests | Read own support request statuses |
| `GET` | `/api/v1/support-requests/{request_id}` | Own request | Own request | Read one own support request status |
| `GET` | `/api/v1/doctor/resources` | Doctor | No | Search catalog-visible official-link metadata |
| `GET` | `/api/v1/doctor/resources/{source_id}` | Doctor | No | Read governed source details and display-approved original sections |
| `POST` | `/api/v1/retrieval/doctor/resources/search` | Doctor | No | Search active doctor-approved evidence release |
| `POST` | `/api/v1/retrieval/patient/evidence` | No | Own request | Retrieve sufficient patient-approved evidence for Slice 5 |
| `GET` | `/api/v1/audit-events` | Administrator only | No | Reserved production audit metadata read/search; not implemented in beta |

All registration and profile-update `display_name` fields accept trimmed
Unicode text from 1 to 120 characters. A single CJK character is valid; empty
or whitespace-only names remain invalid.

The singular `/patient/me/today` path is intentional and is implemented for
the Week 1 patient dashboard. It represents the
current patient's own view and is distinct from doctor-scoped `/patients`.
`GET /api/v1/patients`, `GET /api/v1/patients/{patient_id}`,
`GET /api/v1/patients/{patient_id}/records`,
`GET /api/v1/patients/{patient_id}/medications`,
`GET /api/v1/patients/{patient_id}/doctor-notes`,
`GET /api/v1/patients/{patient_id}/care`, `GET /api/v1/patient/me/care`,
`GET|POST|PUT /api/v1/patients/{patient_id}/clinical-events[...]`,
`GET /api/v1/patient/me/clinical-events`,
`GET /api/v1/patient/me/clinical-events/{event_id}`,
`POST|PUT|DELETE /api/v1/patients/{patient_id}/medications[...]`,
`PATCH /api/v1/patients/{patient_id}/profile`,
`PATCH /api/v1/patient/me/profile`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/allergies[...]`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/chronic-diseases[...]`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/visit-history[...]`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/diagnoses[...]`,
`POST|PUT|DELETE /api/v1/patients/{patient_id}/doctor-notes[...]`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/prescriptions[...]`,
`GET|POST|PUT|DELETE /api/v1/patients/{patient_id}/medication-reminders[...]`,
`POST /api/v1/patients/{patient_id}/assets/presign`,
`POST /api/v1/patients/{patient_id}/imaging/presign`,
`POST /api/v1/patients/{patient_id}/imaging/{asset_id}/complete`,
`GET /api/v1/patients/{patient_id}/imaging`,
`GET /api/v1/patients/{patient_id}/imaging/{asset_id}`,
`POST /api/v1/patients/{patient_id}/imaging/{asset_id}/review`,
`GET /api/v1/patients/{patient_id}/assessments`,
`POST /api/v1/patients/{patient_id}/assessments`,
`GET /api/v1/patients/{patient_id}/recovery-plans`,
`POST /api/v1/patients/{patient_id}/recovery-plans`,
`PUT /api/v1/patients/{patient_id}/recovery-plans/{plan_id}`,
`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/submit-review`,
`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/request-changes`,
`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/approve`,
`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate`,
`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/complete`,
`POST /api/v1/patient/me/tasks/{task_id}/completion`,
`POST /api/v1/chat/threads/{thread_id}/messages`,
`GET /api/v1/consultations`, `POST /api/v1/consultations`,
`POST /api/v1/support-requests`, `GET /api/v1/support-requests`,
`GET /api/v1/support-requests/{request_id}`, `GET /api/v1/medications`,
`GET /api/v1/reminders`, `GET /api/v1/patient/me/notifications`,
`GET /api/v1/patient/me/imaging`, `GET /api/v1/patient/me/imaging/{asset_id}`,
and `GET /api/v1/me/dashboard` are also implemented. Administrator audit
reads, specialist response workflows, admin-managed support/deletion/feedback
handling, external notification delivery, raw file transfer verification
against Tencent COS, and real clinical workflows remain unavailable.

## Phase 2 patient and doctor core

Phase 2 endpoints add persisted production workflow foundations for
demographics, allergies, chronic diseases, visit history, diagnoses, doctor
notes, medications, prescriptions, medication reminders, refill reminders, and
metadata-only in-app queued notifications, imaging upload/review metadata, and
recovery-plan review/approval/completion semantics. The workflow-clarification
slice adds Clinical Events/Care Episodes as the central Phase 2 care object.
These APIs remain synthetic/de-identified only until real-data privacy,
consent, legal, and security gates are cleared.

Rules:

- Doctors can read and edit only patients in an active care relationship.
- Doctors can create an active care relationship by submitting a patient code
  shared by the owning patient. The connection endpoint stores metadata-only
  audit details and does not copy the patient code into audit metadata.
- Patients can read only their own demographics, allergies, chronic diseases,
  Clinical Events, visit history, diagnoses, records, medications,
  prescriptions, reminders, notification metadata, imaging metadata,
  recovery-plan metadata, and care-bundle data.
- Patient profile updates are idempotent: submitting the current values returns
  the current profile rather than a validation error. Blood type is a persisted
  patient-profile field and accepts `Unknown`, `A+`, `A-`, `B+`, `B-`, `AB+`,
  `AB-`, `O+`, or `O-`.
- The editable medical-profile survey is a singleton attached to the patient
  profile. Blood pressure, smoking/alcohol status, condition details,
  patient-reported medication and history notes, and pregnancy status are
  updated in place and returned for future form prefill. Saving this profile
  does not create a `medical_records` intake-summary row. Clinical Events remain
  separate appendable care episodes and retain their own timelines.
- Patients can update only allowed own-profile fields, allergies, and chronic
  diseases in this slice.
- Doctors create and update Clinical Events/Care Episodes. Patients can read
  their own events but cannot edit event diagnosis summaries or doctor
  diagnosis records.
- Patients can submit separate Clinical Event updates for their own events.
  Those updates appear in event readback and timeline context but do not edit
  doctor-owned diagnosis summaries or diagnosis records.
- Doctor medical-history verification, correction requests, and clinician
  amendments are stored as audited overlays on patient-entered history. They
  do not overwrite the original allergy, chronic-disease, or medical-record
  rows.
- Visit-history, diagnosis, doctor-note, medication, prescription, and
  reminder mutations are doctor-only.
- `clinical_event_id` is optional and nullable on visit history, diagnoses,
  medications, prescriptions, medication/refill reminders, metadata-only
  notifications, recovery plans, imaging assets, doctor notes, and consultation
  requests. When provided, it must belong to the same authorized patient.
- Doctor notes are hidden from patient-owned care-bundle responses, and
  patient probes to doctor-note endpoints return neutral `404 not_found`.
- Medication and refill reminders create or update metadata-only in-app
  notification rows when active; no SMS, email, push, native local
  notification, or external delivery service is called by the backend.
- Imaging upload preparation and completion store metadata only. The backend
  does not call Tencent COS, inspect uploaded files, create clinical
  interpretation, run model inference, or expose object keys after presign.
- Imaging review is doctor-only and records `reviewed` or `rejected` status
  plus optional manual doctor-entered finding/result fields. The backend does
  not inspect files, generate findings, or make automated clinical claims.
- Recovery-plan create, edit, submit-review, request-changes, approve,
  activate-compatible, and complete mutations are doctor-only.
- Recovery-plan edits are allowed only while the plan is draft-editable. Edits
  are blocked while a plan is submitted for review and after approval or
  completion.
- Approval activates the submitted plan, records review/approval timestamps,
  and completes any previous active recovery plan for the same Clinical Event
  while preserving active plans for unrelated Clinical Events.
- Completing a recovery plan requires all active plan tasks to be completed by
  the patient first.
- `GET /api/v1/patient/me/today` returns active plan tasks plus
  `today_progress` with task count, completed count, remaining count, and
  completion percent.
- Wrong-role, unrelated-patient, and cross-patient probes return neutral
  `404 not_found` when existence would leak sensitive information.
- Write and sensitive-read audit events store metadata such as actor role,
  field names, statuses, transition labels, counts, and resource IDs only.
  Audit metadata must not
  copy allergy labels, condition names, visit summaries, diagnosis labels,
  doctor-note titles, note bodies, medication names, dosages, schedules,
  prescription notes, reminder labels, filenames, object keys, upload URLs,
  ETags, checksums, imaging content, recovery-plan titles, plan instructions,
  task titles, task details, notification labels, or other medical content.

Expanded care-bundle responses now include `demographics` under `patient` plus
top-level `clinical_events`, `allergies`, `chronic_diseases`, `visit_history`,
`diagnoses`, `imaging_assets`, `medications`, `prescriptions`,
`medication_reminders`, `recovery_plans`, `medical_history_reviews`, and
`clinical_event_updates`. Event-linked resources include their nullable
`clinical_event_id`. Doctor-scoped care bundles include `doctor_notes`;
patient-owned care bundles return an empty `doctor_notes` list.

Clinical Event create/update requests accept:

```json
{
  "title": "Synthetic care episode title",
  "chief_complaint": "Synthetic chief complaint",
  "symptom_summary": "Optional synthetic symptom summary.",
  "diagnosis_summary": "Optional doctor-entered diagnosis summary.",
  "onset_date": "2026-07-01",
  "status": "active"
}
```

Responses include `id`, `patient_id`, nullable `doctor_id`, the same content
fields, `linked_resource_counts`, `patient_updates`, timestamps, and the
synthetic-data safety label. The linked-resource counts are safe metadata
only; they do not copy medical content. Existing resource create/update
payloads remain compatible when `clinical_event_id` is omitted. The Flutter
doctor Patient Management client now treats the selected Clinical Event as the
active workspace context and sends `clinical_event_id` for medication schedule
saves, prescription issue, medical imaging presign, recovery-plan
create/update, and specialist consultation request calls when an event is
selected.

Clinical Event responses include a derived `timeline` array. Timeline entries
are generated from event-linked resources such as encounter updates,
diagnosis updates, prescriptions, recovery plans, imaging reviews, doctor
notes, consultation requests, and patient-submitted updates. Timeline entries
are supporting workflow context; they are not an automated medical
interpretation.

Medical-history review create requests accept `target_type`
(`allergy`, `chronic_disease`, or `medical_record`), `target_id`, `action`
(`verified`, `amendment`, or `correction_requested`), and the action-specific
`amendment_summary` or `correction_request` text where required. Responses are
separate review rows linked to the original target; source history rows remain
unchanged.

Patient Clinical Event update create requests accept `update_type`
(`symptom_update`, `medication_note`, `recovery_check_in`, or
`general_update`), `summary`, and optional `occurred_at`. Responses are
patient-authored update rows linked to the Clinical Event and are read back in
the event timeline without changing doctor diagnosis fields.

## Public enums

Wire values are lowercase strings.

```text
UserRole = doctor | patient | specialist | admin
AssessmentMode = simulated | validated_model
AssessmentStatus = queued | completed | failed
InputCompleteness = complete | partial | insufficient
RiskBand = low | moderate | high
ConsultationStatus = requested | accepted | completed | cancelled
RecoveryPlanStatus = draft | active | completed
RecoveryPlanReviewStatus = draft | in_review | changes_requested | approved
ClinicalEventStatus = active | monitoring | resolved | entered_in_error
```

`specialist` and `admin` are reserved production roles. Their enum values exist
for Phase 1 RBAC preparation, but they do not grant usable product workflows
until specialist/admin authorization, routes, surfaces, and tests are added.
`validated_model` is reserved for a future independently validated adapter. It
must be rejected in the v1 beta until model code, weights, preprocessing,
governance, and release approval exist. Adding a new enum value is treated as a
contract change and requires client compatibility review.

## Phase 3 chatbot contract foundation

`app/chatbot_contracts.py` freezes rights- and review-gated source admission,
doctor search and patient evidence schemas, structured model output, allowlisted
tools, safety/fallback codes, and metadata-only telemetry. The Slice 4
doctor-search and patient-evidence contracts are enabled endpoints; the later
model/orchestrator contracts remain inactive until Slice 5.

Development inference is synthetic-only. Real patient context remains
fail-closed unless the configured Mainland-China location, field allowlist,
no-training, no-retention, privacy, legal, and product approval gates all pass.
This restriction does not change Dr. AI's production/commercial positioning.

### Generated-answer release readiness

The only enabled v1 generated-answer provider is `deepseek`. Provider
independence is retained only for deterministic tests and product-owned fixed
fallbacks. Generation is fail-closed unless the purpose is enabled, its kill
switch is off, and the active `patient_chat_generated_answer` release has the
exact expected purpose, provider, prompt, schema, contract checksum, release
checksum, and passing machine gates.

Release content and transition events are append-only at the database boundary.
Activation, supersession, and rollback use advisory locking, expected active
version/checksum preconditions, and idempotency keys. Rollback may target only
the active release's exact predecessor. Missing or drifted release state,
provider timeout/quota/outage, or malformed output returns a deterministic
product-owned fallback; emergency routing and unrelated APIs remain available.

## Error envelope

Every non-2xx application response uses this shape:

```json
{
  "error": {
    "code": "forbidden",
    "message": "You do not have access to this resource.",
    "request_id": "req_01J...",
    "details": []
  }
}
```

`message` is safe for display and must not reveal resource existence, patient
content, stack traces, tokens, or internal service details. `details` is an
array of structured field errors and is empty when no field-level information
is safe.

Field errors use:

```json
{
  "field": "mode",
  "code": "unsupported_value",
  "message": "Only simulated assessments are available in this beta."
}
```

Frozen error codes:

```text
bad_request
validation_failed
unauthenticated
forbidden
not_found
conflict
rate_limited
unsupported_media_type
payload_too_large
service_unavailable
retrieval_unavailable
internal_error
```

Recommended HTTP mapping:

| HTTP | Error code |
|---:|---|
| `400` | `bad_request` |
| `401` | `unauthenticated` |
| `403` | `forbidden` |
| `404` | `not_found` |
| `409` | `conflict` |
| `422` | `validation_failed` |
| `413` | `payload_too_large` |
| `415` | `unsupported_media_type` |
| `429` | `rate_limited` |
| `503` | `service_unavailable`, `retrieval_unavailable` |
| `500` | `internal_error` |

Cross-patient and wrong-role access returns a neutral `404 not_found` when
revealing that the resource exists would leak sensitive information.

## Role and ownership boundaries

- Authentication does not grant access to patient-owned data by itself.
- A doctor can access a patient-owned resource only through an active
  `CareRelationship`.
- A patient can access only resources whose `patient_id` is their own.
- A payer can access only requests addressed to the payer organization of their
  active membership. A `payer` role without an active membership receives a
  neutral denial.
- A specialist can access only consultation data explicitly assigned to them;
  specialist behavior is not otherwise implemented in the current beta/demo
  API slice.
- Only an administrator can call the reserved `/api/v1/audit-events` workflow
  after an administrator role, endpoint, and UI are implemented. No
  administrator UI exists in the current beta/demo API slice.
- The server enforces every boundary. Flutter route guards are navigation
  assistance, not authorization.
- Sensitive reads, mutations, uploads, assessments, consultation changes, and
  chat escalations create audit events without copying medical content into
  logs.

## Implemented Three-Party Care-And-Cost Contract

This 2026-07-23 slice is an itemized transparency and human-review workflow,
not a formal claim-adjudication API. Money is CNY integer minor units. AI fields
are nullable and default to `ai_review_status = not_evaluated`; no endpoint in
this slice calculates a necessity, abuse, fraud, coverage, or payment decision.

### Patient and doctor ledger

- `GET /api/v1/patient/me/care-costs`: patient-owned Clinical Event-grouped
  ledger.
- `GET /api/v1/patients/{patient_id}/care-costs`: active treating-doctor
  ledger readback.
- `POST /api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items`:
  legacy generic creation is disabled with `409 integrated_financial_required`;
  create the cost from its price-bearing clinical record instead.
- `PUT /api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items/{item_id}`:
  replace editable fields only on an unlinked historical generic row. A
  clinically linked companion returns `409 integrated_financial_required` and
  must be updated through its medication or Clinical Service workflow.
- `DELETE /api/v1/patients/{patient_id}/clinical-events/{event_id}/care-items/{item_id}`:
  delete only an unlinked historical generic row. A clinically linked
  companion returns `409 integrated_financial_required` and follows its
  source record's archive/delete lifecycle. Existing submitted request-line
  snapshots are retained and their source link becomes nullable if a permitted
  source deletion removes the companion.

The implemented price-bearing sources are medications/products and canonical
Clinical Services. Specialist consultation requests create a one-to-one
`category = consultation` Clinical Service when linked to a Clinical Event;
imaging procedures use `category = imaging`. The doctor-owned Clinical Service
write contract also accepts `laboratory`, `treatment`, `rehabilitation`, and
`other_service`; category is immutable after creation, and imaging alone
requires a body region. Medication create/update, consultation create, and
Clinical Service create/update accept an optional
`financial` object with `pricing_state` (`pending_cost`,
`estimated`, or `final`), optional `service_date`, CNY `currency`,
`total_cost_minor`, `payer_requested_minor`, and
`patient_responsibility_minor`. Pending-cost companions must contain zero
amounts and are patient-visible but submission-ineligible. Estimated/final
companions require a positive total and an exact payer-plus-patient allocation.
`PUT /api/v1/patients/{patient_id}/consultations/{consultation_id}/financial`
supports later completion inside the consultation workflow by resolving its
canonical service. `PUT
/api/v1/patients/{patient_id}/clinical-services/{service_id}/financial`
supports later completion from the service record.

Each active companion has a real nullable foreign key to exactly one medication
or Clinical Service and a source-specific unique index. Responses expose
`pricing_state`, canonical `source_record_id`, recognizable `source_category`,
live `source_status`, ordered/scheduled/performed dates, `already_submitted`,
`submission_eligible`, and `ineligibility_reason`. Clinical source and
financial writes synchronize in one transaction. Source deletion cascades the
active companion where deletion is permitted, while prior request-line
snapshots survive with a nullable source pointer.

Prescription documents do not create a second medication charge. A
`MedicalImagingAsset` image/report is evidence linked to an imaging Clinical
Service and never creates another charge. Appointments and equipment bookings
are scheduling/resource containers and are not automatically billable.
Diagnoses, history facts, doctor notes, recovery plans/observations, reminders,
and patient updates remain non-billable clinical documentation.

### Submission and request readback

- `GET /api/v1/payer-organizations`: doctor-visible synthetic organization
  choices for the current slice.
- `POST /api/v1/patients/{patient_id}/clinical-events/{event_id}/payer-requests`:
  submit an explicit, non-empty selection of active care items with a doctor
  summary. The server snapshots immutable lines and reconciles
  `requested_total_minor` from those lines. A source care-cost item that
  already appears in an earlier request snapshot cannot be submitted again;
  a repeated selection returns `409 conflict`. Every selected source must also
  be linked, non-cancelled, CNY, estimated/final, positive-total, exactly
  allocated, source-consistent, authorized, and not already submitted;
  otherwise the server rejects the whole request with per-item eligibility
  reasons.
- `GET /api/v1/doctor/me/payer-requests`: submitting doctor's requests.
- `GET /api/v1/patient/me/payer-requests`: patient's requests. Doctor and
  patient responses exclude payer reviewer notes. Each immutable line exposes
  its nullable `care_cost_item_id` source link so authorized clients can mark
  previously submitted ledger rows; the remaining line fields stay valid if
  the editable source row is later deleted.

### Payer workspace

- `GET /api/v1/payer/me/profile`
- `PATCH /api/v1/payer/me/profile`
- `GET /api/v1/payer/me/dashboard`
- `GET /api/v1/payer/me/requests`
- `GET /api/v1/payer/me/requests/{request_id}`
- `POST /api/v1/payer/me/requests/{request_id}/reviews`

The payer profile update contract accepts only reviewer-owned personal identity
fields:

```json
{
  "display_name": "Mei Reviewer",
  "title": "Senior expenditure reviewer"
}
```

Both fields are optional at the transport level so PATCH can update either
one, but at least one value must differ from the current membership record.
`display_name` is 1-120 trimmed characters and `title` is 2-120 trimmed
characters. Unknown or administrator-controlled fields are rejected with
`422 validation_failed`; this includes organization identity/type,
jurisdiction, membership status, access scope, and organization verification.
The endpoint requires the authenticated payer user's active membership and
otherwise returns the same neutral `404 not_found` boundary as the other payer
workspace endpoints. Account email remains owned by the shared
`PATCH /api/v1/auth/account/email` contract, and password changes continue
through `PUT /api/v1/auth/password` with session revocation.

Review creation accepts `action`, `reason_code`, and optional `note`. Actions
are `request_clarification`, `accept`, `reject`, `escalate`, and `close`; they
map to request statuses `clarification_requested`, `accepted`, `rejected`,
`escalated`, and `closed`. The doctor request-history contract returns every
current status, review action, reason code, and review timestamp but redacts the
reviewer-only note. These are human workflow states, not automatic
reimbursement, payment, coverage, adjudication, or care decisions. Request
existence and reviewer notes remain organization-scoped.

## Internal Governed Care-Reference And Deterministic Contract

Slices B/C intentionally add no HTTP endpoint. Callers inside the API process
must provide four exact compatible releases: scenario definition, care plan,
pricing reference, and utilization rules. Each release carries its ID, key,
version, payload checksum, jurisdiction/region/facility/currency scope,
effective interval, freshness date, lifecycle state, and rights state.

The internal deterministic request contains:

- evaluation date and service/reference date;
- jurisdiction, region, encounter type, facility ownership/level, currency,
  and applicable population fields;
- structured delivered-line identifiers, code system/code, unit, integer
  quantity, currency, and integer-minor-unit amount; and
- an optional attributable justified-exception code, rationale, author, and
  affected line IDs.

The internal result contains:

- `status`, including `suppressed`, `missing_information`, `unsupported`,
  `invalid_reference`, `invalid_observation`, `comparison_not_ready`,
  `within_range`, `review_recommended`, and `exception_recorded`;
- exact integer `total_low_minor`, `total_high_minor`, and
  `observed_total_minor` when calculation is valid;
- item-level ranges and observations;
- transparent `reason_codes`, `missing_information`, and
  `suppression_reasons`;
- the engine contract version, structured input snapshot and checksum, exact
  release IDs/versions/checksums, and result checksum; and
- an optional `prior_evaluation_id`. Re-evaluation inserts a new row and
  cannot update or delete the earlier result.

Release review, activation, supersession, and rollback are server-controlled
internal operations. Activation fails unless the release is effective, fresh,
rights-compatible, and approved by all required checksum-bound review types.
Database triggers prevent content mutation after activation and make reviews,
activation history, and evaluations append-only. No path in this contract
calls DeepSeek, activates the blocked Shanghai candidate, changes a Clinical
Event/Clinical Service/CareCostItem, or rewrites payer-request snapshots.

The implemented resolver accepts exact scenario, care-plan, pricing,
utilization, and scope keys and follows four active pointers. It rejects a
missing specialization, incompatible scenario binding, or missing release
items; it never selects an inferred “latest” version. The orchestration caller
must be an active doctor with an active relationship to the patient, and the
Clinical Event must belong to that patient. If a payer request is supplied, it
must also belong to that patient and event, have been submitted by the same
doctor, and its immutable line-ID set, currencies, and actual amounts must
exactly match the observed input. Any mismatch uses the neutral internal
`not_found` authorization boundary. Success appends an evaluation and a
content-free audit event; it does not mutate the Clinical Event, delivered
service/cost source, payer request, or prior evaluation.

## Internal Expected-Care Candidate Contract

Slice D intentionally adds no HTTP endpoint. Its purpose code is
`expected_care_candidate`, with independent purpose-contract, output-schema,
prompt, and model-configuration versions. It does not reuse patient-chat
prompts, schemas, evaluation, fallback, or activation state.

Before a provider call, the service verifies the active doctor-patient
relationship, exact Clinical Event, and optional submitting-doctor
payer-request scope with neutral `not_found` failures. It resolves the exact
four active releases, runs the B/C deterministic engine, checks freshness,
rights, provider-transmission permission, checksums, compatibility, and
confidentiality, then builds a minimum-necessary structured input.

Provider input contains applicability fields, admitted item/rule/reference
identifiers, server-owned integer-minor-unit ranges/totals, and exact release
lineage. It excludes patient/event identifiers, Clinical Event free text,
payer-review notes, unrelated history, attachments, credentials, contacts,
confidential reference content, and raw source content.

The strict output contains exact echoed applicability and release lineage,
bounded assumptions, missing information, attributable exceptions, confidence
limitations, and structured items. Each item must exactly match an admitted
item key, category, code system/code, unit, integer quantity range,
integer-minor-unit range, pricing-reference item ID, and utilization-rule ID.
The service revalidates every field and reconciles totals with the deterministic
engine. Schema errors, unsupported fields, incompatible or stale releases,
checksum drift, active-release changes, currency mismatch, and deterministic
disagreement fail closed.

Every terminal invocation inserts one append-only request, zero to two
append-only content-free provider attempts, and one append-only result.
Persistence retains case scope, idempotency fingerprint, optional predecessor,
purpose/configuration versions, provider/model metadata, exact release
IDs/checksums, minimum-input and output checksums, lifecycle and validation
outcomes, provider-reported usage, and deterministic-result lineage.

Terminal candidate states are `generated_pending_review`, `invalid`,
`suppressed`, or `provider_unavailable`. A validated candidate is copied
exactly into the separate `validated_baseline_published` domain; none of these
states means clinically correct or payer-approved. Retry is bounded to one additional attempt;
timeout, conservative cost reservation, default-off kill switch, local/test
synthetic-only gating, transaction-scoped idempotency locking, and fixed safe
fallbacks apply. Provider failure preserves manual and `pending_cost`
workflows.

The DeepSeek adapter is used only when explicitly enabled with a server-side
credential. All Slice D verification uses deterministic provider stubs and
prohibits external requests. Slice E baseline publication and clinician
responses never invoke this adapter.
Explanation generation remains outside this contract.

## Authenticated Expected-Care Baseline Contract

All existence-sensitive authorization failures are neutral `404 not_found`.
Stale response versions, release/checksum drift, suppressed or invalid
candidates, and deterministic disagreement return fixed `409 conflict` or
`422 validation_failed` responses. Mutations require an `Idempotency-Key`;
replay with the same content returns the original clinician response, while
reuse with different content returns `409 conflict`.

### Doctor

- `GET /api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates`
- `GET /api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/{candidate_result_id}`
- `GET /api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/{candidate_result_id}/history`
- `POST /api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/candidates/{candidate_result_id}/responses`

The list/history response includes the immutable candidate and separately
published baseline, exact admitted
release IDs/versions/checksums/effective dates, assumptions, missing
information, limitations, item ranges, totals, validation state, and immutable
clinician-response history. It also includes the immutable
`cost_estimation_fact_snapshot`, with server-selected `facts_used`,
`facts_not_used`, `missing_facts`, category counts, provenance, and authority
boundary. Doctor, patient, payer, and provider serialization use separate
allow-lists. It excludes provider prompts, raw provider output, credentials,
storage keys, contact/account identifiers, reviewer-only notes, and
content-free internal diagnostic codes.

Response input is one of `acknowledge`, `concur`, `disagree`, or `exception`,
with `expected_version`. `disagree` and `exception` require an attributable
structured rationale; `acknowledge` and `concur` may include one. The input
accepts no replacement items, quantities, codes, units, currency, reference
IDs, amounts, or totals. A rationale can carry an exception code, optional
patient-safe summary, and admitted item keys. Reviewer-only notes are
doctor-only. Every accepted response re-runs deterministic validation, but no
response can alter, reject, unpublish, or hide the baseline.

### Patient and payer

- `GET /api/v1/patient/clinical-events/{event_id}/expected-care-envelope`
- `GET /api/v1/payer/requests/{payer_request_id}/expected-care-envelope`

The patient route returns the latest deterministically validated, immutable
baseline for the authenticated patient even when no clinician response exists.
It labels the baseline as a system reference range, never a prescribed plan,
quote, bill, coverage determination, reimbursement amount, or final patient
responsibility. It includes patient-safe clinician positions separately and
omits reviewer-only notes, codes, rate IDs, checksums, and suspicion labels.

The payer route additionally requires an active membership in the exact
organization addressed by the immutable request and a baseline bound to that
request/patient/event. Its read-only response separates preserved AI candidate,
deterministic validation, immutable baseline, clinician response, submitted
facts, and human payer review. The clinician cannot hide or modify the
baseline. Payer reimbursement approval, partial approval, clarification, or
decline remains a separate human action; the baseline route exposes no clinical
approval or automated reimbursement action.

## Authenticated support request contract

Phase 1 adds a minimal backend submission/status path for signed-in doctor and
patient accounts only. It does not add public support submission, production
support UI integration, admin queue assignment, admin queue resolution, account
deletion execution, or specialist/admin support workflows.

### Submit support, deletion, or feedback request

`POST /api/v1/support-requests`

```json
{
  "request_type": "deletion",
  "subject": "Synthetic account deletion review",
  "message": "Please queue this synthetic account deletion review."
}
```

Rules:

- Only authenticated `doctor` and `patient` users can submit requests in Phase
  1. `specialist`, `admin`, unsupported, and unauthenticated callers fail
  closed.
- `request_type` is `support`, `deletion`, or `feedback`.
- The request status starts as `queued`.
- Patients' requests are linked to their own `patient_id`; doctor requests are
  account-scoped and not patient-scoped.
- The message must not include contact details, clinical details, medical
  records, imaging/scan content, medication-change requests, or real patient
  data. Unsafe content returns `422 validation_failed`.
- Stored queue rows keep a redacted body plus metadata such as requester role,
  message hash, character count, body-redacted flag, identity-review flag, and
  synthetic-data flag.
- Audit events are metadata-only. They include request type, status,
  requester role, and redaction flags, but not the request subject or message.

Response:

```json
{
  "request_id": "support-request-opaque-uuid",
  "request_type": "deletion",
  "status": "queued",
  "subject": "Synthetic account deletion review",
  "created_at": "2026-07-07T09:30:00Z",
  "updated_at": "2026-07-07T09:30:00Z",
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data."
}
```

### Read own request statuses

`GET /api/v1/support-requests`

`GET /api/v1/support-requests/{request_id}`

Doctors and patients can read only their own submitted request statuses.
Cross-requester probes return neutral `404 not_found`. Status reads create
metadata-only audit events. Admin-managed queue search, assignment, resolution,
policy review, and deletion execution remain Phase 5 production gaps.

## Phase 1 production foundation tables

Migration `20260707_0006` adds production foundation tables for hospitals,
clinics, role assignments, doctor teams, clinic resources, equipment,
appointments, equipment bookings, prescriptions, prescription medications,
medication reminders, notifications, invoices, payment statuses, revenue
summaries, analytics events, and support/deletion/feedback queue requests.

These tables are schema foundations only until specific API routes and UI
workflows are implemented in later Phase 1/Phase 2/Phase 4/Phase 5 slices. The
existing synthetic beta seed flow does not populate them. Their presence does
not make clinic operations, billing, analytics dashboards, real notification
delivery, or admin-managed production support/deletion/feedback handling
available.

## Demo upload presign contract

The presign endpoint creates metadata for a synthetic demo upload only. It does
not complete a real Tencent COS upload in Week 2 and must not accept real
patient images.

### Request

`POST /api/v1/patients/{patient_id}/assets/presign`

```json
{
  "filename": "synthetic-ct-demo.png",
  "content_type": "image/png",
  "size_bytes": 2048
}
```

Rules:

- `filename` must be a short safe filename using letters, numbers, spaces,
  periods, underscores, or hyphens.
- Surrounding whitespace is stripped from string request fields before
  validation.
- `content_type` must be `image/png`, `image/jpeg`, or `application/dicom`.
- `size_bytes` must be between `1` and `10485760`.
- The filename extension must match the content type: `.png` for `image/png`,
  `.jpg` or `.jpeg` for `image/jpeg`, and `.dcm` or `.dicom` for
  `application/dicom`.
- Unsupported content types return `415 unsupported_media_type`; oversized
  metadata returns `413 payload_too_large`; filename/content-type mismatch
  returns `422 validation_failed`.

### Response

```json
{
  "asset_id": "asset-opaque-uuid",
  "patient_id": "patient-opaque-uuid",
  "upload_url": "https://demo-upload.invalid/demo-assets/patient/asset.png",
  "method": "PUT",
  "object_key": "demo-assets/patient-opaque-uuid/asset-opaque-uuid.png",
  "headers": {
    "Content-Type": "image/png",
    "x-dr-ai-demo-upload": "synthetic-only"
  },
  "expires_at": "2026-07-05T08:45:00Z",
  "max_size_bytes": 10485760,
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data."
}
```

The response URL is a demo placeholder in the local Week 2 workflow. Logs and
audit metadata must not store upload URLs, tokens, patient-owned content, or
secrets.

## Phase 2 imaging upload and review contract

The imaging workflow now has two explicit layers:

1. `clinical_services` is the ordered, scheduled, in-progress, performed,
   completed, cancelled, or not-completed imaging procedure. It carries the
   patient, Clinical Event, category/name/type/body region, ordering doctor,
   optional provider/clinic/appointment, lifecycle dates, optional clinical
   indication, and at most one active financial companion.
2. `medical_imaging_assets` stores uploaded images/reports and review results as
   evidence. Multiple assets may link to one imaging service without creating
   additional charges.

Implemented service endpoints:

- `GET /api/v1/patients/{patient_id}/clinical-services`
- `POST /api/v1/patients/{patient_id}/clinical-services`
- `PUT /api/v1/patients/{patient_id}/clinical-services/{service_id}`
- `PUT /api/v1/patients/{patient_id}/clinical-services/{service_id}/financial`

Only an active treating doctor may create or mutate a Clinical Service.
Authorized patients receive read-only service data through the care bundle and
patient-scoped list. Writable request fields are explicitly allow-listed.
Supported categories are `imaging`, `laboratory`, `consultation`, `treatment`,
`rehabilitation`, and `other_service`. Category cannot change after creation.
Each service may retain `pending_cost` until the exact financial allocation is
known; payer submission remains unavailable until the existing reconciliation
contract passes.

The asset layer remains a production-separated metadata/status workflow. It is
Tencent-COS-compatible in shape, but this slice does not call Tencent COS,
inspect uploaded file bytes, or make clinical claims. The historical
`demo_medical_assets` beta table and `/assets/presign` endpoint remain
separate.

### Billable source boundary

| Record | Financial treatment |
|---|---|
| Medication/product | May own one active linked financial companion. |
| Prescription document | Authorization/documentation only; no second charge. |
| Specialist consultation | Its canonical Clinical Service may own one companion. |
| Appointment/meeting booking | Scheduling container only; no automatic charge. |
| Imaging procedure Clinical Service | May own one companion in pending, estimated, or final state. |
| Uploaded image/report | Evidence/result only; never creates a companion automatically. |
| Future laboratory test or treatment session | Must first become a governed Clinical Service with a real lifecycle and authorization path. |
| Equipment reservation | Non-billable until an explicit rental/use/deposit/cancellation policy and source type are implemented. |
| Diagnosis, note, history, observation | Non-billable clinical documentation. |

An appointment may schedule one or more Clinical Services, but the current
slice adds only the optional service-to-appointment foreign key. Requested or
scheduled state does not assert delivery. No deposit, no-show, cancellation,
equipment-use, or rental fee is inferred.

### Prepare imaging upload metadata

`POST /api/v1/patients/{patient_id}/imaging/presign`

```json
{
  "clinical_event_id": "event-opaque-uuid",
  "clinical_service_id": "imaging-service-opaque-uuid",
  "filename": "synthetic-ct-phase2.png",
  "content_type": "image/png",
  "size_bytes": 4096
}
```

Rules:

- Doctors can prepare uploads only for active-care assigned patients.
- Patients can prepare uploads only for their own patient profile.
- PNG, JPEG, DICOM, and PDF evidence use explicit content-type, size, and
  extension validation.
- When `clinical_service_id` is supplied, it must identify an imaging service
  for the same authorized patient and Clinical Event.
- The response includes a short-lived upload URL shape and headers for the
  client upload step, but later imaging list/detail responses do not echo the
  upload URL or object key.
- Audit metadata records actor role, content type, size, storage provider,
  upload status, and review status only.

Response:

```json
{
  "asset_id": "asset-opaque-uuid",
  "patient_id": "patient-opaque-uuid",
  "clinical_event_id": "event-opaque-uuid",
  "clinical_service_id": "imaging-service-opaque-uuid",
  "upload_url": "https://tencent-cos-upload.invalid/medical-imaging-assets/patient/asset.png",
  "method": "PUT",
  "headers": {
    "Content-Type": "image/png",
    "x-dr-ai-upload-purpose": "phase2-imaging-metadata-only"
  },
  "expires_at": "2026-07-08T00:45:00Z",
  "max_size_bytes": 10485760,
  "upload_status": "pending_upload",
  "review_status": "not_ready",
  "storage_provider": "tencent_cos",
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data."
}
```

### Complete upload metadata

`POST /api/v1/patients/{patient_id}/imaging/{asset_id}/complete`

```json
{
  "uploaded_size_bytes": 4096,
  "etag": "\"opaque-cos-etag\"",
  "checksum_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

`etag` and `checksum_sha256` are optional. The uploaded size must match the
prepared size. Completion changes `upload_status` to `uploaded` and
`review_status` to `pending_review`. Expired uploads return `409 conflict`;
wrong-role and cross-patient probes return neutral `404 not_found`.

### List/detail and doctor review

`GET /api/v1/patients/{patient_id}/imaging`

`GET /api/v1/patients/{patient_id}/imaging/{asset_id}`

`GET /api/v1/patient/me/imaging`

`GET /api/v1/patient/me/imaging/{asset_id}`

List/detail responses include only metadata needed for status review:
identifier, patient identifier, storage provider, content type, file extension,
byte counts, upload status, review status, optional manual doctor-entered
finding/result fields, timestamps, and the synthetic-data safety label. They
do not include filenames, object keys, upload URLs, ETags, checksums,
credentials, image contents, or generated diagnostic findings.

`POST /api/v1/patients/{patient_id}/imaging/{asset_id}/review`

```json
{
  "review_status": "reviewed",
  "finding_summary": "Manual doctor-entered finding/result text.",
  "measurement_summary": "Manual doctor-entered measurement or observation.",
  "observed_at": "2026-07-08T10:30:00Z",
  "treatment_relevance_date": "2026-07-08"
}
```

Only assigned doctors can review imaging metadata. `review_status` is
`reviewed` or `rejected`. The finding/result fields are optional, manual, and
doctor-entered. Reviewing an asset that has not completed upload returns
`409 conflict`. Review audit metadata records status and presence flags only;
it does not copy manual finding/result text or store automated clinical
interpretation.

## Simulated assessment contract

Only deterministic synthetic fixtures are permitted in v1. The endpoint must
reject free-form clinical values, real images, genomic files, names, contact
details, and other real patient data.

### Request

`POST /api/v1/patients/{patient_id}/assessments`

```json
{
  "mode": "simulated",
  "fixture_id": "synthetic_lung_case_001",
  "idempotency_key": "client-generated-opaque-value"
}
```

Rules:

- `mode` must be `simulated`.
- `fixture_id` must resolve to a versioned server-owned synthetic fixture.
- The same `idempotency_key`, actor, patient, and request body returns the same
  assessment instead of creating a duplicate.
- The deterministic result is derived from the fixture and simulator version,
  never from the patient's name or identifier.

### Response

```json
{
  "assessment_id": "asm_01J...",
  "mode": "simulated",
  "status": "completed",
  "risk_band": "moderate",
  "demo_score": 0.54,
  "input_completeness": "complete",
  "model_version": "fixture-simulator-1.0.0",
  "limitations": [
    "Synthetic fixture result; no clinical inference was performed.",
    "Not validated for diagnosis, treatment, or prognosis."
  ],
  "recommended_next_steps": [
    "Review the synthetic case with a qualified clinician."
  ],
  "safety_label": "Research simulation - not for diagnosis.",
  "created_at": "2026-07-04T08:30:00Z"
}
```

`demo_score` is a unitless fixture value in the inclusive range `0.0` to `1.0`.
It is not a probability, diagnostic confidence, or reproduction of the
research paper's reported performance. The paper's recurrence and survival
outcomes are not accepted as prediction inputs because they may introduce
outcome leakage.

The future validated-model adapter may use versioned CT, clinical, and genomic
references, but it must preserve this response shape and remain unavailable
until separately approved.

## Recovery plan and Today task contract

Week 3 Days 11-12 recovery plans are synthetic care-loop fixtures. They are not
medical advice and must not contain real patient data.

### Create or edit request

`POST /api/v1/patients/{patient_id}/recovery-plans`

`PUT /api/v1/patients/{patient_id}/recovery-plans/{plan_id}`

```json
{
  "title": "Synthetic Week 3 Recovery Plan",
  "instructions": "Demo-only recovery plan for workflow validation.",
  "tasks": [
    {
      "category": "medication",
      "title": "Demo medication reminder",
      "detail": "Review the synthetic medication fixture only.",
      "due_label": "Today",
      "notification_time": "09:00"
    },
    {
      "category": "exercise",
      "title": "Light demo mobility",
      "detail": "Short synthetic mobility task.",
      "due_label": "Today"
    },
    {
      "category": "diet",
      "title": "Demo hydration check",
      "detail": "Synthetic hydration reminder.",
      "due_label": "Today"
    },
    {
      "category": "follow_up",
      "title": "Synthetic follow-up preparation",
      "detail": "Prepare demo questions.",
      "due_label": "Today"
    }
  ]
}
```

Rules:

- Only doctors with an active care relationship can create, edit, or activate
  plans for a patient.
- Patients cannot create, edit, or activate plans.
- Each plan must include medication, exercise, diet, and follow-up tasks.
- Medication tasks require a `notification_time` label so Flutter can schedule
  the local demo notification shell.
- Cross-patient and wrong-role attempts return neutral `404 not_found`.
- Audit metadata records status, task count, task categories, and affected IDs;
  it must not copy plan instructions or task details.

### Plan response

```json
{
  "plan_id": "plan-opaque-uuid",
  "patient_id": "patient-opaque-uuid",
  "title": "Synthetic Week 3 Recovery Plan",
  "instructions": "Demo-only recovery plan for workflow validation.",
  "status": "active",
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data.",
  "created_at": "2026-07-05T08:30:00Z",
  "updated_at": "2026-07-05T08:30:00Z",
  "activated_at": "2026-07-05T08:45:00Z",
  "tasks": [
    {
      "task_id": "task-opaque-uuid",
      "plan_id": "plan-opaque-uuid",
      "category": "medication",
      "title": "Demo medication reminder",
      "detail": "Review the synthetic medication fixture only.",
      "due_label": "Today",
      "notification_time": "09:00",
      "medication_id": null,
      "is_completed": false,
      "completed_at": null,
      "notification_status": "Local demo notification shell scheduled for 09:00"
    }
  ]
}
```

`POST /api/v1/patients/{patient_id}/recovery-plans/{plan_id}/activate`
returns the same shape with `status: active`. Activating a plan completes any
previous active synthetic plan for the same patient.

### Patient Today and completion

`GET /api/v1/patient/me/today` preserves the Week 1 dashboard envelope and adds
`data.active_recovery_plan` plus `data.today_tasks` when an active plan exists.

`POST /api/v1/patient/me/tasks/{task_id}/completion`

```json
{
  "completed": true
}
```

Only the signed-in patient can complete their own active tasks. Duplicate
completion calls return the already completed task instead of creating a
second completion row.

`DELETE /api/v1/patient/me/tasks/{task_id}/completion`

```json
{
  "completed": false
}
```

Only the signed-in patient can uncomplete their own active tasks. Missing
completion rows return the already-uncompleted task state so accidental
repeated taps remain harmless.

## Educational chat and consultation contract

Week 3 Days 13-14 chat is educational question preparation only. It is not a
diagnosis, triage tool, medication adviser, record interpreter, or clinical
assessment.

### Send chat message

`POST /api/v1/chat/threads/{thread_id}/messages`

The patient app uses the opaque `patient-education` thread key for the current
patient's own educational thread. UUID thread IDs are also accepted when the
thread belongs to the signed-in patient. Doctors do not use patient chat in
this slice.

```json
{
  "message": "What questions should I prepare about the synthetic recovery task?",
  "stream": true
}
```

Rules:

- Patients can send messages only to their own chat thread.
- Surrounding whitespace is stripped before safety checks, rate limiting, and
  provider fallback handling.
- Wrong-role and unknown/cross-patient thread probes return neutral
  `404 not_found`.
- Red-flag detection runs before rate limiting and before any DeepSeek call.
- Red flags return the fixed emergency message and create a metadata-only
  audit event.
- Unsafe prompts, including diagnosis, medication-change, raw-record,
  contact-information, or scan-interpretation requests, return a safe fallback.
- Normal prompts are rate limited per user and return `429 rate_limited` when
  the configured window is exceeded.
- DeepSeek is called only by FastAPI using `deepseek-v4-flash` by default.
- Local/test mode or an unset DeepSeek key uses the safe fallback path.
- A malformed structured response receives one bounded repair attempt carrying
  the complete JSON Schema, enum constraints, and content-free validation
  paths. Repeated malformed output, timeout, quota, and provider-unavailable
  failures return bounded fallback content rather than exposing provider
  details.
- Stored chat metadata includes prompt hash, prompt length, safety category,
  fallback reason, model label, a content-free provider diagnostic subtype, and
  provider attempt count only; raw prompts and raw model output are not stored
  in chat metadata or audit metadata.

Response:

```json
{
  "thread_id": "thread-opaque-uuid",
  "thread_key": "patient-education",
  "message_id": "message-opaque-uuid",
  "assistant_message_id": "message-opaque-uuid",
  "content": "Educational information only - not medical advice. ...",
  "response_chunks": [
    "Educational information only - not medical advice.",
    "Prepare questions for your clinician."
  ],
  "response_mode": "stream_ready",
  "safety_label": "Educational information only - not medical advice.",
  "emergency_label": null,
  "is_red_flag": false,
  "fallback_reason": null,
  "model": "deepseek-v4-flash",
  "created_at": "2026-07-05T15:30:00Z"
}
```

For red-flag handling, `is_red_flag` is `true`, `fallback_reason` is
`red_flag`, and `emergency_label` is
`If this may be an emergency, contact local emergency services now.`

### Consultation requests

`GET /api/v1/consultations`

Doctors see consultation requests for patients in active care relationships.
Patients see only their own consultation requests.

`POST /api/v1/consultations`

```json
{
  "patient_id": "patient-opaque-uuid",
  "specialty": "Pulmonology demo review",
  "question_summary": "Synthetic review of recovery-plan education questions.",
  "priority": "routine"
}
```

Rules:

- Only doctors with an active care relationship can create requests.
- Patients cannot create requests.
- Cross-patient and wrong-role attempts return neutral `404 not_found`.
- `priority` is `routine` or `soon`.
- `specialty` and `question_summary` are stripped before validation and
  duplicate detection.
- Repeating the same `requested` consultation payload for the same doctor and
  patient returns the existing request instead of creating a duplicate.
- Both the specialty and summary must be synthetic and non-identifying; raw
  records, contact information, diagnosis requests, medication-change
  requests, or scan interpretation requests are rejected.
- Status starts as `requested`. Specialist acceptance/completion workflows are
  not implemented in this slice.
- Audit metadata records specialty, priority, status, and affected IDs without
  copying the question summary.

Response:

```json
{
  "consultation_id": "consultation-opaque-uuid",
  "patient_id": "patient-opaque-uuid",
  "specialty": "Pulmonology demo review",
  "question_summary": "Synthetic review of recovery-plan education questions.",
  "priority": "routine",
  "status": "requested",
  "safety_label": "Synthetic demonstration data only. Do not enter real patient data.",
  "created_at": "2026-07-05T15:30:00Z",
  "updated_at": "2026-07-05T15:30:00Z"
}
```

List response:

```json
{
  "items": [],
  "next_cursor": null
}
```

## Safety labels

These exact English labels are frozen:

```text
Research simulation - not for diagnosis.
Synthetic demonstration data only. Do not enter real patient data.
Educational information only - not medical advice.
If this may be an emergency, contact local emergency services now.
```

- The simulation label is persistent anywhere an assessment is requested,
  pending, or displayed.
- The synthetic-data label appears before any future data-entry or upload
  surface.
- Educational chat responses include the educational label.
- Red-flag chat handling bypasses the model and returns the fixed emergency
  label plus locally appropriate emergency guidance configured by deployment.
- No response may claim clinical validation, quote the paper's `96.88%`
  cross-validation accuracy as product performance, or recommend a medication
  change.

## Pagination and concurrency

Collection endpoints will use cursor pagination:

```json
{
  "items": [],
  "next_cursor": null
}
```

Clients send `cursor` and `limit` query parameters. The v1 default is `20` and
the frozen maximum is `50`. The Week 1 assigned-patient list currently returns
`next_cursor: null`; cursor continuation is added only when the dataset can
exceed one page.
Mutating endpoints that can be retried accept an `Idempotency-Key` header or
the explicitly documented body key. Conflicting replays return `409 conflict`.

## Versioning rules

- `/api/v1` is the stable major-version prefix.
- Additive optional response fields may ship within v1.
- Existing fields cannot change meaning, type, or requiredness within v1.
- Removing or renaming a field, path, enum value, or safety label requires a
  new major version.
- New enum values require a compatibility review even when otherwise additive.
- The API publishes an OpenAPI document and a semantic contract version.
- Deprecated v1 behavior receives a documented migration window before
  removal; v1 remains available until the next invited-beta client can migrate.
- `/health` remains unversioned and contains operational status only.

## Implementation gate

Before any deferred endpoint is enabled:

1. Add request and response models matching this contract.
2. Add authentication, server-side role checks, ownership checks, and neutral
   cross-patient failures.
3. Add success, validation, wrong-role, cross-patient, idempotency, and audit
   tests.
4. Verify that logs and error responses contain no synthetic medical content,
   real patient data, secrets, or tokens.
5. Update the OpenAPI contract and this file together.

Related records:

- [Implementation plan](Dr_AI_v1.0_Implementation_Plan.md)
- [Design freeze](Dr_AI_v1.0_Design_Freeze.md)
- [Week 1 Days 1-2 foundation record](beta/Week_1_Days_1_2_Foundation_Record.md)

## Phase 3 Doctor Resource Catalog

### `GET /api/v1/doctor/resources`

Doctor-only, paginated access to catalog-visible authoritative source metadata.
This is a governed link-catalog endpoint, not the approved-passage retrieval
endpoint. It never returns stored article bodies or generated passages.

Optional query parameters: `query`, `topic`, `publisher_id`, `limit` (1-100),
and `offset`.

Each item includes the stable source/publisher IDs, official title and locator,
official English title and locator where paired, `available_languages`,
`is_bilingual`, catalog summary, search keywords, source type, topic,
jurisdiction, language, authority tier, catalog verification time,
lifecycle/review state, `rights_mode`, and nullable `zh_translation_status`.
`official_link_only` means the source may be shown as an official locator but is
not admitted for excerpts, embeddings, or AI retrieval. A generated translation
does not add `zh-Hans` to `available_languages` or set `is_bilingual` until its
medical and native-Chinese reviews are both approved. Translation never creates
a second catalog source.

The optional `query` searches title, official translation title, topic,
catalog summary, bilingual search keywords, and the English plus
Simplified-Chinese text of approved generated summary artifacts. Generated
summary text affects catalog matching only after manual review and approved
import; pending or rejected summaries are excluded. For link-only sources,
catalog summaries still describe verified metadata only and explicitly do not
summarize unstored article text.

### `GET /api/v1/doctor/resources/{source_id}`

Doctor-only source detail used by the stable
`/doctor/resources/{sourceId}/read` application route. It returns the catalog
fields above plus ordered `sections` containing `heading` and `original_text`
only when the current source version was captured as publisher-original text
and its approved rights record permits storage, display, and redistribution.
Link-only sources return no sections. An approved generated translation is
returned separately in `translations` with `language`, translated `title`,
`translation_type=ai_generated_unofficial`,
`review_status=medical_and_native_chinese_approved`, and aligned `sections`.
Pending or singly-approved translations are omitted. The client must not infer
display permission from a button or cached list item, and patient roles receive
`403 forbidden`.

Readable doctor content remains separate from retrieval admission. Medical,
native-language, patient-readability, lifecycle, and immutable-release gates
still determine whether any passage may enter doctor or patient retrieval.

## Phase 3 Approved Retrieval Baseline

### `POST /api/v1/retrieval/doctor/resources/search`

Doctor-only hybrid search over the active `doctor` index release. The request
uses `DoctorResourceSearchRequest`: query, topic/document/organization/
jurisdiction/language/date/status filters, cursor, and limit. The response
preserves the original query, shows reviewed expanded terms, exposes the
evidence decision and active release ID, and returns matched passages with
source/version citations. It does not call an LLM.

### `POST /api/v1/retrieval/patient/evidence`

Patient-only evidence lookup for the later Slice 5 orchestrator. It searches
only the active `patient` release and requires patient eligibility,
native-language/readability approval, current status, requested language and
China jurisdiction, a matching primary clinical symptom concept that is central
to the source metadata rather than incidentally mentioned, a meaningful lexical
topic anchor, and sufficient content coverage.
Sufficiency requires either one strongly covering source or at least two
independently covering sources; source count, dense similarity, and authority
bonuses cannot admit off-topic material. Failed sufficiency or conflict gates
return no passages.

Both endpoints return `503 retrieval_unavailable` when no valid audience index
is active or the release embedding model is not configured. Retrieval events
store only query SHA-256, query length, filter categories, release/source/
passage IDs, score summary, latency, decision, and fallback code. Raw queries
and passage text are never written to retrieval telemetry.

Slice 9A additionally binds every vector to the release embedding version and
binds the active release to its reranker version. Production configuration is
fail-closed unless the declared self-hosted BGE-M3 embedding and BGE reranker
services are configured in an explicitly approved production region. Hong Kong
is accepted for current development/staging; final patient-facing use requires
documented residency, Mainland-user network performance, provider-rights,
privacy/legal, and no-training/no-retention evidence. Reranker outage uses the
recorded deterministic fallback. Patient-index construction
and the immediate pre-generation handoff separately re-read source-matched,
effective, unexpired provider-transmission rights; a stale manifest cannot
override a revoked or expired live rights decision.

Slice 9B does not change the public patient-evidence response. Patient chat
first searches the literal user question. Only a server-defined short-
reference, colloquial/ambiguous, or weak-result trigger may spend one bounded
schema-constrained planner call and one retrieval retry. The server validates
meaning preservation, keeps the original result, collapses duplicate passages,
limits per-source dominance, and uses the fused result only when measured
retrieval utility improves. Planner timeouts, quota errors, malformed output,
meaning drift, retry failure, budget excess, or no improvement retain the
original safe result or its fixed fallback.

### Patient-chat grounding modes

`POST /api/v1/patient/chat/messages` now returns additive
`grounding_mode` with one of:

- `approved_evidence`: the answer was generated only from authorized,
  versioned Dr. AI passages. Every material claim retains validated passage
  support and the response contains real reviewed source cards.
- `general_model_knowledge`: adequate approved evidence was unavailable and
  the independently enabled general model answered without patient-record
  context, citations, passage IDs, or source cards. The UI must disclose
  “General AI-generated information — no supporting Dr. AI source was found.”
  This output can be wrong and is not evidence-grounded.
- `fixed_safety_response`: deterministic emergency/prohibited-action copy,
  authorization denial, provider/retrieval failure, malformed output, or
  another server-owned fixed response.

Historical stored response JSON remains readable: old payloads with source
cards are interpreted as `approved_evidence`; old fallback payloads are
interpreted as `fixed_safety_response`. Provider/model identifiers remain
metadata-only and are not returned as patient-facing details.

The general-knowledge schema has no citation fields. It cannot represent model
memory as reviewed evidence, use patient records as evidence, confirm or rule
out diagnosis, reassure that an emergency is absent, or prescribe a
patient-specific medication start/stop/substitution/dose. It must include
material uncertainty and a sensible next step for symptom-related or otherwise
medically consequential questions. A mixed request may answer the safe general
education portion while explicitly declining a prohibited personal treatment
change. Adequate approved evidence continues to use the grounded schema and
claim/citation/context validation.

The workflow permits zero or one planner request, one answer-generation
request, and at most one malformed-output schema-repair request. This is a
two-stage adaptive workflow with an optional bounded repair, not an absolute
two-request guarantee. Grounded generation and general-model-knowledge
generation have separate kill switches and schema versions. There is no
arbitrary answer-time web browsing.

### Patient-chat urgency response

New patient-chat responses populate the additive `urgency_route` field with one
of `emergency_120`, `urgent_same_day`, `clinician_contact`,
`routine_education`, or `prohibited_medication_change`. The field remains
nullable only so previously stored thread metadata can still be read. It is a
server decision, not model output.

Emergency routes return before retrieval and answer-model generation.
Prohibited medication actions remain server-owned; a mixed request may pass
only its safe educational portion to the general-knowledge schema while the
personalized change is declined. For an allowed non-emergency message, the server passes the model a
bounded next-action allowlist: `urgent_same_day` requires `seek_local_care`;
`clinician_contact` permits `contact_connected_doctor` or `seek_local_care`;
and a routine answer must select a non-emergency, non-`none` practical action.
Routine output also cannot select the same-day-only `seek_local_care` action.
Any model response outside that allowlist fails closed. Evidence/provider
fallbacks preserve same-day care timing without generating a diagnosis or using
model memory as evidence. General-model knowledge is separately labeled and
never presented as evidence.

The current non-emergency care-timing rule table and fixed same-day fallback
copy are local candidates pending named clinical, native-Simplified-Chinese,
and product review. Their presence in the response schema is not production
approval.

## Expected-care deterministic comparison and explanation (Slices F/G)

All routes are authenticated and use neutral `404 not_found` boundaries for
wrong role, patient, Clinical Event, payer organization, membership, request,
baseline, or comparison scope. A clinician response is not required for any
baseline or comparison read.

| Method | Route | Authorization | Behavior |
|---|---|---|---|
| `POST` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/baselines/{baseline_id}/comparisons` | Assigned doctor | Creates or replays one immutable server-calculated comparison. Requires `Idempotency-Key`; conflicting reuse returns `409 conflict`. |
| `POST` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons` | Assigned doctor | Creates or replays a comparison from the latest immutable baseline; Flutter never supplies baseline/provider facts. |
| `GET` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/latest` | Assigned doctor | Latest authorized comparison with technical line evidence. |
| `GET` | `/api/v1/patients/{patient_id}/clinical-events/{event_id}/expected-care/comparisons/history` | Assigned doctor | Immutable comparison history and predecessor differences. |
| `GET` | `/api/v1/patient/clinical-events/{event_id}/expected-care-comparison` | Exact patient | Patient-filtered comparison without service codes, source IDs, reviewer notes, or confidential lineage. |
| `GET` | `/api/v1/payer/requests/{payer_request_id}/expected-care-comparison` | Active membership in exact request organization | Exact request-scoped comparison. |
| `POST/GET` | doctor comparison `/explanations`, `/explanations/latest`, and `/explanations/history` routes | Assigned doctor | Requests, reads, or lists immutable doctor fact-object explanations. History is bounded by `limit=1..100`. |
| `POST/GET` | patient comparison `/explanations`, `/explanations/latest`, and `/explanations/history` routes | Exact patient | Requests, reads, or lists patient-safe explanation attempts. History is bounded by `limit=1..100`. |
| `POST/GET` | payer request comparison `/explanations`, `/explanations/latest`, and `/explanations/history` routes | Active exact-organization membership | Requests, reads, or lists immutable request-scoped payer explanations. History is bounded by `limit=1..100`. |

Comparison creation accepts only `{"include_submitted_facts": boolean}`.
Server arithmetic uses integer minor units and returns
`within_reference_range`, `below_reference_range`,
`above_reference_range`, `not_comparable`, or `missing_cost`. Cross-scope
records, inactive/checksum-drifted releases, incompatible currency, incomplete
allocations, or submitted-total mismatch return `409 conflict` and do not hide
the baseline or block ordinary care/cost work.

Explanation requests accept only `{"locale":"en"|"zh-Hans"}` plus
`Idempotency-Key`. Public output contains the validated display artifact or a
fixed structured fallback. It never exposes prompt text, raw provider output,
credentials, reviewer-only fields outside doctor authorization, confidential
rates, hidden identifiers, or content-bearing operational diagnostics.
Provider, validation, release, or kill-switch failure leaves the immutable
baseline and deterministic comparison available.

Provider output is the canonical
`expected-care-role-explanation-claim-graph.v2` selection contract, not free
prose. It contains admitted fact IDs, controlled claim types, and allow-listed
connectives. The server renders protected values and both languages from the
same claims.

Activation, supersession, kill switch, rollback, early-stage waiver, and
unsuitable-release correction are server-operator commands. They require
advisory locking, exact expected versions, content-bound idempotency,
checksum/contract verification, mandatory executable gates, and an explicit
rollback target, and they append only content-free transition evidence.
