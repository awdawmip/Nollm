from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_memory_adapter import (  # noqa: E402
    build_openclaw_memory_fixture_report,
    write_openclaw_memory_fixture_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse the deterministic OpenClaw memory fixture.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--workspace",
        default="../../examples/openclaw_memory_fixture",
        help="OpenClaw-style memory workspace path.",
    )
    parser.add_argument(
        "--output",
        default="../../out/nollm_runtime/openclaw_memory_fixture_index.json",
        help="Output report JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace = Path(args.workspace).resolve()
    output = Path(args.output).resolve()
    report = build_openclaw_memory_fixture_report(repo_root, workspace)
    write_openclaw_memory_fixture_report(report, output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
