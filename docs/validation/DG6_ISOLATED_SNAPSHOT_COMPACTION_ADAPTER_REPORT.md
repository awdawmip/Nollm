# DG6 Isolated Snapshot Compaction Adapter Report

## Scope

DG6 validates a host-supplied finite DF1 `FiniteFieldSnapshot`, derives DG5 view-only compaction from `snapshot.replayed_traces`, and returns an immutable in-memory `SnapshotCompactionProjection`.

It does not modify snapshot, admission, evidence, field, recall, runtime, storage, cache, database, CLI, OpenClaw, LLM, NLP, embedding, or semantic-search state.

## Verified Facts

- empty snapshot input traces: `0`
- empty snapshot view entries: `0`
- real DX2-style CI1->BA1->DA1->DF1 snapshot id: `sha256:66c8bfe2a4e952048b646bbf903ebdd03d732b8b2698c5eed1f5b648a424fa0a`
- real DX2-style expanded trace count: `8`
- real DX2-style DG5 plan id: `compression_plan:dg5:aaa5c08ceb652a68062165ba86452539`
- isolated synthetic duplicate input traces: `2`
- isolated synthetic duplicate compacted members: `2`
- isolated synthetic duplicate passthrough traces: `0`
- isolated synthetic duplicate view entries: `1`
- isolated synthetic duplicate estimated view-entry reduction: `1`
- isolated synthetic stress input traces: `1000`
- isolated synthetic stress compacted members: `400`
- isolated synthetic stress passthrough traces: `600`
- isolated synthetic stress view entries: `800`
- isolated synthetic stress estimated view-entry reduction: `200`

The duplicate and stress rows are isolated synthetic adapter fixtures. They verify DG6/DG5 projection and expansion behavior; they do not claim that DF1 real admission naturally produced duplicate transport views.

## Reasonable Inference

A future controlled consumer can read this derived projection without changing the finite snapshot or upstream fact sources.

## Forbidden Inference

This report makes no runtime speedup, recall quality, storage compression, automatic compaction, cross-snapshot deduplication, semantic fusion, memory, token, latency, workload, or cost claim.

## Pending Verification

Runtime consumers, cross-snapshot policy, persistent compression, performance measurement, and real workload benefit remain unverified.
