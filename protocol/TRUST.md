# Trust

Trust describes review and support for a card claim. Trust is not the same as status.

Status answers: should this object be surfaced by default?

Trust answers: how should Cortex weigh the claim?

## Allowed Values

- `human-approved`: Explicitly accepted by an operator for current notebook use.
- `source-backed`: Supported by cited project files, ledger events, or references.
- `llm-proposed`: Proposed by Cortex and awaiting review.
- `unverified`: Recorded but not checked.
- `conflicted`: Known to conflict with another source or card.

## Reserved Values

- `policy-approved`: Reserved for later versions; not accepted by the v0.1 reference runtime and not valid for promoting to `confirmed` in v0.1.

## v0.1 Rule

`confirmed` cards should usually have `human-approved` or `source-backed` trust. LLM inference alone must not be recorded as a confirmed stable notebook record. `policy-approved` is reserved for future protocol work, not a v0.1 confirmation path.

`human-approved` is a provenance and trust label. It means an operator accepted the record for current notebook use. It is not proof of factual truth, does not make the operator an oracle, and does not outrank source evidence, ledger consistency, or later corrections.
