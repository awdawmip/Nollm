"""Compare fixed geometric budgets on an explicit field; this is not a Host task."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True, help="frozen native field to read")
    parser.add_argument("--runtime", type=Path, help="optional installed scripts/runtime directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    sys.path[:0] = ([str(args.runtime)] if args.runtime else
                   [str(root / "packages/nollm-core/src"), str(root / "packages/nollm-access/src")])

    from nollm_access import AccessRecallRequest, AccessRuntime, FileHandleStore, FileStatementStore
    from nollm_core import CoreRuntime, GeometryAddress, RecallBudget

    entry = GeometryAddress("default_dream_v1", "default", 0, 0, 1)
    modes = {
        "mixed": ("coverage_down", "coverage_up", "lateral"),
        "lateral": ("lateral",),
        "vertical": ("coverage_down", "coverage_up"),
    }
    observations = []
    with CoreRuntime(args.field) as core, AccessRuntime(
        core, FileStatementStore(args.field), FileHandleStore(args.field)
    ) as access:
        for mode, beam in (("mixed", 16), ("lateral", 16), ("vertical", 16),
                           ("mixed", 64), ("vertical", 64)):
            budget = RecallBudget(2, beam, 2, 1, 0, 20)
            result = access.recall(AccessRecallRequest(
                "self-bootstrap-budget-comparison", (entry,),
                allowed_kernels=modes[mode], budget=budget))
            observations.append({
                "mode": mode, "budget": asdict(budget),
                "items": [{"id": item.statement_id, "via": item.path,
                           "score_q16": item.score_q16} for item in result.items],
                "budget_exhausted": result.budget_exhausted,
            })
    print(json.dumps({"field": str(args.field), "entry": [0, 0, 1],
                      "scope": "controlled geometry, not model quality",
                      "observations": observations}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
