# Trust

Trust describes review and support for a card claim. Trust is not the same as status.

Status answers: should this object be surfaced by default?

Trust answers: how should Cortex weigh the claim?

## Allowed Values

- `human-approved`: Explicitly approved by a human.
- `policy-approved`: Reserved for later versions; not valid for promoting to `confirmed` in v0.1.
- `source-backed`: Supported by cited project files, ledger events, or references.
- `llm-proposed`: Proposed by Cortex and awaiting review.
- `unverified`: Recorded but not checked.
- `conflicted`: Known to conflict with another source or card.

## v0.1 Rule

`confirmed` cards should usually have `human-approved` or `source-backed` trust. LLM inference alone must not be recorded as confirmed fact. `policy-approved` is vocabulary reserved for future protocol work, not a v0.1 confirmation path.
