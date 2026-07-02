# RC1 DF1 to DR1 RecallUniverse Contract

DF1 exposes two immutable, in-memory derived views from the same explicit finite
admission set.

## Snapshot View

`FiniteFieldSnapshot.coarse_covers` is the DG2 local field view. Its
`CoarseCover.support_cell` remains the local `CellRef` emitted by DG2 cover
construction, with `chart_fingerprint` stored on the cover.

## Recall View

`RecallUniverse.covers` is the DR1 executable view. Each cover keeps the same
cover identity, support ids, support keys, axes, mass, policy, state, and
eligibility fields, but its `support_cell` is rebound to the concrete `HexCell`
from the same DF1 replay trace set.

The binding must satisfy:

```text
universe_cover.cover_id == snapshot_cover.cover_id
universe_cover.support_cell.cell_ref == snapshot_cover.support_cell
universe_cover.support_cell.chart_fingerprint == snapshot_cover.chart_fingerprint
```

DF1 must fail closed if a recall cover cannot bind to one of its own support
trace cells. It must not rebuild geometry, guess cells, persist a field, or
return a partial universe.

RC1 does not change DR1 policy, DG2 cover semantics, or FieldSnapshot
fingerprints.
