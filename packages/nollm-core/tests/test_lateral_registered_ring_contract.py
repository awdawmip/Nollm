import pytest
from nollm_core import CoreRecallRequest, CoreRuntime, GeometryAddress, KernelRegistry, RecallBudget

def test_ring_two_rejected_even_with_custom_fanout(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    request = CoreRecallRequest("r", (GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0),), ("lateral",), RecallBudget(2, 12, 0, 2, 0, 2))
    with pytest.raises(ValueError, match="registered lateral ring 1"): runtime.recall(request)
