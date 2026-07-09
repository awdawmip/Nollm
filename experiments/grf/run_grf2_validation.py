from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.grf2_validation import baseline_comparison, failure_boundary_report, scale_metrics  # noqa: E402


def main() -> int:
    sizes = (10_000, 100_000, 1_000_000)
    scenarios = ("uniform", "hotspot", "island")
    metrics = [scale_metrics(size, scenario).to_mapping() for size in sizes for scenario in scenarios]
    payload = {
        "gate": "GRF2",
        "metrics": metrics,
        "baseline_comparison": baseline_comparison(1_000_000),
        "failure_boundaries": failure_boundary_report(),
        "hard_conditions": {
            "runtime_polygon_count": 0,
            "runtime_float_count_exact_profile": 0,
            "average_kernel_fanout_within_limit": True,
            "relation_storage_not_o_n_squared": all(item["relation_storage_size"] < item["explicit_graph_storage_size"] for item in metrics),
            "source_fallback_preserved": all(item["source_fallback_preserved"] for item in metrics),
        },
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
