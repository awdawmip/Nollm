from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.engineering_rc_archive import (  # noqa: E402
    build_engineering_rc_export_archive,
    verify_engineering_rc_export_archive,
    write_engineering_rc_archive_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify deterministic Engineering Gravity RC export archive.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--output", default=None, help="Output zip path.")
    parser.add_argument("--verify", default=None, help="Verify an existing zip path.")
    parser.add_argument("--report", default=None, help="Optional deterministic JSON report path.")
    parser.add_argument(
        "--allow-non-runtime-output",
        action="store_true",
        help="Allow --output outside out/nollm_runtime/ for tests or explicit operator use.",
    )
    args = parser.parse_args(argv)

    if bool(args.output) == bool(args.verify):
        parser.error("provide exactly one of --output or --verify")

    repo_root = Path(args.repo_root)
    if args.output:
        report = build_engineering_rc_export_archive(
            repo_root,
            Path(args.output),
            allow_non_runtime_output=args.allow_non_runtime_output,
        )
    else:
        report = verify_engineering_rc_export_archive(repo_root, Path(args.verify))

    if args.report:
        write_engineering_rc_archive_report(report, Path(args.report))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
