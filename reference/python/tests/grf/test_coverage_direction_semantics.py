from __future__ import annotations

from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP, LAYER_INDEX_DIRECTION, CoverageTemplateCompiler


def test_layer_index_direction_is_finer_with_increasing_index() -> None:
    compiler = CoverageTemplateCompiler()
    up = compiler.compile("eisenstein_exact_v1", COVERAGE_UP)
    down = compiler.compile("eisenstein_exact_v1", COVERAGE_DOWN)
    assert up.compiler["layer_index_direction"] == LAYER_INDEX_DIRECTION
    assert down.compiler["layer_index_direction"] == "finer_with_increasing_index"
    assert {entry.layer_delta for entry in up.entries} == {-1}
    assert {entry.layer_delta for entry in down.entries} == {1}
