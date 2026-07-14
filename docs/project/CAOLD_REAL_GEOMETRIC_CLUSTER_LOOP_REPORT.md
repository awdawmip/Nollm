# CAOLD Real Geometric Cluster Loop Report

Date: 2026-07-14

## Status And Boundary

`REAL_OPENCLAW_GEOMETRIC_CLUSTER_LOOP_VALIDATED` for the bounded Windows and
OpenClaw scenario authorized by
`NOLLM_CAOLD_REAL_GEOMETRIC_CLUSTER_LOOP_TASK_20260714.md`.

Access generates finite geometry candidates from cursor addresses, Core state,
occupancy, and fixed constants without reading Statement text. A separate
bounded Access call attaches local Statement summaries for the Placement LLM.
The LLM returns an action and `candidate_id`; Access regenerates the candidates
and maps the ID to one address. Python performs no semantic routing. OpenClaw
imports Access and has no direct Core import. No global scan, source/topic/entity
lookup, graph, vector, embedding, or statement-hash placement was added.

## Candidate Contract

Placement wire version is `nollm_openclaw_placement_v2`. With no anchor the
only candidate is `new_cluster:0`. With an anchor, the bounded list is:

```text
existing_cell:0
lateral_ring_1:0 through lateral_ring_1:5
new_cluster:0
```

The six lateral coordinates around `(q,r)` are `(q-1,r)`, `(q-1,r+1)`,
`(q,r-1)`, `(q,r+1)`, `(q+1,r-1)`, and `(q+1,r)`. New clusters use the first
free `(8*n,0)` address at least four hex steps from every occupied cell in the
same plane. Candidate IDs are unique and the list has at most eight entries.
New writes to occupied lateral or new-cluster candidates are rejected.

## Primary Live Statements And Placement

Actual model for Host, Formation, Placement, and Recall was
`meituan/LongCat-2.0`.

| Fact | Statement ID | LLM action and candidate | GeometryAddress |
| --- | --- | --- | --- |
| A1 release Wednesday 15:00 | `dream:0e32e3a96c3bc30fa488ca21fc3892a8b9b3dfdc5d01c1c5ecf71d0257843e8a` | `new_cluster`, `new_cluster:0` | `(0,0)` |
| A2 risk review Tuesday 10:00 | `dream:5925c00706c6493eb0402137f86c735b23d0595815f875710445f8db1d64efe2` | `new_local`, `lateral_ring_1:0` | `(-1,0)` |
| A3 owner Priya | `dream:fee09e2b54b345f4d74b09c4b5a119df8e5f126950add0f697dc264dd694e3a5` | `new_local`, `lateral_ring_1:3` | `(0,1)` |
| B1 cafe closes 18:00 | `dream:4efadd6c6e262042e94ea45b89abfb008a628b71d8d2fce89a04ea1d190723fe` | `new_cluster`, `new_cluster:0` | `(8,0)` |
| B2 visitor desk first-floor east | `dream:50dd9d5510fb49589131230ffe67a0cb46e48c2da9e01de59d4c8d98475ebd8e` | `new_local`, `lateral_ring_1:0` | `(7,0)` |

A and B therefore have two anchors, five primary Statements, five distinct
addresses, and real ring-1 relations inside each cluster. Initial multi-turn
A3 and B2 Formation windows omitted the current user observation and reformed
older facts; Placement selected `reuse`, causing zero Core writes. Fresh
single-turn retries formed the intended facts. This host observation-window
limitation is recorded rather than hidden.

## Per-Anchor Core Recall

Direct reopened Access/Core Recall used only lateral ring 1 and one step:

- Anchor `(0,0)` returned exactly A1, A2, and A3 at `(0,0)`, `(-1,0)`, and
  `(0,1)`.
- Anchor `(8,0)` returned exactly B1 and B2 at `(8,0)` and `(7,0)`.
- No B Statement appeared in A's single-anchor result and no A Statement
  appeared in B's single-anchor result.

The cursor persisted at most four anchors and eight entries, with no semantic
labels. The primary validation cursor contained A `(0,0)`, B `(8,0)`, and the
five primary entry cells above.

## Restart And Fresh Sessions

After a Scheduled Task Gateway stop/start, connectivity was `ok` and port
`18789` was listening.

- R1, `Alpha项目发布前我要关注什么？`: Recall Agent selected A1, A2, and
  A3. The visible answer used Tuesday 10:00, Wednesday 15:00, and Priya without
  naming Nollm.
- R2, `访客到办公室后去哪里登记，咖啡厅几点关门？`: Recall Agent selected
  B1 and B2. The visible answer used first-floor east and 18:00, with no Alpha
  content.
- R3, `太阳系最大的行星是什么？`: no Recall injection occurred,
  `runtimeContextChars=0`, and the visible answer was Jupiter. Formation then
  deferred with zero Statements.

Background Formation after R1 and R2 produced additional model-selected
summary clusters at `(16,0)` and `(24,0)`/`(23,0)`. These are real Placement
choices and remain preserved; they do not alter the primary A/B single-anchor
isolation result. This stage does not claim globally optimal model placement.

## Failure And Recovery

Focused tests cover invalid and occupied candidates, exhausted new-cluster
allocation, Core write failure, and Handle write failure. Each path leaves no
new Statement or Core placement and does not update the cursor.

A controlled Handle failure also ran against the live workspace. Core
placement count remained `8`, cursor SHA-256 remained
`928c345014d12d57c0436a06409b737b5940b8ae70007334d1c11957960d6c21`,
and `dream:controlled-live-handle-failure` did not exist afterward. A following
normal OpenClaw turn answered `4`; Formation deferred. The plugin stayed
enabled and no workspace was cleared.

## Plugin And Data State

The loaded plugin is `nollm-formation` version `0.5.0`, sourced from the
geometric-cluster worktree, with no plugin diagnostics. Its isolated workspace
is `nollm-caold-geometric-v1`. The prior `nollm-caold-revision-v5` workspace
and other Nollm data still exist. The final plugin remains installed and
enabled.

## Automated Evidence

- Focused geometry and memory-loop tests: `18 passed`.
- Access and OpenClaw Python tests: `102 passed`.
- Core, Snapshot, and Trace tests: `49 passed`.
- M0 governance tests: `45 passed`.
- OpenClaw Node tests: `15 passed`.
- OpenClaw direct `nollm_core` imports: `0`.
- Ownership manifest: `1769` tracked rows, `unclassified=0`.
- Module boundary gate: `production=0`, `production_cycles=0`.

## Actual Vector And Completion

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%
```

| Module | Actual | Lifecycle |
| --- | ---: | --- |
| CORE | 95% | `CAPABILITY_VALIDATED` |
| SNAPSHOT | 50% | `IMPLEMENTED` |
| TRACE | 40% | `IMPLEMENTED` |
| ACCESS | 100% | `CAPABILITY_VALIDATED` |
| HISTORY | 10% | `PROPOSED` |
| AUDIT | 10% | `PROPOSED` |
| OPENCLAW | 90% | `CAPABILITY_VALIDATED` |
| LAB | 90% | `IMPLEMENTED` |
| DISTRIBUTIONS | 70% | `IMPLEMENTED` |

Known limits: large-scale geometry, cross-cluster stitching, all-model quality,
long-term stability, release readiness, and cross-provider portability were
not validated.
