from __future__ import annotations

from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.legacy_extract import extract_legacy_spans, idempotence_key
from nollm.source_spans import build_source_span_inventory


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_extract_reads_archive_objects_not_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"
    snapshot = create_archive_snapshot(workspace, memory_root)["snapshot_id"]
    build_source_span_inventory(memory_root, str(snapshot))
    workspace.rename(tmp_path / "workspace.moved")

    records = extract_legacy_spans(memory_root, str(snapshot))

    assert len(records) == 3
    assert all(record["source_ref"].startswith(f"archive://snapshot/{snapshot}/source/src_") for record in records)
    assert all("/blob/sha256:" in record["source_ref"] for record in records)
    assert all(record["source_object_id"].startswith("src_") for record in records)
    assert any("Mira coordinates Atlas" in record["text"] for record in records)


def test_idempotence_key_uses_text_ref_and_policy() -> None:
    record = {"text": "A   B", "source_ref": "archive://object/sha256:abc#B0-B3"}

    first = idempotence_key(record, "openclaw_legacy_v1")
    second = idempotence_key({"text": "A B", "source_ref": record["source_ref"]}, "openclaw_legacy_v1")

    assert first == second
    assert first.startswith("sha256:")


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
