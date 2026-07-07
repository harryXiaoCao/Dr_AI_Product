# Week 3, Day 15 Gate Closure Record

Recorded: 2026-07-05

Status: complete for repository implementation and local verification.

Tencent staging status: not touched in this phase.

## Branch and PR handling

Day 15 did not continue directly on `codex/week1-days3-5`. The working tree
contained dirty Week 2 and Week 3 changes, so the current state was preserved
on a new stacked branch:

- current branch after the move: `codex/week2-week3-care-loop`;
- source branch before the move: `codex/week1-days3-5`;
- draft PR #1 and draft PR #2 remain unmerged;
- no history rewrite, force-push, merge, deploy, or staging action was
  performed.

## Closure outcome

Week 3 Day 15 closed the approved gate only:

- verified the full doctor-led loop across doctor and patient accounts through
  an API-level gate test;
- expanded chat safety fixture coverage for red flags, prompt injection,
  medication-change requests, diagnosis requests, contact-info leakage, and
  normal educational questions;
- made repeated identical `requested` specialist-consultation submissions
  return the existing request instead of creating duplicates;
- polished the patient Ask Dr. AI card for small screens with automatic
  scroll-to-latest behavior during the streaming-style reveal and a denser
  send field.

The current JSON-first streaming-style chat remains in place. No true SSE,
DeepSeek fine-tuning, staging deployment, real clinical assessment, real model
inference, real COS upload completion, billing, appointments, video/voice
consultation, analytics, production release, or Week 4 hardening work was
added.

All clinical content remains synthetic, educational, and non-clinical.
DeepSeek keys remain server-side only. Red-flag detection still runs before
rate limiting and before any LLM call. Wrong-role and cross-patient access
remain neutral `404 not_found`.

## Backend evidence

The Day 15 gate is covered by
`tests/test_week3_chat_consultation.py::test_day15_full_doctor_led_loop_across_doctor_and_patient_accounts`.
That test performs:

1. doctor login;
2. assigned patient lookup;
3. demo upload metadata preparation;
4. simulated assessment creation;
5. recovery-plan save and activation;
6. patient Today readback;
7. patient task completion;
8. Ask Dr. AI educational chat;
9. doctor consultation request;
10. patient consultation status readback.

The same focused backend file also verifies chat safety categories, provider
fallbacks, rate limiting, wrong-role denial, duplicate consultation reuse, and
unsafe consultation summary rejection.

## Flutter evidence

The patient Ask Dr. AI card keeps the educational limitation visible, appends
the user message and streaming-style assistant placeholder, reveals response
chunks progressively, preserves the typed question on send failure, and now
keeps the latest message visible on compact screens.

The existing Flutter widget/golden suite verifies the patient mobile
`412x917` layout, doctor desktop `1280x832` layout, Today task completion,
educational chat success/failure state, and doctor/patient consultation
request/status display.

## Documentation updates

- `docs/Dr_AI_v1.0_Implementation_Plan.md` marks Week 3 complete and records
  the branch strategy change in the progress/change log.
- `docs/Dr_AI_v1.0_API_Contract.md` documents duplicate requested-consultation
  reuse.
- `services/api/README.md` documents duplicate consultation behavior and Day
  15 verification status.
- `README.md` updates the current milestone summary to Week 3 complete.

## Local verification evidence

Recorded after the Week 3 Day 15 pass on 2026-07-05.

| Check | Result |
|---|---|
| Backend Ruff | Passed: `All checks passed!` |
| Backend focused Week 3 tests | Passed: `20 passed` for `tests/test_week3_chat_consultation.py`, `tests/test_week3_recovery_plans.py`, and `tests/test_migrations_and_seed.py` |
| Backend full tests | Passed: `47 passed` with `pytest -W error` |
| Alembic upgrade | Passed: `uv run alembic upgrade head` completed successfully |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| Flutter formatting | Passed: `dart format` reported `Formatted 1 file (0 changed)` |
| Flutter verification | Passed: `./scripts/verify_flutter.sh`; analysis clean and `22` widget/golden tests passed |
| Whitespace check | Passed: `git diff --check` |

Staging deployment was not touched, so no staging verification is claimed.

## Deferred to Week 4

- accessibility, keyboard navigation, text-scaling, and broader responsive QA;
- security/dependency review and log-content audit;
- production upload validation and backup restore rehearsal;
- physical-device, browser, TestFlight, Android closed-testing, and web
  deployment release checks;
- beta privacy notice, consent, account deletion, feedback form, known
  limitations, and release tagging.
