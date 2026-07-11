# M1C5 Boundary Closure

## Active Ownership

Core exclusively owns current-state writes, workspace owner leases, runtime operation/transaction locking, consistent-read tokens, canonical Recall, kernel metadata, and read-only occupancy queries. Store writes require a private Runtime capability and live cells are not exported. Access owns pair coordination, Evidence/Binding files, semantic decisions, and cross-store rollback while using the public Core transaction lease. Snapshot uses the Core consistent-state port; Trace remains an optional failure-isolated observer.

## Dependency Result

Production violations and production cycles remain zero. Core remains stdlib-only and never imports Access, Snapshot implementations, Trace implementations, or Legacy. Bare/Minimal do not route through retained GRF. GRF remains a Lab parity oracle only. The result is based on active imports and behavioral tests, not lifecycle suppression.
