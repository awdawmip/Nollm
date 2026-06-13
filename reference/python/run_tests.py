from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    command = [sys.executable, "-m", "pytest", "-q"]
    completed = subprocess.run(command, cwd=Path(__file__).resolve().parent, env=env)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
