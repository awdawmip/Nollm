# DG5 Evidence-Preserving Trace Compaction Validation Report

- validation kind: finite synthetic validation of derived, in-memory compacted transport views
- policy: `dg5_exact_transport_view` version `1`, mode `view_only`
- sealed dependency: DG2 `compact_traces` and `expand_compaction`

## Verified Facts

- Exact duplicate transport views in the finite fixture form compacted view entries.
- Lossless expansion returns every original `GrowthTrace` in canonical input order.
- Distinct evidence identity, proposal, derivation, shared support, or same-cell differences remain passthrough.
- The plan and view are pure-memory, read-only, and disposable derived objects.

## Finite Counts

| fixture | input traces | compacted members | passthrough traces | view entries | estimated view-entry reduction | lossless expansion |
|---|---:|---:|---:|---:|---:|---|
| mixed | 5 | 2 | 3 | 4 | 1 | true |
| stress | 1000 | 400 | 600 | 800 | 200 | true |

- independent passthrough trace count: `301`
- non-conflation witness trace count: `302`
- mixed plan fingerprint: `ba8ce3dd35466f4875047e6641102f4fea4b077c51629e7b384b65635c0fd38a`
- mixed view fingerprint: `8eb498029e160c97d5f754685ba98aa80826a4588d785aa5540fa481c3233e0c`
- stress plan fingerprint: `baf44d03dc7c76c8e2cdf5c6831954d23c91c50c4aa12493d6ac6439adce7538`
- stress view fingerprint: `03e334cc5e1b1da6545ae9f1fba9db1c9a4e11834d854a1b8435f6653ff5e809`

## Reasonable Inference

- A future controlled consumer may choose to read this derived view without changing the original fact source.

## Prohibited Inference

- DG5 does not implement permanent storage compression.
- DG5 does not improve recall or runtime behavior.
- DG5 does not establish global cost reduction.
- DG5 does not prove large-scale workload benefit.
- DG5 does not create parent/child hierarchy, fact ranking, identity merge, or cross-evidence semantic merge.

## Limits

- This report records estimated view-entry reduction only.
- Aggregate mass remains geometric accounting for a view entry; it is not factual importance, truth, trust, rank, or recall priority.
- The validation does not access Evidence, Admission, FieldSnapshot, Recall, runtime, OpenClaw, network, database, cache, LLM/NLP, or embeddings.
