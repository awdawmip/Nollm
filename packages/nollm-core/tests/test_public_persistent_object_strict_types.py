import pytest

from nollm_core import BridgeSpec, GeometryAddress, GeometryAnchor


def test_bad_anchor_and_bridge_types_rejected_before_write() -> None:
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    with pytest.raises(TypeError, match="anchor_id"):
        GeometryAnchor(123, (cell,))
    anchor = GeometryAnchor("a", (cell,))
    with pytest.raises(TypeError, match="bridge_id"):
        BridgeSpec(456, anchor, anchor, 1, "normal", 1, 1)
