from __future__ import annotations

import argparse
import json
from decimal import Decimal

from physical_geometry import beta, hex_center, hex_vertices, layer_angle, layer_side, polygon_area


def validate() -> dict[str, object]:
    value = beta()
    orientations = [str((layer_angle(layer) * Decimal(180) / Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")) % 60) for layer in range(9)]
    areas = [polygon_area(hex_vertices(layer, 0, 0)) for layer in range(9)]
    center = hex_center(0, 1, 0)
    checks = {
        "beta_fourth_power_is_two": abs(value ** 4 - Decimal(2)) < Decimal("1e-60"),
        "beta_squared_is_sqrt_two": abs(value ** 2 - Decimal(2).sqrt()) < Decimal("1e-60"),
        "orientation_phase_repeats_at_eight": abs(Decimal(orientations[0]) - Decimal(orientations[8])) < Decimal("1e-60"),
        "adjacent_area_ratio_is_sqrt_two": all(abs(areas[index] / areas[index + 1] - Decimal(2).sqrt()) < Decimal("1e-60") for index in range(8)),
        "pointy_top_center_spacing": abs(center[0] - Decimal(3).sqrt()) < Decimal("1e-60") and abs(center[1]) < Decimal("1e-60"),
        "regular_hex_has_six_vertices": len(hex_vertices(0, 0, 0)) == 6,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    return {"schema_version": "nollm_rotated_physical_geometry_validation_v1", "checks": checks, "orientation_degrees_mod60": orientations}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
