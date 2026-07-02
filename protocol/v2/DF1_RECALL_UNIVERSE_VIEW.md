# DF1 Recall Universe View

DF1 derives a DR1-compatible `RecallUniverse` from a valid
`FiniteFieldSnapshot`.

The universe view contains current accepted DC1 proposal records, replay-derived
trace and cover surfaces, directed DG1 coverage distributions, verified chart
links, and an internal DG2 gravity snapshot. It does not contain Query, budget
resolution, Public Recall Envelope, host runtime state, mutable state, or
durable storage.

DF1 validates the view with DR1 `validate_recall_universe` and does not call
`resolve_recall`.

The view normalizes replayed trace basis references only at the read boundary so
DR1 can bind the trace back to the exact accepted DC1 proposal step. The
underlying `FiniteFieldSnapshot` retains the original DA1 replayed trace values
and admission provenance.

For cross-chart PlacementPlan bindings, the universe view carries the verified
forward chart link and the corresponding reverse read-link needed for
`K_down` validation. This does not create a new durable transform record.
