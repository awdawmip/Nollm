import pytest
from nollm_core import GeometryAddress, GeometryAnchor

def test_unsorted_anchor_cells_rejected() -> None:
    a = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    b = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0, "p")
    GeometryAnchor("ok", (a, b))
    with pytest.raises(ValueError, match="canonical"): GeometryAnchor("bad", (b, a))
