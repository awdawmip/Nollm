from __future__ import annotations

import json
import os
from pathlib import Path

from integrations.adapters.grf7r_long_running import run_long_running


if __name__ == "__main__":
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "long_running"
    print(json.dumps(run_long_running(output), sort_keys=True, indent=2))
