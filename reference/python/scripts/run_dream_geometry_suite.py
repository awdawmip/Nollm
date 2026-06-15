from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_suite import run_dream_geometry_suite  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal Dream Geometry suite.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/dream_suite_report.json",
        help="Output suite report JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    report = run_dream_geometry_suite(repo_root, output)
    component_count = len(report["components"])  # type: ignore[arg-type]
    print(f"wrote dream geometry suite report path={output} ok={report['ok']} components={component_count}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
