from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

SCHEMA = "nollm.test_matrix.v1"
RECEIPT_SCHEMA = "nollm.test_matrix.shard_receipt.v1"
MARKER = ".nollm_test_matrix_root.json"
WORKTREE_MARKER = ".nollm_test_matrix_worktree_root.json"
RUNTIME_SNAPSHOT_RELATIVE = "inputs/runtime_fixture"
TAIL_CHARS = 12000
POLL_INTERVAL_SECONDS = 0.1
KILL_WAIT_SECONDS = 5.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded complete Nollm pytest matrix.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    _add_roots(plan_parser, include_worktree=False)
    plan_parser.add_argument("--target-node-count", type=int, default=120)
    plan_parser.add_argument("--max-shards", type=int, default=24)

    run_parser = subparsers.add_parser("run-shard")
    _add_roots(run_parser, include_worktree=True)
    shard_group = run_parser.add_mutually_exclusive_group(required=True)
    shard_group.add_argument("--shard")
    shard_group.add_argument("--all", action="store_true")
    run_parser.add_argument("--workers", type=int, default=1)
    run_parser.add_argument("--timeout-seconds", type=float, default=90.0)
    run_parser.add_argument("--resume", action="store_true")

    list_parser = subparsers.add_parser("list-shards")
    _add_roots(list_parser, include_worktree=False)

    verify_parser = subparsers.add_parser("verify")
    _add_roots(verify_parser, include_worktree=True)

    cleanup_parser = subparsers.add_parser("cleanup")
    _add_roots(cleanup_parser, include_worktree=True)
    cleanup_parser.add_argument("--remove-receipts", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            return command_plan(args)
        if args.command == "run-shard":
            return command_run_shard(args)
        if args.command == "list-shards":
            return command_list_shards(args)
        if args.command == "verify":
            return command_verify(args)
        if args.command == "cleanup":
            return command_cleanup(args)
    except MatrixError as exc:
        print(json.dumps(exc.payload, indent=2, sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - final traceback guard
        print(json.dumps({"status": "error", "reason": type(exc).__name__, "message": stable_error(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    return 2


def _add_roots(parser: argparse.ArgumentParser, *, include_worktree: bool) -> None:
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--receipt-root", default=None)
    if include_worktree:
        parser.add_argument("--worktree-root", default=None)


def command_plan(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    head = git_stdout(repo_root, "rev-parse", "HEAD")
    receipt_root = resolve_receipt_root(args.receipt_root, head)
    status = git_status(repo_root)
    if status != "":
        raise MatrixError("source_not_clean", "matrix plan requires a clean tracked source checkout")
    nodes = collect_node_ids(repo_root)
    if not nodes:
        raise MatrixError("collection_empty", "pytest collection produced no node ids")
    shards = assign_shards(nodes, args.target_node_count, args.max_shards)
    if receipt_root.exists():
        shutil.rmtree(receipt_root)
    try:
        runtime_fixture = snapshot_runtime_fixture(repo_root, receipt_root)
        matrix_id = matrix_id_from_receipt_root(receipt_root)
        plan = {
            "schema": SCHEMA,
            "matrix_id": matrix_id,
            "git_head": head,
            "collection_fingerprint": fingerprint(nodes),
            "manifest_fingerprint": fingerprint({"head": head, "nodes": nodes, "shards": shards}),
            "collected_count": len(nodes),
            "target_node_count": args.target_node_count,
            "max_shards": args.max_shards,
            "clean_status_before": "",
            "runtime_fixture": runtime_fixture,
            "node_ids": nodes,
            "shards": [
                {
                    "shard_id": item["shard_id"],
                    "node_ids": item["node_ids"],
                    "node_count": len(item["node_ids"]),
                    "selection_fingerprint": fingerprint(item["node_ids"]),
                }
                for item in shards
            ],
        }
        write_json(receipt_root / MARKER, root_marker_payload(plan, receipt_root))
        write_json(plan_path(receipt_root), plan)
    except Exception:
        if receipt_root.exists():
            shutil.rmtree(receipt_root)
        raise
    print(f"PLAN_OK head={head} collected={len(nodes)} shards={len(shards)} receipt_root={receipt_root}")
    return 0


def command_list_shards(args: argparse.Namespace) -> int:
    plan = load_plan(resolve_receipt_root(args.receipt_root, None))
    for shard in plan["shards"]:
        print(shard["shard_id"])
    return 0


def command_run_shard(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    head = git_stdout(repo_root, "rev-parse", "HEAD")
    receipt_root = resolve_receipt_root(args.receipt_root, head)
    worktree_root = resolve_worktree_root(args.worktree_root, head)
    plan = load_plan(receipt_root)
    assert_source_matches_plan(repo_root, plan)
    assert_receipt_root_marker(receipt_root, plan)
    assert_runtime_fixture_snapshot_matches_plan(receipt_root, plan)
    current_nodes = collect_node_ids(repo_root)
    assert_collection_matches(plan, current_nodes)
    ensure_worktree_root_marker(worktree_root, receipt_root, plan)

    if args.all:
        selected = [shard["shard_id"] for shard in plan["shards"]]
        workers = max(1, int(args.workers))
        if workers == 1:
            receipts = [run_one_shard(repo_root, receipt_root, worktree_root, plan, shard_id, args.timeout_seconds, args.resume) for shard_id in selected]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(run_one_shard, repo_root, receipt_root, worktree_root, plan, shard_id, args.timeout_seconds, args.resume)
                    for shard_id in selected
                ]
                receipts = [future.result() for future in futures]
        failed = [receipt for receipt in receipts if receipt["status"] != "passed"]
        print(f"RUN_ALL_DONE shards={len(receipts)} failed={len(failed)} receipt_root={receipt_root}")
        return 0 if not failed else 1

    receipt = run_one_shard(repo_root, receipt_root, worktree_root, plan, args.shard, args.timeout_seconds, args.resume)
    print(f"SHARD_DONE shard={args.shard} status={receipt['status']} receipt={receipt_path(receipt_root, args.shard)}")
    return 0 if receipt["status"] == "passed" else 1


def command_verify(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    head = git_stdout(repo_root, "rev-parse", "HEAD")
    receipt_root = resolve_receipt_root(args.receipt_root, head)
    worktree_root = resolve_worktree_root(args.worktree_root, head)
    plan = load_plan(receipt_root)
    assert_source_matches_plan(repo_root, plan)
    assert_receipt_root_marker(receipt_root, plan)
    assert_runtime_fixture_snapshot_matches_plan(receipt_root, plan)
    assert_worktree_root_marker(worktree_root, receipt_root, plan)
    current_nodes = collect_node_ids(repo_root)
    assert_collection_matches(plan, current_nodes)

    seen: dict[str, str] = {}
    duplicates: list[str] = []
    failures: list[dict[str, Any]] = []
    for shard in plan["shards"]:
        path = receipt_path(receipt_root, shard["shard_id"])
        if not path.exists():
            failures.append({"shard_id": shard["shard_id"], "reason": "missing_receipt"})
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append({"shard_id": shard["shard_id"], "reason": "malformed_receipt"})
            continue
        issue = validate_success_receipt(plan, shard, receipt)
        if issue is not None:
            failures.append({"shard_id": shard["shard_id"], "reason": issue})
            continue
        for node_id in receipt["selected_node_ids"]:
            if node_id in seen:
                duplicates.append(node_id)
            seen[node_id] = shard["shard_id"]
    missing = [node_id for node_id in current_nodes if node_id not in seen]
    extra = [node_id for node_id in seen if node_id not in set(current_nodes)]
    leftovers = list_worktree_leftovers(matrix_worktree_root(worktree_root, plan))
    if failures or missing or duplicates or extra or leftovers:
        raise MatrixError(
            "verify_failed",
            "matrix verification failed",
            {
                "failed_receipts": failures,
                "missing_count": len(missing),
                "duplicate_count": len(duplicates),
                "extra_count": len(extra),
                "worktree_leftovers": [str(path) for path in leftovers],
            },
        )
    print("FULL_MATRIX_OK")
    print(f"head={plan['git_head']}")
    print(f"collected={len(current_nodes)}")
    print(f"shards={len(plan['shards'])}")
    print(f"passed={len(plan['shards'])}")
    print(f"collection_fingerprint={plan['collection_fingerprint']}")
    print(f"matrix_fingerprint={plan['manifest_fingerprint']}")
    print(f"runtime_fixture_manifest_fingerprint={plan['runtime_fixture']['manifest_fingerprint']}")
    print(f"runtime_fixture_tree_fingerprint={plan['runtime_fixture']['tree_fingerprint'] or 'absent'}")
    print(f"receipt_root={receipt_root}")
    return 0


def command_cleanup(args: argparse.Namespace) -> int:
    head = git_stdout(resolve_repo_root(args.repo_root), "rev-parse", "HEAD")
    receipt_root = resolve_receipt_root(args.receipt_root, head)
    worktree_root = resolve_worktree_root(args.worktree_root, head)
    removed: list[str] = []
    plan = load_plan(receipt_root)
    assert_worktree_root_marker(worktree_root, receipt_root, plan)
    for shard in plan["shards"]:
        worktree = matrix_worktree_root(worktree_root, plan) / shard["shard_id"]
        if worktree.exists():
            remove_worktree(resolve_repo_root(args.repo_root), worktree)
            removed.append(str(worktree))
    if args.remove_receipts:
        marker = receipt_root / MARKER
        if not marker.exists():
            raise MatrixError("cleanup_refused", "receipt root marker missing")
        shutil.rmtree(receipt_root)
        removed.append(str(receipt_root))
    print(json.dumps({"status": "cleanup_done", "removed": removed}, indent=2, sort_keys=True))
    return 0


def run_one_shard(repo_root: Path, receipt_root: Path, worktree_root: Path, plan: dict[str, Any], shard_id: str, timeout_seconds: float, resume: bool) -> dict[str, Any]:
    shard = find_shard(plan, shard_id)
    existing_path = receipt_path(receipt_root, shard_id)
    if resume and existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = None
        if existing is not None and validate_success_receipt(plan, shard, existing) is None:
            existing["resumed"] = True
            return existing

    receipt_root.mkdir(parents=True, exist_ok=True)
    (receipt_root / "junit").mkdir(parents=True, exist_ok=True)
    (receipt_root / "logs").mkdir(parents=True, exist_ok=True)
    owned_worktree_root = matrix_worktree_root(worktree_root, plan)
    owned_worktree_root.mkdir(parents=True, exist_ok=True)
    worktree = owned_worktree_root / shard_id
    junit = receipt_root / "junit" / f"{shard_id}.xml"
    stdout_path = receipt_root / "logs" / f"{shard_id}.stdout.txt"
    stderr_path = receipt_root / "logs" / f"{shard_id}.stderr.txt"
    cleanup_result = "not_started"
    worktree_created_by_this_call = False
    reason = None
    runtime_fixture = plan["runtime_fixture"]
    started = time.monotonic()
    status = "failed"
    returncode = -1
    timed_out = False
    junit_reported_tests = None
    try:
        if worktree.exists():
            reason = "worktree_exists"
            cleanup_result = "not_owned"
            returncode = 1
            raise MatrixError("worktree_exists", "shard worktree already exists", {"worktree": str(worktree)})
        add_worktree(repo_root, worktree, plan["git_head"])
        worktree_created_by_this_call = True
        copy_runtime_fixture_snapshot(receipt_root, worktree, plan)
        collection_cwd = pytest_cwd(worktree)
        command = [sys.executable, "-m", "pytest", "-q", "--junitxml", str(junit), *shard["node_ids"]]
        returncode, timed_out = run_process(command, cwd=collection_cwd, env=pytest_env(worktree), timeout_seconds=timeout_seconds, stdout_path=stdout_path, stderr_path=stderr_path)
        junit_reported_tests = parse_junit_tests(junit) if junit.exists() else None
        if timed_out:
            status = "timed_out"
            reason = "timeout"
        elif returncode == 0 and junit_reported_tests is not None:
            status = "passed"
        else:
            status = "failed"
            reason = "pytest_failed"
    except MatrixError as exc:
        reason = reason or exc.payload["reason"]
    finally:
        if worktree_created_by_this_call:
            cleanup_result = remove_worktree(repo_root, worktree)
    duration = round(time.monotonic() - started, 3)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "shard_id": shard_id,
        "git_head": plan["git_head"],
        "collection_fingerprint": plan["collection_fingerprint"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "selection_fingerprint": shard["selection_fingerprint"],
        "selected_node_ids": shard["node_ids"],
        "selected_count": len(shard["node_ids"]),
        "junit_path": str(junit),
        "junit_tests": len(shard["node_ids"]) if status == "passed" and junit_reported_tests is not None else None,
        "junit_reported_tests": junit_reported_tests,
        "returncode": returncode,
        "reason": reason,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "duration_seconds": duration,
        "stdout_tail": read_tail(stdout_path),
        "stderr_tail": read_tail(stderr_path),
        "worktree_path": str(worktree),
        "worktree_created_by_this_call": worktree_created_by_this_call,
        "worktree_cleanup": cleanup_result,
        "runtime_fixture_state": runtime_fixture["state"],
        "runtime_fixture_manifest_fingerprint": runtime_fixture["manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": runtime_fixture["tree_fingerprint"],
    }
    write_json(existing_path, receipt)
    return receipt


def assign_shards(node_ids: list[str], target_node_count: int, max_shards: int) -> list[dict[str, Any]]:
    target = max(1, int(target_node_count))
    chunks: list[list[str]] = []
    current_file = ""
    current_nodes: list[str] = []
    for node_id in node_ids:
        file_part = node_id.split("::", 1)[0]
        if current_nodes and file_part != current_file:
            chunks.extend(split_large_chunk(current_nodes, target))
            current_nodes = []
        current_file = file_part
        current_nodes.append(node_id)
    if current_nodes:
        chunks.extend(split_large_chunk(current_nodes, target))

    shards: list[list[str]] = []
    current: list[str] = []
    current_weight = 0
    target_weight = target
    if max_shards > 0 and len(node_ids) >= target * 4:
        total_weight = sum(node_cost(node_id) for node_id in node_ids)
        target_weight = max(1, min(target, math.ceil(total_weight / max_shards)))
    for chunk in chunks:
        chunk_weight = sum(node_cost(node_id) for node_id in chunk)
        if current and current_weight + chunk_weight > target_weight:
            shards.append(current)
            current = []
            current_weight = 0
        current.extend(chunk)
        current_weight += chunk_weight
    if current:
        shards.append(current)
    if len(shards) == 1 and len(shards[0]) > 1:
        mid = (len(shards[0]) + 1) // 2
        shards = [shards[0][:mid], shards[0][mid:]]
    if max_shards > 0 and len(node_ids) >= target * 4:
        shards = split_largest_shards(shards, max_shards)
    while max_shards > 0 and len(shards) > max_shards:
        merge_at = min(range(len(shards) - 1), key=lambda index: shard_cost(shards[index]) + shard_cost(shards[index + 1]))
        shards[merge_at : merge_at + 2] = [shards[merge_at] + shards[merge_at + 1]]
    return [{"shard_id": f"s{index:03d}", "node_ids": nodes} for index, nodes in enumerate(shards, start=1)]


def split_largest_shards(shards: list[list[str]], max_shards: int) -> list[list[str]]:
    result = [list(shard) for shard in shards]
    while len(result) < max_shards:
        index = max(range(len(result)), key=lambda item: shard_cost(result[item]))
        left, right = split_shard_at_file_boundary(result[index])
        if not left or not right:
            break
        result[index : index + 1] = [left, right]
    return result


def split_shard_at_file_boundary(nodes: list[str]) -> tuple[list[str], list[str]]:
    if len(nodes) < 2:
        return nodes, []
    chunks: list[list[str]] = []
    current_file = ""
    current_nodes: list[str] = []
    for node_id in nodes:
        file_part = node_id.split("::", 1)[0]
        if current_nodes and file_part != current_file:
            chunks.append(current_nodes)
            current_nodes = []
        current_file = file_part
        current_nodes.append(node_id)
    if current_nodes:
        chunks.append(current_nodes)
    if len(chunks) == 1:
        mid = (len(nodes) + 1) // 2
        return nodes[:mid], nodes[mid:]
    midpoint = shard_cost(nodes) / 2
    left: list[str] = []
    right: list[str] = []
    left_weight = 0
    for chunk in chunks:
        chunk_weight = shard_cost(chunk)
        if not right and left_weight + chunk_weight <= midpoint:
            left.extend(chunk)
            left_weight += chunk_weight
        else:
            right.extend(chunk)
    if not left:
        left = chunks[0]
        right = [node for chunk in chunks[1:] for node in chunk]
    return left, right


def shard_cost(nodes: list[str]) -> int:
    return sum(node_cost(node_id) for node_id in nodes)


def node_cost(node_id: str) -> int:
    file_name = Path(node_id.split("::", 1)[0]).name
    if file_name.startswith(("test_g", "test_geometry", "test_gravity")):
        return 5
    if file_name.startswith("test_mt1_"):
        return 3
    if "report_regeneration" in file_name or "engineering_rc_archive" in file_name:
        return 2
    return 1


def split_large_chunk(nodes: list[str], target: int) -> list[list[str]]:
    if len(nodes) <= target:
        return [nodes]
    return [nodes[index : index + target] for index in range(0, len(nodes), target)]


def collect_node_ids(repo_root: Path) -> list[str]:
    cwd = pytest_cwd(repo_root)
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    with tempfile.TemporaryDirectory() as tmp:
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        returncode, timed_out = run_process(command, cwd=cwd, env=pytest_env(repo_root), timeout_seconds=120.0, stdout_path=stdout_path, stderr_path=stderr_path)
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    if timed_out:
        raise MatrixError("collection_timeout", "pytest collection timed out", {"stderr_tail": tail(stderr)})
    if returncode != 0:
        raise MatrixError("collection_failed", "pytest collection failed", {"returncode": returncode, "stdout_tail": tail(stdout), "stderr_tail": tail(stderr)})
    nodes: list[str] = []
    for line in stdout.splitlines():
        value = line.strip()
        if not value or value.startswith("=") or " warnings" in value or " warning" in value:
            continue
        if value.endswith(" collected") or " no tests collected" in value:
            continue
        if "::" in value:
            nodes.append(value.replace("\\", "/"))
    return nodes


def assert_source_matches_plan(repo_root: Path, plan: dict[str, Any]) -> None:
    head = git_stdout(repo_root, "rev-parse", "HEAD")
    status = git_status(repo_root)
    failures: dict[str, Any] = {}
    if head != plan["git_head"]:
        failures["head"] = {"expected": plan["git_head"], "actual": head}
    if status != plan["clean_status_before"]:
        failures["status"] = {"expected": plan["clean_status_before"], "actual": status}
    if failures:
        raise MatrixError("source_drift", "source branch or working tree changed after plan", failures)


def assert_collection_matches(plan: dict[str, Any], nodes: list[str]) -> None:
    actual = fingerprint(nodes)
    if actual != plan["collection_fingerprint"]:
        raise MatrixError("collection_drift", "pytest collection changed after plan", {"expected": plan["collection_fingerprint"], "actual": actual})


def validate_success_receipt(plan: dict[str, Any], shard: dict[str, Any], receipt: dict[str, Any]) -> str | None:
    if receipt.get("status") != "passed":
        return f"status_{receipt.get('status')}"
    checks = {
        "git_head": plan["git_head"],
        "collection_fingerprint": plan["collection_fingerprint"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "selection_fingerprint": shard["selection_fingerprint"],
    }
    for key, expected in checks.items():
        if receipt.get(key) != expected:
            return f"{key}_mismatch"
    if receipt.get("selected_node_ids") != shard["node_ids"]:
        return "selected_node_ids_mismatch"
    if receipt.get("selected_count") != len(shard["node_ids"]):
        return "selected_count_mismatch"
    if receipt.get("junit_tests") != len(shard["node_ids"]):
        return "junit_count_mismatch"
    if receipt.get("returncode") != 0:
        return "returncode_mismatch"
    if receipt.get("timed_out") is not False:
        return "timed_out"
    runtime_fixture = plan["runtime_fixture"]
    if receipt.get("runtime_fixture_state") != runtime_fixture["state"]:
        return "runtime_fixture_state_mismatch"
    if receipt.get("runtime_fixture_manifest_fingerprint") != runtime_fixture["manifest_fingerprint"]:
        return "runtime_fixture_manifest_fingerprint_mismatch"
    if receipt.get("runtime_fixture_tree_fingerprint") != runtime_fixture["tree_fingerprint"]:
        return "runtime_fixture_tree_fingerprint_mismatch"
    if receipt.get("worktree_created_by_this_call") is not True:
        return "worktree_not_owned"
    if receipt.get("worktree_cleanup") != "removed":
        return "worktree_cleanup_failed"
    return None


def find_shard(plan: dict[str, Any], shard_id: str) -> dict[str, Any]:
    for shard in plan["shards"]:
        if shard["shard_id"] == shard_id:
            return shard
    raise MatrixError("unknown_shard", "shard id is not in plan", {"shard_id": shard_id})


def add_worktree(repo_root: Path, worktree: Path, head: str) -> None:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["git", "worktree", "add", "--detach", str(worktree), head], cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        raise MatrixError("worktree_add_failed", "git worktree add failed", {"stderr_tail": tail(result.stderr)})


def copy_runtime_fixture_snapshot(receipt_root: Path, worktree: Path, plan: dict[str, Any]) -> None:
    runtime_fixture = plan["runtime_fixture"]
    if runtime_fixture["state"] == "absent":
        return
    source = receipt_root / runtime_fixture["snapshot_relative_path"]
    target = worktree / "out" / "nollm_runtime"
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def snapshot_runtime_fixture(repo_root: Path, receipt_root: Path) -> dict[str, Any]:
    source = repo_root / "out" / "nollm_runtime"
    if not source.exists():
        manifest = runtime_manifest_payload("absent", [])
        return {
            "state": "absent",
            "source_kind": "ignored_runtime_baseline",
            "snapshot_relative_path": None,
            "tree_fingerprint": None,
            "file_count": 0,
            "manifest_fingerprint": fingerprint(manifest),
        }
    if not source.is_dir() or source.is_symlink():
        raise MatrixError("fixture_snapshot_rejected", "runtime fixture source is not a regular directory")
    reject_unsupported_runtime_entries(source)
    target = receipt_root / RUNTIME_SNAPSHOT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, symlinks=False)
    entries = build_runtime_manifest_entries(target)
    manifest = runtime_manifest_payload("present", entries)
    write_json(receipt_root / "inputs" / "runtime_fixture_manifest.json", manifest)
    return {
        "state": "present",
        "source_kind": "ignored_runtime_baseline",
        "snapshot_relative_path": RUNTIME_SNAPSHOT_RELATIVE,
        "tree_fingerprint": fingerprint(entries),
        "file_count": len(entries),
        "manifest_fingerprint": fingerprint(manifest),
    }


def assert_runtime_fixture_snapshot_matches_plan(receipt_root: Path, plan: dict[str, Any]) -> None:
    runtime_fixture = plan["runtime_fixture"]
    relative = runtime_fixture.get("snapshot_relative_path")
    target = receipt_root / relative if relative else None
    if runtime_fixture["state"] == "absent":
        manifest = runtime_manifest_payload("absent", [])
        if fingerprint(manifest) != runtime_fixture["manifest_fingerprint"]:
            raise MatrixError("fixture_snapshot_drift", "absent runtime fixture manifest drifted")
        return
    if target is None or not target.exists():
        raise MatrixError("fixture_snapshot_drift", "runtime fixture snapshot is missing")
    entries = build_runtime_manifest_entries(target)
    manifest = runtime_manifest_payload("present", entries)
    if fingerprint(entries) != runtime_fixture["tree_fingerprint"] or fingerprint(manifest) != runtime_fixture["manifest_fingerprint"]:
        raise MatrixError("fixture_snapshot_drift", "runtime fixture snapshot drifted")


def build_runtime_manifest_entries(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            if path.is_dir() and not path.is_symlink():
                continue
            raise MatrixError("fixture_snapshot_rejected", "runtime fixture contains unsupported filesystem entry")
        relative = path.relative_to(root).as_posix()
        if relative.startswith("../") or relative == ".." or "\\" in relative:
            raise MatrixError("fixture_snapshot_rejected", "runtime fixture contains invalid relative path")
        data = path.read_bytes()
        entries.append({"path": relative, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return entries


def reject_unsupported_runtime_entries(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise MatrixError("fixture_snapshot_rejected", "runtime fixture contains unsupported filesystem entry")
        if path.is_dir() or path.is_file():
            continue
        raise MatrixError("fixture_snapshot_rejected", "runtime fixture contains unsupported filesystem entry")


def runtime_manifest_payload(state: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema": "nollm.test_matrix.runtime_fixture_manifest.v1", "state": state, "files": entries}


def matrix_id_from_receipt_root(receipt_root: Path) -> str:
    return receipt_root.name or "default"


def matrix_worktree_root(worktree_root: Path, plan: dict[str, Any]) -> Path:
    return worktree_root / plan["matrix_id"]


def root_marker_payload(plan: dict[str, Any], receipt_root: Path) -> dict[str, Any]:
    return {
        "schema": "nollm.test_matrix.root.v1",
        "git_head": plan["git_head"],
        "matrix_id": plan["matrix_id"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "receipt_root": str(receipt_root.resolve()),
    }


def ensure_worktree_root_marker(worktree_root: Path, receipt_root: Path, plan: dict[str, Any]) -> None:
    root = matrix_worktree_root(worktree_root, plan)
    root.mkdir(parents=True, exist_ok=True)
    marker = root / WORKTREE_MARKER
    payload = root_marker_payload(plan, receipt_root)
    if marker.exists():
        assert_marker_payload(marker, payload, "worktree_root_marker_mismatch")
        return
    write_json(marker, payload)


def assert_worktree_root_marker(worktree_root: Path, receipt_root: Path, plan: dict[str, Any]) -> None:
    marker = matrix_worktree_root(worktree_root, plan) / WORKTREE_MARKER
    if not marker.exists():
        raise MatrixError("cleanup_refused", "matrix worktree root marker missing")
    assert_marker_payload(marker, root_marker_payload(plan, receipt_root), "worktree_root_marker_mismatch")


def assert_receipt_root_marker(receipt_root: Path, plan: dict[str, Any]) -> None:
    marker = receipt_root / MARKER
    if not marker.exists():
        raise MatrixError("receipt_root_marker_missing", "matrix receipt root marker missing")
    assert_marker_payload(marker, root_marker_payload(plan, receipt_root), "receipt_root_marker_mismatch")


def assert_marker_payload(marker: Path, expected: dict[str, Any], reason: str) -> None:
    try:
        actual = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise MatrixError(reason, "matrix root marker is malformed")
    if actual != expected:
        raise MatrixError(reason, "matrix root marker does not match plan")


def remove_worktree(repo_root: Path, worktree: Path) -> str:
    if not worktree.exists():
        return "removed"
    result = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root, text=True, capture_output=True)
    if result.returncode == 0 and not worktree.exists():
        return "removed"
    return "failed"


def list_worktree_leftovers(worktree_root: Path) -> list[Path]:
    if not worktree_root.exists():
        return []
    return [path for path in sorted(worktree_root.iterdir()) if path.is_dir()]


def run_process(command: list[str], *, cwd: Path, env: dict[str, str], timeout_seconds: float, stdout_path: Path, stderr_path: Path) -> tuple[int, bool]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=(os.name != "nt"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        timed_out = wait_with_deadline(process, timeout_seconds)
    return int(process.returncode if process.returncode is not None else -1), timed_out


def wait_with_deadline(process: subprocess.Popen[str], timeout_seconds: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while process.poll() is None:
        if time.monotonic() >= deadline:
            terminate_process_tree(process)
            wait_for_exit(process)
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return False


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.Popen(["taskkill", "/F", "/T", "/PID", str(process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait(timeout=KILL_WAIT_SECONDS)
        except Exception:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception:
            process.kill()


def wait_for_exit(process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + KILL_WAIT_SECONDS
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
    if process.poll() is None:
        process.kill()


def parse_junit_tests(path: Path) -> int | None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    if root.tag == "testsuite":
        return int(root.attrib.get("tests", "-1"))
    total = 0
    for suite in root.findall("testsuite"):
        total += int(suite.attrib.get("tests", "0"))
    return total


def pytest_cwd(repo_root: Path) -> Path:
    return repo_root


def pytest_env(repo_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    reference = repo_root / "reference" / "python"
    if reference.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(reference) if not existing else str(reference) + os.pathsep + existing
    return env


def resolve_repo_root(value: str | None) -> Path:
    if value is not None:
        return Path(value).resolve()
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True)
    if result.returncode != 0:
        raise MatrixError("repo_root_not_found", "could not resolve git repository root")
    return Path(result.stdout.strip()).resolve()


def resolve_receipt_root(value: str | None, head: str | None) -> Path:
    if value is not None:
        return Path(value).resolve()
    if head is None:
        raise MatrixError("receipt_root_required", "receipt root is required when head is unknown")
    return Path("C:/Users/chaos/nollm_test_runs") / head


def resolve_worktree_root(value: str | None, head: str | None) -> Path:
    if value is not None:
        return Path(value).resolve()
    if head is None:
        raise MatrixError("worktree_root_required", "worktree root is required when head is unknown")
    return Path("C:/Users/chaos/nollm_test_worktrees") / head


def git_stdout(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        raise MatrixError("git_failed", "git command failed", {"args": args, "stderr_tail": tail(result.stderr)})
    return result.stdout.strip()


def git_status(repo_root: Path) -> str:
    return git_stdout(repo_root, "status", "--short")


def plan_path(receipt_root: Path) -> Path:
    return receipt_root / "matrix_plan.json"


def receipt_path(receipt_root: Path, shard_id: str) -> Path:
    return receipt_root / "receipts" / f"{shard_id}.json"


def load_plan(receipt_root: Path) -> dict[str, Any]:
    path = plan_path(receipt_root)
    if not path.exists():
        raise MatrixError("plan_missing", "matrix plan is missing", {"path": str(path)})
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def fingerprint(value: Any) -> str:
    import hashlib

    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return f"... output truncated to last {TAIL_CHARS} chars ...\n{text[-TAIL_CHARS:]}"


def read_tail(path: Path) -> str:
    if not path.exists():
        return ""
    return tail(path.read_text(encoding="utf-8", errors="replace"))


def stable_error(exc: BaseException) -> str:
    text = str(exc)
    if "\\" in text:
        text = text.replace("\\", "/")
    return text


class MatrixError(Exception):
    def __init__(self, reason: str, message: str, details: dict[str, Any] | None = None, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.payload = {"status": "error", "reason": reason, "message": message}
        if details:
            self.payload["details"] = details


if __name__ == "__main__":
    raise SystemExit(main())
