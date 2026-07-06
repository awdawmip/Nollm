# TQ1 Bounded Complete Test Matrix

TQ1 defines a delivery verification protocol for the Nollm repository test suite.

Complete test verification means:

```text
For one clean git commit, one pytest collection fingerprint, and one
plan-owned execution contract, plan-owned ignored-runtime fixture snapshot,
every collected node id is
assigned to exactly one shard, every shard completes successfully in a
matrix-owned isolated worktree, and verify proves the receipt directory
inventory is exactly the planned shard JSON set with no missing, duplicate,
stale, extra, timed-out, malformed, failed, unowned, or drifted receipt.
Successful shard receipts bind to the receipt schema, shard identity, immutable
execution contract, exact planned shard timeout, actual JUnit `<testcase>`
proof count, raw JUnit relative path, raw JUnit SHA-256, raw JUnit size, and
no-failure cleanup state, with suite `tests` attributes parsed and rejected
when malformed, not to a planned count echoed by the runner.
```

The canonical commands are:

- `plan`: collect real pytest node ids and write a deterministic matrix plan.
- `run-shard`: run one shard or all shards in detached worktrees with hard timeouts.
- `list-shards`: print planned shard ids for host-timeout-safe execution.
- `verify`: re-collect and prove exact coverage.
- `cleanup`: remove matrix-owned external worktrees and optionally receipts.

`plan` must reject dirty source status before collection and before creating
receipt roots. It must also reject any existing receipt root; a receipt root is
a non-reusable matrix-instance boundary and is never overwritten or adopted. If
`out/nollm_runtime` exists, `plan` snapshots it once under the receipt root and
records canonical file hashes. `run-shard` must copy only
that snapshot, never live source `out/nollm_runtime` and never tracked source
checkout bytes. The final C7R delivery contract freezes
`planned_shard_timeout_seconds=3600.0`, `retry_policy=forbidden`,
`receipt_overwrite=forbidden`, and `execution_mode=single_pass`; the final
execution is one `run-shard --all --workers 4 --timeout-seconds 3600`
invocation. Existing shard receipts are never overwritten by a non-resume run.
Worktree cleanup is allowed only for shard worktrees created by
the current matrix call and rooted under matching root and per-shard ownership
markers. Cleanup refuses with zero deletions when any existing shard path lacks
the exact per-shard marker, has a mismatched marker, or is outside the plan.
Cleanup failure is a failed shard receipt, even when pytest and JUnit succeeded.

After each runtime fixture copy, `run-shard` re-hashes the copied target inside
the detached worktree and starts pytest only if the target manifest and tree
fingerprints exactly match the plan-owned snapshot. Fixture-copy, pytest
startup, malformed JUnit, and other defined operational failures must leave a
structured shard receipt with failure stage, reason, worktree path, ownership
facts, and cleanup state. Plain operational exceptions are mapped by their
active stage, for example `worktree_add_failed`, `fixture_snapshot_copy_failed`,
`pytest_start_failed`, and `junit_missing_or_malformed`; a worktree-add failure
is not reported as pytest startup failure.

`verify` must reject malformed receipt inventories before reading individual
receipt contents. Extra JSON files, non-JSON files, directories, symlinks,
special files, and missing planned receipts are verification failures and are
not deleted or adopted. A successful verify output includes
`receipt_json_count=<planned-shard-count>` and execution contract fields.

`verify` must also reject malformed JUnit inventories before accepting
successful receipts. The `junit/` directory must contain exactly the planned
`sNNN.xml` files; each file is read, hashed, sized, reparsed, and compared to
the success receipt's JUnit evidence fields and selected node count. Deleting,
replacing, or editing a JUnit XML file after shard execution prevents
`FULL_MATRIX_OK`.

When a runtime fixture is present, the frozen
`inputs/runtime_fixture_manifest.json` file is primary input evidence. Verify
rebuilds the canonical manifest from the frozen snapshot tree and rejects a
missing, malformed, non-regular, or mismatched manifest even when the receipt
fields still claim success.

TQ1-C7R delivery uses one complete-history Git bundle containing both the final
code ref and a parentless Delivery Evidence Capsule ref:
`refs/nollm-delivery/tq1-c7r/<final-code-head>`. The capsule carries the raw
final matrix plan, root marker, all receipts, all JUnit XML, frozen runtime
fixture evidence, gate logs, manifest, inventory, and `FULL_MATRIX_OK` output.
`verify-ref` must semantically replay those raw bytes rather than trusting only
the inventory: plan, root marker, receipt/JUnit exactness, runtime fixture
bytes, final `--all` log, verify log, summary, and manifest must all derive to
the same final code head and execution contract.

The protocol does not change Nollm production behavior and does not introduce runtime, OpenClaw, network, LLM/NLP, database, cache, daemon, global discovery, or automatic admission behavior.
