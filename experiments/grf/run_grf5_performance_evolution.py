from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.performance_evolution import run_recall_index_benchmark  # noqa: E402


def main() -> int:
    metrics = run_recall_index_benchmark()
    print(json.dumps(metrics.__dict__, sort_keys=True, indent=2))
    return 0 if metrics.equivalent else 1


if __name__ == "__main__":
    raise SystemExit(main())
