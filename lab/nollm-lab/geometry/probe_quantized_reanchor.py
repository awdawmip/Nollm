"""Replay two representation-only reanchor witnesses in the frozen quantized Lab v1.

Uses the existing frozen seed-20261123 inventory. It does not alter Core, the live
field, map geometry, precision, or original evidence. The observed label changes
are retained as known limitations of the existing world-unit quantized rule.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True,
                        help="Root of the Nollm source checkout being reviewed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path[:0] = [str(repo / "packages/nollm-core/src"), str(repo / "lab/nollm-lab")]
    from geometry.quantized_rational_kernel import compile_quantized_pair
    from geometry.rational_coverage import (
        nearest_axial_rational, rational_sample_numerators, rational_sample_offsets,
    )
    from geometry.rational_geometry import RationalLayerMap

    frozen_path = repo / "lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json"
    frozen = json.loads(frozen_path.read_text())
    records = frozen["inventories"][0]["cases"]
    anchors = (Fraction(1, 3), Fraction(1, 7))
    witnesses = (
        ("d1_compact_weak_up", 8, (0, -1), 89, (2, -1), (1, -1)),
        ("d1_medium_up", 12, (1, 1), 33, (1, 0), (1, 1)),
    )
    results = []
    for name, bits, expected_cell, expected_index, expected_before, expected_after in witnesses:
        record = next(item for item in records if item["scenario"]["name"] == name)
        case = record["scenario"]
        source = RationalLayerMap.from_mapping(case["lower_map"])
        target = RationalLayerMap.from_mapping(case["upper_map"])
        shifted = target.reanchor(anchors)
        coordinates = tuple(tuple(cell) for cell in case["coordinates"])
        before_kernel = compile_quantized_pair(source, target, fractional_bits=bits)
        after_kernel = compile_quantized_pair(source, shifted, fractional_bits=bits)
        changes = []
        for q, r in coordinates:
            before = before_kernel.targets(q, r, rational_sample_numerators(), 36)
            after = after_kernel.targets(q, r, rational_sample_numerators(), 36)
            for index, (first, second) in enumerate(zip(before, after)):
                if first == second:
                    continue
                dq, dr = rational_sample_offsets()[index]
                world = source.forward((q + dq, r + dr))
                exact_before = target.inverse(world)
                exact_after = shifted.inverse(world)
                changes.append({
                    "source": [q, r], "sample_index": index,
                    "before": list(first), "after": list(second),
                    "exact_target": list(nearest_axial_rational(*exact_before)),
                    "exact_coordinates_before": [str(x) for x in exact_before],
                    "exact_coordinates_after": [str(x) for x in exact_after],
                    "exact_inverse_equal": exact_before == exact_after,
                })
        reproduced = (
            len(changes) == 1
            and changes[0]["source"] == list(expected_cell)
            and changes[0]["sample_index"] == expected_index
            and changes[0]["before"] == list(expected_before)
            and changes[0]["after"] == list(expected_after)
            and changes[0]["exact_inverse_equal"]
        )
        results.append({
            "case": name, "bits": bits,
            "target_reanchor": [str(x) for x in anchors],
            "changed_labels": len(changes), "total_labels": 96 * len(coordinates),
            "changes": changes,
            "source_map": source.to_mapping(),
            "target_before": target.to_mapping(),
            "target_after": shifted.to_mapping(),
            "target_affine_forward_equal_at_control_points": all(
                target.frame.forward(point) == shifted.frame.forward(point)
                for point in ((0, 0), (1, 0), (0, 1))
            ),
            "twists_unchanged": target.twists == shifted.twists,
            "expected_witness_reproduced": reproduced,
        })
    output = {
        "schema": "nollm_quantized_reanchor_audit_v1",
        "reviewed_baseline": "f37667bf232360d0c26d37de0639285084230ddc",
        "scope": "old Lab quantized v1 world-unit rule; current Core Q40 unaffected",
        "frozen_inventory": str(frozen_path.relative_to(repo)),
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "cases": [{
            "case": item["case"], "bits": item["bits"],
            "changed_labels": item["changed_labels"],
            "total_labels": item["total_labels"],
            "expected_witness_reproduced": item["expected_witness_reproduced"],
        } for item in results],
    }, ensure_ascii=False))
    return 0 if all(item["expected_witness_reproduced"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

