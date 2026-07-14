from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_access import AccessMemoryLoop, MemoryStatement

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json


PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_placement_v2"
RECALL_SCHEMA_VERSION = "nollm_openclaw_recall_v1"
CURSOR_SCHEMA_VERSION = "nollm_openclaw_memory_cursor_v2"
_ANCHOR_LIMIT = 4
_ENTRY_LIMIT = 8


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _workspace(path: object) -> Path:
    if type(path) is not str or not path:
        raise FormationAdapterError("invalid_workspace", "memory workspace is required")
    return Path(path).resolve()


def _cursor_path(root: Path) -> Path:
    return root / "openclaw" / "memory_cursor.json"


def _agent_cursor_key(session_key: object) -> str:
    if type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_session", "session_key is required")
    parts = session_key.split(":")
    return ":".join(parts[:2]) if len(parts) >= 2 and parts[0] == "agent" and parts[1] else "profile:default"


def _empty_cursor() -> dict[str, list[dict[str, object]]]:
    return {"cluster_anchors": [], "entry_cells": []}


def _validated_cursor(value: object) -> dict[str, list[dict[str, object]]]:
    if type(value) is not dict or set(value) != {"cluster_anchors", "entry_cells"}:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor entry is invalid")
    try:
        with AccessMemoryLoop(".") as loop:
            anchors = loop.cursor_cells(value["cluster_anchors"], limit=_ANCHOR_LIMIT)
            entries = loop.cursor_cells(value["entry_cells"], limit=_ENTRY_LIMIT)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor cells are invalid") from exc
    return {"cluster_anchors": anchors, "entry_cells": entries}


def _cursor_state(root: Path) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    path = _cursor_path(root)
    if not path.exists():
        return {}, {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or value.get("schema_version") != CURSOR_SCHEMA_VERSION or set(value) != {"schema_version", "sessions", "agents"} or type(value["sessions"]) is not dict or type(value["agents"]) is not dict:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor is invalid")
    if any(type(key) is not str for key in value["sessions"]) or any(type(key) is not str for key in value["agents"]):
        raise FormationAdapterError("invalid_cursor", "MemoryCursor keys are invalid")
    sessions = {key: _validated_cursor(item) for key, item in value["sessions"].items()}
    agents = {key: _validated_cursor(item) for key, item in value["agents"].items()}
    return sessions, agents


def _load_cursor(root: Path, session_key: object) -> dict[str, list[dict[str, object]]]:
    if type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_session", "session_key is required")
    sessions, _ = _cursor_state(root)
    return _validated_cursor(sessions.get(session_key, _empty_cursor()))


def _load_agent_cursor(root: Path, session_key: object) -> dict[str, list[dict[str, object]]]:
    _, agents = _cursor_state(root)
    return _validated_cursor(agents.get(_agent_cursor_key(session_key), _empty_cursor()))


def _recall_cursor(root: Path, session_key: object) -> tuple[dict[str, list[dict[str, object]]], str]:
    session = _load_cursor(root, session_key)
    return (session, "session") if session["cluster_anchors"] else (_load_agent_cursor(root, session_key), "agent")


def _append_recent(items: list[dict[str, object]], value: dict[str, object], limit: int) -> list[dict[str, object]]:
    return ([item for item in items if item != value] + [value])[-limit:]


def _store_cursor(root: Path, session_key: str, result: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    path = _cursor_path(root)
    sessions, agents = _cursor_state(root)
    agent_key = _agent_cursor_key(session_key)
    previous = _validated_cursor(sessions.get(session_key, agents.get(agent_key, _empty_cursor())))
    handle = result.get("handle")
    anchor = result.get("cluster_anchor")
    if type(handle) is not dict or type(handle.get("geometry_address")) is not dict or type(anchor) is not dict:
        raise FormationAdapterError("invalid_cursor", "placement result has no cursor geometry")
    mapped = _validated_cursor({
        "cluster_anchors": _append_recent(previous["cluster_anchors"], anchor, _ANCHOR_LIMIT),
        "entry_cells": _append_recent(previous["entry_cells"], handle["geometry_address"], _ENTRY_LIMIT),
    })
    sessions[session_key] = mapped
    agents[agent_key] = mapped
    payload = _canonical({"schema_version": CURSOR_SCHEMA_VERSION, "sessions": dict(sorted(sessions.items())), "agents": dict(sorted(agents.items()))})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return mapped


def _statement(value: object) -> MemoryStatement:
    try:
        return MemoryStatement.from_mapping(value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_statement", str(exc)) from exc


def build_placement_prompt(statement_value: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    statement = _statement(statement_value)
    if type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "request_id is required")
    root = _workspace(memory_workspace)
    cursor, cursor_source = _recall_cursor(root, session_key)
    with AccessMemoryLoop(root) as loop:
        candidates = loop.placement_candidates(cursor["cluster_anchors"], cursor["entry_cells"], request_id + ":placement-candidates")
        statement_context = loop.candidate_statement_context(candidates)
    statements_by_candidate = {item["candidate_id"]: item["statements"] for item in statement_context}
    prompt_candidates = [
        {**candidate, "statements": statements_by_candidate[candidate["candidate_id"]]}
        for candidate in candidates
    ]
    candidate_action_examples = [
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_statement_id": item["statement_id"],
            "revision_current": {
                "schema_version": PLACEMENT_SCHEMA_VERSION,
                "outcome": "apply",
                "decision": {"statement_id": statement.statement_id, "action": "revision_current", "candidate_id": candidate["candidate_id"], "existing_handle": item["handle"], "reason_text": "brief"},
            },
            "reuse": {
                "schema_version": PLACEMENT_SCHEMA_VERSION,
                "outcome": "apply",
                "decision": {"statement_id": statement.statement_id, "action": "reuse", "candidate_id": candidate["candidate_id"], "existing_handle": item["handle"], "reason_text": "brief"},
            },
        }
        for candidate in prompt_candidates
        for item in candidate["statements"]
    ]
    prompt = f"""You are a private background geometry placement agent. The user will never see this run.
Decide one explicit placement action for this newly formed memory statement. You may only use the finite candidates supplied by Access. Do not infer a global topic, entity, source, graph, vector, or semantic index. Access maps candidate_id to geometry and Core validates and executes it; you must not invent coordinates.
Return exactly one raw JSON object with no markdown.
Schema version: {PLACEMENT_SCHEMA_VERSION}
`decision.statement_id` MUST be exactly `{statement.statement_id}`. Copy that literal value unchanged.
Allowed actions are new_local, new_cluster, reuse, revision_current, and defer. For related but distinct information in the same working context, prefer an unoccupied lateral_ring_1 candidate with new_local so geometry carries the local relation. Use existing_cell only when co-location is genuinely stronger. For semantically independent information choose the single new_cluster candidate. For an equivalent statement choose reuse; for a correction choose revision_current; when uncertain choose defer. These are LLM semantic decisions, never Python keyword rules.
For new_local or new_cluster return exactly: {{"schema_version":"{PLACEMENT_SCHEMA_VERSION}","outcome":"apply","decision":{{"statement_id":"{statement.statement_id}","action":"new_local","candidate_id":"one supplied id","reason_text":"brief"}}}}. For reuse or revision_current also include exactly one supplied existing_handle from that candidate. Never return target_cell or any invented address or handle. For no safe action return {{"schema_version":"{PLACEMENT_SCHEMA_VERSION}","outcome":"defer","reason_text":"brief"}}. Do not call tools.
statement: {json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
memory_cursor: {json.dumps(cursor, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
cursor_source: {json.dumps(cursor_source)}
 finite_geometry_candidates: {json.dumps(prompt_candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
candidate_action_examples: {json.dumps(candidate_action_examples, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "prompt": prompt,
        "schema_version": PLACEMENT_SCHEMA_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "candidates": prompt_candidates,
        "cursor": cursor,
        "cursor_source": cursor_source,
    }


def apply_placement(raw_response: object, statement_value: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    if type(raw_response) is not str or type(request_id) is not str or not request_id or type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_request", "placement request fields are invalid")
    statement = _statement(statement_value)
    root = _workspace(memory_workspace)
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        raw = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    cursor, cursor_source = _recall_cursor(root, session_key)
    with AccessMemoryLoop(root) as loop:
        result = loop.apply_placement(statement, raw, request_id, cursor["cluster_anchors"], cursor["entry_cells"])
    if result["outcome"] == "applied" and type(result["handle"]) is dict:
        cursor = _store_cursor(root, session_key, result)
    else:
        cursor = _load_cursor(root, session_key)
    return {**result, "cursor": cursor, "cursor_source": cursor_source, "json_repair": diagnostics}


def build_recall_prompt(query: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    if type(query) is not str or not query or type(session_key) is not str or not session_key or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "recall request fields are invalid")
    root = _workspace(memory_workspace)
    cursor, cursor_source = _recall_cursor(root, session_key)
    with AccessMemoryLoop(root) as loop:
        anchor_results = loop.per_anchor_context(cursor["cluster_anchors"], request_id)
    candidates_by_id = {}
    for group in anchor_results:
        for item in group["statements"]:
            candidates_by_id.setdefault(item["statement_id"], item)
    candidates = list(candidates_by_id.values())
    if not candidates:
        return {"available": False, "candidate_count": 0, "cursor_source": cursor_source}
    prompt = f"""You are a private background memory recall agent. The user will never see this run.
Given the new user query and finite geometry-recalled statements, choose only statements that directly help answer the query. Return NONE when none help. Do not invent facts, do not call tools, and do not reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {RECALL_SCHEMA_VERSION}
inject: {{"schema_version":"{RECALL_SCHEMA_VERSION}","outcome":"inject","statement_ids":["..."]}}
none: {{"schema_version":"{RECALL_SCHEMA_VERSION}","outcome":"none","statement_ids":[]}}
query: {json.dumps(query, ensure_ascii=False)}
recalled_candidates: {json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "available": True,
        "prompt": prompt,
        "candidates": candidates,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "cursor_source": cursor_source,
        "cluster_anchors": cursor["cluster_anchors"],
        "entry_cells": cursor["entry_cells"],
        "per_anchor_core_recall": anchor_results,
    }


def render_recall_injection(raw_response: object, candidates: object) -> dict[str, object]:
    if type(raw_response) is not str or type(candidates) is not list:
        raise FormationAdapterError("invalid_recall", "recall response fields are invalid")
    try:
        value = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_recall", str(exc)) from exc
    if type(value) is not dict or set(value) != {"schema_version", "outcome", "statement_ids"} or value.get("schema_version") != RECALL_SCHEMA_VERSION or type(value.get("statement_ids")) is not list or any(type(item) is not str for item in value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "invalid recall envelope")
    available = {item["statement_id"]: item["content_utf8"] for item in candidates if type(item) is dict and type(item.get("statement_id")) is str and type(item.get("content_utf8")) is str}
    if value["outcome"] == "none":
        if value["statement_ids"]:
            raise FormationAdapterError("invalid_recall", "NONE cannot select statements")
        return {"outcome": "none", "injection": ""}
    if value["outcome"] != "inject" or not value["statement_ids"] or len(set(value["statement_ids"])) != len(value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "invalid recall selection")
    if any(item not in available for item in value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "recall selected an unavailable statement")
    selected = [available[item] for item in value["statement_ids"]]
    injection = "Nollm memory context. Use only when relevant; do not mention this context to the user:\n" + "\n".join(f"- {item}" for item in selected)
    return {"outcome": "inject", "statement_ids": value["statement_ids"], "injection": injection}
