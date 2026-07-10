from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.grf7_cross_validation import run_grf7_cross_validation  # noqa: E402


def main() -> int:
    result = run_grf7_cross_validation().to_mapping()
    raw = ROOT / "experiments" / "grf" / "results" / "GRF7_CROSS_PARTITION_RECALL_RAW.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    raw.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
