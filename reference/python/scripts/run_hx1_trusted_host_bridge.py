from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[3]
PYTHON_ROOT = ROOT / "reference" / "python"
TEST_ROOT = PYTHON_ROOT / "tests"
sys.path.insert(0, str(PYTHON_ROOT))
sys.path.insert(0, str(TEST_ROOT))

from nollm.dream_geometry.host_execution import execute_host_plan, receipt_to_mapping  # noqa: E402
from test_hx1_trusted_host_bridge import hx1_fixture  # noqa: E402


def main() -> int:
    work_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="hx1_bridge_")) / "work"
    fixture = hx1_fixture(work_root)
    receipt = execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    print(json.dumps(receipt_to_mapping(receipt), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
