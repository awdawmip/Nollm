# V2L0 Fixed Gate Receipt

## Scope

This receipt records the fixed V2L0-C3R validation gate definition.

## Engineering RC Focused Integrity Gate

```powershell
python -m pytest -q `
  reference/python/tests/test_engineering_rc_artifact_hashes.py `
  reference/python/tests/test_engineering_rc_export.py `
  reference/python/tests/test_engineering_rc_archive.py `
  reference/python/tests/test_engineering_rc_final_smoke.py
```

The C3R focused gate raw result is bound into the parentless evidence capsule at
`logs/02_rc_export_check.txt`. The slot name is sealed legacy layout metadata
and does not mean only the export checker ran.

Result summary:

```text
34 passed
```

Raw log SHA-256:

```text
5FD40850998F148E81E1687D15D35EEF78C1633EF42F390F751C5C60E9987657
```

## Gate

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
$env:PYTHONPATH="$PWD/reference/python"

python -m pytest -q `
  reference/python/tests/test_v2l0_layer_constitution.py `
  reference/python/tests/test_v2l0_source_reclassification.py `
  reference/python/tests/test_v1_route_lock.py `
  reference/python/tests/test_v1_docs_consistency.py `
  reference/python/tests/test_dg0_v2_module_boundaries.py `
  reference/python/tests/test_dg7_runtime_boundaries.py `
  reference/python/tests/test_geometry.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_terminology.py `
  reference/python/tests/test_repository_hygiene.py `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_package_hygiene_script.py `
  reference/python/tests/test_run_tests_runner.py
```

The command result is captured in delivery evidence after execution.

C3R result summary:

```text
83 passed, 24 subtests passed
```

C3R raw log SHA-256:

```text
034B790CF3AA4F8F8E8749E41076BAFCBE85B49C54DE43548FBAA3439BBF72AD
```

Capsule destination:

```text
logs/01_rc_gate_pytest.txt
```

## Public V2 Regression Gate

```powershell
python -m pytest -q `
  reference/python/tests/test_ci1_capture_ingress.py `
  reference/python/tests/test_ci1_capture_policy.py `
  reference/python/tests/test_ci1_capture_visibility.py `
  reference/python/tests/test_cx1_capture_deferred_visibility_validation.py `
  reference/python/tests/test_hcg1_file_first_capture_gateway.py `
  reference/python/tests/test_hcg1_capture_gateway_boundaries.py `
  reference/python/tests/test_hcg1_capture_gateway_cli.py `
  reference/python/tests/test_hx1_trusted_host_bridge.py `
  reference/python/tests/test_hx1_host_binding_preflight.py `
  reference/python/tests/test_hx1_staged_outcomes.py `
  reference/python/tests/test_hx1_receipt_regeneration.py `
  reference/python/tests/test_hx1_boundaries.py `
  reference/python/tests/test_hxa1_final_acceptance_audit.py
```

C3R result summary:

```text
109 passed
```

C3R raw log SHA-256:

```text
8307D0E457532817D86FE5A6282A6D2CAC29711DFA4FDCD65000CF264921FDA1
```

Capsule destination:

```text
logs/04_dx1_dg0_dg6_targeted_gate.txt
```

## TQ1 Helper Self-Test Slot

The C3R evidence capsule must bind a real helper self-test raw log to
`logs/03_tq1_self_tests.txt`; placeholders are not accepted.

```powershell
python -m pytest -q reference/python/tests/test_nollm_test_shards.py
```

C3R result summary:

```text
8 passed
```

C3R raw log SHA-256:

```text
3FB256C6B2BA14678E05F3445797A8BC1007CB58B3372254EFF7A98778789CE0
```

Capsule destination:

```text
logs/03_tq1_self_tests.txt
```

## Evidence Identity Notes

C3 code head `167c9663888a94185e8631e95f0b60f2d63ad09e` is not the final C3R
evidence head. Final branch truth is the final code head plus final evidence ref
plus `logs/00_environment_and_git_state.txt`. The capsule `code_branch` field is
inherited sealed TQ1 metadata and is non-authoritative for V2L0-C3R.

The C3 RC rebaseline remains exactly one historical manifest record:
`reference/python/tests/test_geometry.py`. Engineering RC remains historical
matrix input only. HAG1-C1R remains accepted / unpromoted.
