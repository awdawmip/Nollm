"""Reopen an occupied field, browse surface windows and enter one physical cell.

Choices are zero-based ranks in the pages of the current window. Each selected
candidate must first be shown by Access. The optional audit runs after recall.
"""

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPO / "packages/nollm-core/src"), str(REPO / "packages/nollm-access/src")]

from nollm_access import (AccessRecallRequest, AccessRuntime, AccessSurfaceNavigator, FileHandleStore,
                          FileStatementStore, SurfaceBudgetProfile)
from nollm_core import CoreRuntime, GeometryAddress, PhysicalFieldScope, Q16_ONE, RecallBudget


def location(address):
    if hasattr(address, "aggregation_order"):
        return [address.aggregation_order, address.q, address.r]
    return [address.layer, address.q, address.r]


def shown_page(page, physical=False):
    visible = page.candidates if physical else page.cells
    if physical:
        previews = [[cell.current_statement_preview] if cell.current_statement_preview else [] for cell in visible]
    else:
        previews = [cell.statements for cell in visible]
    return {
        "kind": "physical" if physical else "surface",
        "call": page.state.call_count, "shown": [location(cell.address) for cell in visible],
        "previews": [[item.content_utf8 for item in group] for group in previews],
        "has_more": page.has_more,
    }


def pick(page, rank, physical, navigator, trace):
    if rank < 0:
        raise ValueError("candidate rank must be non-negative")
    while True:
        visible = page.candidates if physical else page.cells
        trace.append(shown_page(page, physical))
        if rank < len(visible):
            choice = visible[rank]
            trace[-1]["opened"] = location(choice.address)
            return page, choice
        if not page.has_more:
            raise ValueError("candidate rank exceeds the available candidates in this window")
        rank -= len(visible)
        page = navigator.continue_physical_entries(page) if physical else navigator.continue_page(page)


def walk(workspace, scope, order, ranks=(), page_size=2, max_calls=24):
    """Make host choices by shown rank, using the native operation and call budget."""
    if not (workspace / "core" / "current_state.json").is_file():
        raise ValueError("an existing native field is required")
    if not 1 <= order <= 8:
        raise ValueError("choose an observation order from 1 through 8")
    if len(ranks) > order + 2:
        raise ValueError("give one rank per surface order and one physical rank")
    ranks = (*ranks, *(0 for _ in range(order + 2 - len(ranks))))
    budget = SurfaceBudgetProfile(page_size, 1024, 1024, 1, 1, 2048, order, order, max_calls)
    navigator = AccessSurfaceNavigator(workspace)
    page = navigator.begin("repository-surface-walk", scope, budget)
    initial_order = page.state.order
    coarsening = []
    while page.state.order < order:
        coarsening.append(shown_page(page))
        page = navigator.request_coarser_surface(page)

    trace = []
    for rank in ranks[:-1]:
        page, candidate = pick(page, rank, False, navigator, trace)
        if page.state.order == 0:
            break
        page = navigator.open_surface_cell(page, candidate.candidate_id)
    entries = navigator.open_physical_entries(page, candidate.candidate_id)
    entries, candidate = pick(entries, ranks[-1], True, navigator, trace)
    entry = navigator.select_entry(entries, candidate.candidate_id).entry_cell
    recalled = navigator.recall_entry("repository-surface-recall", entry)
    statements = FileStatementStore(workspace)
    evidence = []
    for item in recalled.items:
        statement = statements.get(item["statement_id"])
        evidence.append({
            "source": statement.source_handle, "statement": statement.statement_id,
            "path": item["path"], "score_q16": item["score_q16"],
            "fallback_error": item["fallback_error"],
        })
    return {
        "initial_order": initial_order, "requested_order": order, "page_size": page_size,
        "max_surface_calls": max_calls, "surface_calls": entries.state.call_count,
        "ranks": ranks, "coarsening_pages": coarsening,
        "shown_pages": trace, "physical_entry": location(entry),
        "entry_universe_size": entries.total_candidate_count,
        "recall_budget_exhausted": recalled.budget_exhausted, "recalled": evidence,
    }


def compare_from_entry(workspace, scope, entry):
    """Hold the occupied physical origin, step/beam limits and top-k fixed."""
    address = GeometryAddress(scope.profile_id, scope.chart_id, *entry)
    budget = RecallBudget(2, 64, 2, 1, 0, 10)
    modes = {"lateral": ("lateral",), "vertical": ("coverage_down", "coverage_up")}
    statements = FileStatementStore(workspace)
    runs = {}
    with CoreRuntime(workspace) as core, AccessRuntime(core, statements, FileHandleStore(workspace)) as access:
        for name, kernels in modes.items():
            result = access.recall(AccessRecallRequest("surface-peer-" + name, (address,),
                                                       allowed_kernels=kernels, budget=budget))
            runs[name] = [{"source": statements.get(item.statement_id).source_handle,
                           "path": list(item.path), "score_q16": item.score_q16}
                          for item in result.items]
    return {"entry": entry, "budget": vars(budget), "runs": runs}


def audit_windows(workspace, scope, order):
    """Enumerate recorded windows after the walk to measure mass and shared reach."""
    statements = FileStatementStore(workspace)
    bindings = FileHandleStore(workspace)
    windows = {}
    edge_count = 0
    absent_down = 0
    with CoreRuntime(workspace) as core:
        infos = core.surface_orders(scope, order)
        after = None
        while True:
            page = core.surface_page(scope, 1, after, 256)
            for window in page.cells:
                upper = GeometryAddress(scope.profile_id, scope.chart_id, scope.reference_layer - 1,
                                        window.address.q, window.address.r)
                down = {(target.q, target.r): share for target, share
                        in core.kernel_registry.expand_coverage(upper, "coverage_down")}
                children = core.surface_descend(scope, window.address, None, 256)
                while True:
                    for child in children.cells:
                        lower = child.projection.address
                        reverse = down.get((lower.q, lower.r), 0)
                        edge_count += 1
                        absent_down += int(reverse == 0)
                        records = windows.setdefault(lower, [])
                        records.append((window.address, child.coverage_weight_q16, reverse, child.projection))
                    if not children.has_more:
                        break
                    children = core.surface_descend(scope, window.address, children.next_after, 256)
            if not page.has_more:
                break
            after = page.next_after

        shared = {address: sorted(records, key=lambda row: (-row[1], row[0].stable_key()))
                  for address, records in windows.items() if len(records) > 1}
        witness = None
        if shared:
            lower, rows = min(shared.items(), key=lambda pair: (-pair[1][1][1], pair[0].stable_key()))
            projection = rows[0][3]
            source, weight = min(projection.source_memberships,
                                 key=lambda pair: (-pair[1], pair[0].stable_key()))
            handles = tuple(handle for handle, _ in core.atoms_at(source))
            source_refs = [statements.get(binding.current_statement_id).source_handle
                           for binding in bindings.bindings_for_handles(handles)]
            witness = {
                "order_zero_window": location(lower),
                "order_one_windows": [{"address": location(address), "up_membership_q16": share,
                                       "physical_down_q16": reverse}
                                      for address, share, reverse, _ in rows],
                "physical_source": location(source), "source_to_order_zero_q16": weight,
                "current_source_refs_at_cell": source_refs,
            }
    return {
        "orders": [{"order": info.order, "windows": info.occupied_cell_count,
                    "native_atoms": info.native_atom_count, "mass_q16": info.aggregate_mass_q16}
                   for info in infos],
        "mass_conserved": all(info.aggregate_mass_q16 == infos[0].native_atom_count * Q16_ONE
                              for info in infos),
        "recorded_descent_edges": edge_count,
        "recorded_edges_absent_in_physical_down": absent_down,
        "order_zero_with_multiple_order_one_windows": len(shared),
        "order_zero_windows": len(windows), "shared_witness": witness,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--layers", type=int, nargs="+", default=[0])
    parser.add_argument("--reference-layer", type=int, default=0)
    parser.add_argument("--order", type=int, default=2)
    parser.add_argument("--ranks", type=int, nargs="*", default=[])
    parser.add_argument("--page-size", type=int, default=2)
    parser.add_argument("--max-calls", type=int, default=24)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    try:
        scope = PhysicalFieldScope("default_dream_v1", "default", tuple(sorted(set(args.layers))),
                                   args.reference_layer)
        result = walk(args.workspace, scope, args.order, args.ranks, args.page_size, args.max_calls)
        if args.audit:
            result["same_entry_comparison"] = compare_from_entry(args.workspace, scope, result["physical_entry"])
            result["after_walk_audit"] = audit_windows(args.workspace, scope, args.order)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
