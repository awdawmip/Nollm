"""Validate the committed OCP3b strict live E2E evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "README.md",
    "run_manifest.json",
    "environment.json",
    "runtime_plugin_inspect.json",
    "config_control_proof.json",
    "fixture_hashes_before.json",
    "fixture_hashes_after.json",
    "agent_turn_summary.json",
    "tool_trace_summary.jsonl",
    "gateway_log_excerpt.txt",
    "memory_core_repair.json",
    "scoring_report.json",
    "evidence_manifest.json",
}

BASELINE_TASKS = {"B1", "B2", "B3", "B4"}
NOLLM_REQUIRED_TASKS = {"N5", "N7"}
DIRECT_READ_TOOLS = {"read"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{line_number}: expected object row")
        rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = evidence_dir / "evidence_manifest.json"
    manifest = load_json(manifest_path)
    files = manifest.get("files")
    if not isinstance(files, list):
        return ["evidence_manifest.json files must be a list"]
    seen = set()
    for item in files:
        rel = item.get("path")
        expected = item.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            errors.append("evidence_manifest.json file entries require path and sha256")
            continue
        seen.add(rel)
        if rel == "evidence_manifest.json":
            errors.append("evidence_manifest.json must not hash itself")
            continue
        target = evidence_dir / rel
        if not target.exists():
            errors.append(f"manifest entry missing file: {rel}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            errors.append(f"hash mismatch for {rel}: expected {expected}, got {actual}")
    for required in sorted(REQUIRED_FILES - {"evidence_manifest.json"}):
        if required not in seen:
            errors.append(f"manifest missing required file: {required}")
    if manifest.get("self_hash_excluded") is not True:
        errors.append("evidence_manifest.json must declare self_hash_excluded=true")
    return errors


def validate_turns(evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    turns = load_json(evidence_dir / "agent_turn_summary.json")
    if not isinstance(turns, list):
        return ["agent_turn_summary.json must be a list"]
    by_task = {turn.get("task_id"): turn for turn in turns if isinstance(turn, dict)}

    for task_id in sorted(BASELINE_TASKS):
        turn = by_task.get(task_id)
        if not turn:
            errors.append(f"missing baseline task {task_id}")
            continue
        if turn.get("condition") != "baseline":
            errors.append(f"{task_id} condition must be baseline")
        if turn.get("status") != "pass":
            errors.append(f"{task_id} must pass")
        tools = turn.get("tool_names") or []
        if "memory_search" not in tools or "memory_get" not in tools:
            errors.append(f"{task_id} must include memory_search and memory_get")
        if set(tools) & DIRECT_READ_TOOLS or turn.get("read_called") is not False:
            errors.append(f"{task_id} has direct-read contamination")
        if turn.get("context_injection_count") != 0:
            errors.append(f"{task_id} has context injection contamination")

    for task_id in sorted(NOLLM_REQUIRED_TASKS):
        turn = by_task.get(task_id)
        if not turn:
            errors.append(f"missing Nollm-required task {task_id}")
            continue
        tools = turn.get("tool_names") or []
        if "memory_search" not in tools or "memory_get" not in tools:
            errors.append(f"{task_id} must include memory-core trace")
        required_nollm_tool = "nollm_memory_write_candidate" if task_id == "N7" else "nollm_memory_get"
        if "nollm_memory_search" not in tools and task_id != "N7":
            errors.append(f"{task_id} must include nollm_memory_search")
        if required_nollm_tool not in tools:
            errors.append(f"{task_id} must include {required_nollm_tool}")
        if set(tools) & DIRECT_READ_TOOLS or turn.get("read_called") is not False:
            errors.append(f"{task_id} has direct-read contamination")
        if turn.get("context_injection_count") != 0:
            errors.append(f"{task_id} has context injection contamination")

    traces = load_jsonl(evidence_dir / "tool_trace_summary.jsonl")
    trace_tasks = {row.get("task_id") for row in traces}
    for task_id in sorted(BASELINE_TASKS | NOLLM_REQUIRED_TASKS):
        if task_id not in trace_tasks:
            errors.append(f"missing tool trace row for {task_id}")
    if any(row.get("tool_name") == "read" for row in traces):
        errors.append("tool trace includes direct read tool")

    scoring = load_json(evidence_dir / "scoring_report.json")
    if scoring.get("direct_read_contamination_count") != 0:
        errors.append("direct_read_contamination_count must be 0")
    if scoring.get("context_injection_contamination_count") != 0:
        errors.append("context_injection_contamination_count must be 0")
    if scoring.get("source_mutation_result") != "unchanged":
        errors.append("source_mutation_result must be unchanged")
    if scoring.get("integration") not in {"supported", "not_supported", "inconclusive", "blocked"}:
        errors.append("integration conclusion must use allowed vocabulary")
    if scoring.get("safety") not in {"supported", "not_supported", "inconclusive", "blocked"}:
        errors.append("safety conclusion must use allowed vocabulary")
    if scoring.get("value_hypothesis") not in {"supported", "not_supported", "inconclusive", "blocked"}:
        errors.append("value_hypothesis conclusion must use allowed vocabulary")
    return errors


def validate_hashes(evidence_dir: Path) -> list[str]:
    before = load_json(evidence_dir / "fixture_hashes_before.json")
    after = load_json(evidence_dir / "fixture_hashes_after.json")
    if before != after:
        return ["fixture_hashes_before.json must equal fixture_hashes_after.json"]
    return []


def validate_evidence(evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    if not evidence_dir.exists():
        return [f"evidence directory does not exist: {evidence_dir}"]
    missing = sorted(name for name in REQUIRED_FILES if not (evidence_dir / name).exists())
    errors.extend(f"missing required file: {name}" for name in missing)
    if missing:
        return errors
    errors.extend(validate_manifest(evidence_dir))
    errors.extend(validate_hashes(evidence_dir))
    errors.extend(validate_turns(evidence_dir))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args(argv)
    errors = validate_evidence(args.evidence_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: OCP3b evidence package valid: {args.evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
