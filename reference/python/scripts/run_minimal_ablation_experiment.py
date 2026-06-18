from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.minimal_ablation_experiment import (  # noqa: E402
    ablation_fixture_from_record,
    build_minimal_ablation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal G8 minimal ablation experiment.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument("--fixture", default=None, help="Input fixture JSON path.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to <repo-root>/out/nollm_runtime/minimal_ablation_experiment_report.json.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    fixture_path = (
        Path(args.fixture).resolve()
        if args.fixture is not None
        else repo_root / "examples" / "openclaw_dream" / "minimal_ablation_fixture.json"
    )
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "minimal_ablation_experiment_report.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    questions = ablation_fixture_from_record(fixture)
    report = build_minimal_ablation_report(questions)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "wrote minimal ablation experiment report "
        f"path={output} conditions={report['condition_count']} questions={report['question_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
