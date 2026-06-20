from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_ocp3b_live_e2e_evidence import validate_evidence


REQUIRED_NAMES = [
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
]


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(root: Path) -> None:
    rows = []
    for path in sorted(root.iterdir()):
        if path.name == "evidence_manifest.json":
            continue
        if path.is_file():
            rows.append({"path": path.name, "sha256": _sha(path)})
    _write_json(root / "evidence_manifest.json", {"self_hash_excluded": True, "files": rows})


def _valid_evidence(root: Path) -> None:
    for name in REQUIRED_NAMES:
        (root / name).write_text("{}\n", encoding="utf-8")
    (root / "README.md").write_text("OCP3b test fixture\n", encoding="utf-8")
    (root / "gateway_log_excerpt.txt").write_text("memory_search nollm_memory_search\n", encoding="utf-8")
    hashes = {"MEMORY.md": "abc", "DREAMS.md": "def", "memory/2026-06-20.md": "ghi"}
    _write_json(root / "fixture_hashes_before.json", hashes)
    _write_json(root / "fixture_hashes_after.json", hashes)

    turns = []
    for task_id in ["B1", "B2", "B3", "B4"]:
        turns.append(
            {
                "task_id": task_id,
                "condition": "baseline",
                "status": "pass",
                "tool_names": ["memory_search", "memory_get"],
                "read_called": False,
                "context_injection_count": 0,
            }
        )
    turns.extend(
        [
            {
                "task_id": "N5",
                "condition": "nollm",
                "status": "pass",
                "tool_names": [
                    "memory_search",
                    "memory_get",
                    "nollm_memory_search",
                    "nollm_memory_get",
                ],
                "read_called": False,
                "context_injection_count": 0,
            },
            {
                "task_id": "N7",
                "condition": "nollm",
                "status": "pass",
                "tool_names": [
                    "memory_search",
                    "memory_get",
                    "nollm_memory_write_candidate",
                ],
                "read_called": False,
                "context_injection_count": 0,
            },
        ]
    )
    _write_json(root / "agent_turn_summary.json", turns)

    trace_rows = [
        {"task_id": task_id, "tool_name": "memory_search"} for task_id in ["B1", "B2", "B3", "B4", "N5", "N7"]
    ]
    (root / "tool_trace_summary.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in trace_rows), encoding="utf-8"
    )
    _write_json(
        root / "scoring_report.json",
        {
            "direct_read_contamination_count": 0,
            "context_injection_contamination_count": 0,
            "source_mutation_result": "unchanged",
            "integration": "supported",
            "safety": "supported",
            "value_hypothesis": "inconclusive",
        },
    )
    _write_manifest(root)


def test_ocp3b_evidence_validator_accepts_valid_package(tmp_path: Path) -> None:
    _valid_evidence(tmp_path)

    assert validate_evidence(tmp_path) == []


def test_ocp3b_evidence_validator_rejects_direct_read(tmp_path: Path) -> None:
    _valid_evidence(tmp_path)
    turns = json.loads((tmp_path / "agent_turn_summary.json").read_text(encoding="utf-8"))
    turns[0]["tool_names"].append("read")
    turns[0]["read_called"] = True
    _write_json(tmp_path / "agent_turn_summary.json", turns)
    _write_manifest(tmp_path)

    errors = validate_evidence(tmp_path)

    assert any("direct-read contamination" in error for error in errors)


def test_ocp3b_evidence_validator_rejects_hash_mismatch(tmp_path: Path) -> None:
    _valid_evidence(tmp_path)
    (tmp_path / "gateway_log_excerpt.txt").write_text("mutated\n", encoding="utf-8")

    errors = validate_evidence(tmp_path)

    assert any("hash mismatch" in error for error in errors)
