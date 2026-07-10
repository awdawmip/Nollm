from __future__ import annotations

import json
from nollm.grf.grf8_quality_benchmark import benchmark, compare_baselines
from nollm.grf.grf8_quality_dataset import build_quality_dataset, dataset_digest


def main() -> int:
    evidence, queries = build_quality_dataset()
    metrics = benchmark(evidence, queries)
    baselines = {name: metric.__dict__ for name, metric in compare_baselines(evidence, queries).items()}
    print(json.dumps({"evidence_count": len(evidence), "query_count": len(queries), "dataset_digest": dataset_digest(evidence, queries), "baselines": baselines, **metrics.__dict__}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
