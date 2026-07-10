# NOLLM GRF7 Limitations and Failure Boundary

- The 10M field is logical and sharded across 100 persisted partitions. It is
  not a single resident 10M `RelationField`.
- OpenClaw and Codex validation uses real lifecycle/queue fixtures through the
  Adapter and Contract, not external production processes.
- Reliability evidence is the permitted 1M-operation substitute, not six wall
  clock hours.
- Workflow comparisons are deterministic fixtures and do not prove universal
  retrieval superiority.
- Global query validation hydrates bounded target/neighbor partitions; it does
  not demonstrate arbitrary remote storage latency or distributed consensus.
- The first resource run mixed the resident process peak into global RSS. It
  was rejected and rerun with stage-local RSS sampling; superseded artifacts
  are retained separately and excluded from final hashes.

None of the global stop conditions occurred: directory and bridges remain
sparse, recall does not scan all partitions, identity survives repartition,
fallback is complete, and Host runtime does not enter Core dependencies.
