"""Compare directed physical Recall with descending a rebuilt Surface membership."""
import argparse
import json
from math import ceil, floor
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "packages/nollm-core/src"))
from nollm_core import (
    CoreRecallRequest, CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope,
    RecallBudget, expand_physical_coverage,
)

PROFILE = "default_dream_v1"
UP, DOWN = "coverage_up", "coverage_down"
SOURCE_NOTE = {
    "path": "packages/nollm-core/src/nollm_core/surface.py",
    "commit": "691590dcc6009b59a9cf51dfe7a9e7a7516eca0b",
    "blob": "0aa7267e2dd9e9358022fe441576405796238e73",
    "lines": [255, 275],
    "finding": "Each higher Surface order groups the upward memberships computed for lower records.",
}


def address(layer, q, r):
    return GeometryAddress(PROFILE, "default", layer, q, r)


def coords(cell):
    return [cell.layer, cell.q, cell.r]


def footprint(cell, direction):
    return [
        {"address": coords(m.target), "samples": m.hit_count, "q16": m.weight_q16}
        for m in expand_physical_coverage(cell, direction).members
    ]


def directed_pair(coarse, fine, certify):
    rows = []
    for source, target, direction in ((coarse, fine, DOWN), (fine, coarse, UP)):
        weights = dict(expand_physical_coverage(source, direction).targets())
        row = {"source": coords(source), "target": coords(target), "direction": direction,
               "sampled_q16": weights.get(target, 0)}
        if certify:
            from certified_overlap import certify_coverage

            bounds = certify_coverage(source.layer, source.q, source.r, direction).shares()
            lo, hi = bounds[(target.q, target.r)]
            # Directed outward rounding gives inclusive integer parts per million.
            row["ideal_source_share_ppm_bounds"] = [
                floor(lo * 1_000_000), ceil(hi * 1_000_000),
            ]
        rows.append(row)
    return rows


def reverse_misses():
    counts = {}
    for layer, direction, reverse in ((2, DOWN, UP), (3, UP, DOWN)):
        edges = misses = 0
        for q in range(-10, 11):
            for r in range(-10, 11):
                source = address(layer, q, r)
                for target, _ in expand_physical_coverage(source, direction).targets():
                    edges += 1
                    misses += source not in dict(expand_physical_coverage(target, reverse).targets())
        counts[direction] = {"sources": 441, "edges": edges, "reverse_missing": misses}
    return counts


def surface_witness(coarse, fine):
    scope = PhysicalFieldScope(PROFILE, "default", (fine.layer,), fine.layer)
    with TemporaryDirectory() as temp:
        with CoreRuntime(Path(temp)) as core:
            handle = core.put(MemoryAtom("surface-source", json.dumps(SOURCE_NOTE)), fine)
            original_bytes = core.export_state_bytes()
        with CoreRuntime(Path(temp)) as core:
            tiles = core.surface_page(scope, 1, None, 32).cells
            tile = next(p for p in tiles if (p.address.q, p.address.r) == (coarse.q, coarse.r))
            descent = core.surface_descend(scope, tile.address, None, 32)
            member = next(d for d in descent.cells if handle.geometry_address in d.projection.source_cells)
            physical = core.recall(CoreRecallRequest(
                "down", (coarse,), (DOWN,), RecallBudget(1, 32, 1, 0, 0, 16),
            ))
            return {
                "note": SOURCE_NOTE, "fine": coords(fine), "coarse": coords(coarse),
                "surface_order": 1, "surface_tile_count": len(tiles),
                "surface_total_mass_q16": sum(p.aggregate_mass_q16 for p in tiles),
                "surface_membership_q16": member.coverage_weight_q16,
                "physical_recall_items": len(physical.items),
                "state_bytes_unchanged_after_reopen_and_queries": core.export_state_bytes() == original_bytes,
            }


def run(certify=False):
    if certify:
        sys.path.insert(0, str(ROOT / "lab/nollm-lab/geometry"))
    coarse, fine = address(2, -7, 5), address(3, -7, 8)
    up_only = (address(2, 0, 2), address(3, 2, 2))
    down_only = (address(2, 0, 7), address(3, 5, 5))
    return {
        "coarse_footprint_down": footprint(coarse, DOWN), "fine_footprint_up": footprint(fine, UP),
        "up_only": directed_pair(*up_only, certify), "down_only": directed_pair(*down_only, certify),
        "21x21_source_window": reverse_misses(), "reopened_surface_witness": surface_witness(*up_only),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certify", action="store_true", help="include independent ideal-area enclosures from Lab")
    print(json.dumps(run(parser.parse_args().certify), indent=2))
