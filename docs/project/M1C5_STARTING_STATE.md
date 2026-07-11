# M1C5 Starting State

Input bundle: `nollm_m1c4_single_owner_kernel_public_contract_final_closure_20260711_2142eba6.bundle`; SHA-256 `cbce4fb42bd3118deb1083d814d6265f9156a73e38c5987fb746ffe66a1eb9b2`; HEAD `2142eba63c0e65c5fce0a097affdf3733a2a81ed`; clean worktree. M1C4 package counts: Core 34, Snapshot 5, Trace 1, Access 32; M0 18; architecture/hygiene 8; parity 9/9; production violations/cycles 0/0. External Linux audit: 109 passed, 1 skipped; two zstandard historical tests unavailable.

Preserved reproductions: occupied_cells calls a missing CellStore method; same-thread mutation succeeds during a consistent-read token; failed Access rollback can erase a successful direct Core write; Core and Access close can release leases during blocked operations; public Store and held CellStore bypass runtime truth; Recall accepts noncanonical tuples; CompilerMetadata accepts non-string flags and unbounded quasi residual; reentrant Trace mutation can return success then disappear.
