from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from nollm_access import AccessSurfaceNavigator, PLACEMENT_SURFACE_BUDGET
from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    PhysicalFieldScope,
    PutCommand,
    clear_surface_order_cache,
)


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _coordinates(radius: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    )


def _run(name: str, coordinates: tuple[tuple[int, int], ...], ceiling_ms: float) -> dict[str, object]:
    with TemporaryDirectory(prefix=f"nollm-v39-{name}-") as workspace:
        with CoreRuntime(Path(workspace)) as core:
            core.apply_batch(tuple(
                PutCommand(
                    MemoryAtom(f"atom-{index}", str(index)),
                    GeometryAddress("default_dream_v1", "default", 0, q, r),
                )
                for index, (q, r) in enumerate(coordinates)
            ))
        clear_surface_order_cache()
        navigator = AccessSurfaceNavigator(workspace)
        started = perf_counter()
        first = navigator.begin(name, SCOPE, PLACEMENT_SURFACE_BUDGET)
        cold_ms = (perf_counter() - started) * 1000
        started = perf_counter()
        continued = navigator.continue_page(first) if first.has_more else first
        warm_page_ms = (perf_counter() - started) * 1000
        return {
            "source_cell_count": len(coordinates),
            "selected_order": first.selection.info.order,
            "selected_occupied_cell_count": first.selection.info.occupied_cell_count,
            "selection_overflow": first.selection.overflow,
            "cold_begin_page_ms": cold_ms,
            "warm_continuation_ms": warm_page_ms,
            "continuation_call_count": continued.state.call_count,
            "ceiling_ms": ceiling_ms,
            "ceiling_passed": cold_ms <= ceiling_ms,
        }


def benchmark() -> dict[str, object]:
    small = _run("small", _coordinates(2)[:11], 5000)
    dense = _run("dense", _coordinates(8), 15000)
    return {
        "schema_version": "nollm_lazy_surface_benchmark_v1",
        "small": small,
        "dense": dense,
        "atlas_used": False,
        "passed": small["ceiling_passed"] and dense["ceiling_passed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
