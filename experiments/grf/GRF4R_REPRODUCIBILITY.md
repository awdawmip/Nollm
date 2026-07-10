# GRF4R Reproducibility Package

From the repository root on Windows PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python;$PWD"

python experiments/grf/run_grf4r_readiness.py
python experiments/grf/run_grf4r_reality_benchmark.py
python -m pytest -q -p no:cacheprovider reference/python/tests/grf
python -m pytest -q -p no:cacheprovider reference/python/tests/test_no_forbidden_features.py reference/python/tests/test_architecture_language.py reference/python/tests/test_repository_hygiene.py
git diff --check
```

The scale command always runs 100,000, 500,000, and 1,000,000 records. It does
not accept a formula-only or manually supplied result path. Expected readiness
status is `GRF_READY_FOR_NEXT_STAGE`.
