"""Run local p8/96 Lab coverage or support pressure from one JSON request.

Usage: python3 local_p8_cli.py --input request.json
Use --input - to read stdin. The result is emitted as JSON on stdout.

All requests include operation (coverage or pressure), local_length (an exact
integer or fraction string in world units), and optional fractional_bits (8).
Coverage requests supply source, target_layer, source_map and target_map.
Pressure requests supply upper_layer, upper_map, lower_map, upper_units and
lower_units; inventories are [{"cell": GeometryAddress mapping, "units": int}].
Optional pressure fields are inventory_complete, evaluation_cells and kappa.
Map and address objects use their existing to_mapping() representations.
This command evaluates the explicit Lab contract and does not modify a field.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
if (HERE.parent.parent / "nollm_core").is_dir():
    sys.path.insert(0, str(HERE.parent.parent))
else:
    ROOT = HERE.parents[3]
    sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "lab/nollm-lab")]

from nollm_core import GeometryAddress
from geometry.rational_coverage import evaluate_rational_pressure, sampled_rational_coverage
from geometry.rational_geometry import RationalLayerMap


def _inventory(rows):
    result = {}
    for row in rows:
        cell = GeometryAddress.from_mapping(row["cell"])
        if cell in result:
            raise ValueError("inventory contains a duplicate cell")
        units = row["units"]
        if type(units) is not int:
            raise TypeError("inventory units must be integers")
        result[cell] = units
    return result


def evaluate_request(request):
    """Parse the JSON boundary once, then use the existing public Lab APIs."""
    if not isinstance(request, dict):
        raise TypeError("request must be a JSON object")
    unit = request.get("local_length")
    if unit is None:
        raise ValueError("local_length is required in source-cell world units")
    bits = request.get("fractional_bits", 8)
    if type(bits) is not int:
        raise TypeError("fractional_bits must be an integer")
    options = {"mode": "local_quantized", "fractional_bits": bits, "local_length": unit}
    operation = request["operation"]
    if operation == "coverage":
        result = sampled_rational_coverage(
            GeometryAddress.from_mapping(request["source"]), request["target_layer"],
            RationalLayerMap.from_mapping(request["source_map"]),
            RationalLayerMap.from_mapping(request["target_map"]), **options,
        )
        return result.to_mapping()
    if operation == "pressure":
        complete = request.get("inventory_complete", False)
        if type(complete) is not bool:
            raise TypeError("inventory_complete must be a boolean")
        return evaluate_rational_pressure(
            _inventory(request["upper_units"]), _inventory(request["lower_units"]),
            upper_layer=request["upper_layer"],
            upper_map=RationalLayerMap.from_mapping(request["upper_map"]),
            lower_map=RationalLayerMap.from_mapping(request["lower_map"]),
            inventory_complete=complete,
            evaluation_cells=tuple(GeometryAddress.from_mapping(cell)
                                   for cell in request.get("evaluation_cells", ())),
            kappa=request.get("kappa", "1"), **options,
        )
    raise ValueError("operation must be coverage or pressure")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="JSON request path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        content = sys.stdin.read() if args.input == Path("-") else args.input.read_text(encoding="utf-8")
        result = evaluate_request(json.loads(content))
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
