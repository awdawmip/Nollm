# DG5 Evidence-Preserving Trace Compaction Protocol

DG5 defines a derived, in-memory, view-only capability over an explicit finite `GrowthTrace` set.

## Contract

- `CompressionPolicy` is immutable and fixed to `dg5_exact_transport_view`, version `1`, mode `view_only`.
- `CompressionPlan` records canonical input trace identities, full trace payload fingerprints, sealed DG2 `TraceCompaction` records, passthrough trace ids, counts, estimated view-entry reduction, and a plan fingerprint.
- `CompactedTraceView` is immutable, read-only, disposable, and not a persistent projection.
- Expansion is lossless and returns original `GrowthTrace` objects in `plan.input_trace_ids` order.

## Sealed Dependency

DG5 delegates exact duplicate eligibility to DG2 `compact_traces(...)` and delegates member expansion to DG2 `expand_compaction(...)`.

DG5 does not copy or modify the DG2 canonical exact-duplicate key.

## Non-Inference

- View-entry reduction is not disk saved, memory saved, token saved, latency reduced, global dedup, or compressed storage.
- Shared support, same cell, or aggregate mass is not evidence identity, factual importance, truth, trust, rank, owner relation, or recall priority.
- DG5 does not delete, replace, merge, persist, or rewrite traces or upstream evidence.
- DG5 does not connect to Evidence, Admission, Assembly, Recall, runtime, OpenClaw, CLI, network, database, cache, LLM/NLP, embeddings, or semantic search.

## Failure Boundary

DG5 rejects duplicate trace ids, invalid policy modes, plan fingerprint mismatch, incomplete manifests, missing trace index entries, trace payload drift, unexpected trace index entries, and expansion manifest mismatch with structured `CompressionPlanningError.reason_code` values.

