from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from nollm.cli import main
from subprocess_harness import RunResult


def run_cli(args: list[str], *, cwd: Path) -> RunResult:
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_cwd = Path.cwd()
    try:
        os.chdir(cwd)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = main(args)
    finally:
        os.chdir(old_cwd)

    return RunResult([sys.executable, "-m", "nollm.cli", *args], int(returncode), stdout.getvalue(), stderr.getvalue())
