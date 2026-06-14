# Read

`read_card` reads exactly one explicit card.

`read_card` is not recall. `read_card` is not context composition. `read_card` does not return neighbors. `read_card` does not rank related cards.

Core does not assemble deterministic context. Context composition belongs to Cortex / LLM using explicit calls.

If an LLM needs context, it should make explicit read/inspect/history/ledger/recall calls and compose outside Core.

Surface relation:

- `read` / `read_card` = explicit object read
- `inspect` / `review` = active metadata surface
- `history` = object-level ledger trail
- `ledger` = ledger query
- `annotations` = annotation listing
- `recall` = scale-scan digest
- context composition = Cortex-side, not Core
