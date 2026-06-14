# Audit

An audit report is a deterministic derived projection over a Nollm notebook.

It summarizes existing source-of-truth files:

- cards;
- anchors;
- ledger events;
- recall digests;
- validation results;
- honeycomb metadata;
- scale-scan metadata;
- annotation counts.

Audit output is not memory.

Audit output is not a recall index.

Audit output is not source of truth.

Deleting audit output must not change recall behavior.

Audit may count annotations. Annotation text is not recall content. Annotation text does not change status or trust. Annotation text does not prove truth. Annotation counts are not semantic risk scores. `annotation_count` means there are operator notes, not that a card is more or less reliable.

## P6.0 Scope

P6.0 audit is file-first and rebuildable. It does not use SQLite.

The report may include JSON or Markdown renderings, but both are generated from the same derived audit data.

Audit generation is read-only. It must not append ledger events, create cards, create anchors, or mutate recall digests.

## Schema Contract

The JSON audit schema is documented in `protocol/AUDIT_SCHEMA.md`.

Audit schema stability is for inspection and governance. The schema is not a memory schema, not a recall digest schema, and not source memory.

`examples/audit_reports/openclaw_audit.json` is the deterministic OpenClaw golden snapshot used as an example and regression fixture. Files under `examples/audit_reports/*.json` are not notebook source memory and must not be read by recall.

## Drift Check

`nollm audit-check <notebook_path> --against <snapshot.json>` compares current derived audit output with a saved audit snapshot.

Audit snapshots are regression fixtures. Audit drift checks compare derived inspection output only. Drift means the structural audit report changed; it does not prove semantic correctness or incorrectness.

The comparison ignores environment-dependent fields:

- `notebook.path`

All drifts are sorted deterministically by path. The CLI returns `0` when no drift is found, `1` when drift is found, and `2` for invalid input or schema errors.

Audit drift is not recall, not memory, and not a hidden index.

## Tool Surface

`nollm.audit` exposes the same derived report through the JSON tool bridge.

External LLMs may use audit to inspect notebook health and metadata distribution. They must not use audit as memory recall, cite audit output as factual memory content, or treat audit counts as semantic completeness.

Use `nollm.recall` or `nollm.read_card` for memory content.

## Boundaries

Audit does not perform geometry recall, polygon overlap calculation, automatic placement, semantic completeness scoring, embedding search, vector search, graph traversal, external LLM calls, or MCP service behavior.

SQLite, if ever added, must remain optional, rebuildable, deletable, and audit-only.
