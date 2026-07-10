from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from integrations.adapters.grf7r2_long_running import run_sustained_mutation

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--operations",type=int,default=1_000_000); parser.add_argument("--mutations",type=int,default=1_000); args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-long-") as temp: result=run_sustained_mutation(Path(temp), operation_count=args.operations, mutation_count=args.mutations)
    print(json.dumps({"operation_count":result["operation_count"],"replay":result["snapshot_replay_equals_final_state"],"orphan_count":result["orphan_count"]},sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
