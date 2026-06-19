from __future__ import annotations

from pathlib import Path
import subprocess

from nollm.engineering_rc_final_smoke import (
    SCHEMA,
    CommandResult,
    final_smoke_checks,
    run_final_smoke,
)
from nollm import engineering_rc_final_smoke

ROOT = Path(__file__).resolve().parents[3]


def test_final_smoke_report_schema_and_forbidden_semantics() -> None:
    report = run_final_smoke(ROOT, runner=_ok_runner)

    assert report["schema"] == SCHEMA
    assert report["ok"] is True
    assert report["failures"] == []
    assert all(value is False for value in report["forbidden_semantics"].values())
    assert {item["name"] for item in report["checks"]} >= {
        "local_gate_skip_pytest",
        "engineering_rc_export_check",
        "artifact_hash_manifest_validation",
        "deterministic_archive_verify",
        "package_hygiene",
        "selected_rc_pytest",
    }


def test_final_smoke_failure_aggregation() -> None:
    def runner(check, cwd):
        if check.name == "package_hygiene":
            return CommandResult(1, "", "bad package")
        return CommandResult(0, "", "")

    report = run_final_smoke(ROOT, runner=runner)

    assert report["ok"] is False
    assert report["failures"] == ["package_hygiene"]
    failed = [item for item in report["checks"] if item["name"] == "package_hygiene"][0]
    assert failed["ok"] is False
    assert failed["stderr_tail"] == "bad package"


def test_final_smoke_marks_selected_pytest_as_isolated() -> None:
    report = run_final_smoke(ROOT, runner=_ok_runner)
    checks = {item["name"]: item for item in report["checks"]}

    assert checks["selected_rc_pytest"]["isolated_pytest"] is True
    assert checks["test_shard_smoke"]["isolated_pytest"] is False


def test_final_smoke_pytest_subprocess_uses_isolated_env(monkeypatch) -> None:
    captured = {}

    def fake_run(command, *, cwd, env, text, capture_output, timeout):
        captured["env"] = env
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(engineering_rc_final_smoke.subprocess, "run", fake_run)
    check = [item for item in final_smoke_checks(ROOT) if item.name == "selected_rc_pytest"][0]

    result = engineering_rc_final_smoke._run_subprocess_check(check, ROOT / "reference" / "python")

    assert result.returncode == 0
    assert captured["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert captured["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_final_smoke_default_commands_avoid_heavy_paths() -> None:
    checks = final_smoke_checks(ROOT)
    flattened = [" ".join(check.command) for check in checks]
    joined = "\n".join(flattened)
    selected = [check for check in checks if check.name == "selected_rc_pytest"][0]

    assert "run_tests.py" not in joined
    assert "--generate" not in joined
    assert selected.command[1:4] == ("-m", "pytest", "-q")
    assert "scripts/run_g_series_engineering_gate.py" in joined
    assert "scripts/run_nollm_test_shards.py --profile shard_smoke --timeout 20" in joined


def test_final_smoke_no_archive_build_still_verifies_archive() -> None:
    names = [check.name for check in final_smoke_checks(ROOT, archive_build=False)]

    assert "deterministic_archive_build" not in names
    assert "deterministic_archive_verify" in names


def _ok_runner(check, cwd):
    if check.name == "clean_tree_status":
        return CommandResult(0, "", "")
    return CommandResult(0, "ok", "")
