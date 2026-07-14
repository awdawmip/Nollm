# CAOLD Adaptive Surface Recall Report

Date: 2026-07-14

## Delivery basis

- Input HEAD: `a515ae778888ec76ec258ff51e53ee283501dd9b`.
- Input bundle: `C:\Users\chaos\nollm_caold_real_geometric_cluster_loop_20260714_a515ae77.bundle`, SHA-256 `b2f4d2f11fb6c916e52826fda1c7feebec9db73096a876798564ecc39dd62c2b`.
- Branch: `codex/caold-adaptive-surface-recall`.
- Validated implementation/test checkpoint before this report: `e91fee1e`.
- Final HEAD and capability tag are the commit and annotated tag that contain this report; they are recorded by the external Git bundle delivery receipt because a commit cannot contain its own identity.
- Expected and actual vector: `CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% | HISTORY 0% | AUDIT 0% | OPENCLAW +10% | LAB +5% | DISTRIBUTIONS +5%`.

## Result

Core now derives immutable Order 0/1/2 Surface projections from canonical geometry and Coverage. Access selects the finest affordable order from fixed structural budgets and owns bounded page/descent state, current Handle previews, candidate validation, and canonical multi-entry Recall. OpenClaw 0.6.0 uses real hidden model calls for Surface traversal, Recall selection, and Placement; it has no direct Core import and exposes no main-agent tool.

The completed module estimates are Core 100%, Snapshot 50%, Trace 40%, Access 95%, History 10%, Audit 10%, OpenClaw 85%, Lab 90%, and Distributions 70%. This is capability completion against the current V3.6 task, not product release readiness.

## Migration and preservation

- Source workspace: `C:\Users\Administrator\.openclaw\memory\nollm-caold-geometric-v1`.
- Adaptive workspace: `C:\Users\Administrator\.openclaw\memory\nollm-caold-adaptive-surface-v1`.
- Backup: `C:\Users\Administrator\.openclaw\memory\backups\caold-adaptive-surface-20260714`.
- Cursor backup SHA-256: `928c345014d12d57c0436a06409b737b5940b8ae70007334d1c11957960d6c21`; size 5,566 bytes; 6 sessions; 1 agent.
- Preserved input had 11 Statements. Handle-store SHA-256 was `75c6b63d610e89d4f002f1d75298586e1fa597c5592401eadafa1c0e53030299`; Core-state SHA-256 was `293a035cc99512d2dd6e69f410f7395e7d809ca33918e215647cad35792fbeb5`.
- The old cursor was backed up and then removed. Neither old nor adaptive live workspace contains `memory_cursor.json`. Statements, Handles, Core state, Bridges, plugin data, and old workspace directories were retained.
- Active production paths contain zero `MemoryCursor`, `CURSOR_SCHEMA_VERSION`, `memory_cursor`, `cluster_anchors`, `cursor_cells`, `per_anchor_context`, or `new_cluster` references.

## Surface evidence

The live plane is `SurfacePlane(eisenstein_exact_v1, default, phase=None, base_layer=0)`. After live P1, the rebuildable statistics were:

| Order | Occupied cells | Page hint | Aggregate mass Q16 |
| ---: | ---: | ---: | ---: |
| 0 | 9 | 2 | 589824 |
| 1 | 21 | 3 | 589824 |
| 2 | 37 | 5 | 589788 |

Lab fixtures independently produced occupied counts 4/10/18, three Coverage parents for one source cell, stable pagination, query-free order selection, and byte-identical reopen state/surface results. No aggregate Surface, traversal answer, topic map, or cursor is persisted.

Production budgets are Recall `page_size=8, max_pages=4, max_cells=32, max_projection_units=160, selected_entries=3, max_calls=12`; Placement is `8/6/48/240/1/16`. The coarse live validation temporarily used `max_cells=1` and `max_projection_units=1`, truthfully exercised hard-order-2 overflow, and was restored to production defaults before delivery.

## Windows live gate

- R1, forced coarse: Active Order 2, path `2 -> 1 -> 0`, entries `(0,0)` and `(0,1)`. Independent ring-1 results merged the Alpha risk review, Wednesday 15:00 release window, and Priya. The visible answer included all three facts.
- R2, forced coarse: same Active Order 2, path `2 -> 2(page) -> 1 -> 0`, entries `(7,0)` and `(8,0)`. It returned the first-floor east visitor desk and 18:00 cafe closing time. R1 and R2 therefore used the same structural order and different model-selected regions.
- Gateway restart: service last-run changed and the health probe remained OK. A fresh related query again followed `2 -> 1 -> 0`, selected `(-1,0)` and `(-1,1)`, and recovered the Alpha facts.
- R3, production defaults: Active Order 0 with 9 occupied cells, 2 estimated pages, and 52 projection units. The real Surface agent returned NONE on the first finite page. Evidence is `stage=recall`, `status=completed_none`, empty entry cells, and no injected context. The main model independently answered Jupiter.
- Hidden agents used `meituan/LongCat-2.0`, `deliver=false`, and persisted no subagent transcripts. Visible-message count in Nollm evidence remained zero.

P1 continued after migration. Real Formation produced Statement `dream:b70fb0502962c6a1cb2171730ab535c737973c7f3ca520356508ec7723d32148`; real Surface Placement chose `new_local`, wrote one Core atom at `(-1,1)`, and returned `core_write_count=1`. The final live Core placement count is 9. Earlier P1 evidence predates the correction that adds `surface_path` directly to `placement_apply`; its finite candidate and selected entry remain present, but the path is correlated through adjacent live events rather than embedded in that one event.

Failure atomicity is covered by package tests for invalid candidates, occupied candidates, Core/Handle write failure, traversal limits, malformed envelopes, and defer/NONE. These paths leave no orphan Statement, Handle, Core atom, cursor, or traversal state.

## Verification

- Core: 44 passed; Snapshot: 7 passed; Trace: 3 passed; Access: 75 passed with 8 expected deprecation warnings.
- OpenClaw Python: 36 passed; Node: 18 passed; plugin import check passed.
- M0 governance: 45 passed using explicit current-worktree package paths.
- Geometry parity: 9/9; Core capability: 25; Minimal E2E: passed; Adaptive Surface Lab: passed.
- Ownership: 1,778 tracked rows, zero unclassified; production violations 0; production cycles 0.
- OpenClaw direct `nollm_core` imports: 0. Production Cursor/cluster/new-cluster strings: 0.
- Plugin final state: version 0.6.0, enabled, loaded, diagnostics empty. Gateway health probe OK. Final budgets are the production defaults above.

## Limitations and delivery

Coverage overlap means occupied projection counts can increase at coarser orders; the forced-coarse gate therefore exercised the specified hard-max overflow path instead of claiming that Order 2 reduced this small fixture. The Windows `openclaw gateway restart` CLI repeatedly completed the restart but waited beyond its command timeout; service last-run time and health probe provided the authoritative result. Cross-platform portability, large-scale performance, global semantic quality, multi-plane selection, Stitch, History/Audit completion, and long-term stability were not validated.

The self-contained bundle name is `nollm_caold_adaptive_surface_recall_20260714_<final-short-head>.bundle`. Its final SHA-256 is necessarily computed after the report-containing commit and is supplied in the external delivery receipt; `git bundle verify`, `git fsck`, and clone replay are required before handoff.
