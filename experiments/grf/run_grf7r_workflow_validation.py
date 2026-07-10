from __future__ import annotations

import json
import os
from pathlib import Path

from nollm.grf.grf7r_workflow import run_workflow_benchmark


if __name__ == "__main__":
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "workflow"
    print(json.dumps(run_workflow_benchmark(output), sort_keys=True, indent=2))
