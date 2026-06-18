# Nollm Engineering Gravity RC Audit

Date: 2026-06-18

Baseline commit: `97ab7452b824b19ca93673ccd9ea864f9551c812`

G0-G9b and H0 are closed as an engineering scaffold. This audit does not reopen
architecture decisions and does not add Nollm behavior.

The release-candidate claim is testable, not proven:

```text
We can test whether gravity reports help recall judgment.
We do not claim that Nollm has proven long-term memory.
```

## Fast Path

Run from `reference/python`:

```bash
python scripts/run_nollm_local_gate.py --skip-pytest
python scripts/run_dream_golden_regression.py
python scripts/run_g_series_engineering_gate.py
python scripts/run_nollm_test_shards.py --profile collect --timeout 30
python scripts/run_nollm_test_shards.py --profile core --timeout 60
python scripts/run_nollm_test_shards.py --profile docs --timeout 60
```

Expected result: all commands pass and the closure report remains `ok=true`.

## Optional Targeted Tests

```bash
python -m pytest -q tests/test_geometry.py tests/test_geometry_profiles.py tests/test_multi_step_coverage.py tests/test_offset_sampling.py tests/test_reverse_cover.py tests/test_gravity.py tests/test_mode3_trace_experiment.py tests/test_minimal_ablation_experiment.py tests/test_g_series_engineering_closure.py
```

## Expected Generated Reports

```text
out/nollm_runtime/g_series_engineering_closure_report.json
out/nollm_runtime/minimal_ablation_experiment_report.json
out/nollm_runtime/mode3_trace_report.json
out/nollm_runtime/gravity_report_demo.json
out/nollm_runtime/multi_step_coverage_report.json
out/nollm_runtime/offset_sampling_report.json
out/nollm_runtime/reverse_cover_milp_report.json
```

The current scaffold writes Mode 3 and reverse-cover reports as
`mode3_trace_experiment_report.json` and `reverse_cover_report.json`; the
manifest records the current implementation file names.

## Forbidden Semantics Checklist

Expected false:

```text
stable_recall_surface
hard_drift_rejection
auto_writeback
anchor_creation
parent_child_geometry
trust_status_mapping
```

These flags must remain false. `drift_class` is experimental report metadata
only; it must not become trust, status, approval, rejection, or writeback.
