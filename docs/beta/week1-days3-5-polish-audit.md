# Week 1 Days 3-5 Polish Audit

Recorded: 2026-07-04

Source evidence:

- Frozen doctor target:
  `docs/design-evidence/doctor-dashboard-618-1051.png`
- Frozen patient target:
  `docs/design-evidence/patient-dashboard-663-398.png`
- Local Flutter doctor baseline:
  `apps/dr_ai_app/test/goldens/doctor_dashboard_1280x832.png`
- Local Flutter patient baseline:
  `apps/dr_ai_app/test/goldens/patient_dashboard_412x917.png`

## Steps

1. Doctor dashboard at `1280x832`: broadly matches the frozen three-zone
   information hierarchy. The top application chrome was too tall compared with
   the frozen reference, so it was compressed into one desktop header row with
   logo, search, navigation, account label, and sign-out.
2. Patient dashboard at `412x917`: broadly matches the frozen stacked mobile
   card flow. The implementation remains intentionally synthetic and uses
   Flutter components instead of unavailable Figma image assets. Disabled Week 1
   controls now expose explicit semantic labels.
3. Login and logout: invalid credentials, network/server failure, loading, and
   signed-out feedback are distinct. Password reset is shown as unavailable in
   Week 1 rather than silently missing.
4. Screenshot strategy: pixel goldens remain local visual baselines. CI relies
   on stable structural dashboard assertions and accessibility-label checks
   because Linux raster/font output differs from local macOS rendering.

## Limits

- The audit did not edit Figma and did not infer hidden Figma token values.
- The committed local goldens use Flutter's test rendering and are not
  pixel-perfect copies of the Figma exports.
- Real end-to-end staging sign-in still depends on Tencent staging access.
