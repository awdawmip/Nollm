# Nollm Engineering Gravity RC Export Manifest

Date: 2026-06-18

This manifest lists the files an external reviewer should read first for the
G-series engineering gravity release candidate. It is an export guide, not a
new protocol surface.

## Read First

- `NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md`
- `docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md`
- `docs/engineering/NOLLM_MINIMUM_DATA_MODEL_20260616.md`
- `docs/experiments/NOLLM_MINIMAL_ABLATION_EXPERIMENT_PLAN_20260616.md`
- `docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md`
- `docs/geometry/NOLLM_PARAMETER_PROFILE_REGISTRY.md`
- `docs/geometry/G3_MULTI_STEP_COVERAGE_METRICS.md`
- `docs/experiments/G_SERIES_ENGINEERING_CLOSURE.md`
- `docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_FREEZE_20260618.md`
- `docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md`
- `docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md`
- `protocol/GRAVITY_WELL.md`
- `protocol/GRAVITY_MARK.md`
- `protocol/DRIFT_REPORT.md`
- `protocol/RETURN_VECTOR.md`

## Implementation Modules

- `reference/python/nollm/geometry.py`
- `reference/python/nollm/geometry_profiles.py`
- `reference/python/nollm/multi_step_coverage.py`
- `reference/python/nollm/offset_sampling.py`
- `reference/python/nollm/reverse_cover.py`
- `reference/python/nollm/gravity.py`
- `reference/python/nollm/mode3_trace_experiment.py`
- `reference/python/nollm/minimal_ablation_experiment.py`
- `reference/python/nollm/g_series_engineering_closure.py`

## Tests

- `reference/python/tests/test_geometry.py`
- `reference/python/tests/test_geometry_profiles.py`
- `reference/python/tests/test_multi_step_coverage.py`
- `reference/python/tests/test_offset_sampling.py`
- `reference/python/tests/test_reverse_cover.py`
- `reference/python/tests/test_gravity.py`
- `reference/python/tests/test_mode3_trace_experiment.py`
- `reference/python/tests/test_minimal_ablation_experiment.py`
- `reference/python/tests/test_g_series_engineering_closure.py`

## Runtime Reports

- `out/nollm_runtime/g_series_engineering_closure_report.json`
- `out/nollm_runtime/minimal_ablation_experiment_report.json`
- `out/nollm_runtime/mode3_trace_experiment_report.json`
- `out/nollm_runtime/gravity_report_demo.json`
- `out/nollm_runtime/multi_step_coverage_report.json`
- `out/nollm_runtime/offset_sampling_report.json`
- `out/nollm_runtime/reverse_cover_report.json`

These reports are derived artifacts. They are not source of truth, not memory,
and not a hidden recall index.

## Hash Integrity

- `docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json`

Verify artifact identity from `reference/python`:

```bash
python scripts/check_engineering_rc_export.py
```

Refresh hashes only after an intentional release artifact change:

```bash
python scripts/check_engineering_rc_export.py --write-hashes
```

The hash manifest verifies artifact identity, not scientific validity.

## Deterministic Archive

Build and verify a local zip archive from `reference/python`:

```bash
python scripts/build_engineering_rc_export_archive.py --output ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip --report ../../out/nollm_runtime/engineering_rc_archive_report.json
python scripts/build_engineering_rc_export_archive.py --verify ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip
```

The generated archive is a local release artifact and should not be committed.
