from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import statistics
import sys
from time import perf_counter


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bounded_quadrature import approximate_hits  # noqa: E402
from broad_residue import broad_exact_fixtures, fast_diagnostic_fixtures  # noqa: E402
from oracle_decimal import coverage  # noqa: E402
from nollm_core import (  # noqa: E402
    ACTIVE_APPROXIMATION_POLICY,
    GeometryAddress,
    UnsupportedPhysicalCoverage,
    clear_physical_coverage_cache,
    expand_physical_coverage,
)


POLICIES = (1, 2)
SAMPLE_COUNT = ACTIVE_APPROXIMATION_POLICY.sample_count
MIN_HIT_COUNT = ACTIVE_APPROXIMATION_POLICY.min_hit_count
STORAGE_HEX_RADIUS = ACTIVE_APPROXIMATION_POLICY.storage_hex_radius


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1)]


def _distribution(values: list[float]) -> dict[str, float]:
    return {
        "p50": _percentile(values, 0.50),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "max": max(values),
    }


def _weights(hits: dict[tuple[int, int], int], min_hit_count: int) -> tuple[dict[tuple[int, int], float], float]:
    retained = {target: count for target, count in hits.items() if count >= min_hit_count}
    retained_count = sum(retained.values())
    return ({target: count / retained_count for target, count in retained.items()}, (SAMPLE_COUNT - retained_count) / SAMPLE_COUNT)


def _metrics(oracle: dict[tuple[int, int], float], approximate: dict[tuple[int, int], float]):
    keys = set(oracle) | set(approximate)
    maximum = max(approximate.values())
    dominant_targets = {target for target, weight in approximate.items() if weight == maximum}
    return {
        "missed_mass": sum(oracle[target] for target in oracle.keys() - approximate.keys()),
        "false_mass": sum(approximate[target] for target in approximate.keys() - oracle.keys()),
        "total_variation": 0.5 * sum(abs(oracle.get(target, 0) - approximate.get(target, 0)) for target in keys),
        "dominant_agrees": max(oracle, key=oracle.get) in dominant_targets,
        "fanout": len(approximate),
        "max_support_distance": max(
            min(_hex_distance(target, oracle_target) for oracle_target in oracle)
            for target in approximate
        ),
    }


def _hex_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    q, r = first[0] - second[0], first[1] - second[1]
    return max(abs(q), abs(r), abs(q + r))


def _new_accumulator() -> dict[str, list]:
    return defaultdict(list)


def _record(accumulator: dict[str, list], metrics: dict[str, object], residual: float) -> None:
    for name in ("missed_mass", "false_mass", "total_variation", "fanout", "max_support_distance"):
        accumulator[name].append(metrics[name])
    accumulator["dominant_agrees"].append(metrics["dominant_agrees"])
    accumulator["threshold_residual"].append(residual)


def _summarize(accumulator: dict[str, list]) -> dict[str, object]:
    return {
        "fixture_count": len(accumulator["missed_mass"]),
        "missed_mass": _distribution(accumulator["missed_mass"]),
        "false_mass": _distribution(accumulator["false_mass"]),
        "total_variation": _distribution(accumulator["total_variation"]),
        "dominant_target_agreement": sum(accumulator["dominant_agrees"]) / len(accumulator["dominant_agrees"]),
        "fanout_distribution": dict(sorted(Counter(accumulator["fanout"]).items())),
        "max_fanout": max(accumulator["fanout"]),
        "max_support_distance": max(accumulator["max_support_distance"]),
        "threshold_residual": _distribution(accumulator["threshold_residual"]),
    }


def validate(
    *,
    exact_per_phase_direction: int = 128,
    diagnostic_count: int = 20_000,
) -> dict[str, object]:
    fixtures = broad_exact_fixtures(exact_per_phase_direction)
    accumulators = {
        kernel: {policy: _new_accumulator() for policy in POLICIES}
        for kernel in ("production", "prototype")
    }
    buckets = {
        kernel: {policy: defaultdict(_new_accumulator) for policy in POLICIES}
        for kernel in ("production", "prototype")
    }
    worst_cases = {kernel: {policy: [] for policy in POLICIES} for kernel in ("production", "prototype")}
    production_elapsed = []
    partition_errors = []
    oracle_elapsed = []
    clear_physical_coverage_cache()

    for fixture in fixtures:
        delta = -1 if fixture.direction == "coverage_up" else 1
        started = perf_counter()
        oracle_members = coverage(fixture.layer, fixture.q, fixture.r, fixture.layer + delta, 4)
        oracle_elapsed.append((perf_counter() - started) * 1000)
        oracle = {(member.q, member.r): float(member.source_share) for member in oracle_members}

        started = perf_counter()
        expansion = expand_physical_coverage(
            GeometryAddress("default_dream_v1", "default", fixture.layer, fixture.q, fixture.r),
            fixture.direction,
        )
        production_elapsed.append((perf_counter() - started) * 1000)
        partition_errors.append(abs(65536 - expansion.q16_sum))
        raw = {
            "production": {(member.target.q, member.target.r): member.hit_count for member in expansion.members},
            "prototype": approximate_hits(fixture.layer, fixture.q, fixture.r, fixture.layer + delta, 4),
        }
        for kernel, hits in raw.items():
            for policy in POLICIES:
                weights, residual = _weights(hits, policy)
                metrics = _metrics(oracle, weights)
                _record(accumulators[kernel][policy], metrics, residual)
                for bucket_name in (
                    f"phase:{fixture.phase}",
                    f"direction:{fixture.direction}",
                    f"coordinate:{fixture.coordinate_bucket}",
                ):
                    _record(buckets[kernel][policy][bucket_name], metrics, residual)
                worst_cases[kernel][policy].append({
                    "score": metrics["total_variation"],
                    "layer": fixture.layer,
                    "q": fixture.q,
                    "r": fixture.r,
                    "direction": fixture.direction,
                    "coordinate_bucket": fixture.coordinate_bucket,
                    "oracle": sorted((q, r, weight) for (q, r), weight in oracle.items()),
                    "approximate": sorted((q, r, weight) for (q, r), weight in weights.items()),
                })

    methods = {}
    for kernel in accumulators:
        methods[kernel] = {}
        for policy in POLICIES:
            summary = _summarize(accumulators[kernel][policy])
            summary["buckets"] = {
                name: _summarize(accumulator)
                for name, accumulator in sorted(buckets[kernel][policy].items())
            }
            summary["worst_cases"] = sorted(
                worst_cases[kernel][policy], key=lambda item: item["score"], reverse=True
            )[:16]
            methods[kernel][f"min_hit_{policy}"] = summary

    diagnostic = _diagnose(diagnostic_count)
    selected = methods["production"]["min_hit_1"]
    checks = {
        "full_exact_fixture_count": len(fixtures) >= 2048,
        "phase_direction_minimum": exact_per_phase_direction >= 128,
        "diagnostic_fixture_count": diagnostic_count >= 20_000,
        "selected_policy_is_production_policy": MIN_HIT_COUNT == 1,
        "missed_mass_p99": selected["missed_mass"]["p99"] <= 0.02,
        "false_mass_p99": selected["false_mass"]["p99"] <= 0.02,
        "total_variation_p95": selected["total_variation"]["p95"] <= 0.05,
        "dominant_target_agreement": selected["dominant_target_agreement"] >= 0.95,
        "max_fanout": selected["max_fanout"] <= 8,
        "no_unsupported_long_range_target": selected["max_support_distance"] == 0,
        "partition_mass_error": max(partition_errors) == 0,
    }
    return {
        "schema_version": "nollm_broad_residue_coverage_calibration_v1",
        "fixture_seed": "0x0ca01d39",
        "diagnostic_seed": "0x0ca01d20",
        "exact_fixture_count": len(fixtures),
        "phase_direction_fixture_count": exact_per_phase_direction,
        "diagnostic_fixture_count": diagnostic_count,
        "sample_count": SAMPLE_COUNT,
        "selected_policy": "min_hit_1",
        "selected_policy_reason": "lower broad missed mass without false mass, fanout, dominant, or runtime regression",
        "methods": methods,
        "diagnostic": diagnostic,
        "timing": {
            "oracle_mean_cell_ms": statistics.fmean(oracle_elapsed),
            "oracle_p95_cell_ms": _percentile(oracle_elapsed, 0.95),
            "production_mean_cell_ms": statistics.fmean(production_elapsed),
            "production_p95_cell_ms": _percentile(production_elapsed, 0.95),
            "production_max_cell_ms": max(production_elapsed),
            "production_max_partition_error_q16": max(partition_errors),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def _diagnose(count: int) -> dict[str, object]:
    valid = unsupported = mismatches = 0
    started = perf_counter()
    clear_physical_coverage_cache()
    for fixture in fast_diagnostic_fixtures(count):
        delta = -1 if fixture.direction == "coverage_up" else 1
        prototype = approximate_hits(fixture.layer, fixture.q, fixture.r, fixture.layer + delta, 4)
        prototype_retained = {target: hits for target, hits in prototype.items() if hits >= MIN_HIT_COUNT}
        try:
            expansion = expand_physical_coverage(
                GeometryAddress("default_dream_v1", "default", fixture.layer, fixture.q, fixture.r),
                fixture.direction,
            )
        except UnsupportedPhysicalCoverage:
            unsupported += 1
            continue
        valid += 1
        production = {(member.target.q, member.target.r): member.hit_count for member in expansion.members}
        mismatches += production != prototype_retained
    return {
        "valid": valid,
        "boundary_unsupported": unsupported,
        "production_prototype_hit_mismatch": mismatches,
        "mismatch_rate_over_valid": mismatches / valid if valid else 0,
        "storage_radius": STORAGE_HEX_RADIUS,
        "elapsed_ms": (perf_counter() - started) * 1000,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exact-per-phase-direction", type=int, default=128)
    parser.add_argument("--diagnostic-count", type=int, default=20_000)
    args = parser.parse_args()
    result = validate(
        exact_per_phase_direction=args.exact_per_phase_direction,
        diagnostic_count=args.diagnostic_count,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
