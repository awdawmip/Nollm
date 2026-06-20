from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_active_memory_config import build_ocp6r_cortex_active_memory_patch  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an OCP6R Nollm Cortex Active Memory config patch.")
    parser.add_argument("--repo-root", default="../..")
    parser.add_argument("--workspace", default="examples/openclaw_dream_cortex_fixture")
    parser.add_argument("--config-before", default="")
    parser.add_argument("--agent-id", default="ocp6r-nollm-cortex")
    parser.add_argument("--model", default="kimi/kimi-for-coding")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace = _resolve_repo_path(repo_root, args.workspace)
    config_before = {}
    if args.config_before:
        config_before = json.loads(Path(args.config_before).read_text(encoding="utf-8"))
    patch = build_ocp6r_cortex_active_memory_patch(
        config_before=config_before,
        repo_root=repo_root,
        workspace_root=workspace,
        agent_id=args.agent_id,
        model=args.model,
    )
    print(json.dumps(patch, indent=2, sort_keys=True))
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

