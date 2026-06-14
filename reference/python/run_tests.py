from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


GROUP_TIMEOUT_SECONDS = 90


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
        try:
            completed = subprocess.run(command, cwd=root, env=env, timeout=GROUP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT after {GROUP_TIMEOUT_SECONDS}s: {relative}", file=sys.stderr, flush=True)
            failures.append((relative, "timeout"))
            continue
        if completed.returncode != 0:
            failures.append((relative, completed.returncode))

    if failures:
        print("Failed test groups:", file=sys.stderr)
        for relative, result in failures:
            print(f"- {relative}: {result}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
