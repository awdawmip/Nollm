# E4 One-Command Dream Geometry Suite

E4 provides one internal command for running the current Dream Geometry
experiment stack.

It exists because many integration issues are only visible after running E1,
E2, and E3 together.

Run from `reference/python`:

```bash
python scripts/run_dream_geometry_suite.py --repo-root ../.. --output ../../examples/openclaw_dream/dream_suite_report.json
```

Generated artifact:

```text
examples/openclaw_dream/dream_suite_report.json
```

`ok=true` means the E1 pipeline, E2 batch invariants, and E3 adversarial
regression pack are internally coherent for the committed fixtures.

`ok=true` does not mean placement is stable, memory is confirmed, or recall uses
Dream Geometry.

E4 is not a stable V1 recall/tool surface. It does not write cards, confirm
memory, create anchors, or expose a new external command.
