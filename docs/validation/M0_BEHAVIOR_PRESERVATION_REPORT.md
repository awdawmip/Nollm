# M0C1 Behavior Preservation and Closure Report

Date: 2026-07-11

## Status

M0C1 corrects the rejected M0 ownership, Port-binding, boundary, and architecture
regression claims. It does not start M1, OpenClaw Live Integration, an LLM
corpus, a remote repository split, or a long benchmark.

## External M0 Review Facts

The external review of the M0 bundle reported:

- M0 tests: 7 passed.
- A GRF run: 109 passed and 1 skipped.
- Two optional compact-evidence tests failed because `zstandard` was absent in
  that review environment.
- `test_architecture_language.py` still asserted V2 as the only active
  architecture and failed against the new root navigation.
- The old boundary baseline contained 642 findings and one cycle; most findings
  were Lab/Legacy or root-file classification noise.

Those review results are historical input to M0C1. They are not presented as
successful M0 acceptance.

## Current Windows Environment

The final environment is Windows with Python for Windows. `zstandard 0.25.0` is
installed, so the complete GRF suite runs without excluding the two optional
compression tests. There is no remaining environment-dependent test failure in
the required M0C1 gates.

## Verified M0C1 Facts

| Gate | Result |
| --- | --- |
| Manifest generator `--check` | Read-only, canonical outputs unchanged |
| Manifest validator | 100% tracked coverage; schema and truth rules pass |
| Boundary checker | 9 reviewed production findings, 0 new; 1 reviewed production cycle, 0 new; 44 migration dependencies |
| M0 tests | 18 passed |
| Real Snapshot/Trace Port tests | 4 passed |
| Current architecture/no-forbidden/hygiene tests | 8 passed |
| Complete GRF tests | 112 passed |
| Unclassified tracked files | 0 |
| HIGH + MOVE + PENDING | 0 |
| BLOCKED/DELETE without code evidence | 0 |

## Reproducible Commands

With the taskbook `PYTHONPATH` and pytest environment variables set:

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py
python -m pytest -q reference/python/tests/m0
python -m pytest -q reference/python/tests/m0/test_real_ports.py
python -m pytest -q reference/python/tests/test_no_forbidden_features.py reference/python/tests/test_architecture_language.py reference/python/tests/test_repository_hygiene.py
python -m pytest -q reference/python/tests/grf
git diff --check
git status --short
```

## Ownership Truthfulness

`relation_field.py` is no longer marked `DELETE_LATER`. Code review confirms it
uses explicit Cell, Coverage, Lateral, and Bridge propagation with linear scans
and no route table or external relation index. It is `CORE / MEDIUM / SPLIT`
because it consumes placement and recall-result contracts.

`field_engine.py` is also `CORE / MEDIUM / SPLIT`, not a pure HIGH Core leaf,
because it imports `PlacementRecord` and `RelationField`. Existing experiment
roots are declared Lab roots and use `KEEP`; M0's completed R100 OpenClaw Lab
moves are recorded at their actual target paths.

The Manifest contains no unsupported `BLOCKED` or delete conclusion. Unknown
assets default to `LEGACY / LOW / QUARANTINE`. Seven negative validator tests
prove that forbidden HIGH imports, malformed moves, evidence-free blocks, LOW
deletes, tracked omissions, and unsafe catch-all classifications are rejected.

## Real Snapshot Port

`GRFWorkspaceConsistentStateAdapter` binds the public Core consistent-state port
to a real file-first GRF workspace. Tests use `GRFFacade`, `GRFFileStore`, raw
UTF-8 evidence, explicit admission, a negative-coordinate placement, and actual
workspace files. They verify create, restore, clone, verify, structural diff,
read cleanup after export failure, invalid-input atomicity, and equivalence with
the existing `GRFFacade.snapshot/restore` path.

Snapshot bytes are finite and in memory. Restore uses same-volume staging and
replacement. Snapshot does not infer truth, history, retention, or audit state;
Core does not import the Snapshot implementation.

## Real Trace Port

The Core contract now provides `safe_emit`. Real `CellStore.insert/remove/move`,
`FieldEngine.add_bridge/remove_bridge`, and `RelationField.step` emit optional
events. Tests execute the same real occupancy, bridge, propagation, and bounded
Recall sequence under Null, Memory, Failing, and Composite sinks.

Cell occupancy, placement count, bridge state, RelationField output, Recall
output, return values, and post-failure state are identical. Trace events are
not persisted in Core state, and a failing ordinary sink cannot interrupt a
mutation.

## Remaining M1 Debt

The reviewed production baseline contains nine real mixed-boundary imports and
one `ACCESS/CORE/SNAPSHOT/TRACE` strongly connected component. The exact files,
edges, and extraction actions are recorded in
`docs/architecture/module-ownership/M0C1_BOUNDARY_REVIEW.md`.

M1 must extract those contracts. M0C1 does not delete RelationField, rewrite
FieldEngine, split all Evidence/Source objects, implement semantic Placement, or
perform a GitHub repository split.
