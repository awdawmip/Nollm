from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

sys.dont_write_bytecode = True


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
