# Dr. AI Flutter app

Shared Flutter application for the doctor web and patient mobile experiences.
Week 1 includes email/password sign-in, secure session restoration and logout,
role-protected routes, refresh-and-retry networking, and database-backed
synthetic dashboards.

The app uses Riverpod for state/dependency management, Dio for HTTP, and
`flutter_secure_storage` for the rotating refresh token. The short-lived access
token remains in application memory. On web, deploy only over HTTPS (localhost
is permitted for development).

No clinical feature is enabled. Do not enter real patient data.

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
role routing, wrong-role rejection, network/empty states, accessibility labels,
and the `1280x832` doctor plus `412x917` patient layouts.

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

Native mobile checks are milestone or release-gate checks, not the default
task loop. Run them only when validating platform-specific behavior, beta
packaging, or changes to native iOS/Android configuration:

```bash
flutter build apk --debug
flutter build ios --simulator --no-codesign
```

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
5. Use Sign out and confirm the login screen shows the signed-out notice.

When disk space is tight, prefer CI and physical devices for these native checks
instead of keeping local Android AVDs and iOS simulator runtimes installed.
The local Android SDK and AVD storage are PHILIPS-backed through the mounted
APFS volume `/Volumes/AndroidAVD`: Flutter uses `/Volumes/AndroidAVD/sdk`, and
the default AVD home is `/Volumes/AndroidAVD/avd`. Future phases should keep
Android on that external volume, avoid reinstalling SDK components onto the
internal disk, and minimize iOS simulator usage to native milestone checks.
