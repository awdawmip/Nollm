import pytest
from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress

def test_reuse_rejects_corrupt_evidence_before_binding(tmp_path) -> None:
    evidence=FileEvidenceStore(tmp_path); core=CoreRuntime(tmp_path/'core'); access=AccessRuntime(core,evidence,FileHandleStore(tmp_path))
    evidence.put_original(MemoryStatement('a','a')); cell=GeometryAddress('eisenstein_exact_v1','c',0,0,0)
    handle=access.apply(AccessDecision('a','a','new',target_cell=cell,reason_text='x'))
    evidence.put_original(MemoryStatement('b','b')); evidence._path('b').write_text('{}\n',encoding='utf-8')
    with pytest.raises(ValueError): access.apply(AccessDecision('b','b','reuse',existing_handle=handle,reason_text='x'))
    assert not access.handle_store.exists('b')
