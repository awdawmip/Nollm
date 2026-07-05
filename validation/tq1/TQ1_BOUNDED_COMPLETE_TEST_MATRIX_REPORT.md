# TQ1 Bounded Complete Test Matrix Report

TQ1 adds a bounded complete pytest matrix runner and external delivery directory convention.

Validated behavior:

- Real pytest collection is the manifest source.
- Node ids are assigned exactly once to deterministic shards.
- Shards run in detached git worktrees.
- Receipts record status, fingerprints, selected node ids, JUnit counts, stdout/stderr tails, timeout state, and cleanup state.
- Verify rejects source drift, collection drift, missing or stale receipts, timeout receipts, malformed receipts, duplicate/missing node ids, JUnit mismatches, and worktree leftovers.
- Runtime receipts and worktrees are outside the repository.

Validation results are recorded in the delivery response for the final TQ1 commit.
