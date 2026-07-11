# M1C3 Immutable Kernel, Phase, and Workspace Report

## Verified On Windows

- Registry identity inputs are deeply immutable; exported mappings do not alias.
- Direct CoverageTemplate contradictions in layer, residual, metadata, flags,
  entry order, and fanout are rejected.
- `phase=None` and string phases round-trip through state, Recall, Access, and Snapshot.
- Geometry uses `stable_key`; Anchor cells are sorted unique canonical tuples.
- Lateral supports registered ring 1 only; ring 2 is rejected even with fanout 12.
- One process permits multiple AccessRuntime instances only with the same Core owner.
- A distinct CoreRuntime for the same state path is rejected before Access use.
- Access Recall and saved_handle share the coordinator transaction lock.
- Reuse validates canonical Evidence before writing a supporting binding.

Package gate: 62 passed before final regression. Full parity remains 9/9.

## Guarantee Scope

The coordinator guarantee is same-process only. Multi-process locking, crash
recovery, databases, distributed transactions, PB scale, OpenClaw Live, model
calls, corpus execution, and History/Audit products are out of scope.

The retained external Linux audit remains 109 passed, 1 skipped, with two
zstandard-dependent historical tests unavailable; this task's actual main
acceptance environment is Windows.
