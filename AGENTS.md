# Nollm V3.9 Broad Calibration And Dense Locality Rules

## Authority

- Read `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md` first.
- Active architecture amendment: `docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md`.
- Active route: `docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md`.
- Current task: `docs/project/tasks/NOLLM_C_A_O_L_D_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_RECALL_TASK_20260715.md`.
- `5a45384` is the input checkpoint. Preserve its physical/Surface address separation, single-entry Wire, source-centered Oracle and P1 evidence, but do not preserve Decimal polygon Coverage as the production path.

## Hard physical contract

- Adjacent physical-layer rotation increment is 22.5 degrees.
- `theta(L) = L * 22.5 degrees mod 60 degrees`.
- `beta = 2^(1/4)`; adjacent-layer density ratio is `sqrt(2)`.
- Increasing physical layer index means finer cells.
- Physical Memory Layer and Aggregation Order are separate identity domains.
- Coverage approximation may not alter these constants.

## Approximation contract

- Production Coverage is a bounded structural approximation, not exact physical area measurement.
- Exact polygon/Decimal code belongs in Lab/Oracle and must not run per Surface cell in the chat path.
- Default production method: deterministic equal-area hex quadrature with fixed-point transforms and nearest target-cell assignment.
- A residue atlas may be added only as a derived acceleration of the same quadrature contract.
- Approximation quality is measured by weighted mass errors and total variation, not exact support equality.
- Default Gate targets:
  - `missed_mass_p99 <= 0.02`
  - `false_mass_p99 <= 0.02`
  - `total_variation_p95 <= 0.05`
  - `partition_mass_error == 0` after integer normalization
  - `max_fanout <= 8`
  - no target outside the certified local radius
  - dominant-target agreement >= 0.95
- Small support differences below the declared relation threshold are allowed.
- Approximation policy must be selected from broad, deterministic, exact-Oracle calibration rather than a hand-picked fixture set.
- The storage/transport radius and active writable radius are separate contracts. Writes must remain closed under configured Recall Coverage depth.

## Reuse before rebuild

- Reuse the historical chart/hex/polygon/Coverage assets as Lab Oracle and benchmark inputs.
- Do not copy product, relation-index, Field, Recall or Evidence code from legacy paths into Core.
- Record provenance for any ported math routine.

## Operational domain

- Mathematical coordinates remain conceptually unbounded.
- Active product profile uses `max(|q|,|r|,|q+r|) <= 2^31-1`.
- Do not spend the active task on signed-64 closure, arbitrary-precision Wire or all-plane exact certification.
- Node/JSON integer transport must reject values outside the active domain.

## Surface and Recall

- Surface Orders are computed lazily, finest to coarser, stopping at the first order satisfying budget.
- `page()` and descent may not rebuild all Orders.
- Cache only derived address/residue Coverage and Surface pages; caches must be deletable.
- One traversal selects one final physical entry.
- Natural reachability from multiple entries is an observation, not an invariant or persisted fact-to-entry mapping.
- No `select_entries`, Cursor, Topic/Source route, graph/vector/embedding or Python semantic placement.
- Current Placement policy remains physical layer 0; no Stitch or multi-layer semantic Placement in this task.

## Gate discipline

- Gate 1 calibrates approximate Coverage against exact Oracle on bounded fixtures.
- Gate 2 replaces production Decimal/polygon Coverage.
- Gate 3 implements lazy Surface and proves the small-field runtime target.
- Only then run OpenClaw regression/P1.
- Incomplete work must still be committed with clean tree and one full-history Bundle.
- Update architecture, route, status, ledger, task report and final Manifest in Git.
- Do not describe a capability as sealed, permanently complete, or permanently 100 percent complete.
