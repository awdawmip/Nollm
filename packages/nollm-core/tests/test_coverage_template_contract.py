from nollm_core import CoverageTemplateCompiler, GeometryAddress, expand_template


def test_exact_audit_example_and_layer_direction() -> None:
    cell = GeometryAddress("eisenstein_exact_v1", "chart", 3, 4, -2)
    compiler = CoverageTemplateCompiler()
    up = expand_template(cell, compiler.compile(cell.profile_id, "coverage_up"))
    down = expand_template(cell, compiler.compile(cell.profile_id, "coverage_down"))
    assert [(target.layer, target.q, target.r, weight) for target, weight in up] == [(2, 4, -2, 21846), (2, 4, -1, 21845), (2, 5, -2, 21845)]
    assert {(target.layer, target.q, target.r) for target, _ in down} == {(4, 4, -2), (4, 3, -2), (4, 4, -3)}
