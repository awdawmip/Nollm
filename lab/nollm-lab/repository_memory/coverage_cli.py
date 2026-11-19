"""Inspect native vertical footprints and recall checked Git notes across physical layers."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    RECALL_SURFACE_BUDGET, AccessRecallRequest, AccessRuntime, AccessSurfaceNavigator,
    FileHandleStore, FileStatementStore, PhysicalEntryPage, SurfaceTraversalState,
)
from nollm_core import CoreRuntime, GeometryAddress, PhysicalFieldScope, RecallBudget, expand_physical_coverage

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


def surface(field, scope, order, choices, page_size, max_calls):
    """Replay explicit page-local host choices, stopping at the first unseen page."""
    require_field(field)
    navigator = AccessSurfaceNavigator(field)
    budget = replace(RECALL_SURFACE_BUDGET, page_size=page_size, max_calls=max_calls)
    operation = "repository-coverage-surface"
    if order is None:
        page = navigator.begin(operation, scope, budget)
    else:
        page = navigator.page(SurfaceTraversalState(operation, scope, budget, order))
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
                               "previews": [preview.content_utf8] if preview else [], "truncated": cell.truncated})
    else:
        for cell in page.cells:
            candidates.append({"id": cell.candidate_id, "window": [cell.order, cell.address.q, cell.address.r],
                               "source_cells": cell.physical_source_cell_count, "native_atoms": cell.native_atom_count,
                               "previews": [s.content_utf8 for s in cell.statements], "truncated": cell.truncated})
    return {"kind": "physical" if physical else "surface", "order": page.state.order,
            "surface_calls": page.state.call_count, "has_more": page.has_more,
            "preview_basis": "stored_statement", "candidates": candidates}


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
