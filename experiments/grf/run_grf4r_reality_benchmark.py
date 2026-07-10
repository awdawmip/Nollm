from __future__ import annotations

import gc
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.production_reality_benchmark import run_reality_benchmark  # noqa: E402


def main() -> int:
    metrics = []
    for size in (100_000, 500_000, 1_000_000):
        metrics.append(run_reality_benchmark(size).to_mapping())
        gc.collect()
    relation_growth = tuple(f"{right['relation_storage_size']}/{left['relation_storage_size']}" for left, right in zip(metrics, metrics[1:]))
    kernel_stable = len({item["kernel_storage_size"] for item in metrics}) == 1
    print(json.dumps({"gate": "GRF4R_C", "measurement": "actual Core calls, canonical bytes, and perf_counter_ns", "metrics": metrics, "relation_growth": relation_growth, "kernel_storage_independent": kernel_stable}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
