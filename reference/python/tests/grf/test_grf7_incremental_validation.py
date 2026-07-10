from __future__ import annotations

from nollm.grf.grf7_incremental_validation import run_incremental_repartition_validation


def test_incremental_repartition_matches_full_rebuild_and_preserves_identity() -> None:
    result = run_incremental_repartition_validation()
    assert result.add_changed_state and result.remove_changed_state and result.move_changed_state
    assert result.cross_partition_move_replayed and result.profile_change_replayed
    assert result.stitch_add_remove_replayed and result.split_merge_replayed
    assert result.incremental_equals_full_rebuild
    assert result.evidence_identity_preserved and result.placement_identity_preserved and result.admission_identity_preserved
    assert result.source_fallback_preserved and result.identity_collision_count == 0
    assert result.status == "GATE_F_PASS"
