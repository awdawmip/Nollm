# M0C1 Boundary Baseline Review

Date: 2026-07-11

Status: `HISTORICAL / SUPERSEDED`. This document preserves the M0-to-M1 debt
record. The active boundary truth is `M1_BOUNDARY_CLOSURE.md` plus the generated
`MODULE_OWNERSHIP_MANIFEST.json`, which require zero production violations and
zero production cycles.

## Why the M0 Baseline Was Rejected

The M0 baseline contained 642 undifferentiated findings and one owner cycle.
Most findings were classification noise: approximately 574 were Lab tests
importing Legacy migration implementations, and approximately 40 came from
root/tool files incorrectly classified as Distribution production code.

M0C1 applies the module charters directly:

- Lab may depend on all public modules and Legacy migration assets.
- Production modules may never import Lab.
- Repository tests, experiments, validation scripts, `run_tests.py`, and tools
  are Lab/tool assets rather than Distribution runtime modules.
- Legacy dependencies are reported separately and do not enter the production
  acceptance baseline.

After reclassification, the reviewed report contained 9 production violations
and 43 Legacy migration dependencies. Binding the real Snapshot adapter added
one explicit Legacy `grf/__init__.py` to Snapshot adapter export, bringing the
final migration count to 44. No new package implementation violates a target
package boundary.

## Reviewed Production Debt

| Source | Edge | Current fact | M1 action |
| --- | --- | --- | --- |
| `grf/relation_field.py` | Core to Access | Geometry propagation consumes `PlacementRecord` | Extract a Core occupancy/read contract |
| `grf/field_engine.py` | Core to Access | CellStore/FieldEngine consumes `PlacementRecord` | Split pure CellStore state from Access placement records |
| `grf/replay.py` | Snapshot to Access | Replay reads the mixed `GRFFileStore` | Bind replay to public state/storage ports |
| `grf/replay.py` | Snapshot to Trace | Replay reads `GRFLedger` | Make ledger input an optional public Trace contract |
| `grf/storage.py` | Access to Trace | Mixed store appends ledger events | Inject an optional Trace contract |
| `grf/facade.py` | Access to Trace | Workspace validation reads the ledger | Read through a public Trace/report contract |
| `grf/openclaw_bridge.py` | OpenClaw to Core | Adapter constructs `CellAddress` directly | Translate through Access public request contracts |
| `grf/openclaw_bridge.py` | OpenClaw to Core | Adapter constructs Recall contracts directly | Route Recall requests through Access |
| `integrations/adapters/grf7r_facade_runtime.py` | OpenClaw to Core | Adapter imports canonical Core bytes directly | Move serialization behind Access public contracts |

These are real dependencies in current source. M0C1 records them rather than
rewriting the entire Core/Access boundary.

## Cycles

The production graph has one strongly connected component:

```text
ACCESS <-> CORE
ACCESS -> SNAPSHOT -> ACCESS
ACCESS -> TRACE -> CORE -> ACCESS
```

The component is attributable to the file edges above. Lab is excluded from
production cycle analysis. The M1 action is contract extraction, not deletion
of `RelationField` or broad movement of mixed files.

## Baseline Decision

The schema-v2 baseline may freeze exactly these reviewed production findings
and this production cycle. Final M0C1 checks fail on any additional production
finding or production cycle. Legacy migration relationships remain visible in
the report but do not obscure the production gate.
