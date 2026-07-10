from __future__ import annotations

import json

import pytest

from experiments.grf.grf7r2_evidence_pack import EvidenceSource, build_manifest, verify_pack, write_pack


def test_evidence_pack_rejects_modified_member(tmp_path) -> None:
    source = tmp_path / "raw"
    source.mkdir()
    (source / "event.json").write_text('{"event":1}\n', encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(build_manifest((EvidenceSource("raw", source),), ("generate",), "a" * 40, "b" * 40), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    pack = tmp_path / "evidence.tar.zst"
    write_pack(pack, manifest, (EvidenceSource("raw", source),))
    assert verify_pack(pack)["manifest"]["file_count"] == 1

    (source / "event.json").write_text('{"event":2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        write_pack(tmp_path / "changed.tar.zst", manifest, (EvidenceSource("raw", source),))
