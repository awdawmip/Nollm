from __future__ import annotations

import json
import os
from pathlib import Path
import platform

from nollm.grf.resource_sampler import sample_process_resources


if __name__ == "__main__":
    if platform.system() != "Windows":
        raise SystemExit("GRF7R Windows resource validation requires Windows")
    output = Path(os.environ.get("NOLLM_GRF7R_OUTPUT_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710\grf7r_closure")) / "platform" / "windows_resource_sample.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    sample = sample_process_resources()
    result = {**sample.to_mapping(), "platform": platform.platform(), "cross_platform_portability": "not_validated_in_this_stage"}
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True, indent=2))
