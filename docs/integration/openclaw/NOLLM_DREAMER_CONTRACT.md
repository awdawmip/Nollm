# Nollm Dreamer Contract

Status: OCP7 semantic delta v1.

OpenClaw `MEMORY.md`, `DREAMS.md`, and `memory/*.md` are read-only source files. A normal OpenClaw LLM may act as Dreamer, but it only emits semantic intent. Nollm Core owns final geometry placement.

## Input

- immutable Dream Packet `nollm.dream_packet.v1`;
- source snapshot metadata: path, SHA-256, byte count, line count, and snapshot hash;
- bounded source material text from read-only `MEMORY.md`;
- optional bounded prior-field summary;
- optional source diff metadata during refresh;
- no current user question.

Dream Packet source material is Dreamer-only input. It lets the ordinary LLM distill source meaning into semantic intent. It must not become a Cortex runtime recall unit, search hit, or top-k chunk.

```json
{
  "schema": "nollm.dream_packet.v1",
  "source_snapshot_hash": "...",
  "field_id": "openclaw-dream-field",
  "source_material": [
    {
      "source_path": "MEMORY.md",
      "source_sha256": "...",
      "line_range": [1, 18],
      "text": "actual read-only source text",
      "material_id": "..."
    }
  ],
  "prior_field_summary": []
}
```

## Output Schema

The Dreamer emits exactly one JSON object:

```json
{
  "schema": "nollm.dreamer_delta.v1",
  "source_snapshot_hash": "...",
  "field_id": "openclaw-dream-field",
  "shards": [
    {
      "semantic_key": "stable-key",
      "text": "one independently meaningful dream sentence",
      "status": "source_backed",
      "preferred_scale": "coarse",
      "anchors": ["OpenClaw", "Nollm"],
      "source_links": [
        {"source_path": "MEMORY.md", "line_range": [3, 5], "source_sha256": "..."}
      ],
      "continuity": {"prior_semantic_key": null},
      "near_intents": [],
      "bridge_intents": []
    }
  ],
  "cluster_intents": [{"label": "cluster", "members": ["stable-key"]}]
}
```

Allowed shard statuses are `source_backed`, `derived`, and `tentative`. Allowed preferred scales are `coarse`, `bridge`, and `fine`.

Forbidden anywhere in Dreamer output: `q`, `r`, `layer`, `HexAddress`, `rank`, `score`, `query`, `answer`, `top_k`, and `embedding`.

## Core Responsibilities

Core validates source hashes, packet-bounded line ranges, duplicate semantic keys, and forbidden fields before publishing. It then deterministically places shards into the honeycomb field, stores Dreamer intents as provenance only, and publishes an immutable field revision.

The Dreamer never writes source memory files and never supplies geometry coordinates.
