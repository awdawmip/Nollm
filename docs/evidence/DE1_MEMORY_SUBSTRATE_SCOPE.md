# DE1 Memory Substrate Scope

DE1 establishes a file-first Memory Substrate / Epistemic Core under
`nollm.dream_geometry.evidence`.

It can save and reopen:

- original Dream Shards;
- external Interpretation records;
- explicit Revision Threads;
- Usage State transitions;
- append-oriented Ledger events.

It cannot and must not decide objective truth, infer entities, normalize natural
language time, generate Field objects, select recall results, or connect to any
runtime, CLI, adapter, OpenClaw plugin, or real memory store.

DG1 Geometry and DG2 Field are sealed dependencies. DE1 may preserve opaque
string refs that future stages can use, but it does not import Geometry or
Field.

DE1.1 closes identity and ledger consistency only: transition retry
idempotency, bidirectional object/ledger closure, and global durable record ID
uniqueness. These are store-format and epistemic-identity rules, not security,
locking, crash recovery, or runtime integration.
