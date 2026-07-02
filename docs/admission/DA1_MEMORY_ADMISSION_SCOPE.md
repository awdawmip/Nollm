# DA1 Memory Admission Scope

DA1 implements the deterministic write-side admission boundary for host-supplied
synthetic inputs.

In scope:

- immutable admission request, placement plan, record, receipt, and projection
  value objects;
- zero-write preflight through DC1, DG1, and DG2 public APIs;
- ordered commit through DE1, DC1, then DA1 AdmissionRecord;
- idempotent retry for the same request;
- explicit conflict rejection for changed admission payloads and reused
  proposals;
- read-only replay from AdmissionRecord plus DE1/DC1 and sealed geometry/field
  APIs;
- DA1.1 Replay & Record Closure for cross-chart link replay manifests,
  mandatory non-empty-store replay validation, plan fingerprint closure,
  RFC3339 `recorded_at` validation, and zero-kernel placement rejection.

Out of scope:

- LLM, NLP, Query, Recall, DI1, OpenClaw, runtime, CLI, network, databases,
  caches, sessions, queues, concurrency, or global Field state;
- automatic placement, multi-step ray admission, automatic crystallization,
  compaction, or Field snapshot persistence;
- any modification to sealed DE1, DC1, DG1, DG2, DR1, DI1, or DX1 production
  implementation modules.

DA1.1 does not open DA1.2. Multi-step rays, automatic placement, global Field
persistence, Query, Recall, DI1, runtime, OpenClaw, security systems, network,
database, cache, and concurrency remain deferred.

DA1.1R closes only the `recorded_at` timestamp profile. It accepts `None` or
`YYYY-MM-DDTHH:MM:SS[.fraction](Z|+HH:MM|-HH:MM)` and preserves accepted text
exactly. It does not introduce time inference, clock filling, locale handling,
timezone databases, relative time resolution, or runtime integration.
