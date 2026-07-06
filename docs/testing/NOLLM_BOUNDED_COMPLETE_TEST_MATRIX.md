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
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$head\tq1-c7r"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$head"

python reference/python/scripts/run_nollm_test_matrix.py plan --repo-root . --receipt-root $receiptRoot --target-node-count 120 --max-shards 24 --planned-shard-timeout-seconds 3600
python reference/python/scripts/run_nollm_test_matrix.py run-shard --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot --all --workers 4 --timeout-seconds 3600
python reference/python/scripts/run_nollm_test_matrix.py verify --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot
```

When a host command timeout is possible for diagnostics, list shards and run them one command at a time. This is not the final C7R delivery path:

```powershell
python reference/python/scripts/run_nollm_test_matrix.py list-shards --receipt-root $receiptRoot
python reference/python/scripts/run_nollm_test_matrix.py run-shard --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot --shard s001 --timeout-seconds 3600
python reference/python/scripts/run_nollm_test_matrix.py verify --repo-root . --receipt-root $receiptRoot --worktree-root $worktreeRoot
```

## Receipts

Receipts and JUnit XML are external runtime artifacts under:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\
```

For final TQ1-C7R delivery evidence, use:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\tq1-c7r\
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
The plan records an immutable execution contract. For C7R final delivery this
contract is `planned_shard_timeout_seconds=3600.0`,
`retry_policy=forbidden`, `receipt_overwrite=forbidden`, and
`execution_mode=single_pass`. The final run must use exactly one
`run-shard --all --workers 4 --timeout-seconds 3600` invocation for that root.

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
- the execution contract is missing, malformed, or a success receipt timeout does not match the planned timeout;
- the `receipts/` directory inventory is not exactly the planned shard JSON set;
- any collected node id is missing or duplicated;
- the `junit/` directory inventory is not exactly the planned shard XML set;
- any shard receipt is missing, stale, timed out, malformed, failed, has a schema or shard identity mismatch, or has an exact selected-count/JUnit mismatch against the actual JUnit `<testcase>` proof count while requiring suite `tests` attributes to be parseable integers;
- a successful receipt's JUnit relative path, size, SHA-256, or reparsed testcase count does not match the raw `junit/<shard>.xml` file;
- a present runtime fixture manifest is missing, malformed, non-regular, or does not match the frozen snapshot tree;
- a shard worktree was not created by the current call or lacks the exact per-shard marker;
- the copied runtime fixture target is not attested against the plan snapshot;
- shard worktree cleanup failed;
- matrix-owned worktree leftovers remain.

`FULL_MATRIX_OK` is emitted only after this exact inventory and receipt-content
proof succeeds. Its output includes `receipt_json_count=<planned-shard-count>`
and `junit_xml_count=<planned-shard-count>`, plus the planned timeout and
single-pass policy fields.

The matrix is not Nollm recall, runtime, storage, OpenClaw, network, LLM/NLP, embedding, daemon, cache, database, or automatic admission infrastructure.

Operational matrix receipt roots, JUnit XML, logs, and runtime fixture
manifests are generated outside the repository. For TQ1-C7R delivery, those raw
evidence bytes are copied into a parentless Delivery Evidence Capsule Git ref
inside the single final complete-history bundle; they are not committed to the
code branch. Capsule `verify-ref` semantically replays the plan, root marker,
receipt/JUnit inventory, runtime fixture manifest and bytes, final run log,
FULL_MATRIX_OK output, final evidence summary, and capsule manifest.

## Delivery Bundle Convention

For Nollm TQ1-C7R delivery on the project owner's Windows workspace, create one
complete-history `.bundle` outside the repository at:

```text
C:\Users\chaos\nollm_tq1_c7r_canonical_evidence_one_hour_contract_final_closure_20260706_<short-head>.bundle
```

The bundle must include the code branch and
`refs/nollm-delivery/tq1-c7r/<final-code-head>`. Do not place delivery bundles
inside the repository or under repo/out.
