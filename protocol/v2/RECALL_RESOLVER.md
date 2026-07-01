# DR1 Recall Resolver Contract

DR1 defines a read-only foundation for resolving a `CompiledQueryProbe` against
an explicit finite `RecallUniverse`.

## Inputs

- `CompiledQueryProbe`: DC1 query object. The resolver reads it as supplied and
  does not recompile it.
- `RecallUniverse`: explicit finite proposal, trace, cover, coverage, gravity,
  interpretation, and revision objects supplied by the caller.
- `RuntimeTimeResolution`: caller-supplied resolution for relative-time query
  atoms. Missing or incomplete relative-time resolution defers recall; fabricated,
  duplicate, extra, or non-query spans are rejected.
- DE1 evidence store read API: used only to read DreamShard content and
  UsageState.

## Output

The output is an ephemeral `RecallDigest`.

The digest may contain:

- `outcome`: `resolved`, `insufficient_evidence`, `deferred`,
  `budget_exhausted`, or `rejected`;
- partitioned `primary_evidence` and `contextual_evidence`;
- exact projection references to proposal steps and accepted traces;
- directed coverage traversal diagnostics;
- residual mass diagnostics;
- gravity tie-break metadata;
- interpretation and revision context identifiers.

The digest must not be persisted by DR1 and must not mutate Evidence, Cortex,
Geometry, Field, Adapter, runtime, or ledger state.

## Projection Rules

Recall seeding is structural:

- Query atoms must come from `explicit_in_query` steps or caller-supplied
  relative-time resolution bound exactly to the original query `TextSpanRef`.
- Stored support must bind back to a current accepted DC1 proposal step by exact
  axis, basis, and basis reference identity.
- Accepted traces may seed recall only through stable or crystallized covers
  that satisfy DG2 structural support rules.
- Generic single-axis matches are insufficient.

No NLP, semantic search, embeddings, vector similarity, geometry recall,
automatic placement, automatic anchor creation, or automatic context composition
may fill a missing structural projection.

## Evidence Qualification

DreamShard is the primary evidence fallback. UsageState qualifies inclusion:

- `active`: primary evidence;
- `tentative`: primary evidence only when policy allows tentative evidence;
- `retired`: context-only unless policy explicitly includes retired context;
- `rejected`: context-only unless policy explicitly includes rejected context.

Interpretation and Revision records are context. They do not replace DreamShard
content, determine truth, or change usage state.

## Coverage And Gravity

`K_up` and `K_down` direction is preserved exactly. Residual mass and residual
reasons are carried into traversal diagnostics instead of being inferred away.
Wrong-direction distributions reject the universe.

DR1 traversal is finite and budget-bound. It executes explicit supplied
`fine_to_coarse` distributions before cover intersection and explicit supplied
`coarse_to_fine` distributions before evidence fallback. Budget truncation is
reported as `budget_exhausted` or a structured diagnostic, never as an unmarked
successful recall.

Seed-cover budget is applied only after exact required query atoms have formed
structural seed candidates. Stable or crystallized covers that never become
exact-match candidates may be diagnosed, but they do not consume
`max_seed_covers` and do not by themselves exhaust recall.

Traversal budget accounting is digest-global over the selected executable route
set after global route identity deduplication. `max_cells_per_layer`,
`max_layers`, and `max_charts` count the union of selected route cells, layers,
and chart fingerprints for the whole digest. `max_lateral_hops` counts unique
executed direct cross-chart coverage graph edges; repeated use of the same
`K_up` or `K_down` edge by multiple traces or axes counts once.

Gravity may be used only as a deterministic tie-break among already eligible
structural candidates with equal core scores within fixed machine epsilon. It is
not a score bonus, external selector, query parameter, anchor, index, or evidence
source.

## Universe Validation

DR1 validates the finite `RecallUniverse` before seed or traversal:

- current proposals require accepted growth receipts and normalized payload
  fingerprints matching the supplied proposal;
- proposal, trace, cover, and compaction IDs must be unique;
- traces must resolve to readable DreamShards and uniquely bind current proposal
  steps;
- covers must match their support traces, support shards, support keys, axes,
  DG2 structural floors, and supplied CoverPolicy identity;
- compactions must expose complete member expansion manifests;
- `K_up` must be `fine_to_coarse` and `K_down` must be `coarse_to_fine`.

## Legacy Compatibility

Legacy DC1 proposal records may be surfaced as read-only context by policy, but
they do not seed DR1 recall unless admitted through the current DC1 contract.
