from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.local_gate import build_local_gate_report, write_local_gate_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal Nollm local gate.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/local_gate_report.json",
        help="Output local gate JSON path.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--include-pytest", action="store_true", help="Run python run_tests.py.")
    mode.add_argument("--skip-pytest", action="store_true", help="Skip pytest and record included=false.")
    parser.add_argument("--pytest-timeout", type=int, default=120, help="Timeout for run_tests.py when included.")
    args = parser.parse_args(argv)

    include_pytest = bool(args.include_pytest)
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    report = build_local_gate_report(
        repo_root,
        include_pytest=include_pytest,
        pytest_timeout_seconds=args.pytest_timeout,
    )
    write_local_gate_report(report, output)
    print(
        "wrote nollm local gate report "
        f"path={output} ok={report['ok']} pytest_included={report['components']['pytest']['included']}"
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
