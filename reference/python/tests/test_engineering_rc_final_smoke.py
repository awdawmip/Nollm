from __future__ import annotations

from pathlib import Path

from nollm.engineering_rc_final_smoke import (
    SCHEMA,
    SELECTED_RC_TESTS,
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
        "pytest_engineering_rc_export",
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
    assert failed["timed_out"] is False
    assert failed["stderr_tail"] == "bad package"


def test_final_smoke_marks_every_pytest_file_as_isolated() -> None:
    report = run_final_smoke(ROOT, runner=_ok_runner)
    pytest_checks = [item for item in report["checks"] if item["name"].startswith("pytest_")]

    assert len(pytest_checks) == len(SELECTED_RC_TESTS)
    assert all(item["isolated_pytest"] is True for item in pytest_checks)
    assert all(len(item["command"]) == 5 for item in pytest_checks)
    assert all(item["command"][1:4] == ["-m", "pytest", "-q"] for item in pytest_checks)
    assert {item["command"][4] for item in pytest_checks} == set(SELECTED_RC_TESTS)


def test_final_smoke_pytest_subprocess_uses_isolated_env(monkeypatch) -> None:
    captured = {}

    def fake_hard_timeout(command, *, cwd, env, timeout):
        captured["env"] = env
        return CommandResult(0, "", "")

    monkeypatch.setattr(engineering_rc_final_smoke, "_run_command_hard_timeout", fake_hard_timeout)
    check = [item for item in final_smoke_checks(ROOT) if item.name == "pytest_engineering_rc_export"][0]

    result = engineering_rc_final_smoke._run_subprocess_check(check, ROOT / "reference" / "python")

    assert result.returncode == 0
    assert captured["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert captured["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_final_smoke_default_commands_avoid_heavy_paths() -> None:
    checks = final_smoke_checks(ROOT)
    flattened = [" ".join(check.command) for check in checks]
    joined = "\n".join(flattened)

    assert "run_tests.py" not in joined
    assert "--generate" not in joined
    assert "selected_rc_pytest" not in {check.name for check in checks}
    assert all(check.command[1:4] == ("-m", "pytest", "-q") for check in checks if check.name.startswith("pytest_"))
    assert "scripts/run_g_series_engineering_gate.py" in joined
    assert "scripts/run_nollm_test_shards.py --profile shard_smoke --timeout 20" in joined


def test_final_smoke_no_archive_build_omits_build_and_keeps_clean_tree_check() -> None:
    report = run_final_smoke(ROOT, archive_build=False, runner=_ok_runner)
    names = [item["name"] for item in report["checks"]]

    assert "deterministic_archive_build" not in names
    assert "deterministic_archive_verify" in names
    assert names[-1] == "clean_tree_status"
    assert report["ok"] is True


def test_final_smoke_no_archive_build_still_verifies_archive() -> None:
    names = [check.name for check in final_smoke_checks(ROOT)]

    assert "deterministic_archive_build" not in names
    assert "deterministic_archive_verify" in names


def test_final_smoke_archive_build_is_explicit_opt_in() -> None:
    names = [check.name for check in final_smoke_checks(ROOT, archive_build=True)]

    assert "deterministic_archive_build" in names
    assert "deterministic_archive_verify" in names


def test_final_smoke_timeout_failure_is_recorded_without_aborting_report() -> None:
    def runner(check, cwd):
        if check.name == "pytest_test_shards":
            return CommandResult(-1, "partial out", "partial err", timed_out=True)
        return _ok_runner(check, cwd)

    report = run_final_smoke(ROOT, archive_build=False, runner=runner)
    failed = [item for item in report["checks"] if item["name"] == "pytest_test_shards"][0]

    assert report["ok"] is False
    assert "pytest_test_shards" in report["failures"]
    assert failed["ok"] is False
    assert failed["returncode"] == -1
    assert failed["timed_out"] is True
    assert failed["stdout_tail"] == "partial out"
    assert failed["stderr_tail"] == "partial err"
    assert report["checks"][-1]["name"] == "clean_tree_status"


def _ok_runner(check, cwd):
    if check.name == "clean_tree_status":
        return CommandResult(0, "", "")
    return CommandResult(0, "ok", "")
