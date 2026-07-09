from __future__ import annotations

from grf_runtime_fixture import placement
from nollm.grf.bridge_kernel import BridgeKernel
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.ledger import GRFLedger
from nollm.grf.replay import rebuild_relation_field_from_files
from nollm.grf.storage import GRFFileStore


def test_relation_field_rebuilds_from_files_and_ledger_records(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    left = placement("shard_a", "patch_a", 1, 0, 0, "source:a")
    right = placement("shard_b", "patch_b", 1, 1, 0, "source:b")
    bridge = BridgeKernel("bridge_ab", "patch_a", "patch_b", Q16_ONE // 2, "normal", 1, 2, ("shard:a", "shard:b"))
    store.write_placement_record(left, "2026-07-09T10:00:00+08:00")
    store.write_placement_record(right, "2026-07-09T10:00:01+08:00")
    store.write_bridge_kernel(bridge)
    field = rebuild_relation_field_from_files(tmp_path, "2026-07-09T10:00:02+08:00")
    assert [record.shard_id for record in field.placements] == ["shard_a", "shard_b"]
    assert GRFLedger(tmp_path).events()[-1].event_type == "relation_field_rebuilt"
