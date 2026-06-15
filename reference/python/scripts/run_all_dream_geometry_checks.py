from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_checks_manifest import (  # noqa: E402
    build_all_dream_checks_manifest,
    write_all_dream_checks_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run internal Dream Geometry manifest checks.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    parser.add_argument(
        "--output",
        default="../../examples/openclaw_dream/all_dream_checks_manifest.json",
        help="Output manifest JSON path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    manifest = build_all_dream_checks_manifest(repo_root)
    write_all_dream_checks_manifest(manifest, output)
    print(
        "wrote all dream checks manifest "
        f"path={output} ok={manifest['ok']} components={len(manifest['components'])}"
    )
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
