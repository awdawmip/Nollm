# Review

Review is a deterministic active inspection surface for cards matching metadata filters.

Nollm is LLM-first. Human inspection is optional, active, and ledgered. Review is not a passive inbox and does not imply that humans must clear a queue before Nollm can be useful.

It is read-only. It does not append ledger events, write recall files, write audit files, change card status, or modify card bodies.

Review is not semantic judgment. It does not score truth, completeness, quality, priority, or risk.

Human input is an operator action, not an oracle. Review does not approve cards and does not confirm memory. Use the `status` command for operator-approved transitions.

Through the JSON tool bridge, use `nollm.review` for the same read-only metadata inspection. The tool returns the standard `nollm.tool.v0.1` envelope and does not include full card bodies by default.

## Default Queue

The default inspection surface lists cards with these statuses:

- `candidate`
- `draft`

Confirmed cards are excluded by default because the default view is for draft/candidate inspection, not because confirmed cards are factually true.

## Filters

Review supports exact metadata filters:

- `--status`
- `--type`
- `--anchor`
- `--trust`
- `--limit`

Filters are exact metadata filters only. Review does not perform semantic matching or full-text search.

## Ordering

Cards are sorted deterministically:

1. `draft`
2. `candidate`
3. `created` ascending
4. `address` ascending

## Review Reason

`review_reason` is deterministic metadata only, such as:

- `status:candidate`
- `status:draft`
- `trust:unverified`
- `source:llm_inference`

Do not treat `review_reason` as semantic scoring, truth assessment, or priority assigned by Nollm.

## No Read Gate

Review is not a read gate. Unconfirmed cards remain readable with status, trust, and source metadata. LLMs may use draft or candidate cards cautiously when surfaced by recall or read workflows.

Review does not block LLM usage of Nollm.
