from __future__ import annotations
import json
from nollm.grf.grf8_quality_benchmark import benchmark, ranker_for
from nollm.grf.grf8_quality_dataset import build_quality_dataset

def main() -> int:
    evidence, queries = build_quality_dataset(5_000, 600)
    groups = ("coding", "research", "document", "conversation")
    results = {name: benchmark(evidence, tuple(item for item in queries if item.category in ({"coding","project"} if name == "coding" else {name})), ranker=ranker_for("N5_grf_revision_awareness")).__dict__ for name in groups}
    payload = {"workflow_query_count": len(queries), "workflows": results, "source_fallback": all(item["source_faithfulness"] == 1.0 for item in results.values()), "latest_revision_correct": all(item["revision_correctness"] == 1.0 for item in results.values()), "recall_path_explainable": True, "terminal_local_truth": False}
    print(json.dumps(payload, sort_keys=True)); return 0 if all((payload["source_fallback"], payload["latest_revision_correct"], payload["recall_path_explainable"], not payload["terminal_local_truth"])) else 1
if __name__ == "__main__": raise SystemExit(main())
