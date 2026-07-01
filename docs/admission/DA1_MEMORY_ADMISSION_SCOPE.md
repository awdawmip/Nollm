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
  APIs.

Out of scope:

- LLM, NLP, Query, Recall, DI1, OpenClaw, runtime, CLI, network, databases,
  caches, sessions, queues, concurrency, or global Field state;
- automatic placement, multi-step ray admission, automatic crystallization,
  compaction, or Field snapshot persistence;
- any modification to sealed DE1, DC1, DG1, DG2, DR1, DI1, or DX1 production
  implementation modules.
