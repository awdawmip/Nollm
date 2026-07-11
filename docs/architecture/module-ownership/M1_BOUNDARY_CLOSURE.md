# M1 Production Boundary Closure

Date: 2026-07-11

The reviewed M1 report has zero production violations and no production cycle.
This is an active-path replacement, not an owner-only suppression:

- `nollm-core` now owns executable addressed current state, file persistence,
  atomic commands, Bridge, bounded Recall, Snapshot locking, and Trace emission.
- `nollm-access` now owns Evidence, saved Handles, explicit external decisions,
  action mapping, and Evidence-backed Recall formatting.
- Bare and Minimal distributions point only to package public APIs.
- Package tests run without `reference/python`, Legacy, integrations, or Lab on
  their `PYTHONPATH`.
- `reference/python/nollm/grf` remains a tested Legacy compatibility baseline
  and is absent from every active distribution manifest.

## Closed M0C1 Findings

| Previous debt | M1 resolution | Legacy status |
| --- | --- | --- |
| `relation_field.py` Core to Access placement | New Core Recall traverses `GeometryAddress`, local occupancy, coverage, lateral, and `BridgeSpec` only | GRF implementation retained for migration regression |
| `field_engine.py` Core to Access placement | New Core CellStore stores `GeometryAddress -> local_atom_id -> MemoryAtom` | GRF PlacementRecord store retained outside distributions |
| `replay.py` Snapshot to Access storage | Snapshot consumes new Core `ConsistentStatePort` directly | GRF replay remains Legacy |
| `replay.py` Snapshot to Trace ledger | New Core state bytes need no ledger to restore | GRF ledger replay remains Legacy |
| `storage.py` Access to Trace ledger | New Core and Access stores are separate atomic file stores; Trace is injected | Mixed GRFFileStore remains Legacy |
| `facade.py` Access to Trace ledger | New AccessRuntime uses Core public API and no ledger | GRFFacade remains Legacy compatibility |
| `openclaw_bridge.py` OpenClaw to Core cell/recall | OpenClaw activation is paused; future adapter must call Access public contracts | Existing adapter is an inactive migration asset |
| `grf7r_facade_runtime.py` OpenClaw to Core bytes | It is excluded from active distributions pending future E2E | Existing adapter is an inactive migration asset |
| Access/Core/Snapshot/Trace SCC | New package graph is Core <- Snapshot/Trace/Access with no reverse edge | Old SCC exists only inside the single Legacy GRF namespace |

## Remaining Migration Dependencies

The checker reports nine migration-only dependencies. They originate from
inactive OpenClaw/GRF compatibility assets and are excluded from production
cycle analysis. They are not shipped by Bare or Minimal and are not used by new
package tests.

The zero baseline must be regenerated only after this closure review. Any new
active production dependency or cycle fails the M1 boundary gate.
