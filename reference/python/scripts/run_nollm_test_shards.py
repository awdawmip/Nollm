from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.pytest_env import isolated_pytest_env  # noqa: E402

REFERENCE_PYTHON = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
TAIL_CHARS = 4000
POLL_INTERVAL_SECONDS = 0.1
KILL_WAIT_SECONDS = 3.0

PROFILE_KINDS = {
    "collect": "builtin",
    "core": "pytest",
    "docs": "pytest",
    "dream_pipeline": "pytest",
    "dream_reports": "pytest",
    "dream_gate": "pytest",
    "shard_runner": "pytest",
    "shard_smoke": "pytest",
    "dream": "aggregate",
    "full": "builtin",
}

PROFILE_ORDER = tuple(PROFILE_KINDS)

PROFILE_TESTS: dict[str, tuple[str, ...]] = {
    "core": (
        "tests/test_write_read.py",
        "tests/test_recall.py",
        "tests/test_tool_api.py",
        "tests/test_tool_envelope.py",
        "tests/test_status.py",
        "tests/test_validate.py",
        "tests/test_cortex.py",
        "tests/test_history.py",
        "tests/test_audit.py",
        "tests/test_review.py",
        "tests/test_annotations.py",
    ),
    "docs": (
        "tests/test_architecture_language.py",
        "tests/test_context_boundary.py",
        "tests/test_examples.py",
        "tests/test_honeycomb_metadata.py",
        "tests/test_inspection_semantics.py",
        "tests/test_integration_pack.py",
        "tests/test_no_forbidden_features.py",
        "tests/test_package_hygiene_script.py",
        "tests/test_repository_hygiene.py",
        "tests/test_terminology.py",
        "tests/test_v1_docs_consistency.py",
        "tests/test_v1_route_lock.py",
    ),
    "dream_pipeline": (
        "tests/test_dream_shard.py",
        "tests/test_dream_placement.py",
        "tests/test_dream_pipeline_runner.py",
        "tests/test_dream_geometry_pipeline.py",
        "tests/test_cluster_pressure.py",
        "tests/test_scale_scan_traversal.py",
        "tests/test_parameter_experiments.py",
        "tests/test_openclaw_dream_experiment.py",
    ),
    "dream_reports": (
        "tests/test_dream_checks_manifest.py",
        "tests/test_dream_corpus_dry_run.py",
        "tests/test_dream_experiment_batch.py",
        "tests/test_dream_golden_regression.py",
        "tests/test_dream_regression.py",
        "tests/test_dream_suite.py",
        "tests/test_dream_triage.py",
    ),
    "dream_gate": (
        "tests/test_local_gate.py",
        "tests/test_run_tests_runner.py",
        "tests/test_package_hygiene_script.py",
    ),
    "shard_runner": (
        "tests/test_test_shards.py",
        "tests/test_nollm_test_shards.py",
    ),
    "shard_smoke": (
        "tests/test_init.py",
    ),
}

AGGREGATE_PROFILES = {
    "dream": ("dream_pipeline", "dream_reports", "dream_gate"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic internal Nollm pytest shards.")
    parser.add_argument("--profile", choices=PROFILE_ORDER, default=None)
    parser.add_argument("--list-profiles", action="store_true", help="Print deterministic JSON profile metadata.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root path.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Subprocess timeout in seconds.")
    parser.add_argument("--output", default=None, help="Output JSON path.")
    args = parser.parse_args(argv)

    if args.list_profiles:
        print(json.dumps(profile_manifest(), indent=2, sort_keys=True))
        return 0
    if args.profile is None:
        parser.error("--profile is required unless --list-profiles is used")

    repo_root = Path(args.repo_root).resolve()
    reference_python = repo_root / "reference" / "python"
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "test_shards" / f"{args.profile}.json"
    )
    report = run_test_shard(
        args.profile,
        reference_python=reference_python,
        timeout_seconds=args.timeout,
    )
    write_report(report, output)
    print(
        "wrote nollm test shard report "
        f"path={output} profile={report['profile']} status={report['status']} "
        f"returncode={report['returncode']} timed_out={str(report['timed_out']).lower()}"
    )
    return 0 if report["status"] == "ok" else 1


def run_test_shard(profile: str, *, reference_python: Path, timeout_seconds: float) -> dict[str, object]:
    command, missing = command_for_profile(profile, reference_python)
    env = isolated_pytest_env()
    started = time.monotonic()
    stdout = ""
    stderr = ""
    returncode = 0
    timed_out = False
    if not command:
        status = "skipped"
        duration = time.monotonic() - started
    else:
        try:
            result = _run_command(
                command,
                cwd=reference_python,
                env=env,
                timeout=timeout_seconds,
            )
            stdout = result.stdout
            stderr = result.stderr
            returncode = int(result.returncode)
            status = "ok" if returncode == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            stdout = _string_output(exc.stdout)
            stderr = _string_output(exc.stderr)
            returncode = -1
            timed_out = True
            status = "timed_out"
        duration = time.monotonic() - started

    return {
        "schema": "nollm.test_shard.v1",
        "status": status,
        "profile": profile,
        "command": command,
        "missing_tests": missing,
        "returncode": returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "duration_seconds": round(duration, 3),
        "collected_count": collected_count(stdout),
        "stdout_tail": tail(stdout),
        "stderr_tail": tail(stderr),
    }


def command_for_profile(profile: str, reference_python: Path) -> tuple[list[str], list[str]]:
    if profile == "collect":
        return [sys.executable, "-m", "pytest", "--collect-only", "-q"], []
    if profile == "full":
        return [sys.executable, "run_tests.py"], []
    if profile in AGGREGATE_PROFILES:
        selected: list[str] = []
        missing: list[str] = []
        for child in AGGREGATE_PROFILES[profile]:
            child_command, child_missing = command_for_profile(child, reference_python)
            missing.extend(child_missing)
            selected.extend(child_command[4:] if child_command else [])
        if not selected:
            return [], missing
        return [sys.executable, "-m", "pytest", "-q", *selected], sorted(set(missing))
    selected: list[str] = []
    missing: list[str] = []
    for pattern in PROFILE_TESTS[profile]:
        if any(char in pattern for char in "*?[]"):
            matches = sorted(path.relative_to(reference_python).as_posix() for path in reference_python.glob(pattern))
            if matches:
                selected.extend(matches)
            else:
                missing.append(pattern)
            continue
        path = reference_python / pattern
        if path.exists():
            selected.append(pattern)
        else:
            missing.append(pattern)
    if not selected:
        return [], missing
    return [sys.executable, "-m", "pytest", "-q", *selected], missing


def profile_manifest() -> dict[str, object]:
    return {
        "schema": "nollm.test_shard_profiles.v1",
        "profiles": [
            {"name": name, "kind": PROFILE_KINDS[name]}
            for name in PROFILE_ORDER
        ],
    }


def _run_command(command: list[str], *, cwd: Path, env: dict[str, str], timeout: float) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
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
            raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(command, int(process.returncode), stdout, stderr)


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
    return tail(path.read_text(encoding="utf-8", errors="replace"))


def collected_count(stdout: str) -> int:
    matches = re.findall(r"(\d+)\s+tests?\s+collected", stdout)
    if matches:
        return int(matches[-1])
    node_ids = [
        line
        for line in stdout.splitlines()
        if "::" in line and not line.startswith(("=", " "))
    ]
    return len(node_ids)


def tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return f"... output truncated to last {TAIL_CHARS} chars ...\n{text[-TAIL_CHARS:]}"


def write_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _string_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
