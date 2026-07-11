import pytest
from nollm_core import CoreRuntime

def test_store_and_cell_bypass_rejected(tmp_path):
    core=CoreRuntime(tmp_path);payload=core.state_bytes()
    assert not hasattr(core,'store')
    assert not hasattr(core,'cells');assert core.occupied_cells()==();core.close()
    with pytest.raises(RuntimeError,match='closed'):core.occupied_cells()
