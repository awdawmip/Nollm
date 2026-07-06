# Nollm Bounded Complete Test Matrix

TQ1 defines the complete test gate for Nollm delivery work.

The matrix is a coverage verifier, not a curated quick profile. It starts from
a clean git commit, takes a plan-owned snapshot of any ignored
`out/nollm_runtime` fixture, records real `pytest --collect-only -q` output,
assigns every collected node id to exactly one shard, runs each shard in a
matrix-owned detached git worktree, and verifies the receipts against a fresh
collection for the same clean commit and the same frozen runtime fixture
snapshot.

`reference/python/run_tests.py` remains a legacy single-process diagnostic command. It is useful for local smoke triage, but a timeout from that command is not a full-suite pass or fail by itself. From TQ1 onward, only `run_nollm_test_matrix.py verify` may be used as the complete matrix gate.

## Commands

From the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"

$head = git rev-parse HEAD
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$head\tq1-c5"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$head"

python reference/python/scripts/run_nollm_test_matrix.py plan --repo-root . --receipt-root $receiptRoot --target-node-count 120 --max-shards 24
python reference/python/scripts/run_nollm_test_matrix.py run-shard --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot --all --workers 4 --timeout-seconds 90
python reference/python/scripts/run_nollm_test_matrix.py verify --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot
```

When a host command timeout is possible, list shards and run them one command at a time:

```powershell
python reference/python/scripts/run_nollm_test_matrix.py list-shards --receipt-root $receiptRoot
python reference/python/scripts/run_nollm_test_matrix.py run-shard --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot --shard s001 --timeout-seconds 90
python reference/python/scripts/run_nollm_test_matrix.py verify --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot
```

## Receipts

Receipts and JUnit XML are external runtime artifacts under:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\
```

For final TQ1-C5 delivery evidence, use:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\tq1-c5\
```

Shard worktrees are external runtime artifacts under:

```text
C:\Users\chaos\nollm_test_worktrees\<git-commit>\<matrix-id>\
```

The source repository must be clean before `plan`. Dirty tracked or untracked
source status is rejected before collection, receipt-root creation, and
worktree creation. The runner does not mirror tracked source bytes into shard
worktrees and does not use `git reset --hard` or `git clean` to hide pollution.
The receipt root is a single matrix-instance boundary: `plan` refuses any
existing receipt root and never deletes, overwrites, or adopts prior evidence.

If `out/nollm_runtime` exists, `plan` copies it once into
`<receipt-root>/inputs/runtime_fixture/` and records a canonical file manifest,
tree fingerprint, and manifest fingerprint. Shards copy only that plan-owned
snapshot, then immediately re-hash the copied target in the detached worktree.
Pytest starts only after the target manifest and tree fingerprints exactly
match the plan-owned snapshot. Later changes under source `out/nollm_runtime`
do not affect an already planned matrix. If the fixture is absent, the absent
state is recorded and verified.

Each shard worktree has its own ownership marker:

```text
<worktree-root>\<matrix-id>\<shard-id>\.nollm_test_matrix_worktree.json
```

Cleanup first verifies the receipt-root marker, worktree-root marker, and every
existing planned shard marker. Any missing, malformed, mismatched, or unplanned
worktree directory makes cleanup refuse with zero deletions. Cleanup failure is
never a successful shard receipt; a shard whose pytest/JUnit work succeeded but
whose cleanup failed is recorded as failed.

## Verification Rules

Verification fails if:

- current HEAD differs from the plan HEAD;
- source working tree status is not clean;
- fresh collection fingerprint differs from the plan;
- the plan-owned runtime fixture snapshot is missing or drifted;
- receipt-root or worktree-root markers do not match the plan;
- the `receipts/` directory inventory is not exactly the planned shard JSON set;
- any collected node id is missing or duplicated;
- any shard receipt is missing, stale, timed out, malformed, failed, has a schema or shard identity mismatch, or has an exact selected-count/JUnit mismatch against the actual JUnit `<testcase>` proof count while requiring suite `tests` attributes to be parseable integers;
- a shard worktree was not created by the current call or lacks the exact per-shard marker;
- the copied runtime fixture target is not attested against the plan snapshot;
- shard worktree cleanup failed;
- matrix-owned worktree leftovers remain.

`FULL_MATRIX_OK` is emitted only after this exact inventory and receipt-content
proof succeeds. Its output includes `receipt_json_count=<planned-shard-count>`.

The matrix is not Nollm recall, runtime, storage, OpenClaw, network, LLM/NLP, embedding, daemon, cache, database, or automatic admission infrastructure.

Final matrix receipt roots, JUnit XML, logs, and runtime fixture manifests are
external audit evidence. They must be preserved for review, not committed to
Git, copied into repo/out, or treated as bundle contents.

## Delivery Bundle Convention

For Nollm delivery bundles on the project owner's Windows workspace, create the final complete-history `.bundle` outside the repository at:

```text
C:\Users\chaos\<bundle-name>.bundle
```

Do not place delivery bundles inside the repository or under repo/out.
