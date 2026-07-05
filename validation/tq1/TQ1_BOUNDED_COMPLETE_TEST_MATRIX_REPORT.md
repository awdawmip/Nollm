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

## Resumption Discipline

TQ1 correctly stopped twice before final closure:

- The initial complete matrix exposed the DG0 adapters-to-field dependency
  firewall violation in DG6 snapshot compaction.
- The TQ1-C1 resumed matrix then exposed that DX1's sealed implementation
  witness was freezing the whole future `adapters/` namespace instead of the
  exact DI1 baseline adapter files.

Neither stop is reported as `FULL_MATRIX_OK`. DX1-C1 resumes from a new final
HEAD with fresh collection, fresh receipts, isolated worktrees, and verifier
coverage. Old `da886e...` and `fd088...` receipts are not reused for closure.
