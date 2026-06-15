# Dream Placement

## Definition

Dream placement is a candidate placement record for a dream shard inside a
local chart.

## Scope

- Record candidate addresses for a dream shard.
- Record explicit placement energy terms.
- Rank candidate alternatives deterministically.
- Preserve reasons and anchor hints as inspection aids.

## Non-Scope

Dream placement is not a card. Dream placement is not confirmed memory. D4 does
not perform recall, clustering, card writing, or global atlas construction.

## Record Shape

```text
shard_id
chart_id
address
energy
anchors_used
reasons
status
```

Dream placement may produce multiple alternatives for the same shard.

## Energy Terms

Placement energy is an explicit numeric ranking aid, not semantic truth.

Terms:

```text
semantic_hint_cost
geometric_distance_cost
density_pressure_cost
coverage_potential_cost
future_scan_cost
merge_complexity_cost
compute_cost
```

Lower total energy ranks earlier.

## Placement Statuses

```text
candidate
placed_uncertain
new_chart_candidate
rejected
```

`confirmed` is not a D4 placement status.

## Relation to Dream Shards

A dream placement references a dream shard by `shard_id`. It does not create a
card, confirm memory, or write shard content.

## Relation to Geometry

D4 uses local chart identity and hex addresses as bounded candidate geometry.
Candidate generation does not create anchor ownership.

## Boundary

Dream placement does not create anchor ownership. Anchor hints and reasons are
explicit inputs only. D4 does not add embeddings, vector search, graph search,
MCP behavior, agent runtime behavior, SQLite recall paths, audit expansion, or
history expansion.
