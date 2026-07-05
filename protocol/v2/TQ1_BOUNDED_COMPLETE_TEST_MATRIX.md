# TQ1 Bounded Complete Test Matrix

TQ1 defines a delivery verification protocol for the Nollm repository test suite.

Complete test verification means:

```text
For one clean git commit, one pytest collection fingerprint, and one
plan-owned ignored-runtime fixture snapshot, every collected node id is
assigned to exactly one shard, every shard completes successfully in a
matrix-owned isolated worktree, and verify proves no missing, duplicate,
stale, timed-out, malformed, failed, unowned, or drifted receipt exists.
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
the current matrix call and rooted under a matching matrix marker.

The protocol does not change Nollm production behavior and does not introduce runtime, OpenClaw, network, LLM/NLP, database, cache, daemon, global discovery, or automatic admission behavior.
