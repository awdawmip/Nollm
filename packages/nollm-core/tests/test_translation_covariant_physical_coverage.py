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


# This independent integer oracle freezes the admitted Q40 sampling contract.
# It deliberately does not call production rounding, centroid, or stencil code.
# Agreement certifies the factorization, not exact real-area geometry.
def _reference_hits(q: int, r: int, direction: str, matrix=None):
    scale = 1 << 40
    matrices = {
        "coverage_up": (
            649918386859, -408555777664, 408555777664, 1058474164523,
            375230555604, -489009980729, 235879788213, 569464183794,
        ),
        "coverage_down": (
            1496908518890, 577785121758, -577785121758, 919123397132,
            864240536333, -113779425125, -333584395581, 805343972007,
        ),
    }
    matrix = matrices[direction] if matrix is None else matrix
    vertices = (
        (952205001410, scale // 2), (0, scale),
        (-952205001410, scale // 2), (-952205001410, -scale // 2),
        (0, -scale), (952205001410, -scale // 2),
    )

    def nearest_ratio(n, d):
        whole, residual = divmod(n, d)
        return whole + int(2 * residual > d or (2 * residual == d and whole % 2 != 0))

    counts = {}
    for index, first in enumerate(vertices):
        second = vertices[(index + 1) % 6]
        for a in range(4):
            for b in range(4 - a):
                for shift in ((1, 2) if a + b < 3 else (1,)):
                    x, y = tuple(nearest_ratio(
                        (3 * a + shift) * first[axis] + (3 * b + shift) * second[axis], 12,
                    ) for axis in range(2))
                    qf = matrix[0] * q + matrix[1] * r + nearest_ratio(matrix[4] * x + matrix[5] * y, scale)
                    rf = matrix[2] * q + matrix[3] * r + nearest_ratio(matrix[6] * x + matrix[7] * y, scale)
                    cube = (qf, rf, -qf - rf)
                    rounded = [nearest_ratio(value, scale) for value in cube]
                    errors = tuple(abs(rounded[axis] * scale - cube[axis]) for axis in range(3))
                    repair = errors.index(max(errors))
                    rounded[repair] = -sum(rounded[axis] for axis in range(3) if axis != repair)
                    key = (rounded[0], rounded[1])
                    counts[key] = counts.get(key, 0) + 1
    assert sum(counts.values()) == 96
    return tuple(sorted(counts.items()))


def _assert_reference_expansion(layer, q, r, direction):
    expected = _reference_hits(q, r, direction)
    outside = max(max(abs(a), abs(b), abs(a + b)) for (a, b), _ in expected) > (1 << 31) - 1
    source = address(layer, q, r)
    if outside:
        with pytest.raises(UnsupportedPhysicalCoverage, match="target is outside storage radius"):
            expand_physical_coverage(source, direction)
        return
    result = expand_physical_coverage(source, direction)
    actual = tuple(((member.target.q, member.target.r), member.hit_count) for member in result.members)
    assert actual == expected
    weights = [count * 65536 // 96 for _, count in expected]
    order = sorted(range(len(weights)), key=lambda i: (-(expected[i][1] * 65536 % 96), i))
    for i in order[:65536 - sum(weights)]:
        weights[i] += 1
    assert tuple(member.weight_q16 for member in result.members) == tuple(weights)
    assert result.threshold_residual_q16 == 0
    assert result.q16_sum == 65536
    assert all(member.target.layer == layer + (-1 if direction == "coverage_up" else 1) for member in result.members)


def test_phase_kernel_independent_reference_all_layers_and_large_coordinates():
    clear_physical_coverage_cache()
    for layer in range(-64, 65):
        for direction in ("coverage_up", "coverage_down"):
            if (layer, direction) in ((-64, "coverage_up"), (64, "coverage_down")):
                with pytest.raises(UnsupportedPhysicalCoverage, match="layer"):
                    expand_physical_coverage(address(layer, 0, 0), direction)
                continue
            q = ((layer * 7919) % 2000000001) - 1000000000
            r = -q // 2
            _assert_reference_expansion(layer, q, r, direction)
    for q, r in ((0, 0), (1, -1), (-1, 1), (2147483647, 0), (-2147483647, 0),
                 (2147483647, -2147483647), (-2147483647, 2147483647)):
        for direction in ("coverage_up", "coverage_down"):
            _assert_reference_expansion(0, q, r, direction)


def test_phase_kernel_independent_reference_frozen_random_population():
    # Explicitly deterministic input generation; no runtime time/seed dependency.
    state = 20260910
    for index in range(1024):
        state = (1664525 * state + 1013904223) % (1 << 32)
        q = state % 2000000001 - 1000000000
        state = (1664525 * state + 1013904223) % (1 << 32)
        r = state % 2000000001 - 1000000000
        for direction in ("coverage_up", "coverage_down"):
            _assert_reference_expansion(index % 16 - 8, q, r, direction)


def test_phase_kernel_half_even_ties_preserve_odd_translation_information(monkeypatch):
    # Zero local offsets isolate cube ties without changing the production table.
    # A one-cell quotient would wrongly equate (0.5,0.5) and (1.5,1.5).
    scale = 1 << 40
    synthetic = (scale // 2, 0, scale // 2, 0, 0, 0, 0, 0)
    namespace = expand_physical_coverage.__globals__
    try:
        with monkeypatch.context() as patch:
            patch.setitem(namespace["_TRANSFORMS"], "coverage_down", synthetic)
            clear_physical_coverage_cache()
            for q in range(-17, 18):
                result = expand_physical_coverage(address(0, q, 0), "coverage_down")
                assert tuple(((m.target.q, m.target.r), m.hit_count) for m in result.members) == _reference_hits(q, 0, "coverage_down", synthetic)
            first = expand_physical_coverage(address(0, 1, 0), "coverage_down").members[0].target
            second = expand_physical_coverage(address(0, 3, 0), "coverage_down").members[0].target
            assert (first.q, first.r) == (1, 0)
            assert (second.q, second.r) == (1, 2)
    finally:
        clear_physical_coverage_cache()


def test_phase_kernel_cache_is_shared_across_layers_and_fully_disposable():
    namespace = expand_physical_coverage.__globals__
    clear_physical_coverage_cache()
    before = []
    for layer in range(8):
        before.append(expand_physical_coverage(address(layer, -7, 5), "coverage_down"))
    info = namespace["_phase_footprint"].cache_info()
    assert info.misses == 1 and info.hits == 7
    assert info.maxsize == 8192
    assert namespace["_compiled_sample_offsets_q40"].cache_info().maxsize == 2
    clear_physical_coverage_cache()
    for name in ("_expand_cached", "_phase_footprint", "_compiled_sample_offsets_q40", "_sample_offsets_q40"):
        assert namespace[name].cache_info().currsize == 0
    after = [expand_physical_coverage(address(layer, -7, 5), "coverage_down") for layer in range(8)]
    assert before == after
    with pytest.raises(UnsupportedPhysicalCoverage, match="layer"):
        expand_physical_coverage(address(64, -7, 5), "coverage_down")


def test_phase_kernel_integer_reconstruction_and_even_shift_equivariance():
    namespace = expand_physical_coverage.__globals__
    nearest = namespace["_nearest_axial_q40"]
    scale = 1 << 40
    values = (-scale - 1, -scale, -scale // 2, -1, 0, 1, scale // 2, scale, scale + 1)
    for q in values:
        for r in values:
            base_q, base_r = nearest(q, r)
            for a, b in ((-8, 2), (0, 0), (2, -4), (10, 12)):
                assert nearest(q + a * scale, r + b * scale) == (base_q + a, base_r + b)
            aq, pq = divmod(q, 2 * scale)
            ar, pr = divmod(r, 2 * scale)
            local_q, local_r = nearest(pq, pr)
            assert (base_q, base_r) == (local_q + 2 * aq, local_r + 2 * ar)
