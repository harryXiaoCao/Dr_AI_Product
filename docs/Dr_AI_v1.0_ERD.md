# Dr. AI v1.0 Database ERD

Status: working data-integrity map
Last updated: 2026-07-14
Source: `services/api/app/models.py` and Alembic migrations through `20260714_0023`

This file is a field-level ERD for implementation reviews. It is intentionally
more detailed than a product overview because Dr. AI depends on one consistent
source of truth for account identity, patient profile data, doctor profile
data, Clinical Event context, and future commercial/admin foundations.

## Legend

- `PK`: primary key.
- `FK`: foreign key.
- `UK`: unique key or unique column.
- `IDX`: indexed column.
- `nullable`: optional column.
- `jsonb`: PostgreSQL `JSONB`.
- `datetime_tz`: timezone-aware SQLAlchemy `DateTime`.
- `uuid`: PostgreSQL UUID.
- `varchar_N`: string column with length `N`.

## Full Field-Level ERD

```mermaid
erDiagram
  HOSPITALS {
    uuid id PK
    varchar_160 name
    varchar_240 legal_name "nullable"
    varchar_40 status
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  USERS {
    uuid id PK
    varchar_320 email UK "IDX nullable"
    varchar_40 phone_number UK "IDX nullable"
    varchar_255 password_hash
    enum_user_role role
    boolean is_active
    datetime_tz last_active_at "nullable"
    datetime_tz created_at
    datetime_tz updated_at
  }

  CHAT_RATE_LIMITS {
    uuid user_id PK,FK
    datetime_tz window_start
    integer message_count
    datetime_tz updated_at
  }

  CLINICS {
    uuid id PK
    uuid hospital_id FK
    varchar_160 name
    varchar_80 timezone
    varchar_40 status
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  DASHBOARD_SNAPSHOTS {
    uuid id PK
    uuid user_id FK,UK
    jsonb payload
    datetime_tz updated_at
  }

  DOCTOR_PROFILES {
    uuid id PK
    uuid user_id FK,UK
    varchar_120 display_name
    varchar_160 title
    varchar_160 hospital_name
    date birth_date "nullable"
    varchar_40 gender "nullable"
    varchar_40 contact_phone "nullable"
    text avatar_url "nullable"
    varchar_80 country "nullable"
    varchar_80 province "nullable"
    varchar_80 city "nullable"
    varchar_120 specialty "nullable"
    varchar_120 department "nullable"
    varchar_80 preferred_language "nullable"
  }

  PATIENT_PROFILES {
    uuid id PK
    uuid user_id FK,UK
    varchar_120 display_name
    varchar_80 synthetic_identifier UK "IDX"
    date birth_date "nullable"
    integer birth_year "nullable"
    varchar_40 sex "nullable"
    varchar_40 gender "nullable"
    varchar_40 contact_phone "nullable"
    varchar_120 emergency_contact_name "nullable"
    varchar_40 emergency_contact_phone "nullable"
    varchar_80 preferred_language "nullable"
    varchar_80 contact_preference "nullable"
    text avatar_url "nullable"
    varchar_80 country "nullable"
    varchar_80 province "nullable"
    varchar_80 city "nullable"
    varchar_240 home_address "nullable"
    float height_cm "nullable"
    float weight_kg "nullable"
    varchar blood_type "nullable; Unknown/A+/A-/B+/B-/AB+/AB-/O+/O-"
    int systolic_blood_pressure "nullable"
    int diastolic_blood_pressure "nullable"
    varchar smoking_status "nullable"
    varchar alcohol_consumption "nullable"
    text heart_history "nullable"
    text endocrine_history "nullable"
    text neuro_history "nullable"
    text digestive_history "nullable"
    text respiratory_history "nullable"
    text kidney_history "nullable"
    text cancer_history "nullable"
    text patient_reported_medications "nullable"
    text surgery_history "nullable"
    text family_history "nullable"
    text lifestyle_notes "nullable"
    varchar pregnancy_status "nullable"
    boolean medical_history_setup_completed
  }

  REFRESH_SESSIONS {
    uuid id PK
    uuid family_id
    uuid user_id FK "nullable before registration"
    varchar_64 token_hash UK "IDX"
    datetime_tz expires_at
    datetime_tz created_at
    datetime_tz used_at "nullable"
    datetime_tz revoked_at "nullable"
    uuid replaced_by_id FK "nullable"
  }

  PHONE_VERIFICATION_CHALLENGES {
    uuid id PK
    uuid user_id FK
    varchar_40 phone_number "IDX"
    varchar_40 purpose "IDX"
    varchar_64 code_hash
    integer attempts
    datetime_tz expires_at
    datetime_tz consumed_at "nullable"
    datetime_tz created_at "IDX"
  }

  CARE_RELATIONSHIPS {
    uuid id PK
    uuid doctor_id FK
    uuid patient_id FK
    boolean is_active
    datetime_tz created_at
    datetime_tz revoked_at "nullable"
  }

  CLINICAL_EVENTS {
    uuid id PK
    uuid patient_id FK
    uuid doctor_id FK "nullable"
    varchar_160 title
    varchar_240 chief_complaint
    text symptom_summary "nullable"
    text diagnosis_summary "nullable"
    date onset_date "nullable"
    varchar_40 status
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  CLINICAL_EVENT_UPDATES {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK
    uuid submitted_by_user_id FK
    varchar_60 update_type
    text summary
    datetime_tz occurred_at
    datetime_tz created_at
  }

  MEDICAL_RECORDS {
    uuid id PK
    uuid patient_id FK
    varchar_160 title
    varchar_80 category
    text summary
    datetime_tz recorded_at
    datetime_tz created_at
  }

  MEDICAL_HISTORY_REVIEWS {
    uuid id PK
    uuid patient_id FK
    uuid doctor_id FK "nullable"
    varchar_40 target_type
    uuid target_id
    varchar_40 action
    text amendment_summary "nullable"
    text correction_request "nullable"
    datetime_tz created_at
  }

  PATIENT_ALLERGIES {
    uuid id PK
    uuid patient_id FK
    varchar_160 label
    varchar_240 reaction "nullable"
    varchar_40 severity
    varchar_40 status
    uuid recorded_by_user_id FK
    datetime_tz created_at
    datetime_tz updated_at
  }

  CHRONIC_DISEASES {
    uuid id PK
    uuid patient_id FK
    varchar_160 name
    varchar_40 status
    date diagnosed_on "nullable"
    text notes "nullable"
    uuid recorded_by_user_id FK
    datetime_tz created_at
    datetime_tz updated_at
  }

  VISIT_HISTORY {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    varchar_80 visit_type
    varchar_160 title
    text summary
    datetime_tz occurred_at
    varchar_160 clinician_label "nullable"
    uuid recorded_by_user_id FK
    datetime_tz created_at
    datetime_tz updated_at
  }

  DIAGNOSES {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    varchar_160 label
    varchar_40 status
    date diagnosed_on "nullable"
    text notes "nullable"
    uuid recorded_by_user_id FK
    datetime_tz created_at
    datetime_tz updated_at
  }

  MEDICATIONS {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    varchar_160 name
    varchar_120 dosage
    varchar_160 schedule
    varchar_40 status
    text note
    datetime_tz created_at
  }

  PRESCRIPTIONS {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    uuid prescribed_by_user_id FK
    varchar_40 status
    datetime_tz issued_at "nullable"
    text notes "nullable"
    datetime_tz created_at
    datetime_tz updated_at
  }

  PRESCRIPTION_MEDICATIONS {
    uuid id PK
    uuid prescription_id FK
    uuid medication_id FK "nullable"
    varchar_160 name
    varchar_120 dosage
    varchar_160 schedule
    date start_date "nullable"
    date end_date "nullable"
    jsonb metadata_json
  }

  MEDICATION_REMINDERS {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    uuid medication_id FK "nullable"
    uuid prescription_medication_id FK "nullable"
    varchar_160 schedule_label
    varchar_40 channel
    varchar_40 status
    datetime_tz next_due_at "nullable"
    datetime_tz last_sent_at "nullable"
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  NOTIFICATIONS {
    uuid id PK
    uuid user_id FK
    uuid patient_id FK "nullable"
    uuid clinical_event_id FK "nullable"
    varchar_80 notification_type
    varchar_40 channel
    varchar_40 status
    datetime_tz scheduled_for "nullable"
    datetime_tz sent_at "nullable"
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  DOCTOR_NOTES {
    uuid id PK
    uuid patient_id FK
    uuid doctor_id FK
    uuid clinical_event_id FK "nullable"
    varchar_160 title
    text body
    datetime_tz created_at
    datetime_tz updated_at
  }

  DEMO_MEDICAL_ASSETS {
    uuid id PK
    uuid patient_id FK
    uuid uploaded_by_user_id FK
    varchar_160 filename
    varchar_80 content_type
    integer size_bytes
    varchar_240 object_key UK
    varchar_40 status
    datetime_tz created_at
    datetime_tz expires_at
  }

  MEDICAL_IMAGING_ASSETS {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    uuid uploaded_by_user_id FK
    uuid reviewed_by_user_id FK "nullable"
    varchar_40 storage_provider
    varchar_80 content_type
    varchar_16 file_extension
    integer size_bytes
    integer uploaded_size_bytes "nullable"
    varchar_260 object_key UK
    varchar_40 upload_status
    varchar_40 review_status
    text finding_summary "nullable"
    varchar_240 measurement_summary "nullable"
    datetime_tz observed_at "nullable"
    date treatment_relevance_date "nullable"
    varchar_128 etag "nullable"
    varchar_64 checksum_sha256 "nullable"
    datetime_tz created_at
    datetime_tz updated_at
    datetime_tz expires_at
    datetime_tz uploaded_at "nullable"
    datetime_tz reviewed_at "nullable"
  }

  SIMULATED_ASSESSMENTS {
    uuid id PK
    uuid patient_id FK
    uuid actor_user_id FK
    varchar_80 fixture_id
    varchar_120 idempotency_key
    varchar_64 request_hash
    varchar_40 mode
    varchar_40 status
    varchar_40 risk_band
    varchar_12 demo_score
    varchar_40 input_completeness
    varchar_80 model_version
    jsonb limitations
    jsonb recommended_next_steps
    varchar_80 safety_label
    datetime_tz created_at
  }

  RECOVERY_PLANS {
    uuid id PK
    uuid patient_id FK
    uuid doctor_id FK
    uuid clinical_event_id FK "nullable"
    varchar_160 title
    text instructions
    varchar_40 status
    varchar_40 review_status
    varchar_120 safety_label
    uuid review_actor_user_id FK "nullable"
    datetime_tz created_at
    datetime_tz updated_at
    datetime_tz submitted_at "nullable"
    datetime_tz reviewed_at "nullable"
    datetime_tz approved_at "nullable"
    datetime_tz activated_at "nullable"
    datetime_tz completed_at "nullable"
  }

  RECOVERY_TASKS {
    uuid id PK
    uuid plan_id FK
    uuid patient_id FK
    uuid medication_id FK "nullable"
    varchar_40 category
    varchar_160 title
    text detail
    varchar_80 due_label
    varchar_20 notification_time "nullable"
    integer sort_order
    datetime_tz created_at
  }

  RECOVERY_TASK_COMPLETIONS {
    uuid id PK
    uuid task_id FK
    uuid patient_id FK
    uuid actor_user_id FK
    datetime_tz completed_at
  }

  CHAT_THREADS {
    uuid id PK
    uuid patient_id FK
    uuid doctor_id FK "nullable"
    uuid created_by_user_id FK
    varchar_80 thread_key
    varchar_40 thread_type
    varchar_160 title
    datetime_tz created_at
    datetime_tz last_message_at "nullable"
  }

  CHAT_MESSAGES {
    uuid id PK
    uuid thread_id FK
    uuid patient_id FK
    uuid actor_user_id FK
    varchar_40 role
    text content "nullable"
    varchar_64 prompt_hash "nullable"
    integer prompt_char_count "nullable"
    varchar_80 safety_category
    varchar_80 fallback_reason "nullable"
    varchar_120 model "nullable"
    jsonb metadata_json
    datetime_tz created_at
  }

  CONSULTATION_REQUESTS {
    uuid id PK
    uuid patient_id FK
    uuid clinical_event_id FK "nullable"
    uuid requested_by_user_id FK
    varchar_120 specialty
    varchar_240 question_summary
    varchar_40 priority
    varchar_40 status
    varchar_120 safety_label
    datetime_tz created_at
    datetime_tz updated_at
  }

  AUDIT_EVENTS {
    uuid id PK
    uuid actor_user_id FK
    uuid patient_id FK "nullable"
    varchar_80 event_type
    varchar_80 resource_type
    uuid resource_id "nullable"
    jsonb metadata_json
    datetime_tz created_at
  }

  ROLE_ASSIGNMENTS {
    uuid id PK
    uuid user_id FK
    enum_user_role role
    uuid hospital_id FK "nullable"
    uuid clinic_id FK "nullable"
    uuid assigned_by_user_id FK "nullable"
    varchar_40 status
    datetime_tz created_at
    datetime_tz revoked_at "nullable"
  }

  DOCTOR_TEAMS {
    uuid id PK
    uuid clinic_id FK
    varchar_160 name
    varchar_40 status
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  DOCTOR_TEAM_MEMBERSHIPS {
    uuid id PK
    uuid team_id FK
    uuid user_id FK
    varchar_80 role
    uuid assigned_by_user_id FK "nullable"
    varchar_40 status
    datetime_tz created_at
    datetime_tz revoked_at "nullable"
  }

  CLINIC_RESOURCES {
    uuid id PK
    uuid clinic_id FK
    varchar_80 resource_type
    varchar_160 name
    varchar_40 status
    integer capacity_current "nullable"
    integer capacity_total "nullable"
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  EQUIPMENT {
    uuid id PK
    uuid clinic_id FK
    uuid resource_id FK "nullable"
    varchar_160 name
    varchar_80 equipment_type
    varchar_40 status
    varchar_160 location_label "nullable"
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  APPOINTMENTS {
    uuid id PK
    uuid clinic_id FK
    uuid patient_id FK
    uuid doctor_id FK "nullable"
    uuid specialist_user_id FK "nullable"
    varchar_40 status
    datetime_tz scheduled_start
    datetime_tz scheduled_end
    varchar_80 reason_code
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  EQUIPMENT_BOOKINGS {
    uuid id PK
    uuid equipment_id FK
    uuid appointment_id FK "nullable"
    uuid requested_by_user_id FK
    uuid patient_id FK "nullable"
    varchar_40 status
    datetime_tz start_at
    datetime_tz end_at
    varchar_160 purpose
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  INVOICES {
    uuid id PK
    uuid patient_id FK
    uuid clinic_id FK "nullable"
    varchar_40 status
    varchar_3 currency
    integer total_cents
    datetime_tz issued_at "nullable"
    datetime_tz due_at "nullable"
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  PAYMENT_STATUSES {
    uuid id PK
    uuid invoice_id FK
    varchar_80 provider
    varchar_40 status
    integer amount_cents
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  REVENUE_SUMMARIES {
    uuid id PK
    uuid clinic_id FK
    datetime_tz period_start
    datetime_tz period_end
    varchar_3 currency
    integer invoiced_cents
    integer paid_cents
    integer outstanding_cents
    jsonb metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  ANALYTICS_EVENTS {
    uuid id PK
    uuid actor_user_id FK "nullable"
    uuid patient_id FK "nullable"
    uuid clinic_id FK "nullable"
    varchar_120 event_type
    varchar_80 resource_type "nullable"
    uuid resource_id "nullable"
    jsonb metadata_json
    datetime_tz occurred_at
  }

  SUPPORT_REQUESTS {
    uuid id PK
    uuid requester_user_id FK "nullable"
    uuid patient_id FK "nullable"
    varchar_40 request_type
    varchar_40 status
    varchar_160 subject
    text body_redacted
    varchar_80 source
    uuid assigned_to_user_id FK "nullable"
    jsonb audit_metadata_json
    datetime_tz created_at
    datetime_tz updated_at
  }

  USERS ||--o| DOCTOR_PROFILES : owns
  USERS ||--o| PATIENT_PROFILES : owns
  USERS ||--o{ REFRESH_SESSIONS : has
  USERS ||--o{ PHONE_VERIFICATION_CHALLENGES : verifies
  REFRESH_SESSIONS ||--o{ REFRESH_SESSIONS : replaced_by
  USERS ||--o| DASHBOARD_SNAPSHOTS : has
  USERS ||--o| CHAT_RATE_LIMITS : limited_by

  DOCTOR_PROFILES ||--o{ CARE_RELATIONSHIPS : manages
  PATIENT_PROFILES ||--o{ CARE_RELATIONSHIPS : grants_access
  DOCTOR_PROFILES ||--o{ CLINICAL_EVENTS : leads
  PATIENT_PROFILES ||--o{ CLINICAL_EVENTS : has

  PATIENT_PROFILES ||--o{ CLINICAL_EVENT_UPDATES : submits
  CLINICAL_EVENTS ||--o{ CLINICAL_EVENT_UPDATES : receives
  USERS ||--o{ CLINICAL_EVENT_UPDATES : submitted_by

  PATIENT_PROFILES ||--o{ MEDICAL_RECORDS : owns
  PATIENT_PROFILES ||--o{ MEDICAL_HISTORY_REVIEWS : reviewed
  DOCTOR_PROFILES ||--o{ MEDICAL_HISTORY_REVIEWS : performs
  PATIENT_PROFILES ||--o{ PATIENT_ALLERGIES : has
  USERS ||--o{ PATIENT_ALLERGIES : records
  PATIENT_PROFILES ||--o{ CHRONIC_DISEASES : has
  USERS ||--o{ CHRONIC_DISEASES : records
  PATIENT_PROFILES ||--o{ VISIT_HISTORY : has
  CLINICAL_EVENTS ||--o{ VISIT_HISTORY : contextualizes
  USERS ||--o{ VISIT_HISTORY : records
  PATIENT_PROFILES ||--o{ DIAGNOSES : has
  CLINICAL_EVENTS ||--o{ DIAGNOSES : contextualizes
  USERS ||--o{ DIAGNOSES : records

  PATIENT_PROFILES ||--o{ MEDICATIONS : has
  CLINICAL_EVENTS ||--o{ MEDICATIONS : contextualizes
  PATIENT_PROFILES ||--o{ PRESCRIPTIONS : has
  CLINICAL_EVENTS ||--o{ PRESCRIPTIONS : contextualizes
  USERS ||--o{ PRESCRIPTIONS : prescribes
  PRESCRIPTIONS ||--o{ PRESCRIPTION_MEDICATIONS : contains
  MEDICATIONS ||--o{ PRESCRIPTION_MEDICATIONS : may_reference
  PATIENT_PROFILES ||--o{ MEDICATION_REMINDERS : has
  CLINICAL_EVENTS ||--o{ MEDICATION_REMINDERS : contextualizes
  MEDICATIONS ||--o{ MEDICATION_REMINDERS : schedules
  PRESCRIPTION_MEDICATIONS ||--o{ MEDICATION_REMINDERS : schedules

  USERS ||--o{ NOTIFICATIONS : receives
  PATIENT_PROFILES ||--o{ NOTIFICATIONS : about
  CLINICAL_EVENTS ||--o{ NOTIFICATIONS : about
  PATIENT_PROFILES ||--o{ DOCTOR_NOTES : has
  DOCTOR_PROFILES ||--o{ DOCTOR_NOTES : writes
  CLINICAL_EVENTS ||--o{ DOCTOR_NOTES : contextualizes

  PATIENT_PROFILES ||--o{ DEMO_MEDICAL_ASSETS : has
  USERS ||--o{ DEMO_MEDICAL_ASSETS : uploads
  PATIENT_PROFILES ||--o{ MEDICAL_IMAGING_ASSETS : has
  CLINICAL_EVENTS ||--o{ MEDICAL_IMAGING_ASSETS : contextualizes
  USERS ||--o{ MEDICAL_IMAGING_ASSETS : uploads
  USERS ||--o{ MEDICAL_IMAGING_ASSETS : reviews
  PATIENT_PROFILES ||--o{ SIMULATED_ASSESSMENTS : has
  USERS ||--o{ SIMULATED_ASSESSMENTS : runs

  PATIENT_PROFILES ||--o{ RECOVERY_PLANS : has
  DOCTOR_PROFILES ||--o{ RECOVERY_PLANS : owns
  CLINICAL_EVENTS ||--o{ RECOVERY_PLANS : contextualizes
  USERS ||--o{ RECOVERY_PLANS : reviews
  RECOVERY_PLANS ||--o{ RECOVERY_TASKS : contains
  PATIENT_PROFILES ||--o{ RECOVERY_TASKS : assigned_to
  MEDICATIONS ||--o{ RECOVERY_TASKS : may_reference
  RECOVERY_TASKS ||--o{ RECOVERY_TASK_COMPLETIONS : completed
  PATIENT_PROFILES ||--o{ RECOVERY_TASK_COMPLETIONS : completes
  USERS ||--o{ RECOVERY_TASK_COMPLETIONS : acts

  PATIENT_PROFILES ||--o{ CHAT_THREADS : has
  USERS ||--o{ CHAT_THREADS : creates
  CHAT_THREADS ||--o{ CHAT_MESSAGES : contains
  PATIENT_PROFILES ||--o{ CHAT_MESSAGES : about
  USERS ||--o{ CHAT_MESSAGES : sends
  PATIENT_PROFILES ||--o{ CONSULTATION_REQUESTS : has
  CLINICAL_EVENTS ||--o{ CONSULTATION_REQUESTS : contextualizes
  USERS ||--o{ CONSULTATION_REQUESTS : requests

  USERS ||--o{ AUDIT_EVENTS : acts
  PATIENT_PROFILES ||--o{ AUDIT_EVENTS : audited_for
  USERS ||--o{ ANALYTICS_EVENTS : emits
  PATIENT_PROFILES ||--o{ ANALYTICS_EVENTS : about
  CLINICS ||--o{ ANALYTICS_EVENTS : scoped_to
  USERS ||--o{ SUPPORT_REQUESTS : requests
  USERS ||--o{ SUPPORT_REQUESTS : assigned_to
  PATIENT_PROFILES ||--o{ SUPPORT_REQUESTS : about

  HOSPITALS ||--o{ CLINICS : contains
  HOSPITALS ||--o{ ROLE_ASSIGNMENTS : scopes
  CLINICS ||--o{ ROLE_ASSIGNMENTS : scopes
  USERS ||--o{ ROLE_ASSIGNMENTS : assigned_to
  USERS ||--o{ ROLE_ASSIGNMENTS : assigned_by
  CLINICS ||--o{ DOCTOR_TEAMS : hosts
  DOCTOR_TEAMS ||--o{ DOCTOR_TEAM_MEMBERSHIPS : includes
  USERS ||--o{ DOCTOR_TEAM_MEMBERSHIPS : member
  USERS ||--o{ DOCTOR_TEAM_MEMBERSHIPS : assigned_by
  CLINICS ||--o{ CLINIC_RESOURCES : owns
  CLINICS ||--o{ EQUIPMENT : owns
  CLINIC_RESOURCES ||--o{ EQUIPMENT : may_group
  CLINICS ||--o{ APPOINTMENTS : schedules
  PATIENT_PROFILES ||--o{ APPOINTMENTS : books
  DOCTOR_PROFILES ||--o{ APPOINTMENTS : attends
  USERS ||--o{ APPOINTMENTS : specialist
  EQUIPMENT ||--o{ EQUIPMENT_BOOKINGS : booked
  APPOINTMENTS ||--o{ EQUIPMENT_BOOKINGS : may_need
  USERS ||--o{ EQUIPMENT_BOOKINGS : requests
  PATIENT_PROFILES ||--o{ EQUIPMENT_BOOKINGS : about

  PATIENT_PROFILES ||--o{ INVOICES : billed
  CLINICS ||--o{ INVOICES : issues
  INVOICES ||--o{ PAYMENT_STATUSES : tracks
  CLINICS ||--o{ REVENUE_SUMMARIES : summarizes
```

## Entity Groups

### Identity And Access

- `users`: account identity, credentials, primary role, administrative active
  status, and nullable latest authenticated activity. UI presence is recent
  only while `last_active_at` is within the preceding 14 days; it is not
  inferred from the administrative `is_active` flag.
- `phone_verification_challenges`: short-lived, hashed, attempt-limited phone
  challenges for registration and password recovery. Pre-registration rows may
  not have a user ID until the account is created; external SMS delivery is
  integrated later without changing the verification data boundary.
- `doctor_profiles`: doctor-owned profile fields used by registration,
  account editing, hospital display, and patient workspace context.
- `patient_profiles`: patient-owned identity/profile source of truth, including
  avatar URL, location, contact preferences, height, and weight.
- `refresh_sessions`: rotating refresh-token families and logout/session
  revocation state.
- `care_relationships`: the access boundary between doctors and patients.
- `role_assignments`: future hospital/clinic-scoped roles for doctor,
  specialist, and admin administration.

### Patient And Clinical Workflow

- `clinical_events`: the care-episode object that should organize diagnoses,
  medications, prescriptions, reminders, imaging, recovery plans, notes,
  consultations, and patient updates.
- `medical_records`, `patient_allergies`, `chronic_diseases`,
  `visit_history`, and `diagnoses`: the patient medical-history layer.
- `medical_history_reviews`: doctor verification/correction metadata for
  patient-owned history without silently overwriting patient identity.
- `medications`, `prescriptions`, `prescription_medications`, and
  `medication_reminders`: medication-management and reminder state.
- `medical_imaging_assets`: real imaging metadata and review workflow.
- `demo_medical_assets`: historical/demo upload-presign foundation; should not
  be treated as the production medical-imaging source of truth.
- `recovery_plans`, `recovery_tasks`, and `recovery_task_completions`: doctor
  plan drafting/review plus patient Today completion tracking.
- `chat_threads`, `chat_messages`, and `chat_rate_limits`: educational-chat
  safety state plus text-only private conversations between actively connected
  doctors and patients. Private threads carry both participant profile IDs;
  system chat remains read-only and group chat has no persistence yet.
- `consultation_requests`: specialist consultation request/status foundation.
- `audit_events`: metadata-only audit record for sensitive workflow actions.

### Commercial And Administration Foundations

- `hospitals`, `clinics`, `doctor_teams`, and
  `doctor_team_memberships`: future clinic administration and team structure.
- `clinic_resources`, `equipment`, `appointments`, and `equipment_bookings`:
  future clinic operations and scheduling/resource-management foundation.
- `invoices`, `payment_statuses`, and `revenue_summaries`: bounded billing and
  revenue foundation.
- `analytics_events`: operational/product analytics events.
- `support_requests`: support, deletion, and feedback queue foundation.

### Governed Medical Knowledge And Retrieval

- `kb_publishers`, `kb_rights_records`, `kb_sources`, and
  `kb_source_versions`: authority, rights, searchable catalog metadata,
  immutable source lineage, review status, and audience eligibility.
- `kb_sections` and `kb_passages`: structured reviewed evidence with source
  offsets, concept tags, language/audience flags, content checksums, and
  independently controlled lexical/vector eligibility.
- `kb_terms`: reviewed Chinese/English concepts, aliases, provenance, and
  prohibited expansions used for bounded query expansion.
- `kb_reviews`: medical, native-language, rights, product, and safety review
  lineage for sources and versions.
- `kb_translation_artifacts` and `kb_translation_sections`: unofficial derived
  translations tied to one immutable source version, with provider/model/prompt
  lineage, checksums, token usage, aligned sections, and separate medical plus
  native-Chinese approval state. Their uniqueness is per source version,
  target language, model, and prompt-policy version; they never duplicate a
  `kb_sources` row or become retrieval-eligible by import alone.
- `kb_summary_artifacts`: manually reviewed English and Simplified-Chinese
  search summaries tied to one source version and its approved translation,
  with provider/model/prompt lineage, input checksums, summary checksum, token
  usage, reviewer provenance, and approval state. Approved summaries expand
  catalog matching without changing source count or passage eligibility.
- `kb_index_releases`, `kb_index_release_passages`, and
  `kb_active_index_releases`: immutable audience-specific passage membership,
  model/analyzer/reranker versions, approvals, activation, and rollback.
- `kb_retrieval_events`: metadata-only query hash/length, filters, release and
  result IDs, score summary, latency, decision, and fallback. It never stores
  raw query or passage content.

## Integrity Rules

- `users` stores account identity and role; role-specific facts live in
  `doctor_profiles` or `patient_profiles`.
- Patient profile data entered during registration or onboarding must persist
  in `patient_profiles` when the value is first-class profile state. This
  includes display name, birth date/year, sex/gender, phone, emergency contact,
  preferred language, contact preference, avatar URL, country, province, city,
  home address, height, and weight.
- Medical-history facts should live in the normalized patient-history tables
  where possible: allergies in `patient_allergies`, chronic conditions in
  `chronic_diseases`, visits in `visit_history`, diagnoses in `diagnoses`, and
  broader documents/summaries in `medical_records`.
- Doctor profile location uses the same country/province/city reference data
  in registration and account editing. Hospital association is read-only for
  doctors after registration and is changed through administrator-owned
  hospital/clinic management.
- Doctor-patient access flows through `care_relationships`; doctor screens
  should not fetch patient records outside that relationship.
- `clinical_events` are the organizing object for care work. Medications,
  prescriptions, reminders, imaging, recovery plans, notes, consultations, and
  patient updates should link to a clinical event whenever the workflow context
  exists.
- Medical-history corrections and doctor verification belong in
  `medical_history_reviews`, not by silently overwriting patient-owned identity
  fields.
- Logout/session validity belongs in `refresh_sessions`; account pages should
  call the existing logout endpoint and clear local session state after user
  confirmation.
- Password changes and phone-verified resets revoke active refresh sessions;
  verification codes are stored only as keyed hashes with expiry and attempt
  limits.
- Financial, operations, specialist, and admin tables are schema foundations.
  They should remain hidden from production-facing navigation until the matching
  workflows, authorization, validation, empty states, and tests are implemented.

## Current Caveats

- Some future/commercial tables already exist in the data foundation but do not
  yet have complete product surfaces.
- `metadata_json` and `audit_metadata_json` are intentionally flexible, but they
  should not become a dumping ground for fields that need filtering, validation,
  editing, or cross-page synchronization.
- `synthetic_identifier` is currently the patient-share code. Product copy may
  call it a patient code, but the database column remains named for historical
  compatibility.
