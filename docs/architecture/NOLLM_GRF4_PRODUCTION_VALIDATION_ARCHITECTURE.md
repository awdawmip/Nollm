# NOLLM GRF4 Production-like Validation Architecture

```text
File / declared OpenClaw V2 / declared Codex host
  -> adapter mapping and capability declaration
  -> GRF Host Contract
  -> GRFHostService and GRFFacade
  -> FieldEngine, KernelRegistry, RelationField
  -> recall/replay and source fallback
```

GRF4 adds caches inside Core only: compiled coverage templates, relation-field
cell and patch indexes, and immutable field snapshots. Mutations invalidate a
field snapshot; they do not mutate an existing relation field. Core retains no
adapter or terminal import. The OpenClaw and Codex integrations remain
declaration-driven wrappers over the same contract.
