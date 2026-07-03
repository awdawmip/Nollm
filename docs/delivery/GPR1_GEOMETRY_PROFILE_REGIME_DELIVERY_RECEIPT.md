# GPR1 Geometry Profile / Parameter-Regime Delivery Receipt

- baseline commit: `a0ffe4eed311ee9928804e79a31f246b3ab19c7e`
- branch: `codex/gpr1-c1-multilayer-coverage-diagnostic-closure`
- implementation commit: recorded in final delivery response
- delivery head: recorded in final delivery response
- bundle filename: `nollm_gpr1_c1_multilayer_coverage_diagnostic_closure_20260703.bundle`

## Scope

GPR1-C1 closes a validation evidence defect: the original GPR1 coverage metrics
declared layer range 0..16 but sampled only `base_layer = 0`. C1 makes coverage
sampling use every legal base layer for each gap while continuing to call sealed
DG1 public geometry APIs only. It does not modify `reference/python/nollm/**`
production implementation.

## Fixed Acceptance Commands

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q reference/python/tests/test_gpr1_geometry_profile_regime.py reference/python/tests/test_gpr1_geometry_profile_report_regeneration.py reference/python/tests/test_dg1_hex_coordinates.py reference/python/tests/test_dg1_local_charts.py reference/python/tests/test_dg1_polygon_overlap.py reference/python/tests/test_dg1_coverage_kernels.py reference/python/tests/test_dg1_chart_transforms.py reference/python/tests/test_dg1_anti_resonance_metrics.py reference/python/tests/test_dg1_partition_discipline.py reference/python/tests/test_dg1_purity_and_dependencies.py reference/python/tests/test_dg2_field_boundaries.py reference/python/tests/test_dg2_gravity_snapshot.py
PYTHONDONTWRITEBYTECODE=1 python validation/gpr1/run_gpr1_geometry_profile_regime.py --output docs/validation/GPR1_GEOMETRY_PROFILE_REGIME_BASELINE_REPORT.md
PYTHONDONTWRITEBYTECODE=1 python reference/python/scripts/check_package_hygiene.py
git diff --check a0ffe4eed311ee9928804e79a31f246b3ab19c7e..HEAD
git diff --name-only a0ffe4eed311ee9928804e79a31f246b3ab19c7e..HEAD -- reference/python/nollm
```

Actual command results are reported in the final delivery response after the
delivery head is committed and the worktree is clean.

## Report Regeneration

The committed report is deterministic for the fixed finite multilayer window.
The report regeneration test compares the full report content without
normalizing a runtime head field because the report records only the GPR1
baseline commit.

## Known Limits

The layer window remains finite at 0..16. Source axial disk radius remains 0,
so each legal base layer samples one axial source point; this is not spatial
full-domain coverage. Gap 16 has one legal base layer and remains a single-pair
degeneration. Metrics use DG1 float64 tolerance and do not select a production
profile.

Final bundle SHA-256 is not recorded here because the bundle and final response
are the authoritative non-self-referential delivery witness.
