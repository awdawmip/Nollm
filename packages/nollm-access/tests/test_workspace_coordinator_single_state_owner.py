import pytest
from nollm_access import AccessRuntime, FileEvidenceStore, FileHandleStore
from nollm_core import CoreRuntime

def test_same_core_shared_and_distinct_owner_rejected(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    second = CoreRuntime(tmp_path / "core")
    with pytest.raises(RuntimeError, match="distinct mutable state owner"):
        AccessRuntime(second, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
