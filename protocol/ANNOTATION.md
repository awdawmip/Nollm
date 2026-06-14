# Annotation

Annotations are operator notes recorded as append-only ledger events.

Annotations are ledgered. They do not modify card content, card body, status, trust, source, anchors, or recall digests.

Annotations do not prove truth. They do not approve memory. They do not block LLM usage. They are not passive human review, passive workflow, semantic scoring, or memory recall.

Annotations are active operator actions. They may record notes, concerns, questions, correction requests, or source requests about an existing card.

Allowed annotation types:

- `note`
- `concern`
- `question`
- `correction_request`
- `source_request`

The ledger event uses `op: annotate_card` and records equal `from_status` and `to_status` to make clear that annotation is not a status transition.

Annotation listing reads ledger events for a card. It returns compact event metadata and does not include card bodies.
