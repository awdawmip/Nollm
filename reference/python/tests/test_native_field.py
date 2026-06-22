from __future__ import annotations

from pathlib import Path

from nollm.native_field import build_shard, load_field_head, move_staged_shards, publish_field_revision, stage_shards


def test_stage_move_and_flat_publish_is_retired(tmp_path: Path) -> None:
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

    staged = stage_shards(memory_root, "batch_a", [shard])
    moved = move_staged_shards(memory_root, "batch_a")
    revision = publish_field_revision(memory_root, batch_id="batch_a", target_field_id="field_fixture", shard_ids=[])

    assert staged["ok"] is False
    assert moved["ok"] is False
    assert staged["errors"] == ["unsupported_legacy_flat_writer"]
    assert moved["errors"] == ["unsupported_legacy_flat_writer"]
    assert revision["ok"] is False
    assert revision["errors"] == ["unsupported_legacy_flat_writer"]
    assert load_field_head(memory_root) is None
    assert not (memory_root / "field").exists()
