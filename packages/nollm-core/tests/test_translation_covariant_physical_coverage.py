from decimal import Decimal

import pytest

from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    KernelRegistry,
    MemoryAtom,
    clear_physical_coverage_cache,
    expand_physical_coverage,
)
import nollm_core.physical_coverage as physical_coverage
from nollm_core.physical_coverage import AmbiguousPhysicalCoverage, UnsupportedPhysicalCoverage


def address(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def test_all_phases_and_directions_use_bounded_positive_physical_support() -> None:
    registry = KernelRegistry()
    for layer in range(8):
        for direction in ("coverage_up", "coverage_down"):
            source = address(layer, -7 + layer, 5 - layer)
            expansion = expand_physical_coverage(source, direction)
            assert registry.expand_coverage(source, direction) == expansion.targets()
            assert 1 <= len(expansion.members) <= registry.fanout_limit
            assert expansion.sum_weight_q16 == 65536
            assert expansion.normalization_residual_q16 == 0
            assert expansion.max_quantization_residual_q16 <= 1
            assert Decimal(expansion.raw_partition_residual) <= Decimal(expansion.numeric_error_bound)
            assert Decimal(expansion.candidate_window_residual) <= Decimal(expansion.numeric_error_bound)
            assert expansion.candidate_strategy == "nearest_axial_radius4_validated_by_radius6"
            assert expansion.coordinate_contract_id == "nollm_translation_normalized_physical_coverage_v1"
            assert expansion.oracle_contract_id == "nollm_translation_normalized_independent_oracles_v1"
            assert not expansion.ambiguous
            assert all(member.weight_q16 > 0 and member.intersection_area != "0" for member in expansion.members)
            assert all(not member.ambiguous and member.classification == "core" for member in expansion.members)


def test_large_signed_coordinates_are_translation_normalized_across_all_phases() -> None:
    coordinates = ((10**14, 0), (-10**14, 0), (10**14, -10**14), (-10**14, 10**14))
    for layer in range(8):
        for q, r in coordinates:
            for direction in ("coverage_up", "coverage_down"):
                expansion = expand_physical_coverage(address(layer, q, r), direction)
                assert Decimal(expansion.raw_partition_residual) <= Decimal(expansion.numeric_error_bound)
                assert Decimal(expansion.candidate_window_residual) <= Decimal(expansion.numeric_error_bound)
                assert expansion.q16_sum == 65536
                assert 1 <= len(expansion.members) <= 7


def test_unsupported_address_components_are_rejected_before_coverage() -> None:
    invalid = (
        GeometryAddress("default_dream_v1", "other", 0, 0, 0),
        GeometryAddress("default_dream_v1", "default", 0, 0, 0, "phase"),
        GeometryAddress("default_dream_v1", "default", 65, 0, 0),
        GeometryAddress("default_dream_v1", "default", 0, 1 << 63, 0),
    )
    for source in invalid:
        with pytest.raises(UnsupportedPhysicalCoverage):
            expand_physical_coverage(source, "coverage_down")


def test_invalid_raw_partition_never_reaches_q16(monkeypatch) -> None:
    clear_physical_coverage_cache()
    quantize_called = False

    def fail_quantize(_shares):
        nonlocal quantize_called
        quantize_called = True
        raise AssertionError("Q16 was called before physical mass passed")

    monkeypatch.setattr(physical_coverage, "_intersection_area", lambda *_args: Decimal(0))
    monkeypatch.setattr(physical_coverage, "_quantize", fail_quantize)
    with pytest.raises(AmbiguousPhysicalCoverage, match="failed before Q16"):
        expand_physical_coverage(address(0, 0, 0), "coverage_down")
    assert not quantize_called
    clear_physical_coverage_cache()


def test_static_default_cross_layer_templates_are_not_active() -> None:
    registry = KernelRegistry()
    for direction in ("coverage_up", "coverage_down"):
        try:
            registry.coverage_template("default_dream_v1", direction, 3)
        except ValueError as error:
            assert "unknown coverage template" in str(error)
        else:
            raise AssertionError("default cross-layer static template remained active")


def test_cache_and_reopen_do_not_change_runtime_or_canonical_state(tmp_path) -> None:
    source = address(3, -11, 9)
    before = expand_physical_coverage(source, "coverage_down")
    clear_physical_coverage_cache()
    assert expand_physical_coverage(source, "coverage_down") == before
    with CoreRuntime(tmp_path) as runtime:
        runtime.put(MemoryAtom("source", "payload"), source)
        state_bytes = runtime.export_state_bytes()
        first = runtime.kernel_registry.expand_coverage(source, "coverage_down")
    assert b"intersection_area" not in state_bytes
    assert b"source_share" not in state_bytes
    with CoreRuntime(tmp_path) as reopened:
        assert reopened.export_state_bytes() == state_bytes
        assert reopened.kernel_registry.expand_coverage(source, "coverage_down") == first
