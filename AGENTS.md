# Nollm V3.8 Active Execution Rules

## Authority

- Read `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md` first.
- Current architecture: `docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_8_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_20260714.md`.
- Current route: `docs/project/NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md`.
- Current task: `docs/project/tasks/NOLLM_C_A_O_L_D_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_RESIDUAL_ENTRY_AND_P1_CLOSURE_TASK_20260715.md`.
- `66684dc5` is an IN_PROGRESS checkpoint. Do not preserve its large-coordinate Coverage, physical-residual, final-entry, governance, or P1 completion claims.
- A taskbook may describe only this task's delta. It cannot redefine the architecture.

## Hard physical contract

- Adjacent physical-layer rotation is exactly 22.5 degrees.
- `theta(L) = L * 22.5 degrees mod 60 degrees`.
- `beta = 2^(1/4)` and adjacent-layer density ratio is `sqrt(2)`.
- Increasing physical layer index means finer cells.
- Physical Memory Layer and Aggregation Order are separate identity domains.
- A Surface address is derived and cannot be used for physical mutation.

## Reuse before rebuild

Before editing geometry code, inspect and classify these existing assets:

```text
reference/python/nollm/dream_geometry/geometry/**
reference/python/tests/fixtures/gvr1/**
reference/python/tests/fixtures/gra1/**
reference/python/tests/fixtures/grc1/**
reference/python/tests/fixtures/gkd1/**
reference/python/tests/fixtures/gpr1/**
validation/gvr1/**
validation/gra1/**
validation/grc1/**
validation/gkd1/**
validation/gpr1/**
```

- Do not create a new world-transform, polygon-overlap, Coverage-distribution, translation-variation, or bidirectional-Coverage implementation until `NOLLM_REUSABLE_GEOMETRY_ASSET_INVENTORY_20260714.md` is completed and committed.
- Reuse the historical pure-geometry implementation as one independent Oracle.
- Port code only after recording its source path, source commit, current SHA-256, owner, adaptation, and tests.
- Do not copy old relation indexes, runtime state, Evidence, Field, Recall, or product code into Core.

## Independent mathematics Gate

- A compiler and a validator must not call the same overlap implementation as their only proof.
- Use at least two independent Oracles.
- Validate non-origin cells, negative coordinates, all eight rotation phases, both Coverage directions, and bounded layer gaps.
- A phase-only or origin-only weight table cannot represent translation-varying Coverage.
- Zero false negatives above the declared overlap threshold are mandatory.
- Zero positive-weight propagation to geometrically zero-overlap targets is mandatory.
- Weight and residual errors must have explicit numeric bounds.
- Default Coverage computes overlap in a source-centered or residue-centered local frame; large absolute world coordinates must not be clipped directly.
- Raw partition mass is validated before Q16 conversion. Q16 normalization cannot hide invalid physical mass.
- Physical residual distinguishes candidate-window, threshold, numeric ambiguity, unsupported span, and quantization components.
- Synthetic `SurfaceOrderInfo` is allowed for selector unit tests, not for physical capability claims.
- Do not start OpenClaw Live until the independent mathematics Gate passes.

## Runtime truth before optimization

- The first correct runtime may use deterministic Decimal, rational, interval, or integer fixed-point polygon overlap.
- “No polygon at runtime” is not a hard rule.
- Static phase templates may be used only for legacy profiles, candidate envelopes, precomputed constants, or after translation-covariant certification.
- Any cache must be derived, versioned, deletable, and incapable of changing correctness.
- Do not reintroduce graph/vector/embedding, Topic/Source/Entity routes, Python semantic placement, Cursor, recent entry, or fact-to-entry maps.

## Surface and Recall

- Surface aggregation must use all certified nonzero-overlap members, not nearest-cell rounding.
- Once per traversal, OpenClaw selects exactly one final physical entry.
- When an Order 0 Surface cell contains multiple physical candidates, the Host must explicitly select one displayed operation-local physical candidate; stable-key fallback is forbidden.
- The final Recall fixture must require a real CoverageUp or CoverageDown step; a lateral-only pass is insufficient.
- Natural multi-entry reachability is optional observation only. Never create `select_entries`, `selected_entries_limit`, or per-entry fanout.

## Documentation and status

- Commit the full architecture book, route book, taskbook, status, ledger, and this `AGENTS.md`; do not replace them with summaries.
- Mark requirements as `INVARIANT`, `PHYSICAL_CONTRACT`, `POLICY`, `BUDGET`, `OBSERVATION`, `HYPOTHESIS`, or `LIMITATION`.
- Do not use `exact`, `certified`, `canonical`, `100%`, `complete`, or `validated` beyond the evidence.
- Update the expected vector at each Gate. If a module deviates by more than 5%, update task scope and status.
- Real progress must be committed. An incomplete result still requires a clean tree and one full-history Git bundle.
- Windows-first. Use PowerShell commands in the delivery report.
