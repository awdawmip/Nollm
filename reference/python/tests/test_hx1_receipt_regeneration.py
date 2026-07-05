from __future__ import annotations

from hashlib import sha256

from nollm.dream_geometry.host_execution import execute_host_plan, receipt_to_mapping

from test_hx1_trusted_host_bridge import hx1_fixture


def test_hx1_07_same_plan_same_root_reopens_identical_receipt(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
    before_tree = _tree_manifest(tmp_path / "work")
    second = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
    after_tree = _tree_manifest(tmp_path / "work")

    assert second == first
    assert second["output_fingerprint"] == first["output_fingerprint"]
    assert after_tree == before_tree


def _tree_manifest(root) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))
