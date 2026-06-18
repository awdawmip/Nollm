from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from nollm.engineering_rc_export import (
    CANONICAL_COMMANDS,
    FORBIDDEN_SEMANTICS,
    REQUIRED_RELEASE_FILES,
    SCHEMA,
    build_engineering_rc_export_check,
)

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "check_engineering_rc_export.py"


def test_export_manifest_required_paths_exist() -> None:
    report = build_engineering_rc_export_check(ROOT)

    assert report["ok"] is True
    assert report["schema"] == SCHEMA
    assert report["failures"] == []
    assert "conversation_backups/" not in json.dumps(report, sort_keys=True)
    for path in REQUIRED_RELEASE_FILES:
        assert path in report["checked_files"]


def test_evaluation_guide_commands_include_current_canonical_commands() -> None:
    report = build_engineering_rc_export_check(ROOT)
    guide = (ROOT / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md").read_text(
        encoding="utf-8"
    )

    assert report["checked_commands"] == list(CANONICAL_COMMANDS)
    for command in CANONICAL_COMMANDS:
        assert command in guide


def test_forbidden_semantics_remain_absent() -> None:
    report = build_engineering_rc_export_check(ROOT)

    assert report["forbidden_semantics"] == {phrase: False for phrase in FORBIDDEN_SEMANTICS}


def test_checker_exits_nonzero_for_missing_required_manifest_path(tmp_path: Path) -> None:
    repo = _minimal_release_repo(tmp_path)
    manifest = repo / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["read_first"].append("docs/missing.md")
    manifest.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo)],
        cwd=REFERENCE_PYTHON,
        text=True,
        capture_output=True,
        timeout=30,
    )
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert report["ok"] is False
    assert "missing_path:docs/missing.md" in report["failures"]


def test_checker_exits_nonzero_for_forbidden_phrase(tmp_path: Path) -> None:
    repo = _minimal_release_repo(tmp_path)
    freeze = repo / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_FREEZE_20260618.md"
    freeze.write_text(freeze.read_text(encoding="utf-8") + "\nNollm is proven long-term memory.\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo)],
        cwd=REFERENCE_PYTHON,
        text=True,
        capture_output=True,
        timeout=30,
    )
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert report["ok"] is False
    assert "forbidden_semantics:Nollm is proven long-term memory" in report["failures"]


def test_running_checker_does_not_dirty_working_tree() -> None:
    before = _git_status_short()
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REFERENCE_PYTHON,
        text=True,
        capture_output=True,
        timeout=30,
    )
    after = _git_status_short()

    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def _minimal_release_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    release_dir = repo / "docs/releases"
    release_dir.mkdir(parents=True)

    for path in REQUIRED_RELEASE_FILES:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# placeholder\n", encoding="utf-8")

    guide = release_dir / "NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md"
    guide.write_text("\n".join(CANONICAL_COMMANDS) + "\n", encoding="utf-8")

    runtime_reports = [
        "out/nollm_runtime/g_series_engineering_closure_report.json",
        "out/nollm_runtime/minimal_ablation_experiment_report.json",
        "out/nollm_runtime/mode3_trace_experiment_report.json",
        "out/nollm_runtime/gravity_report_demo.json",
        "out/nollm_runtime/multi_step_coverage_report.json",
        "out/nollm_runtime/offset_sampling_report.json",
        "out/nollm_runtime/reverse_cover_report.json",
    ]
    audit = release_dir / "NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"
    audit.write_text(
        "## Expected Generated Reports\n\n```text\n" + "\n".join(runtime_reports) + "\n```\n",
        encoding="utf-8",
    )

    manifest_paths = {
        "read_first": ["docs/one.md"],
        "implementation_modules": ["reference/python/nollm/one.py"],
        "tests": ["reference/python/tests/test_one.py"],
        "runtime_reports": runtime_reports,
    }
    for paths in manifest_paths.values():
        for path in paths:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}\n" if path.endswith(".json") else "# placeholder\n", encoding="utf-8")
    manifest = {
        "schema": "nollm.engineering_gravity_rc_export_manifest.v1",
        "status": "experimental_internal_only",
        **manifest_paths,
    }
    (release_dir / "NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return repo


def _git_status_short() -> str:
    return subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True, timeout=30)
