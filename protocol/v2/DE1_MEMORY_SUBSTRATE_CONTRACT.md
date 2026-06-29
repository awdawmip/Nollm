# DE1 Memory Substrate Contract

DE1 stores original Dream Shards, externally supplied Interpretation records,
explicit Revision Threads, Usage State transitions, and append-oriented Ledger
events. It is the Memory Substrate / Epistemic Core for Dream Geometry V2.

DE1 does not judge truth, authenticate sources, parse natural language, generate
Growth Proposals, create Trace/Cover/Gravity objects, run recall, or connect to
OpenClaw, CLI, adapters, runtime, databases, or vector search.

## Objects

- `DreamShard` preserves original expression, origin descriptor, temporal
  context, context refs, and initial usage state.
- `InterpretationRecord` is a separate externally supplied statement about an
  existing Dream Shard. It never overwrites shard content.
- `RevisionThread` records explicit relations among existing shards and
  interpretations. Replacement relations are checked for cycles.
- `UsageStateTransition` changes only the usage projection of a shard or
  interpretation. It does not mutate the target object.
- `LedgerEvent` records accepted writes in store order. It is not a
  cryptographic anti-tamper chain.

## Store

`MemorySubstrateStore(root)` writes canonical JSON under the caller-provided
root only:

```text
format.json
shards/
interpretations/
revision_threads/
state_transitions/
ledger/events.jsonl
```

Same ID and same payload is idempotent. Same ID and different payload is
rejected. Closing and reopening the root must reconstruct objects, ledger order,
and usage-state projection.

All durable DE1 record IDs are globally unique within one store root. The same
ID cannot name both a Dream Shard and an Interpretation, Revision Thread, or
Usage State Transition. This prevents usage-state and revision references from
becoming epistemically ambiguous; it is not a user identity or authorization
rule.

Every durable object must have exactly one matching ledger event, and every
ledger event must point to exactly one matching object with the expected record
type, record ID, payload key, and filename position. This ledger closure is a
file-format consistency rule for DE1 reads, not a signature, hash chain, or
anti-tamper promise.

An already accepted `UsageStateTransition` can be retried with the same
canonical payload and transition ID. Such a retry is idempotent and does not
re-evaluate the historical `expected_from_state` against the current projection.

Relative-time expressions are preserved as expressions with optional reference
instants; DE1 does not normalize them into event facts.
