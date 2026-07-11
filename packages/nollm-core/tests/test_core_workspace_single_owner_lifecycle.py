import pytest
from nollm_core import CoreRuntime,GeometryAddress,MemoryAtom

def test_owner_close_reopen_and_closed_rejection(tmp_path):
    core=CoreRuntime(tmp_path)
    with pytest.raises(RuntimeError,match='live mutable owner'):CoreRuntime(tmp_path)
    core.close()
    with pytest.raises(RuntimeError,match='closed'):core.export_state_bytes()
    reopened=CoreRuntime(tmp_path);reopened.put(MemoryAtom('a','a'),GeometryAddress('eisenstein_exact_v1','c',0,0,0));reopened.close()
