from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_cortex_recall import run_demo_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a deterministic OCP6R dream-cortex recall demo report.")
    parser.add_argument("--repo-root", default="../..")
    parser.add_argument("--workspace", default="examples/openclaw_dream_cortex_fixture")
    parser.add_argument("--dreamer-output", default="examples/openclaw_dream_cortex_fixture/dreamer_output.json")
    parser.add_argument("--out", default="out/nollm_runtime/dream_cortex_demo")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    report = run_demo_report(
        _resolve_repo_path(repo_root, args.workspace),
        _resolve_repo_path(repo_root, args.dreamer_output),
        _resolve_repo_path(repo_root, args.out),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def _resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    cwd_path = path.resolve()
    if cwd_path.exists():
        return cwd_path
    return (repo_root / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())

