import inspect

from nollm_core import GeometryAddress, KernelRegistry, expand_template, runtime_profile


def test_default_profile_has_mandatory_physical_identity() -> None:
    profile = runtime_profile("default_dream_v1")
    assert profile.geometry_contract_version == "nollm_rotated_physical_field_v1"
    assert (profile.theta_step_turn_numerator, profile.theta_step_turn_denominator) == (1, 16)
    assert profile.beta_algebraic == "beta=positive_root(x^4-2)"
    assert profile.orientation == "pointy_top"
    assert profile.increasing_layer_direction == "finer_with_increasing_index"
    assert [profile.orientation_turn(layer) for layer in range(9)] == [
        (0, 48), (3, 48), (6, 48), (1, 48), (4, 48),
        (7, 48), (2, 48), (5, 48), (0, 48),
    ]
    assert not profile.runtime_polygon and not profile.runtime_float_allowed


def test_rotated_coverage_is_phase_complete_and_physically_described() -> None:
    registry = KernelRegistry()
    templates = tuple(template for template in registry.templates() if template.profile_id == "default_dream_v1")
    assert len(templates) == 24
    assert {(template.direction, template.from_layer_mod) for template in templates} == {
        (direction, phase)
        for direction in ("coverage_up", "coverage_down", "lateral")
        for phase in range(8)
    }
    for template in templates:
        assert template.compiler.method == "decimal_interval_rotated_hex_envelope_v1"
        assert template.compiler.geometry_contract_version == "nollm_rotated_physical_field_v1"
        assert template.certification == "decimal72_canonical_overlap_plus_conservative_nearest_cell_envelope"
        assert len(template.transform_q32) == 4
        assert all(entry.intersection_area_lower and entry.intersection_area_upper for entry in template.entries)
        assert all(0 <= entry.certification_residual_q16 <= 65536 for entry in template.entries)


def test_runtime_selects_layer_phase_without_float_or_polygon() -> None:
    registry = KernelRegistry()
    cell = GeometryAddress("default_dream_v1", "default", 5, 3, -2)
    template = registry.coverage_template(cell.profile_id, "coverage_up", cell.layer)
    targets = expand_template(cell, template)
    assert template.from_layer_mod == 5
    assert len(targets) == 7
    assert all(target.layer == 4 for target, _weight in targets)
    runtime_source = inspect.getsource(__import__("nollm_core.coverage_template", fromlist=["expand_template"]))
    assert "sin(" not in runtime_source and "cos(" not in runtime_source and "polygon" not in runtime_source
