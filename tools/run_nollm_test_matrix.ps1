param(
  [string]$RepoRoot = (Get-Location).Path,
  [int]$TargetNodeCount = 120,
  [int]$MaxShards = 24,
  [int]$Workers = 4,
  [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = Join-Path $RepoRoot "reference/python"

$head = git -C $RepoRoot rev-parse HEAD
$receiptRoot = "C:\Users\chaos\nollm_test_runs\$head\tq1-c6"
$worktreeRoot = "C:\Users\chaos\nollm_test_worktrees\$head"

New-Item -ItemType Directory -Force "C:\Users\chaos" | Out-Null
New-Item -ItemType Directory -Force "C:\Users\chaos\nollm_test_runs" | Out-Null
New-Item -ItemType Directory -Force "C:\Users\chaos\nollm_test_worktrees" | Out-Null

python reference/python/scripts/run_nollm_test_matrix.py plan `
  --repo-root $RepoRoot `
  --receipt-root $receiptRoot `
  --target-node-count $TargetNodeCount `
  --max-shards $MaxShards

python reference/python/scripts/run_nollm_test_matrix.py run-shard `
  --repo-root $RepoRoot `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot `
  --all `
  --workers $Workers `
  --timeout-seconds $TimeoutSeconds

python reference/python/scripts/run_nollm_test_matrix.py verify `
  --repo-root $RepoRoot `
  --receipt-root $receiptRoot `
  --worktree-root $worktreeRoot
