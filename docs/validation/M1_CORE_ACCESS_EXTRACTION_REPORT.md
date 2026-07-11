# M1 Core/Access Extraction Report

Date: 2026-07-11

## Verified Facts

- Active Core behavior lives in `packages/nollm-core` and imports only the
  Python standard library and its own package modules.
- `MemoryAtom` contains only `atom_id` and semantic-blind `payload_utf8`.
- `AtomHandle` is `GeometryAddress + local_atom_id`; all mutation uses a Handle
  and Core has no global atom/source/topic lookup.
- Core `CellStore` owns only geometry-addressed local `MemoryAtom` occupancy and
  has no `PlacementRecord`, Evidence, Source, patch, island, or relation route.
- Core current state is a canonical file-first JSON document that reconstructs
  Cell occupancy and Bridge state without a relation route table.
- Commands put/remove/replace/move/bridge/apply_batch are atomic; simulated
  batch and disk failures preserve the prior memory and file state.
- Core Recall accepts explicit cells only and traverses local occupancy,
  coverage, lateral geometry, and explicit bounded bridges.
- Access preserves original UTF-8 Evidence separately, stores caller-held
  Handles, and maps all eight externally provided actions to Core operations.
- Snapshot and mutation share the new Core lock. Trace failure does not change
  Core state, Handles, Recall, Bridge state, Snapshot bytes, or reopen results.
- The active production boundary report is zero violations and zero cycles.

## Test Results Before Final Replay

| Gate | Result |
| --- | ---: |
| Core package | 9 passed |
| Snapshot package | 3 passed |
| Trace package | 1 passed |
| Access package | 7 passed |
| Minimal M1 E2E | Passed under Null and Failing Trace sinks |
| Production boundaries | 0 violations, 0 cycles |

The complete pre-delivery replay also passed:

| Compatibility gate | Result |
| --- | ---: |
| M0 tests | 18 passed |
| Current architecture/no-forbidden/hygiene | 8 passed |
| Complete GRF migration regression | 112 passed |

`zstandard 0.25.0` is available in the recorded Windows environment; no GRF
test was excluded.

## Compatibility And Legacy

`reference/python/nollm/grf` remains a Legacy migration and regression asset.
It is not imported by new package code and is absent from Bare and Minimal.
Old ID/source `QueryProbe`, mixed `GRFFileStore`, `GRFLedger`, deterministic
Facade placement, and direct OpenClaw-to-GRF paths are not accepted M1 runtime
surfaces.

No compatibility re-export was needed. Existing OpenClaw adapters remain paused
migration assets pending a future Access-only integration and real E2E.

## Known Limitations

- The M1 Core state file is a single canonical current-state serialization. It
  is not a relation index; geometry-partitioned files are required before a
  future PB-scale stage.
- M1 does not call a model and does not prove LLM placement quality.
- History and Audit remain skeletons.
- OpenClaw Live, corpora, PB/1M benchmarks, remote push, and physical GitHub
  splitting were not performed.
