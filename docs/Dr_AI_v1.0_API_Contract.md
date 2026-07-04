# Dr. AI v1.0 API Contract

Status: authentication and Week 1 dashboard reads implemented; deferred
clinical endpoints remain unavailable

Contract version: `1.0.0`

Recorded: 2026-07-04; authentication models frozen: 2026-07-04

This contract defines the public HTTP boundary planned for Dr. AI v1.0. The
current Week 1 backend exposes the authentication, identity, assigned-patient,
and synthetic dashboard reads identified below. Every clinical route remains
reserved for its scheduled week and must not be inferred to be available.

Dr. AI v1.0 is an invited, non-clinical beta. It uses synthetic demonstration
content only, accepts no real patient data, and provides no diagnosis or
medical advice.

## Transport and representation

- HTTPS is required outside local development.
- JSON is the default request and response representation.
- Timestamps use RFC 3339 UTC strings, for example
  `2026-07-04T08:30:00Z`.
- Resource identifiers are opaque strings. Clients must not infer meaning from
  them.
- The maximum request size, upload media types, rate limits, and pagination
  limits will be set before their corresponding endpoints are implemented.
- Secrets, raw tokens, medical content, and real patient data must not appear
  in URLs, logs, fixtures, or error messages.

## Implemented authentication models

Invited registration is disabled for a role when its server-side invite code is
unset. The role comes from the accepted invitation and is persisted by the
server; Flutter cannot elevate it.

### `POST /api/v1/auth/register`

Request:

```json
{
  "email": "new.patient@example.com",
  "password": "user-supplied minimum 12 characters",
  "role": "patient",
  "invite_code": "server-issued opaque invitation"
}
```

The password is limited to 128 characters. An invalid invitation returns
`403 forbidden`; an existing normalized email returns `409 conflict`.

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
| `GET` | `/api/v1/patients/{patient_id}` | Assigned patient | Own record only | Read a patient summary |
| `GET` | `/api/v1/patients/{patient_id}/records` | Assigned patient | Own records only | List medical-record fixtures |
| `POST` | `/api/v1/patients/{patient_id}/assets/presign` | Assigned patient | Own assets only | Request a short-lived demo upload URL |
| `GET` | `/api/v1/patients/{patient_id}/assessments` | Assigned patient | Own results only | List assessment summaries |
| `POST` | `/api/v1/patients/{patient_id}/assessments` | Assigned patient | No | Run a deterministic simulation |
| `GET` | `/api/v1/patients/{patient_id}/recovery-plans` | Assigned patient | Own plans only | List recovery plans |
| `POST` | `/api/v1/patients/{patient_id}/recovery-plans` | Assigned patient | No | Create a draft recovery plan |
| `GET` | `/api/v1/patient/me/today` | No | Own data | Read the patient's current synthetic tasks |
| `GET` | `/api/v1/medications` | Assigned patient scope | Own data | List medication fixtures |
| `GET` | `/api/v1/reminders` | Assigned patient scope | Own data | List reminders |
| `POST` | `/api/v1/chat/threads/{thread_id}/messages` | Authorized thread | Own thread | Send an educational-chat message |
| `GET` | `/api/v1/consultations` | Authorized cases | Own requests | List consultation requests |
| `POST` | `/api/v1/consultations` | Assigned patient | No | Request asynchronous specialist review |
| `GET` | `/api/v1/audit-events` | Administrator only | No | Read security audit metadata |

The singular `/patient/me/today` path is intentional and is implemented for
the Week 1 patient dashboard. It represents the
current patient's own view and is distinct from doctor-scoped `/patients`.
`GET /api/v1/patients`, `GET /api/v1/patients/{patient_id}`, and
`GET /api/v1/me/dashboard` are also implemented for the Week 1 gate. All other
paths in this table remain unavailable.

## Public enums

Wire values are lowercase strings.

```text
UserRole = doctor | patient
AssessmentMode = simulated | validated_model
AssessmentStatus = queued | completed | failed
InputCompleteness = complete | partial | insufficient
RiskBand = low | moderate | high
ConsultationStatus = requested | accepted | completed | cancelled
RecoveryPlanStatus = draft | active | completed
```

`validated_model` is reserved for a future independently validated adapter. It
must be rejected in the v1 beta until model code, weights, preprocessing,
governance, and release approval exist. Adding a new enum value is treated as a
contract change and requires client compatibility review.

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
| `503` | `service_unavailable` |
| `500` | `internal_error` |

Cross-patient and wrong-role access returns a neutral `404 not_found` when
revealing that the resource exists would leak sensitive information.

## Role and ownership boundaries

- Authentication does not grant access to patient-owned data by itself.
- A doctor can access a patient-owned resource only through an active
  `CareRelationship`.
- A patient can access only resources whose `patient_id` is their own.
- A specialist can access only consultation data explicitly assigned to them;
  specialist behavior is not otherwise implemented in the Days 1-2
  foundation.
- Only an administrator can call `/api/v1/audit-events`. No administrator UI
  is in the v1 golden workflow.
- The server enforces every boundary. Flutter route guards are navigation
  assistance, not authorization.
- Sensitive reads, mutations, uploads, assessments, consultation changes, and
  chat escalations create audit events without copying medical content into
  logs.

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
- [Week 1 Days 1-2 foundation record](Week_1_Days_1_2_Foundation_Record.md)
