# TQ1 Bounded Complete Test Matrix

TQ1 defines a delivery verification protocol for the Nollm repository test suite.

Complete test verification means:

```text
For one git commit and one pytest collection fingerprint, every collected node id is assigned to exactly one shard, every shard completes successfully in an isolated worktree, and verify proves no missing, duplicate, stale, timed-out, malformed, or failed receipt exists.
```

The canonical commands are:

- `plan`: collect real pytest node ids and write a deterministic matrix plan.
- `run-shard`: run one shard or all shards in detached worktrees with hard timeouts.
- `list-shards`: print planned shard ids for host-timeout-safe execution.
- `verify`: re-collect and prove exact coverage.
- `cleanup`: remove matrix-owned external worktrees and optionally receipts.

The protocol does not change Nollm production behavior and does not introduce runtime, OpenClaw, network, LLM/NLP, database, cache, daemon, global discovery, or automatic admission behavior.
