from __future__ import annotations

import json
from pathlib import Path

from cli_harness import run_cli


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mt1" / "legacy_workspace"


def test_legacy_import_cli_end_to_end(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    copy_fixture(FIXTURE, workspace)
    memory_root = tmp_path / "memory-root"

    snapshot = _json(run_cli(["archive", "snapshot", str(workspace), "--memory-root", str(memory_root)], cwd=tmp_path))
    verify = _json(run_cli(["archive", "verify", snapshot["snapshot_id"], "--memory-root", str(memory_root)], cwd=tmp_path))
    plan = _json(
        run_cli(
            ["legacy-import", "plan", snapshot["snapshot_id"], "--memory-root", str(memory_root), "--target-field-id", "field_fixture"],
            cwd=tmp_path,
        )
    )
    dry_run = _json(run_cli(["legacy-import", "run", plan["batch_id"], "--memory-root", str(memory_root), "--dry-run"], cwd=tmp_path))
    commit = _json(run_cli(["legacy-import", "run", plan["batch_id"], "--memory-root", str(memory_root), "--commit"], cwd=tmp_path))
    validate = _json(run_cli(["legacy-import", "validate", plan["batch_id"], "--memory-root", str(memory_root)], cwd=tmp_path))
    report = _json(run_cli(["legacy-import", "report", plan["batch_id"], "--memory-root", str(memory_root)], cwd=tmp_path))

    assert verify["ok"] is True
    assert plan["ok"] is True
    assert dry_run["candidate_shard_count"] == 3
    assert commit["created_shard_count"] == 3
    assert validate["ok"] is True
    assert report["validation"]["ok"] is True


def copy_fixture(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def _json(result: object) -> dict[str, object]:
    assert result.returncode == 0, result
    return json.loads(result.stdout)
