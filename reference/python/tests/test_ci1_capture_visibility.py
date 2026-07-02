from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from nollm.dream_geometry.capture import (
    CaptureDiagnostics,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    CaptureVisibility,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store
from nollm.dream_geometry.protocol.contracts import OriginKind


def test_c108_explicit_physical_visibility_windows_are_precise_and_read_only(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    ingress = CaptureIngress(tmp_path / "ci1")
    session_policy = CapturePolicy("cp_session", allowed_visibility_scopes=(VisibilityScope.session_window,))
    source_policy = CapturePolicy("cp_source", allowed_visibility_scopes=(VisibilityScope.source_window,))
    r1 = ingress.capture(_request("cap_s1", "one", ("session:a",), VisibilityScope.session_window), session_policy, evidence)
    r2 = ingress.capture(_request("cap_s2", "two", ("session:a",), VisibilityScope.session_window), session_policy, evidence)
    r3 = ingress.capture(_request("cap_s3", "three", ("session:b",), VisibilityScope.session_window), session_policy, evidence)
    r4 = ingress.capture(_request("cap_src1", "source one", ("source:x",), VisibilityScope.source_window), source_policy, evidence)
    before = (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1"))

    visibility = CaptureVisibility(ingress.state_store, evidence)

    assert visibility.session_window_ids("session:a") == (r1.shard_id, r2.shard_id)
    assert visibility.session_window_ids("session:b") == (r3.shard_id,)
    assert visibility.source_window_ids("source:x") == (r4.shard_id,)
    assert [shard.content for shard in visibility.session_window("session:a")] == ["one", "two"]
    assert visibility.persistent_explicit((r2.shard_id, r1.shard_id, r2.shard_id))[0].content == "two"
    assert not hasattr(visibility, "list_all")
    assert not hasattr(visibility, "search")
    assert not hasattr(visibility, "rank")
    assert not hasattr(visibility, "recent_global")
    assert (_manifest(tmp_path / "evidence"), _manifest(tmp_path / "ci1")) == before


def test_c109_unadmitted_capture_objects_do_not_cross_into_admission_or_recall_boundaries(tmp_path) -> None:
    evidence = open_store(tmp_path / "evidence")
    receipt = CaptureIngress(tmp_path / "ci1").capture(_request("cap_boundary", "boundary", ("session:a",), VisibilityScope.session_window), CapturePolicy("cp_boundary"), evidence)

    with pytest.raises(AttributeError):
        _ = receipt.record
    with pytest.raises(AttributeError):
        _ = receipt.projection_fingerprint

    source = Path("reference/python/nollm/dream_geometry/capture")
    forbidden_modules = {"cortex", "admission", "geometry", "field", "assembly", "recall", "adapters"}
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name.startswith("nollm.dream_geometry." + module) for name in names for module in forbidden_modules), path


def test_visibility_rejects_implicit_or_global_selectors(tmp_path) -> None:
    visibility = CaptureVisibility(CaptureIngress(tmp_path / "ci1").state_store, open_store(tmp_path / "evidence"))
    with pytest.raises(Exception):
        visibility.session_window("../escape")
    with pytest.raises(Exception):
        visibility.persistent_explicit(())


def _request(capture_id: str, content: str, refs: tuple[str, ...], scope: VisibilityScope) -> CaptureRequest:
    return CaptureRequest(
        capture_id,
        content,
        CaptureOrigin(OriginKind.user_utterance, "opaque", refs[0], "user"),
        "2026-07-02T12:34:56+08:00",
        refs,
        scope,
    )


def _manifest(root: Path) -> tuple[tuple[str, int], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), path.stat().st_size) for path in root.rglob("*") if path.is_file()))
