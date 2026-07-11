import pytest
from nollm_core import CoreRuntime

def test_store_and_cell_bypass_rejected(tmp_path):
    core=CoreRuntime(tmp_path);payload=core.state_bytes()
    with pytest.raises(RuntimeError,match='owner capability'):core.store.write_bytes(payload)
    assert not hasattr(core,'cells');assert core.occupied_cells()==();core.close()
    with pytest.raises(RuntimeError,match='closed'):core.occupied_cells()
