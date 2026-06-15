from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_golden_regression import run_golden_regression, write_golden_regression_result  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal golden Dream Geometry report regression.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--update", action="store_true", help="Refresh golden snapshots.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/golden_regression_report.json",
        help="Output regression result JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    result = run_golden_regression(repo_root, update=args.update)
    write_golden_regression_result(result, output)
    print(
        "wrote dream golden regression report "
        f"path={output} ok={result['ok']} update={result['update']} failed={result['failed_report_count']}"
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
