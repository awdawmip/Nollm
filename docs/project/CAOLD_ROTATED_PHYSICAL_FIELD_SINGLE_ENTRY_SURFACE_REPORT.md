# CAOLD Rotated Physical Field and Single-Entry Surface Report

Date: 2026-07-14

## Delivery identity

- Input bundle: `nollm_caold_adaptive_surface_recall_20260714_00ce6579.bundle`.
- Input bundle SHA-256: `05b142fbea7307d0a198306bee98454a0aed0c6ed8ed7f7f1490b534769a5dc2`.
- Input HEAD: `00ce6579eb29ff98557996105f3b7f9a5d85167d`.
- Validated code/evidence commit: `c9f1a0990fe15186835e8ae2bb6507400226fa44`.
- Completion identity is the annotated `REAL_OPENCLAW_ROTATED_PHYSICAL_FIELD_SINGLE_ENTRY_SURFACE_RECALL_VALIDATED_AT_<HEAD>` tag on the report commit.
- The complete-history bundle filename and SHA-256 are recorded in the external delivery handoff because a bundle cannot contain its own byte hash.

## Capability result

The planned and actual vector match: Core +15%, Access +10%, OpenClaw +5%,
Lab +15%, Distributions +5%; Snapshot, Trace, History, and Audit are unchanged.
Final estimates are Core 90%, Snapshot 50%, Trace 40%, Access 90%, History
10%, Audit 10%, OpenClaw 85%, Lab 90%, and Distributions 70%.

V3.6 remains evidence for cursor-free rebuildable Surface traversal, real host
integration, atomic Placement, and restart persistence. It is not evidence for
the target physical transform, physical/observation address separation, real
coarsening, or single-entry propagation.

## Physical field

`default_dream_v1` binds `nollm_rotated_physical_field_v1`: pointy-top Model T,
delta theta 22.5 degrees, `theta(L) = L * 22.5 degrees mod 60 degrees`,
`beta = 2^(1/4)`, and adjacent-layer density ratio `sqrt(2)`. The generated
artifact SHA-256 is
`3837ff239bb34512aacbfee6a2178afa22c6d4b037278c216a5ec7db74b662a2`.
It contains 24 physical templates over eight phases plus nine legacy templates.
Certified Coverage fanout is seven; normalization residuals are 6 Q16 units
for coverage-up and 1 Q16 unit for coverage-down at every phase. Decimal-72
polygon validation, reciprocal overlap, translation checks, golden centers and
vertices, and runtime integer-only constraints passed.

`GeometryAddress` now identifies physical cells only. `PhysicalFieldScope` and
`SurfaceAggregateAddress` identify rebuildable observation domains; Surface
Order never changes physical layer identity. Orders 0 through 8 rebuild after
mutation, import, and reopen, and native atoms from every supported physical
layer in scope are visible.

Dense radius-5 occupied counts were `91,73,61,49,43,37,31,25,19`, selecting
Order 1 without overflow. Dense radius-8 counts were
`217,169,127,103,85,67,49,43,37`, selecting Order 2. Sparse counts were
`3,4,6,7,8,10,12,13,16`, proving that sparse data is not forced into monotonic
merging. Observation area strictly increased at every Order. Natural
multi-entry reachability remains diagnostic and has no minimum acceptance
count.

## Access and OpenClaw

Access selects the finest affordable real Core Surface from fixed structural
budgets. Query, session, Statement content, and prior traversal do not select
Order. The active Recall budget is `(4,64,2,1,1,16)` and enables bounded
Coverage, Lateral, and Bridge traversal from exactly one final entry. Production
wire and code contain no `select_entries`, `selected_entries_limit`, or
`per_entry_core_recall`. Placement writes only physical layer 0 and
`expand_surface` uses exact pointy-top world distance.

Windows Live used OpenClaw 0.7.0 with the enabled plugin loaded from this
worktree and Gateway Health `OK`. R1 selected entry `(-1,1)` at Order 0 and
returned the Alpha Tuesday 10:00 review, Wednesday 15:00 window, and Priya.
R2 began at the same Order, selected `(7,0)`, and returned the one-floor-east
visitor desk and 18:00 cafe close. R3 completed NONE with no Statement
injection and answered the Jupiter control from general model knowledge.

P1 persisted Statement
`dream:7c8395a63c7c2083fc6bba9d0d9ceb71504313c397278390c24e8fea1cc10719`
through one `new_local` Placement at `(-1,1)` with one Core write. The first
attempt exposed malformed model `existing_handle` input; it was classified as
retryable `invalid_schema` with no orphan. A transient model attempt deferred
without writes. The next attempt succeeded. After Gateway restart, a fresh
single-entry Recall returned Monday 16:00 and Priya from only the P1 Statement.
The visible model answer additionally inferred "weekly" and a purpose not
present in the selected Statement; those additions are not credited as memory
evidence.

## Migration and preservation

The source workspace remains at
`C:\Users\Administrator\.openclaw\memory\nollm-caold-adaptive-surface-v1` and
the migrated workspace is
`C:\Users\Administrator\.openclaw\memory\nollm-caold-rotated-physical-field-v1`.
Migration preserved 9 cells, 9 atoms, 9 bindings, 12 Statement files, and zero
bridges. Source and target Statement tree SHA-256 are both
`1a41c657e4ec1d18ad47333d9b2d8b94c8a2db1520341e26f0f340b3d93757ca`.
The preservation backup is under
`memory/backups/caold-rotated-physical-field-gate0-20260714`. No source data or
workspace was deleted.

## Verification and limits

Package regression: 133 passed with eight expected deprecation warnings;
OpenClaw Python: 37 passed; M0 governance: 45 passed; Node: 18 passed; plugin
import check passed. Physical geometry, certified Coverage, 9/9 legacy parity,
25 Core capabilities, minimal E2E, real coarsening, migration self-check,
Snapshot/Trace, Manifest, and boundary validation passed. Git tracked and
Manifest rows both equal 1787; unclassified assets, production violations,
production cycles, OpenClaw direct Core imports, Cursor, semantic routes,
graph/vector/embedding, and multi-entry production fields are all zero.

Known limits: production Placement is layer-0 only; PB-scale performance,
long-duration quality, complete multi-layer Placement, Stitch finalization,
density-driven relocation, and cross-platform portability were not validated.
Surface is rebuilt by bounded in-memory scans and has no persistent cache.
