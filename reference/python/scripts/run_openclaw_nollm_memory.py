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
from nollm.dream_cortex_recall import (  # noqa: E402
    ingest_dreamer_fixture,
    nollm_compose_digest,
    nollm_drift,
    nollm_focus,
    nollm_orient,
    nollm_read,
    nollm_surface,
    run_demo_report,
    source_snapshot,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the experimental OpenClaw-Nollm memory sidecar.")
    parser.add_argument("--repo-root", default="../..", help="Repository root path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in (
        "index",
        "search",
        "recall",
        "get",
        "write-candidate",
        "commit-candidate",
        "status",
        "snapshot",
        "dream-ingest",
        "orient",
        "surface",
        "focus",
        "drift",
        "read",
        "compose-digest",
        "dream-demo",
    ):
        sub = subparsers.add_parser(name)
        sub.add_argument("--workspace", default="examples/openclaw_memory_fixture")
        sub.add_argument("--out", default="out/nollm_runtime/openclaw_sidecar")
        if name in {"dream-ingest", "dream-demo"}:
            sub.add_argument("--dreamer-output", default="examples/openclaw_dream_cortex_fixture/dreamer_output.json")
        if name in {"search", "recall"}:
            sub.add_argument("--query", required=True)
            sub.add_argument("--limit", type=int, default=5)
        if name in {"orient", "focus", "drift", "compose-digest"}:
            sub.add_argument("--query", required=True)
        if name == "orient":
            sub.add_argument("--limit", type=int, default=3)
        if name in {"surface", "focus"}:
            sub.add_argument("--surface-id", required=True)
        if name in {"drift", "read"}:
            sub.add_argument("--shard-id", required=True)
        if name == "focus":
            sub.add_argument("--sufficient-scale", type=int, default=2)
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
    elif args.command == "snapshot":
        report = source_snapshot(workspace)
    elif args.command == "dream-ingest":
        report = ingest_dreamer_fixture(workspace, _resolve_repo_path(repo_root, args.dreamer_output), out_dir)
    elif args.command == "orient":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_orient(out_dir, query=args.query, limit=args.limit)
    elif args.command == "surface":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_surface(out_dir, surface_id=args.surface_id)
    elif args.command == "focus":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_focus(out_dir, query=args.query, surface_id=args.surface_id, sufficient_scale=args.sufficient_scale)
    elif args.command == "drift":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_drift(out_dir, shard_id=args.shard_id, query=args.query)
    elif args.command == "read":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_read(out_dir, shard_id=args.shard_id)
    elif args.command == "compose-digest":
        _ensure_dream_field(workspace, out_dir, repo_root)
        report = nollm_compose_digest(out_dir, query=args.query)
    elif args.command == "dream-demo":
        report = run_demo_report(workspace, _resolve_repo_path(repo_root, args.dreamer_output), out_dir)
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


def _ensure_dream_field(workspace: Path, out_dir: Path, repo_root: Path) -> None:
    field = out_dir / "dream_field.json"
    if field.exists():
        return
    fixture = repo_root / "examples/openclaw_dream_cortex_fixture/dreamer_output.json"
    ingest_dreamer_fixture(workspace, fixture, out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
