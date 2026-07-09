# Dr. AI Documentation Index

Current stage: Phase 2 patient/doctor workflow foundations are implemented,
but the product is not yet commercial-quality. The next source-of-truth gate is
`Dr_AI_v1.0_Product_Quality_Gate.md`: Phase 3 AI systems must not begin until
the app feels like a real healthcare product with credible typography,
patient avatar/profile setup, guided first-use onboarding, useful empty
states, and normal user flows that are not dominated by synthetic/demo
language.

## Current Production Docs

- `Dr_AI_v1.0_Implementation_Plan.md` - source of truth for production v1.0
  scope, phase tracker, gates, and historical progress log.
- `Dr_AI_v1.0_Product_Quality_Gate.md` - blocking product-quality gate before
  Phase 3; defines real-app UX, aesthetic, onboarding, profile, and demo-copy
  cleanup requirements.
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
- `Dr_AI_v1.0_Design_Freeze.md` - historical doctor/patient beta visual
  baseline only. It is not sufficient evidence that the current product is
  production-quality.

## Historical Beta Records

Historical invited-beta milestones, release notes, staging records, checklist
evidence, and beta web-staging architecture notes live in `beta/`.

Use these records for provenance and regression context. Do not treat beta
completion as production v1.0 completion.

Phase closure records are evidence logs. They should not override the current
source of truth in the implementation plan and product-quality gate.

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
locally, and manual inspection should use invited sign-up plus patient-code
connection to create data from zero.

The next phase is **Phase 2.5 Product Quality and First-Use Readiness**, not
Phase 3 AI. Phase 3 AI systems must not start until the product-quality gate is
closed.
External push, SMS, email, and native notification delivery remain gated
beyond the Phase 2 metadata-only in-app queue path. Phase 5 still owns
specialist/admin UI, audit search, system status, and admin-managed
support/deletion/feedback queue handling. Phase 6 tracks the production
multilingual foundation for Simplified Chinese and English.
