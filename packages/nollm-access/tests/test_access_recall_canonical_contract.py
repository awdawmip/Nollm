import pytest
from nollm_access import AccessRecallRequest
from nollm_core import GeometryAddress,RecallBudget

def test_access_recall_rejects_duplicate_unknown_and_order():
    a=GeometryAddress('eisenstein_exact_v1','c',0,0,0);budget=RecallBudget(0,1,0,0,0,1)
    with pytest.raises(ValueError):AccessRecallRequest('r',entry_cells=(a,a),budget=budget)
    with pytest.raises(ValueError):AccessRecallRequest('r',entry_cells=(a,),allowed_kernels=('unknown',),budget=budget)
    with pytest.raises(ValueError):AccessRecallRequest('r',entry_cells=(a,),allowed_kernels=('lateral','bridge'),budget=budget)


def test_active_default_profile_requires_exactly_one_entry():
    budget=RecallBudget(0,2,0,0,0,2)
    first=GeometryAddress('default_dream_v1','default',0,0,0)
    second=GeometryAddress('default_dream_v1','default',0,1,0)
    with pytest.raises(ValueError,match='exactly one physical entry'):
        AccessRecallRequest('active-multi',entry_cells=(first,second),budget=budget)
