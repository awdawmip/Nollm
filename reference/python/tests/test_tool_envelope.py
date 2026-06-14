from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
READ_ONLY_ACTIONS = {
    "nollm.validate",
    "nollm.audit",
    "nollm.inspect",
    "nollm.review",
    "nollm.annotations",
    "nollm.orient",
    "nollm.surface",
    "nollm.focus",
    "nollm.recall",
    "nollm.read_card",
    "nollm.ledger",
    "nollm.history",
}
WRITE_ACTIONS = {"nollm.annotate", "nollm.write_card", "nollm.update_status"}
REQUIRED_ENVELOPE_FIELDS = {"ok", "protocol", "action", "request_id", "result", "warnings", "ledger_events", "addresses"}


def test_success_response_examples_use_v1_envelope() -> None:
    for path in sorted((ROOT / "examples" / "tool_responses").glob("*.json")):
        response = json.loads(path.read_text(encoding="utf-8-sig"))
        if not response.get("ok"):
            continue
        missing = REQUIRED_ENVELOPE_FIELDS - set(response)
        assert missing == set(), f"{path.name}: {missing}"
        assert response["protocol"] == "nollm.tool.v0.1"
        assert isinstance(response["warnings"], list)
        assert isinstance(response["ledger_events"], list)
        assert isinstance(response["addresses"], list)
        if response["action"] in READ_ONLY_ACTIONS:
            assert response["ledger_events"] == [], path.name
        assert "traceback" not in json.dumps(response).lower()


def test_error_response_examples_are_structured() -> None:
    for path in sorted((ROOT / "examples" / "tool_responses").glob("error_*.json")):
        response = json.loads(path.read_text(encoding="utf-8-sig"))
        assert response["ok"] is False
        assert response["protocol"] == "nollm.tool.v0.1"
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "traceback" not in json.dumps(response).lower()


def test_top_level_request_examples_are_safe_or_temp_handled() -> None:
    mutating_top_level = []
    for path in sorted((ROOT / "examples" / "tool_requests").glob("*.json")):
        request = json.loads(path.read_text(encoding="utf-8-sig"))
        if request.get("action") in WRITE_ACTIONS:
            mutating_top_level.append(path.name)
    assert mutating_top_level == []
    assert (ROOT / "examples" / "tool_requests" / "templates" / "annotate_card.json").exists()