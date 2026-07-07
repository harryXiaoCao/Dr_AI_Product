# Week 4, Days 16-17 Hardening Closure Record

Recorded: 2026-07-06

Status: complete for repository implementation and local verification.

Tencent staging status: not touched in this phase.

## Closure outcome

Week 4 Days 16-17 closed the local hardening pass only:

- added deterministic Flutter focus traversal through the app root;
- added patient mobile text-scaling and responsive QA coverage without changing the frozen 1.0x dashboard goldens;
- added contrast coverage for the core Dr. AI color pairs;
- stripped surrounding whitespace from upload, chat, and consultation request strings before validation;
- rejected unsafe or identifying consultation specialty text as well as unsafe summaries;
- expanded log-hygiene coverage across auth, refresh, upload, chat, and consultation attempts;
- ran repo-scoped dependency compatibility and dependency-tree checks;
- recorded backup/restore rehearsal planning without touching Tencent staging.

No Tencent staging deployment, production release, TestFlight, Android closed
testing, doctor web deployment, privacy notice, consent form, account deletion,
feedback form, analytics, billing, appointments, video/voice consultation, real
COS upload completion, real clinical assessment, real model inference, DeepSeek
fine-tuning, or true SSE work was added.

All clinical content remains synthetic, educational, and non-clinical.
DeepSeek keys remain server-side only. Red-flag detection still runs before any
LLM call. Wrong-role and cross-patient access remain neutral `404 not_found`.

## Backend hardening

The API now normalizes request strings for demo upload metadata, educational
chat, and consultation requests before validation. Consultation creation
rejects unsafe content in both `specialty` and `question_summary`, including
contact information, diagnosis requests, medication-change requests, raw-record
requests, and scan-interpretation requests.

Focused backend tests now verify:

- whitespace trimming before consultation duplicate detection;
- unsafe consultation specialty rejection with safe validation errors;
- auth/refresh/upload/chat/consultation log capture does not include
  credentials, refresh tokens, bearer headers, upload filenames, raw chat
  prompts, unsafe summaries, synthetic medication content, or DeepSeek keys;
- upload audit metadata remains URL-free and metadata-only;
- chat storage remains prompt-hash/length/category/fallback/model metadata
  only.

## Flutter hardening

The Flutter app now wraps the app surface in a `FocusTraversalGroup` using
reading-order traversal. The patient dashboard scales its fixed visual card
heights with active text scaling so enlarged mobile text can be exercised
without render overflow while preserving the frozen 412x917 1.0x golden.

Widget tests now cover:

- deterministic keyboard focus traversal on a visible form field;
- core color-pair contrast ratios;
- enlarged patient-dashboard text on a narrow mobile viewport;
- existing accessibility labels for disabled summary controls;
- existing doctor desktop and patient mobile golden baselines.

## Security and dependency review

Local scan results:

- no Flutter `debugPrint`, `developer.log`, or `console.log` calls were found
  in the app/test surfaces;
- the only `print(` hit in API code is the intentional seed-script CLI summary,
  not an application request log;
- no bearer-token literals, DeepSeek key assignments, or `sk-...` style secret
  literals were found in the scanned repository surfaces;
- `uv pip check` passed for the API project environment;
- `uv lock --check` passed;
- Flutter dependency tree inspection completed with Flutter SDK 3.44.4 and
  Dart SDK 3.12.2.

`uv run pip check` was not used as evidence because this machine's API venv
does not include the `pip` module and the command can inspect unrelated
Anaconda packages from the ambient Python path. The repo-scoped evidence is
`uv pip check`.

## Backup and restore rehearsal plan

No staging or production database was touched. The local-safe rehearsal for
this pass was limited to Alembic upgrade plus drift check. The Days 18-20
release-prep rehearsal should use a disposable database or staging snapshot:

1. create a timestamped `pg_dump` backup from the selected non-production
   database;
2. restore into a fresh disposable database;
3. run `uv run alembic upgrade head`;
4. run `uv run alembic check`;
5. run `uv run python -m app.seed` twice and verify the second seed is
   idempotent;
6. run the backend smoke tests against the restored database;
7. record the backup file path, source revision, restore target, and row-count
   sanity checks.

## Local verification evidence

Recorded after the Week 4 Days 16-17 hardening pass on 2026-07-06.

| Check | Result |
|---|---|
| Branch/status inspection | Confirmed current branch `codex/week2-week3-care-loop`; preserved dirty Week 2 and Week 3 changes. |
| Backend Ruff | Passed: `All checks passed!` |
| Backend focused hardening tests | Passed: `24 passed` for `tests/test_errors_and_logs.py`, `tests/test_week3_chat_consultation.py`, and `tests/test_week2_upload_assessment.py` |
| Backend full tests | Passed: `48 passed` with `pytest -W error` |
| API dependency compatibility | Passed: `uv pip check`; `All installed packages are compatible` |
| API lockfile check | Passed: `uv lock --check`; resolved 47 packages |
| Alembic upgrade | Passed: `uv run alembic upgrade head` |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| Flutter verification | Passed: `./scripts/verify_flutter.sh`; analysis clean and `25` widget/golden tests passed |
| Flutter dependency tree | Passed: `/Users/Harry-Cao/development/flutter/bin/flutter pub deps --style=compact`; dependency tree rendered locally |
| Log/secret/debug scan | Completed with no request debug logs, bearer-token literals, DeepSeek key literals, or Flutter debug logging found; intentional seed CLI `print(` remains. |

Staging deployment was not touched, so no staging verification is claimed.

## Deferred to Days 18-20

- physical iOS/Android device checks and desktop browser checks;
- TestFlight, Android closed testing, and doctor web deployment;
- beta privacy notice, consent, account deletion, feedback form, and known
  limitations page;
- staging or production backup/restore rehearsal using a real disposable
  database target;
- production release tagging, clean-account demo, backup demo video, tester
  invites, and monitoring;
- administrator audit-event read workflow and any real clinical/data
  workflows.
