# DX2 Multi-Admission Assembly-to-Recall Validation

DX2 validates explicit working-set boundaries across sealed V2 modules.

## Contract

The host supplies a finite set through BA1 receipt admission IDs. The validation
must not discover AdmissionRecords by scanning stores or directories. Each
AdmissionRecord is read directly and replayed through the sealed DA1 replay
validator before DF1 assembly.

## Acceptance Invariants

- Captured but unadmitted DreamShards are not formal geometric recall evidence.
- Admitted DreamShards outside the explicit finite set are not discovered.
- DR1 evidence items refer only to admitted DreamShards from the explicit set.
- DI1 returns a public read-only envelope and does not expose internal field,
  cover id, gravity, chart, placement, source trace, or debug records.
- Misses are scoped to the current explicit AdmissionRecord / FieldSnapshot,
  not to all captured material.
- Failure boundaries do not silently substitute captured or unrelated admitted
  controls.

## Current Sealed Constraint

The A/B finite assembly remains single-gravity-chart because sealed DF1 rejects
one snapshot spanning multiple gravity chart fingerprints. DX2 covers a real
VerifiedChartLink through D, an independently admitted cross-chart control that
is deliberately excluded from the explicit DF1 working set.
