from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_pipeline import (  # noqa: E402
    build_dream_geometry_run_report,
    load_dream_geometry_fixture,
    write_dream_geometry_run_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal OpenClaw dream geometry fixture.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/dream_run_report.json",
        help="Output report JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    shards, placements = load_dream_geometry_fixture(repo_root)
    report = build_dream_geometry_run_report(shards, placements)
    write_dream_geometry_run_report(report, output)
    print(
        "wrote dream geometry report "
        f"path={output} shards={len(report['shards'])} placements={len(report['ranked_placements'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
