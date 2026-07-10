from __future__ import annotations

import json

from experiments.grf.verify_external_artifacts import MANIFEST_NAME, build_manifest, verify


def test_external_artifact_verifier_detects_missing_and_modified_files(tmp_path) -> None:
    assert verify(tmp_path)[0] is False
    (tmp_path / "raw.json").write_text("{}\n", encoding="utf-8")
    manifest = build_manifest(tmp_path, "generate")
    (tmp_path / MANIFEST_NAME).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    assert verify(tmp_path)[0] is True

    (tmp_path / "raw.json").write_text("modified\n", encoding="utf-8")
    passed, message = verify(tmp_path)
    assert passed is False
    assert message.startswith("UNVERIFIED")
