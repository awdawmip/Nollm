# V2L0 Fixed Gate Receipt

## Scope

This receipt records the fixed V2L0-C3 validation gate definition.

## Engineering RC Focused Integrity Gate

```powershell
python -m pytest -q `
  reference/python/tests/test_engineering_rc_artifact_hashes.py `
  reference/python/tests/test_engineering_rc_export.py `
  reference/python/tests/test_engineering_rc_archive.py `
  reference/python/tests/test_engineering_rc_final_smoke.py
```

The raw result is recorded externally for final evidence. If the sealed packager
cannot accept an additional log slot, this receipt records the focused gate as a
required C3 external delivery audit artifact.

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
