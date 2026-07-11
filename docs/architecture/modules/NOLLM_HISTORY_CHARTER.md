# Nollm History Charter

Purpose: optional semantic version chains, timelines, and historical retrieval.

- Persistent state: semantic versions and product-level snapshot associations.
- Temporary state: timeline projections.
- Public API: append/query/version linkage through Access contracts.
- Forbidden API: Core mutation internals, Trace substitution, Snapshot-as-history claims.
- Dependencies: Access contracts; optional Snapshot.
- Failure: never affects Core current-state correctness.
- Distributions: optional audited/debug compositions.
- Future repository: `nollm-history`.
- Current sources: historical/revision assets remain candidates pending M1 extraction.
