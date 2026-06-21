# Dream Shard

## Definition

A dream shard is an independently meaningful utterance.

A dream shard is larger than a token and smaller than a stable card. It is
pre-card material that may later support geometry-aware placement work.

## Scope

- Preserve a small utterance-like unit.
- Track a conservative source and status.
- Carry optional anchor hints.
- Carry flat string metadata.

## Non-Scope

A dream shard is not a card, folder, parent node, vector embedding, graph node,
recall result, global atlas entry, final memory fact, or confirmed project
decision.

## Record Shape

```text
shard_id
text
source
status
anchors_hint
metadata
```

Allowed statuses:

```text
draft
candidate
rejected
archived
```

Allowed sources:

```text
user_utterance
assistant_utterance
llm_work_residue
project_note
imported_text
```

## Validation Rules

Text is normalized by trimming surrounding whitespace and collapsing internal
whitespace runs. The normalized text must be non-empty, at least eight
characters long, and contain at least one non-punctuation, non-whitespace
character.

Anchor hints are advisory strings only. Empty anchor hints are invalid.

Metadata is flat string-to-string data. Nested objects are not part of D3.

## Relation to Cards

A dream shard is pre-card material. D3 does not create cards automatically, does
not confirm memory, and does not decide card trust or status.

## Relation to Geometry

D3 does not place shards into geometry. Geometry-based placement is deferred to
later work and must not be inferred from anchor hints.

## Boundary

A dream shard may carry anchor hints, but anchor hints do not create ownership.
D3 does not perform recall, semantic scoring, clustering, vector search, graph
search, MCP behavior, audit expansion, history expansion, or automatic card
writing.
# MT1 Provenance Extension

MT1 native DreamShards add conservative provenance fields:

- `origin_kind`
- `operational_state`
- `epistemic_state`
- `source_refs`
- `continuity_refs`
- `geometry_intent`
- `anchor_field_weights`

Legacy import defaults to `origin_kind: legacy_import`, `operational_state: loose`, and policy-defined `epistemic_state`. Imported legacy text is not automatically confirmed.

## MT1-R1 Source Provenance

Each MT1-R1 imported shard must include exactly matching archive provenance:

- `source_refs` uses `archive://object/sha256:<digest>#B<start>-B<end>`.
- `source_range_hash` is SHA-256 over the raw bytes selected by the source ref.
- `continuity_refs` includes the exact SourceSpan `span_id`.
- `normalization_id` is `nollm.legacy_text_normalization.v1`.
- `text` is the canonical normalized text derived from the archived byte range.
- `text_hash` is SHA-256 over the UTF-8 bytes of `text`.
- A published `SourceSpanLink` points from the span to the shard and from the shard back to the published field revision.

Validation is fail-closed. Prefix-similar archive URIs, nonexistent digests, byte ranges outside the ArchiveObject, mismatched hashes, missing reverse links, duplicate idempotence keys with nonidentical content, or shards absent from the published revision are invalid.

Published validation is HEAD-only. A DreamShard stored in staging, a generic shard directory, or an unpublished revision package is not active memory and cannot prove migration completion.
