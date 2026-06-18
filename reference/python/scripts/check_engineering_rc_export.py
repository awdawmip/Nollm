from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.engineering_rc_export import (  # noqa: E402
    build_engineering_rc_export_check,
    engineering_rc_export_check_json,
    write_engineering_rc_artifact_hash_manifest,
    write_engineering_rc_export_check,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Engineering Gravity RC release/export docs.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    parser.add_argument("--write-hashes", action="store_true", help="Rewrite the deterministic RC artifact hash manifest.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    if args.write_hashes:
        write_engineering_rc_artifact_hash_manifest(repo_root)
    report = build_engineering_rc_export_check(repo_root)
    if args.output:
        write_engineering_rc_export_check(report, Path(args.output))
    print(engineering_rc_export_check_json(report), end="")
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
