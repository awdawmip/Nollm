# DG1.2 Phase Recurrence Correction Delivery Receipt

## Identity

- task id: DG1.2 phase recurrence correction
- branch: `feature/dg1-02-phase-recurrence-correction`
- base SHA: `0ff24c9c428d814e084db7ceba901c8da5ab5bd7`
- final SHA: the commit containing this receipt; exact object id is verified after commit by `git rev-parse HEAD` and bundle `list-heads`.
- commit subject: `DG1.2: correct relative phase recurrence`

## Changed Files

- `docs/delivery/DG1_02_PHASE_RECURRENCE_CORRECTION_DELIVERY_RECEIPT.md`
- `docs/geometry/DG1_GEOMETRY_CONVENTIONS.md`
- `docs/validation/DG1_PURE_GEOMETRY_BASELINE_REPORT.md`
- `reference/python/nollm/dream_geometry/geometry/schedules.py`
- `reference/python/nollm/dream_geometry/validation/dg1_baseline_report.py`
- `reference/python/tests/test_dg1_anti_resonance_metrics.py`

## Correction Summary

- Added immutable diagnostic layer phase policies:
  - `constant_local`: `p_layer = p_0`
  - `layer_drift_control`: `((q + layer/37) mod 1, (r + 2*layer/41) mod 1)`
- Corrected `_phase_score_for()` to compute fixed-gap pair-local relative phase:
  - `phase(chart(layer) <- chart(layer + gap))`
  - no fixed `chart_for_layer(0, ...)` source chart for all pairs.
- Updated the report with a separate `Relative Phase Recurrence Diagnostics` table.
- Kept rotation recurrence, relative phase recurrence, and coverage recurrence as distinct finite-window diagnostics.

## Boundary Statement

DG1.2 only changes phase recurrence diagnostics in the allowed DG1 paths. It does not modify transform, coverage, chart fingerprint, V1, OpenClaw, runtime, plugin, sidecar, native memory, CLI, JSON tool, Field, Cortex, Recall, Adapter, external dependencies, true memory, or agent behavior.

No final beta/theta/phase parameter is selected.

## Test Evidence

### Initial Failure Against DG1.1

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg1_anti_resonance_metrics.py
```

Result before implementation:

```text
ImportError: cannot import name 'LAYER_PHASE_POLICIES' from 'nollm.dream_geometry.geometry.schedules'
```

### DG1 Directed Tests

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg1_hex_coordinates.py tests/test_dg1_local_charts.py tests/test_dg1_polygon_overlap.py tests/test_dg1_chart_transforms.py tests/test_dg1_coverage_kernels.py tests/test_dg1_partition_discipline.py tests/test_dg1_anti_resonance_metrics.py tests/test_dg1_purity_and_dependencies.py
```

Result:

```text
74 passed in 3.55s
```

### DG0 Regression And Firewall

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg0_v2_module_boundaries.py tests/test_dg0_v2_protocol_contracts.py tests/test_dg0_v2_dependency_firewall.py
```

Result:

```text
19 passed in 5.53s
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
Relative phase recurrence diagnostics now use fixed-gap pair-local phase(layer <- layer + gap).
For baseline B and base phase (1/5, 2/5), constant_local scores are 1.0 for gaps 1, 2, 4, 8, and 16.
For the same B/base phase, layer_drift_control scores are 0.0 for gaps 1, 2, 4, 8, and 16.
Baseline B still reports rotation recurrence modulo 60 degrees at gap 8 and gap 16.
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
978 passed, 183 subtests passed in 343.11s (0:05:43)
```

## Push And Bundle Evidence

These values are finalized after the commit exists and are recorded in the final delivery response.

Planned push command:

```powershell
git push -u origin feature/dg1-02-phase-recurrence-correction
```

Planned bundle commands:

```powershell
git bundle create ../nollm_dg1_02_phase_recurrence_correction_20260629.bundle HEAD
git bundle verify ../nollm_dg1_02_phase_recurrence_correction_20260629.bundle
git bundle list-heads ../nollm_dg1_02_phase_recurrence_correction_20260629.bundle
```

Bundle path:

```text
C:\Users\chaos\nollm_dg1_02_phase_recurrence_correction_20260629.bundle
```

## Non-Blocking Risks Recorded

- DG1.2 does not choose final beta/theta/phase.
- DG1.2 does not prove a global atlas.
- DG1.2 does not implement Field Dynamics, Query Probe, runtime recall, OpenClaw, or memory behavior.
- float64 geometry remains tolerance-based.
- Full report generation remains comparatively slow because coverage metrics are still finite-window polygon scans.

## Conclusion

DG1.2 corrects the relative phase recurrence object to fixed-gap pair-local chart relations. DG1 status after this correction is: Accepted - Pure Geometry Kernel and finite-window validation baseline.
