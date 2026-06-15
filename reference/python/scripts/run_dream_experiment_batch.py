from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_experiment_batch import (  # noqa: E402
    build_batch_experiment_report,
    load_batch_fixture,
    write_batch_experiment_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal Dream Geometry batch fixtures.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="examples/openclaw_dream/batch_report.json",
        help="Output batch report JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    fixtures = load_batch_fixture(repo_root)
    report = build_batch_experiment_report(fixtures)
    write_batch_experiment_report(report, output)
    print(
        "wrote dream experiment batch report "
        f"path={output} fixtures={report['fixture_count']} invariants_ok={report['invariants']['ok']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
