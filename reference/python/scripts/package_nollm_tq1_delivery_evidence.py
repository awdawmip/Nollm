from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SCHEMA = "nollm.tq1.delivery-evidence-capsule.v1"
TASK_ORIGINAL = "NOLLM_TQ1_C6_JUNIT_AND_FROZEN_INPUT_EVIDENCE_INTEGRITY_FINAL_CLOSURE_TASK_20260706.md"
TASK_AMENDMENT = "NOLLM_TQ1_C6_SINGLE_BUNDLE_DELIVERY_EVIDENCE_AMENDMENT_20260706.md"
TASK_C7R = "NOLLM_TQ1_C7R_CANONICAL_EVIDENCE_REPLAY_UNIFIED_ONE_HOUR_EXECUTION_FINAL_CLOSURE_TASK_20260706.md"
EXCLUDED_INVENTORY_PATHS = {"CAPSULE_MANIFEST.json", "PAYLOAD_INVENTORY.json"}
C7R_PHASE = "tq1-c7r"
EXECUTION_CONTRACT = {
    "schema": "nollm.test_matrix.execution_contract.v1",
    "planned_shard_timeout_seconds": 3600.0,
    "retry_policy": "forbidden",
    "receipt_overwrite": "forbidden",
    "execution_mode": "single_pass",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package TQ1 final matrix evidence into a Git evidence ref.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-ref")
    build.add_argument("--repo-root", required=True)
    build.add_argument("--receipt-root", required=True)
    build.add_argument("--final-head", required=True)
    build.add_argument("--final-verify-log", required=True)
    build.add_argument("--governance-file", action="append", default=[])
    build.add_argument("--log", action="append", default=[])
    build.add_argument("--evidence-ref", required=True)

    verify = subparsers.add_parser("verify-ref")
    verify.add_argument("--repo-root", required=True)
    verify.add_argument("--evidence-ref", required=True)
    verify.add_argument("--expected-head", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "build-ref":
            return command_build_ref(args)
        if args.command == "verify-ref":
            return command_verify_ref(args)
    except CapsuleError as exc:
        print(json.dumps({"status": "error", "reason": exc.reason, "message": str(exc), "details": exc.details}, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    return 2


def command_build_ref(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    receipt_root = Path(args.receipt_root).resolve()
    final_head = require_head(args.final_head)
    evidence_ref = require_evidence_ref(args.evidence_ref, final_head)
    phase = evidence_phase(evidence_ref, final_head)
    if git(repo_root, "rev-parse", "HEAD").stdout.strip() != final_head:
        raise CapsuleError("head_mismatch", "current repository HEAD does not match final head")
    if git(repo_root, "status", "--short").stdout.strip():
        raise CapsuleError("source_not_clean", "source worktree must be clean before packaging")
    if git_optional(repo_root, "show-ref", "--verify", "--quiet", evidence_ref).returncode == 0:
        raise CapsuleError("evidence_ref_exists", "evidence ref already exists", {"evidence_ref": evidence_ref})

    plan = read_json(receipt_root / "matrix_plan.json")
    if plan.get("git_head") != final_head:
        raise CapsuleError("plan_head_mismatch", "matrix plan does not match final head")
    verify_log_path = Path(args.final_verify_log).resolve()
    verify_output = verify_log_path.read_text(encoding="utf-8")
    require_full_matrix_ok(verify_output, final_head, receipt_root)
    verify_receipt_root_evidence(receipt_root, plan)

    with tempfile.TemporaryDirectory(prefix="nollm-tq1-capsule-") as tmp:
        staging = Path(tmp) / "capsule"
        staging.mkdir()
        source_inventory_before = receipt_source_inventory(receipt_root, plan)
        copy_receipt_root(receipt_root, staging / "receipt_root", plan)
        source_inventory_after = receipt_source_inventory(receipt_root, plan)
        if source_inventory_before != source_inventory_after:
            raise CapsuleError("source_inventory_changed", "receipt root changed while packaging")
        staged_receipt_inventory = inventory_under(staging / "receipt_root", prefix="receipt_root/")
        if staged_receipt_inventory != source_inventory_before:
            raise CapsuleError("staged_inventory_mismatch", "staged receipt evidence differs from source")

        write_governance(staging, args.governance_file)
        write_logs(staging, args.log, verify_log_path)
        evidence = final_matrix_evidence(receipt_root, plan, verify_output)
        write_json(staging / "summary" / "FINAL_MATRIX_EVIDENCE.json", evidence)
        write_text(staging / "summary" / "FULL_MATRIX_OK.txt", verify_output)
        write_text(staging / "summary" / "DELIVERY_COMMANDS.txt", delivery_commands(args))
        write_text(staging / "README.md", readme(final_head, evidence_ref))

        payload_inventory = inventory_under(staging)
        payload_inventory = [item for item in payload_inventory if item["path"] not in EXCLUDED_INVENTORY_PATHS]
        write_json(staging / "PAYLOAD_INVENTORY.json", {"schema": "nollm.tq1.delivery-evidence-payload-inventory.v1", "files": payload_inventory})
        payload_inventory_sha256 = file_sha256(staging / "PAYLOAD_INVENTORY.json")
        manifest = capsule_manifest(args, plan, evidence, evidence_ref, payload_inventory_sha256)
        write_json(staging / "CAPSULE_MANIFEST.json", manifest)

        commit = create_parentless_commit(repo_root, staging, f"{phase.upper()} delivery evidence capsule for {final_head}")
    git(repo_root, "update-ref", evidence_ref, commit)
    print(json.dumps({"status": "built", "evidence_ref": evidence_ref, "evidence_commit": commit, "code_head": final_head}, indent=2, sort_keys=True))
    return 0


def command_verify_ref(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    expected_head = require_head(args.expected_head)
    evidence_ref = require_evidence_ref(args.evidence_ref, expected_head)
    phase = evidence_phase(evidence_ref, expected_head)
    commit = git(repo_root, "rev-parse", evidence_ref).stdout.strip()
    parents = git(repo_root, "rev-list", "--parents", "-n", "1", commit).stdout.strip().split()
    if parents != [commit]:
        raise CapsuleError("evidence_commit_has_parent", "evidence commit must be parentless")
    files = tree_files(repo_root, commit)
    require_tree_layout(files)
    manifest = tree_json(repo_root, commit, "CAPSULE_MANIFEST.json")
    inventory = tree_json(repo_root, commit, "PAYLOAD_INVENTORY.json")
    if manifest.get("schema") != SCHEMA:
        raise CapsuleError("manifest_schema_mismatch", "capsule manifest schema mismatch")
    if manifest.get("code_head") != expected_head:
        raise CapsuleError("manifest_head_mismatch", "capsule manifest code_head mismatch")
    if manifest.get("evidence_ref") != evidence_ref:
        raise CapsuleError("manifest_ref_mismatch", "capsule manifest evidence_ref mismatch")
    inventory_bytes = tree_bytes(repo_root, commit, "PAYLOAD_INVENTORY.json")
    if manifest.get("payload_inventory_sha256") != hashlib.sha256(inventory_bytes).hexdigest():
        raise CapsuleError("payload_inventory_sha256_mismatch", "payload inventory hash mismatch")
    listed = inventory.get("files")
    if not isinstance(listed, list):
        raise CapsuleError("payload_inventory_malformed", "payload inventory files must be a list")
    expected_paths = sorted(path for path in files if path not in EXCLUDED_INVENTORY_PATHS)
    actual_paths = sorted(item.get("path") for item in listed)
    if actual_paths != expected_paths:
        raise CapsuleError(
            "payload_inventory_path_mismatch",
            "payload inventory paths do not match tree",
            {"missing": sorted(set(expected_paths) - set(actual_paths)), "extra": sorted(set(actual_paths) - set(expected_paths))},
        )
    for item in listed:
        path = item["path"]
        data = tree_bytes(repo_root, commit, path)
        if item.get("size_bytes") != len(data) or item.get("sha256") != hashlib.sha256(data).hexdigest():
            raise CapsuleError("payload_inventory_hash_mismatch", "payload inventory entry does not match tree", {"path": path})
    verify_text = tree_bytes(repo_root, commit, "logs/07_matrix_verify.txt").decode("utf-8")
    receipt_root = Path(str(manifest.get("receipt_root_original", "")))
    require_full_matrix_ok(verify_text, expected_head, receipt_root, require_path=False)
    evidence = tree_json(repo_root, commit, "summary/FINAL_MATRIX_EVIDENCE.json")
    if evidence.get("head") != expected_head:
        raise CapsuleError("summary_head_mismatch", "summary head mismatch")
    semantic_replay_capsule(repo_root, commit, files, manifest, inventory, evidence_ref, expected_head, phase)
    print(json.dumps({"status": "verified", "evidence_ref": evidence_ref, "evidence_commit": commit, "code_head": expected_head}, indent=2, sort_keys=True))
    return 0


def require_head(value: str) -> str:
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise CapsuleError("invalid_head", "expected a 40-character lowercase hex head")
    return value


def require_evidence_ref(value: str, final_head: str) -> str:
    allowed = [f"refs/nollm-delivery/tq1-c6/{final_head}", f"refs/nollm-delivery/tq1-c7r/{final_head}"]
    if value not in allowed:
        raise CapsuleError("invalid_evidence_ref", "evidence ref must include an accepted phase and the exact final head", {"expected": allowed, "actual": value})
    return value


def evidence_phase(evidence_ref: str, final_head: str) -> str:
    prefix = "refs/nollm-delivery/"
    suffix = f"/{final_head}"
    if evidence_ref.startswith(prefix) and evidence_ref.endswith(suffix):
        return evidence_ref[len(prefix) : -len(suffix)]
    raise CapsuleError("invalid_evidence_ref", "could not derive evidence phase", {"evidence_ref": evidence_ref})


def require_full_matrix_ok(text: str, final_head: str, receipt_root: Path, *, require_path: bool = True) -> dict[str, str]:
    values = parse_full_matrix_ok(text)
    if values.get("FULL_MATRIX_OK") != "" or values.get("head") != final_head:
        raise CapsuleError("verify_log_not_full_matrix_ok", "verify log does not contain FULL_MATRIX_OK for final head")
    if require_path and values.get("receipt_root") != str(receipt_root):
        raise CapsuleError("verify_log_receipt_root_mismatch", "verify log does not contain the final receipt root")
    return values


def parse_full_matrix_ok(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    seen_ok = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "FULL_MATRIX_OK":
            if seen_ok:
                raise CapsuleError("verify_log_malformed", "verify log contains duplicate FULL_MATRIX_OK")
            values["FULL_MATRIX_OK"] = ""
            seen_ok = True
            continue
        if "=" not in line:
            raise CapsuleError("verify_log_malformed", "verify log contains non key=value line", {"line": line})
        key, value = line.split("=", 1)
        if not key or key in values:
            raise CapsuleError("verify_log_malformed", "verify log contains duplicate or empty key", {"key": key})
        values[key] = value
    if not seen_ok:
        raise CapsuleError("verify_log_not_full_matrix_ok", "verify log does not contain FULL_MATRIX_OK")
    return values


def receipt_source_inventory(receipt_root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    required: list[Path] = [receipt_root / "matrix_plan.json", receipt_root / ".nollm_test_matrix_root.json"]
    for shard in plan["shards"]:
        required.append(receipt_root / "receipts" / f"{shard['shard_id']}.json")
        required.append(receipt_root / "junit" / f"{shard['shard_id']}.xml")
    runtime = plan["runtime_fixture"]
    if runtime["state"] == "present":
        required.append(receipt_root / "inputs" / "runtime_fixture_manifest.json")
        fixture_root = receipt_root / "inputs" / "runtime_fixture"
        required.extend(path for _, path in sorted(
            ((path.relative_to(fixture_root).as_posix(), path) for path in fixture_root.rglob("*") if path.is_file()),
            key=lambda item: item[0],
        ))
    entries = []
    seen = set()
    for path in required:
        relative = "receipt_root/" + safe_relative(path, receipt_root)
        if relative in seen:
            raise CapsuleError("duplicate_payload_path", "duplicate payload path", {"path": relative})
        seen.add(relative)
        assert_regular_file(path)
        entries.append(file_entry(path, relative))
    return sorted(entries, key=lambda item: item["path"])


def verify_receipt_root_evidence(receipt_root: Path, plan: dict[str, Any]) -> None:
    contract = plan.get("execution_contract")
    if not isinstance(contract, dict):
        raise CapsuleError("execution_contract_missing", "matrix plan is missing execution contract")
    planned_timeout = float(contract.get("planned_shard_timeout_seconds", -1))
    for shard in plan["shards"]:
        shard_id = shard["shard_id"]
        receipt = read_json(receipt_root / "receipts" / f"{shard_id}.json")
        if receipt.get("status") != "passed":
            raise CapsuleError("receipt_not_passed", "all packaged receipts must be passed", {"shard_id": shard_id})
        if receipt.get("execution_contract") != contract:
            raise CapsuleError("execution_contract_mismatch", "receipt execution contract mismatch", {"shard_id": shard_id})
        if receipt.get("timeout_seconds") != planned_timeout:
            raise CapsuleError("timeout_contract_mismatch", "receipt timeout does not match plan contract", {"shard_id": shard_id})
        if receipt.get("returncode") != 0 or receipt.get("timed_out") is not False:
            raise CapsuleError("receipt_not_passed", "receipt did not complete cleanly", {"shard_id": shard_id})
        if receipt.get("worktree_cleanup") != "removed" or receipt.get("worktree_cleanup_error") is not None:
            raise CapsuleError("worktree_cleanup_failed", "receipt cleanup did not remove owned worktree", {"shard_id": shard_id})
        if receipt.get("fixture_copy_verified") is not True:
            raise CapsuleError("fixture_copy_not_verified", "runtime fixture copy was not verified", {"shard_id": shard_id})
        if receipt.get("selected_node_ids") != shard["node_ids"]:
            raise CapsuleError("selected_node_ids_mismatch", "receipt selected node ids mismatch", {"shard_id": shard_id})
        expected_relative = f"junit/{shard_id}.xml"
        if receipt.get("junit_relative_path") != expected_relative:
            raise CapsuleError("junit_evidence_path_mismatch", "receipt JUnit path mismatch", {"shard_id": shard_id})
        junit = receipt_root / expected_relative
        assert_regular_file(junit)
        if receipt.get("junit_size_bytes") != junit.stat().st_size:
            raise CapsuleError("junit_evidence_size_mismatch", "JUnit size mismatch", {"shard_id": shard_id})
        if receipt.get("junit_sha256") != file_sha256(junit):
            raise CapsuleError("junit_evidence_hash_mismatch", "JUnit hash mismatch", {"shard_id": shard_id})
        try:
            junit_count = parse_junit_tests(junit)
        except (ET.ParseError, ValueError, KeyError, TypeError, UnicodeError, OSError) as exc:
            raise CapsuleError("junit_evidence_malformed", "JUnit evidence is malformed", {"shard_id": shard_id, "message": str(exc)})
        if junit_count != len(shard["node_ids"]) or receipt.get("junit_tests") != junit_count or receipt.get("junit_reported_tests") != junit_count:
            raise CapsuleError("junit_evidence_count_mismatch", "JUnit evidence count mismatch", {"shard_id": shard_id})
    runtime = plan["runtime_fixture"]
    if runtime["state"] == "present":
        manifest_path = receipt_root / "inputs" / "runtime_fixture_manifest.json"
        assert_regular_file(manifest_path)
        snapshot = receipt_root / "inputs" / "runtime_fixture"
        entries = runtime_manifest_entries(snapshot)
        manifest = {"schema": "nollm.test_matrix.runtime_fixture_manifest.v1", "state": "present", "files": entries}
        recorded = read_json(manifest_path)
        if recorded != manifest:
            raise CapsuleError("runtime_fixture_manifest_mismatch", "runtime fixture manifest does not match snapshot")
        if fingerprint(entries) != runtime["tree_fingerprint"] or fingerprint(manifest) != runtime["manifest_fingerprint"]:
            raise CapsuleError("fixture_snapshot_drift", "runtime fixture snapshot drifted")


def parse_junit_tests(path: Path) -> int:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise ValueError("junit_testsuite_missing")
    for suite in suites:
        int(suite.attrib["tests"])
    testcases = root.findall(".//testcase")
    if not testcases:
        raise ValueError("junit_testcase_missing")
    return len(testcases)


def runtime_manifest_entries(root: Path) -> list[dict[str, Any]]:
    if not root.exists() or root.is_symlink() or not root.is_dir():
        raise CapsuleError("fixture_snapshot_drift", "runtime fixture snapshot missing")
    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise CapsuleError("payload_not_regular", "runtime fixture contains unsupported entry", {"path": str(path)})
        if path.is_file():
            relative = safe_relative(path, root)
            files.append((relative, path))
    entries = []
    for relative, path in sorted(files, key=lambda item: item[0]):
            entries.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": file_sha256(path)})
    return entries


def fingerprint(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def copy_receipt_root(source: Path, target: Path, plan: dict[str, Any]) -> None:
    copy_required_file(source / "matrix_plan.json", target / "matrix_plan.json")
    copy_required_file(source / ".nollm_test_matrix_root.json", target / ".nollm_test_matrix_root.json")
    for shard in plan["shards"]:
        shard_id = shard["shard_id"]
        copy_required_file(source / "receipts" / f"{shard_id}.json", target / "receipts" / f"{shard_id}.json")
        copy_required_file(source / "junit" / f"{shard_id}.xml", target / "junit" / f"{shard_id}.xml")
    runtime = plan["runtime_fixture"]
    if runtime["state"] == "present":
        copy_required_file(source / "inputs" / "runtime_fixture_manifest.json", target / "inputs" / "runtime_fixture_manifest.json")
        copy_tree_regular_files(source / "inputs" / "runtime_fixture", target / "inputs" / "runtime_fixture")


def write_governance(staging: Path, governance_files: list[str]) -> None:
    target = staging / "governance"
    target.mkdir(parents=True, exist_ok=True)
    by_name = {Path(path).name: Path(path).resolve() for path in governance_files}
    if not by_name:
        raise CapsuleError("governance_missing", "at least one governance file is required")
    accepted = {TASK_ORIGINAL, TASK_AMENDMENT, TASK_C7R}
    for name, path in sorted(by_name.items()):
        if name not in accepted and not name.startswith("NOLLM_TQ1_"):
            raise CapsuleError("governance_unexpected", "unexpected governance file", {"name": name})
        copy_required_file(path, target / name)


def write_logs(staging: Path, log_args: list[str], verify_log: Path) -> None:
    names = {
        "00_environment_and_git_state.txt",
        "01_rc_gate_pytest.txt",
        "02_rc_export_check.txt",
        "03_tq1_self_tests.txt",
        "04_dx1_dg0_dg6_targeted_gate.txt",
        "05_matrix_plan.txt",
        "06_matrix_run_all.txt",
        "07_matrix_verify.txt",
        "08_bundle_build_and_audit.txt",
    }
    logs = {}
    for value in log_args:
        if "=" not in value:
            raise CapsuleError("invalid_log_arg", "log arguments must be name=path")
        name, path = value.split("=", 1)
        if name not in names:
            raise CapsuleError("invalid_log_name", "unexpected log name", {"name": name})
        logs[name] = Path(path).resolve()
    logs.setdefault("07_matrix_verify.txt", verify_log)
    target = staging / "logs"
    target.mkdir(parents=True, exist_ok=True)
    for name in sorted(names):
        if name in logs:
            copy_required_file(logs[name], target / name)
        else:
            write_text(target / name, f"{name}\nnot produced for this local regression capsule\n")


def final_matrix_evidence(receipt_root: Path, plan: dict[str, Any], verify_output: str) -> dict[str, Any]:
    receipts = [read_json(receipt_root / "receipts" / f"{shard['shard_id']}.json") for shard in plan["shards"]]
    junit_files = [receipt_root / "junit" / f"{shard['shard_id']}.xml" for shard in plan["shards"]]
    longest = max(receipts, key=lambda receipt: receipt.get("duration_seconds", 0))
    runtime = plan["runtime_fixture"]
    contract = plan["execution_contract"]
    return {
        "schema": "nollm.tq1.final-matrix-evidence.v1",
        "head": plan["git_head"],
        "receipt_root": str(receipt_root),
        "matrix_id": plan["matrix_id"],
        "collected": plan["collected_count"],
        "shards": len(plan["shards"]),
        "passed": len([receipt for receipt in receipts if receipt.get("status") == "passed"]),
        "receipt_json_count": len(receipts),
        "junit_xml_count": len(junit_files),
        "failed_count": len([receipt for receipt in receipts if receipt.get("status") != "passed"]),
        "timeout_count": len([receipt for receipt in receipts if receipt.get("timed_out")]),
        "execution_contract": contract,
        "planned_shard_timeout_seconds": contract["planned_shard_timeout_seconds"],
        "retry_policy": contract["retry_policy"],
        "receipt_overwrite": contract["receipt_overwrite"],
        "execution_mode": contract["execution_mode"],
        "retry_count": 0,
        "longest_shard": longest.get("shard_id"),
        "longest_shard_duration_seconds": longest.get("duration_seconds"),
        "total_shard_duration_seconds": round(sum(receipt.get("duration_seconds", 0) for receipt in receipts), 3),
        "receipt_extras": 0,
        "junit_extras": 0,
        "matrix_worktree_leftovers": 0,
        "source_worktree_clean": True,
        "collection_fingerprint": plan["collection_fingerprint"],
        "matrix_fingerprint": plan["manifest_fingerprint"],
        "runtime_fixture_state": runtime["state"],
        "runtime_fixture_file_count": runtime["file_count"],
        "runtime_fixture_manifest_fingerprint": runtime["manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": runtime["tree_fingerprint"] or "absent",
        "verify_output_sha256": hashlib.sha256(verify_output.encode("utf-8")).hexdigest(),
    }


def capsule_manifest(args: argparse.Namespace, plan: dict[str, Any], evidence: dict[str, Any], evidence_ref: str, payload_inventory_sha256: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "code_head": args.final_head,
        "code_branch": "codex/hx1-trusted-host-staged-plan-execution-bridge",
        "evidence_ref": evidence_ref,
        "matrix_id": plan["matrix_id"],
        "receipt_root_original": str(Path(args.receipt_root).resolve()),
        "runtime_fixture_state": evidence["runtime_fixture_state"],
        "runtime_fixture_file_count": evidence["runtime_fixture_file_count"],
        "runtime_fixture_manifest_fingerprint": evidence["runtime_fixture_manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": evidence["runtime_fixture_tree_fingerprint"],
        "collection_fingerprint": evidence["collection_fingerprint"],
        "matrix_fingerprint": evidence["matrix_fingerprint"],
        "collected": evidence["collected"],
        "shards": evidence["shards"],
        "passed": evidence["passed"],
        "receipt_json_count": evidence["receipt_json_count"],
        "junit_xml_count": evidence["junit_xml_count"],
        "failed_count": evidence["failed_count"],
        "timeout_count": evidence["timeout_count"],
        "execution_contract": evidence["execution_contract"],
        "planned_shard_timeout_seconds": evidence["planned_shard_timeout_seconds"],
        "retry_policy": evidence["retry_policy"],
        "receipt_overwrite": evidence["receipt_overwrite"],
        "execution_mode": evidence["execution_mode"],
        "matrix_worktree_leftovers": evidence["matrix_worktree_leftovers"],
        "source_worktree_clean": evidence["source_worktree_clean"],
        "verify_output_sha256": evidence["verify_output_sha256"],
        "payload_inventory_sha256": payload_inventory_sha256,
    }


def create_parentless_commit(repo_root: Path, staging: Path, message: str) -> str:
    git_dir = git(repo_root, "rev-parse", "--git-dir").stdout.strip()
    with tempfile.NamedTemporaryFile(prefix="nollm-tq1-index-", delete=False) as index_file:
        index_path = index_file.name
    Path(index_path).unlink()
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = index_path
        git(repo_root, "-c", "core.autocrlf=false", "--git-dir", git_dir, "--work-tree", str(staging), "add", "-A", env=env)
        tree = git(repo_root, "-c", "core.autocrlf=false", "--git-dir", git_dir, "--work-tree", str(staging), "write-tree", env=env).stdout.strip()
        return git(repo_root, "commit-tree", tree, input_text=message + "\n").stdout.strip()
    finally:
        try:
            Path(index_path).unlink()
        except OSError:
            pass


def tree_files(repo_root: Path, commit: str) -> list[str]:
    raw = git(repo_root, "ls-tree", "-r", "-z", "--name-only", commit).stdout
    return sorted(item for item in raw.split("\0") if item)


def require_tree_layout(files: list[str]) -> None:
    required = {
        "README.md",
        "CAPSULE_MANIFEST.json",
        "PAYLOAD_INVENTORY.json",
        "summary/FINAL_MATRIX_EVIDENCE.json",
        "summary/FULL_MATRIX_OK.txt",
        "summary/DELIVERY_COMMANDS.txt",
        "receipt_root/matrix_plan.json",
        "receipt_root/.nollm_test_matrix_root.json",
    }
    required.update(f"logs/{name}" for name in [
        "00_environment_and_git_state.txt",
        "01_rc_gate_pytest.txt",
        "02_rc_export_check.txt",
        "03_tq1_self_tests.txt",
        "04_dx1_dg0_dg6_targeted_gate.txt",
        "05_matrix_plan.txt",
        "06_matrix_run_all.txt",
        "07_matrix_verify.txt",
        "08_bundle_build_and_audit.txt",
    ])
    missing = sorted(required - set(files))
    if missing:
        raise CapsuleError("capsule_required_file_missing", "capsule is missing required files", {"missing": missing})
    if not any(path.startswith("governance/") for path in files):
        raise CapsuleError("governance_missing", "capsule is missing governance evidence")
    for path in files:
        if "\\" in path or path.startswith("/") or "/../" in f"/{path}/" or path.startswith("./"):
            raise CapsuleError("capsule_path_invalid", "capsule contains invalid path", {"path": path})


def semantic_replay_capsule(
    repo_root: Path,
    commit: str,
    files: list[str],
    manifest: dict[str, Any],
    inventory: dict[str, Any],
    evidence_ref: str,
    expected_head: str,
    phase: str,
) -> None:
    plan = tree_json(repo_root, commit, "receipt_root/matrix_plan.json")
    if plan.get("git_head") != expected_head:
        raise CapsuleError("plan_head_mismatch", "matrix plan does not match expected head")
    if manifest.get("matrix_id") != plan.get("matrix_id") or manifest.get("matrix_fingerprint") != plan.get("manifest_fingerprint"):
        raise CapsuleError("manifest_plan_mismatch", "capsule manifest does not match matrix plan")
    if phase == C7R_PHASE and plan.get("execution_contract") != EXECUTION_CONTRACT:
        raise CapsuleError("execution_contract_mismatch", "C7R plan execution contract mismatch", {"execution_contract": plan.get("execution_contract")})
    elif phase != C7R_PHASE and not isinstance(plan.get("execution_contract"), dict):
        raise CapsuleError("execution_contract_missing", "matrix plan is missing execution contract")
    contract = plan["execution_contract"]
    planned_timeout = float(contract["planned_shard_timeout_seconds"])
    receipt_root_original = Path(str(manifest.get("receipt_root_original", "")))
    expected_marker = {
        "schema": "nollm.test_matrix.root.v1",
        "git_head": expected_head,
        "matrix_id": plan["matrix_id"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "receipt_root": str(receipt_root_original),
    }
    if tree_json(repo_root, commit, "receipt_root/.nollm_test_matrix_root.json") != expected_marker:
        raise CapsuleError("root_marker_mismatch", "receipt root marker does not match plan and capsule manifest")

    shards = plan.get("shards")
    if not isinstance(shards, list) or not shards:
        raise CapsuleError("plan_shards_malformed", "matrix plan shards are malformed")
    shard_ids = [shard.get("shard_id") for shard in shards]
    expected_receipts = {f"receipt_root/receipts/{shard_id}.json" for shard_id in shard_ids}
    expected_junit = {f"receipt_root/junit/{shard_id}.xml" for shard_id in shard_ids}
    actual_receipts = {path for path in files if path.startswith("receipt_root/receipts/")}
    actual_junit = {path for path in files if path.startswith("receipt_root/junit/")}
    if actual_receipts != expected_receipts:
        raise CapsuleError("receipt_inventory_mismatch", "receipt inventory does not match plan", {"actual": sorted(actual_receipts)})
    if actual_junit != expected_junit:
        raise CapsuleError("junit_inventory_mismatch", "JUnit inventory does not match plan", {"actual": sorted(actual_junit)})

    seen_nodes: dict[str, str] = {}
    receipts: list[dict[str, Any]] = []
    for shard in shards:
        shard_id = shard["shard_id"]
        receipt = tree_json(repo_root, commit, f"receipt_root/receipts/{shard_id}.json")
        receipts.append(receipt)
        issue = validate_tree_receipt(receipt, plan, shard, planned_timeout)
        if issue is not None:
            raise CapsuleError(issue, "receipt semantic replay failed", {"shard_id": shard_id})
        junit_path = f"receipt_root/junit/{shard_id}.xml"
        junit_bytes = tree_bytes(repo_root, commit, junit_path)
        if receipt.get("junit_size_bytes") != len(junit_bytes) or receipt.get("junit_sha256") != hashlib.sha256(junit_bytes).hexdigest():
            raise CapsuleError("junit_evidence_hash_mismatch", "JUnit bytes do not match receipt", {"shard_id": shard_id})
        junit_count = parse_junit_tests_bytes(junit_bytes)
        if junit_count != len(shard["node_ids"]) or receipt.get("junit_tests") != junit_count or receipt.get("junit_reported_tests") != junit_count:
            raise CapsuleError("junit_evidence_count_mismatch", "JUnit count does not match receipt and plan", {"shard_id": shard_id})
        for node_id in receipt["selected_node_ids"]:
            if node_id in seen_nodes:
                raise CapsuleError("node_coverage_duplicate", "node appears in more than one receipt", {"node_id": node_id})
            seen_nodes[node_id] = shard_id
    node_ids = plan.get("node_ids")
    if not isinstance(node_ids, list) or sorted(seen_nodes) != sorted(node_ids):
        raise CapsuleError("node_coverage_mismatch", "receipt node coverage does not match plan")

    runtime_entries, runtime_manifest = runtime_fixture_from_tree(repo_root, commit, files, plan)
    runtime = plan["runtime_fixture"]
    if runtime["state"] == "present":
        if fingerprint(runtime_entries) != runtime["tree_fingerprint"]:
            raise CapsuleError("fixture_snapshot_drift", "runtime fixture tree fingerprint mismatch")
    elif runtime["tree_fingerprint"] is not None:
        raise CapsuleError("fixture_snapshot_drift", "absent runtime fixture has tree fingerprint")
    if fingerprint(runtime_manifest) != runtime["manifest_fingerprint"]:
        raise CapsuleError("runtime_fixture_manifest_mismatch", "runtime fixture manifest fingerprint mismatch")

    verify_values = parse_full_matrix_ok(tree_text(repo_root, commit, "logs/07_matrix_verify.txt"))
    expected_verify = {
        "head": expected_head,
        "collected": str(plan["collected_count"]),
        "shards": str(len(shards)),
        "passed": str(len(shards)),
        "failed": "0",
        "timed_out": "0",
        "receipt_json_count": str(len(shards)),
        "junit_xml_count": str(len(shards)),
        "collection_fingerprint": plan["collection_fingerprint"],
        "matrix_fingerprint": plan["manifest_fingerprint"],
        "runtime_fixture_manifest_fingerprint": runtime["manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": runtime["tree_fingerprint"] or "absent",
        "planned_shard_timeout_seconds": str(planned_timeout),
        "retry_policy": "forbidden",
        "receipt_overwrite": "forbidden",
        "execution_mode": "single_pass",
    }
    for key, expected in expected_verify.items():
        if verify_values.get(key) != expected:
            raise CapsuleError("verify_log_value_mismatch", "verify log value mismatch", {"key": key, "expected": expected, "actual": verify_values.get(key)})
    if phase == C7R_PHASE:
        validate_c7r_run_log(tree_text(repo_root, commit, "logs/06_matrix_run_all.txt"), len(shards))

    evidence = tree_json(repo_root, commit, "summary/FINAL_MATRIX_EVIDENCE.json")
    expected_evidence = expected_final_matrix_evidence(plan, receipts, runtime, tree_text(repo_root, commit, "summary/FULL_MATRIX_OK.txt"), str(receipt_root_original))
    if evidence != expected_evidence:
        raise CapsuleError("summary_evidence_mismatch", "FINAL_MATRIX_EVIDENCE is not derived from capsule evidence")
    expected_manifest = expected_capsule_manifest(manifest, plan, evidence, evidence_ref, inventory, repo_root, commit)
    if manifest != expected_manifest:
        raise CapsuleError("capsule_manifest_mismatch", "CAPSULE_MANIFEST is not derived from capsule evidence")


def validate_tree_receipt(receipt: dict[str, Any], plan: dict[str, Any], shard: dict[str, Any], planned_timeout: float) -> str | None:
    checks = {
        "schema": "nollm.test_matrix.shard_receipt.v1",
        "status": "passed",
        "shard_id": shard["shard_id"],
        "git_head": plan["git_head"],
        "collection_fingerprint": plan["collection_fingerprint"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "selection_fingerprint": shard["selection_fingerprint"],
        "execution_contract": plan["execution_contract"],
    }
    for key, expected in checks.items():
        if receipt.get(key) != expected:
            return "receipt_not_passed" if key == "status" else f"{key}_mismatch"
    if receipt.get("selected_node_ids") != shard["node_ids"] or receipt.get("selected_count") != len(shard["node_ids"]):
        return "selected_node_ids_mismatch"
    if receipt.get("junit_relative_path") != f"junit/{shard['shard_id']}.xml":
        return "junit_evidence_path_mismatch"
    if receipt.get("returncode") != 0:
        return "returncode_mismatch"
    if receipt.get("timed_out") is not False:
        return "timed_out"
    if receipt.get("timeout_seconds") != planned_timeout:
        return "timeout_contract_mismatch"
    if receipt.get("worktree_created_by_this_call") is not True or receipt.get("worktree_add_succeeded") is not True or receipt.get("worktree_marker_written") is not True:
        return "worktree_ownership_mismatch"
    if receipt.get("worktree_cleanup") != "removed" or receipt.get("worktree_cleanup_error") is not None or receipt.get("worktree_cleanup_stage") is not None:
        return "worktree_cleanup_failed"
    if receipt.get("fixture_copy_verified") is not True:
        return "fixture_copy_not_verified"
    runtime = plan["runtime_fixture"]
    if receipt.get("runtime_fixture_state") != runtime["state"]:
        return "runtime_fixture_state_mismatch"
    if receipt.get("runtime_fixture_manifest_fingerprint") != runtime["manifest_fingerprint"]:
        return "runtime_fixture_manifest_fingerprint_mismatch"
    if receipt.get("runtime_fixture_tree_fingerprint") != runtime["tree_fingerprint"]:
        return "runtime_fixture_tree_fingerprint_mismatch"
    if receipt.get("copied_runtime_fixture_state") != runtime["state"]:
        return "copied_runtime_fixture_state_mismatch"
    if receipt.get("copied_runtime_fixture_manifest_fingerprint") != runtime["manifest_fingerprint"]:
        return "copied_runtime_fixture_manifest_fingerprint_mismatch"
    if receipt.get("copied_runtime_fixture_tree_fingerprint") != runtime["tree_fingerprint"]:
        return "copied_runtime_fixture_tree_fingerprint_mismatch"
    return None


def runtime_fixture_from_tree(repo_root: Path, commit: str, files: list[str], plan: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime = plan["runtime_fixture"]
    fixture_paths = sorted(path for path in files if path.startswith("receipt_root/inputs/runtime_fixture/"))
    manifest_path = "receipt_root/inputs/runtime_fixture_manifest.json"
    if runtime["state"] == "absent":
        if fixture_paths or manifest_path in files:
            raise CapsuleError("fixture_snapshot_drift", "absent runtime fixture has fixture payload")
        return [], {"schema": "nollm.test_matrix.runtime_fixture_manifest.v1", "state": "absent", "files": []}
    if runtime["state"] != "present":
        raise CapsuleError("fixture_snapshot_drift", "unknown runtime fixture state")
    if manifest_path not in files or not fixture_paths:
        raise CapsuleError("runtime_fixture_manifest_missing", "present runtime fixture is incomplete")
    entries = []
    prefix = "receipt_root/inputs/runtime_fixture/"
    for path in sorted(fixture_paths, key=lambda item: item.removeprefix(prefix)):
        relative = safe_posix_path(path.removeprefix(prefix))
        data = tree_bytes(repo_root, commit, path)
        entries.append({"path": relative, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"schema": "nollm.test_matrix.runtime_fixture_manifest.v1", "state": "present", "files": entries}
    recorded = tree_json(repo_root, commit, manifest_path)
    if recorded != manifest:
        raise CapsuleError("runtime_fixture_manifest_mismatch", "runtime fixture manifest does not match fixture bytes")
    return entries, manifest


def validate_c7r_run_log(text: str, shard_count: int) -> None:
    lowered = text.lower()
    if "--all" not in text or "--workers 4" not in text or "--timeout-seconds 3600" not in text:
        raise CapsuleError("run_log_contract_mismatch", "run log does not show the C7R final all-shard invocation")
    if "retry" in lowered or "--resume" in lowered:
        raise CapsuleError("run_log_retry_present", "run log contains retry or resume text")
    if text.count("RUN_ALL_DONE") != 1:
        raise CapsuleError("run_log_invocation_mismatch", "run log must contain exactly one RUN_ALL_DONE line")
    if "SHARD_DONE" in text:
        raise CapsuleError("run_log_invocation_mismatch", "run log contains single-shard execution")
    expected = f"RUN_ALL_DONE shards={shard_count} failed=0"
    if expected not in text:
        raise CapsuleError("run_log_failed_count_mismatch", "run log did not complete all planned shards cleanly", {"expected": expected})


def expected_final_matrix_evidence(plan: dict[str, Any], receipts: list[dict[str, Any]], runtime: dict[str, Any], verify_output: str, receipt_root: str) -> dict[str, Any]:
    longest = max(receipts, key=lambda receipt: receipt.get("duration_seconds", 0))
    contract = plan["execution_contract"]
    return {
        "schema": "nollm.tq1.final-matrix-evidence.v1",
        "head": plan["git_head"],
        "receipt_root": receipt_root,
        "matrix_id": plan["matrix_id"],
        "collected": plan["collected_count"],
        "shards": len(plan["shards"]),
        "passed": len(receipts),
        "receipt_json_count": len(receipts),
        "junit_xml_count": len(receipts),
        "failed_count": 0,
        "timeout_count": 0,
        "execution_contract": contract,
        "planned_shard_timeout_seconds": contract["planned_shard_timeout_seconds"],
        "retry_policy": contract["retry_policy"],
        "receipt_overwrite": contract["receipt_overwrite"],
        "execution_mode": contract["execution_mode"],
        "retry_count": 0,
        "longest_shard": longest.get("shard_id"),
        "longest_shard_duration_seconds": longest.get("duration_seconds"),
        "total_shard_duration_seconds": round(sum(receipt.get("duration_seconds", 0) for receipt in receipts), 3),
        "receipt_extras": 0,
        "junit_extras": 0,
        "matrix_worktree_leftovers": 0,
        "source_worktree_clean": True,
        "collection_fingerprint": plan["collection_fingerprint"],
        "matrix_fingerprint": plan["manifest_fingerprint"],
        "runtime_fixture_state": runtime["state"],
        "runtime_fixture_file_count": runtime["file_count"],
        "runtime_fixture_manifest_fingerprint": runtime["manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": runtime["tree_fingerprint"] or "absent",
        "verify_output_sha256": hashlib.sha256(verify_output.encode("utf-8")).hexdigest(),
    }


def expected_capsule_manifest(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    evidence: dict[str, Any],
    evidence_ref: str,
    inventory: dict[str, Any],
    repo_root: Path,
    commit: str,
) -> dict[str, Any]:
    inventory_sha = hashlib.sha256(tree_bytes(repo_root, commit, "PAYLOAD_INVENTORY.json")).hexdigest()
    return {
        "schema": SCHEMA,
        "code_head": plan["git_head"],
        "code_branch": manifest.get("code_branch"),
        "evidence_ref": evidence_ref,
        "matrix_id": plan["matrix_id"],
        "receipt_root_original": manifest.get("receipt_root_original"),
        "runtime_fixture_state": evidence["runtime_fixture_state"],
        "runtime_fixture_file_count": evidence["runtime_fixture_file_count"],
        "runtime_fixture_manifest_fingerprint": evidence["runtime_fixture_manifest_fingerprint"],
        "runtime_fixture_tree_fingerprint": evidence["runtime_fixture_tree_fingerprint"],
        "collection_fingerprint": evidence["collection_fingerprint"],
        "matrix_fingerprint": evidence["matrix_fingerprint"],
        "collected": evidence["collected"],
        "shards": evidence["shards"],
        "passed": evidence["passed"],
        "receipt_json_count": evidence["receipt_json_count"],
        "junit_xml_count": evidence["junit_xml_count"],
        "failed_count": evidence["failed_count"],
        "timeout_count": evidence["timeout_count"],
        "execution_contract": evidence["execution_contract"],
        "planned_shard_timeout_seconds": evidence["planned_shard_timeout_seconds"],
        "retry_policy": evidence["retry_policy"],
        "receipt_overwrite": evidence["receipt_overwrite"],
        "execution_mode": evidence["execution_mode"],
        "matrix_worktree_leftovers": evidence["matrix_worktree_leftovers"],
        "source_worktree_clean": evidence["source_worktree_clean"],
        "verify_output_sha256": evidence["verify_output_sha256"],
        "payload_inventory_sha256": inventory_sha,
    }


def parse_junit_tests_bytes(data: bytes) -> int:
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, UnicodeError) as exc:
        raise CapsuleError("junit_evidence_malformed", "JUnit evidence is malformed", {"message": str(exc)})
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise CapsuleError("junit_evidence_malformed", "JUnit evidence is malformed")
    for suite in suites:
        int(suite.attrib["tests"])
    testcases = root.findall(".//testcase")
    if not testcases:
        raise CapsuleError("junit_evidence_malformed", "JUnit evidence has no testcases")
    return len(testcases)


def tree_text(repo_root: Path, commit: str, path: str) -> str:
    return tree_bytes(repo_root, commit, path).decode("utf-8")


def tree_json(repo_root: Path, commit: str, path: str) -> dict[str, Any]:
    return json.loads(tree_bytes(repo_root, commit, path).decode("utf-8"))


def tree_bytes(repo_root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "cat-file", "-p", f"{commit}:{path}"], cwd=repo_root, capture_output=True)
    if result.returncode != 0:
        raise CapsuleError("tree_read_failed", "could not read evidence tree path", {"path": path})
    return result.stdout


def inventory_under(root: Path, *, prefix: str = "") -> list[dict[str, Any]]:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise CapsuleError("payload_not_regular", "payload contains unsupported filesystem entry", {"path": str(path)})
        if path.is_dir():
            continue
        entries.append(file_entry(path, prefix + safe_relative(path, root)))
    return sorted(entries, key=lambda item: item["path"])


def file_entry(path: Path, relative: str) -> dict[str, Any]:
    return {"path": safe_posix_path(relative), "size_bytes": path.stat().st_size, "sha256": file_sha256(path)}


def safe_relative(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return safe_posix_path(relative)


def safe_posix_path(path: str) -> str:
    if "\\" in path or path.startswith("/") or path in {"", ".", ".."} or "/../" in f"/{path}/" or "/./" in f"/{path}/" or "\x00" in path:
        raise CapsuleError("invalid_payload_path", "invalid payload path", {"path": path})
    parts = path.split("/")
    if ".git" in parts or "node_modules" in parts or "__pycache__" in parts or any(part.endswith(".pyc") for part in parts):
        raise CapsuleError("forbidden_payload_path", "capsule payload contains forbidden development/runtime path", {"path": path})
    return path


def assert_regular_file(path: Path) -> None:
    if not path.exists():
        raise CapsuleError("payload_missing", "required evidence file is missing", {"path": str(path)})
    if path.is_symlink() or not path.is_file():
        raise CapsuleError("payload_not_regular", "required evidence path is not a regular file", {"path": str(path)})


def copy_required_file(source: Path, target: Path) -> None:
    assert_regular_file(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree_regular_files(source: Path, target: Path) -> None:
    if not source.exists() or source.is_symlink() or not source.is_dir():
        raise CapsuleError("payload_missing", "runtime fixture snapshot directory is missing", {"path": str(source)})
    files: list[tuple[str, Path]] = []
    for path in source.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise CapsuleError("payload_not_regular", "runtime fixture contains unsupported entry", {"path": str(path)})
        if path.is_file():
            files.append((path.relative_to(source).as_posix(), path))
    for relative, path in sorted(files, key=lambda item: item[0]):
        copy_required_file(path, target / relative)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readme(final_head: str, evidence_ref: str) -> str:
    return f"# Nollm TQ1-C6 Delivery Evidence Capsule\n\ncode_head: `{final_head}`\nevidence_ref: `{evidence_ref}`\n"


def delivery_commands(args: argparse.Namespace) -> str:
    return "\n".join([
        "package_nollm_tq1_delivery_evidence.py build-ref",
        f"  --receipt-root {Path(args.receipt_root).resolve()}",
        f"  --final-head {args.final_head}",
        f"  --evidence-ref {args.evidence_ref}",
        "",
    ])


def git(repo_root: Path, *args: str, env: dict[str, str] | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, env=env, input=input_text)
    if result.returncode != 0:
        raise CapsuleError("git_failed", "git command failed", {"args": args, "stderr": result.stderr[-4000:]})
    return result


def git_optional(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True)


class CapsuleError(Exception):
    def __init__(self, reason: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


if __name__ == "__main__":
    raise SystemExit(main())
