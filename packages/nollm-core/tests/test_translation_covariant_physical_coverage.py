from pathlib import Path

import pytest

from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY,
    CoreRuntime,
    GeometryAddress,
    KernelRegistry,
    MemoryAtom,
    clear_physical_coverage_cache,
    expand_physical_coverage,
)
from nollm_core.physical_coverage import UnsupportedPhysicalCoverage


def address(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def test_all_phases_and_directions_use_bounded_quadrature_contract() -> None:
    assert ACTIVE_APPROXIMATION_POLICY.policy_id == "nollm_broad_residue_min_hit_1_v1"
    assert ACTIVE_APPROXIMATION_POLICY.sample_count == 96
    assert ACTIVE_APPROXIMATION_POLICY.storage_hex_radius == (1 << 31) - 1
    registry = KernelRegistry()
    for layer in range(8):
        for direction in ("coverage_up", "coverage_down"):
            source = address(layer, -7 + layer, 5 - layer)
            expansion = expand_physical_coverage(source, direction)
            assert registry.expand_coverage(source, direction) == expansion.targets()
            assert expansion.method_id == "equal_area_hex_microtriangle_q40_m4_v1"
            assert expansion.approximation_contract_id == "nollm_bounded_approximate_hex_coverage_v1"
            assert expansion.coordinate_contract_id == "nollm_hex_radius_2p31_default_chart_null_phase_v1"
            assert expansion.sample_count == 96
            assert expansion.relation_threshold_q16 == 683
            assert expansion.min_hit_count == 1
            assert expansion.approximation_policy_id == "nollm_broad_residue_min_hit_1_v1"
            assert 1 <= expansion.fanout == len(expansion.members) <= 8
            assert expansion.sum_weight_q16 == 65536
            assert expansion.normalization_residual_q16 == 0
            assert expansion.max_quantization_residual_q16 <= 1
            assert 0 <= expansion.threshold_residual_q16 <= 65536
            assert not expansion.ambiguous
            assert all(member.weight_q16 > 0 and member.hit_count >= 1 for member in expansion.members)
            assert all(member.classification == "bounded_equal_area_quadrature" for member in expansion.members)


def test_active_coordinate_boundary_is_deterministic_across_all_phases() -> None:
    coordinates = ((10**9, 0), (-10**9, 0), (10**9, -10**9), (-10**9, 10**9))
    for layer in range(8):
        for q, r in coordinates:
            for direction in ("coverage_up", "coverage_down"):
                expansion = expand_physical_coverage(address(layer, q, r), direction)
                assert expansion.q16_sum == 65536
                assert 1 <= len(expansion.members) <= 8
                assert expansion == expand_physical_coverage(address(layer, q, r), direction)


@pytest.mark.parametrize(
    "values",
    (
        ("default_dream_v1", "other", 0, 0, 0, None),
        ("default_dream_v1", "default", 0, 0, 0, "phase"),
        ("default_dream_v1", "default", 65, 0, 0, None),
        ("default_dream_v1", "default", 0, 1 << 31, 0, None),
        ("default_dream_v1", "default", 0, (1 << 31) - 1, 1, None),
    ),
)
def test_active_address_domain_is_rejected_during_construction(values) -> None:
    with pytest.raises(ValueError):
        GeometryAddress(*values)


def test_invalid_direction_is_rejected_before_quadrature() -> None:
    with pytest.raises(UnsupportedPhysicalCoverage):
        expand_physical_coverage(address(0, 0, 0), "lateral")


def test_production_coverage_has_no_exact_measurement_dependency() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "nollm_core"
    source = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("approximate_coverage.py", "coverage_contract.py", "physical_coverage.py")
    )
    for forbidden in ("decimal", "polygon", "intersection_area", "sin(", "cos(", "oracle_decimal"):
        assert forbidden not in source.lower()


def test_static_default_cross_layer_templates_are_not_active() -> None:
    registry = KernelRegistry()
    for direction in ("coverage_up", "coverage_down"):
        with pytest.raises(ValueError, match="unknown coverage template"):
            registry.coverage_template("default_dream_v1", direction, 3)


def test_cache_and_reopen_do_not_change_runtime_or_canonical_state(tmp_path) -> None:
    source = address(3, -11, 9)
    before = expand_physical_coverage(source, "coverage_down")
    clear_physical_coverage_cache()
    assert expand_physical_coverage(source, "coverage_down") == before
    with CoreRuntime(tmp_path) as runtime:
        runtime.put(MemoryAtom("source", "payload"), source)
        state_bytes = runtime.export_state_bytes()
        first = runtime.kernel_registry.expand_coverage(source, "coverage_down")
    assert b"hit_count" not in state_bytes and b"method_id" not in state_bytes
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.export_state_bytes() == state_bytes
        assert reopened.kernel_registry.expand_coverage(source, "coverage_down") == first
