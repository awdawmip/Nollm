import pytest
from nollm_access import AccessRuntime,FileEvidenceStore,FileHandleStore
from nollm_core import CoreRuntime

def test_same_core_different_access_root_rejected_and_release(tmp_path):
    core=CoreRuntime(tmp_path/'core');a=AccessRuntime(core,FileEvidenceStore(tmp_path/'a'),FileHandleStore(tmp_path/'a'))
    with pytest.raises(ValueError,match='different Access root'):AccessRuntime(core,FileEvidenceStore(tmp_path/'b'),FileHandleStore(tmp_path/'b'))
    a.close();b=AccessRuntime(core,FileEvidenceStore(tmp_path/'b'),FileHandleStore(tmp_path/'b'));b.close();core.close()
