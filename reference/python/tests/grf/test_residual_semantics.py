from __future__ import annotations

from nollm.grf.coverage_template import COVERAGE_UP, CoverageTemplateCompiler


def test_normalization_and_approximation_residuals_are_distinct() -> None:
    compiler = CoverageTemplateCompiler()
    exact = compiler.compile("eisenstein_exact_v1", COVERAGE_UP)
    aligned = compiler.compile("aligned_baseline_v1", COVERAGE_UP)
    quasi = compiler.compile("dream_quasi_v1", COVERAGE_UP)
    assert exact.normalization_residual_q16 == 0
    assert aligned.normalization_residual_q16 == 0
    assert exact.approximation_residual_q16 == 0
    assert aligned.approximation_residual_q16 == 0
    assert quasi.normalization_residual_q16 == 0
    assert quasi.approximation_residual_q16 > 0
