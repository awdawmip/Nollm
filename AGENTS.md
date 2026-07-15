# Nollm V3.9 Legal Traversal And Live Closure Rules

## Authority

- Read `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md` first.
- Active architecture amendment: `docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md`.
- Active route: `docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md`.
- Current task: `docs/project/tasks/NOLLM_C_A_O_L_D_WRITE_POLICY_LEGAL_TRAVERSAL_P1_DENSE_LIVE_CLOSURE_TASK_20260715.md`.
- `2e779764` is the input checkpoint. Preserve its calibrated Coverage, safe-field proof, dense Surface, single-entry Recall, failed P1 Statement, and live evidence.

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

## Active write and traversal policy

- Core storage validity and Access/OpenClaw active semantic write policy are different contracts.
- Active semantic Placement remains `default_dream_v1/default/layer0/phase=null` and active writable radius only.
- Surface prompts must be generated from state-derived `legal_actions`; never advertise impossible actions.
- Invalid model navigation is recoverable only through a bounded operation-local correction loop with zero state mutation.
- Mechanical singleton physical-entry resolution is allowed only when the total visible candidate universe contains exactly one entry; otherwise the LLM selects one visible candidate.
- Existing failed P1 Statement/Evidence must be reused when valid; do not create duplicate facts merely to retry Placement.
- Provider latency and model failures must be reported separately from Surface/Core timing.
- No Stitch, multi-layer semantic Placement, Cursor, semantic route, graph/vector/embedding, exact polygon production path, or persistent traversal state.
- Final delivery commit must be included in the ownership manifest before bundle creation.

## Gate discipline

- Gate 1 calibrates approximate Coverage against exact Oracle on bounded fixtures.
- Gate 2 replaces production Decimal/polygon Coverage.
- Gate 3 implements lazy Surface and proves the small-field runtime target.
- Only then run OpenClaw regression/P1.
- Incomplete work must still be committed with clean tree and one full-history Bundle.
- Update architecture, route, status, ledger, task report and final Manifest in Git.
- Do not describe a capability as sealed, permanently complete, or permanently 100 percent complete.
