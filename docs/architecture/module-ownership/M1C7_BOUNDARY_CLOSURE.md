# M1C7 Boundary Closure

This closure changes executable behavior rather than ownership labels. Core owns its lifecycle coordinator, workspace owner, client leases, transaction capabilities, callback fence, consistent-read token ownership, canonical current state, and bounded Recall. Access owns its lifecycle/pair coordinator, Evidence/Binding callbacks, explicit decisions, and cross-store rollback through the Core public capability contract.

Snapshot remains a consumer of the Core consistent-state port. Trace remains an optional observer implementation; Core only owns the Trace contract and guarded invocation. Store and Trace implementations were not moved into Access or Core incorrectly. Legacy GRF, OpenClaw, adapters, and Lab remain outside Bare/Minimal production paths.

The implementation adds no relation index, semantic fallback, graph, vector, embedding, database, cache, or new durable state. `M1C7_BOUNDARY_REPORT.json` is generated from actual imports and must retain `production_violations=[]` and `cycles_production=[]`.
