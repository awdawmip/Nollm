from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, CoreRecallRequest, RecallBudget

def test_mixed_none_and_string_phase_round_trip_and_recall(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    cells = (GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0), GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0, "p"))
    for i, cell in enumerate(cells): runtime.put(MemoryAtom(str(i), str(i)), cell)
    payload = runtime.state_bytes(); runtime.close()
    runtime = CoreRuntime(tmp_path)
    assert runtime.state_bytes() == payload
    result = runtime.recall(CoreRecallRequest("r", cells, (), RecallBudget(0, 2, 0, 0, 0, 2)))
    assert len(result.items) == 2
