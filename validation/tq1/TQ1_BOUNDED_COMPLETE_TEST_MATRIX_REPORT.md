# TQ1 Bounded Complete Test Matrix Report

TQ1 adds a bounded complete pytest matrix runner and external delivery directory convention.

Validated behavior:

- Real pytest collection is the manifest source.
- Node ids are assigned exactly once to deterministic shards.
- Plan rejects dirty source status before collection or receipt-root creation.
- Ignored `out/nollm_runtime`, when present, is snapshotted once under the receipt root and bound by manifest and tree fingerprints.
- Shards run in matrix-owned detached git worktrees and copy only the plan-owned runtime fixture snapshot.
- Receipts record status, fingerprints, selected node ids, exact JUnit proof fields, stdout/stderr tails, timeout state, runtime fixture fingerprints, ownership state, and cleanup state.
- Verify rejects source drift, collection drift, runtime snapshot drift, missing or stale receipts, timeout receipts, malformed receipts, duplicate/missing node ids, exact JUnit mismatches, unowned worktrees, and worktree leftovers.
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

## TQ1-C2 Input And Worktree Closure

TQ1-C2 closes the remaining matrix-proof gaps:

- A complete matrix plan is valid only from a clean tracked source checkout.
- Tracked source files are not mirrored into shard worktrees.
- Ignored runtime fixture input is frozen once at plan time under the external receipt root.
- Every shard receipt binds to the runtime fixture state and fingerprints from the plan.
- Pre-existing worktrees at planned shard paths are rejected with a structured receipt and are not deleted.
- Cleanup is limited to matrix-owned worktrees under a matching marker.

The final TQ1-C2 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c2`; earlier C1 receipts are
not final closure evidence.
