# Dr. AI Flutter app

Shared Flutter foundation for doctor web and patient mobile experiences.
Week 1 Days 1-2 intentionally include routing, design tokens, and synthetic
foundation screens only.

No authentication or clinical feature is enabled. Do not enter real patient
data.

## Local verification

Flutter 3.44.4 can build and test from this repository, but its analyzer emits
malformed analysis-server protocol output when the package path contains
Chinese characters. Until the upstream toolchain handles this path reliably,
run the repository wrapper from the repository root. It creates an isolated
ASCII-path copy, excludes generated files, and fails on the first unsuccessful
command:

```bash
./scripts/verify_flutter.sh
```

The same commands can be run directly in an ASCII-path checkout:

```bash
flutter pub get
flutter analyze
flutter test
flutter build web
flutter build apk --debug
flutter build ios --simulator --no-codesign
```

Preview either synthetic foundation role:

```bash
flutter run -d chrome --dart-define=DR_AI_PREVIEW_ROLE=doctor
flutter run --dart-define=DR_AI_PREVIEW_ROLE=patient
```
