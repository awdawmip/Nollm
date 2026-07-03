# GAT1 Chart Groupoid Delivery Receipt

## Scope

GAT1 implements finite chart-atlas transition / groupoid synthetic validation for sealed baseline B.

- input baseline: `ffe76e4ed574209e05ef3f8e35440aa50c0cd234`
- branch: `codex/gat1-c1-report-reproducibility-closure`
- implementation commit: `f2ea194fe4338eb067f568011c6b8978ab57d584`
- closure: GAT1-C1 report reproducibility
- bundle name: `nollm_gat1_c1_report_reproducibility_closure_20260703.bundle`
- status: implemented; final acceptance pending

## Implemented Assets

- `reference/python/tests/fixtures/gat1/fixture.py`
- `reference/python/tests/test_gat1_chart_groupoid.py`
- `reference/python/tests/test_gat1_report_regeneration.py`
- `validation/gat1/run_gat1_chart_groupoid.py`
- `docs/validation/GAT1_CHART_GROUPOID_BASELINE_REPORT.md`
- `docs/validation/GAT1_CHART_GROUPOID_SCOPE.md`
- `protocol/v2/GAT1_CHART_GROUPOID_VALIDATION.md`
- `ROADMAP.md`

## GAT1-C1 Closure

GAT1-C1 adds `GAT1_REPORTING_NOISE_FLOOR = 1e-12` and a deterministic report renderer. Diagnostics at or below the reporting floor are displayed as `≤1.000000e-12`; values above it remain rendered as concrete scientific-notation values. This does not change raw DG1 transform calculations, GAT1 validation states, or acceptance thresholds.

## Boundary

GAT1 does not modify `reference/python/nollm/**`, GPR1 sealed validation assets, GVR1 sealed validation assets, DG1/DG2 production implementation, memory, capture, admission, assembly, recall, adapters, runtime, OpenClaw, network, database, cache, LLM, NLP, embedding, or semantic search behavior.

## Verification

Final verification must be run at the delivery head with a clean worktree. Bundle SHA-256 is recorded in the external delivery response after the final delivery commit is bundled.
