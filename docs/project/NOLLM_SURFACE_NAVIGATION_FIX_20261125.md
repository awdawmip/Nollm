# Observed Surface choices across pages

Date: 2026-11-25. The independent reader run used fixed runtime
`a30dafca126b2b533ee86868cab10d1bc7e5e51a` and exposed two navigation problems:
selecting a candidate after its page had been left failed, and an oversized
`--page-size 16` printed a traceback without documenting the existing limit.

An encounter now remembers the native page cursor and candidate IDs it actually
displayed, only until a physical entrance is selected. A Host can select an
earlier observed candidate after continuing to another page. The runtime
reopens its original native page and checks the ID against live geometry; it
does not accept an unobserved ID or a removed candidate. The extra page read
increments the encounter's current cumulative call count. Reopening an earlier
page cannot reset an exhausted budget. Coarser Surface pages and final physical
menus follow the same rule. Once an entrance is chosen, the single-entry
constraint remains in force and temporary page history is discarded.

The encounter and walk CLIs now describe and parse menu widths from 1 through 8.
Invalid widths fail before opening a field or writing a cursor. Read-only
encounter `ValueError` messages use ordinary CLI errors instead of stack traces.
The width limit, physical geometry and stored field content have not changed.

## Executed checks

Seven new behavior tests were run before and after the fix. The corrected
baseline fixture produced two passes, one failure and four errors; all seven
passed after the change. They cover previous-page selection, unseen IDs,
removed candidates, cumulative-budget exhaustion, coarse descent, physical
menus, CLI help and invalid-width zero-write behavior.

Twenty-two existing project-encounter, stored-Surface, local-observation-cost and
installed coverage tests also passed. The new suite ran in 0.819 seconds and
the existing tests in 8.428 seconds in this environment. This is **29 distinct
focused tests**, separate from the earlier deployment and recovery validation.

The two actual failed previous-page selections were then replayed on the same
frozen 14-entry field copy: both changed from exit 1 to successful native
localities, with cumulative `surface_calls=4` after two displayed pages and the
reopened-page selection. The oversized-width case now exits 2 with a clear
1–8 range and no traceback. All field files remained byte-for-byte unchanged.
Process times of the three corrected calls were approximately 0.236–0.249
seconds; these are CLI timings, not end-to-end model costs or speed comparisons.

The [machine-readable result](../../lab/nollm-lab/repository_memory/results/surface_navigation_fix_20261125.json)
records the before/after checks. Original reader answers and failures remain
unchanged. This follow-up is a targeted regression check, not a repeated blind
trial. A pre-upgrade cursor has no history for pages it never recorded; a fresh
encounter is needed to observe those pages under the new behavior.
