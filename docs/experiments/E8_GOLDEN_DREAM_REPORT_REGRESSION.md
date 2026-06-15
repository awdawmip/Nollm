# E8 Golden Dream Report Regression

E8 is an internal regression guard for deterministic Dream Geometry reports.

It compares normalized current outputs from E4, E5, E6, and E7 against checked-in
golden snapshots. It exists to catch unexpected drift after future edits.

Compare mode:

```bash
python scripts/run_dream_golden_regression.py
```

Update mode:

```bash
python scripts/run_dream_golden_regression.py --update
```

Update mode intentionally refreshes golden snapshots. Compare mode exits
non-zero when current normalized output differs from the checked-in snapshots.

E8 is `experimental_internal_only`. It is not stable recall, not a stable tool
surface, does not write cards, does not confirm placements, and does not create
anchors.
