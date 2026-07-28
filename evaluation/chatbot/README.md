# Patient chatbot product-path evaluation

`frozen_suite.v1.json` is the immutable synthetic Phase 3 release gate for the
generated-answer purpose. It executes the real FastAPI patient-chat route with
deterministic DeepSeek stubs and fault injection; it never reads a provider key
or makes a paid/network call.

From `services/api`:

```bash
uv run python scripts/evaluate_chatbot_product.py validate
uv run python scripts/evaluate_chatbot_product.py run
```

Every run writes a new checksum-bearing result under `results/` using exclusive
creation. Passing and failing results are retained. A passing result is
necessary but not sufficient for controlled staging activation: its checksum
must be registered in a compatible chatbot release and activated through the
append-only governance service.

The pending release manifest can be registered and transitioned by the
operator CLI:

```bash
uv run python -m scripts.manage_chatbot_release register \
  --manifest ../../evaluation/chatbot/releases/patient-chat-generated-answer.v1.pending.json \
  --actor-id <operator-uuid> \
  --idempotency-key <unique-key>
```

`activate`, `supersede`, `rollback`, and `kill` require explicit release and
expected-active preconditions. The checked-in v1 manifest remains pending and
kill-switched; an isolated database rehearsal is not staging activation.
