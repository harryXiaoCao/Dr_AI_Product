# Week 4, Days 18-20 Release Closure Record

Recorded: 2026-07-06

Status: complete for local release-prep and release-gate preparation.

Tencent staging status: not touched in this phase.

## Closure outcome

Week 4 Days 18-20 prepared the remaining beta-release surfaces and local gate
artifacts without performing external release actions:

- added a Flutter Beta support surface reachable before sign-in from the login
  screen and directly at `/beta-support`;
- prepared the privacy notice, consent checklist, account deletion request,
  feedback draft, and known-limitations surfaces locally;
- prepared release notes for `v1.0.0-beta.1`;
- prepared the device/browser, packaging, clean-account demo, backup demo,
  backup/restore, tagging, tester invite, and monitoring checklist;
- preserved the API contract, migrations, seed script, and existing dirty
  Week 2/Week 3/Week 4 working tree.

The account deletion and feedback controls prepare local drafts only. They do
not delete data, send messages, invite testers, or change accounts.

No Tencent staging deployment, production deployment, TestFlight upload,
Android closed-testing upload, web deployment, tag creation, commit, push,
pull request, tester invite, monitoring change, account change, screen
recording, real COS upload completion, real clinical assessment, real model
inference, DeepSeek fine-tuning, billing, appointments, video/voice
consultation, analytics expansion, or true SSE work was performed.

All clinical content remains synthetic, educational, and non-clinical.
DeepSeek keys remain server-side only. Red-flag detection still runs before any
LLM call. Wrong-role and cross-patient access remain neutral `404 not_found`.

## Local implementation evidence

- Flutter route: `/beta-support`.
- Entry point: `Beta privacy and support` link on the sign-in screen, plus
  direct `/beta-support` route.
- Local-only controls:
  - consent readiness checklist;
  - account deletion request preparation requiring `REQUEST DEMO DELETION`;
  - feedback draft preparation;
  - known-limitations disclosure.

## Prepared but not externally executed

- TestFlight build command shape.
- Android closed-testing app bundle command shape.
- Doctor web build/deployment command shape.
- Clean-account demo script.
- Backup demo video evidence plan.
- Disposable backup/restore rehearsal plan.
- `v1.0.0-beta.1` tag plan.
- Tester invite and monitoring checklist.

## Verification evidence

| Check | Result |
|---|---|
| Branch/status inspection | Confirmed current branch `codex/week2-week3-care-loop`; preserved dirty Week 2, Week 3, and Week 4 changes. |
| Backend Ruff | Passed: `All checks passed!` |
| Backend full tests | Passed: `48 passed` with `uv run pytest -W error` |
| API dependency compatibility | Passed: `uv pip check`; `All installed packages are compatible` |
| API lockfile check | Passed: `uv lock --check`; resolved 47 packages |
| Alembic upgrade | Passed: `uv run alembic upgrade head` |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| Flutter verification | Passed: `./scripts/verify_flutter.sh`; analysis clean and `26` widget/golden tests passed |
| Flutter web build | Passed: `flutter build web --release`; built `apps/dr_ai_app/build/web` locally. Non-fatal warning: build expected `CupertinoIcons` font assets but found only `MaterialIcons`. |
| Whitespace check | Passed: `git diff --check` |

Physical iOS and Android device checks, TestFlight build/upload, Android
closed-testing bundle/upload, deployed doctor web verification, clean-account
second-device demo, backup demo video recording, staging backup/restore
rehearsal, release tagging, tester invites, and monitoring setup were prepared
only and not executed because they require explicit approval and/or connected
release devices/accounts.

## Remaining explicit approvals

- Verify, refresh, or deploy Tencent staging.
- Configure signing or upload TestFlight builds.
- Configure signing or upload Android closed-testing bundles.
- Deploy doctor web.
- Create or push `v1.0.0-beta.1`.
- Invite testers.
- Alter monitoring or account settings.
- Record demo video evidence with GUI tools.
