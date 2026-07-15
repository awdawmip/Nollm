from nollm_core import GeometryAddress, KernelRegistry, clear_physical_coverage_cache, expand_physical_coverage, runtime_profile


def test_default_profile_has_mandatory_physical_identity() -> None:
    profile = runtime_profile("default_dream_v1")
    assert profile.geometry_contract_version == "nollm_translation_normalized_physical_coverage_v1"
    assert (profile.theta_step_turn_numerator, profile.theta_step_turn_denominator) == (1, 16)
    assert profile.beta_algebraic == "beta=positive_root(x^4-2)"
    assert profile.orientation == "pointy_top"
    assert profile.increasing_layer_direction == "finer_with_increasing_index"
    assert [profile.orientation_turn(layer) for layer in range(9)] == [
        (0, 48), (3, 48), (6, 48), (1, 48), (4, 48),
        (7, 48), (2, 48), (5, 48), (0, 48),
    ]
    assert profile.runtime_polygon and not profile.runtime_float_allowed
    assert profile.coordinate_model == "integer_axial_with_translation_normalized_decimal_overlap"


def test_rotated_coverage_is_phase_complete_and_physically_described() -> None:
    registry = KernelRegistry()
    templates = tuple(template for template in registry.templates() if template.profile_id == "default_dream_v1")
    assert len(templates) == 8
    assert {(template.direction, template.from_layer_mod) for template in templates} == {
        (direction, phase)
        for direction in ("lateral",)
        for phase in range(8)
    }
    for template in templates:
        assert template.compiler.method == "decimal_interval_rotated_hex_envelope_v1"
        assert template.compiler.geometry_contract_version == "nollm_rotated_physical_field_v1"
        assert template.certification == "decimal72_canonical_overlap_plus_conservative_nearest_cell_envelope"
        assert len(template.transform_q32) == 4
        assert all(entry.intersection_area_lower and entry.intersection_area_upper for entry in template.entries)
        assert all(0 <= entry.certification_residual_q16 <= 65536 for entry in template.entries)


def test_runtime_uses_full_address_and_is_cache_independent() -> None:
    registry = KernelRegistry()
    cell = GeometryAddress("default_dream_v1", "default", 5, 3, -2)
    targets = registry.expand_coverage(cell, "coverage_up")
    translated = registry.expand_coverage(GeometryAddress("default_dream_v1", "default", 5, 4, -2), "coverage_up")
    before = expand_physical_coverage(cell, "coverage_up")
    clear_physical_coverage_cache()
    assert expand_physical_coverage(cell, "coverage_up") == before
    assert targets != translated
    assert 1 <= len(targets) <= 7
    assert all(target.layer == 4 for target, _weight in targets)
    assert sum(weight for _target, weight in targets) == 65536
    assert before.normalization_residual_q16 == 0
    assert before.max_quantization_residual_q16 <= 1
