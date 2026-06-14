# LLM Integration

Nollm is an external notebook for LLMs. External tools should call Nollm through the JSON bridge instead of scraping human CLI output.

## Calling Nollm

Use:

```bash
python -m nollm.cli tool request.json
```

Each request uses the `nollm.tool.v0.1` envelope and receives a structured `ok: true` or `ok: false` response.

`notebook_path` is resolved relative to the current working directory of the `nollm tool` process, not relative to the request JSON file.

Runnable OpenClaw scale-scan recall example:

```bash
cd reference/python
python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json
```

That request uses `notebook_path: "../../examples/openclaw"` so it resolves correctly from `reference/python`.

## Example Request Convention

Top-level files in `examples/tool_requests/*.json` are runnable examples. Run them from `reference/python` unless a file says otherwise.

Files under `examples/tool_requests/templates/` are request templates and may contain placeholders. They are not expected to run as-is.

If `examples/tool_requests/error_cases/` exists, files inside it are intentional failure examples and should return structured `ok: false` errors.

## Read Flow

Use the deterministic Cortex read flow:

`orient -> surface -> focus -> recall`

- `orient`: Identify active anchor fields.
- `surface`: Read finite current-scale cards influenced by those fields.
- `focus`: Select sufficient-scale card front matter and claims.
- `recall`: Produce a one-shot digest when the caller wants context in a single step.

Conceptually this is now interpreted as anchor-field orientation and scale scanning.

For one-shot context retrieval, call `nollm.recall`. For controlled multi-step use, call `nollm.orient`, then `nollm.surface`, then `nollm.focus`.

## Active Inspection

Use `nollm.inspect` to inspect draft and candidate cards matching active metadata filters.

Nollm is LLM-first. Human inspection is optional, active, and ledgered. Human input is an operator action, not an oracle.

Inspect is deterministic metadata inspection. Do not use inspect as proof that a card is true or false. Do not use inspect as memory recall. Do not treat `review_reason` as semantic scoring, truth assessment, or priority assigned by Nollm.

Inspect is not a read gate. Unconfirmed cards remain readable with status, trust, and source metadata. LLMs may use draft or candidate cards cautiously when surfaced by recall or read workflows.

Use `nollm.update_status` or the CLI `status` command for operator-approved transitions.

`review` remains a compatibility command; its semantics are active inspection.

## Operator Annotations

Use `nollm.annotate` to append an operator annotation ledger event to an existing card. Use `nollm.annotations` to list annotation events for a card.

Annotations are operator notes. Annotations are ledgered. Annotations do not modify card content. Annotations do not change status. Annotations do not change trust. Annotations do not prove truth. Annotations do not approve memory. Annotations do not block LLM usage. Annotations are not passive human review. Annotations are active operator actions.

Do not use annotations as recall content by default. Do not treat annotation text as source evidence, truth scoring, approval, or priority assigned by Nollm.

## Audit

Use `nollm.audit` to inspect notebook health, validation status, file counts, metadata distribution, recall digest shape, and boundary flags.

Audit is derived and read-only. Do not use audit as memory recall. Do not treat audit counts as semantic completeness. Do not cite audit output as factual memory content. Use `nollm.recall` or `nollm.read_card` for memory content.

The audit JSON contract is documented in `protocol/AUDIT_SCHEMA.md`. Audit schema stability is for inspection and governance only. It is not a memory schema, not a recall digest schema, and not source memory.

`examples/audit_reports/openclaw_audit.json` is a deterministic audit snapshot for examples and regression tests. It must not be read as notebook memory or used by recall.

Use `audit-check` to compare current derived audit output with a saved snapshot:

```bash
python3 -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
```

Exit code `0` means no drift, `1` means structural drift was detected, and `2` means invalid input or schema error. Audit drift is useful for governance and CI, but it does not prove semantic correctness or incorrectness. Audit drift is not recall, not memory, and not a hidden index.

## Recall Digest Consumption

A recall digest is a reading packet, not canonical memory.

- Treat `active_anchor_fields` as active semantic fields, not ownership folders.
- Treat `scale_path` as a metadata-only scale trace, not a tree path.
- Do not infer geometry overlap from `scale_path`.
- Do not infer semantic completeness from `sufficient_scale_reached`.
- Read `warnings` and `do_not_assume` before relying on recalled points.

Anchor is Field, not Folder. Recall is Scale Scan, not Tree Descent. SQLite is Audit Projection, not Memory.

## Writing

External LLMs may propose durable memory with `nollm.write_card`, but default writes are `candidate`.

External LLMs must not write `confirmed` cards directly. `confirmed` requires explicit operator approval through a status update.

`confirmed` means currently accepted as stable within the notebook. It does not mean factually true, permanently correct, or human oracle truth.

`human-approved` means an operator accepted the record for current notebook use. It is not proof of factual truth and does not outrank source evidence, ledger consistency, or later corrections.

Cards with `source: llm_inference` cannot be confirmed directly. First replace or support the source with human decision, project file, ledger event, user statement, or external reference.

## Actor Metadata

Tool bridge requests should use honest actor metadata:

```json
{
  "actor": "codex",
  "actor_type": "tool"
}
```

Allowed `actor_type` values are `human`, `llm`, `tool`, and `system`.

## Card Statuses

- `candidate`: Plausible, not confirmed. Do not treat as fact.
- `hypothesis`: Tentative explanation or proposal.
- `confirmed`: Currently accepted as stable within the notebook. Not a factual truth guarantee.
- `superseded`: Replaced by newer memory. Preserve for audit.
- `rejected`: Preserved as rejected with reason.
- `archived`: Readable history, not surfaced by default.

## Fallback Lexical Scan

Fallback lexical scan is not semantic understanding. It is a bounded deterministic scan used when no anchor field matched. Treat fallback results as lower-confidence and inspect `anchors_discovered_from_cards`.
