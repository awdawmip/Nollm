import pytest
from nollm_access import AccessDecision,AccessRecallRequest

def test_public_access_types_rejected():
    with pytest.raises((TypeError,ValueError)):AccessDecision(1,2,'defer',reason_text=3)
    with pytest.raises(TypeError):AccessRecallRequest(1,entry_cells=[])
