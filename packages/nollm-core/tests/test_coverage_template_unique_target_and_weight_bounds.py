import pytest
from dataclasses import replace
from nollm_core import CoverageTemplateCompiler,KernelEntry

def test_duplicate_target_and_overweight_rejected():
    t=CoverageTemplateCompiler().compile('eisenstein_exact_v1','coverage_up')
    duplicate=(KernelEntry(-1,0,0,30000,flags=('eisenstein_exact',)),KernelEntry(-1,0,0,35536,flags=('eisenstein_exact',)))
    with pytest.raises(ValueError):replace(t,entries=duplicate,sum_weight_q16=65536)
    with pytest.raises(ValueError):replace(t,normalization_residual_q16=-1,sum_weight_q16=65537)
