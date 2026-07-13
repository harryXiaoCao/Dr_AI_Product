# Dr. AI Documentation Index

Current stage: Phase 2 patient/doctor workflow foundations and the Phase 2.5
product-quality gate are complete. Chatbot evaluation is reported complete,
and Phase 3 chatbot development planning is active. The product-quality gate
remains a regression standard, while the next blocking work is the governed
medical knowledge/retrieval foundation and its medical, native-Chinese,
privacy, legal, provider, security, and regulatory release gates.

## Current Production Docs

- `Dr_AI_v1.0_Implementation_Plan.md` - source of truth for production v1.0
  scope, phase tracker, gates, and historical progress log.
- `Dr_AI_v1.0_Product_Quality_Gate.md` - completed pre-Phase-3 product-quality
  gate and continuing regression standard for real-app UX, aesthetics,
  onboarding, profile, and production copy.
- `Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md` - frozen intended use,
  prohibited behavior, rural-China usage model, patient-context boundary, and
  safety acceptance criteria for the first Phase 3 chatbot deliverable.
- `Phase_3_Chatbot_Evaluation_and_Model_Strategy.md` - consolidated research
  record for evaluation datasets, the private rural-China suite, model
  benchmarking, selection, fine-tuning, architecture, and deployment gates.
- `Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md` - approved
  planning baseline for the doctor Resources page, constrained patient-chat
  agent flow, authoritative Chinese/WHO retrieval, knowledge-base schema,
  source rights/version governance, and adapter recommendation.
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

## Current Production Phase

The doctor Patient Management workspace now uses an active Clinical Event
context for event create/update/select and event-linked medication,
prescription, imaging, recovery-plan, medical-history review, and consultation
writes. The eight-functionality Phase 2 workflow-clarification list is closed
locally, and manual inspection should use invited sign-up plus patient-code
connection to create data from zero.

The current phase is **Phase 3 AI systems**, beginning with the bounded patient
chatbot, doctor Resources page, and governed Chinese/WHO retrieval foundation.
The implementation sequence and release gates are frozen in
`Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`.
External push, SMS, email, and native notification delivery remain gated
beyond the Phase 2 metadata-only in-app queue path. Phase 5 still owns
specialist/admin UI, audit search, system status, and admin-managed
support/deletion/feedback queue handling. Phase 6 tracks the production
multilingual foundation for Simplified Chinese and English.
