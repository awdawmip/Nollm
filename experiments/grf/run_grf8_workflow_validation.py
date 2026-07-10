from __future__ import annotations
import json
from nollm.grf.grf8_quality_benchmark import benchmark
from nollm.grf.grf8_quality_dataset import build_quality_dataset

def main() -> int:
    evidence, queries = build_quality_dataset(5_000, 600)
    groups = ("coding", "research", "document", "conversation")
    results = {name: benchmark(evidence, tuple(item for item in queries if item.category in ({"coding","project"} if name == "coding" else {name}))).__dict__ for name in groups}
    payload = {"workflow_query_count": len(queries), "workflows": results, "source_fallback": all(item["source_faithfulness"] == 1.0 for item in results.values())}
    print(json.dumps(payload, sort_keys=True)); return 0 if payload["source_fallback"] else 1
if __name__ == "__main__": raise SystemExit(main())
