"""Finite forward-audit versus inverse-down cost probe using public APIs.

This research fixture expects the formed default-chart L-2/L-1/L0 field. It
compares complete finite descent (including empty intermediate cells), occupied
only descent, and on-demand real readers of changed lower cells. Candidate
bounds are independent integer algebra over public Q40 stencil values; actual
membership always uses public expand_physical_coverage. No persistent index or
runtime dependency is added, and no semantic correction or transform is timed.

The original field is read only. Four temporary copies each receive one trusted
fixture decision: NEW, REUSE, revision_current, MOVE. Copy preparation and file
comparison are excluded from timing. File replacements report replacement file
sizes, not physical disk writes. Counters observe public callable boundaries;
they do not inspect private kernel caches or claim to count cache misses.

Example from the repository root:
    python3 -B lab/nollm-lab/repository_memory/probe_forward_inverse_cost.py \
        --field sujiben/field --output /tmp/nollm-forward-inverse-cost.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
from functools import lru_cache
import json
import os
from pathlib import Path
import shutil
from statistics import median
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src")]

import nollm_core as core_api
from nollm_core import CoreRuntime, GeometryAddress
from nollm_access import (AccessDecision, AccessRuntime, FileHandleStore,
                          FileStatementStore, MemoryStatement,
                          EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)

TOP, LEAF, Q40_ONE = -2, 0, 1 << 40
# Vertices of the nearest-cell axial hexagon, multiplied by three.
HEX_THIRDS = ((1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2), (2, -1))
STRATEGIES = ("sweep_all_content", "sweep_full_targeted",
              "sweep_occupied_targeted", "inverse_targeted")


def address(layer, q, r):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


@lru_cache(maxsize=1)
def inverse_down_bounds():
    """A conservative integer envelope; native membership removes false hits.

    Each mapped sample is M*source + offset in Q40 axial coordinates. A sample
    assigned to target lies in target + its nearest-cell hexagon. Apply M^-1
    to that hexagon minus each offset, take coordinate extrema, and enumerate
    the resulting integer rectangle. Closed bounds include rounding ties.
    """
    origin, unit_q, unit_r = [core_api.coverage_stencil_q40(address(0, q, r), "coverage_down")
                              for q, r in ((0, 0), (1, 0), (0, 1))]
    if origin.center_q40 != (0, 0):
        raise ValueError("this fixed-transform experiment expects a zero mapped origin")
    a, c = unit_q.center_q40
    b, d = unit_r.center_q40
    denominator = 3 * (a * d - b * c)
    if denominator <= 0:
        raise ValueError("this fixture expects the admitted positive determinant")
    rows = []
    for x, y in ((d, -b), (-c, a)):
        hex_values = [x * q + y * r for q, r in HEX_THIRDS]
        offset_values = [x * q + y * r for q, r in origin.offsets_q40]
        lower = Q40_ONE * min(hex_values) - 3 * max(offset_values)
        upper = Q40_ONE * max(hex_values) - 3 * min(offset_values)
        rows.append((x, y, lower, upper))
    return denominator, tuple(rows)


def inverse_down_candidates(target):
    denominator, rows = inverse_down_bounds()
    intervals = []
    for a, b, lower, upper in rows:
        center = 3 * Q40_ONE * (a * target.q + b * target.r)
        first = -(-(center + lower) // denominator)
        last = (center + upper) // denominator
        intervals.append(range(first, last + 1))
    return tuple(address(target.layer - 1, q, r)
                 for q in intervals[0] for r in intervals[1]
                 if max(abs(q), abs(r), abs(q + r)) <= (1 << 31) - 1)


def new_expander():
    # Both algorithms receive exactly the same disposable per-request reuse.
    expansions = {}
    def expand(cell):
        if cell not in expansions:
            expansions[cell] = tuple(member.target for member in
                                    core_api.expand_physical_coverage(cell, "coverage_down").members)
        return expansions[cell]
    return expand, expansions


def sweep(core, retain_empty, expand):
    frontier = {cell for cell in core.occupied_cells() if cell.layer == TOP}
    visited, edges = set(frontier), {}
    for _layer in range(TOP, LEAF):
        following = set()
        for source in sorted(frontier, key=lambda cell: cell.stable_key()):
            edges[source] = expand(source)
            following.update(target for target in edges[source]
                             if retain_empty or core.atoms_at(target))
        frontier = following - visited
        visited.update(frontier)
    return visited, edges


def affected_from_edges(edges, changed):
    affected = set(changed)
    for source in sorted(edges, key=lambda cell: (-cell.layer, cell.q, cell.r)):
        if any(target in affected for target in edges[source]):
            affected.add(source)
    return affected - set(changed)


def inverse_ancestors(core, changed, expand):
    affected, frontier = set(), set(changed)
    candidate_counts = []
    while frontier and min(cell.layer for cell in frontier) > TOP:
        wanted_by_source = {}
        for target in frontier:
            candidates = inverse_down_candidates(target)
            candidate_counts.append(len(candidates))
            for source in candidates:
                wanted_by_source.setdefault(source, set()).add(target)
        previous = set()
        for source, targets in sorted(wanted_by_source.items(), key=lambda item: item[0].stable_key()):
            # Empty intermediate nodes transmit paths. Only at the declared root
            # boundary can unoccupied nodes be excluded from this finite scope.
            if source.layer == TOP and not core.atoms_at(source):
                continue
            if targets.intersection(expand(source)):
                previous.add(source)
        frontier = previous - affected
        affected.update(previous)
    return affected, candidate_counts


def documents(field, core, cells):
    handles = tuple(handle for cell in sorted(cells, key=lambda c: c.stable_key())
                    for handle, _atom in core.atoms_at(cell))
    bindings = FileHandleStore(field).bindings_for_handles(handles) if handles else ()
    store = FileStatementStore(field)
    statements = [store.get(binding.current_statement_id) for binding in bindings]
    return tuple(sorted(statement.statement_id for statement in statements)), sum(
        len(statement.content_utf8.encode("utf-8")) for statement in statements)


def run_strategy(field, strategy, changed, *, identities=False):
    with CoreRuntime(field) as core:
        expand, expansions = new_expander()
        if strategy == "inverse_targeted":
            affected, candidate_counts = inverse_ancestors(core, changed, expand)
            visited = None
        else:
            visited, edges = sweep(core, strategy != "sweep_occupied_targeted", expand)
            affected = affected_from_edges(edges, changed)
            candidate_counts = []
        occupied_affected = {cell for cell in affected if core.atoms_at(cell)}
        if strategy == "sweep_all_content":
            context = {cell for cell in visited if core.atoms_at(cell)}
        else:
            context = set(changed) | occupied_affected
            # Revising a summary can need its current children as well as a delta.
            for cell in occupied_affected:
                context.update(target for target in expand(cell) if core.atoms_at(target))
        statement_ids, body_bytes = documents(field, core, context)
        result = {
            "changed_cells": len(changed), "affected_occupied_cells": len(occupied_affected),
            "affected_geometric_cells": len(affected),
            "visited_cells": None if visited is None else len(visited),
            "visited_occupied_cells": None if visited is None else sum(bool(core.atoms_at(c)) for c in visited),
            "expanded_sources": len(expansions),
            "max_inverse_candidates_per_target": max(candidate_counts, default=0),
            "statement_count": len(statement_ids), "body_utf8_bytes": body_bytes,
        }
        if identities:
            result["affected_identity"] = sorted(cell.stable_key() for cell in occupied_affected)
            result["statement_identity"] = statement_ids
        return result


def measure(field, operation):
    """Observe file reads/replacements and public geometry call boundaries."""
    file_reads, file_bytes, public_calls = Counter(), Counter(), Counter()
    replacements = []
    real_read_bytes, real_read_text, real_replace = Path.read_bytes, Path.read_text, os.replace
    functions = {name: getattr(core_api, name) for name in (
        "expand_physical_coverage", "coverage_stencil_q40",
        "incoming_coverage", "incoming_coverage_candidates")}

    def relative(path):
        try:
            return Path(path).resolve().relative_to(field).as_posix()
        except ValueError:
            return None

    def category(name):
        if name == "core/current_state.json": return "whole_core_state"
        if name == "access/bindings.json": return "whole_bindings"
        if name.startswith("access/statements/"): return "statement_files"
        return name

    def record(path, payload):
        name = relative(path)
        if name is not None:
            kind = category(name)
            file_reads[kind] += 1
            file_bytes[kind] += len(payload)

    def read_bytes(path):
        result = real_read_bytes(path)
        record(path, result)
        return result

    def read_text(path, *args, **kwargs):
        result = real_read_text(path, *args, **kwargs)
        record(path, result.encode("utf-8"))
        return result

    def replace(source, target, *args, **kwargs):
        name = relative(target)
        size = Path(source).stat().st_size if name is not None else None
        result = real_replace(source, target, *args, **kwargs)
        if name is not None:
            replacements.append({"path": name, "replacement_file_bytes": size})
        return result

    def wrapper(name, original):
        def call(*args, **kwargs):
            key = name
            if name == "expand_physical_coverage":
                direction = args[1] if len(args) > 1 else kwargs["direction"]
                key = f"{name}:{direction}"
            public_calls[key] += 1
            return original(*args, **kwargs)
        return call

    with ExitStack() as stack:
        stack.enter_context(patch.object(Path, "read_bytes", read_bytes))
        stack.enter_context(patch.object(Path, "read_text", read_text))
        stack.enter_context(patch.object(os, "replace", replace))
        # Account for already imported aliases of these same public callables.
        # No private callable, constant, cache info or reset is consulted.
        for module in tuple(sys.modules.values()):
            if module is None or not getattr(module, "__name__", "").startswith(("nollm_core", "nollm_access")):
                continue
            for attribute, value in tuple(vars(module).items()):
                for name, original in functions.items():
                    if value is original:
                        stack.enter_context(patch.object(module, attribute, wrapper(name, original)))
        start = perf_counter_ns()
        result = operation()
        elapsed_ms = (perf_counter_ns() - start) / 1e6
    return {"instrumented_elapsed_ms": elapsed_ms, "public_calls": dict(public_calls),
            "file_read_calls": dict(file_reads), "file_read_bytes": dict(file_bytes),
            "atomic_replacements": replacements, "result": result}


def clear_algorithm_caches():
    core_api.clear_physical_coverage_cache()
    inverse_down_bounds.cache_clear()


def cold_hot(field, operation, repetitions):
    clear_algorithm_caches()
    cold, warm = measure(field, operation), measure(field, operation)
    timings = {"cold_algorithm_cache": [], "warm_algorithm_cache": []}
    for _ in range(repetitions):
        clear_algorithm_caches()
        for key in timings:
            start = perf_counter_ns()
            operation()
            timings[key].append((perf_counter_ns() - start) / 1e6)
    return {"cold": cold, "warm": warm,
            "median_uninstrumented_ms": {key: median(values) for key, values in timings.items()}}


def file_contents(field):
    # One small-fixture before/after comparison, never part of a runtime path.
    return {path.relative_to(field).as_posix(): path.read_bytes()
            for path in field.rglob("*") if path.is_file()}


def write_probe(field, original_files):
    with CoreRuntime(field) as core:
        source = next(cell for cell in core.occupied_cells()
                      if cell.layer == LEAF and len(core.atoms_at(cell)) == 1
                      and len(core.atoms_at(cell)[0][1].payload_utf8.encode("utf-8")) < 8000)
        handle, atom = core.atoms_at(source)[0]
        target = address(LEAF, source.q + 1, source.r)
        while core.atoms_at(target):
            target = address(LEAF, target.q + 1, target.r)
    current_id = FileHandleStore(field).statement_for_handle(handle)
    output = {}
    with TemporaryDirectory(prefix="nollm-forward-inverse-writes-") as temporary:
        for action in ("new", "reuse", "revision_current", "move"):
            copied = Path(temporary) / action
            shutil.copytree(field, copied)
            identity = current_id if action == "move" else f"cost-probe.{action}.v1"
            text = ("隔离写入计量；不写回原工作场。" if action == "new" else
                    atom.payload_utf8 + ("〔隔离计量修订〕" if action == "revision_current" else ""))
            statement = MemoryStatement(identity, text, "fixture:forward-inverse-cost")
            decision = AccessDecision(
                f"cost-probe:{action}", identity, action,
                target_cell=target if action in {"new", "move"} else None,
                existing_handle=handle if action != "new" else None,
                reason_text="Explicit trusted fixture for one isolated persistence measurement.",
                decided_by="fixture", write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
            )
            def operation():
                with CoreRuntime(copied) as core, AccessRuntime(
                    core, FileStatementStore(copied), FileHandleStore(copied),
                ) as access:
                    start = perf_counter_ns()
                    if action != "move":
                        access.capture(statement)
                    access.apply(decision)
                    return {"capture_apply_instrumented_ms": (perf_counter_ns() - start) / 1e6,
                            "atoms_after": core.placement_count()}
            clear_algorithm_caches()
            result = measure(copied, operation)
            after = file_contents(copied)
            changed = sorted(name for name in original_files.keys() | after.keys()
                             if original_files.get(name) != after.get(name))
            result["changed_files"] = [
                {"path": name, "before_bytes": len(original_files[name]) if name in original_files else None,
                 "after_bytes": len(after[name]) if name in after else None} for name in changed]
            result["final_whole_file_bytes"] = {name: len(after[name]) for name in
                                                ("core/current_state.json", "access/bindings.json")}
            output[action] = result
    return output


def probe(field, repetitions):
    if not (field / "core/current_state.json").is_file():
        raise ValueError("the probe requires an existing formed field")
    original_files = file_contents(field)
    with CoreRuntime(field) as core:
        cells = core.occupied_cells()
        if any(cell.profile_id != "default_dream_v1" or not TOP <= cell.layer <= LEAF for cell in cells):
            raise ValueError("this finite experiment expects default-chart L-2/L-1/L0 cells")
        leaves = tuple(cell for cell in cells if cell.layer == LEAF)
        field_counts = {"atoms": core.placement_count(), "occupied_cells": len(cells),
                        "occupied_cells_by_layer": dict(Counter(cell.layer for cell in cells))}
        expand, _ = new_expander()
        full, full_edges = sweep(core, True, expand)
        pruned, pruned_edges = sweep(core, False, expand)
        for target in leaves:
            exhaustive = {cell for cell in cells if cell.layer == target.layer - 1 and target in expand(cell)}
            candidates = {cell for cell in inverse_down_candidates(target)
                          if core.atoms_at(cell) and target in expand(cell)}
            if exhaustive != candidates:
                raise AssertionError("inverse envelope missed an occupied direct down reader")
        shape = {"full_geometric_visited": len(full), "full_expanded_sources": len(full_edges),
                 "occupied_pruned_visited": len(pruned), "occupied_pruned_expanded_sources": len(pruned_edges),
                 "all_occupied_reached_by_full": set(cells) <= full,
                 "all_occupied_reached_by_pruned_on_this_field": set(cells) <= pruned,
                 "inverse_matches_all_current_leaf_occupied_readers": True}
        if not shape["all_occupied_reached_by_full"]:
            raise ValueError("the declared roots do not reach every occupied cell in this fixture")
    scenarios = {"single_lower": (address(0, 1, -1),),
                 "three_adjacent_lower": (address(0, 0, 0), address(0, 1, -1), address(0, 1, 0)),
                 "all_lower": leaves}
    results = {}
    for name, changed in scenarios.items():
        if not set(changed) <= set(leaves):
            raise ValueError("this experiment's declared changed lower cells are not occupied")
        full_result = run_strategy(field, "sweep_full_targeted", changed, identities=True)
        inverse_result = run_strategy(field, "inverse_targeted", changed, identities=True)
        for key in ("affected_identity", "statement_identity"):
            if full_result[key] != inverse_result[key]:
                raise AssertionError(f"forward and inverse disagree on {key}")
        results[name] = {strategy: cold_hot(
            field, lambda strategy=strategy: run_strategy(field, strategy, changed), repetitions,
        ) for strategy in STRATEGIES}
    denominator, rows = inverse_down_bounds()
    result = {
        "field": str(field), "field_counts": field_counts, "shape": shape,
        "inverse_candidate_interval_widths": [(upper - lower) / denominator for _, _, lower, upper in rows],
        "public_api_only": True,
        "measurement_scope": {
            "cache": "Cold clears public physical-coverage caches and this script's derived inverse envelope; warm repeats in the same process. Every run reopens field files; OS page/disk caches are not flushed.",
            "geometry_counts": "Public expansion requests after equal per-request deduplication, not private kernel cache misses. Three public stencil calls prepare the cold inverse envelope.",
            "timing": f"Read medians use {repetitions} uninstrumented cold/warm repetitions. Write durations are single instrumented observations; copy preparation and file comparison are excluded.",
            "writes": "Each action uses a separate temporary field copy. Capture is included except MOVE, which reuses current evidence. Atomic replacement sizes are file sizes, not physical disk I/O bytes.",
            "semantics": "No LLM correction, actual transform or persistent reverse index is implemented or timed. Targeted methods load changed bodies, affected occupied summaries and their direct occupied lower context.",
            "finite_scope": "Occupied L-2 roots through declared L0 leaves. Complete descent retains empty intermediate cells; occupied-only pruning is a restricted comparison, not generally safe.",
        },
        "scenarios": results, "isolated_write_actions": write_probe(field, original_files),
    }
    if file_contents(field) != original_files:
        raise AssertionError("source field changed during the experiment")
    result["source_field_unchanged"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    field, output = args.field.resolve(), args.output.resolve()
    if output.is_relative_to(field):
        parser.error("--output must be outside the read-only source field")
    result = probe(field, args.repetitions)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "field_counts": result["field_counts"],
                      "shape": result["shape"], "source_field_unchanged": True},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
