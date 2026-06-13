# Architecture

Nollm treats Architecture is the Index as a design constraint. A memory is oriented through source files, cards, anchor fields, addresses, and ledger events, not through hidden model state or opaque retrieval machinery.

Required principles:

- Not an LLM.
- Architecture is the Index.
- Anchor is Field, not Folder.
- Recall is Scale Scan, not Tree Descent.
- SQLite is Audit Projection, not Memory.

Nollm is a layered rotating honeycomb memory field. Anchors are column fields / semantic fields crossing layers. Cards exist at every scale as durable memory expressions. Recall is scale scanning, not tree descent, and there is no absolute leaf layer.

## Layers

### Nollm Core

Core defines the durable notebook:

- Cards in Markdown.
- Anchors in YAML.
- Aliases in YAML.
- Ledger events in JSONL.
- Recall digests in Markdown or JSON.
- Memory addresses as deterministic references.
- Statuses and action records.

Core must be boring by design. It should validate, append, and expose records without interpreting them creatively.

For v0.1, promotion to `confirmed` requires explicit human approval. Policy-event confirmation is deferred until a later version defines it strictly.

### Nollm Cortex

Cortex is the orientation layer used by an LLM or prompt wrapper:

- Identifies active anchor fields.
- Reads cards by address.
- Writes new cards according to policy.
- Summarizes recall material into digest form.
- Proposes drafts, candidates, or status changes for approval.
- Keeps model-side reasoning separate from Core truth.

Cortex may be adaptive. Core must remain stable.

## Index Principle

Architecture is the Index. The durable architecture is expressed by Markdown, YAML, JSONL, card fields, anchor fields, addresses, and ledger events. SQLite, if used, is only an optional audit projection, not memory.

`search` may help an implementation inspect files, but the cognitive interface remains anchor-field-oriented: orient, surface, focus, recall. Conceptually, this is scale scan, not tree descent.

The current runtime remains filesystem-first and deterministic. It does not implement honeycomb geometry, coordinate placement, or a visualization engine.

## Audit Projection

P6.0 audit reports are deterministic file-first projections over cards, anchors, ledger events, recall digests, validation results, honeycomb metadata, and scale-scan metadata.

Audit output is rebuildable and disposable. It is not memory, not a recall index, and not source of truth. Deleting audit output must not change recall behavior.

P6.0 does not introduce SQLite. SQLite, if ever added, remains optional audit projection only.

## Exclusions For v0.1

Nollm v0.1 excludes embeddings, vector stores, graph backends, automatic ontology generation, autonomous memory mutation, and external LLM extraction pipelines.
