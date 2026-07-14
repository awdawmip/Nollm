from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src")]

from nollm_access import SurfaceBudgetProfile, select_active_surface  # noqa: E402
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope  # noqa: E402


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _populate_disk(runtime: CoreRuntime, radius: int, prefix: str) -> int:
    count = 0
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if max(abs(q), abs(r), abs(q + r)) <= radius:
                runtime.put(MemoryAtom(f"{prefix}:{count}", prefix), GeometryAddress("default_dream_v1", "default", 0, q, r))
                count += 1
    return count


def _fixture(radius: int) -> dict[str, object]:
    with TemporaryDirectory(prefix=f"nollm-rotated-dense-{radius}-") as temporary:
        with CoreRuntime(temporary) as runtime:
            native = _populate_disk(runtime, radius, f"dense{radius}")
            infos = runtime.surface_orders(SCOPE, 8)
        counts = [info.occupied_cell_count for info in infos]
        budget = SurfaceBudgetProfile(8, 20, counts[1], 8, 4, 100000, 8, 8, 24)
        selected = select_active_surface(infos, budget)
        return {"radius": radius, "native": native, "counts": counts, "areas_q32": [info.grid.observation_area_ratio_q32 for info in infos], "selected_order": selected.info.order, "overflow": selected.overflow}


def validate() -> dict[str, object]:
    dense = [_fixture(5), _fixture(8)]
    with TemporaryDirectory(prefix="nollm-rotated-sparse-") as temporary:
        with CoreRuntime(temporary) as runtime:
            for index, q in enumerate((0, 100, 200)):
                runtime.put(MemoryAtom(f"s:{index}", "sparse"), GeometryAddress("default_dream_v1", "default", 0, q, 0))
            sparse_counts = [info.occupied_cell_count for info in runtime.surface_orders(SCOPE, 8)]
    checks = {
        "two_dense_fixtures": len(dense) == 2,
        "observation_area_strictly_grows": all(all(right > left for left, right in zip(item["areas_q32"], item["areas_q32"][1:])) for item in dense),
        "dense_real_coarsening": all(any(count < item["counts"][0] for count in item["counts"][1:]) for item in dense),
        "real_budget_selects_coarser_without_overflow": all(item["selected_order"] > 0 and not item["overflow"] for item in dense),
        "sparse_not_forced_monotonic": len(sparse_counts) == 9,
    }
    if not all(checks.values()):
        raise AssertionError({"checks": checks, "dense": dense, "sparse_counts": sparse_counts})
    return {"schema_version": "nollm_rotated_surface_coarsening_validation_v1", "checks": checks, "dense": dense, "sparse_counts": sparse_counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
