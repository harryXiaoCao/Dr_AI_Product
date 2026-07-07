# Dr. AI Flutter app

Shared Flutter application for the doctor web and patient mobile experiences.
Week 1 includes email/password sign-in, secure session restoration and logout,
role-protected routes, refresh-and-retry networking, and database-backed
synthetic dashboards. Week 2 Days 6-7 adds the doctor Patient Management
workflow for assigned patient search/list, profile, medical history,
medications, and doctor notes, plus a patient-side self profile/history/
medication section. Week 2 Days 8-10 adds demo upload preparation, simulated
assessment, result display, and failure recovery. Week 3 Days 11-12 adds the
doctor recovery-plan editor, patient Today tasks, completion tracking, and a
demo-only local medication notification shell. Week 3 Days 13-14 adds the
patient educational chat surface with streaming-style response display and the
doctor/patient specialist-consultation request/status workflow. Week 4 Days
16-17 hardening adds deterministic focus traversal, contrast coverage, and
patient mobile text-scaling/responsive QA without redesigning the existing
doctor or patient workflows. Week 4 Days 18-20 adds a public pre-login Beta
support surface with privacy notice, consent readiness, account deletion
request preparation, feedback draft preparation, and known limitations.

The app uses Riverpod for state/dependency management, Dio for HTTP, and
`flutter_secure_storage` for the rotating refresh token. The short-lived access
token remains in application memory. On web, deploy only over HTTPS (localhost
is permitted for development).

Only synthetic patient-care fixtures, demo upload metadata, simulated
assessment results, recovery-plan tasks, educational question-preparation chat,
and asynchronous synthetic consultation requests are enabled. No real
notification delivery, real COS upload completion, real model inference, or
clinical feature is enabled. The Beta support feedback and deletion controls
prepare local drafts only; they do not send messages, delete data, invite
testers, or alter accounts. Do not enter real patient data.

## Configuration

Use Chrome for the default development loop. This keeps iteration fast and
avoids loading local iOS or Android simulators for ordinary UI and API work.
Set the API origin at compile time:

```bash
flutter run -d chrome \
  --dart-define=DR_AI_API_BASE_URL=http://127.0.0.1:8000
```

The server determines the signed-in role; there is no client-side role picker.

## Verification

Flutter 3.44.4's analyzer has a byte-framing failure from this repository's
Chinese-character path. Run the reproducible ASCII-copy wrapper from the
repository root:

```bash
./scripts/verify_flutter.sh
```

The wrapper runs dependency resolution, analysis, and widget tests. The widget
suite covers login validation/loading/success/error, restoration, logout,
role routing, wrong-role rejection, doctor patient search/list/detail,
patient-side profile/history/medication display, recovery-plan editing,
patient Today task completion, educational chat success/failure state,
specialist-consultation request/status display, network/empty states,
accessibility labels, deterministic keyboard focus traversal, core color
contrast, enlarged patient-dashboard text scaling, the local-only Beta support
surface, and the `1280x832` doctor plus `412x917` patient layouts.

Golden baselines under `test/goldens/` are local visual baselines for the two
frozen dashboard sizes. They are skipped on Linux CI because Flutter raster and
font output drifts between local macOS and GitHub Linux runners. CI still runs
the structural dashboard assertions and accessibility-label checks, which are
the stable design-regression gate.

Default local checks:

```bash
./scripts/verify_flutter.sh
flutter build web
```

Release-prep command shapes for TestFlight, Android closed testing, and doctor
web live deployment are documented in
`../../docs/Week_4_Days_18_20_Release_Gate_Checklist.md`. Do not upload,
submit, deploy, invite testers, create tags, or change account settings without
explicit approval.

Native mobile checks are milestone or release-gate checks, not the default
task loop. Run them only when validating platform-specific behavior, beta
packaging, or changes to native iOS/Android configuration:

```bash
flutter build apk --debug
flutter build ios --simulator --no-codesign
```

For first personal Android phone testing, use a debug APK built against
Tencent staging rather than release signing:

```bash
flutter build apk --debug \
  --dart-define=DR_AI_API_BASE_URL=https://dr-ai.43.132.169.195.sslip.io
```

The current debug APK output path is
`build/app/outputs/flutter-apk/app-debug.apk`.

For Google Play closed-testing artifacts, release builds now require a local
upload keystore. Copy `android/key.properties.example` to
`android/key.properties`, point `storeFile` to an ignored local keystore, and
keep all passwords out of git. Without that file, `flutter build appbundle
--release` fails intentionally instead of producing a debug-signed release.

For iPhone testing, the checked-in iOS project uses automatic signing and
bundle id `com.harrycao.drai.drAiApp`, but no development team is configured.
The fastest route is direct Xcode install to a connected iPhone after selecting
an Apple Developer team in Xcode. TestFlight requires explicit approval plus an
Apple Developer account/team, App Store Connect app record, signing profiles,
build number, privacy/export/compliance fields, upload, and tester invitation.

The Android seeded-login smoke can be run against a local FastAPI service with
synthetic credentials supplied through `--dart-define`:

```bash
flutter test integration_test/auth_smoke_test.dart -d emulator-5554 \
  --dart-define=DR_AI_API_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=DR_AI_SMOKE_EMAIL=patient.demo@example.com \
  --dart-define=DR_AI_SMOKE_PASSWORD="$DR_AI_SEED_PATIENT_PASSWORD" \
  --dart-define=DR_AI_SMOKE_DASHBOARD_TEXT="Recovery Plan"
```

Use the same integration test for doctor web sign-in confidence. This is the
maintainable smoke path for Flutter web because Flutter renders the app through
its own widget tree/canvas and does not expose reliable DOM text fields for
browser automation:

```bash
flutter test integration_test/auth_smoke_test.dart -d chrome \
  --dart-define=DR_AI_API_BASE_URL=http://127.0.0.1:8000 \
  --dart-define=DR_AI_SMOKE_EMAIL=doctor.demo@example.com \
  --dart-define=DR_AI_SMOKE_PASSWORD="$DR_AI_SEED_DOCTOR_PASSWORD" \
  --dart-define=DR_AI_SMOKE_DASHBOARD_TEXT="Quick Access"
```

Manual doctor-web smoke route:

1. Start FastAPI locally with seeded synthetic accounts.
2. Run Flutter web with
   `--dart-define=DR_AI_API_BASE_URL=http://127.0.0.1:8000`.
3. Sign in as `doctor.demo@example.com`.
4. Confirm the doctor dashboard shows `Quick Access`, `Recent Activities`,
   `Resource Overview`, and the synthetic-data warning.
5. Open `Patient Management`, select `Riley Demo Patient`, and confirm
   `Medical History`, `Medications`, and `Doctor Notes` render synthetic
   content.
6. Scroll to the recovery-plan editor, save a synthetic plan, and activate it.
7. Submit a synthetic specialist-consultation request and confirm it appears
   as `requested`.
8. Sign in as `patient.demo@example.com` and confirm the Today card shows
   medication, exercise, diet, and follow-up tasks plus the local demo
   medication notification shell.
9. Open Ask Dr. AI, send a general educational question, and confirm the
   streaming-style response keeps the educational limitation visible.
10. Use Sign out and confirm the login screen shows the signed-out notice.

When disk space is tight, prefer CI and physical devices for these native checks
instead of keeping local Android AVDs and iOS simulator runtimes installed.
The local Android SDK and AVD storage are PHILIPS-backed through the mounted
APFS volume `/Volumes/AndroidAVD`: Flutter uses `/Volumes/AndroidAVD/sdk`, and
the default AVD home is `/Volumes/AndroidAVD/avd`. Future phases should keep
Android on that external volume, avoid reinstalling SDK components onto the
internal disk, and minimize iOS simulator usage to native milestone checks.
