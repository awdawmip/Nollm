# Active V3.7 Correction Rules

- Current active correction is V3.7 rotated physical field and single-entry Surface Recall.
- The default physical geometry is mandatory: delta theta is 22.5 degrees; theta(L) is L times 22.5 degrees modulo hexagonal 60-degree symmetry; beta is 2^(1/4); the physical cell-density ratio per increasing layer is beta squared, or sqrt(2).
- Increasing physical layer index means finer cells unless the active route explicitly changes the convention.
- Physical Memory Layer and Aggregation Order are different domains and must not share address identity.
- Surface Order must not be encoded by changing GeometryAddress.layer.
- Do not call a profile or template exact unless the target physical transform and overlap are certified.
- Do not validate adaptive coarsening only with synthetic SurfaceOrderInfo values.
- Surface occupied counts are dataset-dependent results; do not require monotonic decrease for every order or sparse fixture.
- One fact becoming reachable from multiple recall entries is an emergent dense-field result, not a required invariant.
- Active OpenClaw Recall selects one final entry per traversal. Do not compensate with select_entries or per-entry fanout.
- Preserve no-Cursor, no relation-index, real-LLM semantic selection, Windows-first, internal Gates, clean tree, and one full-history bundle.
- Do not restore graph/vector/embedding, Python semantic placement, Topic/Source/Entity routes, or persistent entry hints.
