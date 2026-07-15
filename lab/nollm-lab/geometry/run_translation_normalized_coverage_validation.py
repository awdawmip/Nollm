from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from oracle_decimal import coverage  # noqa: E402


MASS_BOUND = Decimal("1e-70")


def validate() -> dict[str, object]:
    coordinates = (
        (0, 0),
        (10**14, 0),
        (-10**14, 0),
        (10**14, 10**14),
        (10**14, -10**14),
        (-10**14, 10**14),
    )
    max_mass_error = Decimal(0)
    candidate_mismatches = 0
    reciprocal_mismatches = 0
    sample_count = 0
    for layer in range(8):
        for q, r in coordinates:
            for delta in (-1, 1):
                target_layer = layer + delta
                radius4 = coverage(layer, q, r, target_layer, 4)
                radius6 = coverage(layer, q, r, target_layer, 6)
                support4 = {(item.q, item.r) for item in radius4}
                support6 = {(item.q, item.r) for item in radius6}
                candidate_mismatches += support4 != support6
                with localcontext() as context:
                    context.prec = 96
                    mass = sum((item.source_share for item in radius6), Decimal(0))
                max_mass_error = max(max_mass_error, abs(Decimal(1) - mass))
                for item in radius4:
                    reverse = coverage(target_layer, item.q, item.r, layer, 4)
                    match = next((entry for entry in reverse if (entry.q, entry.r) == (q, r)), None)
                    with localcontext() as context:
                        context.prec = 96
                        side_ratio_squared = Decimal(2).sqrt() ** (layer - target_layer)
                        reciprocal_error = MASS_BOUND if match is None else abs(match.intersection_area * side_ratio_squared - item.intersection_area)
                    if match is None or reciprocal_error > MASS_BOUND:
                        reciprocal_mismatches += 1
                sample_count += 1
    checks = {
        "partition_mass_within_bound": max_mass_error <= MASS_BOUND,
        "radius4_equals_radius6_support": candidate_mismatches == 0,
        "reciprocal_intersection_area": reciprocal_mismatches == 0,
        "large_coordinates_exercised": True,
        "all_eight_phases_and_both_directions": sample_count == 96,
    }
    return {
        "schema_version": "nollm_translation_normalized_oracle_c_v1",
        "coordinate_domain": {"q_r": "signed-64", "layer": [-64, 64], "chart_id": "default", "phase": None},
        "sample_count": sample_count,
        "max_partition_mass_error": format(max_mass_error, "e"),
        "candidate_mismatch_count": candidate_mismatches,
        "reciprocal_mismatch_count": reciprocal_mismatches,
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
