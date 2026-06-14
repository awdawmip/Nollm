from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

from pytest import main as pytest_main  # noqa: E402


def main() -> int:
    return int(pytest_main(["-q"]))



if __name__ == "__main__":
    raise SystemExit(main())
