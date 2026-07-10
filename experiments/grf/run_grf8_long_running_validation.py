from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from integrations.adapters.grf7r2_long_running import run_sustained_mutation

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--operations",type=int,default=1_000_000); parser.add_argument("--mutations",type=int,default=1_000); args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-long-") as temp: result=run_sustained_mutation(Path(temp), operation_count=args.operations, mutation_count=args.mutations)
    keys=("operation_count","operation_counts","throughput_operations_per_second","latency_by_operation","resource_backend","current_rss_bytes","peak_rss_bytes","rss_growth_bytes","disk_bytes","partition_count","identity_collision_count","orphan_count","replay_failure_count","fallback_failure_count","snapshot_replay_equals_final_state")
    print(json.dumps({key:result[key] for key in keys},sort_keys=True)); return 0 if result["identity_collision_count"] == result["orphan_count"] == result["replay_failure_count"] == result["fallback_failure_count"] == 0 else 1
if __name__ == "__main__": raise SystemExit(main())
