from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


POLL_INTERVAL_SECONDS = 0.1
KILL_WAIT_SECONDS = 5
OUTPUT_TAIL_CHARS = 12000


@dataclass(frozen=True)
class RunResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_subprocess(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 20,
    label: str | None = None,
    request_path: Path | None = None,
    input_text: str | None = None,
) -> RunResult:
    if label is None and request_path is not None:
        label = request_path.as_posix()
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    with tempfile.TemporaryDirectory() as tmp:
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE if input_text is not None else None,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=os.name != "nt",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            if input_text is not None:
                assert process.stdin is not None
                process.stdin.write(input_text)
                process.stdin.close()
            timed_out = wait_with_deadline(process, timeout_seconds)

        stdout = read_tail(stdout_path)
        stderr = read_tail(stderr_path)
        if timed_out:
            return RunResult(command, -1, stdout, stderr, timed_out=True)
        return RunResult(command, int(process.returncode), stdout, stderr)


def wait_with_deadline(process: subprocess.Popen[str], timeout_seconds: int) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while process.poll() is None:
        if time.monotonic() >= deadline:
            terminate_process_tree(process)
            wait_for_exit(process)
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return False


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
    deadline = time.monotonic() + KILL_WAIT_SECONDS
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)


def read_tail(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= OUTPUT_TAIL_CHARS:
        return text
    return f"... output truncated to last {OUTPUT_TAIL_CHARS} chars ...\n{text[-OUTPUT_TAIL_CHARS:]}"


def subprocess_failure_message(result: RunResult, cwd: Path, label: str | None = None) -> str:
    message = [
        f"command: {' '.join(str(part) for part in result.args)}",
        f"cwd: {cwd}",
    ]
    if label:
        message.append(f"label: {label}")
    if result.timed_out:
        message.append("exit_code: timeout")
    else:
        message.append(f"exit_code: {result.returncode}")
    message.append(f"stdout: {result.stdout}")
    message.append(f"stderr: {result.stderr}")
    return "\n".join(message)
