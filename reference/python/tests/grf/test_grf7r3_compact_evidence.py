from __future__ import annotations

import json

from experiments.grf.grf7r3_compact_evidence import EvidenceSource, build_manifest, verify_capsule, write_capsule


def test_compact_capsule_binds_manifest_receipt_and_jsonl_samples(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "events.jsonl").write_text('{"event":1}\n{"event":2}\n', encoding="utf-8")
    manifest = build_manifest((EvidenceSource("r2", source),), producing_commit="a" * 40, report_commit="b" * 40)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "nollm_grf7r3_delivery_receipt_v2", "actual_final_head": "c" * 40}), encoding="utf-8")
    report = tmp_path / "report.txt"
    report.write_text("Windows test transcript", encoding="utf-8")
    capsule = tmp_path / "compact.tar.zst"
    write_capsule(capsule, manifest_path, receipt, (report,), (EvidenceSource("r2", source),))
    result = verify_capsule(capsule)
    assert result["manifest"]["merkle_root_sha256"] == manifest["merkle_root_sha256"]
    assert result["sample_groups"] == 1
