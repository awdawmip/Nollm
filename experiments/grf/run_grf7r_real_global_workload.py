from __future__ import annotations

import json
import os
from pathlib import Path

from nollm.grf.grf7r_real_global import run_real_global_workload


if __name__ == "__main__":
    source = Path(os.environ.get("NOLLM_GRF7_GLOBAL_ARTIFACT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7_scale_artifacts\global"))
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "real_global"
    print(json.dumps(run_real_global_workload(source, output), sort_keys=True, indent=2))
