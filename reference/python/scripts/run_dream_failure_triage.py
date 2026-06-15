from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_triage import (  # noqa: E402
    build_dream_triage_report,
    write_dream_triage_json,
    write_dream_triage_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render internal Dream Geometry failure triage.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/dream_failure_triage.md",
        help="Output Markdown path.",
    )
    parser.add_argument("--json-output", help="Optional structured JSON output path.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    report = build_dream_triage_report(repo_root)
    write_dream_triage_report(report, output)
    if args.json_output:
        write_dream_triage_json(report, Path(args.json_output).resolve())
    print(
        "wrote dream failure triage "
        f"path={output} ok={report['ok']} reports={report['summary']['report_count']}"
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
