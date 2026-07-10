"""JSON-line bridge used only by the native OpenClaw GRF adapter."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .cell_address import CellAddress
from .facade import GRFFacade
from .placement_protocol import NollmPlacementRequest, decision_from_mapping, validate_decision
from .recall import QueryProbe, RecallBudget


def dispatch(command: str, payload: dict[str, Any], workspace: Path) -> dict[str, object]:
    facade = GRFFacade(workspace)
    if command == "capture":
        receipt = facade.capture_text(str(payload["capture_id"]), str(payload["content"]), str(payload["source_window_id"]), str(payload["recorded_at"]))
        return _mapping(receipt)
    if command == "prepare_placement":
        return _request(payload).to_mapping()
    if command == "apply_placement":
        request = _request(dict(payload["request"]))
        decision = decision_from_mapping(dict(payload["decision"]))
        validate_decision(request, decision)
        if decision.action == "defer":
            return {"action": "defer", "mutated": False, "reason": decision.reason}
        if decision.action == "reuse":
            raise ValueError("reuse requires an explicit existing-admission host flow")
        result = facade.admit(request.evidence_shard_id, str(payload["source_window_id"]), {"action": "place", "decision_id": decision.decision_id, "candidate_id": decision.candidate_id, "placement_id": decision.placement_id, "selected_cell": decision.selected_cell.to_mapping(), "reasons": (decision.reason,), "admitted_by": "openclaw_llm", "placement_action": decision.action}, str(payload["recorded_at"]))
        return {"action": decision.action, "mutated": True, "placement": _mapping(result.placement_record), "admission": _mapping(result.admission_record)}
    if command == "recall":
        cell = _cell(dict(payload["cell"]))
        budget = RecallBudget(0, 1, 0, 0, 0, int(payload.get("max_results", 8)))
        digest = facade.recall(QueryProbe(str(payload["query_id"]), "explicit_cell", cell, ("coverage_up", "coverage_down", "lateral", "bridge"), budget))
        return _mapping(digest)
    if command == "show_source":
        return {"shard_id": str(payload["shard_id"]), "content": facade.get_source(str(payload["shard_id"]))}
    if command == "status":
        return _mapping(facade.validate_workspace())
    raise ValueError("unknown bridge command")


def _request(payload: dict[str, Any]) -> NollmPlacementRequest:
    return NollmPlacementRequest(str(payload["request_id"]), str(payload["evidence_shard_id"]), tuple(_cell(dict(value)) for value in payload["candidate_cells"]), tuple(str(value) for value in payload.get("session_items", ())), tuple(str(value) for value in payload.get("source_revision_refs", ())), tuple(str(value) for value in payload.get("referenced_placements", ())), tuple(str(value) for value in payload.get("nearby_cell_occupancy", ())), tuple(str(value) for value in payload.get("stitch_candidates", ())), tuple(str(value) for value in payload.get("candidate_reuse_placements", ())))


def _cell(value: dict[str, Any]) -> CellAddress:
    return CellAddress(str(value["profile_id"]), str(value["chart_id"]), int(value["layer"]), int(value["q"]), int(value["r"]), value.get("phase"))


def _mapping(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    raise TypeError("bridge response must be dataclass or mapping")


def main() -> None:
    request = json.loads(sys.stdin.read())
    try:
        result = dispatch(str(request["command"]), dict(request["payload"]), Path(str(request["workspace"])))
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, separators=(",", ":")))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
