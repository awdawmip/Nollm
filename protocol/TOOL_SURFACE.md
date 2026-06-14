# Tool Surface

The Nollm tool surface exposes deterministic filesystem actions through JSON envelopes.

This is a local JSON bridge only. It is not an MCP server, HTTP server, websocket server, agent runtime, or model integration.

## V1 Surface Table

| CLI command | Tool action | Read/write | Writes ledger? | Mutates card files? | Returns body/text? | V1 status | Notes / boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `validate` | `nollm.validate` | read | no | no | no | stable | Deterministic structural validation only. |
| `orient` | `nollm.orient` | read | no | no | no | stable | Anchor-field orientation; not context composition. |
| `recall` | `nollm.recall` | derived write | no | no | yes | stable | May write recall digest files; not canonical memory or semantic completeness. |
| `read` | `nollm.read_card` | read | no | no | yes | stable | Explicit single-card read; no neighbors or ranking. |
| `inspect` | `nollm.inspect` | read | no | no | no | stable | Active metadata inspection; not truth or approval. |
| `review` | `nollm.review` | read | no | no | no | stable | Compatibility name for active inspection. |
| `annotate` | `nollm.annotate` | write | yes | no | no | stable | Appends operator notes; does not approve or change trust/status. |
| `annotations` | `nollm.annotations` | read | no | no | yes | stable | Lists annotation ledger events. |
| `ledger` | `nollm.ledger` | read | no | no | yes | stable | Audit trail query; not recall or truth. |
| `history` | `nollm.history` | read | no | no | yes | stable | Object-level ledger inspection. |
| `audit` | `nollm.audit` | read | no | no | no | stable | Derived inspection projection; not memory. |
| `audit-check` | none | read | no | no | no | stable | Compares audit snapshots; structural drift only. |
| `tool` | envelope runner | read/write by action | by action | by action | by action | stable | Executes JSON envelope actions. |
| `surface` | `nollm.surface` | read | no | no | no | internal/experimental | Existing orientation helper; not stable V1 external surface. |
| `focus` | `nollm.focus` | read | no | no | no | internal/experimental | Existing orientation helper; not stable V1 external surface. |
| `write` | `nollm.write_card` | write | yes | yes | yes | internal/experimental | Candidate/draft writing helper; no direct confirmed writes. |
| `status` | `nollm.update_status` | write | yes | yes | no | internal/experimental | Operator transition helper; must preserve confirmation boundaries. |
| `tools` | none | read | no | no | no | internal/experimental | Local manifest inspection helper, not a protocol action. |
| `init` | none | write | no | yes | no | internal/experimental | Local notebook bootstrap helper, not a memory protocol action. |

## Stable Read-Only Actions

- `nollm.validate`
- `nollm.audit`
- `nollm.inspect`
- `nollm.review`
- `nollm.annotations`
- `nollm.orient`
- `nollm.recall`
- `nollm.read_card`
- `nollm.ledger`
- `nollm.history`

`nollm.recall` writes recall digest files, but it does not mutate canonical memory or append ledger events.

`nollm.audit` returns a deterministic derived audit report. It is read-only, does not append ledger events, does not create files, does not use SQLite, and must not be used as memory recall.

The audit report JSON shape is a stable inspection contract documented in `protocol/AUDIT_SCHEMA.md`. It is not a memory schema, not a recall digest schema, and not source memory. `examples/audit_reports/*.json` files are deterministic audit snapshots for examples and regression tests, not notebook memory.

`nollm.read_card` reads exactly one explicit card. `read_card` is not recall. `read_card` is not context composition. `read_card` does not return neighbors. `read_card` does not rank related cards. Core does not assemble deterministic context. Context composition belongs to Cortex / LLM using explicit calls.

`nollm.inspect` returns a deterministic active inspection surface for cards matching metadata filters. It is read-only, does not append ledger events, does not include full card bodies by default, does not approve cards, and does not change status.

Use inspect for optional operator inspection. Do not use inspect as proof that a card is true or false, do not use it as memory recall, and do not treat `review_reason` as semantic scoring, truth assessment, or priority assigned by Nollm. Use `nollm.update_status` or the CLI `status` command for operator-approved transitions.

`review` remains a compatibility command; its semantics are active inspection.

Inspect is not a read gate. Unconfirmed cards remain readable with status, trust, and source metadata.

`nollm.annotations` lists ledgered operator notes for a card. Annotations do not modify card content, change status, change trust, prove truth, approve memory, block LLM usage, or create passive human review.

Inspect/review may show `annotation_count`. Audit may count annotations. Annotation text is not recall content. Annotation counts are not semantic risk scores. `annotation_count` means there are operator notes, not that a card is more or less reliable.

`nollm.ledger` returns filtered audit trail events. `nollm.history` returns object-level ledger inspection. Ledger/history do not prove truth, approve memory, change status, change trust, perform semantic scoring, or act as recall.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

## Surface Relation

- `read` / `read_card` = explicit object read
- `inspect` / `review` = active metadata surface
- `history` = object-level ledger trail
- `ledger` = ledger query
- `annotations` = annotation listing
- `recall` = scale-scan digest
- context composition = Cortex-side, not Core

`nollm.recall` returns a digest with scale-scan metadata:

- `active_anchor_fields`
- `scale_path`
- `lateral_recovery`
- `sufficient_scale_reached`

Treat these as metadata-only reading aids. `scale_path` is not a tree path, not a geometry result, and not evidence that Core calculated polygon overlap. `sufficient_scale_reached` does not mean semantic completeness.

## Path Resolution

`notebook_path` is resolved relative to the current working directory of the `nollm tool` process.

It is not resolved relative to the request JSON file.

Example tool requests in this repository are written for a documented working directory. Safe top-level examples run from `reference/python`. Generated-output examples, including the OpenClaw recall example, should run against temporary notebook copies or be cleaned after use:

```bash
cd reference/python
python3 -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json
```

In that request, `notebook_path: "../../examples/openclaw"` resolves from the `reference/python` process directory and may create generated recall digest files.

## Example Request Convention

Top-level files in `examples/tool_requests/*.json` are safe runnable examples. They are intended to be executed from `reference/python` unless a file says otherwise.

Files under `examples/tool_requests/templates/` are request templates and may contain placeholders. They are not expected to run as-is.

Files under `examples/tool_requests/generated_output_examples/` may create generated outputs and should be run against temporary notebook copies.

If `examples/tool_requests/error_cases/` exists, files inside it are intentional failure examples and must return structured `ok: false` errors.

## Ledger-Writing Actions

- Stable V1: `nollm.annotate`
- Internal/experimental: `nollm.write_card`, `nollm.update_status`

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

## V1 Tool Surface Finalization

Every V1 tool response uses the existing `nollm.tool.v0.1` envelope:

- `ok`
- `protocol`
- `action`
- `request_id`
- `result`
- `warnings`
- `ledger_events`
- `addresses`

For read-only tools, `ledger_events` must be `[]`.

For write tools, `ledger_events` contains appended event ids.

Error responses are structured and must not expose raw Python tracebacks.

V1 stable tool actions are `nollm.validate`, `nollm.orient`, `nollm.recall`, `nollm.read_card`, `nollm.inspect`, `nollm.review`, `nollm.annotate`, `nollm.annotations`, `nollm.ledger`, `nollm.history`, and `nollm.audit`.

Additional existing actions are internal or experimental unless later promoted. They must still preserve Core boundaries.
