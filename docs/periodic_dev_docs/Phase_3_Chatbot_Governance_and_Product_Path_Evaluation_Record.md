# Phase 3 Chatbot Governance and Product-Path Evaluation Record

Date: 2026-07-27

## Implemented boundary

The patient-chat generated-answer purpose now has a DeepSeek-only v1 provider
contract, default-off purpose enablement, default-on kill switch, and
checksum-bound release readiness. Deterministic emergency, privacy,
authorization, retrieval, medication-change, and fixed fallback behavior stays
provider-independent.

Migration `20260727_0050_chatbot_generation_governance.py` adds immutable
chatbot releases and transition events plus the advisory-locked active release
pointer. Activation and supersession require expected state. Rollback may
target only the active release's exact predecessor. Drift, missing readiness,
kill switch, provider outage, timeout, quota, or malformed output fails closed
without disabling unrelated APIs.

The persisted thread workflow separately supports creation, history, reopen,
archive, soft deletion, source and limitation display, retries, and
question-bounded record-context category disclosure.

## Executable evidence

The frozen suite at `evaluation/chatbot/frozen_suite.v1.json` executes the real
FastAPI patient-chat route through `TestClient` with deterministic adapter
injection. It covers:

- English and Simplified-Chinese answers;
- privacy and context minimization;
- prompt injection;
- malformed output, timeout, quota, and provider outage;
- context drift and cross-patient isolation;
- kill-switch behavior and exact rollback.

The original retained result
`evaluation/chatbot/results/20260726T162853Z.sanitized.json` and the final
clean rerun
`evaluation/chatbot/results/20260726T164729Z.sanitized.json` passed all 11
machine gates through six focused product-path tests. They record zero live
provider calls and no credential use. A clean isolated PostgreSQL database was
upgraded through migration `0051`; focused governance/product-path tests
passed, and register/activate/readiness operations were rehearsed against the
pending manifest.

## Release state and remaining external evidence

`evaluation/chatbot/releases/patient-chat-generated-answer.v1.pending.json`
remains pending and kill-switched. Local passing evidence does not activate it.
Controlled Tencent synthetic staging and a separately recorded live DeepSeek
assurance run remain external Phase 3 exit evidence. Paid calls were
authorized, but no DeepSeek credential was present in the repository or
process environment, so no paid call was made during this local evaluation.
