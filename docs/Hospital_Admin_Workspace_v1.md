# Hospital operations workspace v1

## Evidence and scope

The current schema has `hospitals`, `clinics` (the department-like unit),
`role_assignments`, `doctor_teams`, `clinic_resources`, `equipment`,
`equipment_bookings`, `appointments`, and `audit_events`. Bookings are linked
to equipment, which is linked to a clinic and hospital. Appointments have a
clinic. This supports hospital-scoped operational demand and status counts.

Consultation and payer requests do not consistently carry a hospital/clinic
key. Clinical Event Intelligence and payer signals are not quality or
eligibility outcomes. They are excluded from the admin workspace. Existing
doctor teams have no established management workflow; v1 manages department
access through `role_assignments` rather than creating a second membership
system.

## Information architecture

- **Demand:** status counts for equipment bookings and appointments, scoped to
  authorized departments. `completed` is a recorded workflow state, not a
  measure of treatment success.
- **Requests:** filtered, newest-first equipment booking queue, 25 per page.
  Shows department, equipment, time, purpose, status, and valid next actions.
- **Resources:** equipment/resource availability and recorded capacity by
  department. Admins set `available`, `limited`, or `unavailable` with a reason.
- **Staff access:** active and revoked doctor assignments per department.
  Admins grant or revoke an existing doctor's department access by account
  email, with a reason. Doctors see only their active departments' resources.

The workspace does not display patient identifiers. Status counts are raw
operational records, not adjusted rates; no inferred quality score is shown.

## Permissions and workflow

Admin users are provisioned through `scripts/provision_hospital_admin.py` in a
local/test backend process. Each user has their own email/password and an
active `admin` role assignment linked to one hospital. A hospital-wide
assignment permits all its active clinics; a clinic assignment permits only
that clinic. Multiple distinct admin users may be assigned to one hospital.
Public registration accepts only doctor, patient, and payer roles. There is
no admin enrollment in the app.

All workspace and mutation endpoints derive the hospital and permitted clinic
IDs from the authenticated user's live role assignments. A foreign clinic,
resource, or booking returns 404. The doctor availability endpoint separately
requires a current doctor assignment for each department. Revocation removes
its resources from the next read, including direct API calls.

Booking transitions are `requested → approved | declined`, then `approved →
completed | cancelled`. Approval requires available equipment and resource,
and no overlapping approved booking. Invalid transitions, duplicates,
unavailable equipment, and overlaps return conflicts. These actions are
operational scheduling decisions; they do not make clinical or coverage
determinations. Resource capacity cannot exceed recorded total capacity.
Staff access changes require an active doctor account; a doctor with an
active assignment to another hospital cannot be granted access here.

Successful resource, booking, and staff changes add an `audit_events` row in
the same transaction: actor user ID, event type, resource ID, hospital and
clinic IDs, previous state, next state, reason, and timestamp. The
provisioning command also audits each new admin account. The UI requires a
reason and shows save/failure feedback; server validation remains authoritative.

## Local use

No new database migration is required. Existing foundation tables are used.
Apply the existing Alembic migrations before first use. In `services/api`, run
`python -m scripts.provision_hospital_admin --email PERSON@example.com
--hospital-id HOSPITAL_UUID` and enter a unique password at the prompt.
Add `--clinic-id CLINIC_UUID` to limit an admin to one department. Run the
command once per person. For local demonstration data only, run
`python -m scripts.seed_hospital_admin_demo` first and enter a separate
synthetic doctor password.

## Limits

Resource availability is a recorded planning signal and is not guaranteed
real-time capacity. Appointment outcomes are status counts only. The queue
does not create bookings; it acts on existing bookings. Staff access controls
the new hospital availability view and admin operations, while existing
clinical patient access continues to use its established care relationship
rules. No patient or payer decisions are transferred to admins.
