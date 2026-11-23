"""Cost and structural error of accepted, one-pass rational-map quantization.

The seeded stratified inventories are experiments, not a production distribution.
Reference preparation is separate from quantized evaluation and timing. Every
fixed precision retains its actual labels, including missing or additional edges.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from fractions import Fraction as F
import json
from math import ceil
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
from geometry.quantized_rational_kernel import compile_quantized_pair
from geometry.rational_affine_kernel import compile_affine_pair
from geometry.rational_coverage import (
    _sampled, nearest_axial_rational, pressure_display, rational_pressure_score,
    rational_sample_numerators, rational_sample_offsets, sampled_rational_coverage,
)
from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist


DEFAULT_OUTPUT = ROOT / "lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json"
MAIN_BITS = (*range(2, 17), 20, 24, 32)
HOLDOUT_BITS = (6, 8, 10, 12, 16, 24)


@dataclass(frozen=True)
class Scenario:
    name: str
    cohort: str
    depth: int
    regime: str
    direction: str
    lower: RationalLayerMap
    upper: RationalLayerMap
    coordinates: tuple[tuple[int, int], ...]

    def pair(self):
        return (self.lower, self.upper) if self.direction == "up" else (self.upper, self.lower)

    def mapping(self):
        return {"name": self.name, "cohort": self.cohort, "depth": self.depth,
                "regime": self.regime, "direction": self.direction,
                "lower_map": self.lower.to_mapping(), "upper_map": self.upper.to_mapping(),
                "coordinates": self.coordinates}

    @classmethod
    def from_mapping(cls, value):
        return cls(value["name"], value["cohort"], value["depth"], value["regime"],
                   value["direction"], RationalLayerMap.from_mapping(value["lower_map"]),
                   RationalLayerMap.from_mapping(value["upper_map"]),
                   tuple(tuple(point) for point in value["coordinates"]))


def world_shift(mapping, anchor):
    def shifted(point):
        return tuple(a+b for a, b in zip(point, anchor))
    return RationalLayerMap(replace(mapping.frame, origin=shifted(mapping.frame.origin)),
                            tuple(replace(t, center=shifted(t.center)) for t in mapping.twists))


def build_scenarios(seed):
    """Freeze inputs before observing any precision's errors or timings."""
    rng = random.Random(seed)
    pool = [(q, r) for q in range(-2, 3) for r in range(-2, 3)
            if max(abs(q), abs(r), abs(q+r)) <= 2]
    regimes = (("compact_weak", F(2), F(1, 20), F(7, 8), F(1, 11)),
               ("medium", F(9), F(1, 5), F(9, 8), F(-1, 7)),
               ("wide_strong", F(36), F(3, 5), F(5, 4), F(2, 9)))
    scenarios = []
    for depth in (1, 2, 3, 5):
        for regime, radius, strength, scale, rotation in regimes:
            lower_frame = RationalAffine.similarity(scale, rotation,
                origin=(F(rng.randrange(-8, 9), 17), F(rng.randrange(-8, 9), 19)),
                local_anchor=(F(rng.randrange(-3, 4), 13), F(rng.randrange(-3, 4), 11)))
            upper_frame = RationalAffine.similarity(F(7, 6), -rotation/F(2),
                origin=(F(rng.randrange(-8, 9), 19), F(rng.randrange(-8, 9), 17)),
                local_anchor=(F(rng.randrange(-3, 4), 11), F(rng.randrange(-3, 4), 13)))
            twists = tuple(RationalRadialTwist(
                (F(rng.randrange(-7, 8), 11), F(rng.randrange(-7, 8), 13)),
                radius*F(7+(i % 3), 8), strength*F((-1)**i*(7+i), 8))
                for i in range(depth))
            split = (depth+1)//2
            lower, upper = RationalLayerMap(lower_frame, twists[:split]), RationalLayerMap(upper_frame, twists[split:])
            coordinates = tuple(rng.sample(pool, 8))
            for direction in ("up", "down"):
                scenarios.append(Scenario(f"d{depth}_{regime}_{direction}", "main", depth,
                                           regime, direction, lower, upper, coordinates))
    # Controls share fixed inputs with designated cases, without entering main rates.
    chosen = next(s for s in scenarios if s.name == "d2_medium_up")
    scenarios.append(replace(chosen, name="affine_control", cohort="control", depth=0,
                             lower=replace(chosen.lower, twists=()), upper=replace(chosen.upper, twists=())))
    big = 1 << 160
    scenarios.append(replace(chosen, name="huge_common_anchor_control", cohort="control",
                             lower=world_shift(chosen.lower, (big, -big)),
                             upper=world_shift(chosen.upper, (big, -big))))
    scenarios.append(replace(chosen, name="representation_reanchor_control", cohort="control",
                             lower=chosen.lower.reanchor((F(17, 19), F(-23, 29))),
                             upper=chosen.upper.reanchor((F(-31, 37), F(41, 43)))))
    small = RationalAffine.similarity("1/10", "1/7")
    tip = max((small.forward(point) for point in rational_sample_offsets()), key=lambda point: 2*point[0]+point[1])
    boundary = F(1, 2)+F(1, 1 << 40), F(0)
    edge_frame = replace(small, origin=(boundary[0]-tip[0], -tip[1]))
    edge = RationalLayerMap(edge_frame, (RationalRadialTwist(boundary, F(1, 1 << 20), "1/7"),))
    scenarios.append(Scenario("one_hit_delta_2_pow_minus_40", "stress", 1, "near_face", "up",
                               edge, RationalLayerMap(), ((0, 0),)))
    strong = tuple(RationalRadialTwist((F(i % 2, 5), F((-1)**i, 7)), F(4, 3), F((-1)**i*7, 3))
                   for i in range(5))
    scenarios.append(Scenario("strong_local_d5", "stress", 5, "strong_local", "up",
        RationalLayerMap(RationalAffine.similarity("4/5", "1/13", origin=("1/7", "-2/11")), strong),
        RationalLayerMap(RationalAffine(origin=("-1/3", "1/5"))), ((0, 0), (1, -1))))
    return scenarios


def compiler(source, target, mode):
    return (compile_adaptive_pair(source, target, initial_bits=16)
            if mode == "adaptive16" else compile_quantized_pair(source, target, fractional_bits=int(mode[1:])))


def labels_for(source, target, coordinates, mode):
    kernel = compiler(source, target, mode)
    return tuple(kernel.targets(q, r, rational_sample_numerators(), 36) for q, r in coordinates)


def candidate_maps(lower):
    origin = lower.frame.origin
    return [("current", lower),
            ("shift_positive", replace(lower, frame=replace(lower.frame,
                origin=(origin[0]+F(1, 5), origin[1]-F(1, 7))))),
            ("shift_negative", replace(lower, frame=replace(lower.frame,
                origin=(origin[0]-F(1, 7), origin[1]+F(1, 5)))))]


def prepare_case(scenario, seed, index):
    source, target = scenario.pair()
    geometry = labels_for(source, target, scenario.coordinates, "adaptive16")
    q, r = scenario.coordinates[0]
    dq, dr = rational_sample_offsets()[0]
    checked = nearest_axial_rational(*target.inverse(source.forward((q+dq, r+dr))))
    if checked != geometry[0][0]:
        raise AssertionError(f"independent exact reference mismatch: {scenario.name}")
    candidates = []
    reference_targets = set()
    for name, mapping in candidate_maps(scenario.lower):
        candidate_labels = (geometry if name == "current" and scenario.direction == "up"
                            else labels_for(mapping, scenario.upper, scenario.coordinates, "adaptive16"))
        reference_targets.update(point for values in candidate_labels for point in values)
        candidates.append({"name": name, "lower_map": mapping.to_mapping(), "reference_labels": candidate_labels})
    rng = random.Random(seed*1000+index)
    lower_units = [rng.randrange(1, 10) for _ in scenario.coordinates]
    upper_units = [[q, r, rng.randrange(1, 9)] for q, r in sorted(reference_targets)]
    affine = compile_affine_pair(replace(source, twists=()), replace(target, twists=()))
    affine_labels = tuple(affine.targets(q, r, rational_sample_numerators(), 36) for q, r in scenario.coordinates)
    return {"scenario": scenario.mapping(), "reference_labels": geometry,
            "independent_fraction_checks": 1,
            "reference_multi_target_cells": sum(len(set(values)) > 1 for values in geometry),
            "twisted_vs_affine_label_changes": sum(a != b for av, bv in zip(geometry, affine_labels) for a, b in zip(av, bv)),
            "pressure": {"lower_units": lower_units, "upper_units": upper_units, "kappa": "1",
                         "objective": "minimize mean exact pressure on the fixed positive-demand target set; first candidate wins an exact tie",
                         "near_tie_mean_pressure_gap_points": "1/10", "candidates": candidates}, "measurements": {}}


def normalized_labels(values):
    return tuple(tuple(tuple(point) for point in row) for row in values)


def structural_metrics(reference, candidate):
    if len(reference) != len(candidate):
        raise ValueError("the precision experiment must retain every source cell")
    totals = Counter(source_cells=len(reference), samples=sum(map(len, reference)))
    edits, tvs, first_change = [], [], None
    for index, (expected, actual) in enumerate(zip(reference, candidate)):
        expected, actual = tuple(map(tuple, expected)), tuple(map(tuple, actual))
        if len(expected) != 96 or len(actual) != 96:
            raise ValueError("the precision experiment must retain all 96 samples")
        a, b = Counter(expected), Counter(actual)
        sa, sb = set(a), set(b)
        fn, fp, union = sa-sb, sb-sa, sa|sb
        flips = sum(x != y for x, y in zip(expected, actual))
        tv = sum(abs(a[c]-b[c]) for c in union)//2
        edit = len(fn)+len(fp)
        totals.update(reference_edges=len(sa), candidate_edges=len(sb), false_negative_edges=len(fn),
                      false_positive_edges=len(fp), union_edges=len(union), intersection_edges=len(sa & sb),
                      label_mismatches=flips, tv_hit_units=tv,
                      lost_edge_hit_units=sum(a[c] for c in fn), false_edge_hit_units=sum(b[c] for c in fp),
                      dominant_set_changed=int({c for c in sa if a[c] == max(a.values())}
                                               != {c for c in sb if b[c] == max(b.values())}))
        edits.append(edit/len(union))
        tvs.append(tv/96)
        if first_change is None and (fn or fp or flips):
            first_change = {"source_index": index, "reference_hits": [[*c, n] for c, n in sorted(a.items())],
                            "candidate_hits": [[*c, n] for c, n in sorted(b.items())],
                            "label_mismatches": flips}
    return {"counts": dict(totals), "per_source_structural_error": edits,
            "per_source_tv": tvs, "first_change": first_change, **summarize_structure(totals, edits, tvs)}


def percentile(values, proportion):
    return sorted(values)[max(0, ceil(len(values)*proportion)-1)] if values else None


def summarize_structure(totals, edits, tvs):
    def ratio(n, d):
        return totals[n]/totals[d] if totals[d] else 0
    return {"structural_error_micro": (totals["false_negative_edges"]+totals["false_positive_edges"])/totals["union_edges"],
            "fn_over_reference_edges": ratio("false_negative_edges", "reference_edges"),
            "fp_over_candidate_edges": ratio("false_positive_edges", "candidate_edges"),
            "fp_over_reference_edges": ratio("false_positive_edges", "reference_edges"),
            "label_mismatch_rate": ratio("label_mismatches", "samples"),
            "mean_tv": totals["tv_hit_units"]/(96*totals["source_cells"]),
            "lost_edge_mass_mean": totals["lost_edge_hit_units"]/(96*totals["source_cells"]),
            "false_edge_mass_mean": totals["false_edge_hit_units"]/(96*totals["source_cells"]),
            "dominant_set_changed_rate": ratio("dominant_set_changed", "source_cells"),
            "structural_error_per_source_p95": percentile(edits, .95),
            "structural_error_per_source_max": max(edits, default=0),
            "tv_per_source_p95": percentile(tvs, .95), "tv_per_source_max": max(tvs, default=0)}


def pressure_values(labels, lower_units, demands, region):
    if len(labels) != len(lower_units):
        raise ValueError("pressure labels must retain every inventory source cell")
    support = defaultdict(F)
    for values, units in zip(labels, lower_units):
        for target, hits in Counter(map(tuple, values)).items():
            support[target] += F(units*hits, 96)
    exact = {c: rational_pressure_score(demands.get(c, 0), support[c]) for c in region}
    display = {c: pressure_display(value) for c, value in exact.items()}
    deficit = sum((max(F(demand)-support[c], 0) for c, demand in demands.items()), F(0))
    return exact, display, deficit


def error_summary(histogram):
    histogram = Counter({int(k): v for k, v in histogram.items()})
    count = sum(histogram.values())
    values = sorted(histogram)
    cumulative, p95 = 0, 0
    for value in values:
        cumulative += histogram[value]
        if cumulative >= ceil(.95*count):
            p95 = value
            break
    return {"observations": count, "mae": sum(value*histogram[value] for value in values)/count if count else None,
            "p95": p95 if count else None, "max": max(values, default=None),
            "changed": count-histogram.get(0, 0), "abs_error_histogram": dict(sorted(histogram.items()))}


def compare_pressure(record, scenario, mode):
    data = record["pressure"]
    demands = {(q, r): units for q, r, units in data["upper_units"]}
    reference, approximate, region = [], [], set(demands)
    for item in data["candidates"]:
        reference_labels = normalized_labels(item["reference_labels"])
        labels = (reference_labels if mode == "adaptive16" else labels_for(
            RationalLayerMap.from_mapping(item["lower_map"]), scenario.upper, scenario.coordinates, mode))
        validate_label_domain(labels, 0)
        reference.append(reference_labels)
        approximate.append(labels)
        region.update(c for values in reference_labels+labels for c in values)
    expected, actual, expected_deficits, actual_deficits = [], [], [], []
    all_errors, demand_errors = Counter(), Counter()
    exact_error_sum, exact_error_max, observations = F(0), F(0), 0
    for expected_labels, actual_labels in zip(reference, approximate):
        ep, ed, er = pressure_values(expected_labels, data["lower_units"], demands, region)
        ap, ad, ar = pressure_values(actual_labels, data["lower_units"], demands, region)
        expected_deficits.append(er)
        actual_deficits.append(ar)
        expected.append(sum((ep[c] for c in demands), F(0))/len(demands))
        actual.append(sum((ap[c] for c in demands), F(0))/len(demands))
        for c in region:
            error = abs(ed[c]-ad[c])
            all_errors[error] += 1
            if demands.get(c, 0) > 0:
                demand_errors[error] += 1
            exact_error_sum += abs(ep[c]-ap[c])
            exact_error_max = max(exact_error_max, abs(ep[c]-ap[c]))
            observations += 1
    signs = lambda value: (value > 0)-(value < 0)
    ranks = Counter(candidate_sets=1)
    max_flipped_reference_gap = F(0)
    for i in range(len(expected)):
        for j in range(i):
            gap, changed = expected[i]-expected[j], actual[i]-actual[j]
            old, new = signs(gap), signs(changed)
            ranks["reference_tied_pairs" if old == 0 else "reference_strict_pairs"] += 1
            if old != new:
                ranks["changed_pairs"] += 1
                ranks["ties_broken" if old == 0 else "strict_pairs_collapsed_to_ties" if new == 0 else "strict_order_reversals"] += 1
                ranks["near_tie_changes" if abs(gap) <= F(1, 10) else "larger_gap_changes"] += 1
                max_flipped_reference_gap = max(max_flipped_reference_gap, abs(gap))
    best_ref = [i for i, value in enumerate(expected) if value == min(expected)]
    best_approx = [i for i, value in enumerate(actual) if value == min(actual)]
    ranks["candidate_set_order_changed"] = int(bool(ranks["changed_pairs"]))
    ranks["best_set_changed"] = int(best_ref != best_approx)
    chosen_regret = expected[best_approx[0]]-min(expected)
    return {"display_all_union_cells": error_summary(all_errors),
            "display_positive_demand_cells": error_summary(demand_errors),
            "exact_pressure_mae": float(exact_error_sum/observations), "exact_pressure_max": float(exact_error_max),
            "region_cells": len(region), "rank_counts": dict(ranks),
            "reference_candidate_deficits": list(map(str, expected_deficits)),
            "candidate_deficits": list(map(str, actual_deficits)),
            "reference_candidate_mean_exact_pressure": list(map(str, expected)),
            "candidate_mean_exact_pressure": list(map(str, actual)), "reference_best_indices": best_ref,
            "best_indices": best_approx, "selected_reference_regret_pressure_points": str(chosen_regret),
            "max_changed_reference_gap_pressure_points": str(max_flipped_reference_gap)}


def validate_label_domain(labels, target_layer):
    """Out-of-domain output is a recorded failed case, never a discarded sample."""
    for q, r in {point for values in labels for point in values}:
        GeometryAddress("default_dream_v1", "default", target_layer, q, r)


def evaluate_case(record, modes):
    scenario = Scenario.from_mapping(record["scenario"])
    source, target = scenario.pair()
    reference = normalized_labels(record["reference_labels"])
    for mode in modes:
        if mode in record["measurements"]:
            continue
        try:
            labels = reference if mode == "adaptive16" else labels_for(source, target, scenario.coordinates, mode)
            validate_label_domain(labels, 0 if scenario.direction == "up" else 1)
            structural = structural_metrics(reference, labels)
            record["measurements"][mode] = {"structure": structural,
                "pressure": compare_pressure(record, scenario, mode),
                "coverage_hit_histograms": [[[q, r, count] for (q, r), count in sorted(Counter(row).items())] for row in labels],
                "timing_ms": {"compile_inclusive": [], "compiled_reuse": []}}
        except Exception as exc:
            record["measurements"][mode] = {"error": {"type": type(exc).__name__, "message": str(exc)}}


def complete_coverage_run(scenario, mode, kernel=None):
    source_map, target_map = scenario.pair()
    source_layer, target_layer = (1, 0) if scenario.direction == "up" else (0, 1)
    bits = None if mode == "adaptive16" else int(mode[1:])
    result = []
    for q, r in scenario.coordinates:
        source = GeometryAddress("default_dream_v1", "default", source_layer, q, r)
        if kernel is None:
            kwargs = {"mode": "adaptive", "initial_bits": 16} if bits is None else {"mode": "quantized", "fractional_bits": bits}
            result.append(sampled_rational_coverage(source, target_layer, source_map, target_map, **kwargs))
        else:
            result.append(_sampled(source, target_layer, source_map, target_map, kernel, bits))
    return result


def time_inventory(inventory, repeats, write_progress):
    modes, records = inventory["modes"], inventory["cases"]
    scenarios = [Scenario.from_mapping(record["scenario"]) for record in records]
    kernels = {(i, mode): compiler(*scenario.pair(), mode) for i, scenario in enumerate(scenarios) for mode in modes}
    orders = inventory.setdefault("timing_orders", [])
    for repeat in range(len(orders), repeats):
        rng = random.Random(inventory["seed"]+repeat*100_003)
        mode_order, case_order = list(modes), list(range(len(records)))
        rng.shuffle(mode_order)
        rng.shuffle(case_order)
        order_record = {"round": repeat, "mode_order": mode_order,
                        "case_order": [scenarios[i].name for i in case_order], "scope_orders": {}}
        for mode in mode_order:
            for i in case_order:
                record, scenario = records[i], scenarios[i]
                measurement = record["measurements"][mode]
                if "error" in measurement:
                    continue
                scopes = ["compile_inclusive", "compiled_reuse"]
                rng.shuffle(scopes)
                order_record["scope_orders"][scenario.name+"/"+mode] = scopes
                for scope in scopes:
                    start = perf_counter()
                    try:
                        result = complete_coverage_run(scenario, mode,
                            kernels[i, mode] if scope == "compiled_reuse" else None)
                    except Exception as exc:
                        measurement["error"] = {"phase": "timing", "type": type(exc).__name__, "message": str(exc)}
                        break
                    elapsed = (perf_counter()-start)*1000
                    histograms = [[[member.target.q, member.target.r, member.hit_count] for member in value.members] for value in result]
                    if histograms != measurement["coverage_hit_histograms"]:
                        raise AssertionError(f"nondeterministic replay: {scenario.name}/{mode}/{scope}")
                    measurement["timing_ms"][scope].append(elapsed)
        orders.append(order_record)
        write_progress()
        print(json.dumps({"inventory": inventory["name"], "timing_round": repeat+1, "completed": True}), flush=True)


def aggregate(inventory):
    summaries = {}
    for cohort in ("main", "control", "stress"):
        records = [r for r in inventory["cases"] if r["scenario"]["cohort"] == cohort]
        summaries[cohort] = {}
        for mode in inventory["modes"]:
            failures = [{"case": r["scenario"]["name"], "error": r["measurements"].get(mode, {}).get("error")}
                        for r in records if "error" in r["measurements"].get(mode, {}) or mode not in r["measurements"]]
            if failures:
                summaries[cohort][mode] = {"complete": False, "failures": failures}
                continue
            totals, edits, tvs, all_hist, demand_hist, ranks = Counter(), [], [], Counter(), Counter(), Counter()
            worst_regret = F(0)
            timings = {scope: [] for scope in ("compile_inclusive", "compiled_reuse")}
            for record in records:
                measurement = record["measurements"][mode]
                st, pr = measurement["structure"], measurement["pressure"]
                totals.update(st["counts"])
                edits.extend(st["per_source_structural_error"])
                tvs.extend(st["per_source_tv"])
                all_hist.update({int(k): v for k, v in pr["display_all_union_cells"]["abs_error_histogram"].items()})
                demand_hist.update({int(k): v for k, v in pr["display_positive_demand_cells"]["abs_error_histogram"].items()})
                ranks.update(pr["rank_counts"])
                worst_regret = max(worst_regret, F(pr["selected_reference_regret_pressure_points"]))
            for scope in timings:
                lengths = [len(r["measurements"][mode]["timing_ms"][scope]) for r in records]
                if lengths and len(set(lengths)) == 1:
                    timings[scope] = [sum(r["measurements"][mode]["timing_ms"][scope][i] for r in records) for i in range(lengths[0])]
            summaries[cohort][mode] = {"complete": True, "counts": dict(totals),
                **summarize_structure(totals, edits, tvs),
                "pressure_all_union_cells": error_summary(all_hist),
                "pressure_positive_demand_cells": error_summary(demand_hist),
                "rank_counts": dict(ranks), "worst_selected_reference_regret_pressure_points": str(worst_regret),
                "timing_round_totals_ms": timings,
                "timing_median_ms": {scope: median(values) if values else None for scope, values in timings.items()}}
    constraints = {}
    for scope in ("compile_inclusive", "compiled_reuse"):
        options = []
        for tolerance in (.001, .01, .05):
            eligible = [(mode, row) for mode, row in summaries["main"].items()
                        if mode != "adaptive16" and row.get("complete")
                        and row["structural_error_micro"] <= tolerance
                        and row["timing_median_ms"][scope] is not None]
            winner = min(eligible, key=lambda pair: pair[1]["timing_median_ms"][scope]) if eligible else None
            options.append({"structural_error_limit": tolerance, "eligible_modes": [mode for mode, _ in eligible],
                            "observed_minimum_median_cost_mode": winner[0] if winner else None})
        constraints[scope] = options
    return {"cohorts": summaries, "observed_cost_constraint_solutions": constraints}


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":"))+"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prepare", "evaluate", "time", "all"), default="all")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    if args.phase in {"prepare", "all"}:
        if args.output.exists():
            parser.error("output already exists; use evaluate/time to continue its frozen inventory")
        document = {"schema": "nollm_quantized_structure_benchmark_v1", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version, "platform": platform.platform(),
            "execution": "fixed p, signed half-even nonlinear pass; no certification, escalation or exact repair; affine stays integer-exact",
            "inventory_design": "24 strata: depths 1/2/3/5, three radius/strength/scale regimes, both directions; 8 seeded cells each",
            "structure_definition": "source-target sampled edges; E_struct=(FN+FP)/|reference union candidate|; every source has 96 labels",
            "pressure_scope": "lower-to-upper candidate maps and one fixed complete finite inventory; compare on the reference/candidate footprint union; positive-demand subset also reported",
            "timing_scope": {"compile_inclusive": "complete 96-point coverage objects; compile per source cell",
                             "compiled_reuse": "same complete coverage objects; map-pair kernel compiled once outside timing"},
            "timing_excludes": "reference preparation, metric calculations, equality replay checks, JSON serialization, disk writes, kernel setup for compiled_reuse",
            "limitations": ["seeded stratified experiment, not measured production traffic", "96-sample relationship contract, not continuous overlap truth",
                            "fixed-point errors are deterministic and phase-dependent", "observed minimum medians do not establish a universal optimal precision"],
            "inventories": []}
        save(args.output, document)
        for name, seed, bits in (("main", 20261123, MAIN_BITS), ("holdout", 20261124, HOLDOUT_BITS)):
            inventory = {"name": name, "seed": seed, "modes": [f"q{p}" for p in bits]+["adaptive16"], "cases": []}
            document["inventories"].append(inventory)
            start = perf_counter()
            for index, scenario in enumerate(build_scenarios(seed)):
                inventory["cases"].append(prepare_case(scenario, seed, index))
                save(args.output, document)
            inventory["reference_preparation_seconds"] = perf_counter()-start
            print(json.dumps({"inventory": name, "prepared_cases": len(inventory["cases"]),
                              "reference_preparation_seconds": inventory["reference_preparation_seconds"]}), flush=True)
        save(args.output, document)
    else:
        document = json.loads(args.output.read_text())
    if args.phase in {"evaluate", "all"}:
        for inventory in document["inventories"]:
            start = perf_counter()
            for record in inventory["cases"]:
                evaluate_case(record, inventory["modes"])
                save(args.output, document)
            inventory["evaluation_seconds"] = perf_counter()-start
            inventory["summary"] = aggregate(inventory)
            print(json.dumps({"inventory": inventory["name"], "evaluation_seconds": inventory["evaluation_seconds"]}), flush=True)
        save(args.output, document)
    if args.phase in {"time", "all"}:
        for inventory in document["inventories"]:
            if any(mode not in record["measurements"] for record in inventory["cases"] for mode in inventory["modes"]):
                raise ValueError("run --phase evaluate before timing the frozen inventory")
            time_inventory(inventory, args.repeats, lambda: save(args.output, document))
            inventory["summary"] = aggregate(inventory)
        save(args.output, document)
    print(json.dumps({"output": str(args.output), "phase": args.phase, "inventory_count": len(document["inventories"])}), flush=True)


if __name__ == "__main__":
    main()
