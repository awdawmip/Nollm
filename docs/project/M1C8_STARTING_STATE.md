# M1C8 Starting State

## Input Evidence

- Bundle: `nollm_m1c7_callback_fence_client_lease_consistent_read_ownership_20260711_66a04f6d.bundle`
- SHA-256: `3F2D4EFF8532D296FFA4253DC6993367DD10A281F885C8E8CF6C17A2627F07DF`
- Input HEAD: `66a04f6db148eadd149ec3465ce4152ee780ddab`
- New clone: `C:\Users\chaos\nollm_m1c8_work`
- Work branch: `codex/m1c8-workspace-callback-bound-store-runtime-config`

`Get-FileHash`, `git bundle verify`, `git bundle list-heads`, input-commit identity, clean worktree, and `git fsck --no-reflogs --connectivity-only` were verified before edits. Fsck exited 0; complete-bundle dangling-object diagnostics were nonblocking.

## Executable Reproduction Command

The committed reproducer executes all B1-B8 attacks in separate temporary workspaces. It was run against a detached worktree of the unmodified input commit:

```powershell
$input = "C:\Users\chaos\nollm_m1c8_input_repro"
git worktree add --detach $input 66a04f6db148eadd149ec3465ce4152ee780ddab
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$input/packages/nollm-core/src",
  "$input/packages/nollm-snapshot/src",
  "$input/packages/nollm-access/src"
) -join ";"
python lab/nollm-lab/m1/reproduce_m1c8_input_blockers.py --source-root $input
```

The script contains the complete operations and derives every JSON field from input-code behavior or direct inspection of the input M1-C7 report. It does not hardcode the observed booleans.

## Actual Reproduction Output

```json
{"b1_capture_returned":true,"b1_count":0,"b1_evidence_exists":true,"b2_nested_binding_after_rollback":false,"b2_nested_callback_returned":true,"b2_unbounded_variant":"RecursionError followed by AccessConsistencyError","b3_a2_state":"CLOSING","b3_close_error":["RuntimeError: Core callback cannot enter client lease release"],"b3_repeated_close_variant":"second close waits indefinitely","b4_apply_error":"AccessConsistencyError: fatal consistency failure during Access rollback","b5_c1_count":0,"b5_c2_count":1,"b5_rebound":true,"b6_core_contains":false,"b6_saved_fake":true,"b7_original_diverged":true,"b7_redirect_exists":true,"b7_state_path_redirected":true,"b8_placeholder_present":true}
```

## Blocker Classification

1. A callback on A1 did not fence A2 bound to the same canonical pair.
2. Nested Binding work could return and then be erased by outer rollback; an unguarded variant recursed.
3. Cross-Access close entered `CLOSING` before Core rejected client-lease release.
4. Callback recursion could corrupt rollback and surface fatal consistency failure.
5. Reassigning `AccessRuntime.core` redirected real work away from the lease-bound Core.
6. Direct `FileHandleStore.put` created a dangling binding without a Core atom.
7. A retained `FileCoreStateStore` could redirect its path after Runtime binding.
8. M1-C7 Starting State contained a placeholder reproduction body and its report overclaimed callback coverage.

All executable attacks were same-process, bounded where threads were involved, and used no model, OpenClaw, network, database, cache, corpus, or relation index.
