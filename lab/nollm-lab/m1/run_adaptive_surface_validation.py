from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import SurfaceBudgetProfile, select_active_surface
from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    SurfaceOrderInfo,
    SurfacePlane,
)


PLANE = SurfacePlane("eisenstein_exact_v1", "default", None, 0)


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "default", 0, q, r)


def budget(max_cells: int, max_units: int = 10_000) -> SurfaceBudgetProfile:
    return SurfaceBudgetProfile(8, 8, max_cells, 8, 4, max_units, 3, 2, 2, 12)


def selector_boundaries() -> list[int]:
    infos = tuple(
        SurfaceOrderInfo(PLANE, order, count, 1, 0, count * 65536, order)
        for order, count in enumerate((24, 8, 2))
    )
    return [
        select_active_surface(infos, budget(24)).info.order,
        select_active_surface(infos, budget(8)).info.order,
        select_active_surface(infos, budget(2)).info.order,
    ]


def validate() -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-adaptive-surface-") as temporary:
        root = Path(temporary)
        with CoreRuntime(root) as core:
            for atom_id, address in (
                ("alpha-window", cell(0, 0)),
                ("alpha-owner", cell(0, 1)),
                ("office-desk", cell(8, 0)),
                ("office-cafe", cell(9, 0)),
            ):
                core.put(MemoryAtom(atom_id, f"payload:{atom_id}"), address)
            orders = core.surface_orders(PLANE, 2)
            pages = tuple(core.surface_page(PLANE, order, None, 256) for order in range(3))
            source = cell(0, 0)
            parents = tuple(
                parent.address
                for parent in pages[1].cells
                if any(
                    child.projection.address == source
                    for child in core.surface_descend(PLANE, 1, parent.address, None, 256).cells
                )
            )
            before = tuple(page.cells for page in pages)
            state_bytes = core.export_state_bytes()

        with CoreRuntime(root) as reopened:
            after = tuple(reopened.surface_page(PLANE, order, None, 256).cells for order in range(3))
            reopened_bytes = reopened.export_state_bytes()

        checks = {
            "orders_0_1_2": [info.order for info in orders] == [0, 1, 2],
            "order_zero_canonical": [item.address for item in pages[0].cells]
            == sorted((cell(0, 0), cell(0, 1), cell(8, 0), cell(9, 0)), key=lambda item: item.stable_key()),
            "coverage_down_multi_parent": len(parents) > 1 and len(set(parents)) == len(parents),
            "reopen_surface_identity": before == after,
            "reopen_state_identity": state_bytes == reopened_bytes,
            "selector_order_boundaries": selector_boundaries() == [0, 1, 2],
            "selector_has_no_query_input": tuple(inspect.signature(select_active_surface).parameters) == ("infos", "budget"),
            "cursor_absent": not (root / "openclaw" / "memory_cursor.json").exists(),
        }
        if not all(checks.values()):
            raise AssertionError({key: value for key, value in checks.items() if not value})
        return {
            "schema_version": "nollm_adaptive_surface_lab_v1",
            "status": "pass",
            "checks": checks,
            "occupied_cells": {f"order_{info.order}": info.occupied_cell_count for info in orders},
            "source_parent_count": len(parents),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail unless all adaptive Surface invariants hold")
    parser.parse_args()
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
