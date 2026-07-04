# Week 1, Days 1-2 Foundation Record

Recorded: 2026-07-02

Closed: 2026-07-04

Status: complete; Week 1 remains in progress because Days 3-5 are not complete

## Closure outcome

Dr. AI v1.0 Week 1 Days 1-2 is formally closed. The Flutter web, Android, and
iOS foundations build; the FastAPI foundation is warning-free; the design
freeze is reconciled against the supplied Figma metadata; and the planned v1
API boundary is frozen without implementing any deferred endpoint.

Closure branch: `codex/week1-days1-2-closure`

Draft pull request: <https://github.com/harryXiaoCao/Dr_AI_Product/pull/1>

First green CI run:
<https://github.com/harryXiaoCao/Dr_AI_Product/actions/runs/28676795816>

## Repository baseline

- The existing repository and `origin` were preserved.
- No history was rewritten and no force-push was used.
- The closure work is isolated on a dedicated branch and draft pull request.
- Generated caches, local configuration, build outputs, secrets, credentials,
  and real patient data are excluded from the commit.
- The pull request must not be merged without separate authorization.

## Toolchain

| Tool | Final verified version/status |
|---|---|
| Flutter | `3.44.4` stable |
| Dart | `3.12.2` |
| Flutter/Dart shell PATH | Added to `~/.zshrc`; verified in a fresh login shell |
| Android SDK | API 36, Build Tools `36.0.0`, Platform Tools `37.0.0` |
| Android Emulator | `36.6.11`; `Dr_AI_API_36` Pixel 6 AVD configured |
| Android NDK | `28.2.13676358` |
| CMake | `3.22.1` |
| Java | OpenJDK `21.0.11` LTS; pinned in Flutter configuration |
| Android licenses | All accepted |
| Xcode | `26.3` (`17C529`) |
| iOS Simulator | iOS `26.3.1` runtime installed; iPhone 16e booted and detected |
| CocoaPods | `1.16.2` |
| Python | Project requires `>=3.12`; CI uses `3.12` |
| uv | Lockfile-backed backend environment |
| GitHub CLI | Authenticated with `repo` and `workflow` scopes |

Official setup guidance was checked before installation:

- [Flutter Android setup](https://docs.flutter.dev/platform-integration/android/setup)
- [Android sdkmanager](https://developer.android.com/tools/sdkmanager)
- [Flutter iOS setup](https://docs.flutter.dev/platform-integration/ios/setup)
- [CocoaPods installation](https://guides.cocoapods.org/using/getting-started.html)

## Implemented foundation

- `apps/dr_ai_app/`
  - Flutter web, iOS, and Android scaffold.
  - Strict analysis and formatting configuration.
  - Role-aware doctor and patient home routes plus unauthorized handling.
  - Figma-reconciled central colors and verified typography metrics.
  - Doctor and patient navigation labels aligned with the frozen targets.
  - Synthetic-content and non-clinical notice.
  - Widget tests for both role homes and cross-role rejection.
- `services/api/`
  - FastAPI application factory.
  - Environment-backed settings.
  - `GET /health` only.
  - Health and OpenAPI safety-description tests.
  - Ruff and pytest configuration.
  - Starlette's supported `httpx2` test-client dependency, eliminating the
    prior deprecation warning instead of suppressing it.
- `.github/workflows/ci.yml`
  - Flutter formatting, analysis, widget tests, and web build.
  - Lockfile-backed FastAPI Ruff and warning-as-error pytest jobs.
- `docs/Dr_AI_v1.0_API_Contract.md`
  - Planned v1 paths, enums, error envelope, role boundaries, simulation
    contract, safety labels, and versioning rules.
  - Deferred paths are documented only and are not implemented.
- Environment templates contain documentation values only and no secrets.

Authentication, DeepSeek, medical records, assessments, recovery plans,
consultations, and clinical functionality remain deliberately unimplemented.

## Design-freeze reconciliation

The manually supplied Figma inspection record replaced the exhausted MCP quota
for this closure and was treated as authoritative. The design freeze now:

- records the exact target dimensions, frame properties, direct hierarchy,
  instance names, variants, published libraries, raw colors, named color
  styles, and verified text styles;
- distinguishes verified Figma values from Flutter implementation defaults;
- corrects the patient target from an assumed scrolling frame to Figma's
  fixed, clipped, `No scrolling` frame;
- records that Figma defines no local variables, collections, modes, spacing
  scale, radius scale, shadow scale, or breakpoint system;
- names every unavailable font, token-source, responsive, and interaction
  field without inventing values; and
- preserves the Figma file unchanged.

See [the design freeze](Dr_AI_v1.0_Design_Freeze.md) for the complete evidence
boundary.

## Unicode-path analyzer diagnosis

Direct `flutter analyze -v` from the original Chinese-character workspace
fails in Flutter `3.44.4` before analysis begins:

```text
FormatException: Unterminated string
LspByteStreamServerChannel._readMessage
analysis server exited with code 255
```

The verbose trace shows a percent-encoded non-ASCII workspace URI followed by a
truncated LSP `initialize` body. The observed failure is a byte-length framing
problem between Flutter's analyzer client and Dart's LSP channel, not a source
diagnostic. Searches of the official Flutter and Dart issue trackers found no
matching published issue at closure time.

`scripts/verify_flutter.sh` is the durable repository workaround. It:

1. creates a new ASCII-only temporary directory;
2. copies the Flutter source while excluding generated files;
3. runs `flutter pub get`, `flutter analyze`, and `flutter test`;
4. exits on the first failure; and
5. removes the temporary copy on exit.

CI uses an ASCII GitHub workspace and runs the same direct Flutter commands.
The original repository was not moved, deleted, or replaced.

## Verification evidence

| Check | Result |
|---|---|
| `flutter doctor -v` | No issues found |
| Dart formatting | 12 files checked; no changes required |
| `./scripts/verify_flutter.sh` | Analysis clean; 3 widget tests passed |
| `flutter build web` | Passed |
| `flutter build apk --debug` | Passed; debug APK produced |
| XcodeBuildMCP `Runner` simulator build | `BUILD SUCCEEDED` |
| `flutter build ios --simulator --no-codesign` | Passed; `Runner.app` produced |
| `uv run ruff check .` | Passed |
| `uv run pytest -W error` | 2 passed; zero warnings |
| Environment-template review | No credentials or secrets |
| Markdown local-link/path review | Passed |
| Staged cache/build/credential scan | Passed |
| `git diff --check` | Passed |
| GitHub Actions Flutter job | Passed |
| GitHub Actions FastAPI job | Passed |

Build products and Gradle/Xcode caches were removed after their successful
results were recorded to preserve local disk space. The installed Android SDK,
Android AVD, iOS runtime, CocoaPods, Java, Flutter configuration, and source
remain available.

## Remaining Week 1 work

Week 1 itself is not complete. Days 3-5 still require the separately approved
database, authentication, authorization, responsive shell, seeded-dashboard,
and staging work. No part of that later scope was pulled into this closure.

There is no external blocker to the completed Days 1-2 scope. The Figma fields
that remain unavailable are explicitly bounded in the design freeze and do not
block foundation implementation.
