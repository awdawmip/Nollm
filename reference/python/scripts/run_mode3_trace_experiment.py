from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.mode3_trace_experiment import (  # noqa: E402
    build_mode3_trace,
    mode3_trace_fixture_from_record,
    mode3_trace_result_to_record,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal G7 Mode 3 free-drift trace experiment.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--fixture", default=None, help="Input fixture JSON path.")
    parser.add_argument("--max-items", type=int, default=None, help="Optional positive trace truncation count.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to <repo-root>/out/nollm_runtime/mode3_trace_experiment_report.json.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    fixture_path = (
        Path(args.fixture).resolve()
        if args.fixture is not None
        else repo_root / "examples" / "openclaw_dream" / "mode3_trace_fixture.json"
    )
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "mode3_trace_experiment_report.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    well, candidates = mode3_trace_fixture_from_record(fixture)
    result = build_mode3_trace(well, candidates, max_items=args.max_items)
    report = mode3_trace_result_to_record(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote mode3 trace experiment report path={output} items={report['trace_item_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
