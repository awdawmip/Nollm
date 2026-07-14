# V3.8 Single-Entry Cross-Layer Recall Gate 5 Report

Date: 2026-07-15
Input checkpoint: `f71e449578c10fe96b3a730b03104dd863d8a9a4`

## Fixture

- Profile: `default_dream_v1`.
- One explicit Recall entry at physical layer 2.
- One target at physical layer 3 selected from a positive runtime
  `coverage_down` overlap member.
- One deliberately incorrect layer-3 target outside the overlap support.
- No Bridge and no lateral substitute are required.
- Budget: one step, layer delta one, beam 32.

## Result

- With coverage disabled, only the entry statement was returned.
- With `coverage_down` enabled, the cross-layer target was returned.
- The returned target path was exactly `("coverage_down",)`.
- The incorrect target was never returned.
- Core path was passed through Access without reconstruction.
- The Surface/OpenClaw candidate envelope exposed path as
  `["coverage_down"]` and explicitly marked `path_is_not_truth_proof=true`.
- Reopening the workspace produced the same target and path.
- The production request remained a single-entry request; no multi-entry or
  per-entry compatibility envelope was added.
- Core + Access + OpenClaw formation-loop regression: 165 passed.

External JUnit evidence:
`C:\Users\chaos\nollm_v38_gate5_single_entry_recall.xml`

SHA-256: `f08625569442533fdb290b23ac9cee435137eb92bd386b31418b0b3ca83543dc`
