from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
from time import perf_counter


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bounded_quadrature import approximate_hits, sample_offsets  # noqa: E402
from oracle_decimal import coverage  # noqa: E402
from nollm_core import GeometryAddress, clear_physical_coverage_cache, expand_physical_coverage  # noqa: E402


RELATION_THRESHOLD = 0.02


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1)]


def _weights(hits: dict[tuple[int, int], int]) -> dict[tuple[int, int], float]:
    sample_count = sum(hits.values())
    retained = {target: count for target, count in hits.items() if count / sample_count >= RELATION_THRESHOLD}
    retained_count = sum(retained.values())
    return {target: count / retained_count for target, count in retained.items()}


def _metrics(oracle: dict[tuple[int, int], float], approximate: dict[tuple[int, int], float]):
    keys = set(oracle) | set(approximate)
    maximum = max(approximate.values())
    dominant_targets = {target for target, weight in approximate.items() if weight == maximum}
    return (
        sum(oracle[target] for target in oracle.keys() - approximate.keys()),
        sum(approximate[target] for target in approximate.keys() - oracle.keys()),
        0.5 * sum(abs(oracle.get(target, 0) - approximate.get(target, 0)) for target in keys),
        max(oracle, key=oracle.get) in dominant_targets,
        len(approximate),
    )


def validate() -> dict[str, object]:
    fixtures = ((-7, -3), (-2, 5), (0, 0), (3, -4), (9, 2), (100, -77))
    oracle_cases = []
    for layer in range(8):
        for q, r in fixtures:
            for direction, delta in (("coverage_up", -1), ("coverage_down", 1)):
                members = coverage(layer, q, r, layer + delta, 4)
                oracle_cases.append((layer, q, r, direction, delta, {
                    (member.q, member.r): float(member.source_share)
                    for member in members
                }))

    methods = {}
    for subdivision in (3, 4):
        missed, false, variations, dominant, fanouts = [], [], [], [], []
        started = perf_counter()
        for layer, q, r, _direction, delta, oracle in oracle_cases:
            values = _weights(approximate_hits(layer, q, r, layer + delta, subdivision))
            miss, extra, variation, agrees, fanout = _metrics(oracle, values)
            missed.append(miss)
            false.append(extra)
            variations.append(variation)
            dominant.append(agrees)
            fanouts.append(fanout)
        methods[f"m{subdivision}"] = {
            "sample_count": len(sample_offsets(subdivision)),
            "missed_mass_p99": _percentile(missed, 0.99),
            "false_mass_p99": _percentile(false, 0.99),
            "total_variation_p95": _percentile(variations, 0.95),
            "dominant_target_agreement": sum(dominant) / len(dominant),
            "max_fanout": max(fanouts),
            "prototype_elapsed_ms": (perf_counter() - started) * 1000,
        }

    clear_physical_coverage_cache()
    production_elapsed = []
    production_matches = 0
    partition_errors = []
    for layer, q, r, direction, delta, _oracle in oracle_cases:
        started = perf_counter()
        expansion = expand_physical_coverage(
            GeometryAddress("default_dream_v1", "default", layer, q, r), direction
        )
        production_elapsed.append((perf_counter() - started) * 1000)
        prototype = approximate_hits(layer, q, r, layer + delta, 4)
        retained = {target: count for target, count in prototype.items() if count / 96 >= RELATION_THRESHOLD}
        production = {(member.target.q, member.target.r): member.hit_count for member in expansion.members}
        production_matches += production == retained
        partition_errors.append(abs(65536 - expansion.q16_sum))

    selected = methods["m4"]
    checks = {
        "m4_selected_after_m3_tv_failure": methods["m3"]["total_variation_p95"] > 0.05,
        "missed_mass_p99": selected["missed_mass_p99"] <= 0.02,
        "false_mass_p99": selected["false_mass_p99"] <= 0.02,
        "total_variation_p95": selected["total_variation_p95"] <= 0.05,
        "dominant_target_agreement": selected["dominant_target_agreement"] >= 0.95,
        "max_fanout": selected["max_fanout"] <= 8,
        "partition_mass_error": max(partition_errors) == 0,
        "production_matches_independent_prototype": production_matches == len(oracle_cases),
    }
    return {
        "schema_version": "nollm_bounded_approximate_coverage_calibration_v1",
        "fixture_count": len(oracle_cases),
        "relation_threshold": RELATION_THRESHOLD,
        "methods": methods,
        "selected_method": "m4",
        "production": {
            "mean_cell_ms": statistics.fmean(production_elapsed),
            "p95_cell_ms": _percentile(production_elapsed, 0.95),
            "max_cell_ms": max(production_elapsed),
        },
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
