"""Inspect native vertical footprints and recall checked Git notes across physical layers."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    RECALL_SURFACE_BUDGET, AccessRecallRequest, AccessRuntime, AccessSurfaceNavigator,
    FileHandleStore, FileStatementStore, PhysicalEntryPage, SurfaceTraversalState, select_active_surface,
)
from nollm_core import CoreRuntime, GeometryAddress, PhysicalFieldScope, RecallBudget, SurfaceAggregateAddress, expand_physical_coverage

from field_demo import write_field
from repo_notes import _commit, _compare, _object_id, _path, inspect_notes, read_manifest


DIRECTIONS = {"up": ("coverage_up",), "down": ("coverage_down",),
              "both": ("coverage_down", "coverage_up")}


def address(layer, q, r):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def coords(cell):
    return [cell.layer, cell.q, cell.r]


def footprint(entry, direction):
    expansions = []
    for kernel in DIRECTIONS[direction]:
        expansion = expand_physical_coverage(entry, kernel)
        expansions.append({"kernel": kernel, "method_id": expansion.method_id,
                           "sample_count": expansion.sample_count, "q16_sum": expansion.q16_sum,
                           "targets": [{"cell": coords(member.target), "hits": member.hit_count,
                                        "weight_q16": member.weight_q16} for member in expansion.members]})
    return {"entry": coords(entry), "expansions": expansions}


def build(repo, rev, manifest, field, placements):
    if field.exists() or field.is_symlink():
        raise ValueError(f"choose a new field directory: {field}")
    checked = inspect_notes(repo, read_manifest(repo, manifest), rev)
    cells = [(key, int(q), int(r)) for key, q, r in placements]
    if len({key for key, _, _ in cells}) != len(cells):
        raise ValueError("each note key needs one physical placement")
    field.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=field.parent) as tmp:
        stage = Path(tmp) / "field"
        write_field(stage, checked, cells)
        stage.rename(field)
    return {"commit": checked["commit"], "placed": len(cells)}


def git_note(statement):
    """Recognize the Git evidence convention shared by repository fields."""
    if not statement.source_handle or not statement.context_refs:
        return None
    try:
        commit, primary_path = statement.source_handle.split(":", 1)
        _object_id(commit)
        evidence = []
        for ref in statement.context_refs:
            blob, path = ref.split(":", 1)
            evidence.append({"path": _path(path), "blob": _object_id(blob)})
    except ValueError:
        return None
    if primary_path not in {ref["path"] for ref in evidence}:
        return None
    return {"key": statement.statement_id, "evidence": evidence}


def require_field(field):
    if not (field / "core" / "current_state.json").is_file():
        raise ValueError(f"native Core state missing at {field}")


def _start_surface(navigator, field, scope, order, budget, adaptive):
    # Keep narrow menus when the ordinary Access selection fits. Only plan a
    # different start when every allowed order overflowed at the narrow width.
    operation = "repository-coverage-surface"
    policy = "native" if order is None else "explicit-order"
    if adaptive:
        with CoreRuntime(field) as core:
            infos = core.surface_orders(scope, 0)
            if select_active_surface(infos, budget).overflow:
                infos = core.surface_orders(scope, budget.hard_max_order)
        selection = select_active_surface(infos, budget)
        if selection.overflow:
            permitted = infos if order is None else (infos[order],)
            for width in range(budget.page_size, RECALL_SURFACE_BUDGET.page_size + 1):
                # Root scan plus one page per descent and one physical menu.
                # Child pagination may cost extra; the estimate is not a bound.
                estimated, best_order = min(
                    ((info.occupied_cell_count + width - 1) // width + info.order + 1, info.order)
                    for info in permitted)
                if estimated <= budget.max_calls:
                    break
            if order is None:
                order = best_order
            budget = replace(budget, page_size=width)
            policy = "overflow-plan"
        elif order is None:
            order = selection.info.order
    if order is None:
        page = navigator.begin(operation, scope, budget)
    else:
        page = navigator.page(SurfaceTraversalState(operation, scope, budget, order))
    info = page.selection.info
    if info.order != page.state.order:
        with CoreRuntime(field) as core:
            info = core.surface_orders(scope, page.state.order)[-1]
    root_pages = (info.occupied_cell_count + budget.page_size - 1) // budget.page_size
    return page, {"policy": policy, "order": info.order, "root_cells": info.occupied_cell_count,
                  "root_pages": root_pages, "root_plus_descent": root_pages + info.order + 1,
                  "soft_root_pages": budget.max_pages, "active_order": page.selection.info.order,
                  "active_overflow": page.selection.overflow}


def _cursor(page):
    # IDs are formed from the count before rendering. This is enough to
    # reopen precisely the shown page, even in a different Host process.
    cursor = {"state": AccessSurfaceNavigator.state_to_mapping(
        replace(page.state, call_count=page.state.call_count - 1))}
    if page.next_after is not None:
        cursor["next_after"] = page.next_after.to_mapping()
    if isinstance(page, PhysicalEntryPage):
        cursor["physical"] = [page.source_surface_candidate_id, page.source_surface_address.to_mapping(),
                              page.after.to_mapping() if page.after else None]
    return cursor


def _resume_surface(navigator, cursor, choices):
    state = navigator.state_from_mapping(cursor["state"])
    # A sequential scan can advance directly from the native continuation.
    advance = choices and choices[0] == "next" and "next_after" in cursor
    if advance:
        state = replace(state, call_count=state.call_count + 1)
        choices = choices[1:]
    if "physical" in cursor:
        candidate, address, after = cursor["physical"]
        page = navigator.reopen_physical_entries_from_mapping(
            state, candidate, address, cursor["next_after"] if advance else after)
    else:
        if advance:
            state = replace(state, after=SurfaceAggregateAddress.from_mapping(cursor["next_after"]))
        page = navigator.page(state)
    return page, choices


def surface(field, scope, order, choices, page_size, max_calls, cursor=None, with_cursor=False):
    """Follow explicit Host choices, from the root or the last observed page."""
    require_field(field)
    navigator = AccessSurfaceNavigator(field)
    start = None
    if cursor is None:
        budget = replace(RECALL_SURFACE_BUDGET, page_size=3 if page_size is None else page_size, max_calls=max_calls)
        page, start = _start_surface(navigator, field, scope, order, budget, page_size is None)
    else:
        page, choices = _resume_surface(navigator, cursor, choices)
    for index, choice in enumerate(choices):
        physical = isinstance(page, PhysicalEntryPage)
        if choice == "next":
            page = navigator.continue_physical_entries(page) if physical else navigator.continue_page(page)
        elif physical:
            entry = navigator.select_entry(page, choice).entry_cell
            if index + 1 != len(choices):
                raise ValueError("selection already reached a physical entry")
            return {"kind": "entry", "entry": coords(entry), "surface_calls": page.state.call_count}
        elif page.state.order == 0:
            page = navigator.open_physical_entries(page, choice)
        else:
            page = navigator.open_surface_cell(page, choice)

    physical = isinstance(page, PhysicalEntryPage)
    candidates = []
    if physical:
        for cell in page.candidates:
            preview = cell.current_statement_preview
            candidates.append({"id": cell.candidate_id, "physical_cell": coords(cell.address),
                               "membership_weight_q16": cell.membership_weight_q16,
                               "native_atoms": cell.native_atom_count,
                               "previews": [preview.content_utf8] if preview else [], "truncated": cell.truncated,
                               "text_truncated": preview.text_truncated if preview else False})
    else:
        for cell in page.cells:
            candidates.append({"id": cell.candidate_id, "window": [cell.order, cell.address.q, cell.address.r],
                               "source_cells": cell.physical_source_cell_count, "native_atoms": cell.native_atom_count,
                               "previews": [s.content_utf8 for s in cell.statements], "truncated": cell.truncated,
                               "text_truncated": any(s.text_truncated for s in cell.statements)})
    result = {
        "kind": "physical" if physical else "surface", "order": page.state.order,
        "page_size": page.state.budget.page_size, "pages_left": page.state.budget.max_calls - page.state.call_count,
        "surface_calls": page.state.call_count, "has_more": page.has_more,
        "preview_basis": "stored_statement", "candidates": candidates,
    }
    if start is not None and page.state.call_count == 1:
        result["start"] = start
    if with_cursor or cursor is not None:
        result["cursor"] = _cursor(page)
    return result


def recall(repo, rev, field, entry, direction, budget):
    require_field(field)
    commit = _commit(repo, rev)
    items = []
    notes = []
    bodies = {}
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        result = access.recall(AccessRecallRequest("repository-coverage", entry_cells=(entry,),
                              allowed_kernels=DIRECTIONS[direction], budget=budget))
        for hit in result.items:
            item = {"id": hit.statement_id, "cell": coords(hit.handle.geometry_address),
                    "path": list(hit.path), "score_q16": hit.score_q16}
            items.append(item)
            if hit.fallback_error:
                item["status"] = hit.fallback_error
                continue
            statement = access.statement_store.get(hit.statement_id)
            item.update(source=statement.source_handle, context_refs=list(statement.context_refs))
            note = git_note(statement)
            if note is None:
                item["status"] = "no_git_evidence"
                continue
            notes.append(note)
            bodies[hit.statement_id] = hit.evidence_utf8
    checked = {n["key"]: n for n in _compare(repo, commit, notes)}
    for item in items:
        if "status" in item:
            continue
        note = checked[item["id"]]
        item["status"] = note["status"]
        if note["status"] == "current":
            item["text"] = bodies[item["id"]]
        else:
            item["changes"] = note["changes"]
    return {"commit": commit, "entry": coords(entry), "kernels": list(DIRECTIONS[direction]),
            "budget_exhausted": result.budget_exhausted, "items": items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="op", required=True)
    inspect_cmd = commands.add_parser("footprint", help="expand the native adjacent-layer sampling kernel")
    build_cmd = commands.add_parser("build", help="write Git notes at host-chosen layer-zero cells in a fresh field")
    read_cmd = commands.add_parser("recall", help="traverse an existing field and check reached evidence at a Git revision")
    surface_cmd = commands.add_parser("surface", help="browse native aggregation pages and choose a single physical entry")
    surface_cmd.add_argument("--field", type=Path, required=True)
    surface_cmd.add_argument("--order", type=int, help="start at this aggregation order (default: native budget selection)")
    surface_cmd.add_argument("--choose", action="append", default=[], help="append a shown candidate ID or next")
    surface_cmd.add_argument("--page-size", type=int, default=RECALL_SURFACE_BUDGET.page_size)
    surface_cmd.add_argument("--max-calls", type=int, default=RECALL_SURFACE_BUDGET.max_calls)
    surface_cmd.add_argument("--layers", nargs="+", type=int, default=[0], help="physical layers in view")
    surface_cmd.add_argument("--reference-layer", type=int, default=0)
    for cmd in (inspect_cmd, read_cmd):
        cmd.add_argument("--entry", nargs=3, type=int, required=True, metavar=("LAYER", "Q", "R"))
        cmd.add_argument("--direction", choices=DIRECTIONS, required=True)
    for cmd in (build_cmd, read_cmd):
        cmd.add_argument("--repo", type=Path, default=Path("."))
        cmd.add_argument("--rev", default="HEAD")
        cmd.add_argument("--field", type=Path, required=True)
    build_cmd.add_argument("--manifest", type=Path)
    build_cmd.add_argument("--place", nargs=3, action="append", required=True, metavar=("KEY", "Q", "R"))
    read_cmd.add_argument("--steps", type=int, default=1)
    read_cmd.add_argument("--layer-delta", type=int, help="maximum displacement from entry (defaults to steps)")
    read_cmd.add_argument("--beam", type=int, default=8)
    read_cmd.add_argument("--limit", type=int, default=16)
    args = parser.parse_args()
    try:
        if args.op == "build":
            output = build(args.repo, args.rev, args.manifest, args.field, args.place)
        elif args.op == "surface":
            scope = PhysicalFieldScope("default_dream_v1", "default", tuple(sorted(set(args.layers))),
                                       args.reference_layer)
            output = surface(args.field, scope, args.order, args.choose, args.page_size, args.max_calls)
        elif args.op == "footprint":
            output = footprint(address(*args.entry), args.direction)
        else:
            delta = args.steps if args.layer_delta is None else args.layer_delta
            budget = RecallBudget(args.steps, args.beam, delta, 0, 0, args.limit)
            output = recall(args.repo, args.rev, args.field, address(*args.entry), args.direction, budget)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
