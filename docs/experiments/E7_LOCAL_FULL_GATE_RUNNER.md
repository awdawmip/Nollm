# E7 Local Full Gate Runner

E7 is an internal local gate for project health checks.

It combines package hygiene, the all-dream-checks manifest, and optional
`python run_tests.py` execution into one deterministic JSON report.

Run from `reference/python`:

```bash
python scripts/run_nollm_local_gate.py --skip-pytest
python scripts/run_nollm_local_gate.py --include-pytest
```

E7 is not a stable V1 recall/tool surface. It does not write cards, confirm
placement, create anchors, or change recall behavior.

The full gate exits non-zero if any included required component fails.
