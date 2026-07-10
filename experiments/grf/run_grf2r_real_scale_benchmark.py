from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.real_scale_benchmark import inject_failure_boundaries, run_incremental_equivalence, run_real_scale_benchmark  # noqa: E402


def main() -> int:
    metrics = [run_real_scale_benchmark(size).to_mapping() for size in (10_000, 100_000, 1_000_000)]
    payload = {
        "gate": "GRF2R",
        "measurement_method": "actual in-memory objects and materialized local explicit graph edges",
        "metrics": metrics,
        "storage_growth_ratios": {
            "relation": tuple(f"{right['relation_storage_size']}/{left['relation_storage_size']}" for left, right in zip(metrics, metrics[1:])),
            "explicit_graph": tuple(f"{right['explicit_graph_storage_size']}/{left['explicit_graph_storage_size']}" for left, right in zip(metrics, metrics[1:])),
            "kernel": tuple(f"{right['kernel_storage_size']}/{left['kernel_storage_size']}" for left, right in zip(metrics, metrics[1:])),
        },
        "incremental_equivalence": run_incremental_equivalence().to_mapping(),
        "failure_boundaries": inject_failure_boundaries(),
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
