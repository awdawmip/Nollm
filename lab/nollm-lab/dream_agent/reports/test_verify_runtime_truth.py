from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from verify_runtime_truth import EvidenceError, verify


@pytest.fixture()
def evidence(tmp_path: Path) -> Path:
    root = tmp_path
    for mode in ("enabled", "disabled"):
        folder = root / mode
        folder.mkdir()
        receipts = []
        for index in range(1, 16):
            (folder / f"turn-{index:02d}.json").write_text(json.dumps({"status": "ok", "result": {"payloads": [{"text": "reply"}], "meta": {"agentMeta": {"provider": "meituan", "model": "LongCat-2.0"}}}}), encoding="utf-8")
            receipts.append({"turn": index, "session_id": f"{mode}-s{index}", "exit_code": 0, "main_started_at": index * 1000, "main_command_returned_at": index * 1000 + 100})
        (folder / "receipts.jsonl").write_text("\n".join(json.dumps(item) for item in receipts) + "\n", encoding="utf-8")
    events = []
    for index in range(1, 16):
        run = f"run-{index}"
        events.extend([
            {"status": "hook", "hook": "agent_end", "hook_handler_duration_ms": 1},
            {"status": "started", "run_id": run, "session_key": f"agent:main:explicit:enabled-s{index}", "turn_key_sha256": f"turn-{index}", "deliver": False, "duplicate_dream_suppressed_count": 0, "trigger_phase": "AFTER_TURN", "source_hook": "agent_end", "material": {"turns": [{"role": "user", "content_utf8": f"question-{index}"}]}},
            {"status": "completed", "stage": "parse_store", "run_id": run, "parent_session_key": f"agent:main:explicit:enabled-s{index}", "dream_completed_at": index * 1000 + 200, "resolved_model_ref": "meituan/LongCat-2.0", "python_semantic_fallback": False, "visible_message_count": 0},
        ])
    (root / "enabled" / "events.jsonl").write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
    dedicated = root / "dedicated"
    dedicated.mkdir()
    (dedicated / "events.jsonl").write_text("\n".join((
        json.dumps({"status": "started", "run_id": "dedicated-run", "model_mode": "dedicated"}),
        json.dumps({"status": "completed", "run_id": "dedicated-run", "resolved_model_ref": "meituan/LongCat-2.0"}),
    )) + "\n", encoding="utf-8")
    return root


def _events(root: Path) -> list[dict]:
    return [json.loads(line) for line in (root / "enabled" / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def _write_events(root: Path, events: list[dict]) -> None:
    (root / "enabled" / "events.jsonl").write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")


def test_accepts_complete_raw_evidence(evidence: Path) -> None:
    assert verify(evidence)["dream"]["terminal_count"] == 15


@pytest.mark.parametrize("mutation", ["phase", "missing_reply", "second_reply", "second_dream", "model", "early", "summary", "system", "duplicate_user"])
def test_rejects_mutated_evidence(evidence: Path, mutation: str) -> None:
    events = _events(evidence)
    if mutation == "phase":
        next(item for item in events if item["status"] == "started")["trigger_phase"] = "AFTER_DELIVERY"
    elif mutation in {"missing_reply", "second_reply"}:
        path = evidence / "enabled" / "turn-01.json"
        raw = json.loads(path.read_text())
        if mutation == "missing_reply":
            raw["result"]["payloads"] = []
        else:
            raw["result"]["payloads"].append({"text": "extra"})
        path.write_text(json.dumps(raw), encoding="utf-8")
    elif mutation == "second_dream":
        duplicate = copy.deepcopy(next(item for item in events if item["status"] == "started"))
        duplicate["run_id"] = "duplicate-run"
        events.append(duplicate)
    elif mutation == "model":
        next(item for item in events if item["status"] == "completed")["resolved_model_ref"] = "other/model"
    elif mutation == "early":
        for item in events:
            if item["status"] == "completed":
                item["dream_completed_at"] = 0
    elif mutation == "summary":
        (evidence / "summary.json").write_text(json.dumps({"verified": True}), encoding="utf-8")
    elif mutation == "system":
        next(item for item in events if item["status"] == "started")["material"]["turns"].append({"role": "system", "content_utf8": "secret"})
    elif mutation == "duplicate_user":
        turns = next(item for item in events if item["status"] == "started")["material"]["turns"]
        turns.append(copy.deepcopy(turns[0]))
    _write_events(evidence, events)
    with pytest.raises(EvidenceError):
        verify(evidence)
