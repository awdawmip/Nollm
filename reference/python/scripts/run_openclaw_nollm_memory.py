from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_memory_adapter import (  # noqa: E402
    build_sidecar_store,
    commit_candidate,
    get_sidecar_item,
    recall_sidecar,
    search_sidecar,
    sidecar_status,
    write_candidate,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the experimental OpenClaw-Nollm memory sidecar.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("index", "search", "recall", "get", "write-candidate", "commit-candidate", "status"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--workspace", default="examples/openclaw_memory_fixture")
        sub.add_argument("--out", default="out/nollm_runtime/openclaw_sidecar")
        if name in {"search", "recall"}:
            sub.add_argument("--query", required=True)
            sub.add_argument("--limit", type=int, default=5)
        if name == "get":
            sub.add_argument("--id", required=True)
        if name == "write-candidate":
            sub.add_argument("--text", required=True)
            sub.add_argument("--source", required=True)
            sub.add_argument("--why", default="pending explicit review before durable promotion")
        if name == "commit-candidate":
            sub.add_argument("--candidate-id", required=True)
            sub.add_argument("--explicit-confirmation", action="store_true")
            sub.add_argument("--target", choices=["durable", "daily"], required=True)
            sub.add_argument("--reason", required=True)
            sub.add_argument("--source", required=True)

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    workspace = _resolve_repo_path(repo_root, args.workspace)
    out_dir = _resolve_repo_path(repo_root, args.out)

    if args.command == "index":
        report = build_sidecar_store(repo_root, workspace, out_dir)
    elif args.command == "search":
        report = search_sidecar(repo_root, workspace, out_dir, query=args.query, limit=args.limit)
    elif args.command == "recall":
        report = recall_sidecar(repo_root, workspace, out_dir, query=args.query, limit=args.limit)
    elif args.command == "get":
        report = get_sidecar_item(repo_root, workspace, out_dir, args.id)
    elif args.command == "write-candidate":
        report = write_candidate(repo_root, workspace, out_dir, text=args.text, source=args.source, why=args.why)
    elif args.command == "commit-candidate":
        report = commit_candidate(
            repo_root,
            workspace,
            out_dir,
            candidate_id=args.candidate_id,
            explicit_confirmation=args.explicit_confirmation,
            target=args.target,
            reason=args.reason,
            source=args.source,
        )
    elif args.command == "status":
        report = sidecar_status(repo_root, workspace, out_dir)
    else:
        raise AssertionError("unreachable command")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") is True else 1


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
