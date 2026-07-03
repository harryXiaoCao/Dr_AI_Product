# Dr. AI v1.0 Design Freeze - Week 1, Days 1-2

Status: reconciled and complete for implementation

Recorded: 2026-07-02; reconciled: 2026-07-04

Figma file: `8EJikM9M97nVy3R5JLeC0O`

Doctor frame: `618:1051`

Patient frame: `663:398`

This is the implementation-facing design freeze for the v1.0 foundation. It
does not redesign either target and does not claim that deferred product
features are implemented. The Figma file was not edited.

## Evidence and authority

- [Doctor dashboard export](design-evidence/doctor-dashboard-618-1051.png):
  direct frameless 1x PNG, `1280 x 832`.
- [Patient dashboard export](design-evidence/patient-dashboard-663-398.png):
  direct frameless 1x PNG, `412 x 917`.
- The screenshots establish visible composition and copy.
- The manually supplied Figma inspection record establishes node names,
  styles, variants, layout settings, and prototype properties. It is the
  authoritative substitute while the Figma MCP read quota is unavailable.
- The approved
  [implementation plan](Dr_AI_v1.0_Implementation_Plan.md) establishes product
  scope. Where the plan defines adaptive behavior that Figma does not define,
  this document marks it as an implementation decision.

## Fixed target frames

| Property | Doctor | Patient |
|---|---|---|
| Name | `Dashboard - for doctors` | `Dashboard - for patients` |
| Node | `618:1051` | `663:398` |
| Size | `1280 x 832` | `412 x 917` |
| Position | `(998, -528)` | `(2450, -528)` |
| Rotation | `0 degrees` | `0 degrees` |
| Layout | Freeform; Auto Layout off | Freeform; Auto Layout off |
| Dimensions | Fixed | Fixed |
| Clip content | Enabled | Enabled |
| Overflow | No scrolling | No scrolling |
| Frame fill | `#FFFFFF`, 100% | `#FFFFFF`, 100% |
| Frame opacity | 100% | 100% |
| Frame radius | `0` | `0` |
| Frame stroke/effect | None | None |

Because Auto Layout is off, neither frame defines direction, padding, or gap.
No responsive relationship between the two frames is encoded in Figma.

## Screen inventory

### Doctor experience

1. Global header
   - Product mark.
   - Search for patients, cases, diagnoses, and resources.
   - Dashboard, AI Diagnostic, AI Recovery Plan, Medical Resources, and Patient
     Management destinations.
   - Profile/avatar action.
2. Hospital and doctor identity
   - Hospital image, name, location, summary, and edit action.
   - Doctor rating, profile, role, expertise, and edit action.
3. Quick Access
   - CT, X-ray, and MRI diagnostic/upload tiles.
   - Medical record, recovery plan, imaging result, and medical equipment
     tiles.
4. Recent Activities
   - Synthetic scheduled activity with a visible time-picker state.
   - Cancel, OK, and More Activities controls.
5. Resource Overview
   - Expanded medical-equipment availability summary.
   - Collapsed medication stock, staffing level, and bed availability rows.
   - Read-only demonstration content in v1.0.
6. Team Management
   - Three doctor cards and an add-team-member tile.

### Patient experience

1. Global header
   - Product mark and profile/avatar action.
2. Recovery Plan
   - Today, Jan. 2, and Jan. 3 columns.
   - Medication, hydration, trigger-avoidance, contact-hospital, and activity
     task chips.
   - See More control for each day.
3. Contact Doctor
   - Assigned doctor identity, role, image, and expertise.
4. Medical Fee
   - Itemized checklist and Pay Now action. Billing is deferred, so this is a
     non-functional visual placeholder in v1.0.
5. Medical Record
   - Explicit empty state: `No Medical Records`.
6. Imaging Results
   - Explicit empty state: `No Imaging Results`.
7. Search and bottom navigation
   - Search field.
   - Dashboard, Contact, Medical Service, and Recovery Plan destinations.

The target frame itself is fixed and set to `No scrolling`; a runtime may add
safe scrolling when text scaling or a smaller viewport would otherwise clip
content.

## Direct Figma hierarchy

### Doctor `618:1051`

- Groups: `Group 2`, `Group 1`.
- Instances:
  - `Accordion` - variant/badge `Desktop + 1`.
  - `Button` - `Blue DT`.
  - `Keyboard picker` - `Baseline + 1`.
  - `Online Medical Service Monitor`.
  - `Target` - `SDS Dark`.
  - `People`.
  - `Calendar 01`.
  - `Navigation Button` - `SDS Dark`.
  - `Stats Card` x3 - `SDS Dark`.
  - `Button` x3 - `SDS Dark`.
  - `Product Info Card` x7 - `SDS Dark`.
- Text: `Title` x4.
- Shapes: `Rectangle 9`, `Rectangle 8`, `Rectangle 10`.

### Patient `663:398`

- Text: `No Medical Records`, `No Imaging Results`.
- `Search bar` instance - `Blue DT`.
- `Button` instance.
- `List: -4 Density` instance - `Baseline + 1`.
- `Button` x3 - `Blue DT`.
- `Avoid triggers` text x3.
- Groups: `Group 9`, `Group 8`, `Group 7`.
- Text:
  - `Goal: began light activites like...`
  - `Come to xxx hospital if xxx....`
  - `50mg of Sumatriptan`
- `Testimonial Card` x7.
- `Review Card` x1.
- Text: `Medical Fee`, `Check Imaging Results`, `Check Medical Record`,
  `Contact Doctor`, `Recovery Plan`.
- Shape: `Rectangle 18`.

No local components surfaced in Assets. The instances above come from enabled
published libraries:

- iOS and iPadOS 26 UI Kit: 175 components.
- Material 3 Design Kit: 357 components.
- Simple Design System: 1,844 components.

Flutter components should reproduce the required behavior and semantics; their
class names do not need to copy Figma library instance names.

## Verified colors

The central Flutter mapping lives in
`../apps/dr_ai_app/lib/design_system/dr_ai_tokens.dart`.

### Material 3 library styles

| Figma style | Value |
|---|---:|
| `M3/sys/light/primary` | `#6750A4` |
| `M3/sys/light/on-primary` | `#FFFFFF` |
| `M3/sys/light/on-surface` | `#1D1B20` |
| `M3/sys/light/on-surface-variant` | `#49454F` |
| `M3/sys/light/surface` | `#FEF7FF` |
| `M3/sys/light/outline` | `#79747E` |
| `M3/sys/light/outline-variant` | `#CAC4D0` |
| `M3/sys/light/secondary-container` | `#E8DEF8` |
| `M3/sys/light/primary-container` | `#EADDFF` |
| `M3/sys/light/on-primary-container` | `#4F378A` |
| `M3/sys/light/tertiary-container` | `#FFD8E4` |
| `M3/sys/light/on-tertiary-container` | `#633B48` |
| `M3/sys/light/surface-container-high` | `#ECE6F0` |
| `M3/sys/light/surface-container-highest` | `#E6E0E9` |
| `M3/state-layers/light/onSurface/opacity-0.08` | `#1D1B20` at 8% |
| `M3/state-layers/light/onSurfaceVariant/opacity-0.08` | `#49454F` at 8% |

### iOS library styles

| Figma style | Value |
|---|---:|
| `Colors/Indigo` | `#5856D6` |
| `Colors/Blue` | `#007AFF` |
| `Colors/Cyan` | `#32ADE6` |
| `Colors/Mint` | `#00C7BE` |
| `Colors/Orange` | `#FF9500` |

### Raw target colors

- Doctor: `#030025`, `#FFFFFF`, `#000000`, `#F5F5F5`, `#0A0076`,
  `#D9D9D9`, `#E5E5E5`, `#1E1E1E`, `#DEDCFC`, all 100%.
- Patient: `#FFFFFF`, `#030025`, `#000000`, `#0A0076`, `#E5E5E5`,
  `#B0C6FF`, `#DEDCFC`, all 100%.
- Instance-linked tokens additionally expose `#444444`, `#FFFFFF`,
  `#F5F5F5`, `#2C2C2C`, and `#1E1E1E`, generally at 100%. Secondary white
  text/icon tokens use 70%; one tertiary white token uses 40%.

Semantic application colors such as error red and muted body text are required
for runtime states but were not exposed by the two target frames. They must be
marked as application semantics, not Figma-verified target values.

## Verified typography

| Usage/source | Style | Size and line height | Color |
|---|---|---:|---:|
| Doctor `Title` | `Subheading` | `20px / 120%` | `#FFFFFF` |
| Patient `No Medical Records` | `Body Base` | `16px / 140%` | `#000000` |
| Patient `Recovery Plan` | `Body Base` | `16px / 140%` | `#FFFFFF` |
| Patient `Avoid triggers` | `M3/label/small` | `11px / 16px` | `#FFFFFF` |

The library picker also exposes M3 headline, title, label, body, and emphasized
counterparts at `24/32`, `22/28`, `16/24`, `14/20`, `12/16`, and `11/16`.
`Title Hero` appears at `72px / 120%`.

Font family, numeric weight, and letter spacing are unavailable because Dev
Mode is blocked by an Upgrade to Professional paywall. Flutter therefore uses
the platform system sans-serif and implementation-level weights until those
fields can be inspected; those choices are not claimed as Figma values.

## Spacing, radii, shadows, and breakpoints

- Figma reports no local variables, collections, or modes.
- Library-linked variables exist inside instances, but their source
  collections and modes are not inspectable.
- No local numeric spacing scale is available.
- No global radius, border, or shadow scale is available.
- Both top-level target frames use radius `0`, no stroke, and no effect.
- No responsive breakpoint system is defined.
- An additional top-level `iPad Pro - 11" (6th generation)` item exists, but
  its relationship to either target is undefined.

The Flutter scales `4, 8, 12, 16, 24, 32, 48`, radii `4, 8, 12, 16, 999`, and
breakpoints `<600`, `600-1023`, and `>=1024` are implementation choices from
the approved adaptive plan. They are not reverse-engineered Figma values.
Reference QA remains fixed at `1280 x 832` and `412 x 917`.

## Navigation and routing freeze

- Role determines the permitted route family: `/doctor` or `/patient`.
- Cross-role navigation resolves to `/unauthorized`.
- Doctor desktop navigation uses the five visible labels from the target:
  Dashboard, AI Diagnostic, AI Recovery Plan, Medical Resources, and Patient
  Management.
- Patient navigation uses the four visible labels from the target: Dashboard,
  Contact, Medical Service, and Recovery Plan.
- Only the role homes and unauthorized state exist in the Days 1-2 scaffold.
  Other labels remain non-functional until their scheduled week.
- Flutter route guards are not security controls; later server authorization
  must enforce role and care-relationship boundaries.

## Components and states

Current Flutter foundation components:

- Central theme and design tokens.
- Role-aware routes and unauthorized screen.
- `SectionCard`.
- `FoundationNotice`.
- Doctor top navigation at the desktop breakpoint.
- Patient bottom navigation.

Planned reusable Flutter components:

- Global search and profile menu.
- Section header bar.
- Patient summary card.
- Task/status chip.
- Empty-state panel.
- Loading skeleton.
- Inline error with retry.
- Confirmation dialog.
- Persistent simulated-assessment disclosure and result panel.
- Responsive two- and three-column dashboard grids.

Verified target states:

- Patient empty states: `No Medical Records` and `No Imaging Results`.
- Doctor visible time-picker state.
- Current instance variants: `Desktop + 1`, `Blue DT`, `Baseline + 1`, and
  `SDS Dark`.
- Neither frame is a flow starting point.
- Neither frame exposes frame-level interaction entries.
- No verified loading, error, hover, focus, pressed, or disabled variants exist.

Required runtime states are therefore implementation requirements, not claims
about hidden Figma variants:

| State | Required treatment |
|---|---|
| Loading | Preserve layout with a named busy region; never imply a diagnosis is being generated. |
| Empty | Plain-language title, what is absent, and one safe next action. |
| Error | Inline explanation, safe retry, and preserved input; no stack trace or secret. |
| Unauthorized | Neutral lock state with no sensitive object detail and a route back to the role home. |
| Simulated AI | Persistent `Research simulation - not for diagnosis.` label, limitations, completeness, fixture version, and safe next steps. |
| Focus/hover/pressed/disabled | Use accessible Material behavior until a verified target variant exists. |

## Golden workflow boundary

The frozen v1 workflow is:

1. Doctor opens a synthetic patient record.
2. Doctor reviews synthetic clinical information and a demo CT image.
3. Doctor runs a clearly labeled simulated lung-metastasis assessment.
4. Doctor reviews limitations and creates a recovery plan.
5. Patient receives the plan, reminders, and educational guidance.
6. Doctor may submit an asynchronous specialist-consultation request.

The Days 1-2 foundation implements only role-aware route boundaries, shared
tokens, representative home surfaces, empty/synthetic notices, and CI. It does
not implement authentication, patient records, assessment logic, recovery
plans, consultation, DeepSeek, or any clinical behavior.

## Precisely unavailable fields

The following remain unavailable and must not be invented:

1. Font family, numeric font weight, and letter spacing for the verified text
   styles.
2. Source collections and modes for library-linked variables.
3. Numeric spacing values and a global spacing scale.
4. Global component radius, border, and shadow scales beyond the verified
   top-level frame properties.
5. Responsive breakpoint rules or the relationship of the iPad item to the two
   targets.
6. Component behaviors or variants for loading, error, hover, focus, pressed,
   and disabled states.
7. Prototype transitions beyond the verified absence of frame-level entries
   and flow starting points.

These gaps do not block the Week 1 Days 1-2 implementation freeze because they
are explicitly bounded and the app-level fallback choices are documented.
