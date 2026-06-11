# Architecture

Nollm treats architecture as the index. A memory is found through stable paths, anchors, addresses, and ledger events, not through hidden model state or opaque retrieval machinery.

## Layers

### Nollm Core

Core defines the durable notebook:

- Cards in Markdown.
- Anchors in YAML.
- Aliases in YAML.
- Ledger events in JSONL.
- Recall digests in Markdown.
- Memory addresses as deterministic coordinates.

Core must be boring by design. It should validate, append, and expose records without interpreting them creatively.

### Nollm Cortex

Cortex is the orientation layer used by an LLM or prompt wrapper:

- Chooses relevant anchors.
- Reads cards by address.
- Writes new cards according to policy.
- Summarizes recall material into digest form.
- Keeps model-side reasoning separate from Core truth.

Cortex may be adaptive. Core must remain stable.

## Index Principle

The directory layout, filenames, front matter, anchors, and ledger are the index. Derived indexes may be built for convenience, but they are disposable.

## Exclusions For v0.1

Nollm v0.1 excludes embeddings, vector stores, graph backends, automatic ontology generation, autonomous memory mutation, and external LLM extraction pipelines.

