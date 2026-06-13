from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .audit import build_audit_report
from .cortex import focus_cards, orient_notebook, surface_anchor
from .filesystem import (
    append_ledger,
    card_address,
    find_card_path,
    notebook_name,
    read_card,
    read_ledger,
    read_yaml_file,
    render_card,
    utc_timestamp,
    write_card_file,
)
from .ids import card_id_for, next_event_id
from .models import CARD_DIRS, CARD_TYPES, SOURCE_KINDS, STATUS_TRANSITIONS, TRUST_VALUES, WRITE_STATUSES
from .recall import deterministic_recall
from .validation import architecture_metadata_issues, validate_notebook

PROTOCOL = "nollm.tool.v0.1"
ACTOR_TYPES = {"human", "llm", "tool", "system"}
OPTIONAL_LIST_FIELDS = ("evidence_refs", "implications", "do_not_infer")
OPTIONAL_ARCHITECTURE_FIELDS = ("layer", "hex", "anchor_fields", "scale_links")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_tool_manifest() -> dict[str, Any]:
    manifest_path = repo_root() / "tools" / "nollm_tool_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def dispatch_tool_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        return error_response("", "invalid_request", "Tool request must be a JSON object.")
    request_id = request.get("request_id")
    action = str(request.get("action", ""))
    protocol = str(request.get("protocol", PROTOCOL))
    if protocol != PROTOCOL:
        return error_response(action, "unsupported_protocol", f"Unsupported protocol: {protocol}", request_id=request_id)
    if action not in ACTIONS:
        return error_response(action, "unknown_action", f"Unknown tool action: {action}", request_id=request_id)
    if "notebook_path" not in request:
        return error_response(action, "missing_field", "Missing required field: notebook_path", request_id=request_id)

    notebook_path = Path(str(request["notebook_path"]))
    payload = request.get("input", {})
    if not isinstance(payload, dict):
        return error_response(action, "invalid_input", "Request input must be an object.", request_id=request_id)
    actor_type = str(request.get("actor_type", "tool"))
    if actor_type not in ACTOR_TYPES:
        return error_response(action, "invalid_actor_type", f"Invalid actor_type: {actor_type}", request_id=request_id)
    payload = dict(payload)
    payload["__actor"] = str(request.get("actor", "tool_user"))
    payload["__actor_type"] = actor_type

    missing = [field for field in REQUIRED_FIELDS[action] if field not in payload]
    if missing:
        return error_response(action, "missing_field", f"Missing required field: input.{missing[0]}", request_id=request_id)

    try:
        response = ACTIONS[action](notebook_path, payload)
    except (FileNotFoundError, ValueError) as exc:
        response = error_response(action, "invalid_request", str(exc))
    if request_id is not None:
        response["request_id"] = request_id
    return response


def success_response(
    action: str,
    result: dict[str, Any],
    *,
    warnings: list[str] | None = None,
    ledger_events: list[str] | None = None,
    addresses: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "protocol": PROTOCOL,
        "action": action,
        "result": result,
        "warnings": warnings or [],
        "ledger_events": ledger_events or [],
        "addresses": addresses or [],
    }


def error_response(action: str, code: str, message: str, warnings: list[str] | None = None, request_id: Any = None) -> dict[str, Any]:
    response = {
        "ok": False,
        "protocol": PROTOCOL,
        "action": action,
        "error": {"code": code, "message": message},
        "warnings": warnings or [],
    }
    if request_id is not None:
        response["request_id"] = request_id
    return response


def action_validate(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    issues = validate_notebook(path)
    return success_response("nollm.validate", {"pass": not issues, "issues": issues})


def action_audit(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    audit_format = str(payload.get("format", "json"))
    if audit_format != "json":
        return error_response("nollm.audit", "unsupported_format", "nollm.audit supports only format=json in the tool bridge")
    return success_response("nollm.audit", build_audit_report(path))


def action_orient(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = orient_notebook(path, str(payload["query_or_task"]))
    return success_response("nollm.orient", result, warnings=result.get("warnings", []))


def action_surface(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = surface_anchor(path, str(payload["anchor"]), int(payload.get("limit", 5)))
    return success_response("nollm.surface", result)


def action_focus(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = focus_cards(
        path,
        anchor_id=str(payload["anchor"]),
        card_type=payload.get("type"),
        status=payload.get("status"),
        limit=int(payload.get("limit", 5)),
        include_body=bool(payload.get("include_body", False)),
    )
    return success_response("nollm.focus", result, warnings=result.get("warnings", []), addresses=[card["address"] for card in result["cards"]])


def action_recall(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    digest, json_path, md_path = deterministic_recall(path, str(payload["query_or_task"]))
    addresses = [digest.get("address", ""), *digest.get("cards_read", [])]
    return success_response(
        "nollm.recall",
        {"digest": digest, "json_path": str(json_path), "markdown_path": str(md_path)},
        warnings=digest.get("warnings", []),
        addresses=[address for address in addresses if address],
    )


def action_write_card(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    status = str(payload.get("status", "candidate"))
    if status not in WRITE_STATUSES:
        return error_response("nollm.write_card", "invalid_status", "write_card refuses confirmed/superseded/rejected/archived status")
    anchors = payload.get("anchors", [])
    if not isinstance(anchors, list) or not anchors:
        return error_response("nollm.write_card", "missing_field", "input.anchors must be a non-empty list")
    known_anchors = anchor_ids(path)
    missing_anchors = [str(anchor) for anchor in anchors if str(anchor) not in known_anchors]
    if missing_anchors:
        return error_response("nollm.write_card", "unknown_anchor", f"Unknown anchor(s): {', '.join(missing_anchors)}")
    if payload["source"] not in SOURCE_KINDS:
        return error_response("nollm.write_card", "invalid_source", f"Invalid source: {payload['source']}")
    if payload["trust"] not in TRUST_VALUES:
        return error_response("nollm.write_card", "invalid_trust", f"Invalid trust: {payload['trust']}")
    if payload["type"] not in CARD_TYPES:
        return error_response("nollm.write_card", "invalid_type", f"Invalid card type: {payload['type']}")
    for field in OPTIONAL_LIST_FIELDS:
        if field in payload and not isinstance(payload[field], list):
            return error_response("nollm.write_card", "invalid_input", f"input.{field} must be a list")
    for field in ("hex", "anchor_fields", "scale_links"):
        if field in payload and not isinstance(payload[field], dict):
            return error_response("nollm.write_card", "invalid_input", f"input.{field} must be an object")

    notebook = notebook_name(path)
    card_type = str(payload["type"])
    card_id = card_id_for(str(payload["title"]), path / "cards")
    event_id = next_event_id(path / "ledger" / "events.jsonl")
    front = {
        "id": card_id,
        "title": str(payload["title"]),
        "type": card_type,
        "anchors": [str(anchor) for anchor in anchors],
        "created": utc_timestamp(),
        "status": status,
        "claim": str(payload["claim"]),
        "reason": str(payload["reason"]),
        "source": str(payload["source"]),
        "trust": str(payload["trust"]),
        "evidence_refs": [str(item) for item in payload.get("evidence_refs", [])],
        "implications": [str(item) for item in payload.get("implications", [])],
        "do_not_infer": [str(item) for item in payload.get("do_not_infer", [])],
        "ledger_event": event_id,
    }
    for field in OPTIONAL_ARCHITECTURE_FIELDS:
        if field in payload:
            front[field] = payload[field]
    metadata_issues = architecture_metadata_issues(front, card_id) if any(field in payload for field in OPTIONAL_ARCHITECTURE_FIELDS) else []
    if metadata_issues:
        return error_response(
            "nollm.write_card",
            "invalid_architecture_metadata",
            "; ".join(metadata_issues),
        )
    body = str(payload.get("body") or f"# {payload['title']}\n\n{payload['claim']}\n")
    card_path = path / "cards" / CARD_DIRS[card_type] / f"{card_id}.md"
    write_card_file(card_path, front, body)
    address = card_address(notebook, card_id)
    event = {
        "event_id": event_id,
        "op": "write_card",
        "actor": str(payload.get("__actor", "tool_user")),
        "actor_type": str(payload.get("__actor_type", "tool")),
        "from_status": None,
        "to_status": status,
        "reason": str(payload["reason"]),
        "timestamp": utc_timestamp(),
        "object_type": "card",
        "object_id": card_id,
        "address": address,
        "action": "create",
    }
    append_ledger(path, event)
    return success_response(
        "nollm.write_card",
        {"card_id": card_id, "address": address, "event_id": event_id, "path": str(card_path)},
        ledger_events=[event_id],
        addresses=[address],
    )


def action_read_card(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    front, body, card_path = read_card(path, str(payload["card_id_or_address"]))
    return success_response("nollm.read_card", {"front": front, "body": body, "path": str(card_path)}, addresses=[card_address(notebook_name(path), str(front.get("id")))])


def action_update_status(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    to_status = str(payload["to"])
    reason = str(payload["reason"])
    human_approval = payload.get("human_approval")
    superseded_by = payload.get("superseded_by")
    if to_status == "confirmed" and not human_approval:
        return error_response("nollm.update_status", "human_approval_required", "human_approval is required when confirming")
    if to_status == "superseded" and not superseded_by:
        return error_response("nollm.update_status", "superseded_by_required", "superseded_by is required when superseding")

    front, body, card_path = read_card(path, str(payload["card_id_or_address"]))
    from_status = front.get("status")
    if (from_status, to_status) not in STATUS_TRANSITIONS:
        return error_response("nollm.update_status", "invalid_transition", f"Invalid status transition: {from_status} -> {to_status}")
    if to_status == "confirmed" and front.get("source") == "llm_inference":
        return error_response("nollm.update_status", "llm_inference_confirmation_rejected", "Cannot confirm a card with source llm_inference")

    card_id = str(front["id"])
    event_id = next_event_id(path / "ledger" / "events.jsonl")
    notebook = notebook_name(path)
    trust_before = front.get("trust")
    trust_after = "human-approved" if to_status == "confirmed" and human_approval else trust_before
    event = {
        "event_id": event_id,
        "op": "update_status",
        "actor": str(payload.get("__actor", "tool_user")),
        "actor_type": str(payload.get("__actor_type", "tool")),
        "from_status": from_status,
        "to_status": to_status,
        "reason": reason,
        "timestamp": utc_timestamp(),
        "object_type": "card",
        "object_id": card_id,
        "address": card_address(notebook, card_id),
        "trust_before": trust_before,
        "trust_after": trust_after,
    }
    if human_approval:
        event["human_approval"] = str(human_approval)
    if superseded_by:
        superseded_path = find_card_path(path, str(superseded_by))
        if superseded_path.stem == card_id:
            return error_response("nollm.update_status", "self_supersede_rejected", "superseded_by must not refer to the same card")
        event["superseded_by"] = superseded_path.stem
        front["superseded_by"] = event["superseded_by"]

    append_ledger(path, event)
    front["status"] = to_status
    front["trust"] = trust_after
    front["ledger_event"] = event_id
    card_path.write_text(render_card(front, body), encoding="utf-8")
    return success_response(
        "nollm.update_status",
        {"card_id": card_id, "from_status": from_status, "to_status": to_status, "event_id": event_id},
        ledger_events=[event_id],
        addresses=[card_address(notebook, card_id)],
    )


def action_ledger(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    limit = int(payload.get("limit", 10))
    return success_response("nollm.ledger", {"events": read_ledger(path)[-limit:]})


def anchor_ids(path: Path) -> set[str]:
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    return {
        str(anchor.get("id"))
        for anchor in anchors_doc.get("anchors", []) or []
        if isinstance(anchor, dict) and anchor.get("id")
    }


REQUIRED_FIELDS = {
    "nollm.validate": [],
    "nollm.audit": [],
    "nollm.orient": ["query_or_task"],
    "nollm.surface": ["anchor"],
    "nollm.focus": ["anchor"],
    "nollm.recall": ["query_or_task"],
    "nollm.write_card": ["type", "title", "claim", "reason", "anchors", "source", "trust"],
    "nollm.read_card": ["card_id_or_address"],
    "nollm.update_status": ["card_id_or_address", "to", "reason"],
    "nollm.ledger": [],
}

ACTIONS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "nollm.validate": action_validate,
    "nollm.audit": action_audit,
    "nollm.orient": action_orient,
    "nollm.surface": action_surface,
    "nollm.focus": action_focus,
    "nollm.recall": action_recall,
    "nollm.write_card": action_write_card,
    "nollm.read_card": action_read_card,
    "nollm.update_status": action_update_status,
    "nollm.ledger": action_ledger,
}
