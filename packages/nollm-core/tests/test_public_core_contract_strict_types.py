import pytest
from nollm_core import CoreRecallRequest,RecallBudget

def test_recall_contract_types():
    with pytest.raises((TypeError,ValueError)):CoreRecallRequest(1,[],[],RecallBudget(0,1,0,0,0,1))
    with pytest.raises(ValueError):RecallBudget(True,1,0,0,0,1)
