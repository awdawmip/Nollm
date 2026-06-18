from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True

from nollm.pytest_env import isolated_pytest_env  # noqa: E402

os.environ.update(isolated_pytest_env(os.environ))

from pytest import main as pytest_main  # noqa: E402


def main() -> int:
    return int(pytest_main(["-q"]))



if __name__ == "__main__":
    raise SystemExit(main())
