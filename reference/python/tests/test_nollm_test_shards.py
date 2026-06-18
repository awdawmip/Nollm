from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from subprocess_harness import run_subprocess
ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_nollm_test_shards.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_nollm_test_shards", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_list_profiles_returns_deterministic_json() -> None:
    first = subprocess.check_output([sys.executable, str(SCRIPT), "--list-profiles"], cwd=REFERENCE_PYTHON, text=True)
    second = subprocess.check_output([sys.executable, str(SCRIPT), "--list-profiles"], cwd=REFERENCE_PYTHON, text=True)
    data = json.loads(first)

    assert first == second
    assert data["schema"] == "nollm.test_shard_profiles.v1"
    assert [item["name"] for item in data["profiles"]] == [
        "collect",
        "core",
        "docs",
        "dream_pipeline",
        "dream_reports",
        "dream_gate",
        "dream",
        "full",
    ]
    assert {item["name"]: item["kind"] for item in data["profiles"]}["dream"] == "aggregate"


def test_dream_subprofiles_resolve_to_deterministic_commands() -> None:
    runner = load_runner()

    for profile in ("dream_pipeline", "dream_reports", "dream_gate"):
        first, first_missing = runner.command_for_profile(profile, REFERENCE_PYTHON)
        second, second_missing = runner.command_for_profile(profile, REFERENCE_PYTHON)
        assert first == second
        assert second_missing == first_missing == []
        assert first[:4] == [sys.executable, "-m", "pytest", "-q"]
        assert all(item.startswith("tests/") for item in first[4:])


def test_dream_profile_aggregates_subprofiles() -> None:
    runner = load_runner()
    dream, missing = runner.command_for_profile("dream", REFERENCE_PYTHON)
    pipeline, _ = runner.command_for_profile("dream_pipeline", REFERENCE_PYTHON)
    reports, _ = runner.command_for_profile("dream_reports", REFERENCE_PYTHON)
    gate, _ = runner.command_for_profile("dream_gate", REFERENCE_PYTHON)

    assert missing == []
    assert dream[:4] == [sys.executable, "-m", "pytest", "-q"]
    assert dream[4:] == pipeline[4:] + reports[4:] + gate[4:]


def test_timeout_report_schema_with_fake_subprocess(monkeypatch) -> None:
    runner = load_runner()

    class FakeProcess:
        pid = 12345
        returncode = None
        calls = 0

        def communicate(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(["fake"], timeout, output="partial out", stderr="partial err")
            self.returncode = -1
            return "partial out", "partial err"

        def poll(self):
            return None

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr(runner, "_terminate_process_tree", lambda process: None)

    report = runner.run_test_shard("collect", reference_python=REFERENCE_PYTHON, timeout_seconds=0.01)

    assert report["status"] == "timed_out"
    assert report["timed_out"] is True
    assert report["timeout_seconds"] == 0.01
    assert report["returncode"] == -1
    assert report["command"] == [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    assert "partial out" in report["stdout_tail"]
    assert "partial err" in report["stderr_tail"]


def test_runtime_report_path_does_not_dirty_git_status() -> None:
    output = ROOT / "out" / "nollm_runtime" / "test_shards" / "dream_gate.json"
    output.unlink(missing_ok=True)
    before = _git_status_short()
    result = run_subprocess(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            "dream_gate",
            "--repo-root",
            str(ROOT),
            "--timeout",
            "60",
        ],
        cwd=REFERENCE_PYTHON,
        timeout_seconds=80,
    )
    after = _git_status_short()

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.exists()
    assert before == after


def _git_status_short() -> str:
    result = run_subprocess(["git", "status", "--short"], cwd=ROOT, timeout_seconds=30)
    assert result.returncode == 0
    return result.stdout
