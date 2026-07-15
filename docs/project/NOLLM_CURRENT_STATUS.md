# Nollm Current Status

Date: 2026-07-15

```text
route: NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
task: NOLLM_C_A_O_L_D_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_RECALL_TASK_20260715.md
status: CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS
input HEAD: 5a453847747a7f460ce37df044dec50c554b494b
```

Preserved checkpoint capability:

```text
K=96 bounded approximate fixed-point Coverage;
missed p99=0.016413, false p99=0, TV p95=0.042893;
Q16 partition error=0, dominant agreement=1.0, max fanout=7;
lazy 11-cell Surface=27.829ms, dense 217-cell Surface=823.615ms;
one physical entry, no Cursor/select_entries;
real R1 Alpha, R2 Office, R3 NONE;
P1 core_write_count=1 and restart Recall answer BX-3917.
```

Active live workspace:

```text
C:\Users\Administrator\.openclaw\memory\nollm-v39-bounded-approximate-v1-migrated
non-destructive registry migration v5 -> v6; physical addresses unchanged
Statement and HandleBinding bytes preserved from the accepted source
```

Independent audit correction:

```text
512 broad fixtures: 434 valid and 78 boundary-unsupported;
missed p99 about 2.1371%, TV p99 about 2.8102%, false max 0, fanout max 7;
20,000 fast fixtures: 17,091 valid, 2,909 boundary-unsupported;
production/prototype hit mismatch 683, requiring separate Oracle scoring;
the transport radius 2^31-1 is not the active two-step writable radius.
```

Broad calibration result:

```text
2048 exact fixtures and 20,000 diagnostics passed;
selected policy nollm_broad_residue_min_hit_1_v1;
production missed p99 1.2411%, TV p95 2.0776%, false max 0;
dominant agreement 98.97%, max fanout 7, Q16 partition error 0;
17,036 diagnostics valid, 2,964 boundary unsupported, 651 hit mismatches.
```

Dense locality result:

```text
density_state removed; candidate occupancy is exact {count, band};
300 occupied cells and 1,000 atoms validated;
300-cell cold/continuation 1.116s/95.5ms;
1,000-atom cold/continuation 0.533s/259.9ms;
31 truncated Surface cells; reopen identity and mutation invalidation passed;
Order 8 overflow remains truthful at 112 aggregate cells.
```

Dense single-entry Recall result:

```text
301 occupied cells and 1,000 atoms;
one entry A, 59 unique bounded results, target score 49,152;
target path coverage_down; disabled kernels do not reach target;
direct and coverage_down+lateral geometry deduplicates to one target item;
natural entry B did not emerge; observation minimum is zero;
no combined request, semantic index, or persisted fact-to-entry mapping.
```

Current legal boundary:

```text
storage/transport hex radius <= 2^31-1;
active writable hex radius <= 2^30-1 with max coverage-down depth 2;
physical layer -64..64;
chart_id=default; phase=null; semantic Placement layer 0;
exact Decimal/polygon only as Lab Oracle;
no Stitch, persistent Surface cache, PB run, multi-Chart, graph/vector/embedding.
```

The active policy choice, safe writable radius, dense-field evidence, and final
HEAD have not yet been established. Progress is recorded in
`docs/project/CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_REPORT.md`.
