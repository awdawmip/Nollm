from nollm_access import AccessDecision, AccessRecallRequest, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget

def test_mixed_phase_access_entry_order(tmp_path) -> None:
    core=CoreRuntime(tmp_path/'core'); access=AccessRuntime(core,FileEvidenceStore(tmp_path),FileHandleStore(tmp_path))
    cells=(GeometryAddress('eisenstein_exact_v1','c',0,0,0),GeometryAddress('eisenstein_exact_v1','c',0,0,0,'p'))
    for i,cell in enumerate(cells):
        access.capture(MemoryStatement(str(i),str(i)))
        handle=core.put(MemoryAtom(str(i),str(i)),cell)
        access.handle_store.put(str(i),handle)
    assert len(access.recall(AccessRecallRequest('r',entry_cells=cells,budget=RecallBudget(0,2,0,0,0,2))).items)==2
