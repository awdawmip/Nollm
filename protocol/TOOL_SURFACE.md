# Tool Surface

The Nollm tool surface exposes deterministic filesystem actions through JSON envelopes.

This is MCP-preparation only. It is not an MCP server, HTTP server, websocket server, agent runtime, or model integration.

## Read-Only Actions

- `nollm.validate`
- `nollm.audit`
- `nollm.inspect`
- `nollm.review`
- `nollm.annotations`
- `nollm.orient`
- `nollm.surface`
- `nollm.focus`
- `nollm.recall`
- `nollm.read_card`
- `nollm.ledger`
- `nollm.history`

`nollm.recall` writes recall digest files, but it does not mutate canonical memory or append ledger events.

`nollm.audit` returns a deterministic derived audit report. It is read-only, does not append ledger events, does not create files, does not use SQLite, and must not be used as memory recall.

The audit report JSON shape is a stable inspection contract documented in `protocol/AUDIT_SCHEMA.md`. It is not a memory schema, not a recall digest schema, and not source memory. `examples/audit_reports/*.json` files are deterministic audit snapshots for examples and regression tests, not notebook memory.

`nollm.inspect` returns a deterministic active inspection surface for cards matching metadata filters. It is read-only, does not append ledger events, does not include full card bodies by default, does not approve cards, and does not change status.

Use inspect for optional operator inspection. Do not use inspect as proof that a card is true or false, do not use it as memory recall, and do not treat `review_reason` as semantic scoring, truth assessment, or priority assigned by Nollm. Use `nollm.update_status` or the CLI `status` command for operator-approved transitions.

`review` remains a compatibility command; its semantics are active inspection.

Inspect is not a read gate. Unconfirmed cards remain readable with status, trust, and source metadata.

`nollm.annotations` lists ledgered operator notes for a card. Annotations do not modify card content, change status, change trust, prove truth, approve memory, block LLM usage, or create passive human review.

Inspect/review may show `annotation_count`. Audit may count annotations. Annotation text is not recall content. Annotation counts are not semantic risk scores. `annotation_count` means there are operator notes, not that a card is more or less reliable.

`nollm.ledger` returns filtered audit trail events. `nollm.history` returns object-level ledger inspection. Ledger/history do not prove truth, approve memory, change status, change trust, perform semantic scoring, or act as recall.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

`nollm.recall` returns a digest with scale-scan metadata:

- `active_anchor_fields`
- `scale_path`
- `lateral_recovery`
- `sufficient_scale_reached`

Treat these as metadata-only reading aids. `scale_path` is not a tree path, not a geometry result, and not evidence that Core calculated polygon overlap. `sufficient_scale_reached` does not mean semantic completeness.

## Path Resolution

`notebook_path` is resolved relative to the current working directory of the `nollm tool` process.

It is not resolved relative to the request JSON file.

Example tool requests in this repository are written for a documented working directory. The built-in runnable OpenClaw recall example is intended to be run from `reference/python`:

```bash
cd reference/python
python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json
```

In that request, `notebook_path: "../../examples/openclaw"` resolves from the `reference/python` process directory.

## Example Request Convention

Top-level files in `examples/tool_requests/*.json` are runnable examples. They are intended to be executed from `reference/python` unless a file says otherwise.

Files under `examples/tool_requests/templates/` are request templates and may contain placeholders. They are not expected to run as-is.

If `examples/tool_requests/error_cases/` exists, files inside it are intentional failure examples and must return structured `ok: false` errors.

## Ledger-Writing Actions

- `nollm.write_card`
- `nollm.update_status`
- `nollm.annotate`

These actions must preserve Core validation rules:

- `write_card` must not create `confirmed` cards directly.
- `write_card` must not create anchors automatically.
- `update_status` must append a ledger event.
- `annotate` must append a ledger event and must not mutate the target card.
- `confirmed` requires explicit operator approval.
- Cards with `source: llm_inference` must not be directly confirmed.
- Self-supersede must be rejected.

Tool bridge ledger events should record honest actor metadata. The default is `actor: tool_user` and `actor_type: tool`; requests may provide `actor` and `actor_type`.

For `nollm.annotate`, the annotation default actor is `operator` and the default `actor_type` is `human` when no actor metadata is provided. Annotation is an active operator action, not approval or truth judgment.

## Boundary

The tool surface formats requests and responses. It does not add embeddings, vector databases, graph databases, external LLM extraction, automatic ontology generation, network calls, or autonomous memory mutation.
