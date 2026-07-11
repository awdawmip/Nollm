from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_snapshot import SnapshotService

def test_mixed_phase_snapshot_identity(tmp_path) -> None:
    runtime=CoreRuntime(tmp_path); service=SnapshotService()
    for i,p in enumerate((None,'p')): runtime.put(MemoryAtom(str(i),str(i)),GeometryAddress('eisenstein_exact_v1','c',0,0,0,p))
    payload=service.create(runtime); service.restore(runtime,payload)
    assert payload==runtime.state_bytes()==runtime.state_path.read_bytes()
