# Expected-care explanation evaluation

This folder is a frozen, wholly synthetic research/evaluation boundary for
`expected_care_role_explanation`. It is not operational input, training data,
or evidence for real patients or payer requests.

- `frozen_suite.v1.json` covers rehabilitation, laboratory, alternate
  pathways, quantities/ranges, missing/conflicting facts, release drift,
  currencies/arithmetic, pending cost, clinician positions, payer boundaries,
  provider/schema/leakage failures, cross-role attacks, bilingual equivalence,
  and fallback.
- `results/*.sanitized.json` contains content-free metrics, checksums, latency,
  provider-reported tokens, configured cost, and diagnostic codes.
- `results/raw/` is ignored and protected because it contains the exact
  synthetic fact objects and raw provider output.
- `releases/*.pending.json` is the immutable release input. Pending review
  statuses are deliberate and must never be rewritten as approvals.

Failed live runs `20260726T104515Z` and `20260726T110243Z` are retained. The
first exposed empty citations for absence claims; explicit absence facts fixed
that contract. The later hardening run exposed an attempted citation to
top-level purpose metadata; prompt v2 now permits only exact IDs from the facts
array. The source-checksum-gated final live run `20260726T111243Z` passed all
machine gates. Its pending v2 release is predecessor-linked to the immutable
pending v1 registration; external reviews and runtime activation remain
blocked.
