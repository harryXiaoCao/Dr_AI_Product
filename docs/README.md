# Dr. AI Documentation Index

Current stage: Phases 1-4 are locally complete as one synthetic
patient/doctor/payer product foundation through migration `0051`. Clinical
Event, Clinical Service, persisted role destinations, imaging-byte
provenance, manual payer transitions, source-linked care cost,
governed-knowledge, and bounded-chatbot workflows are implemented.
Provider-neutral scenario/care-plan/pricing/utilization
release persistence and the model-free deterministic comparison engine are
also implemented internally, including database-backed active-release
resolution and an authorized Clinical Event/payer-request orchestration path.
Slice D's separate schema-constrained expected-care candidate purpose is also
implemented internally with immutable lineage, deterministic revalidation,
provider-stub tests, an independent paid synthetic evaluation, and a
default-off kill switch. Slice E adds the
immutable system baseline and separate append-only clinician responses. Slices
F/G add versioned deterministic comparison, a canonical bilingual claim graph,
executable paid DeepSeek gates, append-only operational transitions, and
pending v3. Four governed synthetic reference families exercise the product;
the real-world Shanghai candidate stays blocked. Baseline display and
comparison do not require clinician concurrence. The product-quality gate
remains a regression standard. No real-data, live-payer, public-production, or
commercial release is active.

## Current Production Docs

- `Dr_AI_v1.0_Implementation_Plan.md` - source of truth for production v1.0
  scope, phase tracker, gates, and historical progress log.
- `Dr_AI_v1.0_AI_Platform_Architecture.md` - provider-neutral AI control plane,
  implemented-versus-planned AI portfolio, DeepSeek cost-envelope boundary,
  deterministic authority, human review, fallback, evaluation, and staged
  implementation sequence.
- `Dr_AI_v1.0_First_Scenario_Reference_Boundary.md` - Slice A evidence audit,
  selected Shanghai outpatient single-region CT plain-scan candidate, frozen
  applicability/reference/fixture boundary, and explicit blocked activation
  gates for rights, named review, and usable price/range evidence.
- `Dr_AI_v1.0_ERD.md` - implemented and explicitly planned data boundary.
- `Dr_AI_v1.0_API_Contract.md` - implemented API boundary; planned AI and
  payer/cost routes stay out until their state and authorization contracts are
  fixed.
- `Dr_AI_v1.0_Product_Quality_Gate.md` - completed pre-Phase-3 product-quality
  gate and continuing regression standard for real-app UX, aesthetics,
  onboarding, profile, and production copy.
- `periodic_dev_docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md` -
  frozen intended use,
  prohibited behavior, rural-China usage model, patient-context boundary, and
  safety acceptance criteria for the first Phase 3 chatbot deliverable.
- `chatbot-evaluation/Phase_3_Chatbot_Evaluation_and_Model_Strategy.md` -
  consolidated research
  record for evaluation datasets, the private rural-China suite, model
  benchmarking, selection, fine-tuning, architecture, and deployment gates.
- `periodic_dev_docs/Phase_3_Chatbot_RAG_Agentic_Architecture_and_Knowledge_Base.md`
  - approved
  planning baseline for the doctor Resources page, constrained patient-chat
  agent flow, authoritative Chinese/WHO retrieval, knowledge-base schema,
  source rights/version governance, and adapter recommendation.
- `periodic_dev_docs/Phase_0_Production_v1_Surface_Audit.md` - surface
  inventory,
  classifications, product-scope decisions, and production support/admin/
  specialist judgments.
- `periodic_dev_docs/Phase_0_Production_v1_Closure_Record.md` - Phase 0 go/no-go closure and
  Phase 1 readiness boundary.
- `periodic_dev_docs/Phase_1_Production_Data_Foundation_Record.md` - Phase 1 schema/RBAC,
  support queue submission/status, data-boundary, and verification record.
- `periodic_dev_docs/Phase_1_4_Live_Gap_Matrix_2026-07-27.md` - repository and
  rendered-product gap matrix rebuilt from the final Phase 1-4 source state.
- `periodic_dev_docs/Phase_1_4_Closure_Record_2026-07-27.md` - integrated
  implementation, verification, immutable-evidence compatibility, and
  concrete external-condition record for Phase 1-4 closure.
- `periodic_dev_docs/Phase_2_Patient_Doctor_Core_Progress_Record.md` - Phase 2 patient/doctor
  core workflow closure, RBAC/audit boundary, and deferred gates.
- `periodic_dev_docs/Phase_4_Slices_B_C_Care_Reference_Foundation_Record.md` -
  governed care-reference persistence, deterministic comparison engine,
  synthetic fixture boundary, migration evidence, and local verification.
- `periodic_dev_docs/Phase_4_Slice_D_Expected_Care_Candidate_Record.md` -
  separate expected-care purpose contract, immutable candidate persistence,
  provider-stub verification, failure boundaries, and remaining Slice E gates.
- `periodic_dev_docs/Phase_4_Slice_E_Doctor_Review_and_Presentation_Record.md` -
  append-only doctor-review lifecycle, deterministic revalidation, role-scoped
  routes, bilingual rendered evidence, and remaining Slice F/live gates.
- `periodic_dev_docs/Phase_4_Slices_F_G_Comparison_Explanation_Governance_Record.md`
  - deterministic comparison, role fact objects, paid DeepSeek evaluation,
  pending release, rollback, role UI, and verification evidence.
- `runbooks/Expected_Care_Explanation_Controlled_Staging_Runbook.md` -
  backup-first controlled-staging, synthetic walkthrough, activation, and
  rollback boundary.
- `beta/Dr_AI_v1.0_Design_Freeze.md` - historical doctor/patient beta visual
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

The current direction is the China-first, multi-scenario, three-party
care-and-cost platform recorded in the PRD and implementation plan. The
patient chatbot and governed medical knowledge retain independent production
evidence gates. The coherent AI sequence and current state are:

1. freeze the first scenario and usable reference boundary - complete, with
   the selected CT reference still blocked;
2. implement versioned scenario, care-plan, pricing, and utilization-rule data
   - complete with synthetic-only verification;
3. implement the deterministic range/comparison engine without AI - complete
   as an internal service, including exact active-bundle resolution,
   authorization, immutable persistence, rollback, and stale-release
   suppression;
4. add a separate schema-constrained DeepSeek expected-care candidate purpose
   - complete with stub verification, paid synthetic executable gates, and a
     separate pending release;
5. publish the baseline independently and retain clinician responses as
   separate evidence - complete locally;
6. add deterministic comparison and validated role explanation - complete
   locally; and
7. evaluate and release each purpose independently - complete for the current
   synthetic stage with truthful product-owner waivers; pending releases remain
   kill-switched and all future real-world gates remain separate.

The detailed boundary is frozen in
`Dr_AI_v1.0_AI_Platform_Architecture.md`. External notification delivery,
specialist/admin/clinic operations, live claims/coverage/payment, real-patient
use, and public production activation remain separately gated.
