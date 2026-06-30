# DC1 Cortex Compiler Conventions

DC1 submissions are strict mappings. Unknown fields are rejected rather than
ignored. Absent values and empty strings are distinct.

Growth Proposals are durable Cortex artifacts. Query Probes are ephemeral and
must leave the Cortex root and Evidence root unchanged.

`relative_time` is forbidden in Growth. In Query, relative-time expressions are
preserved with a caller-supplied runtime-resolution requirement; DC1 never
computes an absolute date such as "yesterday -> 2026-06-29".

`provisional_llm_generalization` remains provisional-only metadata for later
Field stages. DC1 does not upgrade it into truth, stable state, or confirmed
memory.
