from nollm_core import CoreRuntime, GeometryAddress, KernelRegistry, MemoryAtom, clear_physical_coverage_cache, expand_physical_coverage


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
            assert all(member.weight_q16 > 0 and member.intersection_area != "0" for member in expansion.members)


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
