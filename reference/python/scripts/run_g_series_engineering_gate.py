from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.g_series_engineering_closure import (  # noqa: E402
    build_g_series_engineering_closure_report,
    write_closure_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal G-series engineering closure gate.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to <repo-root>/out/nollm_runtime/g_series_engineering_closure_report.json.",
    )
    parser.add_argument("--no-generate", action="store_true", help="Do not refresh prerequisite runtime reports.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "g_series_engineering_closure_report.json"
    )
    report = build_g_series_engineering_closure_report(repo_root, generate_reports=not args.no_generate)
    write_closure_report(report, output)
    print(f"wrote g-series engineering closure report path={output} ok={report['ok']}")
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
