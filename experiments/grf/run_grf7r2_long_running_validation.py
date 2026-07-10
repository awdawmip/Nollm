from __future__ import annotations

import json
import os
from pathlib import Path

from integrations.adapters.grf7r2_long_running import run_sustained_mutation


if __name__ == "__main__":
    root = Path(os.environ.get("NOLLM_GRF7R2_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7r2_external_evidence_20260710")) / "long_running"
    print(json.dumps(run_sustained_mutation(root), sort_keys=True, indent=2))
