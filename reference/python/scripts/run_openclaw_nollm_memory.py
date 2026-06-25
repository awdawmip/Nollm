from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_memory_adapter import (  # noqa: E402
    build_sidecar_store,
    get_native_companion_memory,
    get_sidecar_item,
    recall_native_companion_memory,
    recall_sidecar,
    remember_native_companion_memory,
    search_sidecar,
    sidecar_status,
)
from nollm.dream_cortex_recall import (  # noqa: E402
    ingest_dreamer_fixture,
    nollm_compose_digest,
    nollm_drift,
    nollm_field_overview,
    nollm_focus,
    nollm_open_well,
    nollm_read,
    nollm_recall_trace,
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
        "status",
        "snapshot",
        "dream-ingest",
        "field-overview",
        "open-well",
        "surface",
        "focus",
        "drift",
        "read",
        "recall-trace",
        "dream-demo",
        "native-remember",
        "native-recall",
        "native-get",
    ):
        sub = subparsers.add_parser(name)
        sub.add_argument("--workspace", default="examples/openclaw_memory_fixture")
        sub.add_argument("--out", default="out/nollm_runtime/openclaw_sidecar")
        if name in {"dream-ingest", "dream-demo"}:
            sub.add_argument("--dreamer-output", default="examples/openclaw_dream_cortex_fixture/dreamer_output.json")
        if name in {"search", "recall"}:
            sub.add_argument("--query", required=True)
            sub.add_argument("--limit", type=int, default=5)
        if name == "field-overview":
            sub.add_argument("--field-id", default=None)
            sub.add_argument("--limit", type=int, default=20)
        if name == "open-well":
            sub.add_argument("--entry-shard-id", required=True)
            sub.add_argument("--entry-task", required=True)
            sub.add_argument("--anchor-vector", required=True, help="JSON object of non-negative Cortex-proposed anchor weights.")
            sub.add_argument("--revision-id", default=None)
            sub.add_argument("--ttl-seconds", type=int, default=3600)
        if name == "surface":
            sub.add_argument("--well-id", required=True)
            sub.add_argument("--center-shard-id", required=True)
            sub.add_argument("--radius", type=int, default=1)
            sub.add_argument("--target-scale", default=None)
        if name == "focus":
            sub.add_argument("--well-id", required=True)
            sub.add_argument("--target-shard-id", required=True)
            sub.add_argument("--target-scale", default=None)
        if name == "drift":
            sub.add_argument("--well-id", required=True)
            sub.add_argument("--current-shard-id", required=True)
            sub.add_argument("--chosen-shard-id", default=None)
            sub.add_argument("--radius", type=int, default=1)
        if name == "read":
            sub.add_argument("--well-id", required=True)
            sub.add_argument("--shard-id", required=True)
        if name == "recall-trace":
            sub.add_argument("--well-id", required=True)
            sub.add_argument("--path", required=True, help="JSON array of Cortex-selected shard ids.")
        if name == "get":
            sub.add_argument("--id", required=True)
        if name == "native-remember":
            sub.add_argument("--memory", required=True)
            sub.add_argument("--kind", default="note")
            sub.add_argument("--scope", default="user")
            sub.add_argument("--source", default="explicit_user")
        if name == "native-recall":
            sub.add_argument("--query", required=True)
            sub.add_argument("--limit", type=int, default=5)
            sub.add_argument("--scope", default=None)
        if name == "native-get":
            sub.add_argument("--id", required=True)

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
    elif args.command == "status":
        report = sidecar_status(repo_root, workspace, out_dir)
    elif args.command == "native-remember":
        report = remember_native_companion_memory(
            repo_root,
            workspace,
            out_dir,
            memory=args.memory,
            kind=args.kind,
            scope=args.scope,
            source=args.source,
        )
    elif args.command == "native-recall":
        report = recall_native_companion_memory(
            repo_root,
            workspace,
            out_dir,
            query=args.query,
            limit=args.limit,
            scope=args.scope,
        )
    elif args.command == "native-get":
        report = get_native_companion_memory(repo_root, workspace, out_dir, args.id)
    elif args.command == "snapshot":
        report = source_snapshot(workspace)
    elif args.command == "dream-ingest":
        report = ingest_dreamer_fixture(workspace, _resolve_repo_path(repo_root, args.dreamer_output), out_dir)
    elif args.command == "field-overview":
        report = nollm_field_overview(out_dir, field_id=args.field_id, limit=args.limit, workspace=workspace)
    elif args.command == "open-well":
        report = _run_geometry_command(
            nollm_open_well,
            out_dir,
            entry_shard_id=args.entry_shard_id,
            entry_task=args.entry_task,
            anchor_vector=json.loads(args.anchor_vector),
            revision_id=args.revision_id,
            ttl_seconds=args.ttl_seconds,
        )
    elif args.command == "surface":
        report = _run_geometry_command(
            nollm_surface,
            out_dir,
            well_id=args.well_id,
            center_shard_id=args.center_shard_id,
            radius=args.radius,
            target_scale=args.target_scale,
        )
    elif args.command == "focus":
        report = _run_geometry_command(
            nollm_focus,
            out_dir,
            well_id=args.well_id,
            target_shard_id=args.target_shard_id,
            target_scale=args.target_scale,
        )
    elif args.command == "drift":
        report = _run_geometry_command(
            nollm_drift,
            out_dir,
            well_id=args.well_id,
            current_shard_id=args.current_shard_id,
            chosen_shard_id=args.chosen_shard_id,
            radius=args.radius,
        )
    elif args.command == "read":
        report = _run_geometry_command(nollm_read, out_dir, well_id=args.well_id, shard_id=args.shard_id)
    elif args.command == "recall-trace":
        report = _run_geometry_command(nollm_recall_trace, out_dir, well_id=args.well_id, path=json.loads(args.path))
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


def _run_geometry_command(fn, *args, **kwargs) -> dict[str, object]:
    try:
        return fn(*args, **kwargs)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "error": "field_unavailable",
            "message": str(exc),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "error": "invalid_geometry_request",
            "message": str(exc),
        }


if __name__ == "__main__":
    raise SystemExit(main())
