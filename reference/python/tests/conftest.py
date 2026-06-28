from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

sys.dont_write_bytecode = True
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import subprocess


def _run_command(
    command: list[str],
    *,
    cwd: str | Path,
    timeout: int = 60,
    input_data: str | bytes | None = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess with timeout; keeps subprocess.run out of test files."""
    text = not isinstance(input_data, bytes)
    stdin_pipe = subprocess.PIPE if input_data is not None else None
    with subprocess.Popen(
        command,
        stdin=stdin_pipe,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        cwd=cwd,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(input=input_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                stdout, stderr = ("", "") if text else (b"", b"")
            raise
    return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)



def pytest_sessionfinish(session, exitstatus) -> None:
    cleanup_generated_python_artifacts()


def cleanup_generated_python_artifacts() -> None:
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
    for path in ROOT.rglob(".pytest_cache"):
        if path.is_dir():
            shutil.rmtree(path)
    for path in ROOT.rglob("*.pyc"):
        if path.is_file():
            path.unlink()
