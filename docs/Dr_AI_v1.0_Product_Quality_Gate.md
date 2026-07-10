# Dr. AI v1.0 Product Quality Gate

Status: blocking gate before Phase 3 AI work

Created: 2026-07-09

## Why This Gate Exists

Phase 2 made the patient/doctor workflow more coherent at the data and API
level, but the visible application is not yet a commercial, production-quality
healthcare product. The current app still feels like an engineering prototype:
too much test vocabulary, too many exposed implementation concepts, weak first
use guidance, missing patient identity setup, and a visual system that does not
yet communicate trust.

This is not a cosmetic concern. In a healthcare app, aesthetic quality,
typography, information hierarchy, and onboarding clarity are part of product
safety and user trust. A patient or doctor who sees rough typography,
placeholder-like content, or repeated "synthetic/demo" wording will reasonably
assume the product is not ready for serious use.

Phase 3 AI systems must not begin until this gate is closed. Adding AI on top
of an unconvincing product surface would make the product feel less credible,
not more advanced.

## Current Product Diagnosis

The following issues are blockers, not polish:

- The app does not yet feel like a real commercial mobile/web application.
- The typography, spacing, and hierarchy feel generic and unfinished.
- Patient onboarding does not guide a real person through identity, profile,
  medical history, and doctor connection.
- The patient avatar/profile entry point is not treated as the obvious place
  for profile setup and editing.
- Basic patient profile fields are not presented as a first-class journey:
  avatar, display name, birth date or age, sex/gender, contact number,
  emergency contact, preferred language, and contact preference.
- User-facing surfaces still expose too much "synthetic", "demo", and test
  language. That language is acceptable in documentation, logs, fixtures, and
  staging safety banners, but it should not dominate the normal app workflow.
- Empty states are technically present but not product-led. They should tell
  the user what to do next.
- The doctor workspace is structurally better after Phase 2, but still feels
  dense and admin-like rather than calm, clinical, and action-oriented.
- The patient dashboard does not yet feel like a guided care companion. It
  lacks a clear first-week journey and a humane sense of "what happens next".
- Documentation has grown large enough that future work can accidentally
  follow stale beta/demo assumptions unless the current source-of-truth path is
  clear.

## Product Principles Going Forward

1. **Build a real app before a smarter app.**
   Phase 3 AI is deferred until the non-AI product feels credible.

2. **Aesthetic quality is a functional requirement.**
   Fonts, spacing, color, icons, avatar treatment, empty states, and copy are
   not decorations. They decide whether a doctor or patient trusts the product.

3. **Patient identity comes first.**
   A patient should be able to create an account, add their name and core
   profile, see their avatar/profile settings, share a patient code, and
   understand the next step without seeing database or fixture language.

4. **Doctors review patient identity; patients own it.**
   Doctors should see a clean read-only patient profile summary and request
   correction when needed. Doctors should not casually overwrite patient-owned
   identity fields.

5. **No test vocabulary in normal product flows.**
   "Synthetic", "demo", "fixture", "seed", and similar words belong in
   developer docs, staging safety notes, and test harnesses. Normal users
   should see clear staging/no-real-data framing without the app feeling fake.

6. **Every screen needs one primary job.**
   A screen that exposes many unrelated actions at once is not production
   ready, even if all buttons call real endpoints.

7. **Empty state is onboarding.**
   A blank workspace must explain the next useful action: complete profile,
   add medical history, connect a doctor, create a Clinical Event, or review a
   care plan.

8. **Healthcare tone must be calm and precise.**
   Copy should be reassuring, non-dramatic, clinically careful, and free of
   claims the product cannot support.

## Required Work Before Phase 3

### 1. Documentation And Scope Cleanup

- Make this file and `Dr_AI_v1.0_Implementation_Plan.md` the first read for
  future work.
- Keep historical beta/demo records under `docs/beta/` as provenance only.
- Avoid adding more long progress logs unless they change the source of truth.
- Summarize outdated details instead of letting old beta assumptions compete
  with current product direction.

### 2. Product Surface Audit With Screenshots

- Inspect the live staging app as a user, not only through tests.
- Capture current patient and doctor screenshots.
- Mark each screen as production-ready, needs redesign, or should be hidden.
- Record the actual user confusion points: unclear next step, poor typography,
  crowded layout, missing profile entry, visible test language, or weak empty
  state.

### 3. Visual System Reset

- Choose and document a production font strategy for English and Simplified
  Chinese.
  - Approved 2026-07-10: Inter for Latin text and Noto Sans SC for Simplified
    Chinese. Both variable fonts and their OFL license text are bundled in the
    Flutter application; platform fonts remain fallbacks only.
- Define type scale, line height, color roles, spacing, surfaces, avatar
  treatment, status chips, form fields, and button hierarchy.
- Review the proposed English/Simplified Chinese font pairing with the product
  owner before changing the production theme.
  - Complete: the product owner selected Inter + Noto Sans SC after reviewing
    matched bilingual Dr. AI interface specimens.
- Use one restrained page-transition language across role routes and honor the
  platform reduced-motion preference.
- Replace generic/default-looking typography and inconsistent card density.
- Avoid decorative clutter. The visual tone should be clinical, warm, calm,
  and premium enough for a commercial healthcare product.
- Verify the result on mobile and desktop screenshots, not just widget tests.

### 4. Patient Onboarding And Profile

- New patient first run should guide the patient through:
  - account creation with a required phone number and optional email;
  - verification-code entry;
  - avatar/profile setup;
  - display name;
  - birth date or age;
  - sex/gender;
  - contact number;
  - emergency contact;
  - preferred language;
  - contact preference;
  - medical-history setup entry point.
- The patient avatar/profile entry point should open profile editing.
- Patient and doctor account editing must accept Unicode profile text and an
  optional email that can be added, changed, or removed.
- A one-character Chinese family name must not be rejected by a two-character
  Western-name assumption.
- Doctor Account must show the recorded phone and available email. Its active
  status is true only when authenticated activity occurred within 14 days.
- The patient dashboard should show a clear next step if profile/history is
  incomplete.
- The patient code should be easy to share with a doctor, but it should not be
  the emotional center of the patient experience.

### 5. Doctor Onboarding And Patient Connection

- A doctor should understand the workflow in this order:
  1. create or sign in to an approved doctor account;
  2. complete doctor identity/profile basics if missing;
  3. connect a patient by patient-shared code;
  4. review patient profile and medical history;
  5. create or select a Clinical Event;
  6. manage prescriptions, recovery plan, imaging, and consultation inside the
     event context.
- The doctor workspace must not feel like disconnected CRUD panels.
- Doctor copy should use clinical workflow language, not implementation terms.

### 6. Demo And Seed Language Cleanup

- Keep seeded data available only for regression and smoke checks.
- Manual staging inspection should start from invited sign-up and user-created
  records.
- Replace normal-flow copy that says "synthetic", "demo", or "fixture" with
  production-quality user language.
- Keep a concise staging banner or environment notice that says no real
  patient data should be entered.
- If old staging data becomes distracting, wipe or archive it only through a
  separately confirmed staging-only reset.

### 7. Real Empty States

Every major empty state must answer:

- What is missing?
- Why does it matter?
- What should the user do next?
- Who owns the next action: patient, doctor, or system?

Examples:

- New patient: "Complete your profile so your doctor can recognize your
  account."
- New patient with no doctor: "Share your patient code with your doctor."
- New doctor with no patients: "Connect a patient using the code they share."
- New event with no plan: "Create a recovery plan for this Clinical Event."

### 8. Production Readiness Review

Before Phase 3 starts, the app should pass a simple human review:

- A new patient can sign up, complete profile basics, find profile settings,
  share a code, and understand what happens next.
- A new doctor can sign up, connect a patient, and start a Clinical Event
  without needing seed data.
- The app does not look like a test harness.
- The app does not foreground "synthetic/demo" vocabulary in normal use.
- The app has coherent typography, spacing, and hierarchy.
- The patient and doctor experiences feel like one product, not separate
  technical panels.
- Screenshots look credible enough to show to an advisor, early tester, or
  competition judge without explaining away the UI.

### 9. Account, Identity, And Connection Safety

- Doctors and patients can change passwords from Account after confirming the
  current password; successful changes revoke existing refresh sessions.
- Registration and forgot-password use the verified phone number, an expiring hashed
  verification challenge, an attempt limit, and audited reset. The external SMS
  provider remains the Phase 6 delivery integration; local/test environments
  may expose a development code, while staging/production responses do not.
- Doctor Account supports a real editable email and local-file avatar upload.
- Hospital information is read-only for doctors after registration and belongs
  to the administrator workflow.
- Patient-ID connection shows the doctor a minimal match preview and requires
  explicit confirmation before access is created.
- Patient medical intake uses named sections, required/optional language,
  examples, and conditional follow-up fields so empty text boxes have clear
  meaning.
- Unfinished patient navigation and the historical demo upload/assessment
  controls are hidden until production workflows, permissions, and validation
  are ready.

### 10. Localization Quality

- Chinese and English must use the same routes, controls, permissions, and
  product behavior; localization must not create a second app or forked flow.
- First use follows Chinese or English device language and falls back to
  English for every other locale. Both roles can change the interface language
  from Account, and the visible change is immediate.
- A Chinese localization release is not complete while production routes still
  contain hardcoded English labels, validation, empty states, notifications,
  status text, semantics, tooltips, or dialogs.
- Patient IDs and other stable identifiers remain unchanged. Patient-entered
  and clinician-entered clinical content is displayed exactly as entered and
  is never silently machine-translated.
- Verify Chinese and English screenshots at patient phone width and doctor
  desktop width, including long labels, form errors, dialogs, navigation, and
  enlarged text. No clipped or overlapping Chinese copy is acceptable.
- Localization smoke fixtures must remain test-only and must not create or
  leave synthetic records in production-facing data stores.

## Out Of Scope For This Gate

- Phase 3 AI generation, model inference, diagnosis automation, and AI recovery
  plan drafting.
- Phase 4 clinic operations.
- Phase 5 specialist/admin UI.
- Phase 6 operations beyond the localization work tracked in the implementation
  plan, including notification delivery and production release operations.
- Production deployment, store upload, real patient data, or clinical claims.

This gate is about making the existing patient/doctor product feel real before
the product becomes broader or more intelligent.

## Definition Of Done

This gate is closed only when:

- Documentation clearly identifies the current product-quality gap.
- The implementation plan blocks Phase 3 until the gap is closed.
- The patient profile/avatar/onboarding requirements are explicit.
- The visual-quality requirements are explicit enough to guide code.
- Current docs point future work to this gate before any new feature phase.
- A future implementation slice can be judged by screenshots and first-use
  workflow quality, not only by number of endpoints or tests.
