from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "reference" / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "reference" / "python"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf4_host_validation import run_multi_host_conformance  # noqa: E402
from nollm.grf.production_validation import run_production_like_benchmark  # noqa: E402


def main() -> int:
    metrics = run_production_like_benchmark(1_000_001)
    with TemporaryDirectory(prefix="nollm_grf4_") as directory:
        hosts = run_multi_host_conformance(Path(directory))
    print(json.dumps({"gate": "GRF4", "production_metrics": metrics.to_mapping(), "multi_host": hosts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
