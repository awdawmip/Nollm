from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_corpus_dry_run import run_real_corpus_dry_run, write_real_corpus_dry_run_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal real-corpus Dream Geometry dry-run.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/real_corpus_dry_run_report.json",
        help="Output dry-run report JSON path.",
    )
    parser.add_argument("--max-files", type=int, default=8, help="Maximum corpus files to process.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    report = run_real_corpus_dry_run(repo_root, max_files=args.max_files)
    write_real_corpus_dry_run_report(report, output)
    print(
        "wrote real corpus dream dry-run report "
        f"path={output} ok={report['ok']} files={report['file_count']} shards={report['shard_count']}"
    )
    return 0 if report["ok"] and report["failed_invariant_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
