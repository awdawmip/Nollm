from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from nollm.pytest_env import isolated_pytest_env

SCHEMA = "nollm.engineering_rc_final_smoke.v1"
FORBIDDEN_SEMANTICS = {
    "stable_recall_surface": False,
    "hard_drift_rejection": False,
    "auto_writeback": False,
    "anchor_creation": False,
    "trust_status_mapping": False,
}

SELECTED_RC_TESTS = (
    "tests/test_engineering_rc_export.py",
    "tests/test_engineering_rc_artifact_hashes.py",
    "tests/test_engineering_rc_archive.py",
    "tests/test_g_series_engineering_closure.py",
    "tests/test_minimal_ablation_experiment.py",
    "tests/test_mode3_trace_experiment.py",
    "tests/test_gravity.py",
    "tests/test_nollm_test_shards.py",
    "tests/test_test_shards.py",
)
POLL_INTERVAL_SECONDS = 0.05
KILL_WAIT_SECONDS = 3.0
TAIL_CHARS = 4000


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    command: tuple[str, ...]
    timeout_seconds: int = 120
    isolated_pytest: bool = False


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


Runner = Callable[[SmokeCheck, Path], CommandResult]


def final_smoke_checks(repo_root: Path, *, archive_build: bool = False) -> list[SmokeCheck]:
    reference_python = repo_root / "reference" / "python"
    archive_path = repo_root / "out" / "nollm_runtime" / "releases" / "nollm_engineering_gravity_rc.zip"
    archive_report = repo_root / "out" / "nollm_runtime" / "engineering_rc_archive_report.json"
    checks = [
        SmokeCheck("local_gate_skip_pytest", (sys.executable, "scripts/run_nollm_local_gate.py", "--skip-pytest")),
        SmokeCheck("dream_golden_regression", (sys.executable, "scripts/run_dream_golden_regression.py")),
        SmokeCheck("g_series_engineering_gate", (sys.executable, "scripts/run_g_series_engineering_gate.py")),
        SmokeCheck("engineering_rc_export_check", (sys.executable, "scripts/check_engineering_rc_export.py")),
        SmokeCheck("package_hygiene", (sys.executable, "scripts/check_package_hygiene.py", "../..")),
        SmokeCheck("artifact_hash_manifest_validation", (sys.executable, "scripts/check_engineering_rc_export.py")),
    ]
    if archive_build:
        checks.append(
            SmokeCheck(
                "deterministic_archive_build",
                (
                    sys.executable,
                    "scripts/build_engineering_rc_export_archive.py",
                    "--output",
                    _relative_to(reference_python, archive_path),
                    "--report",
                    _relative_to(reference_python, archive_report),
                ),
            )
        )
    checks.extend(
        [
            SmokeCheck(
                "deterministic_archive_verify",
                (
                    sys.executable,
                    "scripts/build_engineering_rc_export_archive.py",
                    "--verify",
                    _relative_to(reference_python, archive_path),
                ),
            ),
            SmokeCheck("test_shard_list_profiles", (sys.executable, "scripts/run_nollm_test_shards.py", "--list-profiles")),
            SmokeCheck(
                "test_shard_smoke",
                (sys.executable, "scripts/run_nollm_test_shards.py", "--profile", "shard_smoke", "--timeout", "20"),
                timeout_seconds=40,
            ),
            *_pytest_smoke_checks(),
            SmokeCheck("clean_tree_status", ("git", "status", "--short")),
        ]
    )
    return checks


def _pytest_smoke_checks() -> list[SmokeCheck]:
    return [
        SmokeCheck(
            f"pytest_{Path(test_path).stem.removeprefix('test_')}",
            (sys.executable, "-m", "pytest", "-q", test_path),
            timeout_seconds=35,
            isolated_pytest=True,
        )
        for test_path in SELECTED_RC_TESTS
    ]


def run_final_smoke(
    repo_root: Path,
    *,
    archive_build: bool = False,
    runner: Runner | None = None,
    verbose: bool = False,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    reference_python = repo_root / "reference" / "python"
    run = runner or _run_subprocess_check
    check_records: list[dict[str, object]] = []
    failures: list[str] = []
    for check in final_smoke_checks(repo_root, archive_build=archive_build):
        started = time.monotonic()
        result = run(check, reference_python)
        duration = round(time.monotonic() - started, 3)
        stdout_tail = _tail(result.stdout) if verbose or result.returncode != 0 else ""
        stderr_tail = _tail(result.stderr) if verbose or result.returncode != 0 else ""
        ok = result.returncode == 0
        if check.name == "clean_tree_status":
            ok = ok and result.stdout.strip() == ""
        if not ok:
            failures.append(check.name)
        check_records.append(
            {
                "name": check.name,
                "ok": ok,
                "returncode": int(result.returncode),
                "duration_seconds": duration,
                "timed_out": bool(result.timed_out),
                "isolated_pytest": check.isolated_pytest,
                "command": list(check.command),
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            }
        )
    report = {
        "schema": SCHEMA,
        "ok": not failures and not any(FORBIDDEN_SEMANTICS.values()),
        "checks": check_records,
        "failures": failures,
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
    }
    _assert_json_primitive(report)
    return report


def write_final_smoke_report(report: Mapping[str, object], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _run_subprocess_check(check: SmokeCheck, cwd: Path) -> CommandResult:
    env = isolated_pytest_env() if check.isolated_pytest else None
    command = list(check.command)
    if check.isolated_pytest:
        return _run_command_hard_timeout(command, cwd=cwd, env=env, timeout=check.timeout_seconds)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=check.timeout_seconds,
        )
        return CommandResult(int(result.returncode), result.stdout, result.stderr, False)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(-1, _string_output(exc.stdout), _string_output(exc.stderr), True)


def _run_command_hard_timeout(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None,
    timeout: float,
) -> CommandResult:
    with tempfile.TemporaryDirectory() as tmp:
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=dict(env) if env is not None else None,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=(os.name != "nt"),
                creationflags=creationflags,
            )
            timed_out = _wait_with_deadline(process, timeout)
        stdout = _read_tail_file(stdout_path)
        stderr = _read_tail_file(stderr_path)
        if timed_out:
            return CommandResult(-1, stdout, stderr, True)
        return CommandResult(int(process.returncode), stdout, stderr, False)


def _wait_with_deadline(process: subprocess.Popen[str], timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while process.poll() is None:
        if time.monotonic() >= deadline:
            _terminate_process_tree(process)
            _wait_for_exit(process, KILL_WAIT_SECONDS)
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return False


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).wait(timeout=KILL_WAIT_SECONDS)
        except Exception:
            process.kill()
    else:
        import signal

        os.killpg(process.pid, signal.SIGKILL)


def _wait_for_exit(process: subprocess.Popen[str], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
    if process.poll() is None:
        try:
            process.kill()
        except Exception:
            pass


def _read_tail_file(path: Path) -> str:
    if not path.exists():
        return ""
    return _tail(path.read_text(encoding="utf-8", errors="replace"), limit=TAIL_CHARS)


def _relative_to(base: Path, target: Path) -> str:
    return Path(os.path.relpath(target.resolve(), base.resolve())).as_posix()


def _tail(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return f"... output truncated to last {limit} chars ...\n{text[-limit:]}"


def _string_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _assert_json_primitive(value: object) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_primitive(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("report keys must be strings")
            _assert_json_primitive(item)
        return
    raise TypeError(f"report value is not JSON primitive: {type(value).__name__}")


__all__ = [
    "FORBIDDEN_SEMANTICS",
    "SCHEMA",
    "CommandResult",
    "SmokeCheck",
    "final_smoke_checks",
    "run_final_smoke",
    "write_final_smoke_report",
]
