# Active Inspection

Inspect is the preferred deterministic active inspection surface for cards matching metadata filters.

Nollm is LLM-first. Human inspection is optional, active, and ledgered. Inspect is not a passive inbox and does not imply that humans must clear a queue before Nollm can be useful.

It is read-only. It does not append ledger events, write recall files, write audit files, change card status, or modify card bodies.

Inspect is not semantic judgment. It does not score truth, completeness, quality, priority, or risk.

Human input is an operator action, not an oracle. Inspect does not approve cards and does not confirm memory. Use the `status` command for operator-approved transitions.

Through the JSON tool bridge, use `nollm.inspect` for the same read-only metadata inspection. The tool returns the standard `nollm.tool.v0.1` envelope and does not include full card bodies by default.

`review` remains a compatibility command; its semantics are active inspection.

## Default Queue

The default inspection surface lists cards with these statuses:

- `candidate`
- `draft`

Confirmed cards are excluded by default because the default view is for draft/candidate inspection, not because confirmed cards are factually true.

## Filters

Inspect supports exact metadata filters:

- `--status`
- `--type`
- `--anchor`
- `--trust`
- `--limit`

Filters are exact metadata filters only. Inspect does not perform semantic matching or full-text search.

## Ordering

Cards are sorted deterministically:

1. `draft`
2. `candidate`
3. `created` ascending
4. `address` ascending

## Inspection Reason

`review_reason` is deterministic metadata only, such as:

- `status:candidate`
- `status:draft`
- `trust:unverified`
- `source:llm_inference`

Do not treat `review_reason` as semantic scoring, truth assessment, or priority assigned by Nollm.

## No Read Gate

Inspect is not a read gate. Unconfirmed cards remain readable with status, trust, and source metadata. LLMs may use draft or candidate cards cautiously when surfaced by recall or read workflows.

Inspect does not block LLM usage of Nollm.

Annotations may be used for active operator notes during inspection, but annotations are not approval, truth, status changes, trust changes, card content, passive human review, or memory recall.

Inspect/review may show `annotation_count`. Annotation text is not recall content and is not included in inspect/review card lists. Annotation counts are not semantic risk scores. `annotation_count` means there are operator notes, not that a card is more or less reliable.
