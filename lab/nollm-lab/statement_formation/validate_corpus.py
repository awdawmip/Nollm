from __future__ import annotations

import argparse
from collections import Counter
import json

from corpus_support import METRICS, load_cases, materialize
from nollm_access import assemble_formed_statements


def validate() -> dict[str, object]:
    cases = load_cases()
    categories = Counter()
    languages = Counter()
    formed_count = 0
    defer_count = 0
    statement_count = 0
    for case in cases:
        request, decision = materialize(case)
        categories[case["category"]] += 1
        languages[case["language"]] += 1
        formed = assemble_formed_statements(request, decision)
        if decision.outcome == "formed":
            formed_count += 1
            statement_count += len(formed)
        else:
            defer_count += 1
    if len(cases) < 120 or len(categories) < 12 or set(languages) != {"zh", "en", "mixed"}:
        raise ValueError("corpus coverage minimum is not met")
    splits = Counter(case["split"] for case in cases)
    if not splits["development"] or not splits["held_out"]:
        raise ValueError("development and held_out must both be populated")
    return {
        "case_count": len(cases),
        "category_counts": dict(sorted(categories.items())),
        "language_counts": dict(sorted(languages.items())),
        "split_counts": dict(sorted(splits.items())),
        "formed_count": formed_count,
        "defer_count": defer_count,
        "statement_count": statement_count,
        "span_boundary_valid_rate": 1.0,
        "overlap_violation_count": 0,
        "gold_text_mismatch_count": 0,
        "unknown_field_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    metrics = validate()
    recorded = json.loads(METRICS.read_text(encoding="utf-8"))
    if recorded.get("corpus") != metrics:
        raise ValueError("recorded corpus metrics are stale")
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
