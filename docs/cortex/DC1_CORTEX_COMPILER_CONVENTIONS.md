# DC1 Cortex Compiler Conventions

DC1 submissions are strict mappings. Unknown fields are rejected rather than
ignored. Absent values and empty strings are distinct.

Growth Proposals are durable Cortex artifacts. Query Probes are ephemeral and
must leave the Cortex root and Evidence root unchanged.

`relative_time` is forbidden in Growth. In Query, relative-time expressions are
preserved with a caller-supplied runtime-resolution requirement; DC1 never
computes an absolute date such as "yesterday -> 2026-06-29".

Query `relative_time` requires an exact `explicit_in_query` span. A rule-only
relative-time ray is rejected because it would lose the caller's original
relative expression.

Growth budget keys are `max_axes`, `max_total_steps`, and `max_ray_steps`.
Query budget keys are `max_axes`, `max_charts`, `max_layers`, and
`max_cells_per_layer`.

`possible_conflict_refs` are explicit DE1 DreamShard or InterpretationRecord
IDs. DC1 checks only existence and duplicates; it does not read those records as
basis and does not judge conflicts.

`provisional_llm_generalization` remains provisional-only metadata for later
Field stages. DC1 does not upgrade it into truth, stable state, or confirmed
memory.
