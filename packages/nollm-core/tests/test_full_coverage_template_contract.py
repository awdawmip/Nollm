from nollm_core import CoverageTemplateCompiler


def test_nine_full_templates_and_quasi_metadata() -> None:
    compiler = CoverageTemplateCompiler()
    templates = [compiler.compile(profile, direction) for profile in ("eisenstein_exact_v1", "aligned_baseline_v1", "dream_quasi_v1") for direction in ("coverage_up", "coverage_down", "lateral")]
    assert len(templates) == 9
    quasi = compiler.compile("dream_quasi_v1", "coverage_up")
    assert quasi.normalization_residual_q16 == 0
    assert quasi.approximation_residual_q16 > 0
    assert quasi.compiler["method"] == "symbolic_research_template_with_residual"
    assert "boundary_ambiguous" in quasi.compiler["flags"]
