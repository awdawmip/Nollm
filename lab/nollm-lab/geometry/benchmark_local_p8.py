"""Compare the local p8/96 executor on the frozen 2026-11-23/24 inventories.

The input may be the original quantized benchmark or its lossless input-only
projection. No random case selection or parameter tuning occurs here. Timings
include complete coverage construction; exact-map labels remain the previously
saved reference. Controls and stress cases stay separate from the 24 main strata.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction as F
import json
from math import isqrt
from pathlib import Path
import platform
import random
from statistics import median
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "lab/nollm-lab")]

from nollm_core import GeometryAddress
from geometry.adaptive_rational_kernel import compile_adaptive_pair
from geometry.benchmark_quantized_rational import (
    Scenario, error_summary, normalized_labels, pressure_values,
    structural_metrics, summarize_structure, validate_label_domain,
)
from geometry.local_quantized_rational_kernel import _source_stencil, compile_local_quantized_pair
from geometry.quantized_rational_kernel import compile_quantized_pair
from geometry.rational_coverage import (
    _sampled, rational_sample_numerators, sampled_rational_coverage,
)
from geometry.rational_geometry import RationalLayerMap


MODES = ("local_p8", "world_p8", "world_p12", "adaptive16")
INPUT_PATH = "lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json"
INPUT_BLOB = "fb80dbfd318631b66a0bd8381d731a14f5a55ec2"


def similarity_unit(mapping: RationalLayerMap) -> F:
    """Extract a rational cell length only from a verified axial similarity.

    This helper belongs to the fixed experiment, not the general affine API.
    The nonlinear executor receives its length explicitly.
    """
    (a, b), (c, d) = mapping.frame.matrix
    squared = a*a+a*c+c*c
    if b*b+b*d+d*d != squared or 2*a*b+a*d+b*c+2*c*d != squared:
        raise ValueError("frozen experiment requires a similarity, not arbitrary shear")
    numerator, denominator = isqrt(squared.numerator), isqrt(squared.denominator)
    if numerator*numerator != squared.numerator or denominator*denominator != squared.denominator:
        raise ValueError("frozen experiment requires an exact rational cell length")
    return F(numerator, denominator)


def compiler(source, target, mode):
    if mode == "local_p8":
        return compile_local_quantized_pair(source, target, local_length=similarity_unit(source))
    if mode == "adaptive16":
        return compile_adaptive_pair(source, target, initial_bits=16)
    return compile_quantized_pair(source, target, fractional_bits=int(mode.split("p")[1]))


def labels_for(source, target, coordinates, mode):
    kernel = compiler(source, target, mode)
    return tuple(kernel.targets(q, r, rational_sample_numerators(), 36) for q, r in coordinates)


def changed_labels(before, after):
    return sum(a != b for first, second in zip(before, after) for a, b in zip(first, second))


def hit_histograms(labels):
    return [[[q, r, hits] for (q, r), hits in sorted(Counter(row).items())] for row in labels]


def compare_pressure(record, scenario, mode):
    """Use all three frozen candidate maps and exact material counts."""
    data = record["pressure"]
    demands = {(q, r): units for q, r, units in data["upper_units"]}
    expected_labels, actual_labels, region = [], [], set(demands)
    for item in data["candidates"]:
        reference = normalized_labels(item["reference_labels"])
        actual = labels_for(RationalLayerMap.from_mapping(item["lower_map"]),
                            scenario.upper, scenario.coordinates, mode)
        validate_label_domain(actual, 0)
        expected_labels.append(reference)
        actual_labels.append(actual)
        region.update(point for row in reference+actual for point in row)
    expected, actual, reference_deficits, candidate_deficits = [], [], [], []
    all_errors, demand_errors, ranks = Counter(), Counter(), Counter(candidate_sets=1)
    exact_error_sum, exact_error_max, observations = F(0), F(0), 0
    for reference, candidate in zip(expected_labels, actual_labels):
        ep, ed, er = pressure_values(reference, data["lower_units"], demands, region)
        ap, ad, ar = pressure_values(candidate, data["lower_units"], demands, region)
        reference_deficits.append(er)
        candidate_deficits.append(ar)
        expected.append(sum((ep[cell] for cell in demands), F(0))/len(demands))
        actual.append(sum((ap[cell] for cell in demands), F(0))/len(demands))
        for cell in region:
            all_errors[abs(ed[cell]-ad[cell])] += 1
            if demands.get(cell, 0) > 0:
                demand_errors[abs(ed[cell]-ad[cell])] += 1
            error = abs(ep[cell]-ap[cell])
            exact_error_sum += error
            exact_error_max = max(exact_error_max, error)
            observations += 1
    worst_gap = F(0)
    sign = lambda value: (value > 0)-(value < 0)
    for i in range(len(expected)):
        for j in range(i):
            reference_gap, candidate_gap = expected[i]-expected[j], actual[i]-actual[j]
            old, new = sign(reference_gap), sign(candidate_gap)
            ranks["reference_tied_pairs" if old == 0 else "reference_strict_pairs"] += 1
            if old != new:
                ranks["changed_pairs"] += 1
                ranks["ties_broken" if old == 0 else "strict_pairs_collapsed_to_ties" if new == 0 else "strict_order_reversals"] += 1
                ranks["near_tie_changes" if abs(reference_gap) <= F(1, 10) else "larger_gap_changes"] += 1
                worst_gap = max(worst_gap, abs(reference_gap))
    reference_best = [i for i, value in enumerate(expected) if value == min(expected)]
    candidate_best = [i for i, value in enumerate(actual) if value == min(actual)]
    ranks["candidate_set_order_changed"] = int(bool(ranks["changed_pairs"]))
    ranks["best_set_changed"] = int(reference_best != candidate_best)
    return {"display_all_union_cells": error_summary(all_errors),
            "display_positive_demand_cells": error_summary(demand_errors),
            "exact_pressure_mae": float(exact_error_sum/observations),
            "exact_pressure_max": float(exact_error_max), "region_cells": len(region),
            "rank_counts": dict(ranks),
            "reference_candidate_deficits": list(map(str, reference_deficits)),
            "candidate_deficits": list(map(str, candidate_deficits)),
            "reference_candidate_mean_exact_pressure": list(map(str, expected)),
            "candidate_mean_exact_pressure": list(map(str, actual)),
            "reference_best_indices": reference_best, "best_indices": candidate_best,
            "selected_reference_regret_pressure_points": str(expected[candidate_best[0]]-min(expected)),
            "max_changed_reference_gap_pressure_points": str(worst_gap)}


def complete_coverage_run(scenario, mode, kernel=None):
    source_map, target_map = scenario.pair()
    source_layer, target_layer = (1, 0) if scenario.direction == "up" else (0, 1)
    if mode == "local_p8":
        kwargs = {"mode": "local_quantized", "local_length": similarity_unit(source_map),
                  "fractional_bits": 8}
        bits = 8
    elif mode == "adaptive16":
        kwargs, bits = {"mode": "adaptive", "initial_bits": 16}, None
    else:
        bits = int(mode.split("p")[1])
        kwargs = {"mode": "quantized", "fractional_bits": bits}
    result = []
    for q, r in scenario.coordinates:
        source = GeometryAddress("default_dream_v1", "default", source_layer, q, r)
        if kernel is None:
            coverage = sampled_rational_coverage(source, target_layer, source_map, target_map, **kwargs)
        else:
            coverage = _sampled(source, target_layer, source_map, target_map, kernel, bits,
                                kernel.local_length if mode == "local_p8" else None)
        result.append(coverage)
    return result


def time_inventory(inventory, repeats):
    scenarios = [Scenario.from_mapping(record["scenario"]) for record in inventory["cases"]]
    kernels = {(i, mode): compiler(*scenario.pair(), mode)
               for i, scenario in enumerate(scenarios) for mode in MODES}
    for repeat in range(repeats):
        rng = random.Random(inventory["seed"]+repeat*100003)
        modes, indices = list(MODES), list(range(len(scenarios)))
        rng.shuffle(modes)
        rng.shuffle(indices)
        for mode in modes:
            for index in indices:
                scenario = scenarios[index]
                measurement = inventory["cases"][index]["measurements"][mode]
                scopes = ["compile_inclusive", "compiled_reuse"]
                rng.shuffle(scopes)
                for scope in scopes:
                    start = perf_counter()
                    result = complete_coverage_run(scenario, mode,
                        kernels[index, mode] if scope == "compiled_reuse" else None)
                    elapsed = (perf_counter()-start)*1000
                    histograms = [[[member.target.q, member.target.r, member.hit_count]
                                   for member in value.members] for value in result]
                    if histograms != measurement["coverage_hit_histograms"]:
                        raise AssertionError(f"timed replay changed output: {scenario.name}/{mode}/{scope}")
                    if any(sum(m.hit_count for m in value.members) != 96
                           or sum(m.weight for m in value.members) != 1
                           or sum(m.weight_q16 for m in value.members) != 65536 for value in result):
                        raise AssertionError("coverage count/share/Q16 mass changed")
                    measurement["timing_ms"][scope].append(elapsed)
        print(json.dumps({"inventory": inventory["name"], "timing_round": repeat+1}), flush=True)


def summarize(inventory):
    result = {}
    for cohort in ("main", "control", "stress"):
        records = [row for row in inventory["cases"] if row["scenario"]["cohort"] == cohort]
        result[cohort] = {}
        for mode in MODES:
            totals, errors, tvs = Counter(), [], []
            all_errors, demand_errors, ranks = Counter(), Counter(), Counter()
            worst_regret = F(0)
            for record in records:
                row = record["measurements"][mode]
                structure, pressure = row["structure"], row["pressure"]
                totals.update(structure["counts"])
                errors.extend(structure["per_source_structural_error"])
                tvs.extend(structure["per_source_tv"])
                all_errors.update(pressure["display_all_union_cells"]["abs_error_histogram"])
                demand_errors.update(pressure["display_positive_demand_cells"]["abs_error_histogram"])
                ranks.update(pressure["rank_counts"])
                worst_regret = max(worst_regret, F(pressure["selected_reference_regret_pressure_points"]))
            timings = {scope: [sum(record["measurements"][mode]["timing_ms"][scope][i]
                                  for record in records)
                               for i in range(len(records[0]["measurements"][mode]["timing_ms"][scope]))]
                       for scope in ("compile_inclusive", "compiled_reuse")}
            result[cohort][mode] = {"counts": dict(totals),
                **summarize_structure(totals, errors, tvs),
                "pressure_all_union_cells": error_summary(all_errors),
                "pressure_positive_demand_cells": error_summary(demand_errors),
                "rank_counts": dict(ranks),
                "worst_selected_reference_regret_pressure_points": str(worst_regret),
                "timing_round_totals_ms": timings,
                "timing_median_ms": {scope: median(values) if values else None
                                     for scope, values in timings.items()}}
    return result


def world_transform(mapping, factor, shift=(F(0), F(0))):
    """Apply the same positive world-unit change to frames and radial supports."""
    frame = replace(mapping.frame,
        matrix=tuple(tuple(factor*value for value in row) for row in mapping.frame.matrix),
        origin=tuple(factor*value+delta for value, delta in zip(mapping.frame.origin, shift)))
    twists = tuple(replace(twist,
        center=tuple(factor*value+delta for value, delta in zip(twist.center, shift)),
        radius_squared=factor*factor*twist.radius_squared) for twist in mapping.twists)
    return RationalLayerMap(frame, twists)


def invariance_checks(frozen):
    transforms = (("unit_1_over_256", F(1, 256), (F(0), F(0))),
                  ("unit_1_over_65536", F(1, 65536), (F(0), F(0))),
                  ("unit_3_over_17", F(3, 17), (F(0), F(0))),
                  ("fractional_translation", F(1), (F(1, 3), F(-2, 7))),
                  ("huge_translation", F(1), (F(1 << 160), F(-(1 << 160)))))
    rows = []
    for inventory in frozen["inventories"]:
        for record in inventory["cases"]:
            scenario = Scenario.from_mapping(record["scenario"])
            source, target = scenario.pair()
            baseline = labels_for(source, target, scenario.coordinates, "local_p8")
            checks = {}
            for name, factor, shift in transforms:
                mapped = labels_for(world_transform(source, factor, shift),
                                    world_transform(target, factor, shift),
                                    scenario.coordinates, "local_p8")
                checks[name] = changed_labels(baseline, mapped)
            for name, a, b in (("source_reanchor", source.reanchor((F(1, 3), F(1, 7))), target),
                               ("target_reanchor", source, target.reanchor((F(1, 3), F(1, 7)))),
                               ("both_reanchor", source.reanchor((F(17, 19), F(-23, 29))),
                                target.reanchor((F(-31, 37), F(41, 43))))):
                checks[name] = changed_labels(baseline, labels_for(a, b, scenario.coordinates, "local_p8"))
            rows.append({"inventory": inventory["name"], "case": scenario.name,
                         "labels_per_transform": sum(map(len, baseline)), "changed_labels": checks})
    return {"cases": rows, "total_cases": len(rows),
            "tested_labels": sum(row["labels_per_transform"]*len(row["changed_labels"]) for row in rows),
            "changed_labels": sum(sum(row["changed_labels"].values()) for row in rows)}


def old_reanchor_witnesses(frozen):
    records = frozen["inventories"][0]["cases"]
    rows = []
    for name, bits in (("d1_compact_weak_up", 8), ("d1_medium_up", 12)):
        record = next(row for row in records if row["scenario"]["name"] == name)
        scenario = Scenario.from_mapping(record["scenario"])
        source, target = scenario.pair()
        target_after = target.reanchor((F(1, 3), F(1, 7)))
        before = labels_for(source, target, scenario.coordinates, f"world_p{bits}")
        after = labels_for(source, target_after, scenario.coordinates, f"world_p{bits}")
        local_before = labels_for(source, target, scenario.coordinates, "local_p8")
        local_after = labels_for(source, target_after, scenario.coordinates, "local_p8")
        rows.append({"case": name, "old_bits": bits, "sample_count": sum(map(len, before)),
                     "old_changed_labels": changed_labels(before, after),
                     "local_p8_changed_labels": changed_labels(local_before, local_after)})
    return rows


def stencil_cache_checks(frozen):
    """A cleared cache, new pair object and changed visit order keep all labels."""
    rows = []
    for inventory in frozen["inventories"]:
        record = next(row for row in inventory["cases"]
                      if row["scenario"]["name"] == "d2_medium_up")
        scenario = Scenario.from_mapping(record["scenario"])
        source, target = scenario.pair()
        _source_stencil.cache_clear()
        cold = labels_for(source, target, scenario.coordinates, "local_p8")
        after_cold = _source_stencil.cache_info()._asdict()
        # Recompile the pair, then visit the very same cells in reverse order.
        repeated = labels_for(source, target, scenario.coordinates, "local_p8")
        reversed_run = tuple(reversed(labels_for(source, target,
                                    tuple(reversed(scenario.coordinates)), "local_p8")))
        after_warm = _source_stencil.cache_info()._asdict()
        _source_stencil.cache_clear()
        cleared_again = labels_for(source, target, scenario.coordinates, "local_p8")
        changes = {"new_pair": changed_labels(cold, repeated),
                   "reverse_cell_order": changed_labels(cold, reversed_run),
                   "cleared_again": changed_labels(cold, cleared_again)}
        if any(changes.values()) or after_cold["misses"] != 1 or after_warm["misses"] != 1:
            raise AssertionError("disposable source stencil changed labels or failed to reuse geometry")
        rows.append({"inventory": inventory["name"], "case": scenario.name,
                     "labels_per_replay": sum(map(len, cold)), "changed_labels": changes,
                     "after_cleared_cache_pass": after_cold, "after_new_pair_and_reverse_order": after_warm})
    return {"cold_definition": "only the source-stencil cache is explicitly cleared; process and imported modules remain warm",
            "warm_definition": "the same normalized stencil is present while pair objects and source-cell order can change",
            "timed": False, "cases": rows}


def save(path, document):
    # Maps and original labeled references already live at INPUT_BLOB. Persist
    # only case identifiers, measurements and replay evidence in the new report.
    output = {**document, "inventories": [
        {**inventory, "cases": [
            {**record, "scenario": {key: value for key, value in record["scenario"].items()
                                    if key not in {"lower_map", "upper_map", "coordinates"}},
             "source_cells": len(record["scenario"]["coordinates"])}
            for record in inventory["cases"]]}
        for inventory in document["inventories"]]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":"))+"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / INPUT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--previous-result", type=Path,
                        help="Optional pre-cache measurement to compare all saved hit histograms")
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("repeats must be positive")
    frozen = json.loads(args.input.read_text())
    previous = json.loads(args.previous_result.read_text()) if args.previous_result else None
    previous_cases = ({(inventory["name"], row["scenario"]["name"]): row
                       for inventory in previous["inventories"] for row in inventory["cases"]}
                      if previous else {})
    document = {"schema": "nollm_local_p8_frozen_comparison_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(),
        "input_source": {"path": INPUT_PATH, "blob": INPUT_BLOB,
                         "projection": frozen.get("schema") == "nollm_local_p8_frozen_input_projection_v1"},
        "modes": MODES, "repeats": args.repeats, "sample_count": 96,
        "local_unit": "verified exact rational source-affine similarity length",
        "timing_scope": {"compile_inclusive": "one public coverage call per source cell; includes pair compilation, 96 labels, addresses, exact shares and Q16 projection",
                         "compiled_reuse": "one pair compilation outside timing, then 96 labels, addresses, exact shares and Q16 projection for every source cell"},
        "timing_cache_state": "warm process after full case/pressure evaluation; source-stencil LRU and existing geometry caches may be reused in both timing scopes; not a cold-start latency measurement",
        "reference_scope": "previously frozen exact-map sampled labels; equal-weight source metrics, not continuous area or measured production traffic",
        "stencil_cache_checks": stencil_cache_checks(frozen),
        "inventories": []}
    if previous:
        document["before_cache_comparison"] = {
            "basis": "earlier same-input run before the disposable source-stencil cache",
            "generated_at_utc": previous["generated_at_utc"],
            "histogram_cases_compared": 0, "histogram_source_cells_compared": 0,
            "changed_histograms": 0,
            "main_summaries": {inventory["name"]: inventory["summary"]["main"]
                               for inventory in previous["inventories"]}}
    for original in frozen["inventories"]:
        inventory = {"name": original["name"], "seed": original["seed"], "cases": []}
        for record in original["cases"]:
            scenario = Scenario.from_mapping(record["scenario"])
            source, target = scenario.pair()
            reference = normalized_labels(record["reference_labels"])
            case = {"scenario": record["scenario"], "local_length": str(similarity_unit(source)),
                    "measurements": {}}
            for mode in MODES:
                labels = labels_for(source, target, scenario.coordinates, mode)
                validate_label_domain(labels, 0 if scenario.direction == "up" else 1)
                case["measurements"][mode] = {
                    "structure": structural_metrics(reference, labels),
                    "pressure": compare_pressure(record, scenario, mode),
                    "coverage_hit_histograms": hit_histograms(labels),
                    "timing_ms": {"compile_inclusive": [], "compiled_reuse": []}}
            if previous:
                earlier = previous_cases[inventory["name"], scenario.name]
                before = earlier["measurements"]["local_p8"]["coverage_hit_histograms"]
                after = case["measurements"]["local_p8"]["coverage_hit_histograms"]
                changed = sum(a != b for a, b in zip(before, after))
                if len(before) != len(after) or changed:
                    raise AssertionError(f"stencil cache changed coverage: {scenario.name}")
                document["before_cache_comparison"]["histogram_cases_compared"] += 1
                document["before_cache_comparison"]["histogram_source_cells_compared"] += len(after)
                document["before_cache_comparison"]["changed_histograms"] += changed
            inventory["cases"].append(case)
        time_inventory(inventory, args.repeats)
        inventory["summary"] = summarize(inventory)
        document["inventories"].append(inventory)
        save(args.output, document)
        print(json.dumps({"inventory": inventory["name"], "cases": len(inventory["cases"]),
                          "main_summary": inventory["summary"]["main"]}), flush=True)
    document["old_reanchor_witnesses"] = old_reanchor_witnesses(frozen)
    document["invariance"] = invariance_checks(frozen)
    save(args.output, document)
    ok = (document["invariance"]["changed_labels"] == 0
          and all(row["old_changed_labels"] == 1 and row["local_p8_changed_labels"] == 0
                  for row in document["old_reanchor_witnesses"]))
    print(json.dumps({"output": str(args.output), "invariance_changed_labels": document["invariance"]["changed_labels"],
                      "invariance_tested_labels": document["invariance"]["tested_labels"],
                      "old_reanchor_witnesses": document["old_reanchor_witnesses"], "checks_passed": ok}), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
