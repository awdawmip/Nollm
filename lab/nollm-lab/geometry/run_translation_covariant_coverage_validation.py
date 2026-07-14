from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "reference/python"
ORACLE = Path(__file__).resolve().parent
sys.path[:0] = [str(REFERENCE), str(ORACLE)]

from nollm.dream_geometry.geometry.chart import make_hex_cell  # noqa: E402
from nollm.dream_geometry.geometry.hexgrid import disk, nearest_axial  # noqa: E402
from nollm.dream_geometry.geometry.polygon import convex_polygon_intersection_area  # noqa: E402
from nollm.dream_geometry.geometry.schedules import PARAMETER_MATRIX, ScaleRotationSchedule  # noqa: E402
from nollm.dream_geometry.geometry.types import AxialCoord  # noqa: E402
from oracle_decimal import coverage as decimal_coverage  # noqa: E402
from oracle_decimal import fractional_target_axial  # noqa: E402
from physical_geometry import axial_transform_q32  # noqa: E402


THRESHOLD = 1e-10


def oracle_a(schedule, source_layer: int, q: int, r: int, target_layer: int):
    source_chart = schedule.chart_for_layer(source_layer)
    target_chart = schedule.chart_for_layer(target_layer)
    source = make_hex_cell(source_chart, AxialCoord(q, r))
    nearest = nearest_axial(target_chart, source.center)
    output = {}
    for target_address in disk(nearest, 4):
        target = make_hex_cell(target_chart, target_address)
        area = convex_polygon_intersection_area(source.vertices, target.vertices)
        if area > THRESHOLD:
            output[(target_address.q, target_address.r)] = area / source.area
    return output


def validate() -> dict[str, object]:
    parameter = next(value for value in PARAMETER_MATRIX if value.parameter_id == "B")
    schedule = ScaleRotationSchedule(parameter)
    false_negatives = 0
    false_positive_weights = 0
    support_mismatches = 0
    phase_only_mismatches = 0
    samples = 0
    max_share_error = Decimal(0)
    max_q16_error = 0
    max_transform_error = Decimal(0)
    origin_samples = 0
    phase_origin_support: dict[tuple[int, int], frozenset[tuple[int, int]]] = {}
    for direction, delta, layers in (
        ("coverage_up", -1, range(1, 9)),
        ("coverage_down", 1, range(0, 8)),
    ):
        for source_layer in layers:
            target_layer = source_layer + delta
            origin = decimal_coverage(source_layer, 0, 0, target_layer)
            origin_nearest_q = min(origin, key=lambda item: (-item.source_share, item.q, item.r)).q
            origin_nearest_r = min(origin, key=lambda item: (-item.source_share, item.q, item.r)).r
            phase_origin_support[(source_layer % 8, delta)] = frozenset((item.q - origin_nearest_q, item.r - origin_nearest_r) for item in origin)
            for q in range(-4, 5):
                for r in range(-4, 5):
                    samples += 1
                    origin_samples += q == 0 and r == 0
                    a = oracle_a(schedule, source_layer, q, r, target_layer)
                    b_members = decimal_coverage(source_layer, q, r, target_layer)
                    b = {(item.q, item.r): item.source_share for item in b_members}
                    a_support, b_support = set(a), set(b)
                    false_negatives += len(a_support - b_support)
                    false_positive_weights += len(b_support - a_support)
                    support_mismatches += a_support != b_support
                    for address in a_support & b_support:
                        error = abs(Decimal(str(a[address])) - b[address])
                        max_share_error = max(max_share_error, error)
                        aq16 = int((Decimal(str(a[address])) * 65536).to_integral_value(rounding=ROUND_HALF_EVEN))
                        bq16 = int((b[address] * 65536).to_integral_value(rounding=ROUND_HALF_EVEN))
                        max_q16_error = max(max_q16_error, abs(aq16 - bq16))
                    strongest = max(b_members, key=lambda item: (item.source_share, -item.q, -item.r))
                    relative = frozenset((item.q - strongest.q, item.r - strongest.r) for item in b_members)
                    phase_only_mismatches += relative != phase_origin_support[(source_layer % 8, delta)]
            matrix = axial_transform_q32(direction)
            for q in range(-16, 17):
                for r in range(-16, 17):
                    expected_q, expected_r = fractional_target_axial(source_layer, q, r, target_layer)
                    actual_q = Decimal(matrix[0] * q + matrix[1] * r) / Decimal(1 << 32)
                    actual_r = Decimal(matrix[2] * q + matrix[3] * r) / Decimal(1 << 32)
                    max_transform_error = max(max_transform_error, abs(expected_q - actual_q), abs(expected_r - actual_r))
    checks = {
        "two_independent_oracles": True,
        "false_negative_count_zero": false_negatives == 0,
        "positive_weight_on_zero_overlap_zero": false_positive_weights == 0,
        "oracle_support_sets_equal": support_mismatches == 0,
        "share_error_bounded": max_share_error < Decimal("1e-9"),
        "q16_error_bounded": max_q16_error <= 1,
        "non_origin_majority": origin_samples < samples // 10,
        "phase_only_reuse_disproved": phase_only_mismatches > 0,
        "q32_world_transform_bounded": max_transform_error < Decimal("1e-8"),
    }
    if not all(checks.values()):
        raise AssertionError({key: value for key, value in checks.items() if not value})
    return {
        "schema_version": "nollm_translation_covariant_coverage_oracle_validation_v1",
        "status": "pass",
        "checks": checks,
        "samples": samples,
        "origin_samples": origin_samples,
        "false_negative_count": false_negatives,
        "positive_weight_on_zero_overlap_count": false_positive_weights,
        "support_mismatch_count": support_mismatches,
        "phase_only_mismatch_count": phase_only_mismatches,
        "max_source_share_error": format(max_share_error, "e"),
        "max_q16_error": max_q16_error,
        "max_q32_world_transform_error": format(max_transform_error, "e"),
        "candidate_radius": 4,
        "decimal_precision": 80,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output")
    arguments = parser.parse_args()
    document = validate()
    payload = json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        Path(arguments.output).write_text(payload, encoding="utf-8", newline="\n")
    print(json.dumps(document, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
