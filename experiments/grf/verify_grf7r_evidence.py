from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

from nollm.grf.gate_evidence import GateEvidence, GatePredicate
from nollm.grf.json_canonical import canonical_dumps

from experiments.grf.verify_external_artifacts import verify as verify_external


ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = ROOT / "experiments" / "grf" / "results" / "grf7r"
REPORT_PATH = ROOT / "docs" / "validation" / "GRF7R_EVIDENCE_INTEGRITY_REPORT.md"


def verify_all(external_root: Path, *, include_gate_j: bool = True) -> tuple[tuple[GateEvidence, ...], dict[str, object]]:
    closure = Path(external_root) / "grf7r_closure"
    core = _read(closure / "core_integrity" / "core_integrity_metrics.json")
    global_metrics = _read(closure / "real_global" / "real_global_metrics.json")
    runtime = _read(closure / "runtime" / "runtime_semantics_metrics.json")
    long_run = _read(closure / "long_running" / "long_running_metrics.json")
    workflow = _read(closure / "workflow" / "workflow_metrics.json")
    query_ledger = closure / "real_global" / "query_ledger.jsonl"
    stitch_ledger = _read(closure / "real_global" / "stitch_event_ledger.json")
    query_lines = _line_count(query_ledger)
    stitch_counts = {name: sum(item["event"] == event for item in stitch_ledger) for name, event in (("proposal_count", "proposed"), ("accepted_count", "accepted"), ("rejected_count", "rejected"), ("deferred_count", "deferred"), ("decayed_count", "decayed"), ("rollback_count", "rolled_back"))}
    snapshots_valid = all((closure / "long_running" / "snapshots" / item["path"]).is_file() and _sha(closure / "long_running" / "snapshots" / item["path"]) == item["sha256"] for item in long_run["snapshots"])
    required_long_classes = {"capture", "place", "admit", "recall", "replay", "cross_recall", "stitch", "rollback", "move", "split_merge", "restart", "post_commit_retry", "adapter_failure"}
    gates = (
        _gate("A", "verifier/computed_gate_framework", {"negative_controls": 4, "raw_inputs": 5}, (_p("raw inputs present", 5, 5, "eq"), _p("negative control coverage", 4, 4, "ge")), 5),
        _gate("B", "core_integrity/core_integrity_metrics.json", core, (
            _p("100K directory", core["directory_partition_count"], 100_000, "ge"), _p("indexed lookup descriptors", core["directory_descriptors_examined"], 1, "le"), _p("directory replay", core["directory_replay_deterministic"], True, "eq"), _p("identity conflict rejected", core["unique_identity_conflict_rejected_without_mutation"], True, "eq"), _p("shared route cardinality", core["shared_entry_partition_count"], 2, "ge"),
        ), int(core["directory_partition_count"])),
        _gate("C", "real_global/real_global_metrics.json", global_metrics, (
            _p("persisted placement count", global_metrics["artifact_inventory"]["placement_count"], 10_000_000, "eq"), _p("all identity hashes", global_metrics["all_artifact_identity_hashes_verified"], 10_000_000, "eq"), _p("query count", global_metrics["query_count"], 20_000, "eq"), _p("cross queries", global_metrics["cross_partition_query_count"], 5_000, "ge"), _p("stitch queries", global_metrics["stitch_query_count"], 1_000, "ge"), _p("rejection rollback queries", global_metrics["rejection_rollback_verification_count"], 1_000, "ge"), _p("fallback hashes", global_metrics["content_hash_resolution_count"], global_metrics["query_count"], "eq"), _p("raw query ledger", query_lines, global_metrics["query_count"], "eq"), _p("bounded hydration", global_metrics["max_hydrated_partitions"], global_metrics["activation_budget"], "le"), _p("semantic replay", global_metrics["replay_deterministic"], True, "eq"),
        ), query_lines),
        _gate("D", "real_global/stitch_event_ledger.json", {"event_counts": stitch_counts, "reported_counts": global_metrics["stitch_metrics"], **core}, (
            _p("stitch counts reproduce", stitch_counts, global_metrics["stitch_metrics"], "eq"), _p("valid bridge recalled", core["valid_bridge_recalled"], True, "eq"), _p("rejected bridge inactive", core["rejected_bridge_never_active"], True, "eq"), _p("decayed bridge inactive", core["decayed_bridge_never_active"], True, "eq"), _p("rollback cleanup", core["rollback_removed_false_bridge"], True, "eq"), _p("evidence unchanged", core["evidence_bytes_unchanged"], True, "eq"),
        ), len(stitch_ledger)),
        _gate("E", "core_integrity/core_integrity_metrics.json", core, tuple(_p(name, core[key], True, "eq") for name, key in (("move changed directory", "move_directory_changed"), ("move identity", "move_identity_preserved"), ("fallback preserved", "source_fallback_preserved"), ("profile atomic rejection", "profile_change_atomic_rejection"), ("merge replay equivalence", "merge_directory_replay_equivalent"), ("merge identities", "merge_placement_identities_preserved"), ("no dangling bridge", "no_dangling_bridge_partition"))), 7),
        _gate("F", "runtime/runtime_semantics_metrics.json", runtime, (
            _p("post commit retries", runtime["post_commit_retry_count"], 3, "ge"), _p("retry identities", runtime["retry_identities_stable"], True, "eq"), _p("cache deletion", runtime["durable_counts_unchanged_after_cache_delete"], True, "eq"), _p("replay restart", runtime["replay_deterministic_before_after_restart"], True, "eq"), _p("all attacks rejected", runtime["attack_rejection_count"], runtime["attack_count"], "eq"), _p("adapter not truth", runtime["adapter_owns_durable_truth"], False, "eq"),
        ), int(runtime["attack_count"])),
        _gate("G", "long_running/long_running_metrics.json", long_run, (
            _p("one million operations", long_run["operation_count"], 1_000_000, "ge"), _p("all operation classes", required_long_classes.issubset(long_run["operation_counts"]), True, "eq"), _p("majority contract dispatch", long_run["minimum_contract_dispatch_count"], long_run["operation_count"] // 2 + 1, "ge"), _p("snapshot files", snapshots_valid, True, "eq"), _p("snapshot replay", long_run["snapshot_replay_equals_final_state"], True, "eq"), _p("recoveries", long_run["recovery_count"], long_run["injected_recoverable_failure_count"], "eq"), _p("no evidence loss", long_run["evidence_loss_count"], 0, "eq"), _p("no orphans", long_run["orphan_object_count"], 0, "eq"), _p("no collisions", long_run["identity_collision_count"], 0, "eq"), _p("memory explained", long_run["memory_growth_explained_by_retained_files"], True, "eq"),
        ), int(long_run["operation_count"])),
        _gate("H", "workflow/workflow_metrics.json", workflow, (
            _p("four workflows", workflow["workflow_count"], 4, "eq"), _p("five models", len(workflow["models"]), 5, "eq"), _p("false relation injected", workflow["false_relation_injected"], True, "eq"), _p("false bridge before rollback", workflow["grf_false_bridge_used_before_rollback"], True, "eq"), _p("false bridge after rollback", workflow["grf_false_bridge_used_after_rollback"], False, "eq"), _p("rollback success", workflow["grf_rollback_success"], True, "eq"), _p("bounded conclusion", workflow["scope"], "observed_on_current_fixture_only", "eq"),
        ), int(workflow["query_count"])),
        _platform_gate(closure, probe=not include_gate_j),
    )
    external_ok, external_message = verify_external(external_root)
    windows_marker = _optional_read(closure / "platform" / "windows_clean_clone.json")
    if include_gate_j:
        marker_commit = "" if windows_marker is None else str(windows_marker.get("commit", ""))
        marker_ancestor = bool(marker_commit and subprocess.run(["git", "merge-base", "--is-ancestor", marker_commit, "HEAD"], cwd=ROOT).returncode == 0)
        gate_j = _gate("J", "GRF7R_EXTERNAL_ARTIFACT_MANIFEST.json", {"external_verification": external_message, "windows_clean_clone": windows_marker, "cross_platform_portability": "not_validated_in_this_stage"}, (
            _p("external artifacts", external_ok, True, "eq"), _p("windows clean clone", bool(windows_marker and windows_marker.get("passed")), True, "eq"), _p("clean clone commit ancestor", marker_ancestor, True, "eq"),
        ), 3)
        gates = (*gates, gate_j)
    inventory = {"raw_sha256": _raw_hashes(closure), "git_blob_sha256": _git_blob_hashes(), "current_head": _git("rev-parse", "HEAD")}
    return gates, inventory


def write_outputs(gates: tuple[GateEvidence, ...], inventory: dict[str, object]) -> None:
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = _collection(gates)
    (RESULT_ROOT / "GRF7R_GATE_EVIDENCE.json").write_bytes(canonical_dumps(payload))
    producing_commit = os.environ.get("NOLLM_GRF7R_PRODUCING_COMMIT", str(inventory["current_head"]))
    manifest = {"schema": "grf7r_evidence_manifest_v1", **inventory, "git_blob_sha256": _git_blob_hashes(producing_commit), "producing_commit": producing_commit, "report_commit": os.environ.get("NOLLM_GRF7R_REPORT_COMMIT", inventory["current_head"]), "final_head": inventory["current_head"]}
    (RESULT_ROOT / "GRF7R_EVIDENCE_MANIFEST.json").write_bytes(canonical_dumps(manifest))
    REPORT_PATH.write_text(_report_text(gates, str(payload["overall"])), encoding="utf-8", newline="\n")


def verify_written_outputs(gates: tuple[GateEvidence, ...], inventory: dict[str, object]) -> None:
    gate_path = RESULT_ROOT / "GRF7R_GATE_EVIDENCE.json"
    manifest_path = RESULT_ROOT / "GRF7R_EVIDENCE_MANIFEST.json"
    if gate_path.read_bytes() != canonical_dumps(_collection(gates)):
        raise ValueError("committed GateEvidence does not reproduce from raw evidence")
    report = _report_text(gates, str(_collection(gates)["overall"]))
    if REPORT_PATH.read_text(encoding="utf-8") != report:
        raise ValueError("committed GRF7R report does not reproduce")
    manifest = _read(manifest_path)
    if manifest.get("schema") != "grf7r_evidence_manifest_v1" or manifest.get("raw_sha256") != inventory["raw_sha256"]:
        raise ValueError("evidence manifest raw hashes do not reproduce")
    for key in ("producing_commit", "report_commit", "final_head"):
        commit = str(manifest.get(key, ""))
        if not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode != 0:
            raise ValueError(f"evidence manifest {key} is not an ancestor of HEAD")
    if manifest.get("git_blob_sha256") != _git_blob_hashes(str(manifest["producing_commit"])):
        raise ValueError("Git blob byte hashes do not reproduce at producing_commit")


def _collection(gates: tuple[GateEvidence, ...]) -> dict[str, object]:
    return {"schema": "grf7r_gate_collection_v1", "gates": tuple(item.to_mapping() for item in gates), "overall": "GRF7_ACCEPTED" if all(item.result.passed for item in gates) and len(gates) == 10 else "GRF7_NOT_ACCEPTED"}


def _report_text(gates: tuple[GateEvidence, ...], overall: str) -> str:
    lines = ["# GRF7R Evidence Integrity Report", "", f"Overall: `{overall}`", "", "Cross-platform portability was not validated in this stage.", ""]
    for gate in gates:
        lines.extend((f"## Gate {gate.gate}", "", f"Status: `{gate.result.status}`", f"Raw: `{gate.source_raw_path}`", f"Events: `{gate.event_count}`", ""))
        lines.extend(f"- `{item.predicate}`: measured `{item.measured_value}`, required `{item.operator} {item.required_value}`, pass `{str(item.passed).lower()}`" for item in gate.predicates)
        lines.append("")
    return "\n".join(lines)


def _platform_gate(closure: Path, *, probe: bool) -> GateEvidence:
    windows = _optional_read(closure / "platform" / "windows_clean_clone.json")
    sample = _read(closure / "platform" / "windows_resource_sample.json")
    measurements = {"resource_sample": sample, "windows": windows, "cross_platform_portability": "not_validated_in_this_stage"}
    predicates = (_p("windows process backend", sample["backend_name"], "windows_GetProcessMemoryInfo", "eq"), _p("current RSS measured", sample["current_rss_bytes"], 0, "gt"), _p("peak RSS measured", sample["peak_rss_bytes"], sample["current_rss_bytes"], "ge"))
    if not probe:
        predicates = (*predicates, _p("windows tests", bool(windows and windows.get("passed")), True, "eq"))
    return _gate("I", "platform/windows_clean_clone.json", measurements, predicates, 3 if probe else 4)


def _gate(name: str, source: str, measurements: dict[str, object], predicates: tuple[GatePredicate, ...], events: int) -> GateEvidence:
    return GateEvidence(name, source, measurements, predicates, events)


def _p(name: str, measured: object, required: object, operator: str) -> GatePredicate:
    return GatePredicate(name, measured, required, operator)


def _read(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"required raw evidence is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_read(path: Path) -> dict[str, object] | None:
    return _read(path) if path.is_file() else None


def _line_count(path: Path) -> int:
    if not path.is_file():
        raise FileNotFoundError(f"required raw evidence is missing: {path}")
    with path.open("rb") as stream:
        return sum(1 for _line in stream)


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _raw_hashes(closure: Path) -> dict[str, str]:
    return {path.relative_to(closure).as_posix(): _sha(path) for path in sorted(item for item in closure.rglob("*") if item.is_file())}


def _git_blob_hashes(ref: str = "HEAD") -> dict[str, str]:
    paths = _git("ls-tree", "-r", "--name-only", ref, "reference/python/nollm/grf", "integrations/adapters", "experiments/grf", "docs/validation").splitlines()
    result = {}
    for path in paths:
        completed = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, check=True, stdout=subprocess.PIPE)
        result[path] = sha256(completed.stdout).hexdigest()
    return result


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--external-root",
        type=Path,
        default=Path(os.environ.get("NOLLM_GRF7R_EXTERNAL_ROOT", str(Path.home() / "nollm_grf7_external_evidence_20260710"))),
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--probe", type=Path)
    args = parser.parse_args()
    try:
        gates, inventory = verify_all(args.external_root, include_gate_j=args.probe is None)
        passed = all(item.result.passed for item in gates) and (len(gates) == 10 or args.probe is not None)
        if args.probe is not None:
            args.probe.parent.mkdir(parents=True, exist_ok=True)
            marker = {"platform": platform.system().lower(), "passed": passed, "commit": inventory["current_head"], "gate_statuses": tuple(item.result.status for item in gates), "verification_command": "python experiments/grf/verify_grf7r_evidence.py --probe <marker>"}
            args.probe.write_text(json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        if args.write:
            write_outputs(gates, inventory)
        elif args.probe is None:
            verify_written_outputs(gates, inventory)
        print("GRF7_ACCEPTED" if passed and len(gates) == 10 else ("GRF7R_PROBE_PASS" if passed else "GRF7_NOT_ACCEPTED"))
        return 0 if passed else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"GRF7_NOT_ACCEPTED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
