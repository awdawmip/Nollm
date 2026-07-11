# Nollm Codex Rules

Execute the current taskbook exactly. Do not redesign or broaden scope.

- Before any Nollm task, read:
  `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md`
  and the current taskbook.
- First-principles invariants govern architecture direction.
- Current modular charters govern component ownership.
- Dated execution order in the first-principles document is historical stage
  context; the current taskbook governs scheduling without overriding the
  architectural invariants.
- If a filename-based classification conflicts with current code behavior,
  inspect the code and classify from behavior, dependencies, and state ownership.
- Never mark a component `DELETE_LATER` merely because an older version of a
  same-named file contained a forbidden path.
- Current stage is M1-C3 immutable-kernel, phase-canonicality, and workspace-coordinator closure.
- Preserve all accepted M1-C2 nine-template, canonical-Evidence, HandleBinding, boundary, and package results.
- KernelRegistry and every registry/state identity input are immutable after construction.
- Persistent and Recall geometry ordering uses GeometryAddress.stable_key only.
- GeometryAnchor cells are strictly sorted, unique canonical set tuples.
- Active lateral supports registered ring 1 only; unregistered rings are rejected.
- One process cannot host independent mutable CoreRuntime owners for one canonical Core workspace.
- Access reads spanning Core, Binding, and Evidence share the workspace coordinator lock.
- Preserve M1/M1-C1 Addressed Handle, package boundaries, and one-current HandleBinding.
- Kernel parity covers all three profiles and up/down/lateral, including residuals and fanout semantics.
- Geometry registry identity binds every active relation-kernel semantic used by Recall.
- Any accepted Core state must re-encode byte-for-byte to persisted bytes; semantic reordering and empty cells are invalid.
- Persistent public dataclasses reject incorrect direct-constructor types before any write.
- MemoryStatement and Evidence files never coerce numeric, bool, or object values into strings.
- Access mutations are serialized across Core and Binding snapshots, actions, and rollback.
- Forget by explicit Handle remains possible when Evidence is missing.
- Core Recall must use the accepted Coverage Template registry; heuristic layer or coordinate scaling is forbidden.
- Increasing layer indices are finer: coverage up decrements the layer and coverage down increments it.
- Core and Access persisted state must use strict canonical bytes with no type coercion or duplicate identities.
- Access Evidence resolution must use the exact canonical HandleBinding; lexical aliases and atom-id fallback are forbidden.
- Cross-store Access mutations must be exception-atomic and expose fatal consistency failure when rollback cannot complete.
- Do not resume OpenClaw Live, model calls, or corpus execution.
- Core operations require addressed handles; no global atom-id lookup.
- Core Recall accepts explicit geometry entry cells only.
- Access owns semantic decisions and evidence/source mapping.
- Old GRF compatibility code may remain only outside active distributions.
- Do not remove a legacy implementation until a tested replacement exists.
- Production boundary target for M1 is zero violations and zero cycles.
- Preserve all potentially useful components until ownership is proven.
- Classify before moving; move before deleting.
- Core owns geometry current-state operations only.
- Snapshot, Trace, Access, History, Audit, OpenClaw, Lab, and Distributions are separate modules.
- Do not add relation indexes, embeddings, semantic graphs, or Python semantic-placement logic.
- Do not run live OpenClaw, long LLM corpus jobs, or remote GitHub changes in this stage.
- Windows-first; fix ordinary failures inside the task.
- Deliver one clean Git bundle and a clean working tree.
