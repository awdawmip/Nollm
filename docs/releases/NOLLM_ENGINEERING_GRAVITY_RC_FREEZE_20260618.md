# Nollm Engineering Gravity RC Freeze

Date: 2026-06-18

Freeze baseline commit: `b544a47`

This release-candidate freeze closes the G-series engineering scaffold. It does
not claim that Nollm is proven. It states that G0-G9b are now a closed
engineering experiment scaffold, and that the next phase should run external
evaluations rather than add more internal metaphors.

## G-Series Status

- G0: V4 engineering gravity decision docs.
- G1: strict true-tiling kernel hardening.
- G2: parameter profile registry.
- G3: multi-step coverage metrics.
- G4: offset sampling metrics.
- G5/G5b: reverse-cover MILP and nontrivial cluster pack.
- G6: Gravity Report V1 data model and generator.
- G7: Mode 3 free-drift trace experiment.
- G8: minimal ablation experiment scaffold.
- G9/G9b: closure gate and fast runtime hardening.

## Verified Fast Path

Run from `reference/python`:

```bash
python scripts/run_nollm_local_gate.py --skip-pytest
python scripts/run_dream_golden_regression.py
python scripts/run_g_series_engineering_gate.py
python scripts/run_nollm_test_shards.py --profile collect --timeout 30
python scripts/run_nollm_test_shards.py --profile core --timeout 60
python scripts/run_nollm_test_shards.py --profile docs --timeout 60
```

Expected result: each command completes successfully; the G-series engineering
gate writes `out/nollm_runtime/g_series_engineering_closure_report.json` with
`ok=true`.

Heavy report regeneration is explicit opt-in only:

```bash
python scripts/run_g_series_engineering_gate.py --generate
```

The default closure gate reads existing runtime reports and does not regenerate
the nontrivial reverse-cover MILP report.

## Failure-Oriented Interpretation

Nollm is worth continuing only if gravity reports improve recall judgment in
external evaluation. If gravity reports are unused decoration, the approach
should be reconsidered.

G-series proves that Nollm's engineering hypothesis can now be tested, not that
the hypothesis is true.

## Forbidden Semantics Checklist

Expected false:

- stable recall surface
- hard drift rejection
- auto writeback
- anchor creation
- parent-child geometry
- trust/status mapping from drift class
