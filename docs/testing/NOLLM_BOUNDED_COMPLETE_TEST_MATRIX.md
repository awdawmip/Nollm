# Nollm Bounded Complete Test Matrix

TQ1 defines the complete test gate for Nollm delivery work.

The matrix is a coverage verifier, not a curated quick profile. It starts from real `pytest --collect-only -q` output, records every collected node id, assigns every node id to exactly one shard, runs each shard in a detached git worktree, and verifies the receipts against a fresh collection for the same commit.

`reference/python/run_tests.py` remains a legacy single-process diagnostic command. It is useful for local smoke triage, but a timeout from that command is not a full-suite pass or fail by itself. From TQ1 onward, only `run_nollm_test_matrix.py verify` may be used as the complete matrix gate.

## Commands

From the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"

$head = git rev-parse HEAD
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$head"
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

Shard worktrees are external runtime artifacts under:

```text
C:\Users\chaos\nollm_test_worktrees\<git-commit>\
```

The source repository must remain clean. The matrix runner does not use `git reset --hard` or `git clean` to hide pollution.

## Verification Rules

Verification fails if:

- current HEAD differs from the plan HEAD;
- source working tree status differs from the plan baseline;
- fresh collection fingerprint differs from the plan;
- any collected node id is missing or duplicated;
- any shard receipt is missing, stale, timed out, malformed, failed, or has a JUnit count mismatch;
- shard worktree cleanup failed.

The matrix is not Nollm recall, runtime, storage, OpenClaw, network, LLM/NLP, embedding, daemon, cache, database, or automatic admission infrastructure.

## Delivery Bundle Convention

For Nollm delivery bundles on the project owner's Windows workspace, create the final complete-history `.bundle` outside the repository at:

```text
C:\Users\chaos\<bundle-name>.bundle
```

Do not place delivery bundles inside the repository or under repo/out.
