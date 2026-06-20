# Nollm Dreamer Contract

Status: OCP6R fixture contract.

Nollm is not an embedding-free `MEMORY.md` search adapter. OpenClaw memory files are read-only source snapshots. A normal LLM may act as Dreamer, but tests use checked-in deterministic Dreamer output instead of a live provider call.

Input:

- source snapshot: file identity, SHA-256, read timestamp, and source span references;
- bounded local Nollm surface from a prior field, when available;
- source diff metadata, when refreshing.

Output:

- coarse surface shards;
- bridge shards;
- fine meaningful dream shards;
- source links;
- placement proposals;
- shard trace status: `source_backed`, `derived`, `tentative`, or `superseded`.

The Dreamer must not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`. Nollm Core ingests the Dreamer output, validates the deterministic field, and exposes Cortex traversal tools.

