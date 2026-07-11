import pytest
from nollm_core import KernelEntry

@pytest.mark.parametrize('kwargs',[{'kernel_type':'graph_edge'},{'flags':('z','a')},{'flags':('a','a')},{'weight_q16':0},{'weight_q16':65537}])
def test_bad_kernel_entry_rejected(kwargs):
    values=dict(layer_delta=-1,dq=0,dr=0,weight_q16=1,kernel_type='coverage_template',flags=('a',));values.update(kwargs)
    with pytest.raises((ValueError,TypeError)):KernelEntry(**values)
