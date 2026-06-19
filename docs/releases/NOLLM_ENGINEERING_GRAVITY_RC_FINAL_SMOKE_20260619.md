# Nollm Engineering Gravity RC Final Smoke

Date: 2026-06-19

The final smoke gate is a release-audit wrapper for the Engineering Gravity RC.
It exists so an external evaluator can run one stable command:

```bash
cd reference/python
python scripts/run_engineering_rc_final_smoke.py
```

The gate checks local release health: local gate without pytest, golden
regression, G-series closure, export/hash validation, package hygiene, archive
build and verification, shard profile listing, `shard_smoke`, a selected
plugin-isolated pytest suite, and clean git status.

It intentionally does not run full pytest, heavy G-series regeneration, real
LLM calls, memory writeback, automatic anchor creation, or new experiments.

Optional forms:

```bash
python scripts/run_engineering_rc_final_smoke.py --report ../../out/nollm_runtime/engineering_rc_final_smoke_report.json
python scripts/run_engineering_rc_final_smoke.py --no-archive-build
python scripts/run_engineering_rc_final_smoke.py --verbose
```

The generated report is a runtime artifact under `out/nollm_runtime/`.
The RC remains an experimental scaffold, not a proven long-term memory system.
