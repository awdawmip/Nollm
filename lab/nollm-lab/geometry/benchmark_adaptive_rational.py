"""Compare the existing rational auto path with adaptive integer intervals.

Full operations include compilation, all 96 labels, weights and output reports.
The opt-in timings have no CI threshold. Exact maps remain the input contract;
changing initial precision changes execution work, never the accepted labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction as F
import json
from pathlib import Path
import platform
from statistics import median
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "lab/nollm-lab")]

from nollm_core import GeometryAddress
from geometry.adaptive_rational_kernel import compile_adaptive_pair
from geometry.rational_coverage import (
    RATIONAL_COVERAGE_CONTRACT_ID, compare_rational_pressure,
    rational_sample_numerators, sampled_rational_coverage,
)
from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist


def cell(layer, q, r):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def scenarios():
    sf = RationalAffine.similarity("5/4", "1/7", origin=("1/11", "-2/13"))
    tf = RationalAffine.similarity("7/6", "-1/9", origin=("-1/5", "2/7"),
                                   local_anchor=("1/13", "-1/17"))
    coordinates = tuple((q, r) for q in range(-4, 4) for r in range(-2, 2))
    source, target = RationalLayerMap(sf), RationalLayerMap(tf)
    yield "affine_32", source, target, coordinates
    first = RationalRadialTwist((0, 0), 25, "1/5")
    second = RationalRadialTwist(("1/5", 0), 25, "-1/7")
    yield "distinct_world_twists_16", RationalLayerMap(sf, (first,)), \
        RationalLayerMap(tf, (second,)), coordinates[8:24]
    anchor = 2**160
    near = tuple((q, r) for q in range(-1, 2) for r in range(-1, 2)
                 if max(abs(q), abs(r), abs(q+r)) <= 1)
    yield "common_anchor_distinct_twists_7", \
        RationalLayerMap(replace(sf, origin=(anchor+1, -anchor)),
                         (replace(first, center=(anchor, -anchor)),)), \
        RationalLayerMap(replace(tf, origin=(anchor, -anchor)),
                         (replace(second, center=(F(anchor)+F(1, 5), -anchor)),)), near
    local = RationalAffine.similarity("1/10", origin=("1/4", "1/5"))
    alternating = tuple(RationalRadialTwist((0 if i % 2 == 0 else F(1, 5), 0),
                                          1, "1/5") for i in range(5))
    for length in (2, 3, 5):
        yield f"alternating_centers_{length}_one_cell", \
            RationalLayerMap(local, alternating[:length]), RationalLayerMap(), ((0, 0),)
    yield "alternating_centers_5_multiple_targets", RationalLayerMap(local, alternating), \
        RationalLayerMap(RationalAffine(origin=("-7/10", "-1/36"))), ((0, 0),)
    common = RationalRadialTwist(("-1/7", "1/11"), 25, "1/9")
    yield "common_outer_suffix_one_cell", RationalLayerMap(sf, (first, common)), \
        RationalLayerMap(tf, (second, common)), ((0, 0),)
    yield "outside_twist_support_32", RationalLayerMap(sf, (first,)), target, \
        tuple((q+100, r-100) for q, r in coordinates)


def timed(run, repeats, initial_bits=16, max_bits=128):
    expected = run("auto", initial_bits, max_bits)
    assert run("adaptive", initial_bits, max_bits) == expected
    timings = {"auto": [], "adaptive": []}
    for repeat in range(repeats):
        modes = ("auto", "adaptive") if repeat % 2 == 0 else ("adaptive", "auto")
        for mode in modes:
            started = perf_counter_ns()
            actual = run(mode, initial_bits, max_bits)
            timings[mode].append((perf_counter_ns()-started)/1_000_000)
            assert actual == expected
    old, new = (median(timings[mode]) for mode in ("auto", "adaptive"))
    return {"initial_bits": initial_bits, "max_bits": max_bits,
            "auto_ms": timings["auto"], "adaptive_ms": timings["adaptive"],
            "auto_median_ms": old, "adaptive_median_ms": new,
            "auto_over_adaptive": old/new, "complete_results_equal": True}


def execution_stats(source, target, coordinates, initial_bits=16, max_bits=128):
    kernel = compile_adaptive_pair(source, target, initial_bits=initial_bits, max_bits=max_bits)
    attempts, certified = Counter(), Counter()
    totals = Counter()
    for q, r in coordinates:
        row = kernel.targets_with_stats(q, r, rational_sample_numerators(), 36).stats
        attempts.update(row["attempted_by_bits"])
        certified.update(row["certified_by_bits"])
        for key in ("sample_count", "exact_fallback", "affine_exact"):
            totals[key] += row[key]
    return {**totals, "attempted_by_bits": dict(sorted(attempts.items())),
            "certified_by_bits": dict(sorted(certified.items())),
            "cancelled_common_twists": row["cancelled_common_twists"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    rational_sample_numerators()
    cases = []
    all_scenarios = list(scenarios())
    for name, source, target, coordinates in all_scenarios:
        def run(mode, initial_bits, max_bits):
            return tuple(sampled_rational_coverage(cell(1, q, r), 0, source, target,
                mode=mode, initial_bits=initial_bits, max_bits=max_bits).to_mapping()
                for q, r in coordinates)
        record = {"name": name, "source_map": source.to_mapping(),
                  "target_map": target.to_mapping(), "coordinates": coordinates,
                  "timed_scope": "complete per-cell coverage including compilation and output mappings",
                  **timed(run, args.repeats),
                  "execution": execution_stats(source, target, coordinates)}
        record["target_hit_counts"] = [
            [{"q": m.target.q, "r": m.target.r, "hits": m.hit_count}
             for m in sampled_rational_coverage(cell(1, q, r), 0, source, target,
                                                mode="adaptive").members]
            for q, r in coordinates]
        cases.append(record)
        print(json.dumps({k: record[k] for k in ("name", "auto_median_ms",
              "adaptive_median_ms", "auto_over_adaptive", "execution")}), flush=True)
    # A complete comparison includes material aggregation, Q16 output and the
    # union of old/new supports; these use the same exact classified samples.
    _, lower_map, upper_map, coordinates = all_scenarios[1]
    coordinates = coordinates[:8]
    upper = {cell(0, q, r): 1+i % 3 for i, (q, r) in enumerate(coordinates)}
    lower = {cell(1, q, r): 1+i % 5 for i, (q, r) in enumerate(coordinates)}
    after = replace(lower_map, frame=replace(lower_map.frame,
        origin=(lower_map.frame.origin[0]+F(1, 7), lower_map.frame.origin[1])))
    def run_pressure(mode, initial_bits, max_bits):
        return compare_rational_pressure(upper, lower, upper_layer=0,
            before_upper_map=upper_map, before_lower_map=lower_map,
            after_lower_map=after, inventory_complete=True,
            mode=mode, initial_bits=initial_bits, max_bits=max_bits)
    pressure = {"name": "nonlinear_candidate_pressure_8", "timed_scope":
                "both complete pressure reports and old/new union comparison",
                "upper_units": [{"cell": c.to_mapping(), "units": n} for c, n in upper.items()],
                "lower_units": [{"cell": c.to_mapping(), "units": n} for c, n in lower.items()],
                "before_lower_map": lower_map.to_mapping(), "after_lower_map": after.to_mapping(),
                "upper_map": upper_map.to_mapping(), **timed(run_pressure, args.repeats)}
    cases.append(pressure)
    print(json.dumps({k: pressure[k] for k in ("name", "auto_median_ms",
          "adaptive_median_ms", "auto_over_adaptive")}), flush=True)
    # Fixed inputs, varying only the initial fractional precision. Reuse the
    # reference once; these are measured execution choices, not universal optima.
    _, source, target, coordinates = all_scenarios[1]
    expected = tuple(sampled_rational_coverage(cell(1, q, r), 0, source, target,
                     mode="auto") for q, r in coordinates)
    precision_sweep = []
    for bits in (4, 8, 12, 16, 24, 32):
        durations = []
        for _ in range(args.repeats):
            start = perf_counter_ns()
            actual = tuple(sampled_rational_coverage(cell(1, q, r), 0, source, target,
                mode="adaptive", initial_bits=bits) for q, r in coordinates)
            durations.append((perf_counter_ns()-start)/1_000_000)
            assert actual == expected
        precision_sweep.append({"initial_bits": bits, "adaptive_ms": durations,
            "median_ms": median(durations), "complete_results_equal": True,
            "execution": execution_stats(source, target, coordinates, bits)})
    output = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "repeats": args.repeats,
        "coverage_contract_id": RATIONAL_COVERAGE_CONTRACT_ID,
        "comparison": "existing exact rational auto versus adaptive integer interval execution",
        "warmup": "one complete auto and adaptive call per full-operation case",
        "timing_excludes": "map parsing, equality assertions, JSON encoding, statistics collection and disk writes",
        "cases": cases, "precision_sweep_case": "distinct_world_twists_16",
        "precision_sweep_scope": "complete coverage objects, without to_mapping projection",
        "precision_sweep": precision_sweep,
        "limitations": ["local single-process timings", "sampled coverage contract, not continuous area",
                        "exact fallback may still require large rational intermediates",
                        "initial-bit sweep describes these inputs and implementation only"]}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"precision_sweep": precision_sweep}, indent=2), flush=True)


if __name__ == "__main__":
    main()
