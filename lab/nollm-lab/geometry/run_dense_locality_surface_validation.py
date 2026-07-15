from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from nollm_access import (
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    PLACEMENT_SURFACE_BUDGET,
)
from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY,
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    PhysicalFieldScope,
    PutCommand,
    clear_surface_order_cache,
)


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _coordinates(radius: int, *, offset_q: int = 0) -> tuple[tuple[int, int], ...]:
    return tuple(
        (q + offset_q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    )


def _populate(workspace: Path, coordinates: tuple[tuple[int, int], ...], atom_count: int, bind_count: int) -> None:
    addresses = tuple(GeometryAddress("default_dream_v1", "default", 0, q, r) for q, r in coordinates)
    if atom_count < len(addresses) + max(0, bind_count - 1):
        raise ValueError("atom_count cannot occupy every fixture cell with requested bound previews")
    assigned = [addresses[0]] * bind_count if bind_count else [addresses[0]]
    assigned.extend(addresses[1:])
    assigned.extend(addresses[index % len(addresses)] for index in range(atom_count - len(assigned)))
    with CoreRuntime(workspace) as core:
        handles = core.apply_batch(tuple(
            PutCommand(MemoryAtom(f"atom-{index:04d}", f"dense fixture statement {index:04d}"), address)
            for index, address in enumerate(assigned)
        ))
    statements = FileStatementStore(workspace)
    bindings = FileHandleStore(workspace)
    for index, handle in enumerate(handles[:bind_count]):
        statement_id = f"atom-{index:04d}"
        statements.put(MemoryStatement(statement_id, f"dense fixture statement {index:04d}"))
        bindings.put(statement_id, handle)


def _all_pages(navigator: AccessSurfaceNavigator, first):
    pages = [first]
    continuation_times = []
    current = first
    while current.has_more:
        started = perf_counter()
        current = navigator.continue_page(current)
        continuation_times.append((perf_counter() - started) * 1000)
        pages.append(current)
    return pages, continuation_times


def _dense_case(name: str, cell_count: int, atom_count: int, ceiling_ms: float) -> dict[str, object]:
    with TemporaryDirectory(prefix=f"nollm-caold-{name}-") as raw_workspace:
        workspace = Path(raw_workspace)
        coordinates = _coordinates(10)[:cell_count]
        bind_count = min(16, atom_count) if atom_count > cell_count else 0
        _populate(workspace, coordinates, atom_count, bind_count)
        clear_surface_order_cache()
        navigator = AccessSurfaceNavigator(workspace)
        started = perf_counter()
        first = navigator.begin(f"dense:{name}", SCOPE, PLACEMENT_SURFACE_BUDGET)
        cold_ms = (perf_counter() - started) * 1000
        pages, continuation_times = _all_pages(navigator, first)
        order_infos = ()
        with CoreRuntime(workspace) as core:
            order_infos = core.surface_orders(SCOPE, first.selection.info.order)
        reopened_basis = first.to_mapping()
        clear_surface_order_cache()
        reopened = AccessSurfaceNavigator(workspace).begin(f"dense:{name}", SCOPE, PLACEMENT_SURFACE_BUDGET)
        reopen_identity = reopened.to_mapping() == reopened_basis

        current = first
        while current.state.order > 0:
            candidate = max(current.cells, key=lambda item: (item.aggregate_atom_count, item.candidate_id))
            current = navigator.open_surface_cell(current, candidate.candidate_id)
        leaf = max(current.cells, key=lambda item: (item.native_atom_count, item.candidate_id))
        physical = navigator.open_physical_entries(current, leaf.candidate_id)

        with CoreRuntime(workspace) as core:
            before_atoms = core.placement_count()
            core.put(MemoryAtom("mutation", "cache invalidation"), GeometryAddress("default_dream_v1", "default", 0, 20, 0))
        mutated = navigator.begin(f"dense:{name}:mutated", SCOPE, PLACEMENT_SURFACE_BUDGET)
        mutation_invalidated = mutated.selection.info.native_atom_count == before_atoms + 1

        return {
            "occupied_cell_count": cell_count,
            "atom_count": atom_count,
            "selected_order": first.selection.info.order,
            "overflow": first.selection.overflow,
            "order_statistics": [
                {
                    "order": info.order,
                    "occupied_cell_count": info.occupied_cell_count,
                    "native_atom_count": info.native_atom_count,
                    "aggregate_mass_q16": info.aggregate_mass_q16,
                }
                for info in order_infos
            ],
            "cold_begin_ms": cold_ms,
            "continuation_page_count": len(pages) - 1,
            "max_continuation_ms": max(continuation_times, default=0),
            "truncated_cell_count": sum(cell.truncated for page in pages for cell in page.cells),
            "physical_entry_page_size": len(physical.candidates),
            "physical_entry_total_count": physical.total_candidate_count,
            "physical_entry_truncated_count": sum(candidate.truncated for candidate in physical.candidates),
            "reopen_identity": reopen_identity,
            "mutation_invalidated": mutation_invalidated,
            "ceiling_ms": ceiling_ms,
            "ceiling_passed": cold_ms <= ceiling_ms,
            "continuation_ceiling_passed": max(continuation_times, default=0) <= 1000,
        }


def _structural_fixtures() -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-caold-structural-") as raw_workspace:
        workspace = Path(raw_workspace)
        sparse = ((-60, 0), (-30, 0), (0, 0), (30, 0), (60, 0), (90, 0))
        left = _coordinates(2, offset_q=-100)
        right = _coordinates(2, offset_q=100)
        radius = ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius - 4096
        boundary = ((radius, 0), (0, radius), (-radius, radius), (-radius, 0), (0, -radius), (radius, -radius))
        coordinates = sparse + left + right + boundary
        _populate(workspace, coordinates, len(coordinates), 0)
        with CoreRuntime(workspace) as core:
            info = core.surface_orders(SCOPE, 0)[0]
            occupied = core.occupied_cells()
            return {
                "sparse_cell_count": len(sparse),
                "unrelated_left_cell_count": len(left),
                "unrelated_right_cell_count": len(right),
                "boundary_cell_count": len(boundary),
                "order_zero_occupied_cell_count": info.occupied_cell_count,
                "bridge_count": len(core.bridges()),
                "maximum_radius": max(max(abs(cell.q), abs(cell.r), abs(cell.q + cell.r)) for cell in occupied),
                "all_within_writable_radius": all(
                    max(abs(cell.q), abs(cell.r), abs(cell.q + cell.r)) <= ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius
                    for cell in occupied
                ),
            }


def validate(*, dense_cell_count: int = 300, atom_count: int = 1000) -> dict[str, object]:
    dense_cells = _dense_case("300-cells", dense_cell_count, dense_cell_count, 5000)
    dense_atoms = _dense_case("1000-atoms", dense_cell_count, atom_count, 10000)
    structural = _structural_fixtures()
    checks = {
        "dense_cell_minimum": dense_cell_count >= 300,
        "dense_atom_minimum": atom_count >= 1000,
        "dense_cell_cold_ceiling": dense_cells["ceiling_passed"],
        "dense_atom_cold_ceiling": dense_atoms["ceiling_passed"],
        "continuation_ceiling": dense_cells["continuation_ceiling_passed"] and dense_atoms["continuation_ceiling_passed"],
        "truncation_observed": dense_atoms["truncated_cell_count"] > 0 or dense_atoms["physical_entry_truncated_count"] > 0,
        "reopen_identity": dense_cells["reopen_identity"] and dense_atoms["reopen_identity"],
        "mutation_invalidation": dense_cells["mutation_invalidated"] and dense_atoms["mutation_invalidated"],
        "unrelated_without_bridge": structural["bridge_count"] == 0,
        "boundary_within_writable_radius": structural["all_within_writable_radius"],
    }
    return {
        "schema_version": "nollm_dense_locality_surface_validation_v1",
        "dense_cells": dense_cells,
        "dense_atoms": dense_atoms,
        "structural_fixtures": structural,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
