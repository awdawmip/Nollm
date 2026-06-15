from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_regression import build_dream_regression_report, write_dream_regression_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal adversarial Dream Geometry regressions.")
    parser.add_argument(
        "--output",
        default="examples/openclaw_dream/regression_report.json",
        help="Output regression report JSON path.",
    )
    args = parser.parse_args(argv)

    output = Path(args.output).resolve()
    report = build_dream_regression_report()
    write_dream_regression_report(report, output)
    print(
        "wrote dream regression report "
        f"path={output} cases={report['case_count']} ok={report['summary']['ok']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
