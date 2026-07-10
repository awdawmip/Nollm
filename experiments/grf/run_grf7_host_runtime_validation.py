from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.grf.run_grf7r_runtime_semantics import run  # noqa: E402


def main() -> int:
    runtime_root = ROOT / "experiments" / "grf" / "results" / "grf7_runtime_artifacts"
    result = run(runtime_root)
    raw = ROOT / "experiments" / "grf" / "results" / "GRF7_HOST_RUNTIME_RAW.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    raw.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
