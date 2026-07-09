from __future__ import annotations

from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP, LATERAL, CoverageTemplateCompiler
from nollm.grf.fixed_point import Q16_ONE


def test_templates_report_sum_and_residual() -> None:
    compiler = CoverageTemplateCompiler()
    for profile_id in ("aligned_baseline_v1", "eisenstein_exact_v1", "dream_quasi_v1"):
        template = compiler.compile(profile_id, COVERAGE_UP)
        assert template.sum_weight_q16 == Q16_ONE
        assert template.normalization_residual_q16 == 0
        assert template.compiler["weight_format"] == "q16_65536"


def test_up_and_down_are_distinct_directional_templates() -> None:
    compiler = CoverageTemplateCompiler()
    up = compiler.compile("eisenstein_exact_v1", COVERAGE_UP)
    down = compiler.compile("eisenstein_exact_v1", COVERAGE_DOWN)
    assert up is not down
    assert up.direction == COVERAGE_UP
    assert down.direction == COVERAGE_DOWN
    assert up.entries != down.entries


def test_lateral_template_is_bounded() -> None:
    template = CoverageTemplateCompiler().compile("aligned_baseline_v1", LATERAL)
    assert len(template.entries) == 6
    assert template.sum_weight_q16 == Q16_ONE


def test_dream_quasi_is_marked_research_ambiguous() -> None:
    template = CoverageTemplateCompiler().compile("dream_quasi_v1", COVERAGE_UP)
    assert "boundary_ambiguous" in template.compiler["flags"]
    assert template.compiler["method"] == "symbolic_research_template_with_residual"
    assert template.approximation_residual_q16 > 0
