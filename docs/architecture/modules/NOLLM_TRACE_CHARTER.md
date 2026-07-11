# Nollm Trace Charter

Purpose: optional operation, frontier, bridge, partition, cache, and performance observation.

- Persistent state: sink-owned event streams; Core owns none.
- Temporary state: sink buffers and metric accumulators.
- Public API: Null, JSONL, console, memory, metrics, composite sinks, and Trace inspector over Core's immutable event contract.
- Forbidden API: mutation authority, facts, audit decisions, product policy.
- Dependencies: Core trace contracts only.
- Failure: sink errors are isolated and cannot change Core results.
- Distributions: debug and audited; optional elsewhere.
- Future repository: `nollm-trace`.
- Current sources: ledger, digest, metrics, inspector, and benchmark assets after ownership review.
