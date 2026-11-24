"""Host-authored local reform with actual forward paths and one Access batch.

The encounter observations are temporary working context, never a persistent
semantic router. The Host authors every expression and explicitly chooses cells.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

from nollm_access import (
    AccessDecision, AccessRecallRequest, AccessRuntime, ContentBudgetPolicy,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileHandleStore,
    FileStatementStore, MemoryStatement, RECALL_SURFACE_BUDGET,
)
from nollm_core import AtomHandle, CoreRuntime, RecallBudget, expand_physical_coverage

from coverage_cli import address, coords


SCHEMA_VERSION = "nollm_local_reorganization_v1"


def _cell(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("a physical cell is [layer, q, r]")
    return address(*value)


def _validate_path(path, target, allowed_roots):
    if not isinstance(path, list) or not path:
        raise ValueError("readback needs a nonempty physical path")
    cells = tuple(_cell(value) for value in path)
    if cells[0] not in allowed_roots or cells[-1] != target:
        raise ValueError("readback must start at an observed entrance and end at the final placement")
    for parent, child in zip(cells, cells[1:]):
        if child not in {member.target for member in expand_physical_coverage(parent, "coverage_down").members}:
            raise ValueError("readback path does not follow actual adjacent coverage_down")
    return cells


def _observed_route(target, observations, allowed_roots):
    if target in allowed_roots:
        return (target,)
    for observation in reversed(observations):
        prefix = observation.get("focus_path", ())
        if not prefix:
            continue
        cells = [_cell(value) for value in prefix]
        candidates = []
        if target in cells:
            candidates.append(cells[:cells.index(target) + 1])
        candidates.extend([*cells[:index + 1], target]
                          for index, parent in enumerate(cells)
                          if target.layer == parent.layer + 1)
        for candidate in candidates:
            try:
                return _validate_path([coords(cell) for cell in candidate], target, allowed_roots)
            except ValueError:
                continue
    raise ValueError("no observed forward path reaches this placement; supply an actual readback path")


def _configuration(field, cursor, plan):
    from project_memory import KERNELS, _encounter_defaults, _selected_layers, _surface_scope

    files = {}
    current = _encounter_defaults(field)
    replacement = plan.get("encounter")
    if replacement is not None:
        allowed = {"surface_layers", "layers", "order", "page_size", "steps", "limit", "via", "beam", "compact"}
        if not isinstance(replacement, dict) or set(replacement) - allowed:
            raise ValueError("encounter update contains an unknown setting")
        current = {**current, **replacement}
        if "layers" in current:
            _selected_layers(current["layers"])
        if "surface_layers" in current:
            _surface_scope(current["surface_layers"])
        if current.get("via", "local") not in KERNELS:
            raise ValueError("unknown propagation choice")
        for key in ("order", "steps"):
            if key in current and (type(current[key]) is not int or current[key] < 0):
                raise ValueError(f"{key} must be a nonnegative integer")
        for key in ("beam", "limit", "page_size"):
            if key in current and (type(current[key]) is not int or current[key] < 1):
                raise ValueError(f"{key} must be a positive integer")
        if (current.get("order", 0) > RECALL_SURFACE_BUDGET.hard_max_order
                or current.get("page_size", RECALL_SURFACE_BUDGET.page_size) > RECALL_SURFACE_BUDGET.page_size):
            raise ValueError("encounter order and page_size must fit the existing Surface budget")
        if "compact" in current and type(current["compact"]) is not bool:
            raise ValueError("compact must be a boolean")
        files[Path("access/encounter.json")] = (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode()
    layers = tuple(current.get("layers", cursor["layers"])) if replacement is not None else tuple(cursor["layers"])
    surface = tuple(current.get("surface_layers", cursor["surface_layers"])) if replacement is not None else tuple(cursor["surface_layers"])
    budget = ContentBudgetPolicy.from_mapping(plan["content_budget"]) if "content_budget" in plan else None
    return files, layers, surface, budget


def reorganize(field, cursor, plan):
    """Apply one explicit local plan; retain evidence and report actual readback.

Changes use action new/revise/reuse/move/forget, target an observed fact or cell,
and carry id/text/sources for a new expression. A move uses `to` for its cell.
Optional readback entries contain id and a physical path; common observed paths
are inferred mechanically. Configuration updates are part of the same batch.
"""
    field = Path(field)
    if cursor.get("field") != str(field.resolve()) or "entry" not in cursor:
        raise ValueError("reorganization needs an encounter in this field with one selected entry")
    if not isinstance(plan, dict) or set(plan) - {"schema_version", "changes", "readback", "content_budget", "encounter"}:
        raise ValueError("invalid local reorganization plan")
    if plan.get("schema_version") != SCHEMA_VERSION or not isinstance(plan.get("changes"), list) or not plan["changes"]:
        raise ValueError("local reorganization requires its schema version and changes")
    observed_items = {item["id"]: item for item in cursor.get("observed_items", ())}
    observed_cells = {item["id"]: item for item in cursor.get("observed_cells", ())}
    configuration_files, writable_layers, surface_layers, budget = _configuration(field, cursor, plan)
    observations = [*observed_items.values(), *observed_cells.values()]
    roots = {_cell(cursor["entry"])}
    roots.update(_cell(item["cell"]) for item in observations if item["cell"][0] in surface_layers)
    roots = {cell for cell in roots if cell.layer in surface_layers}
    if not roots:
        raise ValueError("the proposed Surface needs an observed physical entrance")

    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        # Serialize the complete Host operation with the existing Access owner.
        # Public Access calls acquire their own Core lease, which is not reentrant.
        with access.reorganization_scope():
            current = {note_id: AtomHandle.from_mapping(item["handle"])
                       for note_id, item in observed_items.items()}
            checked_current = set()

            def require_current(note_id):
                if note_id in checked_current or note_id not in observed_items:
                    return
                handle = AtomHandle.from_mapping(observed_items[note_id]["handle"])
                try:
                    binding = access.handle_store.binding_for_handle(handle)
                    core.get(handle)
                except KeyError as error:
                    raise ValueError("an observed fact moved or was removed; reopen the locality") from error
                if binding.current_statement_id != note_id:
                    raise ValueError("an observed fact was revised; reopen the locality")
                checked_current.add(note_id)
            decisions, statements, effects = [], [], []
            changed_ids = set()
            cell_delta = defaultdict(int)
            policy = budget if budget is not None else access.content_budget

            def destination(cell_id):
                observation = observed_cells.get(cell_id)
                if observation is None or not observation.get("writable"):
                    raise ValueError("choose a writable cell observed with prepare-write")
                cell = _cell(observation["cell"])
                if cell.layer not in writable_layers:
                    raise ValueError("target is outside the final writable layers")
                if policy is not None and policy.limits_for(cell) is None:
                    raise ValueError(f"configure the content budget for layer {cell.layer}")
                return cell

            for number, change in enumerate(plan["changes"]):
                if not isinstance(change, dict) or set(change) - {"action", "target", "to", "id", "text", "sources", "reason"}:
                    raise ValueError("invalid local change")
                action = change.get("action")
                if action not in {"new", "revise", "reuse", "move", "forget"}:
                    raise ValueError("unknown local reorganization action")
                target = change.get("target")
                old_handle = None
                target_cell = None
                if action == "new":
                    target_cell = destination(target)
                else:
                    if target not in current:
                        raise ValueError("choose an observed current fact or a current result of this batch")
                    require_current(target)
                    old_handle = current[target]
                    if old_handle.geometry_address.layer not in writable_layers:
                        raise ValueError("fact is outside the final writable layers")
                    if action == "move":
                        target_cell = destination(change.get("to"))
                if action in {"new", "revise", "reuse"}:
                    note_id, text, sources = change.get("id"), change.get("text"), change.get("sources")
                    if not isinstance(sources, list) or not sources or any(not isinstance(ref, str) or not ref for ref in sources):
                        raise ValueError("new expressions need the actually read source references")
                    references = list(sources[1:])
                    if action in {"revise", "reuse"}:
                        references.append(f"{'revises' if action == 'revise' else 'reuses'}:{target}")
                    statements.append(MemoryStatement(note_id, text, sources[0], tuple(references)))
                else:
                    note_id = target
                if action == "new":
                    handle = AtomHandle(target_cell, note_id)
                    current[note_id] = handle
                    checked_current.add(note_id)
                    cell_delta[target_cell] += 1
                    changed_ids.add(note_id)
                elif action == "revise":
                    handle = old_handle
                    del current[target]
                    current[note_id] = handle
                    checked_current.add(note_id)
                    changed_ids.discard(target)
                    changed_ids.add(note_id)
                elif action == "move":
                    handle = AtomHandle(target_cell, old_handle.local_atom_id)
                    current[target] = handle
                    cell_delta[old_handle.geometry_address] -= 1
                    cell_delta[target_cell] += 1
                    changed_ids.add(target)
                elif action == "forget":
                    handle = old_handle
                    del current[target]
                    cell_delta[old_handle.geometry_address] -= 1
                    changed_ids.discard(target)
                else:
                    handle = old_handle
                    changed_ids.add(target)
                decisions.append(AccessDecision(
                    f"local-reform-{number}", note_id,
                    "revision_current" if action == "revise" else action,
                    existing_handle=old_handle, target_cell=target_cell,
                    reason_text=change.get("reason") or f"Host selected {action} in the observed locality.",
                    write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
                ))
                effects.append({"action": action, "id": note_id, "cell": coords(handle.geometry_address)})

            checks = []
            explicit = plan.get("readback", [])
            if not isinstance(explicit, list):
                raise ValueError("readback must be a list")
            checked_ids = set()
            for request in explicit:
                if not isinstance(request, dict) or set(request) != {"id", "path"} or request["id"] not in current:
                    raise ValueError("readback must name a final current expression and its path")
                note_id = request["id"]
                require_current(note_id)
                path = _validate_path(request["path"], current[note_id].geometry_address, roots)
                checks.append((note_id, path))
                checked_ids.add(note_id)
            for note_id in sorted(changed_ids - checked_ids):
                path = _observed_route(current[note_id].geometry_address, observations, roots)
                checks.append((note_id, path))
            for _, path in checks:
                if len(core.atoms_at(path[0])) + cell_delta[path[0]] <= 0:
                    raise ValueError("a required Surface entrance would have no stored judgment")
            for layer in set(writable_layers) - set(cursor["layers"]):
                if policy is not None and policy.limits_for(address(layer, 0, 0)) is None:
                    raise ValueError(f"new writable layer {layer} requires its content budget")

            access.reorganize(tuple(decisions), statements=tuple(statements),
                              content_budget=budget, configuration_files=configuration_files)
            readback = []
            for note_id, path in checks:
                # Recheck the real forward edges after the accepted change, then
                # consume the terminal physical cell through normal Access recall.
                _validate_path([coords(cell) for cell in path], current[note_id].geometry_address, roots)
                count = max(1, len(core.atoms_at(path[-1])))
                result = access.recall(AccessRecallRequest(
                    "local-reform-readback", (path[-1],), budget=RecallBudget(0, 1, 0, 0, 0, count)))
                hit = next((item for item in result.items if item.statement_id == note_id), None)
                if hit is None or hit.fallback_error:
                    raise RuntimeError(f"committed reorganization needs readback inspection: {note_id}")
                readback.append({"id": note_id, "path": [coords(cell) for cell in path],
                                 "text": hit.evidence_utf8, "current": True})
    return {"kind": "result", "effect": "reorganize", "entry": cursor["entry"],
            "changes": effects, "readback": readback, "commit_state": "committed",
            "readback_scope": "changed_current_and_explicit_paths",
            "configuration_updated": bool(configuration_files) or budget is not None}
