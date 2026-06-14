from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


GROUP_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 0.1
OUTPUT_TAIL_CHARS = 12000


def run_group(command: list[str], *, cwd: Path, env: dict[str, str], timeout_seconds: int) -> tuple[int | str, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                start_new_session=os.name != "nt",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            deadline = time.monotonic() + timeout_seconds
            timed_out = False
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    timed_out = True
                    terminate_process_tree(process)
                    break
                time.sleep(POLL_INTERVAL_SECONDS)
            if timed_out:
                wait_for_exit(process)

        stdout = read_tail(stdout_path)
        stderr = read_tail(stderr_path)
        if timed_out:
            return "timeout", stdout, stderr
        return int(process.returncode), stdout, stderr


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def wait_for_exit(process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 5
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)


def read_tail(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= OUTPUT_TAIL_CHARS:
        return text
    return f"... output truncated to last {OUTPUT_TAIL_CHARS} chars ...\n{text[-OUTPUT_TAIL_CHARS:]}"


def main() -> int:
    root = Path(__file__).resolve().parent
    test_files = sorted((root / "tests").glob("test_*.py"))
    if not test_files:
        print("No test files found.", file=sys.stderr)
        return 2

    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    failures: list[tuple[str, int | str]] = []

    for path in test_files:
        relative = path.relative_to(root).as_posix()
        print(f"== {relative} ==", flush=True)
        command = [sys.executable, "-m", "pytest", "-q", relative]
        result, stdout, stderr = run_group(command, cwd=root, env=env, timeout_seconds=GROUP_TIMEOUT_SECONDS)
        if stdout:
            print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
        if stderr:
            print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
        if result == "timeout":
            print(f"TIMEOUT after {GROUP_TIMEOUT_SECONDS}s: {relative}", file=sys.stderr, flush=True)
            failures.append((relative, "timeout"))
            continue
        if result != 0:
            failures.append((relative, result))

    if failures:
        print("Failed test groups:", file=sys.stderr)
        for relative, result in failures:
            print(f"- {relative}: {result}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
