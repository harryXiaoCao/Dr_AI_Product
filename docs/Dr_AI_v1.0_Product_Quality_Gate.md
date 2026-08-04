# Dr. AI v1.0 Product Quality Gate

Created: 2026-07-09

## Product Principles Going Forward

1. **Build a real app before a smarter app.**
   Please always keep in mind that we are developing a production-ready product but not a beta version.

2. **Aesthetic quality is a functional requirement.**
   Fonts, spacing, color, icons, avatar treatment, empty states, and copy are
   not decorations. They decide whether a doctor or patient trusts the product.

3. **No test vocabulary in normal product flows.**
   "Synthetic", "demo", "fixture", "seed", and similar words belong in
   developer docs, staging safety notes, and test harnesses. Normal users
   should see clear staging/no-real-data framing without the app feeling fake.

4. **Every screen needs one primary job.**
   A screen that exposes many unrelated actions at once is not production
   ready, even if all buttons call real endpoints.

5. **Empty state is onboarding.**
   A blank workspace must explain the next useful action: complete profile,
   add medical history, connect a doctor, create a Clinical Event, or review a
   care plan.

6. **Healthcare tone must be calm and precise.**
   Copy should be reassuring, non-dramatic, clinically careful, and free of
   claims the product cannot support.

7. **Price the care source, not its paperwork.**
   Financial status and its next action must be visible on the medication or
   Clinical Service record. Appointments schedule, services represent care,
   and uploads/reports provide evidence; the UI must not imply that a booking,
   document, image, report, diagnosis, note, or observation is automatically a
   separate charge.

8. **Make chatbot grounding unmistakable.**
   Reviewed Dr. AI evidence, general model knowledge, and server-owned fixed
   safety copy must never look interchangeable. A general-model answer shows a
   conspicuous no-supporting-source label and no Sources section; an approved
   answer shows actionable reviewed source cards; an emergency or provider
   failure remains visibly server-controlled. An AI disclosure supplements,
   but never replaces, deterministic emergency, authorization, privacy, record,
   and action boundaries.

## Controlled-Staging Operational Gate

A product-quality implementation is not operationally complete merely because
its local tests pass. Before a controlled-staging phase closes:

- the deployed API, retrieval, web, and schema identities must be immutable and
  recorded;
- pre-change and post-change backups must be owner-only, checksum-verified, and
  listable or restorable;
- enabled AI purposes must have separate compatible governed releases and must
  return to the documented disabled state after exercise;
- patient, doctor, and payer authentication, authorization, idempotency,
  conflict, history, and neutral-denial paths must pass against the deployed
  system;
- mobile, tablet, and desktop rendered states must be inspected in addition to
  executable localization/accessibility coverage;
- logs and closure artifacts must pass presence-only or count-only redaction
  scans; and
- exact predecessor rollback and recovery must be exercised without using a
  missing provider credential, approval, receipt, or physical target as
  fabricated completion evidence.

Phase 7 met this gate for controlled synthetic staging. External notification
display, multimodal DeepSeek capability, real-patient, live-payer,
public-production, and commercial authorization remain separate gates.

## Clinical Event Intelligence Gate

The 2026-08-01 implementation passes its local wholly synthetic gate only when
all of the following remain true: migration downgrade/re-upgrade and schema
drift checks pass; every requested line appears exactly once; all six score
dimensions and deterministic aggregation validate; tier 5 is visibly
exploratory with zero cost-alignment weight; authorization and revoked-scope
tests fail closed; provider failure preserves human documentation,
`pending_cost`, clarification, and review workflows; and patient, doctor, and
payer mobile/desktop states pass Flutter analysis, tests, and rendered review.
No result from this gate activates a purpose release or closes clinical,
privacy, payer, regulatory, or production-deployment authorization.

## Clinical Event Intelligence controlled-synthetic activation evidence

The 2026-08-02 activation gate additionally requires three independent active
v5 releases with matching source, payload, evaluation-manifest, and result
checksums; clear purpose kill switches; `ready` health status; a successful
wholly synthetic primary/critic run; persisted role-and-locale explanations;
same-key retry/concurrency proof; authorization and leakage attacks; exact
v5-to-v4 rollback and restoration; and visual inspection of all three roles in
English/Simplified Chinese at mobile/desktop widths. The machine-readable
activation result and dated implementation record are the evidence index.

Passing this gate remains local synthetic evidence only and must not be
reported as clinical, payer, legal, privacy, security, regulatory, commercial,
or public-production approval.

## Clinical workflow integrity gate (2026-08-02)

The slice passes only when focused tests prove canonical dropdown safety,
field-preserving recovery validation, source-cost uniqueness, incomplete-cost
payer rejection, multi-line atomic prescription persistence, finalized and
published immutability, supersession readback, authorization failures, and
same-key retry/concurrency. Migration `0058` must downgrade to `0057`, re-upgrade
to head, and produce no Alembic operations. FastAPI and Flutter suites, Ruff,
Flutter analysis, relevant rendered English/Chinese mobile/desktop workflows,
browser/API logs, and `git diff --check` must also be inspected.

The UI gate also requires the Consultation section to remain specialist-request
only, while ordinary doctor consultations, encounter updates, and diagnoses
append and read back inside the selected Clinical Event without hidden database
edits.

Passing is local wholly synthetic engineering evidence. It is not clinical
validation, official pricing, payer acceptance, privacy/security certification,
legal/regulatory approval, real-patient authorization, or public-production
readiness.
