from __future__ import annotations

import pytest

from nollm.grf.bridge_kernel import BridgeKernel
from nollm.grf.fixed_point import Q16_ONE


def test_bridge_kernel_requires_bounds_and_evidence() -> None:
    with pytest.raises(ValueError):
        BridgeKernel("bridge_bad", "patch_a", "patch_b", 0, "normal", 1, 1, ("shard:a",))
    with pytest.raises(ValueError):
        BridgeKernel("bridge_bad", "patch_a", "patch_b", Q16_ONE // 2, "normal", 1, 1, ())
    with pytest.raises(ValueError):
        BridgeKernel("bridge_bad", "patch_a", "patch_b", Q16_ONE // 2, "normal", 0, 1, ("shard:a",))


def test_bridge_kernel_fanout_and_mapping_do_not_merge_content() -> None:
    bridge = BridgeKernel("bridge_a", "patch_a", "patch_b", Q16_ONE, "strong", 2, 3, ("shard:a", "shard:b"))
    assert bridge.fanout_allowed(3) is True
    assert bridge.fanout_allowed(4) is False
    rendered = bridge.to_mapping()
    assert "content" not in rendered
    assert rendered["not_fact_merge"] is True
    assert rendered["not_parent_child"] is True
    assert rendered["no_global_traversal"] is True
