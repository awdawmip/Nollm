"""Measure exact rational reference and integer-compiled execution together.

This opt-in benchmark compares two implementations of the SAME new Lab
contract. It does not compare with the different production Q40 contract.
Timed coverage includes compilation and output construction; timed pressure
includes both complete candidate reports. Inputs are already parsed maps.
There is no timing assertion, external dependency, network call or CI gate.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import platform
from statistics import median
import sys
from time import perf_counter_ns


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
                str(ROOT / "lab/nollm-lab")]

from nollm_core import GeometryAddress
from geometry.rational_affine_kernel import compile_affine_pair
from geometry.rational_coverage import (
    RATIONAL_COVERAGE_CONTRACT_ID, compare_rational_pressure,
    rational_sample_numerators, sampled_rational_coverage,
)
from geometry.rational_geometry import (
    RATIONAL_MAP_CONTRACT_ID, RationalAffine, RationalLayerMap,
    RationalRadialTwist,
)


def cell(layer, q, r):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def timed_pair(run, repeats):
    reference = run("reference")
    assert run("auto") == reference
    samples = {"reference_ms": [], "auto_ms": []}
    for repeat in range(repeats):
        modes = ("reference", "auto") if repeat % 2 == 0 else ("auto", "reference")
        for mode in modes:
            started = perf_counter_ns()
            result = run(mode)
            samples[f"{mode}_ms"].append((perf_counter_ns() - started) / 1_000_000)
            # Full result equality is checked outside the timed operation.
            assert result == reference
    ref_time, auto_time = (median(samples[f"{mode}_ms"]) for mode in ("reference", "auto"))
    return {**samples, "reference_median_ms": ref_time, "auto_median_ms": auto_time,
            "reference_over_auto": ref_time / auto_time,
            "complete_results_equal": True}


def compilation_summary(source, target):
    compiled = compile_affine_pair(source, target)
    if compiled is None:
        return {"execution": "exact_fraction_fallback"}
    coefficients = (*compiled.q_row, *compiled.r_row, compiled.denominator)
    return {"execution": "compiled_integer_affine",
            "coefficient_max_bits": max(abs(value).bit_length() for value in coefficients),
            "denominator_bits": compiled.denominator.bit_length(),
            "common_twists_cancelled": len(source.twists)}


def coverage_case(name, source, target, coordinates, repeats):
    cells = tuple(cell(1, q, r) for q, r in coordinates)
    result = timed_pair(lambda mode: tuple(sampled_rational_coverage(
        address, 0, source, target, mode=mode).to_mapping() for address in cells), repeats)
    return {"name": name, "source_cells": len(cells), "points_per_cell": 96,
            "timed_scope": "coverage batch including per-cell compilation and output mappings",
            "source_map": source.to_mapping(), "target_map": target.to_mapping(),
            "source_coordinates": [list(value) for value in coordinates],
            **compilation_summary(source, target), **result}


def bit_growth(centers, steps):
    point = (Fraction(1, 4), Fraction(1, 5))
    rows = []
    for index in range(steps):
        center = centers[index % len(centers)]
        twist = RationalRadialTwist(center, 1, "1/5")
        previous = point
        started = perf_counter_ns()
        point = twist.forward(previous)
        elapsed = (perf_counter_ns() - started) / 1_000_000
        assert twist.inverse(point) == previous
        rows.append({"step": index + 1,
                     "center": [str(value) for value in center],
                     "max_integer_bits": max(abs(part).bit_length() for value in point
                                             for part in (value.numerator, value.denominator)),
                     "forward_ms": elapsed, "single_step_inverse_exact": True})
    return {"initial_point": ["1/4", "1/5"], "strength": "1/5",
            "radius_squared": "1", "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    rational_sample_numerators()
    source_frame = RationalAffine.similarity("5/4", "1/7", origin=("1/11", "-2/13"))
    target_frame = RationalAffine.similarity("7/6", "-1/9", origin=("-1/5", "2/7"),
                                            local_anchor=("1/13", "-1/17"))
    source, target = RationalLayerMap(source_frame), RationalLayerMap(target_frame)
    coordinates = tuple((q, r) for q in range(-4, 4) for r in range(-4, 4))
    cases = [coverage_case("affine_64", source, target, coordinates, args.repeats)]
    anchor = 2**160
    large_source = RationalLayerMap(replace(source_frame, origin=(anchor + 1, -anchor)))
    large_target = RationalLayerMap(replace(target_frame, origin=(anchor, -anchor)))
    cases.append(coverage_case("common_160_bit_anchor_plus_one_64", large_source,
                               large_target, coordinates, args.repeats))
    twists = (RationalRadialTwist((0, 0), 25, "1/5"),
              RationalRadialTwist(("1/5", 0), 25, "-1/7"))
    near = tuple((q, r) for q in range(-1, 3) for r in range(2))
    cases.append(coverage_case("common_two_world_twists_8", RationalLayerMap(source_frame, twists),
                               RationalLayerMap(target_frame, twists), near, args.repeats))
    distinct = RationalLayerMap(source_frame, (twists[0],))
    cases.append(coverage_case("distinct_world_twist_fallback_16", distinct, target,
                               coordinates[24:40], args.repeats))
    lower = {cell(1, q, r): 1 + (i % 5) for i, (q, r) in enumerate(coordinates[16:48])}
    upper = {cell(0, q, r): 1 + (i % 3) for i, (q, r) in enumerate(coordinates[16:48])}
    after = RationalLayerMap(replace(source_frame, origin=(source_frame.origin[0] + Fraction(1, 3),
                                                          source_frame.origin[1])))
    pressure = timed_pair(lambda mode: compare_rational_pressure(
        upper, lower, upper_layer=0, before_upper_map=target, before_lower_map=source,
        after_lower_map=after, inventory_complete=True, mode=mode), args.repeats)
    cases.append({"name": "candidate_pressure_comparison_32", "lower_cells": len(lower),
                  "upper_cells": len(upper), "points_per_cell_per_candidate": 96,
                  "timed_scope": "both complete pressure reports and union-region comparison",
                  "before_lower_map": source.to_mapping(), "after_lower_map": after.to_mapping(),
                  "upper_map": target.to_mapping(),
                  "lower_units": [{"cell": c.to_mapping(), "units": n} for c, n in lower.items()],
                  "upper_units": [{"cell": c.to_mapping(), "units": n} for c, n in upper.items()],
                  "execution": "one integer compilation per candidate per request", **pressure})
    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "repeats": args.repeats,
        "map_contract_id": RATIONAL_MAP_CONTRACT_ID,
        "coverage_contract_id": RATIONAL_COVERAGE_CONTRACT_ID,
        "comparison": "new rational reference versus exact integer-compiled auto; not old Core",
        "warmup": "one full reference and auto call; immutable stencil cache populated",
        "timing_excludes": "map parsing, equality assertion, JSON encoding, disk output",
        "cases": cases,
        "bit_growth": {"same_center": bit_growth(((0, 0),), 9),
                       "alternating_centers": bit_growth(((0, 0), (Fraction(1, 5), 0)), 5)},
        "limitations": ["local single-process timings, not a production service benchmark",
                        "exact sample assignment does not prove continuous overlap error bounds",
                        "bit-growth examples are fixed probes, not universal complexity bounds"],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": [{key: row[key] for key in (
        "name", "reference_median_ms", "auto_median_ms", "reference_over_auto",
        "complete_results_equal")} for row in cases], "bit_growth": output["bit_growth"]}, indent=2))


if __name__ == "__main__":
    main()
