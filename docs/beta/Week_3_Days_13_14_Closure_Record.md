# Week 3, Days 13-14 Chat and Consultation Closure Record

Recorded: 2026-07-05

Status: complete for repository implementation and local verification.

Tencent staging status: not touched in this phase.

## Closure outcome

Week 3 Days 13-14 closed the approved chat and consultation slice:

- server-side DeepSeek educational-chat proxy;
- streaming-style patient chat response UI;
- fixed red-flag emergency escalation before any LLM call;
- persisted per-user chat rate limiting;
- safe fallbacks for timeout, malformed response, quota, unsafe prompt, and
  local/test no-key operation;
- asynchronous synthetic specialist-consultation request and status display.

No real clinical assessment, real model inference, real COS upload completion,
billing, appointments, video/voice consultation, analytics, staging deployment,
production release, or Week 4 hardening/release work was added.

Branch: `codex/week1-days3-5`

Draft stacked PR #1 and PR #2 remain unmerged.

## Backend implementation

Added the smallest coherent Week 3 schema:

- `chat_threads`
- `chat_messages`
- `chat_rate_limits`
- `consultation_requests`

FastAPI now handles `POST /api/v1/chat/threads/{thread_id}/messages`,
`GET /api/v1/consultations`, and `POST /api/v1/consultations`.

DeepSeek keys remain server-side only. `deepseek-v4-flash` is the default
model, while local/test environments and unset keys use a safe fallback so
tests never need a real key or network. Red-flag messages bypass rate limiting
and the adapter, return the fixed emergency guidance, and create a
metadata-only audit event. Unsafe prompts and provider timeout/malformed/quota
failures return bounded educational fallback content.

Chat storage records prompt hash, prompt length, safety category, fallback
reason, and model label only. It does not store raw prompts or raw model output.
Consultation audit metadata records specialty, priority, status, and IDs
without copying the request summary.

Wrong-role and cross-patient access remains neutral `404 not_found`.

## Flutter implementation

The patient dashboard now includes an educational Ask Dr. AI panel that reveals
server response chunks progressively and keeps the frozen educational limitation
visible. Failed sends preserve the typed question.

The doctor Patient Management workflow now includes a synthetic specialist
consultation request panel after recovery-plan editing. The patient Contact
Doctor card displays the latest authorized consultation status. All labels
remain synthetic/non-clinical.

## Documentation updates

- `docs/Dr_AI_v1.0_API_Contract.md` documents the chat and consultation
  contracts.
- `services/api/README.md` documents backend endpoint and safety behavior.
- `apps/dr_ai_app/README.md` documents the new UI/verification coverage.
- `README.md` and `docs/Dr_AI_v1.0_Implementation_Plan.md` mark Days 13-14
  complete.

## Local verification evidence

Recorded after the Week 3 Days 13-14 pass on 2026-07-05.

| Check | Result |
|---|---|
| Backend focused tests | Passed: `9 passed` for `tests/test_week3_chat_consultation.py` and `tests/test_migrations_and_seed.py` |
| Backend Ruff | Passed: `All checks passed!` |
| Backend full tests | Passed: `39 passed` with `pytest -W error` |
| Alembic upgrade | Passed: upgraded `20260705_0004 -> 20260705_0005` |
| Alembic model drift check | Passed: `No new upgrade operations detected.` |
| Flutter verification | Passed: `./scripts/verify_flutter.sh`; analysis clean and `22` widget/golden tests passed |
| Whitespace check | Passed: `git diff --check` |

Staging deployment was not touched, so no staging verification is claimed.
