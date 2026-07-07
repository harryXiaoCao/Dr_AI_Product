# Dr. AI Documentation Index

Current stage: production/commercial v1.0 Phase 1 data foundation is complete.
Phase 1 adds production schema foundations, fail-closed role boundaries,
route-level RBAC helpers, and authenticated support/deletion/feedback
submission plus requester-scoped status endpoints. Phase 2 workflows have not
started.

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

Phase 2 is the next production phase and should start only when explicitly
requested. Phase 5 still owns specialist/admin UI, audit search, system
status, and admin-managed support/deletion/feedback queue handling.
