# DG1.1 Core Mathematical Repair Delivery Receipt

## Identity

- task id: DG1.1 core mathematical repair
- branch: `feature/dg1-01-core-mathematical-repair`
- base SHA: `97c27ef92686ceb04eebda97d27e79a295a0cbcc`
- final SHA: the commit containing this receipt; exact object id is self-referential and is verified after commit by `git rev-parse HEAD` and bundle `list-heads`.
- commit subject: `DG1.1: repair core geometry validation`

## Changed Files

- `docs/delivery/DG1_01_CORE_MATHEMATICAL_REPAIR_DELIVERY_RECEIPT.md`
- `docs/geometry/DG1_GEOMETRY_CONVENTIONS.md`
- `docs/validation/DG1_PURE_GEOMETRY_BASELINE_REPORT.md`
- `reference/python/nollm/dream_geometry/geometry/__init__.py`
- `reference/python/nollm/dream_geometry/geometry/chart.py`
- `reference/python/nollm/dream_geometry/geometry/coverage.py`
- `reference/python/nollm/dream_geometry/geometry/transform.py`
- `reference/python/nollm/dream_geometry/geometry/types.py`
- `reference/python/nollm/dream_geometry/validation/dg1_baseline_report.py`
- `reference/python/tests/test_dg1_anti_resonance_metrics.py`
- `reference/python/tests/test_dg1_chart_transforms.py`
- `reference/python/tests/test_dg1_coverage_kernels.py`

## Repair Summary

- Rejected zero-scale and non-finite similarity transforms.
- Rejected two-pair fits where the source pair or target pair is degenerate.
- Required verified transforms to have at least three distinct, non-collinear source and target witnesses.
- Required cycle verification to check both witness residuals and the composed transform identity errors `|a - 1|` and `|b| / reference_scale`.
- Added immutable chart geometry fingerprints to hex cells and required a target partition to share one fingerprint.
- Added `relative_phase(source_chart, target_chart)` and changed report phase recurrence to scan `phase(layer0 <- layer)` instead of echoing local phase input.

## Boundary Statement

DG1.1 only repairs pure geometry math under the allowed DG1 paths. It does not modify V1, OpenClaw, plugin, sidecar, runtime, native memory, CLI, JSON tool, Field, Cortex, Recall, Adapter, DG0.2 firewall, external dependencies, or true memory. No numpy, scipy, shapely, or other third-party dependency was added.

The only subprocess/CLI operations used were local verification, report generation, Git, and bundle commands for delivery.

## Test Evidence

### Regression Tests Added First

New DG1.1 tests initially failed against the DG1 implementation:

```text
test_dg1_chart_transforms.py: 6 failed, 11 passed
test_dg1_coverage_kernels.py: 2 failed, 10 passed
test_dg1_anti_resonance_metrics.py: ImportError for missing relative_phase
```

### DG1 Directed Tests

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg1_hex_coordinates.py tests/test_dg1_local_charts.py tests/test_dg1_polygon_overlap.py tests/test_dg1_chart_transforms.py tests/test_dg1_coverage_kernels.py tests/test_dg1_partition_discipline.py tests/test_dg1_anti_resonance_metrics.py tests/test_dg1_purity_and_dependencies.py
```

Result:

```text
71 passed in 3.89s
```

### DG0 Regression And Firewall

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg0_v2_module_boundaries.py tests/test_dg0_v2_protocol_contracts.py tests/test_dg0_v2_dependency_firewall.py
```

Result:

```text
19 passed in 5.67s
```

### Baseline Report

Command:

```powershell
cd reference/python
python3 -m nollm.dream_geometry.validation.dg1_baseline_report --output ..\..\docs\validation\DG1_PURE_GEOMETRY_BASELINE_REPORT.md
```

Result:

```text
exit code 0
report written to docs/validation/DG1_PURE_GEOMETRY_BASELINE_REPORT.md
```

Report observations:

```text
Baseline B keeps rotation recurrence modulo 60 degrees at gap 8 and gap 16.
Relative phase recurrence now reports phase(layer0 <- layer) and is not globally constant across all A-E/gap/phase samples.
No final beta/theta/phase parameter is selected.
```

### Package Hygiene

Command:

```powershell
cd reference/python
python3 scripts/check_package_hygiene.py ../..
```

Result:

```text
PASS package hygiene
```

### Full Suite

Command:

```powershell
cd reference/python
python3 run_tests.py
```

Result:

```text
975 passed, 183 subtests passed in 320.68s (0:05:20)
```

## Push And Bundle Evidence

These values are finalized after the commit exists and are recorded in the final delivery response.

Planned push command:

```powershell
git push -u origin feature/dg1-01-core-mathematical-repair
```

Planned bundle commands:

```powershell
git bundle create ../nollm_dg1_01_core_mathematical_repair_20260629.bundle HEAD
git bundle verify ../nollm_dg1_01_core_mathematical_repair_20260629.bundle
git bundle list-heads ../nollm_dg1_01_core_mathematical_repair_20260629.bundle
```

Bundle path:

```text
C:\Users\chaos\nollm_dg1_01_core_mathematical_repair_20260629.bundle
```

## Non-Blocking Risks Recorded

- R-DG1-01: DG0 dependency firewall is not a malicious Python sandbox.
- R-DG1-02: float64 clipping and tolerance boundaries remain approximate.
- R-DG1-03: complete baseline report generation remains comparatively slow.
- R-DG1-04: DG1.1 does not select final beta/theta/phase.
- R-DG1-05: DG1.1 does not prove a global atlas.
- R-DG1-06: DG1.1 does not implement Field Dynamics, Query Probe, runtime recall, or memory behavior.

## Conclusion

DG1.1 repairs the listed core mathematical blockers in the pure geometry kernel and keeps DG1 scoped to deterministic geometry validation only.
