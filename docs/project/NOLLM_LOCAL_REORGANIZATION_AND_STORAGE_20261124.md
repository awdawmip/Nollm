# Local reorganization and physical storage

Implemented and locally verified, 2026-11-24. Development input:
`ac587624411fe9c1270317cc89f816efd1ccb535` on main. The frozen
`test/nollm-20261123-1` branch stays at `c4b6b922b993732e008e8d1b95951b47bec823df`;
its runtime/field input remains `f37667bf232360d0c26d37de0639285084230ddc`.

## Implemented behavior

Stored Surface made upper judgments small, but daily reading still opened
whole-state files, and a later Host could not submit a coherent reorganization
under a final-layout budget. This change supplies those operations. The Host
authors judgments and placement; Core computes the non-tree honeycomb relations.
No semantic parent table or alternate router is introduced.

| Layer | Change | Scope |
| --- | --- | --- |
| Core | Geometry-addressed pages, lazy bodies, occupancy/byte metadata, local undo | Explicit migration; existing single-file fields remain readable |
| Access | Paged physical bindings and `reorganize` | Final-layout budget; touched cells, handles and selected configuration recover together |
| Encounter | Read first; explicit write preparation and pressure | Singleton physical candidates require one Host selection; successful recall reuses the loaded Statement |
| Host reorganization | `--reorganize PLAN_JSON` | New/revise/reuse/move/forget from accumulated observations; actual forward paths and terminal readback |
| Storage command | `storage` / `storage --enable-paged` | Read-only layout inspection, or explicit idempotent component migration |

The [skill reference](../../lab/nollm-lab/repository_memory/skills/nollm-repository-memory/references/local-reorganization.md)
documents plan syntax, commands and failures.

## Reading and placement

Ordinary `encounter` returns facts, sources and actual adjacent descent candidates.
`--prepare-write` adds physical placement candidates; `--pressure` requests support
pressure and implies preparation. `--read-only` stops both; `--no-pressure` stops
pressure while retaining preparation. A write choice follows a separate observation.

Writable layers are distinct from Surface layers. Local writing intersects the
configured writable set with the focus and its adjacent layers. Explicit descents
can therefore continue deep into a field without putting every layer on the first
page. Candidate flags report the current focus, downward readability and whether
its layer has a content budget. A singleton Surface candidate exposes its physical
member for direct Host selection; multiple members retain physical selection.
Historical `walk` behavior is retained.

Ordinary NEW under `via=downward` requires the focus or an actual downward target.
The frozen witness L−2(0,−2) → L−1(−2,−2) has upward support 683/65536 but no
downward edge; it is rejected before Evidence capture. Other explicitly chosen
kernels retain their previous placement capability.

## Local reorganization

```python
access.reorganize(
    decisions,
    statements=statements,
    content_budget=policy,
    configuration_files=configuration,
)
```

Access projects ordered explicit decisions before mutating. The Core/Access API
also supports `revision_keep_history`; the native CLI exposes new, revise, reuse,
move and forget. Entrance/writable-layer configuration and content budget can
change in the same batch. Targets come from prepared observations, and a later
action can reference a current ID created earlier in that batch.

Capacity applies to the **final** contents. Tests execute a full-Surface NEW+FORGET
replacement, middle revision and detail move together, then read the result again
from the native entrance. Another case adds a more coarse L−3 entrance while
switching its budget and Surface configuration, preserving the path to L0.

The adapter validates real adjacent `coverage_down` edges for changed current
expressions and explicit readback requests. After commit it checks these edges
again and consumes the terminal current expression through normal Access recall.
An observed ancestor prefix remains usable after further descent. An unrelated
stale observation does not block the touched facts.

The returned guarantee is `changed_current_and_explicit_paths`. Other known old
entrances should be included explicitly if their reading paths must remain.
This is not a whole-field orphan proof or evidence that another model will choose
these paths within a finite budget. It does not maintain reverse coverage. The
[earlier study](NOLLM_TOP_DOWN_MAINTENANCE_AND_REORGANIZATION_20261123.md) records
why zero global orphans does not prove retention of useful old entrances.

### Recovery and ownership

Preflight failure leaves placement and new Evidence untouched. After preflight,
captured immutable Statements survive a later commit failure. Ordinary exceptions
restore the affected cells, bindings and settings. After process interruption,
the next Access open restores the local recovery record before use. Failed CLI
plans retain their cursor; successful retry deletes it.

The existing single-Core owner and Access composition lock serialize mutations.
Independent direct Core readers do not obtain a cross-file instantaneous view.
Ordinary Access mutations now use the same local savepoints; bridge actions keep
their existing separate path. The explicit `apply_if_state` API still performs
its contractual full-state comparison.

Fresh immutable IDs captured in the same locked operation skip binding inventory.
Separated capture→apply retains the duplicate-binding check; a test covers another
Access instance binding the ID between those calls. There is no new shared fresh-ID
cache or statement-to-geometry routing index.

## Physical storage

Core and binding pages use profile, chart, phase, physical layer and coordinate
partition; default width is 64. All cells within a page share its file. Occupancy
metadata includes current bytes. Missing metadata falls back to its page body,
so deleting a cache does not hide facts. Core logical v1 export/import and binding
logical v2 export remain unchanged; canonical and mixed-phase identity are tested.

```sh
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field FIELD storage --enable-paged --partition-width 64
```

Migration processes Core then bindings. Failure in the second component reports
`partial`, identifies the error and exits nonzero; repeating the command skips
the completed component and finishes the other. `storage` alone inspects the two
markers without opening runtimes or triggering recovery. Already-paged components
keep their original width. Logical comparisons occur in tests, without adding a
full-state export to the migration command.

## Measured application file bytes

The [probe](../../lab/nollm-lab/repository_memory/probe_local_storage_cost.py) compares
two layouts using the **same candidate code and logical inputs**, not historical
release speeds. It adds 256 remote L0 facts × 8,192 bytes = 2,097,152 bytes in
distinct width-64 partitions. The local facts and bounded L−2 Surface stay fixed.
Each operation opens a fresh runtime. Formation, migration, copying, cursor
preparation and post-checks are outside measurement.

Counts intercept actual Python file reads/writes, including immutable captures,
atomic temporary writes and Core/Access recovery journals. They exclude directory
and stat work, fsync/rename device traffic and OS physical I/O. No timing or
disk-speed ratio is claimed. All 16 outcomes and final logical states match.

Values are bytes, **0 remote facts → 256 remote facts**:

| Operation | Single-file read | Paged read | Single-file write | Paged write |
| --- | ---: | ---: | ---: | ---: |
| Native first Surface | 2,078 → 2,210,564 | 1,585 → 1,585 | 0 → 0 | 0 → 0 |
| NEW at known cell | 3,578 → 2,329,542 | 2,917 → 2,917 | 3,564 → 2,212,050 | 3,120 → 3,120 |
| Native observed revision | 5,220 → 2,448,662 | 4,214 → 4,214 | 3,529 → 2,212,015 | 3,085 → 3,085 |
| Revision after ID lookup | 4,994 → 2,448,436 | 4,260 → 78,103 | 3,529 → 2,212,015 | 3,085 → 3,085 |

ID lookup inventories binding pages: 9 → 265 read files versus 8 for observed
revision, without reading remote bodies. Paged NEW includes Access/Core journal
writes of 1,161/709 bytes; revision includes 1,407/709, already counted above.
The [raw result](../../lab/nollm-lab/repository_memory/results/local_storage_cost_20261124.json)
contains method boundaries and per-category counts.

```sh
python3 -B lab/nollm-lab/repository_memory/probe_local_storage_cost.py \
  --output /tmp/nollm-local-storage-cost.json
```

The probe accepts `--remote-count`, `--body-bytes` and `--include-files`, uses
isolated fields and refuses to overwrite an existing output.

## Validation and remaining work

The engine/Access/Snapshot run passed **101 tests**; affected native, installer and
CLI tests passed **57**: **158 distinct tests**, without adding repeated smaller
runs. [Validation details](../../lab/nollm-lab/repository_memory/results/local_reorganization_validation_20261124.json)
give exact paths and commands. Coverage includes process-exit recovery, full-cell
swaps, canonical state, binding uniqueness/current/support, revision continuation,
stale observations, genuine missing forward edges, new coarse entrances, partial
migration retry and installed batch→reopen→descent recall. Fault-injection ports
were updated to local persistence, with semantic recovery assertions retained.
This is focused validation, not all historical project tests.

- Surface still inventories occupancy metadata for declared layers. Its stored
  judgments must remain small and meaningful; paging does not repair formation.
- One page includes its other cells, which still affect read/write/journal size.
- Core opening reads the complete bridges file. Whole-layer budgets, exact-ID
  location searches and explicit complete exports retain their wider cost.
- Automatic forward-maintenance scheduling and orphan repair remain separate.
  The Host decides interpretation, organization and preservation scope.
- Core Q40/96 and the frozen scientific input are unchanged. Selected adjacent
  local-p8/96 remains pending; this change does not fix old Lab world-unit/reanchor
  dependence by implication.
