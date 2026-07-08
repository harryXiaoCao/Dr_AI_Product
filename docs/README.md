# Dr. AI Documentation Index

Current stage: production/commercial v1.0 Phase 2 patient/doctor core
workflows are complete locally. Phase 1 data foundation is complete, and Phase
2 now includes demographics, allergies, chronic diseases, visit history,
diagnoses, doctor notes, medication CRUD, prescription CRUD, medication/refill
reminders, metadata-only in-app queued notification records,
Tencent-COS-compatible upload metadata/finalization, imaging list/detail,
doctor-only imaging review status, recovery-plan review/approval/completion,
patient Today progress tracking, expanded care-bundle readback,
doctor/patient Flutter surfaces, focused RBAC/audit tests, and the first
frontend-only Clinical Event/Care Episode workflow clarification in doctor
Patient Management. The deeper additive backend/API Clinical Event/Care
Episode slice is now implemented locally with persisted events, nullable event
links across core Phase 2 resources, patient-own reads, and focused
RBAC/audit coverage. The latest local Phase 2 workflow polish adds derived
Clinical Event timeline readback, manual doctor-entered imaging
findings/results, event-scoped active Recovery Plan replacement, audited
doctor Medical History review overlays, and patient-submitted Clinical Event
updates that preserve doctor-owned diagnosis controls.

## Current Production Docs

- `Dr_AI_v1.0_Implementation_Plan.md` - source of truth for production v1.0
  scope, phase tracker, gates, and historical progress log.
- `Phase_0_Production_v1_Surface_Audit.md` - current surface inventory,
  classifications, product-scope decisions, and production support/admin/
  specialist judgments.
- `Phase_0_Production_v1_Closure_Record.md` - Phase 0 go/no-go closure and
  Phase 1 readiness boundary.
- `Phase_1_Production_Data_Foundation_Record.md` - Phase 1 schema/RBAC,
  support queue submission/status, data-boundary, and verification record.
- `Phase_2_Patient_Doctor_Core_Progress_Record.md` - Phase 2 patient/doctor
  core workflow closure, RBAC/audit boundary, and deferred gates.
- `Dr_AI_v1.0_API_Contract.md` - implemented beta API boundary plus reserved
  production v1.0 contract gaps.
- `Dr_AI_v1.0_Design_Freeze.md` - doctor/patient visual baseline from the
  historical beta foundation; not evidence for specialist/admin/support
  production surfaces.

## Historical Beta Records

Historical invited-beta milestones, release notes, staging records, checklist
evidence, and beta web-staging architecture notes live in `beta/`.

Use these records for provenance and regression context. Do not treat beta
completion as production v1.0 completion.

## Evidence Folders

- `design-evidence/` - doctor and patient design exports used by the design
  freeze.
- `release-evidence/` - non-secret public-route screenshots captured during
  beta release preparation.

## Next Production Phase

The doctor Patient Management workspace now uses an active Clinical Event
context for event create/update/select and event-linked medication,
prescription, imaging, recovery-plan, medical-history review, and consultation
writes. The eight-functionality Phase 2 workflow-clarification list is closed
locally. Phase 3 AI systems must not start without explicit approval.
External push, SMS, email, and native notification delivery remain gated
beyond the Phase 2 metadata-only in-app queue path. Phase 5 still owns
specialist/admin UI, audit search, system status, and admin-managed
support/deletion/feedback queue handling. Phase 6 tracks the production
multilingual foundation for Simplified Chinese and English.
