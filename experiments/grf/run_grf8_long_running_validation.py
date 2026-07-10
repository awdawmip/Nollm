from __future__ import annotations
import json, tempfile
from pathlib import Path
from integrations.adapters.grf7r2_long_running import run_sustained_mutation

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-long-") as temp: result=run_sustained_mutation(Path(temp), operation_count=10_000, mutation_count=10)
    print(json.dumps({"operation_count":result["operation_count"],"replay":result["snapshot_replay_equals_final_state"],"orphan_count":result["orphan_count"]},sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
