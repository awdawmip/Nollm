from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_access import AccessMemoryLoop, MemoryStatement

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json


PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_placement_v1"
RECALL_SCHEMA_VERSION = "nollm_openclaw_recall_v1"
CURSOR_SCHEMA_VERSION = "nollm_openclaw_memory_cursor_v1"
_CURSOR_LIMIT = 8


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


def _cursor_state(root: Path) -> tuple[dict[str, list[object]], dict[str, list[object]]]:
    path = _cursor_path(root)
    if not path.exists():
        return {}, {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or value.get("schema_version") != CURSOR_SCHEMA_VERSION or set(value) not in ({"schema_version", "sessions"}, {"schema_version", "sessions", "agents"}) or type(value["sessions"]) is not dict:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor is invalid")
    agents = value.get("agents", {})
    if type(agents) is not dict:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor agents are invalid")
    if any(type(key) is not str or type(items) is not list for key, items in value["sessions"].items()) or any(type(key) is not str or type(items) is not list for key, items in agents.items()):
        raise FormationAdapterError("invalid_cursor", "MemoryCursor entries are invalid")
    return {key: list(items) for key, items in value["sessions"].items()}, {key: list(items) for key, items in agents.items()}


def _cells(raw: list[object]) -> list[dict[str, object]]:
    try:
        return AccessMemoryLoop(".").cursor_cells(raw)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor cells are invalid") from exc


def _load_cursor(root: Path, session_key: object) -> list[dict[str, object]]:
    if type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_session", "session_key is required")
    sessions, _ = _cursor_state(root)
    return _cells(sessions.get(session_key, []))


def _load_agent_cursor(root: Path, session_key: object) -> list[dict[str, object]]:
    _, agents = _cursor_state(root)
    return _cells(agents.get(_agent_cursor_key(session_key), []))


def _recall_cursor(root: Path, session_key: object) -> tuple[list[dict[str, object]], str]:
    session = _load_cursor(root, session_key)
    return (session, "session") if session else (_load_agent_cursor(root, session_key), "agent")


def _store_cursor(root: Path, session_key: str, cell: dict[str, object]) -> list[dict[str, object]]:
    path = _cursor_path(root)
    sessions, agents = _cursor_state(root)
    previous = list(_cells(sessions.get(session_key, [])))
    ordered = [item for item in previous if item != cell]
    ordered.append(cell)
    ordered = ordered[-_CURSOR_LIMIT:]
    mapped = ordered
    sessions[session_key] = mapped
    agents[_agent_cursor_key(session_key)] = mapped
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
    return ordered


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
    cursor, _cursor_source = _recall_cursor(root, session_key)
    with AccessMemoryLoop(root) as loop:
        nearby = loop.local_context(cursor, request_id + ":placement-context")
    prompt = f"""You are a private background geometry placement agent. The user will never see this run.
Decide one explicit placement action for this newly formed memory statement. You may only use the supplied local MemoryCursor and local geometry context. Do not infer a global topic, entity, source, graph, vector, or semantic index. Core validates and executes, you only decide.
Return exactly one raw JSON object with no markdown.
Schema version: {PLACEMENT_SCHEMA_VERSION}
For a new memory, `decision.statement_id` MUST be exactly `{statement.statement_id}`. Copy that literal value unchanged; do not use a placeholder, a draft id, or the statement text. The exact new-memory object is {{\"schema_version\":\"{PLACEMENT_SCHEMA_VERSION}\",\"outcome\":\"apply\",\"decision\":{{\"statement_id\":\"{statement.statement_id}\",\"action\":\"new\",\"target_cell\":{{\"profile_id\":\"eisenstein_exact_v1\",\"chart_id\":\"default\",\"layer\":0,\"q\":0,\"r\":0,\"phase\":null}},\"reason_text\":\"brief\"}}}}
For a known equivalent or revision, use action reuse, revision_current, move, or revision_keep_history with one supplied existing_handle where required. When the new statement explicitly supersedes, corrects, cancels, or replaces one supplied local candidate, choose revision_current with that candidate's handle instead of new. This is an LLM decision from the supplied statements, not a keyword rule. For no safe action use {{\"schema_version\":\"{PLACEMENT_SCHEMA_VERSION}\",\"outcome\":\"defer\",\"reason_text\":\"brief\"}}. Do not invent handles. Do not call tools.
statement: {json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
memory_cursor: {json.dumps(cursor, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
local_geometry_context: {json.dumps(nearby, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {"prompt": prompt, "schema_version": PLACEMENT_SCHEMA_VERSION, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}


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
    with AccessMemoryLoop(root) as loop:
        result = loop.apply_placement(statement, raw, request_id)
    if result["outcome"] == "applied" and type(result["handle"]) is dict:
        cursor = _store_cursor(root, session_key, result["handle"]["geometry_address"])
    else:
        cursor = _load_cursor(root, session_key)
    return {**result, "cursor": cursor, "json_repair": diagnostics}


def build_recall_prompt(query: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    if type(query) is not str or not query or type(session_key) is not str or not session_key or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "recall request fields are invalid")
    root = _workspace(memory_workspace)
    cursor, cursor_source = _recall_cursor(root, session_key)
    with AccessMemoryLoop(root) as loop:
        candidates = loop.local_context(cursor, request_id)
    if not candidates:
        return {"available": False, "candidate_count": 0, "cursor_source": cursor_source}
    prompt = f"""You are a private background memory recall agent. The user will never see this run.
Given the new user query and finite geometry-recalled statements, choose only statements that directly help answer the query. Return NONE when none help. Do not invent facts, do not call tools, and do not reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {RECALL_SCHEMA_VERSION}
inject: {{\"schema_version\":\"{RECALL_SCHEMA_VERSION}\",\"outcome\":\"inject\",\"statement_ids\":[\"...\"]}}
none: {{\"schema_version\":\"{RECALL_SCHEMA_VERSION}\",\"outcome\":\"none\",\"statement_ids\":[]}}
query: {json.dumps(query, ensure_ascii=False)}
recalled_candidates: {json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {"available": True, "prompt": prompt, "candidates": candidates, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "cursor_source": cursor_source, "entry_cells": cursor}


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
