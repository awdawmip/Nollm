from nollm_core import CoreRecallRequest, CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget


def test_recall_uses_registered_exact_coverage(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = GeometryAddress("eisenstein_exact_v1", "c", 3, 4, -2)
    target = GeometryAddress("eisenstein_exact_v1", "c", 2, 4, -2)
    runtime.put(MemoryAtom("a", "payload"), target)
    result = runtime.recall(CoreRecallRequest("r", (entry,), ("coverage_up",), RecallBudget(1, 8, 1, 0, 0, 4)))
    assert [(item.atom.atom_id, item.score_q16) for item in result.items] == [("a", 21846)]
