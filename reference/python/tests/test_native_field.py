from __future__ import annotations

from pathlib import Path

from nollm.native_field import build_shard, existing_shards_by_key, move_staged_shards, publish_field_revision, stage_shards


def test_stage_move_and_publish_field_revision(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory-root"
    shard = build_shard(
        {
            "text": "A memory shard",
            "text_hash": "sha256:" + "a" * 64,
            "source_ref": "archive://object/sha256:abc#B0-B14",
            "span_id": "span_abc_0000",
        },
        batch_id="batch_a",
        source_policy_id="openclaw_legacy_v1",
        idempotence_key="sha256:" + "b" * 64,
    )

    stage_shards(memory_root, "batch_a", [shard])
    moved = move_staged_shards(memory_root, "batch_a")
    revision = publish_field_revision(memory_root, batch_id="batch_a", target_field_id="field_fixture", shard_ids=moved)

    assert moved == [shard["shard_id"]]
    assert revision["shard_count"] == 1
    assert (memory_root / "field" / "HEAD.json").exists()
    assert existing_shards_by_key(memory_root)[shard["idempotence_key"]]["shard_id"] == shard["shard_id"]
