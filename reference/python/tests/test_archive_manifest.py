from __future__ import annotations

from nollm.archive_manifest import manifest_hash, newline_profile


def test_manifest_hash_excludes_manifest_hash_field() -> None:
    manifest = {"schema": "x", "objects": [], "manifest_hash": None}
    digest = manifest_hash(manifest)
    manifest["manifest_hash"] = digest

    assert manifest_hash(manifest) == digest


def test_newline_profile_detects_lf_crlf_and_mixed() -> None:
    assert newline_profile(b"a\nb\n") == "lf"
    assert newline_profile(b"a\r\nb\r\n") == "crlf"
    assert newline_profile(b"a\r\nb\n") == "mixed"
