from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
for package in ("nollm-access", "nollm-core", "nollm-trace"):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from nollm_access import FileStatementStore  # noqa: E402


def _json_lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_round(round_dir: Path) -> dict[str, Any]:
    metadata = json.loads((round_dir / "round.json").read_text(encoding="utf-8"))
    events = _json_lines(round_dir / "events.jsonl")
    receipts = _json_lines(round_dir / "turn-receipts.jsonl")
    round_number = metadata["round"]
    eligible = metadata["eligible_inputs"]

    _require(eligible == 15, f"round {round_number}: expected 15 eligible inputs")
    _require(len(receipts) == eligible, f"round {round_number}: receipt count mismatch")
    _require(all(item["exit_code"] == 0 for item in receipts), f"round {round_number}: main chat failed")
    _require(len({item["session_id"] for item in receipts}) == eligible, f"round {round_number}: duplicate session")

    started = [item for item in events if item.get("status") == "started"]
    terminal = [item for item in events if item.get("run_id") and item.get("status") in {"completed", "error"}]
    _require(len(started) == eligible, f"round {round_number}: started count mismatch")
    _require(len(terminal) == eligible, f"round {round_number}: terminal count mismatch")
    _require(len({item["run_id"] for item in started}) == eligible, f"round {round_number}: duplicate run")
    _require({item["run_id"] for item in terminal} == {item["run_id"] for item in started}, f"round {round_number}: terminal run mismatch")
    _require(all(item["deliver"] is False for item in started), f"round {round_number}: visible delivery enabled")
    _require(all(item["main_reply_delivered_at"] < item["dream_started_at"] for item in started), f"round {round_number}: Dream started before delivery")
    _require(all(item.get("visible_message_count", 0) == 0 for item in started + terminal), f"round {round_number}: extra visible message")
    _require(all(item.get("python_semantic_fallback", False) is False for item in terminal), f"round {round_number}: semantic fallback used")

    status_counts = Counter(item.get("error", item["status"]) for item in terminal)
    completed = [item for item in terminal if item["status"] == "completed"]
    writes = sum(item.get("statement_store_write_count", 0) for item in completed)
    statement_ids: list[str] = []
    for item in completed:
        statement_ids.extend(statement["statement_id"] for statement in item.get("statements", []))

    if metadata["write_mode"] == "shadow":
        _require(writes == 0, f"round {round_number}: shadow mode wrote state")
        _require(not (round_dir / "store-workspace").exists(), f"round {round_number}: shadow Store exists")
    else:
        _require(metadata["write_mode"] == "statement-store", f"round {round_number}: unknown write mode")
        _require(writes > 0 and writes == len(statement_ids), f"round {round_number}: write evidence mismatch")
        _require(len(set(statement_ids)) == len(statement_ids), f"round {round_number}: duplicate statement id")
        store = FileStatementStore(round_dir / "store-workspace")
        for event in completed:
            for expected in event.get("statements", []):
                reopened = store.get(expected["statement_id"])
                _require(reopened is not None, f"round {round_number}: statement did not reopen")
                _require(reopened.to_mapping() == expected, f"round {round_number}: reopened statement mismatch")

    return {
        "round": round_number,
        "prompt_version": metadata["prompt_version"],
        "write_mode": metadata["write_mode"],
        "eligible_inputs": eligible,
        "main_chat_success": len(receipts),
        "dream_started": len(started),
        "terminal_statuses": dict(sorted(status_counts.items())),
        "visible_message_count": 0,
        "python_semantic_fallback_count": 0,
        "statement_store_write_count": writes,
        "reopened_statement_count": len(statement_ids) if metadata["write_mode"] == "statement-store" else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rounds = [verify_round(args.runs / f"round-{number}") for number in (1, 2, 3)]
    result = {
        "schema_version": "nollm_aold_live_evidence_v1",
        "verified": True,
        "total_live_turns": sum(item["eligible_inputs"] for item in rounds),
        "total_visible_messages": 0,
        "total_python_semantic_fallbacks": 0,
        "rounds": rounds,
    }
    rendered = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
