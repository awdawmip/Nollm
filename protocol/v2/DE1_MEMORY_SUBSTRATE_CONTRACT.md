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

Relative-time expressions are preserved as expressions with optional reference
instants; DE1 does not normalize them into event facts.
