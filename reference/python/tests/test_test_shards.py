from __future__ import annotations

import json
from pathlib import Path
import sys

from subprocess_harness import run_subprocess, subprocess_failure_message


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_nollm_test_shards.py"


def test_collect_profile_writes_default_runtime_report() -> None:
    result = run_subprocess(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            "collect",
            "--repo-root",
            str(ROOT),
            "--timeout",
            "30",
        ],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=40,
    )
    output = ROOT / "out" / "nollm_runtime" / "test_shards" / "collect.json"
    data = json.loads(output.read_text(encoding="utf-8"))

    assert result.returncode == 0, subprocess_failure_message(result, REFERENCE_PYTHON, "run_nollm_test_shards")
    assert data["profile"] == "collect"
    assert data["status"] == "ok"
    assert data["returncode"] == 0
    assert data["timed_out"] is False
    assert data["collected_count"] > 0
    assert "Traceback" not in data["stderr_tail"]


def test_tiny_timeout_reports_json_without_traceback_spam(tmp_path: Path) -> None:
    output = tmp_path / "timeout.json"
    result = run_subprocess(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            "collect",
            "--repo-root",
            str(ROOT),
            "--timeout",
            "0",
            "--output",
            str(output),
        ],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=20,
    )
    data = json.loads(output.read_text(encoding="utf-8"))

    assert result.returncode != 0
    assert data["profile"] == "collect"
    assert data["status"] == "timed_out"
    assert data["returncode"] == -1
    assert data["timed_out"] is True
    assert data["timeout_seconds"] == 0
    assert "Traceback" not in data["stdout_tail"]
    assert "Traceback" not in data["stderr_tail"]


def test_profile_reports_missing_files_without_failing_known_profiles(tmp_path: Path) -> None:
    output = tmp_path / "docs.json"
    result = run_subprocess(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            "docs",
            "--repo-root",
            str(ROOT),
            "--timeout",
            "60",
            "--output",
            str(output),
        ],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=70,
    )
    data = json.loads(output.read_text(encoding="utf-8"))

    assert result.returncode == 0, subprocess_failure_message(result, REFERENCE_PYTHON, "run_nollm_test_shards docs")
    assert data["profile"] == "docs"
    assert isinstance(data["missing_tests"], list)
    assert data["status"] == "ok"


def test_shard_runner_does_not_leave_python_runtime_cache() -> None:
    leftovers = []
    leftovers.extend(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("__pycache__"))
    leftovers.extend(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.pyc"))

    assert sorted(leftovers) == []
