# GPR1 Geometry Profile / Parameter-Regime Delivery Receipt

- baseline commit: `5e5110a0b1c4f08e9b5cce1b4864f7d403a35cee`
- branch: `codex/gpr1-geometry-profile-regime-validation`
- implementation commit: recorded in final delivery response
- delivery head: recorded in final delivery response
- bundle filename: `nollm_gpr1_geometry_profile_regime_validation_20260703.bundle`

## Scope

GPR1 adds validation-only fixture, tests, runner, baseline report, scope,
protocol, delivery receipt, and roadmap status. It does not modify
`reference/python/nollm/**` production implementation.

## Fixed Acceptance Commands

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q reference/python/tests/test_gpr1_geometry_profile_regime.py reference/python/tests/test_gpr1_geometry_profile_report_regeneration.py reference/python/tests/test_dg1_hex_coordinates.py reference/python/tests/test_dg1_local_charts.py reference/python/tests/test_dg1_polygon_overlap.py reference/python/tests/test_dg1_coverage_kernels.py reference/python/tests/test_dg1_chart_transforms.py reference/python/tests/test_dg1_anti_resonance_metrics.py reference/python/tests/test_dg1_partition_discipline.py reference/python/tests/test_dg1_purity_and_dependencies.py reference/python/tests/test_dg2_field_boundaries.py reference/python/tests/test_dg2_gravity_snapshot.py
PYTHONDONTWRITEBYTECODE=1 python validation/gpr1/run_gpr1_geometry_profile_regime.py --output docs/validation/GPR1_GEOMETRY_PROFILE_REGIME_BASELINE_REPORT.md
PYTHONDONTWRITEBYTECODE=1 python reference/python/scripts/check_package_hygiene.py
git diff --check 5e5110a0b1c4f08e9b5cce1b4864f7d403a35cee..HEAD
```

Actual command results are reported in the final delivery response after the
delivery head is committed and the worktree is clean.

## Report Regeneration

The committed report is deterministic for the fixed finite window. The report
regeneration test compares the full report content without normalizing a runtime
head field because the report records only the GPR1 baseline commit.

## Known Limits

The source axial disk radius is 0 for fixed-window speed and reproducibility.
This is sufficient for GPR1's parameter-regime diagnostic contract, but it is
not a global coverage proof or production profile selection.

Final bundle SHA-256 is not recorded here because the bundle and final response
are the authoritative non-self-referential delivery witness.
