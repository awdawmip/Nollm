from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.reverse_cover import ReverseCoverCase, reverse_cover_cases_for_pack, reverse_cover_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal G5 reverse-cover MILP metrics.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--profile", action="append", dest="profiles", help="Profile id to include. Repeatable.")
    parser.add_argument("--step", action="append", type=int, dest="steps", help="Step to include. Repeatable.")
    parser.add_argument(
        "--case-pack",
        choices=("smoke", "nontrivial", "all"),
        default="smoke",
        help="Deterministic reverse-cover case pack.",
    )
    parser.add_argument("--target-radius", type=int, default=1, help="Axial target-cluster radius.")
    parser.add_argument("--time-limit-seconds", type=float, default=5.0, help="SciPy MILP/LP time limit.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to <repo-root>/out/nollm_runtime/reverse_cover_report.json.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "reverse_cover_report.json"
    )
    cases = (
        reverse_cover_cases_for_pack(args.case_pack)
        if args.steps is None
        else [
            ReverseCoverCase(
                step=step,
                target_radius=args.target_radius,
                case_pack=args.case_pack,
            )
            for step in args.steps
        ]
    )
    report = reverse_cover_report(
        profile_ids=args.profiles,
        cases=cases,
        time_limit_seconds=args.time_limit_seconds,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote reverse-cover report path={output} profiles={len(report['profiles'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
