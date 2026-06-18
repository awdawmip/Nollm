# Nollm Engineering Gravity RC Evaluation Guide

Date: 2026-06-18

This guide is for external evaluation of the G-series engineering gravity
scaffold. It is not a product recall API and not proof of long-term memory.

## What To Test

- Whether gravity reports reduce misuse of far-drift content.
- Whether lateral discoveries become visible.
- Whether return vectors help re-center.
- Whether the B profile is more stable in finite-depth scale scan.
- Whether the A profile is more robust under offset noise.

## Ablation Conditions

```text
N0: Vector RAG only
N1: Vector RAG + geometry mark only
N2: Vector RAG + gravity report
N3: Vector RAG + gravity report + return vector
N4: medium_practical profile, sqrt(2) / 15 deg
N5: default_dream profile, 2^(1/4) / 22.5 deg
```

## Success Criteria

- Gravity reports improve judgment.
- Over-drift is more visible.
- Useful lateral discovery is visible.
- Return vector improves re-centering.
- B/A profile differences remain measurable.

## Failure Criteria

- Gravity reports are unused decoration.
- Geometry mark adds no value beyond embedding similarity.
- Free drift mainly increases hallucination risk.
- Implementation cost exceeds measurable benefit.

## Warnings

```text
Do not treat the RC scaffold as a product recall API.
Do not use drift_class as trust/status.
Do not auto-write drifted recall into persistent memory.
```

The evaluator should judge whether the scaffold improves model-side recall
judgment, not whether it replaces retrieval, validation, operator approval, or
Nollm Core's deterministic filesystem protocol.

## Command Smoke

Run these smoke commands from the repository root. They are release/audit
checks only and do not run heavy report regeneration.

```bash
cd reference/python
python scripts/check_engineering_rc_export.py
python scripts/check_engineering_rc_export.py --write-hashes
python scripts/build_engineering_rc_export_archive.py --output ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip --report ../../out/nollm_runtime/engineering_rc_archive_report.json
python scripts/build_engineering_rc_export_archive.py --verify ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip
python scripts/run_nollm_test_shards.py --list-profiles
python scripts/run_nollm_test_shards.py --profile shard_smoke --timeout 20
python scripts/run_nollm_test_shards.py --profile core --timeout 60
python scripts/run_nollm_test_shards.py --profile docs --timeout 60
python scripts/run_nollm_local_gate.py --skip-pytest
python scripts/run_g_series_engineering_gate.py
python scripts/run_dream_golden_regression.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_export.py tests/test_g_series_engineering_closure.py tests/test_minimal_ablation_experiment.py tests/test_mode3_trace_experiment.py tests/test_gravity.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_artifact_hashes.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_archive.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_nollm_test_shards.py
```

The hash manifest verifies artifact identity, not scientific validity.

## Build Deterministic Export Archive

Run from `reference/python`:

```bash
python scripts/check_engineering_rc_export.py
python scripts/build_engineering_rc_export_archive.py --output ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip --report ../../out/nollm_runtime/engineering_rc_archive_report.json
python scripts/build_engineering_rc_export_archive.py --verify ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip
```

The generated archive is a local release artifact and should not be committed.

Test shard profiles are documented in
`docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_TEST_SHARDS_20260619.md`.
