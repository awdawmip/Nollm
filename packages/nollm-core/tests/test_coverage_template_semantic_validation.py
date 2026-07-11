import pytest
from dataclasses import replace
from nollm_core import CoverageTemplateCompiler

def test_direct_template_rejects_semantic_contradictions() -> None:
    template = CoverageTemplateCompiler().compile("eisenstein_exact_v1", "coverage_up")
    with pytest.raises(ValueError, match="layer"): replace(template, to_layer_mod=99)
    with pytest.raises(ValueError, match="residual"): replace(template, approximation_residual_q16=1)
