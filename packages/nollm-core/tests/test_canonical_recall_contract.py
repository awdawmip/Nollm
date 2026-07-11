import pytest
from nollm_core import CoreRecallRequest,GeometryAddress,RecallBudget

def test_recall_rejects_noncanonical_tuples():
    a=GeometryAddress('eisenstein_exact_v1','c',0,0,0);b=GeometryAddress('eisenstein_exact_v1','c',0,0,0,'p');budget=RecallBudget(0,1,0,0,0,1)
    with pytest.raises(ValueError,match='canonical'):CoreRecallRequest('r',(b,a),(),budget)
    with pytest.raises(ValueError,match='canonical'):CoreRecallRequest('r',(a,),('lateral','bridge'),budget)
