# Active Project Basis

Current authority rebase: 2026-09-10.

The active development baseline is V3.14 native OpenClaw memory-slot integration,
merged through PR #2 (`6c4f93cef77bb2c03c98777015416843e5bbaf8d`) and the mainline
README at `91bd14ab394e87931b45baaaa87671f30fcfd706`. The V3.13 checkpoint below
is inherited provenance, not an instruction to restart PR #1 or restore its
custom tool as a competing integration.

The current user instruction authorizes building the new kernel and reconciling
branches: merge compatible validated work; cold-store unique incompatible work
without discarding its original commits. The execution branch is
`kernel/q40-phase-20260910`. Its changes are described below. Host packaging,
Windows Live, automatic capture/Formation migration and public ClawHub release
remain separate unclosed gates; this task does not declare them complete.

## Governing and inherited sources

- Highest principle: [NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md](../architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)
- Inherited architecture, subject to the V3.14 mainline and current kernel amendment: [V3.13 Rev1 Direct Encounter Activation](../architecture/NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md)
- Inherited route, not the current execution dispatch: [V3.13 Rev1 Direct Encounter Activation](NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md)
- Preserved previous task and Live restrictions: [A-O-L-D Direct Encounter Activation, Provider Live and GitHub Delivery](tasks/NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md)
- Content-neutral authority: [Memory Eligibility Decision](../architecture/NOLLM_CONTENT_NEUTRALITY_AND_MEMORY_ELIGIBILITY_DECISION_20260723.md)
- Current status: [NOLLM_CURRENT_STATUS.md](NOLLM_CURRENT_STATUS.md)
- Inherited module capability ledger: [NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md](NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md)
- Preserved V3.13 execution evidence, not a current V3.14 Live result: [V3_13_REV1_DIRECT_ACTIVATION_REPORT.md](V3_13_REV1_DIRECT_ACTIVATION_REPORT.md)
- Active repository asset policy: [NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md](NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md)
- Lifecycle authority: [ACTIVE_ASSET_LIFECYCLE_PLAN.json](../architecture/module-ownership/ACTIVE_ASSET_LIFECYCLE_PLAN.json)
- Boundary report: [MODULE_BOUNDARY_REPORT.json](../architecture/module-ownership/MODULE_BOUNDARY_REPORT.json)
- Preserved V3.12 capability record: [AOLD_UNIFIED_FIELD_ENCOUNTER_REPORT.md](AOLD_UNIFIED_FIELD_ENCOUNTER_REPORT.md)

## Current kernel amendment: parity-preserving Q40 phase factorization

Implementation: `packages/nollm-core/src/nollm_core/approximate_coverage.py`.
Regression gate: `packages/nollm-core/tests/test_translation_covariant_physical_coverage.py`.

The predecessor already used dynamic integer equal-area quadrature, not eight
fixed translation templates. This amendment factors that existing admitted
algorithm into a compiled sample stencil and a counted relative-phase footprint.
It does not replace the bounded approximate contract with exact-area geometry.

Let `S = 2**40`, and let `(cq, cr)` be the source center mapped by the existing
compiled Q40 transform. Use exact integer division:

```text
cq = 2*S*bq + pq,  0 <= pq < 2*S
cr = 2*S*br + pr,  0 <= pr < 2*S
anchor = (2*bq, 2*br)
footprint = counted_cube_rounding(direction, pq, pr, unchanged_sample_offsets)
targets = anchor + footprint
```

Half-to-even rounding is equivariant under even integer translations. All three
cube-coordinate errors and their tie ordering are therefore unchanged. A
one-cell quotient would lose integer parity at midpoint ties: cube rounding of
`(0.5,0.5)` is `(1,0)`, while `(1.5,1.5)` is `(1,2)`, not `(2,1)`.
The two-cell carrier preserves this repair coordinate.

The retained information is direction, both exact residuals and every sample's
integer multiplicity. The permitted future observations are target coordinates,
hit counts, thresholds, stable sorting, Q16 normalization and storage checks.
Absolute anchors are restored before storage-boundary validation. Physical
layers and source identities are not needed in the cached relative footprint;
semantic data never enter it.

All 96 samples, their original compiled constants, target ordering, Q16 weights,
policy identifiers, coordinate bounds, failure behavior and canonical state
identity remain unchanged. The implementation identity is
`parity_preserving_q40_phase_kernel_v1`; geometric registry identity is not
changed because this is an output-preserving implementation replacement.

Caches are bounded and disposable: two directional compiled stencils, 8192
relative footprints, the existing 8192 full expansions and one source stencil.
The public cache-clear operation empties all four. Rebuilding them must reproduce
the same result. No persistent source-to-entry or semantic routing index is added.

## Validation and mathematical scope

Five additional tests independently reconstruct the admitted integer quadrature,
cover every physical layer, frozen large-coordinate populations, negative
coordinates, storage failures, midpoint parity, layer-shared footprints and
cache deletion/rebuild. Existing tests remain intact. The independent reference
does not call production centroid, sample-stencil or rounding routines.

A finite regression run alone is not a universal proof. The exact implementation
equivalence also follows from the even-translation identity above and the fact
that the transformed sample offsets do not depend on the source address.
Full repository/package admission checks must accompany publication; execution
results belong in the PR/run record, not a fabricated Live-completion claim.

The ideal unrounded transform's eight-layer scale/rotation identity is not a
permitted shortcut for repeatedly rounded Q40 transforms. Orientation periodicity
must not be equated with eight translation states. Certified real-area overlap,
error bounds for the current 96-sample approximation, a phase-region atlas and
any changed coverage semantics remain future mathematical work, requiring their
own contract, independent oracle and migration gate.

## Unchanged project boundaries

Evidence remains the fact source. Core stays deterministic, integer-only and
semantic-blind; Access and the real LLM/Host retain semantic ownership. Unified
Field Encounter still selects one physical entry. Physical Memory Layer is not
Aggregation Order. The V3.14 native exclusive memory slot and standard
`memory_search` / `memory_get` direction remain active. This kernel task neither
reintroduces a custom competing Host tool nor expands the public release claim.
