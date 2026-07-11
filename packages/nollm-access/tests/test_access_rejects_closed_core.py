import pytest
from nollm_access import AccessRuntime,FileEvidenceStore,FileHandleStore
from nollm_core import CoreRuntime

def test_closed_core_rejected(tmp_path):
    core=CoreRuntime(tmp_path/'core');core.close()
    with pytest.raises(RuntimeError,match='OPEN'):AccessRuntime(core,FileEvidenceStore(tmp_path),FileHandleStore(tmp_path))
