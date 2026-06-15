# E2 Batch Dream Experiments

E2 is internal experiment infrastructure for Dream Geometry.

It runs multiple tiny fixtures to expose integration problems across the D-series
records. It produces deterministic batch reports with invariant checks.

E2 does not write cards, confirm memories, make placement stable or
authoritative, create anchors automatically, or expose a stable V1 tool surface.

The invariant checks reject tree, folder, and anchor-ownership regressions such
as parent fields, children fields, owner anchors, or belongs-to-anchor fields.

Run from the repository root:

```bash
python reference/python/scripts/run_dream_experiment_batch.py
```
