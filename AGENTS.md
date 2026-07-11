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
- Current stage is M1 Core/Access extraction and cycle removal.
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
