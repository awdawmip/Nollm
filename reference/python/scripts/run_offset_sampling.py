from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.offset_sampling import offset_sampling_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal G4 offset sampling metrics.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--profile", action="append", dest="profiles", help="Profile id to include. Repeatable.")
    parser.add_argument("--max-step", type=int, default=8, help="Maximum positive step depth.")
    parser.add_argument("--seed", type=int, default=20260616, help="Seed for pseudo-random offset samples.")
    parser.add_argument("--random-count", type=int, default=32, help="Pseudo-random sample count.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to <repo-root>/out/nollm_runtime/offset_sampling_report.json.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "offset_sampling_report.json"
    )
    report = offset_sampling_report(
        profile_ids=args.profiles,
        max_step=args.max_step,
        seed=args.seed,
        random_count=args.random_count,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "wrote offset sampling report "
        f"path={output} profiles={len(report['profiles'])} max_step={args.max_step} "
        f"random_count={args.random_count} seed={args.seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
