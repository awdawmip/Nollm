from __future__ import annotations

from nollm.grf.openclaw_bridge import dispatch


def test_openclaw_bridge_captures_then_applies_explicit_model_decision(tmp_path) -> None:
    captured = dispatch("capture", {"capture_id": "capture:bridge", "content": "retained source", "source_window_id": "window:bridge", "recorded_at": "2026-07-11T06:00:00Z"}, tmp_path)
    shard_id = str(captured["shard_id"])
    request = {"request_id": "request:bridge", "evidence_shard_id": shard_id, "candidate_cells": [{"profile_id": "eisenstein_exact_v1", "chart_id": "chart:bridge", "layer": 0, "q": -1, "r": 2, "phase": None}]}
    prepared = dispatch("prepare_placement", request, tmp_path)
    applied = dispatch("apply_placement", {"request": prepared, "decision": {"decision_id": "decision:bridge", "request_id": "request:bridge", "action": "new", "reason": "actual model output", "selected_cell": request["candidate_cells"][0], "candidate_id": "candidate:bridge", "placement_id": "placement:bridge"}, "source_window_id": "window:bridge", "recorded_at": "2026-07-11T06:00:01Z"}, tmp_path)
    assert applied["action"] == "new"
    assert applied["mutated"] is True


def test_openclaw_bridge_defer_has_no_mutation(tmp_path) -> None:
    request = {"request_id": "request:defer", "evidence_shard_id": "shard:missing", "candidate_cells": [{"profile_id": "eisenstein_exact_v1", "chart_id": "chart:bridge", "layer": 0, "q": 0, "r": 0, "phase": None}]}
    prepared = dispatch("prepare_placement", request, tmp_path)
    applied = dispatch("apply_placement", {"request": prepared, "decision": {"decision_id": "decision:defer", "request_id": "request:defer", "action": "defer", "reason": "insufficient context"}, "source_window_id": "window:defer", "recorded_at": "2026-07-11T06:00:01Z"}, tmp_path)
    assert applied == {"action": "defer", "mutated": False, "reason": "insufficient context"}
