from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(source: Path) -> dict[str, object]:
    document = json.loads(source.read_text(encoding="utf-8"))
    if document.get("schema_version") != "nollm_dense_single_entry_recall_validation_v1":
        raise ValueError("unsupported dense Recall evidence")
    observation = document["natural_multi_entry_observation"]
    checks = {
        "minimum_is_zero": observation["minimum_required"] == 0,
        "no_combined_request": observation["combined_request_used"] is False,
        "no_persisted_mapping": observation["persisted_fact_to_entries"] is False,
        "each_run_is_single_entry": all(
            not item["available"] or item["request_entry_count"] == 1
            for item in observation["runs"]
        ),
    }
    return {
        "schema_version": "nollm_natural_multi_entry_observation_v1",
        "source_schema_version": document["schema_version"],
        "observation": observation,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
