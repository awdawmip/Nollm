from __future__ import annotations

from hashlib import sha256

from nollm.grf.evidence import EvidenceShardRecord
from nollm.grf.json_canonical import canonical_loads
from nollm.grf.ledger import GRFLedger
from nollm.grf.storage import GRFFileStore


def test_evidence_shard_stores_original_content_and_hash(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    shard = EvidenceShardRecord("shard:ci1:abc/unsafe?", "alpha beta", "2026-07-09T00:00:00Z", "validation_fixture", ("window:1",), "trusted_fixture", "captured")
    path = store.write_evidence_shard(shard, "2026-07-09T00:00:01Z")

    assert "shard:ci1" not in path.name
    payload = canonical_loads(path.read_bytes())["payload"]
    assert payload["shard_id"] == shard.shard_id
    assert payload["content"] == "alpha beta"
    assert payload["content_sha256"] == sha256(b"alpha beta").hexdigest()
    assert "truth_score" not in payload
    assert "importance_score" not in payload
    assert "semantic_edge" not in payload
    assert store.read_evidence_shard(shard.shard_id) == shard
    assert GRFLedger(tmp_path).events()[0].event_type == "object_written"
