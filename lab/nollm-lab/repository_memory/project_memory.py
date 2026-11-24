"""Project memory. The calling model authors text and chooses cells."""
import argparse
from dataclasses import asdict
from itertools import islice
import json
from pathlib import Path
import sys

from nollm_access import (
    ACTIVE_SEMANTIC_WRITE_POLICY_ID, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
    RECALL_SURFACE_BUDGET, AccessDecision, AccessRecallRequest, AccessRuntime,
    FileHandleStore, FileStatementStore, MemoryStatement, semantic_write_policy, write_pressure,
)
from nollm_core import (
    AtomHandle, BridgeSpec, CoreRuntime, GeometryAnchor, JunctionRequest, PhysicalFieldScope,
    RecallBudget, UnsupportedPhysicalCoverage, expand_physical_coverage, incoming_coverage,
)

from coverage_cli import address, coords, require_field, surface
from repo_notes import _commit, _git


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
KERNELS = {
    "local": ("coverage_down", "coverage_up", "lateral"),
    "connected": ("bridge", "coverage_down", "coverage_up", "lateral"),
    "vertical": ("coverage_down", "coverage_up"),
    "downward": ("coverage_down",),
    "lateral": ("lateral",),
}


def save(field, repo, rev, note_id, body, citations, at, revise, reuse=None, *,
         layer=0, write_policy_id=ACTIVE_SEMANTIC_WRITE_POLICY_ID):
    commit = _commit(repo, rev)
    return save_statement(field, note_id, body, [f"{commit}:{citation}" for citation in citations],
                          at, revise, reuse, layer=layer, write_policy_id=write_policy_id)


def save_statement(field, note_id, body, sources, at, revise, reuse=None, *,
                   layer=0, write_policy_id=ACTIVE_SEMANTIC_WRITE_POLICY_ID):
    """Save Host-authored understanding with already selected, pinned source references."""
    if sum(choice is not None for choice in (at, revise, reuse)) != 1:
        raise ValueError("choose exactly one of at, revise, or reuse")
    primary, *others = sources
    with CoreRuntime(field) as core, AccessRuntime(
        core, FileStatementStore(field), FileHandleStore(field)
    ) as access:
        if at is not None:
            decision = AccessDecision(note_id, note_id, "new", target_cell=address(layer, *at),
                                      reason_text="Host selected this cell for a distinct proposition.",
                                      write_policy_id=write_policy_id)
        else:
            current_id = revise if revise is not None else reuse
            existing_handle = access.saved_handle(current_id)
            if access.handle_store.statement_for_handle(existing_handle) != current_id:
                raise ValueError("revise and reuse require the current statement ID")
            if revise is not None:
                action = "revision_current"
                reason = f"Host supersedes {revise} in the same proposition slot."
                others.append(f"revises:{revise}")
            else:
                action = "reuse"
                reason = f"Host confirms this expression supports the current judgment {reuse}."
                others.append(f"reuses:{reuse}")
            decision = AccessDecision(note_id, note_id, action, existing_handle=existing_handle,
                                      reason_text=reason, write_policy_id=write_policy_id)
        handle, = access.reorganize((decision,), statements=(
            MemoryStatement(note_id, body, primary, tuple(others)),
        ))
    result = {"id": note_id, "cell": coords(handle.geometry_address), "revises": revise}
    if reuse is not None:
        result["reuses"] = reuse
    return result


def describe(field, note_id):
    statement = FileStatementStore(field).get(note_id)
    bindings = FileHandleStore(field)
    try:
        current = bindings.statement_for_handle(bindings.get(note_id)) == note_id
    except KeyError:
        current = False
    result = _statement_description(statement, current)
    if not current:
        result["continuation"] = _revision_continuation(field, statement)
    return result


def _statement_description(statement, current):
    sources = [statement.source_handle]
    result = {"id": statement.statement_id, "text": statement.content_utf8, "sources": sources,
              "current": current}
    for ref in statement.context_refs:
        if ref.startswith("revises:"):
            result["revises"] = ref.removeprefix("revises:")
        elif ref.startswith("reuses:"):
            result["reuses"] = ref.removeprefix("reuses:")
        else:
            sources.append(ref)
    return result


def _revision_continuation(field, statement):
    """Locate the current native revision slot without replacing old evidence."""
    store = FileStatementStore(field)
    cache = {statement.statement_id: statement}

    def chain(note_id, stop_at=None):
        seen = set()
        while note_id not in seen:
            seen.add(note_id)
            if note_id == stop_at:
                return seen, False
            try:
                if note_id not in cache:
                    cache[note_id] = store.get(note_id)
                parents = {ref.removeprefix("revises:") for ref in cache[note_id].context_refs
                           if ref.startswith("revises:")}
            except (FileNotFoundError, TypeError, ValueError, UnicodeError):
                return seen, True
            if not parents:
                return seen, False
            if len(parents) != 1 or "" in parents:
                return seen, True
            note_id = next(iter(parents))
        return seen, True

    ancestors, incomplete = chain(statement.statement_id)
    candidates = []
    for binding in FileHandleStore(field).bindings_for_atom_ids(tuple(ancestors)):
        lineage, unresolved = chain(binding.current_statement_id, statement.statement_id)
        if statement.statement_id in lineage and not unresolved:
            candidates.append({"id": binding.current_statement_id,
                               "cell": coords(binding.handle.geometry_address)})
        else:
            incomplete = incomplete or unresolved
    status = ("incomplete" if incomplete else "ambiguous" if len(candidates) > 1
              else "unique" if candidates else "not_found")
    return {"scope": "native_revision_slot", "status": status, "candidates": candidates}


def excerpt(repo, reference):
    blob, fragment = reference.rsplit("#L", 1)
    start, _, end = fragment.partition("-L")
    first, last = int(start), int(end or start)
    lines = _git(repo, "show", blob).decode("utf-8").splitlines()
    if not 1 <= first <= last <= len(lines):
        raise ValueError(f"line window outside source: {reference} ({len(lines)} lines)")
    return "\n".join([reference, *(f"{n}\t{lines[n-1]}" for n in range(first, last + 1))])


def stitch(field, link_id, from_id, to_id):
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        origin = access.saved_handle(from_id).geometry_address
        target = access.saved_handle(to_id).geometry_address
        link = BridgeSpec(link_id, GeometryAnchor("from", (origin,)), GeometryAnchor("to", (target,)),
                          1 << 15, "normal", 1, 1)
        access.apply(AccessDecision(link_id, from_id, "stitch", bridge_spec=link,
                                    reason_text=f"Host connects the cells of {from_id} and {to_id}."))
        return {"id": link_id, "from": coords(origin), "to": coords(target)}


def unstitch(field, link_id):
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        link = {b.bridge_id: b for b in core.bridges()}[link_id]
        access.apply(AccessDecision(link_id, link_id, "unstitch", bridge_spec=link,
                                    reason_text=f"Host withdraws {link_id}."))
        return {"removed": link_id}


def links(field, link_id=None):
    """Read current native bridges, optionally selecting one known link ID."""
    require_field(field)
    with CoreRuntime(field) as core:
        return [link.to_mapping() for link in core.bridges()
                if link_id is None or link.bridge_id == link_id]


def _storage_components(field):
    """Inspect physical layout without opening runtimes or replaying recovery."""
    return {"core": CoreRuntime.inspect_storage(field),
            "bindings": FileHandleStore.inspect_storage(field)}


def storage(field, *, enable_paged=False, partition_width=64):
    """Inspect storage or explicitly migrate the two independent components."""
    field = Path(field)
    require_field(field)
    before = _storage_components(field)
    result = {"kind": "storage", "field": str(field.resolve()), "status": "observed", **before}
    if not enable_paged:
        return result
    if type(partition_width) is not int or partition_width <= 0:
        raise ValueError("partition width must be a positive integer")
    migrations = {"core": "not_attempted", "bindings": "not_attempted"}
    stage = "open"
    try:
        with CoreRuntime(field) as core, AccessRuntime(
            core, FileStatementStore(field), FileHandleStore(field)
        ) as access:
            with access.reorganization_scope():
                stage = "core"
                core.enable_paged_storage(partition_width=partition_width)
                migrations[stage] = "already_paged" if before[stage]["layout"] == "paged" else "migrated"
                stage = "bindings"
                access.handle_store.enable_paged_storage(partition_width=partition_width)
                migrations[stage] = "already_paged" if before[stage]["layout"] == "paged" else "migrated"
    except Exception as error:
        if stage in migrations:
            migrations[stage] = "failed"
        result["status"] = ("partial" if any(value in {"migrated", "already_paged"}
                                               for value in migrations.values()) else "failed")
        result["error"] = {"component": stage, "type": type(error).__name__, "message": str(error)}
        result["retry"] = f"storage --enable-paged --partition-width {partition_width}"
    else:
        result["status"] = "completed"
    for name, component in _storage_components(field).items():
        result[name] = {**component, "migration": migrations[name]}
    return result


def walk(field, choices, order, page_size, steps, limit, via, cursor=None, with_cursor=False, beam=16):
    page = surface(field, SCOPE, order, choices, page_size, RECALL_SURFACE_BUDGET.max_calls, cursor, with_cursor)
    if page["kind"] != "entry":
        # The first line is the Host's cue; expand the body after choosing a cell.
        for candidate in page["candidates"]:
            titles = [preview.splitlines()[0] for preview in candidate["previews"]]
            candidate["text_truncated"] = candidate["text_truncated"] or titles != candidate["previews"]
            candidate["previews"] = titles
        return page
    return {**page, **_locality(field, address(*page["entry"]), steps, limit, via, beam)}


def _selected_layers(layers):
    selected = tuple(sorted(set(layers)))
    if not selected:
        raise ValueError("choose at least one physical layer")
    for layer in selected:
        address(layer, 0, 0)
    return selected


def _surface_scope(layers):
    selected = _selected_layers(layers)
    reference = 0 if 0 in selected else selected[len(selected) // 2]
    return PhysicalFieldScope("default_dream_v1", "default", selected, reference)


def _writing_scope(layers, focus):
    """Use only the configured layers adjacent to this observed physical focus."""
    selected = tuple(layer for layer in layers if abs(layer - focus.layer) <= 1)
    if not selected:
        return None
    reference = focus.layer if focus.layer in selected else selected[0]
    return PhysicalFieldScope("default_dream_v1", "default", selected, reference)


def _placement_cells(core, entry, recall_items, scope):
    if scope is None:
        return []
    cells = {entry, *(hit.handle.geometry_address for hit in recall_items
                      if scope.contains(hit.handle.geometry_address))}
    if scope.contains(entry):
        cells.update(candidate.cell for candidate in core.junction_candidates(JunctionRequest(scope, (entry,))))
    for direction, target_layer in (("coverage_up", entry.layer - 1),
                                     ("coverage_down", entry.layer + 1)):
        if target_layer in scope.physical_layers:
            cells.update(member.target for member in expand_physical_coverage(entry, direction).members)
    if entry.layer + 1 in scope.physical_layers:
        # Up support is not the reciprocal of the parent's down sample list.
        cells.update(member.source for member in incoming_coverage(entry).members)
    radius = semantic_write_policy(EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID).active_writable_hex_radius
    return sorted((cell for cell in cells if scope.contains(cell)
                   and max(abs(cell.q), abs(cell.r), abs(cell.q + cell.r)) <= radius),
                  key=lambda cell: cell.stable_key())


def _locality(field, entry, steps, limit, via, beam, *, placement=False, scope=SCOPE,
              pressure=False, describe_items=False, descent=False):
    kernels = KERNELS[via]
    budget = RecallBudget(steps, beam, steps, 1, int("bridge" in kernels), limit)
    with CoreRuntime(field) as core, AccessRuntime(
        core, FileStatementStore(field), FileHandleStore(field)
    ) as access:
        recall = access.recall(AccessRecallRequest(
            "project-memory", (entry,), allowed_kernels=kernels,
            budget=budget,
        ))
        items = []
        for hit in recall.items:
            if hit.fallback_error:
                raise RuntimeError(hit.fallback_error)
            item = {"id": hit.statement_id, "cell": coords(hit.handle.geometry_address),
                    "via": hit.path, "text": hit.evidence_utf8}
            if describe_items:
                statement = hit.statement or access.statement_store.get(hit.statement_id)
                item.update(_statement_description(statement, True))
                item["_handle"] = hit.handle.to_mapping()
            items.append(item)
        result = {"kernels": kernels, "items": items, "budget": asdict(budget),
                  "budget_exhausted": recall.budget_exhausted}
        if descent or placement:
            with core.operation_lease():
                units = {}

                def units_at(cell):
                    if cell not in units:
                        units[cell] = tuple(handle for handle, _ in core.atoms_at(cell))
                    return units[cell]

                try:
                    downward = expand_physical_coverage(entry, "coverage_down").members
                except UnsupportedPhysicalCoverage as error:
                    downward = ()
                    result["descent_error"] = str(error)
                down_cells = {member.target for member in downward}
                result["descent_candidates"] = [
                    {"id": f"cell:{member.target.layer}:{member.target.q}:{member.target.r}",
                     "cell": coords(member.target), "native_atoms": len(units_at(member.target)),
                     "weight_q16": member.weight_q16}
                    for member in downward
                ]
                result["cells"] = []
                if placement:
                    for cell in _placement_cells(core, entry, recall.items, scope):
                        candidate = {"id": f"cell:{cell.layer}:{cell.q}:{cell.r}",
                                     "cell": coords(cell), "native_atoms": len(units_at(cell)),
                                     "readable_downward": cell in down_cells,
                                     "at_focus": cell == entry,
                                     "content_budget_configured": (access.content_budget is None or
                                         access.content_budget.limits_for(cell) is not None)}
                        if pressure:
                            candidate["write_pressure"] = write_pressure(cell, units_at).to_mapping()
                        result["cells"].append(candidate)
    return result


def _encounter_defaults(field):
    """Field-local physical scopes and ordinary observation defaults."""
    path = field / "access/encounter.json"
    if not path.exists():
        return {}
    defaults = json.loads(path.read_text(encoding="utf-8"))
    allowed = {"surface_layers", "layers", "order", "page_size", "steps", "limit", "via", "beam", "compact"}
    if not isinstance(defaults, dict) or set(defaults) - allowed:
        raise ValueError("encounter.json must contain only physical scopes and encounter defaults")
    if "via" in defaults and defaults["via"] not in KERNELS:
        raise ValueError("encounter.json has an unknown propagation choice")
    return defaults


def _compact_locality(locality):
    """Project a newly read locality without changing text or selectable IDs."""
    for item in locality["items"]:
        sources = item["sources"]
        item["source_count"] = len(sources)
        item["sources_truncated"] = len(sources) > 1
        item["sources"] = sources[:1]
    pressure_fields = ("pressure", "write_weight", "advisory", "score_kind",
                       "support_complete", "demand_complete")
    for cell in locality.get("cells", ()):
        pressure = cell.get("write_pressure")
        if pressure is None:
            continue
        projected = {name: pressure[name] for name in pressure_fields}
        for name in ("unknown_cells", "geometry_error"):
            if pressure[name]:
                projected[name] = pressure[name]
        cell["write_pressure"] = projected


def encounter(field, choices=(), *, order=None, page_size=None, steps=None, limit=None,
              via=None, beam=None, cursor=None, layers=None, surface_layers=None,
              descend=None, ascend=False, compact=None, prepare_write=None, pressure=None):
    """Observe one field for either a query or an incoming proposition.

    The disposable cursor retains the shown page or the chosen physical entry.
    Reopening a locality may change its budget, while keeping that same entry.
    Surface layers select the entrance. Writable layers constrain mutations.
    A focus descends one actual Coverage edge within that same rooted encounter.
    """
    field = Path(field)
    state = dict(cursor) if cursor is not None else {"field": str(field.resolve())}
    if state["field"] != str(field.resolve()):
        raise ValueError("encounter cursor belongs to another field")
    defaults = _encounter_defaults(field) if cursor is None else {}
    selected_layers = _selected_layers(layers if layers is not None else state.get("layers", defaults.get("layers", (0,))))
    if cursor is not None and layers is not None and selected_layers != tuple(state.get("layers", (0,))):
        raise ValueError("restart the encounter to change physical layers")
    selected_surface = (surface_layers if surface_layers is not None else
                        state.get("surface_layers", defaults.get("surface_layers", selected_layers)))
    surface_scope = _surface_scope(selected_surface)
    if cursor is not None and surface_layers is not None and surface_scope.physical_layers != tuple(state.get("surface_layers", state.get("layers", (0,)))):
        raise ValueError("restart the encounter to change Surface layers")
    state["layers"] = list(selected_layers)
    state["surface_layers"] = list(surface_scope.physical_layers)
    write_policy_id = (ACTIVE_SEMANTIC_WRITE_POLICY_ID if selected_layers == (0,)
                       else EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
    for name, value, default in (("steps", steps, 1), ("limit", limit, 5),
                                  ("via", via, "local"), ("beam", beam, 16),
                                  ("compact", compact, False)):
        state[name] = value if value is not None else state.get(name, defaults.get(name, default))
    if state["via"] not in KERNELS:
        raise ValueError("unknown propagation choice")
    if not isinstance(state["compact"], bool):
        raise ValueError("compact must be a boolean")
    for name, value in (("prepare_write", prepare_write), ("pressure", pressure)):
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{name} must be a boolean")
        state[name] = value if value is not None else state.get(name, False)
    if prepare_write is False and pressure is True:
        raise ValueError("choose read-only observation or write pressure")
    if pressure is True:
        state["prepare_write"] = True
    if not state["prepare_write"]:
        state["pressure"] = False
    if descend is not None or ascend:
        if "entry" not in state or choices or (descend is not None and ascend):
            raise ValueError("choose one observed locality before descending or returning")
    if "entry" in state:
        if choices:
            raise ValueError("encounter already has one physical entry; restart to choose another")
    elif state.get("seed"):
        # An empty Surface offers the Core origin as a physical entry. The Host
        # still chooses it before seeing facts and placement targets.
        with CoreRuntime(field) as core:
            candidate = core.junction_candidates(JunctionRequest(surface_scope, (), candidate_limit=1))[0]
        if not choices:
            return {"kind": "physical", "surface_calls": state["surface_calls"],
                    "candidates": [{"id": candidate.candidate_id, "physical_cell": coords(candidate.cell),
                                    "native_atoms": 0, "previews": [], "truncated": False,
                                    "text_truncated": False}],
                    "surface_layers": list(surface_scope.physical_layers),
                    "physical_layers": list(selected_layers),
                    "compact": state["compact"], "cursor": state}
        if list(choices) != [candidate.candidate_id]:
            raise ValueError("choose the shown empty-field physical entry")
        state.pop("seed")
        state["entry"] = coords(candidate.cell)
    else:
        # Opening a new workspace uses Core's ordinary empty-state persistence.
        if cursor is None and not (field / "core/current_state.json").exists():
            with CoreRuntime(field):
                pass
        page = surface(field, surface_scope, order if order is not None else defaults.get("order"), choices,
                       page_size if page_size is not None else defaults.get("page_size"), RECALL_SURFACE_BUDGET.max_calls,
                       state.get("surface"), True, resolve_singletons=True)
        state["surface_calls"] = page["surface_calls"]
        if page["kind"] != "entry":
            state["surface"] = page.pop("cursor")
            if not page["candidates"] and page.get("start", {}).get("root_cells") == 0:
                state.pop("surface")
                state["seed"] = True
                return encounter(field, cursor=state)
            # Keep Access's stored-statement excerpts. Full bodies arrive in the
            # locality; text_truncated reports clipped text, while truncated
            # reports omitted statements.
            return {**page, "surface_layers": list(surface_scope.physical_layers),
                    "physical_layers": list(selected_layers),
                    "compact": state["compact"], "cursor": state}
        state.pop("surface", None)
        state["entry"] = page["entry"]
    focus = state.get("focus", state["entry"])
    focus_path = state.get("focus_path", [state["entry"]])
    if descend is not None:
        selected = next((item for item in state.get("descent_candidates", ()) if item["id"] == descend), None)
        if selected is None:
            raise ValueError("choose a descent candidate shown in this locality")
        target = address(*selected["cell"])
        if target not in {member.target for member in expand_physical_coverage(address(*focus), "coverage_down").members}:
            raise ValueError("descent must follow one adjacent coverage_down edge")
        focus = coords(target)
        focus_path = [*focus_path, focus]
    elif ascend:
        if len(focus_path) == 1:
            raise ValueError("already at the original physical entry")
        focus_path = focus_path[:-1]
        focus = focus_path[-1]
    state["focus"], state["focus_path"] = focus, focus_path
    scope = _writing_scope(selected_layers, address(*focus))
    locality = _locality(field, address(*focus), state["steps"], state["limit"],
                         state["via"], state["beam"], placement=state["prepare_write"],
                         pressure=state["pressure"], scope=scope, describe_items=True, descent=True)
    observed_items = {item["id"]: item for item in state.get("observed_items", ())}
    for item in locality["items"]:
        item["entry_path"] = ("coverage_down",) * (len(focus_path) - 1) + tuple(item["via"])
        observed_items[item["id"]] = {"id": item["id"], "cell": item["cell"],
                                     "handle": item.pop("_handle"), "focus_path": focus_path,
                                     "via": list(item["via"])}
    state["observed_items"] = list(observed_items.values())
    observed_cells = {item["id"]: item for item in state.get("observed_cells", ())}
    for item in locality["descent_candidates"]:
        previous = observed_cells.get(item["id"], {})
        observed_cells[item["id"]] = {**previous, "id": item["id"], "cell": item["cell"],
                                      "focus_path": focus_path, "readable_downward": True,
                                      "writable": previous.get("writable", False)}
    for item in locality["cells"]:
        observed_cells[item["id"]] = {"id": item["id"], "cell": item["cell"],
                                      "focus_path": focus_path, "writable": True,
                                      "readable_downward": item["readable_downward"],
                                      "at_focus": item["at_focus"],
                                      "content_budget_configured": item["content_budget_configured"]}
    state["observed_cells"] = list(observed_cells.values())
    if state["compact"]:
        _compact_locality(locality)
    state["descent_candidates"] = [{"id": item["id"], "cell": item["cell"]}
                                   for item in locality["descent_candidates"]]
    return {"kind": "locality", "entry": state["entry"], "surface_calls": state["surface_calls"],
            "focus": focus, "focus_path": focus_path,
            "surface_layers": list(surface_scope.physical_layers),
            "physical_layers": list(selected_layers), "write_policy_id": write_policy_id,
            "compact": state["compact"], "write_prepared": state["prepare_write"],
            "pressure_requested": state["pressure"],
            "local_writable_layers": list(scope.physical_layers) if scope else [],
            **locality, "cursor": state}


def _recall_observed(field, cursor, target):
    observed = next((item for item in cursor.get("observed_items", ()) if item["id"] == target), None)
    if observed is None:
        # Older cursors and a just-written fact may not have an observation yet.
        # Reopen only the reading path; no placement or pressure work is needed.
        locality = encounter(field, cursor=cursor, prepare_write=False, pressure=False)
        found = next((item for item in locality["items"] if item["id"] == target), None)
        if found is None:
            raise ValueError("choose a current fact shown in this locality")
        return found
    handle = AtomHandle.from_mapping(observed["handle"])
    with CoreRuntime(field) as core, AccessRuntime(
        core, FileStatementStore(field), FileHandleStore(field)
    ) as access:
        try:
            binding = access.handle_store.binding_for_handle(handle)
            atom = core.get(handle)
        except KeyError as error:
            raise ValueError("observed current fact moved or was removed; reopen the locality") from error
        if binding.current_statement_id != target:
            raise ValueError("observed current fact was revised; reopen the locality")
        statement = access.statement_store.get(target)
        if statement.content_utf8 != atom.payload_utf8:
            raise RuntimeError("evidence_payload_mismatch")
    item = {**_statement_description(statement, True), "cell": coords(handle.geometry_address),
            "via": tuple(observed["via"]),
            "entry_path": ("coverage_down",) * (len(observed["focus_path"]) - 1) + tuple(observed["via"])}
    if cursor.get("compact"):
        _compact_locality({"items": [item], "cells": []})
    return item


def decide(field, cursor, action, target=None, *, note_id=None, body=None, sources=None):
    """Apply the Host's terminal choice in its observed, current locality."""
    result = {"kind": "result", "effect": action, "entry": cursor.get("entry"),
              "focus": cursor.get("focus", cursor.get("entry")),
              "focus_path": cursor.get("focus_path", [cursor["entry"]] if "entry" in cursor else [])}
    if action == "defer":
        return result
    if "entry" not in cursor:
        raise ValueError("choose one physical entry before a terminal decision")
    if action == "none":
        return result
    if action == "recall":
        return {**result, "item": _recall_observed(field, cursor, target)}
    if action == "new" and not cursor.get("prepare_write"):
        raise ValueError("prepare writing before choosing a placement cell")
    locality = encounter(field, cursor=cursor, prepare_write=action == "new", pressure=False)
    if action in {"reuse", "revision"}:
        found = next((item for item in locality["items"] if item["id"] == target), None)
        if found is None:
            raise ValueError("choose a current fact shown in this locality")
        if found["cell"][0] not in locality["local_writable_layers"]:
            raise ValueError("choose a fact in the encounter's local writable layers")
        at, revise, reuse = None, target if action == "revision" else None, target if action == "reuse" else None
    elif action == "new":
        cell = next((item for item in locality["cells"] if item["id"] == target), None)
        if cell is None:
            raise ValueError("choose a placement cell shown in this locality")
        if cursor.get("via", "local") == "downward" and not (cell["at_focus"] or cell["readable_downward"]):
            raise ValueError("this placement has no downward read path from the current focus; "
                             "use reorganization with an actual readable path")
        if not cell["content_budget_configured"]:
            raise ValueError(f"configure a content budget for layer {cell['cell'][0]} before writing there")
        at, revise, reuse = cell["cell"][1:], None, None
    else:
        raise ValueError(f"unknown encounter decision: {action}")
    if not note_id or not body or not sources:
        raise ValueError("a new expression needs an ID, body, and source references")
    saved = save_statement(field, note_id, body, sources, at, revise, reuse,
                           layer=cell["cell"][0] if action == "new" else 0,
                           write_policy_id=locality["write_policy_id"])
    return {**result, **saved}


def literal_matches(field, term):
    """Auxiliary scan of current statements. No geometry entry is selected here."""
    require_field(field)
    term = term.casefold()
    with CoreRuntime(field) as core:
        handles = tuple(handle for cell in core.occupied_cells() for handle, _ in core.atoms_at(cell))
        bindings = FileHandleStore(field).bindings_for_handles(handles)
        store = FileStatementStore(field)
        for binding in bindings:
            note = store.get(binding.current_statement_id)
            if term in note.statement_id.casefold() or term in note.content_utf8.casefold():
                yield {"id": note.statement_id, "preview": note.content_utf8.splitlines()[0]}


def main(argv=None, *, default_field=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, default=default_field, required=default_field is None,
                        help="native workspace (explicit for project memory)")
    commands = parser.add_subparsers(dest="op", required=True)
    browse = commands.add_parser("walk", help="observe a Surface page; selecting a physical candidate recalls its neighborhood")
    browse.add_argument("choices", nargs="*", help="successive candidate ids shown on pages, or next")
    browse.add_argument("--order", type=int, help="initial aggregation order; default: Access budget")
    browse.add_argument("--page-size", type=int, help="pin the menu width (1 to 8); default starts at 3 and plans on overflow")
    browse.add_argument("--cursor-file", type=Path, help="keep the last page here; omit choices to start a new walk")
    connect = commands.add_parser("stitch", help="add a directed native link between the current cells of two notes")
    connect.add_argument("link_id")
    connect.add_argument("from_id")
    connect.add_argument("to_id")
    disconnect = commands.add_parser("unstitch", help="remove one directed native link by ID")
    disconnect.add_argument("link_id")
    inspect_links = commands.add_parser("links", help="read native directed links, optionally by ID")
    inspect_links.add_argument("link_id", nargs="?")
    inspect_storage = commands.add_parser("storage", help="inspect storage layout or explicitly migrate to physical pages")
    inspect_storage.add_argument("--enable-paged", action="store_true",
                                 help="migrate Core and bindings independently; retry this command after a partial failure")
    inspect_storage.add_argument("--partition-width", type=int,
                                 help="geometry partition width for migration (default: 64)")
    browse.add_argument("--steps", type=int, default=1, help="kernel steps from the selected physical entry (default: 1)")
    browse.add_argument("--beam", type=int, default=16, help="maximum propagated cells per step (default: 16)")
    browse.add_argument("--limit", type=int, default=5, help="maximum returned statements after traversal (default: 5)")
    browse.add_argument("--via", choices=KERNELS, default="local")
    meet = commands.add_parser("encounter", help="share Surface, one locality and a Host decision for queries or propositions")
    meet.add_argument("choices", nargs="*", help="shown candidate IDs or next; omit to reopen the current page")
    meet.add_argument("--cursor-file", type=Path, required=True, help="disposable state for this encounter")
    meet.add_argument("--restart", action="store_true", help="start a new Surface traversal with this cursor file")
    meet.add_argument("--order", type=int, help="initial aggregation order; default: Access budget")
    meet.add_argument("--page-size", type=int, help="initial menu width; default: adaptive Surface")
    meet.add_argument("--steps", type=int, help="propagation steps; default: 1, or the current encounter budget")
    meet.add_argument("--beam", type=int, help="propagated cells per step; default: 16, or the current encounter budget")
    meet.add_argument("--limit", type=int, help="returned facts; default: 5, or the current encounter budget")
    meet.add_argument("--via", choices=KERNELS, help="propagation kernels; default: local, or the current encounter choice")
    meet.add_argument("--layers", type=int, nargs="+",
                      help="explicit experimental physical writing layers (default: 0); retained in this cursor")
    meet.add_argument("--surface-layers", type=int, nargs="+",
                      help="physical entry layers, independently of --layers; default: field configuration or writing layers")
    focus = meet.add_mutually_exclusive_group()
    focus.add_argument("--descend", metavar="CELL_ID", help="follow one shown coverage_down target within the same physical entry")
    focus.add_argument("--ascend", action="store_true", help="return one step along this encounter's observed focus path")
    detail = meet.add_mutually_exclusive_group()
    detail.add_argument("--compact", dest="compact", action="store_true", default=None,
                        help="show complete bodies, one source per fact and compact pressure fields")
    detail.add_argument("--full-details", dest="compact", action="store_false",
                        help="show all fixed sources and pressure calculation fields")
    preparation = meet.add_mutually_exclusive_group()
    preparation.add_argument("--prepare-write", dest="prepare_write", action="store_true", default=None,
                             help="show local writable candidates without calculating pressure")
    preparation.add_argument("--read-only", dest="prepare_write", action="store_false",
                             help="return to reading and descent without write diagnostics")
    pressure_option = meet.add_mutually_exclusive_group()
    pressure_option.add_argument("--pressure", dest="pressure", action="store_true", default=None,
                                 help="prepare writing and calculate advisory pressure")
    pressure_option.add_argument("--no-pressure", dest="pressure", action="store_false",
                                 help="keep local candidates but omit advisory pressure calculation")
    decision = meet.add_mutually_exclusive_group()
    decision.add_argument("--recall", metavar="FACT_ID", help="return one observed current fact")
    decision.add_argument("--reuse", metavar="FACT_ID", help="support one observed current fact")
    decision.add_argument("--revise", metavar="FACT_ID", help="supersede one observed current fact in place")
    decision.add_argument("--new", metavar="CELL_ID", help="place a distinct proposition at an observed available cell")
    decision.add_argument("--none", action="store_true", help="finish with no relevant fact")
    decision.add_argument("--defer", action="store_true", help="finish without deciding")
    decision.add_argument("--reorganize", type=Path, metavar="PLAN_JSON",
                          help="apply an explicit local reorganization plan to observed items and cells")
    meet.add_argument("--id", help="immutable statement version ID for new, reuse or revise")
    meet.add_argument("--repo", type=Path, help="source Git checkout for new, reuse or revise")
    meet.add_argument("--rev", default="HEAD", help="source revision for new citations")
    meet.add_argument("--cite", action="append", help="PATH#Lfirst-Llast (repeatable); statement body comes from stdin")
    search = commands.add_parser("find", help="case-insensitive literal in current IDs or bodies (auxiliary)")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=5)
    show = commands.add_parser("show", help="open an exact statement version and its ordered source windows")
    show.add_argument("id")
    source = commands.add_parser("source", help="expand a pinned Git source window with original line numbers")
    origin = source.add_mutually_exclusive_group(required=True)
    origin.add_argument("--id", help="use this saved version and its pinned source")
    origin.add_argument("--at", help="read PATH#Lfirst-Llast directly for formation")
    source.add_argument("--number", type=int, default=1, help="1-based source number for --id")
    write = commands.add_parser("save", help="read a model-authored statement from stdin")
    write.add_argument("id", help="new, immutable statement version ID")
    placement = write.add_mutually_exclusive_group(required=True)
    placement.add_argument("--at", type=int, nargs=2, metavar=("Q", "R"), help="host-selected cell in --layer")
    write.add_argument("--layer", type=int, default=0, help="physical layer for --at (default: 0)")
    write.add_argument("--experimental-multilayer", action="store_true",
                       help="explicitly enable the experimental multilayer write policy")
    placement.add_argument("--revise", help="ID of the current version to supersede in place")
    placement.add_argument("--reuse", help="ID of the current judgment supported by this new expression")
    write.add_argument("--cite", action="append", required=True, help="PATH#Lfirst-Llast (repeatable)")
    for command in (source, write):
        command.add_argument("--repo", type=Path, required=True, help="the source Git checkout paired with this field")
        command.add_argument("--rev", default="HEAD", help="source revision for a new citation or direct --at window")

    args = parser.parse_args(argv)
    if args.op == "save":
        result = save(args.field, args.repo, args.rev, args.id, sys.stdin.read().strip(),
                      args.cite, args.at, args.revise, args.reuse, layer=args.layer,
                      write_policy_id=(EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID
                                       if args.experimental_multilayer else ACTIVE_SEMANTIC_WRITE_POLICY_ID))
    elif args.op == "show":
        result = describe(args.field, args.id)
    elif args.op == "source":
        if args.id is None:
            reference = f"{_commit(args.repo, args.rev)}:{args.at}"
        else:
            sources = describe(args.field, args.id)["sources"]
            if not 1 <= args.number <= len(sources):
                raise IndexError(f"choose source 1..{len(sources)}")
            reference = sources[args.number - 1]
        print(excerpt(args.repo, reference))
        return
    elif args.op == "walk":
        path = args.cursor_file
        cursor = json.loads(path.read_text()) if path and args.choices else None
        result = walk(args.field, args.choices, args.order, args.page_size,
                      args.steps, args.limit, args.via, cursor, path is not None, args.beam)
        if path:
            if result["kind"] == "entry":
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(result.pop("cursor"), separators=(",", ":")))
    elif args.op == "encounter":
        path = args.cursor_file
        cursor = json.loads(path.read_text()) if path.exists() and not args.restart else None
        selected = next(((action, target) for action, target in (
            ("recall", args.recall), ("reuse", args.reuse), ("revision", args.revise),
            ("new", args.new), ("none", args.none), ("defer", args.defer),
            ("reorganize", args.reorganize),
        ) if target), None)
        if selected is not None and (cursor is None or args.choices or args.restart):
            parser.error("observe a locality with --cursor-file before choosing its outcome")
        if selected is not None and any(value is not None for value in
                                        (args.order, args.page_size, args.steps, args.beam, args.limit,
                                         args.via, args.layers, args.surface_layers, args.descend, args.compact,
                                         args.prepare_write, args.pressure)):
            parser.error("reopen the encounter with its new budget before choosing an outcome")
        if selected is not None and args.ascend:
            parser.error("observe the returned focus before choosing an outcome")
        if selected is not None and selected[0] in {"new", "reuse", "revision"}:
            if not args.id or args.repo is None or not args.cite:
                parser.error("new, reuse and revise need --id, --repo and --cite, with the body on stdin")
            sources = [f"{_commit(args.repo, args.rev)}:{citation}" for citation in args.cite]
            body = sys.stdin.read().strip()
        else:
            sources, body = None, None
        if selected is None:
            result = encounter(args.field, args.choices, order=args.order, page_size=args.page_size,
                               steps=args.steps, limit=args.limit, via=args.via, beam=args.beam, cursor=cursor,
                               layers=args.layers, surface_layers=args.surface_layers,
                               descend=args.descend, ascend=args.ascend, compact=args.compact,
                               prepare_write=args.prepare_write, pressure=args.pressure)
            path.write_text(json.dumps(result.pop("cursor"), separators=(",", ":")))
        else:
            if selected[0] == "reorganize":
                from local_reorganization import reorganize
                plan = json.loads(selected[1].read_text(encoding="utf-8"))
                result = reorganize(args.field, cursor, plan)
            else:
                result = decide(args.field, cursor, *selected,
                                note_id=args.id, body=body, sources=sources)
            path.unlink()
    elif args.op == "stitch":
        result = stitch(args.field, args.link_id, args.from_id, args.to_id)
    elif args.op == "unstitch":
        result = unstitch(args.field, args.link_id)
    elif args.op == "links":
        result = links(args.field, args.link_id)
    elif args.op == "storage":
        if args.partition_width is not None and not args.enable_paged:
            parser.error("--partition-width requires --enable-paged")
        result = storage(args.field, enable_paged=args.enable_paged,
                         partition_width=args.partition_width if args.partition_width is not None else 64)
    else:
        result = list(islice(literal_matches(args.field, args.term), args.limit))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.op == "storage" and result["status"] in {"partial", "failed"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

