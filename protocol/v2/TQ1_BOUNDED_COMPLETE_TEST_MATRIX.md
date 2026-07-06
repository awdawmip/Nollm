# TQ1 Bounded Complete Test Matrix

TQ1 defines a delivery verification protocol for the Nollm repository test suite.

Complete test verification means:

```text
For one clean git commit, one pytest collection fingerprint, and one
plan-owned ignored-runtime fixture snapshot, every collected node id is
assigned to exactly one shard, every shard completes successfully in a
matrix-owned isolated worktree, and verify proves no missing, duplicate,
stale, timed-out, malformed, failed, unowned, or drifted receipt exists.
Successful shard receipts bind to the actual JUnit `<testcase>` proof count,
with suite `tests` attributes parsed and rejected when malformed, not to a
planned count echoed by the runner.
```

The canonical commands are:

- `plan`: collect real pytest node ids and write a deterministic matrix plan.
- `run-shard`: run one shard or all shards in detached worktrees with hard timeouts.
- `list-shards`: print planned shard ids for host-timeout-safe execution.
- `verify`: re-collect and prove exact coverage.
- `cleanup`: remove matrix-owned external worktrees and optionally receipts.

`plan` must reject dirty source status before collection and before creating
receipt roots. If `out/nollm_runtime` exists, `plan` snapshots it once under
the receipt root and records canonical file hashes. `run-shard` must copy only
that snapshot, never live source `out/nollm_runtime` and never tracked source
checkout bytes. Worktree cleanup is allowed only for shard worktrees created by
the current matrix call and rooted under matching root and per-shard ownership
markers. Cleanup refuses with zero deletions when any existing shard path lacks
the exact per-shard marker, has a mismatched marker, or is outside the plan.

After each runtime fixture copy, `run-shard` re-hashes the copied target inside
the detached worktree and starts pytest only if the target manifest and tree
fingerprints exactly match the plan-owned snapshot. Fixture-copy, pytest
startup, malformed JUnit, and other defined operational failures must leave a
structured shard receipt.

The protocol does not change Nollm production behavior and does not introduce runtime, OpenClaw, network, LLM/NLP, database, cache, daemon, global discovery, or automatic admission behavior.
