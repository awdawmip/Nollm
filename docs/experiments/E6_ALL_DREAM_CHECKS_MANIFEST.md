# E6 All Dream Checks Manifest

E6 is an internal experiment/regression manifest.

It combines E4 one-command suite output and E5 real-corpus dry-run output into a
compact deterministic gate.

E6 does not write cards, confirm placement, create anchors, or expose a stable
recall/tool surface.

The manifest gates forbidden tree, folder, and anchor-ownership semantics. If a
required report disappears, becomes invalid, or reports a forbidden semantic
flag, the manifest is not ok.

Run from `reference/python`:

```bash
python scripts/run_all_dream_geometry_checks.py
```

Generated artifact:

```text
examples/openclaw_dream/all_dream_checks_manifest.json
```
