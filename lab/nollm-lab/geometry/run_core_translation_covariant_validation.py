from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "reference/python"), str(Path(__file__).resolve().parent)]

from nollm_core import GeometryAddress, clear_physical_coverage_cache, expand_physical_coverage  # noqa: E402
from oracle_decimal import coverage as oracle_b_coverage  # noqa: E402
from run_translation_covariant_coverage_validation import oracle_a  # noqa: E402
from nollm.dream_geometry.geometry.schedules import PARAMETER_MATRIX, ScaleRotationSchedule  # noqa: E402


def _digest(rows: list[object]) -> str:
    payload = json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


def validate() -> dict[str, object]:
    parameter = next(value for value in PARAMETER_MATRIX if value.parameter_id == "B")
    schedule = ScaleRotationSchedule(parameter)
    samples = 0
    support_mismatches = 0
    positive_weight_on_zero_overlap = 0
    max_a_share_error = Decimal(0)
    max_b_share_error = Decimal(0)
    max_q16_error = 0
    max_quantization_residual = 0
    max_partition_residual = Decimal(0)
    max_candidate_residual = Decimal(0)
    rows = []
    for direction, delta, layers in (("coverage_up", -1, range(1, 9)), ("coverage_down", 1, range(0, 8))):
        for source_layer in layers:
            for q in range(-4, 5):
                for r in range(-4, 5):
                    samples += 1
                    source = GeometryAddress("default_dream_v1", "default", source_layer, q, r)
                    runtime = expand_physical_coverage(source, direction)
                    runtime_members = {(member.target.q, member.target.r): member for member in runtime.members}
                    a = oracle_a(schedule, source_layer, q, r, source_layer + delta)
                    b = {(member.q, member.r): member.source_share for member in oracle_b_coverage(source_layer, q, r, source_layer + delta)}
                    support_mismatches += not (set(runtime_members) == set(a) == set(b))
                    positive_weight_on_zero_overlap += len(set(runtime_members) - set(a))
                    for target in set(runtime_members) & set(a) & set(b):
                        share = Decimal(runtime_members[target].source_share)
                        max_a_share_error = max(max_a_share_error, abs(share - Decimal(str(a[target]))))
                        max_b_share_error = max(max_b_share_error, abs(share - b[target]))
                        expected_q16 = int((b[target] * 65536).to_integral_value(rounding=ROUND_HALF_EVEN))
                        max_q16_error = max(max_q16_error, abs(runtime_members[target].weight_q16 - expected_q16))
                    max_quantization_residual = max(max_quantization_residual, runtime.max_quantization_residual_q16)
                    max_partition_residual = max(max_partition_residual, Decimal(runtime.raw_partition_residual))
                    max_candidate_residual = max(max_candidate_residual, Decimal(runtime.candidate_window_residual))
                    rows.append((direction, source_layer, q, r, tuple((member.target.q, member.target.r, member.weight_q16) for member in runtime.members)))
    large_support_mismatches = 0
    large_samples = 0
    for source_layer in range(8):
        for q, r in ((10**14, 0), (-10**14, 0), (10**14, -10**14), (-10**14, 10**14)):
            for direction, delta in (("coverage_up", -1), ("coverage_down", 1)):
                large_samples += 1
                source = GeometryAddress("default_dream_v1", "default", source_layer, q, r)
                runtime = expand_physical_coverage(source, direction)
                oracle = oracle_b_coverage(source_layer, q, r, source_layer + delta)
                large_support_mismatches += {
                    (member.target.q, member.target.r) for member in runtime.members
                } != {(member.q, member.r) for member in oracle}
                max_partition_residual = max(max_partition_residual, Decimal(runtime.raw_partition_residual))
                max_candidate_residual = max(max_candidate_residual, Decimal(runtime.candidate_window_residual))
    before_clear = _digest(rows)
    clear_physical_coverage_cache()
    replay_rows = []
    for direction, delta, layers in (("coverage_up", -1, range(1, 9)), ("coverage_down", 1, range(0, 8))):
        for source_layer in layers:
            for q in range(-4, 5):
                for r in range(-4, 5):
                    source = GeometryAddress("default_dream_v1", "default", source_layer, q, r)
                    runtime = expand_physical_coverage(source, direction)
                    replay_rows.append((direction, source_layer, q, r, tuple((member.target.q, member.target.r, member.weight_q16) for member in runtime.members)))
    after_clear = _digest(replay_rows)
    checks = {
        "all_samples_support_equal": support_mismatches == 0,
        "positive_weight_on_zero_overlap_zero": positive_weight_on_zero_overlap == 0,
        "oracle_a_share_error_bounded": max_a_share_error < Decimal("1e-9"),
        "oracle_b_share_error_bounded": max_b_share_error < Decimal("1e-68"),
        "q16_error_bounded": max_q16_error <= 1,
        "quantization_residual_bounded": max_quantization_residual <= 1,
        "cache_clear_deterministic": before_clear == after_clear,
        "large_coordinate_support_equal_oracle_b": large_support_mismatches == 0,
        "raw_partition_mass_certified": max_partition_residual <= Decimal("1e-72"),
        "candidate_window_complete": max_candidate_residual <= Decimal("1e-72"),
    }
    if not all(checks.values()):
        raise AssertionError({key: value for key, value in checks.items() if not value})
    return {
        "schema_version": "nollm_core_translation_normalized_runtime_validation_v1",
        "status": "pass",
        "checks": checks,
        "samples": samples,
        "large_coordinate_samples": large_samples,
        "large_coordinate_support_mismatch_count": large_support_mismatches,
        "support_mismatch_count": support_mismatches,
        "positive_weight_on_zero_overlap_count": positive_weight_on_zero_overlap,
        "max_oracle_a_source_share_error": format(max_a_share_error, "e"),
        "max_oracle_b_source_share_error": format(max_b_share_error, "e"),
        "max_q16_error": max_q16_error,
        "max_quantization_residual_q16": max_quantization_residual,
        "max_raw_partition_residual": format(max_partition_residual, "e"),
        "max_candidate_window_residual": format(max_candidate_residual, "e"),
        "result_digest_before_cache_clear": before_clear,
        "result_digest_after_cache_clear": after_clear,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
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
