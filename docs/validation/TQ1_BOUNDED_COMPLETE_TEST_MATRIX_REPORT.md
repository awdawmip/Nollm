# TQ1 Bounded Complete Test Matrix Report

TQ1 adds a bounded complete pytest matrix runner and external delivery directory convention.

Validated behavior:

- Real pytest collection is the manifest source.
- Node ids are assigned exactly once to deterministic shards.
- Plan rejects dirty source status before collection or receipt-root creation.
- Ignored `out/nollm_runtime`, when present, is snapshotted once under the receipt root and bound by manifest and tree fingerprints.
- Shards run in matrix-owned detached git worktrees and copy only the plan-owned runtime fixture snapshot.
- Each copied runtime fixture target is re-hashed inside the detached worktree before pytest starts.
- Receipts record status, fingerprints, selected node ids, actual JUnit proof fields, stdout/stderr tails, timeout state, runtime fixture fingerprints, copied-target fingerprints, ownership state, and cleanup state.
- Verify rejects source drift, collection drift, runtime snapshot drift, missing or stale receipts, timeout receipts, malformed receipts, duplicate/missing node ids, exact actual-JUnit testcase proof mismatches, unowned worktrees, unattested fixture copies, and worktree leftovers.
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

## RCH1 Canonical RC Artifact Bytes

RCH1 preserves the TQ1-C2 clean-source, plan-owned fixture, and owned-worktree
rules. It does not restore tracked source byte mirroring.

The TQ1-C2 detached matrix exposed that the Engineering RC hash manifest had
recorded host checkout CRLF bytes for
`docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md` instead of the
committed LF release content. RCH1 changes RC manifest and archive handling to
canonical release bytes for governed text artifacts: CRLF is normalized to LF,
bare CR is rejected, archive entries are written with the same canonical bytes,
and substantive content changes still change size and hash.

The final RCH1/TQ1-C2 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c2-rch1`; earlier C2 stopped
receipts are not final closure evidence.

## TQ1-C3 Receipt Truthfulness And Ownership Closure

TQ1-C3 closes the remaining complete-matrix proof gaps:

- Passed receipts bind `junit_tests` and `junit_reported_tests` to the actual JUnit `<testcase>` proof count and reject malformed suite `tests` attributes.
- A successful shard requires return code 0, no timeout, and actual JUnit count equal to the selected node id count.
- Fixture copy, pytest startup, malformed JUnit, fixture drift, and fixture target mismatch leave structured failed receipts instead of missing receipt evidence.
- Every shard worktree has an exact per-shard ownership marker; cleanup preflights every existing shard path and refuses with zero deletions on missing, malformed, mismatched, or unplanned paths.
- Every shard receipt records copied runtime fixture target fingerprints and `fixture_copy_verified=true` only after the copied target matches the plan-owned snapshot.

The final TQ1-C3 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c3`; earlier C2/RCH1 receipts
are not final closure evidence.

## TQ1-C4 Failure Atomicity And Evidence Closure

TQ1-C4 closes the final matrix-proof semantics:

- Receipt roots are non-reusable matrix instances; `plan` refuses an existing root and never overwrites prior evidence.
- Shard receipts separate `worktree_add_succeeded`, `worktree_marker_written`, and `worktree_created_by_this_call`.
- Every defined operational failure records `failure_stage`, `reason`, shard identity, git head, worktree path, and cleanup state.
- Cleanup failure, cleanup refusal, or cleanup `OSError` cannot produce a passed receipt.
- Cleanup binds the receipt-root marker, worktree-root marker, and exact per-shard marker before deletion.
- Final matrix evidence remains external under `C:\Users\chaos\nollm_test_runs` and is not copied into Git or the delivery bundle.

The final TQ1-C4 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c4`; earlier C3 receipts are
not final closure evidence.

## TQ1-C5 Malformed JUnit And Receipt Inventory Closure

TQ1-C5 closes the final receipt-proof semantics:

- JUnit structural failures, including missing or illegal suite `tests`
  attributes, missing testcase structure, XML parse errors, Unicode errors, and
  JUnit read errors, produce failed shard receipts with
  `reason=junit_missing_or_malformed` and `failure_stage=junit_parse`.
- Plain operational failures are mapped by active stage; `worktree_add`
  failures use `worktree_add_failed` and cannot be reported as
  `pytest_start_failed`.
- Passed receipts must match the receipt schema, planned shard identity,
  selected nodes, fingerprints, JUnit count, runtime fixture attestations,
  worktree ownership flags, removed cleanup state, and null failure fields.
- `verify` rejects any missing planned receipt, extra receipt JSON, non-JSON
  file, directory, symlink, or special entry under `receipts/` before reading
  receipt contents.
- `FULL_MATRIX_OK` is printed only after exact receipt inventory succeeds and
  includes `receipt_json_count=<planned-shard-count>`.

The final TQ1-C5 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c5`; earlier C4 receipts are
not final closure evidence.

## TQ1-C6 JUnit, Frozen Input, And Single-Bundle Evidence Closure

TQ1-C6 closes the final evidence transport and raw-proof semantics:

- Successful receipts bind the exact `junit/<shard>.xml` relative path,
  SHA-256, size, reparsed testcase count, schema, shard identity, fingerprints,
  runtime fixture attestations, worktree ownership, removed cleanup state, and
  null failure fields.
- `verify` rejects missing, extra, malformed, edited, or unbound JUnit XML
  before `FULL_MATRIX_OK`; raw JUnit files are primary proof, not disposable
  logs or receipt-only summaries.
- When a runtime fixture is present, `verify` reparses
  `inputs/runtime_fixture_manifest.json` and proves it equals the canonical
  manifest regenerated from the frozen snapshot tree.
- The final successful output includes both `receipt_json_count` and
  `junit_xml_count`.
- `package_nollm_tq1_delivery_evidence.py` creates a parentless Delivery
  Evidence Capsule ref at `refs/nollm-delivery/tq1-c6/<final-code-head>` using
  a temporary Git index, without changing the code branch or source index.
- The final TQ1-C6 delivery is a single complete-history Git bundle containing
  the code ref and the evidence ref; the capsule contains raw matrix plan,
  root marker, all receipts, all JUnit XML, frozen fixture evidence, gate logs,
  manifests, inventories, and true `FULL_MATRIX_OK` output.

The final TQ1-C6 matrix must use fresh receipts under
`C:\Users\chaos\nollm_test_runs\<final-head>\tq1-c6`; earlier C5 receipts are
not final closure evidence.
