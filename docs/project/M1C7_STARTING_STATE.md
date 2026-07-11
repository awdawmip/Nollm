# M1C7 Starting State

## Input Evidence

- Bundle: `nollm_m1c6_reentrancy_safe_lifecycle_trace_isolation_reuse_consistency_20260711_c1fc0dc4.bundle`
- SHA-256: `bfd88ab2622277a9d69dc77bed1fef73c7a9397bee6e6710d507caa133f0ea5a`
- Input branch: `codex/m1c6-reentrancy-safe-lifecycle-trace-isolation-reuse-consistency`
- Input HEAD: `c1fc0dc41cae2e43c109d8da3b809d322765e526`
- New clone: `C:\Users\chaos\nollm_m1c7_work`
- Work branch: `codex/m1c7-callback-fence-client-lease-consistent-read-ownership`

`Get-FileHash`, `git bundle verify`, and `git bundle list-heads` matched the taskbook. The bundle contains complete history. The input and new-clone worktrees were clean. `git fsck --no-reflogs --connectivity-only` exited 0 and reported only dangling objects carried by the complete bundle.

M1-C6 input gates: Manifest 1440/1440; production violations 0; production cycles 0; Core 44; Snapshot 5; Trace 1; Access 39; M0 18; architecture/forbidden/hygiene 8; geometry parity 9/9; M1 E2E and adversarial matrix passed. `zstandard` was available in the Windows environment during the preceding full run, which produced GRF 112 passed.

## Reproduction Command

The seven issues were reproduced before production edits with one bounded inline Python program under explicit package-only `PYTHONPATH`:

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"
@'<deterministic callback/thread reproduction>'@ | python -
```

## Actual Reproduction Output

```json
{"b1_binding_exists_after_rollback":false,"b1_core_contains_after_rollback":false,"b1_nested_apply_returned":true,"b1_placement_count":0,"b2_core_contains_after_rollback":false,"b2_direct_put_returned":true,"b3_nested_recall_atom":"a","b3_nested_recall_fallback_error":"binding_missing","b3_nested_recall_statement_id":"","b4_errors":["RuntimeError: cannot release un-acquired lock","close=RuntimeError: cannot close during an active Core operation","second_end=ValueError: invalid consistent-read token"],"b5_constructed":true,"b5_constructed_core_open":false,"b6_later_put_error":"OSError: trace hook","b6_public_store":true,"b7_access_only_closed_bool":true,"b7_core_only_closed_bool":true}
```

## Thread And Callback Order

1. Binding callback nested `Access.apply(B)` returned a Handle; outer A then failed and restored both snapshots. B disappeared from Core and Binding and placement count became zero.
2. Binding callback direct `core.put(B)` returned a Handle; outer rollback deleted B.
3. Binding callback nested `Access.recall` observed A after Core write but before Binding commit, returning `binding_missing` with empty statement identity.
4. Thread B accepted Thread A's token far enough to clear `_read_token`, then failed to release A's RLock. A could neither close nor end again.
5. A test Core blocked after constructor's temporary transaction lease exited. Another thread closed Core, then Access construction returned with `core.is_open=false`.
6. Trace on `core.recall.begin` assigned `core.store.before_replace`; the next put raised the installed `OSError`.
7. Static behavior confirmed both runtimes had only `_closed` booleans and no CLOSING linearization state.

All reproductions were same-process, deterministic, bounded, file-local, and used no model, OpenClaw, network, database, cache, corpus, or relation index.
