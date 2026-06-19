from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.engineering_rc_final_smoke import run_final_smoke, write_final_smoke_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Engineering Gravity RC final smoke gate.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--report",
        default=None,
        help="Report JSON path. Defaults to <repo-root>/out/nollm_runtime/engineering_rc_final_smoke_report.json.",
    )
    parser.add_argument("--no-archive-build", action="store_true", help="Verify an existing archive without rebuilding it.")
    parser.add_argument("--verbose", action="store_true", help="Include stdout/stderr tails for successful checks.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    report_path = (
        Path(args.report).resolve()
        if args.report
        else repo_root / "out" / "nollm_runtime" / "engineering_rc_final_smoke_report.json"
    )
    report = run_final_smoke(repo_root, archive_build=not args.no_archive_build, verbose=args.verbose)
    write_final_smoke_report(report, report_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
