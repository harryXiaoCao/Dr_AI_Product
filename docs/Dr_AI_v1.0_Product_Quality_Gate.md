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